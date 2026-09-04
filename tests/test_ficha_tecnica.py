"""Pruebas del módulo de ficha técnica (modelo, controller y diálogo).

Cubre:
    - Guardado y lectura de la ficha de un modelo (upsert).
    - Fotos por tipo (guardar, leer, reemplazar y borrar).
    - Kardex con saldo acumulado.
    - Registro de la ficha en la BD (tablas nuevas).

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest

from src.controllers.inventario_controller import InventarioController
from src.database.db_manager import DatabaseManager
from src.models.ficha_tecnica_model import (
    CAMPOS_ENCABEZADO, CAMPOS_FICHA, FichaTecnicaModel, TIPOS_FOTO,
)


@pytest.fixture(scope="session", autouse=True)
def _esquema_ficha():
    """Asegura que las tablas de la ficha existan en la BD."""
    DatabaseManager().initialize_schema()


@pytest.fixture
def modelo(qapp):
    """Crea un modelo de prueba y devuelve su id."""
    db = DatabaseManager()
    import uuid
    codigo = f"FT-{uuid.uuid4().hex[:8]}"
    cursor = db.execute(
        "INSERT INTO modelos (codigo, nombre, descripcion) VALUES (?, ?, ?)",
        (codigo, "Modelo Ficha Test", "Modelo de prueba de ficha técnica"))
    modelo_id = cursor.lastrowid
    yield modelo_id
    db.execute("DELETE FROM lista_materiales WHERE modelo_id = ?", (modelo_id,))
    db.execute("DELETE FROM ficha_tecnica_fotos WHERE modelo_id = ?", (modelo_id,))
    db.execute("DELETE FROM fichas_tecnicas WHERE modelo_id = ?", (modelo_id,))
    db.execute("DELETE FROM modelos WHERE id = ?", (modelo_id,))


# ------------------------------------------------- Catálogo de campos
class TestCamposFicha:
    def test_columnas_caracteristica_no_repetidas(self):
        columnas = [col for _, col in CAMPOS_FICHA]
        assert len(columnas) == len(set(columnas))

    def test_tipos_foto_validos(self):
        tipos = [tipo for _, tipo in TIPOS_FOTO]
        assert tipos == ["producto", "tubo", "chinela", "talon", "suela"]


# ------------------------------------------------- Modelo
class TestModeloFicha:
    def test_guardar_y_obtener(self, qapp, modelo):
        m = FichaTecnicaModel()
        datos = {"proyecto": "Invierno 2026", "etapa": "MUESTRA", "suela": "TR",
                 "comentarios": "Sin comentarios"}
        m.guardar(modelo, datos)
        ficha = m.obtener(modelo)
        assert ficha is not None
        assert ficha["proyecto"] == "Invierno 2026"
        assert ficha["suela"] == "TR"
        assert ficha["comentarios"] == "Sin comentarios"

    def test_guardar_actualiza_sin_duplicar(self, qapp, modelo):
        m = FichaTecnicaModel()
        m.guardar(modelo, {"suela": "TR"})
        m.guardar(modelo, {"suela": "CAUCHO"})
        ficha = m.obtener(modelo)
        assert ficha["suela"] == "CAUCHO"
        filas = DatabaseManager().fetch_all(
            "SELECT COUNT(*) AS total FROM fichas_tecnicas WHERE modelo_id = ?",
            (modelo,))
        assert filas[0]["total"] == 1

    def test_guardar_foto_y_obtener(self, qapp, modelo):
        m = FichaTecnicaModel()
        imagen = b"datos-imagen-fake"
        m.guardar_foto(modelo, "suela", imagen)
        assert m.obtener_foto(modelo, "suela") == imagen

    def test_guardar_foto_reemplaza(self, qapp, modelo):
        m = FichaTecnicaModel()
        m.guardar_foto(modelo, "tubo", b"primera")
        m.guardar_foto(modelo, "tubo", b"segunda")
        assert m.obtener_foto(modelo, "tubo") == b"segunda"

    def test_guardar_foto_none_borra(self, qapp, modelo):
        m = FichaTecnicaModel()
        m.guardar_foto(modelo, "talon", b"algo")
        m.guardar_foto(modelo, "talon", None)
        assert m.obtener_foto(modelo, "talon") is None

    def test_obtener_fichas_inexistente(self, qapp, modelo):
        assert FichaTecnicaModel().obtener(999999) is None

    def test_valores_historicos(self, qapp, modelo):
        m = FichaTecnicaModel()
        m.guardar(modelo, {"suela": "TR", "forro": "MICROFIBRA"})
        hist = m.valores_historicos("suela")
        assert "TR" in hist
        # Campo inexistente devuelve []
        assert m.valores_historicos("no_existe") == []

    def test_insumos_activos(self, qapp):
        m = FichaTecnicaModel()
        lista = m.insumos_activos()
        assert isinstance(lista, list)


# ------------------------------------------------- Controller
class TestControllerFicha:
    def test_guardar_y_obtener_via_controller(self, qapp, modelo):
        c = InventarioController()
        c.guardar_ficha(modelo, {"proyecto": "Verano", "cierre": "CORDÓN"})
        ficha = c.obtener_ficha(modelo)
        assert ficha["proyecto"] == "Verano"
        assert ficha["cierre"] == "CORDÓN"

    def test_fotos_via_controller(self, qapp, modelo):
        c = InventarioController()
        c.guardar_foto_ficha(modelo, "producto", b"foto")
        assert c.obtener_foto_ficha(modelo, "producto") == b"foto"

    def test_listar_kardex_con_saldo(self, qapp, modelo):
        c = InventarioController()
        import uuid
        codigo = f"KARDEX-{uuid.uuid4().hex[:8]}"
        insumo_id = c.crear_insumo(codigo, "Suela kardex", "Suelas")
        try:
            c.registrar_movimiento(insumo_id, "entrada", 100)
            c.registrar_movimiento(insumo_id, "salida", 30)
            c.registrar_movimiento(insumo_id, "entrada", 10)
            movs = c.listar_kardex(insumo_id)
            assert [m["saldo"] for m in movs] == [100, 70, 80]
            assert [m["entrada"] for m in movs] == [100, 0, 10]
            assert [m["salida"] for m in movs] == [0, 30, 0]
        finally:
            c.desactivar_insumo(insumo_id)

    def test_kardex_sin_movimientos(self, qapp, modelo):
        c = InventarioController()
        import uuid
        codigo = f"KARDEX-0-{uuid.uuid4().hex[:8]}"
        insumo_id = c.crear_insumo(codigo, "Suela vacía", "Suelas")
        try:
            assert c.listar_kardex(insumo_id) == []
        finally:
            c.desactivar_insumo(insumo_id)

    def test_valores_historicos_via_controller(self, qapp, modelo):
        c = InventarioController()
        c.guardar_ficha(modelo, {"suela": "TR"})
        hist = c.valores_historicos_ficha("suela")
        assert "TR" in hist

    def test_insumos_activos_via_controller(self, qapp):
        c = InventarioController()
        assert isinstance(c.insumos_activos(), list)

    def test_agregar_insumo_a_lista(self, qapp, modelo):
        c = InventarioController()
        import uuid
        codigo = f"BOM-{uuid.uuid4().hex[:8]}"
        insumo_id = c.crear_insumo(codigo, "Insumo BOM", "Suelas")
        try:
            # Primera inserción: True
            assert c.agregar_insumo_a_lista(modelo, insumo_id) is True
            # Duplicada: False
            assert c.agregar_insumo_a_lista(modelo, insumo_id) is False
        finally:
            c.desactivar_insumo(insumo_id)


# ------------------------------------------------- Diálogo
class TestDialogoFicha:
    def test_construccion_dialogo(self, qapp, modelo):
        from src.controllers.produccion_controller import ProduccionController
        from src.views.dialogs import DialogFichaTecnica
        c = InventarioController()
        dlg = DialogFichaTecnica(c, ProduccionController(), modelo)
        assert dlg.windowTitle().startswith("Ficha técnica")
        assert len(dlg.campos_encabezado) == len(CAMPOS_ENCABEZADO)
        assert len(dlg.campos_ficha) == len(CAMPOS_FICHA)
        dlg.deleteLater()
