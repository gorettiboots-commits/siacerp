"""Pruebas del reporte HTML de Órdenes de Compra (membrete y observaciones).

Convención de nombres: [función]_[condición]_[resultadoEsperado].
Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import base64

import pytest

import src.components.preview_impresion as pim
from src.utils.export_utils import _oc_receipt_html, print_orden_compra

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def _datos(**extra) -> dict:
    base = {
        "folio": "OC-0001",
        "fecha_emision": "2026-08-12",
        "estatus": "pendiente",
        "metodo_pago": "Transferencia bancaria",
        "solo_remision": False,
        "observaciones": "",
        "proveedor_nombre": "Proveedor X",
        "proveedor_telefono": "",
        "proveedor_email": "",
        "proveedor_rfc": "",
        "proveedor_direccion": "",
    }
    base.update(extra)
    return base


def _detalle() -> list[dict]:
    return [
        {"insumo_nombre": "Suela", "cantidad": 10, "precio_unitario": 25.0,
         "tallas": [
             {"talla_id": 1, "talla": "15", "pares": 6, "precio": 25.5},
             {"talla_id": 2, "talla": "15.5", "pares": 4, "precio": 30.0},
         ]},
    ]


def _base64_de(ruta: str) -> str:
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ----------------------------------------------------------------- Membrete
class TestMembrete:
    def test_reporte_usa_logonew_como_membrete(self):
        html = _oc_receipt_html(_datos(), _detalle())
        assert _base64_de("logonew.png") in html

    def test_reporte_muestra_logo_a_tamano_de_membrete(self):
        html = _oc_receipt_html(_datos(), _detalle())
        assert 'width="90"' in html or 'width="100"' in html or 'width="110"' in html or 'width="120"' in html

    def test_reporte_conserva_marca_y_totales(self):
        html = _oc_receipt_html(_datos(), _detalle())
        # La marca viene de _nombre_empresa() (BD o fallback)
        from src.utils.export_utils import _nombre_empresa
        assert _nombre_empresa().upper() in html
        assert "RECIBO DE COMPRA" in html
        # 6*25.5 + 4*30 = 153 + 120 = 273 de subtotal
        assert "$273.00" in html


# ----------------------------------------------------------- Observaciones
class TestObservaciones:
    def test_sin_observaciones_no_muestra_la_seccion(self):
        html = _oc_receipt_html(_datos(), _detalle())
        assert "Observaciones" not in html

    def test_con_observaciones_muestra_la_seccion_y_conserva_saltos(self):
        html = _oc_receipt_html(
            _datos(observaciones="Entregar antes del viernes\nEn caja A"),
            _detalle(),
        )
        assert "Observaciones" in html
        assert "Entregar antes del viernes" in html
        assert "En caja A" in html
        assert "<br/>" in html

    def test_con_observaciones_escapa_html(self):
        html = _oc_receipt_html(
            _datos(observaciones="<b>urgente</b> & entrega"),
            _detalle(),
        )
        assert "&lt;b&gt;urgente&lt;/b&gt;" in html
        assert "&amp;" in html


# -------------------------------------------------------------- Vista previa
class TestVistaPrevia:
    def test_print_orden_compra_abre_la_vista_previa(self, monkeypatch):
        abiertos = []

        def _stub(html: str, titulo: str = "", parent=None) -> None:
            abiertos.append((html, titulo))

        monkeypatch.setattr(pim, "previsualizar_html", _stub)
        print_orden_compra(_datos(), _detalle(), None)
        assert len(abiertos) == 1
        assert "RECIBO DE COMPRA" in abiertos[0][0]
        assert "Orden de Compra" in abiertos[0][1]
