"""Pruebas unitarias del componente aprobado 'preview_impresion'.

Convención de nombres: [función]_[condición]_[resultadoEsperado].
Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import os
import tempfile

import pytest
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtTest import QTest

import src.components.preview_impresion as mod
from src.components import listar_componentes, obtener_componente
from src.components.preview_impresion import (
    PreviewImpresion,
    previsualizar_html,
)
from src.views.sandbox_preview_impresion import (
    PreviewImpresionDemo,
    _reporte_inventario_html,
    _reporte_oc_ejemplo_html,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

HTML_PRUEBA = ("<html><body><h1>Reporte de prueba</h1>"
               "<p>Contenido de ejemplo.</p></body></html>")


@pytest.fixture
def sin_webengine(monkeypatch):
    """Usa el fallback QTextBrowser: determinista y sin Chromium en CI."""
    monkeypatch.setattr(mod, "_HAS_WEBENGINE", False)


@pytest.fixture
def preview(qapp, sin_webengine):
    dlg = PreviewImpresion(HTML_PRUEBA, titulo="Reporte de prueba")
    dlg.show()
    # Espera el QTimer.singleShot(0) que recalcula el tamaño de la hoja
    # con el ancho real del visor.
    QTest.qWait(120)
    yield dlg
    dlg.close()
    dlg.deleteLater()


# ---------------------------------------------------------------- Catálogo
class TestCatalogo:
    def test_preview_impresion_esta_registrado(self):
        nombres = [c["nombre"] for c in listar_componentes()]
        assert "preview_impresion" in nombres

    def test_obtener_componente_devuelve_la_clase(self):
        assert obtener_componente("preview_impresion") is PreviewImpresion

    def test_componente_no_registrado_lanza_keyerror(self):
        with pytest.raises(KeyError):
            obtener_componente("no_existe")


# ------------------------------------------------------------- Construcción
class TestConstruccion:
    def test_dialogo_se_construye_con_titulo(self, preview):
        assert preview.windowTitle() == "Reporte de prueba"

    def test_toolbar_tiene_pagina_y_orientacion(self, preview):
        assert preview.cmb_pagina.count() == len(mod.PAGINAS)
        assert preview.cmb_pagina.currentText() == "Carta (Letter)"
        assert preview.cmb_orientacion.currentText() == "Vertical"

    def test_sin_webengine_usa_fallback_y_avisa(self, preview):
        assert preview._wysiwyg is False
        assert preview._web is None
        assert preview._lbl_aviso.isVisible()

    def test_hoja_tiene_tamano_valido(self, preview):
        ancho, alto = (preview._hoja._contenido.width(),
                       preview._hoja._contenido.height())
        assert ancho > 200
        assert alto > ancho  # proporción vertical (1.414:1)

    def test_cambio_orientacion_recalcula_hoja(self, preview):
        ancho_v = preview._hoja._contenido.width()
        preview.cmb_orientacion.setCurrentText("Horizontal")
        preview._actualizar_hoja()
        ancho_h = preview._hoja._contenido.width()
        assert ancho_h > ancho_v


# -------------------------------------------------------------------- Zoom
class TestZoom:
    def test_zoom_in_aumenta_etiqueta_y_hoja(self, preview):
        antes = preview._hoja._contenido.width()
        preview._zoom_in()
        assert preview._btn_zoom.text() == "125%"
        assert preview._hoja._contenido.width() > antes

    def test_zoom_out_disminuye_etiqueta_y_hoja(self, preview):
        preview._zoom_in()
        preview._zoom_out()
        assert preview._btn_zoom.text() == "100%"

    def test_zoom_tiene_limites(self, preview):
        for _ in range(10):
            preview._zoom_in()
        assert preview._zoom == 2.0
        for _ in range(10):
            preview._zoom_out()
        assert preview._zoom == 0.5


# ------------------------------------------------------------- Impresión
class TestImpresion:
    def test_printer_aplica_pagina_y_orientacion(self, preview):
        preview.cmb_pagina.setCurrentText("A4")
        preview.cmb_orientacion.setCurrentText("Horizontal")
        printer = preview._printer()
        assert printer.pageLayout().pageSize().id() == QPageSize.A4
        assert printer.pageLayout().orientation() == QPageLayout.Landscape

    def test_printer_para_pdf_usa_formato_pdf(self, preview):
        printer = preview._printer(para_pdf=True)
        assert printer.outputFormat() == QPrinter.PdfFormat

    def test_renderizar_genera_pdf_valido(self, preview):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = os.path.join(tmp, "reporte.pdf")
            printer = preview._printer(para_pdf=True)
            printer.setOutputFileName(ruta)
            preview._renderizar(printer)
            assert os.path.exists(ruta)
            assert os.path.getsize(ruta) > 0


# -------------------------------------------------- previsualizar_html()
class TestPrevisualizarHtml:
    def test_previsualizar_html_abre_el_dialogo(self, qapp, sin_webengine,
                                                monkeypatch):
        abiertos = []

        class _Stub(PreviewImpresion):
            def exec(self):
                abiertos.append(True)
                return 1

        monkeypatch.setattr(mod, "PreviewImpresion", _Stub)
        previsualizar_html(HTML_PRUEBA, titulo="X")
        assert abiertos == [True]


# ------------------------------------------------------------------ Demos
class TestDemos:
    def test_reporte_oc_ejemplo_genera_html_valido(self):
        html = _reporte_oc_ejemplo_html()
        assert html.lstrip().startswith("<!DOCTYPE html>")
        assert "RECIBO DE COMPRA" in html
        assert "SIAC ERP" in html or "GORETTI" in html
        assert "Gracias por su compra" in html

    def test_reporte_inventario_genera_html(self):
        html = _reporte_inventario_html()
        assert "Reporte de Inventario" in html
        assert "<table" in html

    def test_demo_sandbox_construye(self, qapp):
        dlg = PreviewImpresionDemo()
        assert dlg.cmb_reporte.count() == 2
        dlg.close()
        dlg.deleteLater()
