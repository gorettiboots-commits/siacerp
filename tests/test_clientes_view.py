"""Pruebas del restyling Windows Forms clásico en la vista de Clientes.

Cubre:
    - Aplicación del estilo local (objectName/#F0F0F0) en la vista y diálogos.
    - Acciones por registro nuevas (Cancelar en pedidos, Activar/Desactivar
      en clientes) y su resolución dinámica de texto/habilitado.

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest

from src.components.complex_grid import ComplexGrid
from src.controllers.clientes_controller import ClientesController
from src.controllers.programacion_controller import ProgramacionController
from src.views.clientes_view import (
    ClientesView, _aplicar_estilo_forms, _DialogCliente,
    _DialogLineaPedido, _DialogPedidoCliente,
)
from src.views.programar_pedido_dialog import ProgramarPedidoDialog

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def vista(qapp):
    v = ClientesView()
    yield v
    v.deleteLater()


@pytest.fixture
def controller(qapp):
    return ClientesController()


# ------------------------------------------------- Estilo
class TestEstiloForms:
    def test_vista_aplica_estilo_local(self, vista):
        qss = vista.styleSheet()
        assert qss
        assert "#F0F0F0" in qss

    def test_dialogo_cliente_aplica_estilo(self, controller):
        dlg = _DialogCliente(controller)
        assert "#F0F0F0" in dlg.styleSheet()
        dlg.deleteLater()

    def test_dialogo_linea_aplica_estilo(self, qapp):
        dlg = _DialogLineaPedido()
        assert "#F0F0F0" in dlg.styleSheet()
        dlg.deleteLater()

    def test_dialogo_pedido_aplica_estilo(self, controller):
        dlg = _DialogPedidoCliente(controller)
        assert "#F0F0F0" in dlg.styleSheet()
        dlg.deleteLater()

    def test_helper_aplica_a_widget(self, qapp):
        from PySide6.QtWidgets import QWidget

        w = QWidget()
        _aplicar_estilo_forms(w)
        assert "#F0F0F0" in w.styleSheet()
        w.deleteLater()


# ------------------------------------------------- Acciones por registro
class TestAccionesGrid:
    def test_pedidos_registra_tres_acciones(self, vista):
        assert len(vista.vista._acciones) == 3
        textos = [acc["texto"] for acc in vista.vista._acciones]
        assert "Programar" in textos and "Editar" in textos and "Cancelar" in textos

    def test_pedidos_cancelar_deshabilitado_en_cancelado(self, vista):
        acc = vista.vista._acciones[2]
        assert acc["texto"] == "Cancelar"
        fn = acc["habilitado"]
        assert fn({"estatus": "surtido"}) is False
        assert fn({"estatus": "cancelado"}) is False
        assert fn({"estatus": "pendiente"}) is True

    def test_pedidos_programar_deshabilitado_en_cancelado(self, vista):
        acc = vista.vista._acciones[0]
        assert acc["texto"] == "Programar"
        fn = acc["habilitado"]
        assert fn({"estatus": "surtido"}) is False
        assert fn({"estatus": "cancelado"}) is False
        assert fn({"estatus": "pendiente"}) is True

    def test_clientes_registra_dos_acciones(self, vista):
        assert len(vista.grid_cli._acciones) == 2
        textos = [acc["texto"] for acc in vista.grid_cli._acciones]
        assert "Editar" in textos

    def test_clientes_texto_activo_desactivo(self, vista):
        acc = vista.grid_cli._acciones[1]
        assert acc["texto"]({"activo": 1}) == "Desactivar"
        assert acc["texto"]({"activo": 0}) == "Activar"


# ------------------------------------------------- Estatus programado (folios)
class TestEstatusProgramado:
    """El estatus 'programado' no se elige a mano: lo fija la programación
    cuando el pedido ya tiene folios de programación (tarjetas)."""

    @staticmethod
    def _datos_programables(controller) -> dict:
        """Crea cliente + pedido; regresa ids y datos para programar."""
        puntos = controller.listar_puntos()
        assert puntos, "tallas_catalogo debe tener tallas activas"
        talla = puntos[0]
        cliente_id = controller.crear_cliente("Cliente Prueba Estatus")
        pedido_id = controller.crear_pedido(
            controller.siguiente_folio(), cliente_id, "2026-08-13",
            estatus="pendiente",
            detalle=[{"modelo": "MODELO PRUEBA", "piel": "PIEL", "color": "COLOR",
                      "puntos": [{"punto_id": talla["id"], "pares": 6}]}])
        detalle_id = controller.obtener_detalle_pedido(pedido_id)[0]["id"]
        return {"cliente_id": cliente_id, "pedido_id": pedido_id,
                "detalle_id": detalle_id, "talla": talla["punto"]}

    @staticmethod
    def _limpiar(controller, datos: dict) -> None:
        prog = ProgramacionController()
        prog.model.db.execute(
            "DELETE FROM programacion_lineas WHERE pedido_id = ?",
            (datos["pedido_id"],))
        controller.pedido_model.db.execute(
            "DELETE FROM detalle_pedido_cliente WHERE pedido_id = ?",
            (datos["pedido_id"],))
        controller.pedido_model.db.execute(
            "DELETE FROM pedidos_cliente WHERE id = ?",
            (datos["pedido_id"],))
        controller.cliente_model.db.execute(
            "DELETE FROM clientes WHERE id = ?", (datos["cliente_id"],))

    @staticmethod
    def _opciones_estatus(dlg) -> list:
        return [dlg.cmb_estatus.itemData(i)
                for i in range(dlg.cmb_estatus.count())]

    def test_pedido_nuevo_no_ofrece_programado(self, controller):
        dlg = _DialogPedidoCliente(controller)
        assert "programado" not in self._opciones_estatus(dlg)
        assert dlg._tiene_programacion is False
        dlg.deleteLater()

    def test_pedido_sin_folios_no_ofrece_programado(self, controller):
        datos = self._datos_programables(controller)
        try:
            dlg = _DialogPedidoCliente(controller, datos["pedido_id"])
            assert "programado" not in self._opciones_estatus(dlg)
            assert dlg._tiene_programacion is False
            dlg.deleteLater()
        finally:
            self._limpiar(controller, datos)

    def test_programar_fija_estatus_y_ofrece_programado(self, controller):
        datos = self._datos_programables(controller)
        try:
            prog = ProgramacionController()
            semana_id = prog.listar_semanas_programar()[0]["id"]
            folios = prog.programar_pedido(
                pedido_id=datos["pedido_id"], folio_pedido="",
                cliente="Cliente Prueba Estatus",
                total_pedido=6, semana_id=semana_id, fecha_prog="2026-08-10",
                corridas=[{"detalle_id": datos["detalle_id"],
                           "modelo": "MODELO PRUEBA", "piel": "PIEL",
                           "color": "COLOR",
                           "tallas": [{"talla": datos["talla"], "pares": 6}]}])
            assert folios, "debe generar al menos un folio de programación"

            pedido = controller.obtener_pedido(datos["pedido_id"])
            assert pedido["estatus"] == "programado"

            dlg = _DialogPedidoCliente(controller, datos["pedido_id"])
            assert "programado" in self._opciones_estatus(dlg)
            assert dlg._tiene_programacion is True
            dlg.deleteLater()
        finally:
            self._limpiar(controller, datos)


# ------------------------------------------------- Línea con captura de tallas
class TestLineaConTallas:
    def test_dialogo_linea_embebe_matriz_y_total_en_vivo(self, controller):
        dlg = _DialogLineaPedido(controller)
        assert hasattr(dlg, "matriz")
        puntos = dlg.puntos
        assert puntos, "tallas_catalogo debe tener tallas activas"
        primera = puntos[0]
        celda = dlg.matriz.celdas[str(primera["punto"])]
        celda.setText("12")
        assert dlg.matriz.lbl_total.text() == "Total de pares: 12"
        dlg.txt_modelo.setText("MODELO PRUEBA")
        dlg._save()
        assert dlg.modelo == "MODELO PRUEBA"
        assert dlg.pares.get(primera["id"]) == 12
        dlg.deleteLater()

    def test_dialogo_linea_excluye_pares_en_cero(self, controller):
        dlg = _DialogLineaPedido(controller)
        puntos = dlg.puntos
        if puntos:
            dlg.matriz.celdas[str(puntos[0]["punto"])].setText("0")
        dlg.txt_modelo.setText("MODELO PRUEBA")
        dlg._save()
        assert dlg.pares == {}
        dlg.deleteLater()


# ------------------------------------------- Corrida visible en programación
class TestCorridaVisibleProgramacion:
    def test_columna_corrida_muestra_rango_capturado(self, controller):
        puntos = controller.listar_puntos()
        assert len(puntos) >= 2, "se requieren al menos dos tallas"
        t1, t2 = puntos[0], puntos[1]
        cliente_id = controller.crear_cliente("Cliente Corrida")
        pedido_id = controller.crear_pedido(
            controller.siguiente_folio(), cliente_id, "2026-08-13",
            estatus="pendiente",
            detalle=[{"modelo": "MODELO PRUEBA", "piel": "PIEL",
                      "color": "COLOR",
                      "puntos": [{"punto_id": t1["id"], "pares": 3},
                                 {"punto_id": t2["id"], "pares": 2}]}])
        try:
            prog = ProgramacionController()
            dlg = ProgramarPedidoDialog(controller, prog, pedido_id)
            recs = dlg._detalle_recs
            assert recs and recs[0]["corrida_cap"]
            assert "del" in recs[0]["corrida_cap"]
            assert dlg._texto_corrida_rango(recs[0]) == recs[0]["corrida_cap"]
            dlg.deleteLater()
        finally:
            controller.pedido_model.db.execute(
                "DELETE FROM detalle_pedido_cliente WHERE pedido_id = ?",
                (pedido_id,))
            controller.pedido_model.db.execute(
                "DELETE FROM pedidos_cliente WHERE id = ?", (pedido_id,))
            controller.cliente_model.db.execute(
                "DELETE FROM clientes WHERE id = ?", (cliente_id,))


# ------------------------------------------------- Integración con el grid
class TestIntegracionConGrid:
    def test_vista_es_complex_grid(self, vista):
        assert isinstance(vista.vista, ComplexGrid)
        assert isinstance(vista.grid_cli, ComplexGrid)