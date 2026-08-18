"""Pruebas unitarias del componente aprobado 'matriz_tallas'.

Convención de nombres: [función]_[condición]_[resultadoEsperado].
Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import pytest
from src.components import listar_componentes, obtener_componente
from src.components.tallas_matrix import MatrizTallasDialog

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

TALLAS = [
    {"id": 1, "talla": "15"},
    {"id": 2, "talla": "15.5"},
    {"id": 3, "talla": "16"},
    {"id": 4, "talla": "17"},
]


def _dialogo(precios: bool = False) -> MatrizTallasDialog:
    dlg = MatrizTallasDialog(tallas=list(TALLAS), titulo="MATRIZ", con_precios=precios)
    dlg.show()
    return dlg


# ---------------------------------------------------------------- Catálogo
class TestCatalogo:
    def test_matriz_tallas_esta_registrado(self):
        nombres = [c["nombre"] for c in listar_componentes()]
        assert "matriz_tallas" in nombres

    def test_obtener_componente_devuelve_la_clase(self):
        assert obtener_componente("matriz_tallas") is MatrizTallasDialog


# ----------------------------------------------------------- Sin precios
class TestModoSinPrecios:
    def test_sin_precios_no_crea_celdas_de_precio(self, qapp):
        dlg = _dialogo(precios=False)
        assert len(dlg.celdas) == len(TALLAS)
        assert len(dlg.celdas_precios) == 0
        dlg.close()
        dlg.deleteLater()

    def test_establecer_y_obtener_valores(self, qapp):
        dlg = _dialogo(precios=False)
        dlg.establecer_valores({"1": 6, "2": 4})
        valores = dlg.obtener_valores()
        assert valores["1"] == 6
        assert valores["2"] == 4
        assert valores["3"] == 0
        assert "Total de pares: 10" in dlg.lbl_total.text()
        dlg.close()
        dlg.deleteLater()


# ---------------------------------------------------------- Con precios
class TestModoConPrecios:
    def test_con_precios_crea_celdas_de_precio(self, qapp):
        dlg = _dialogo(precios=True)
        assert len(dlg.celdas) == len(TALLAS)
        assert len(dlg.celdas_precios) == len(TALLAS)
        dlg.close()
        dlg.deleteLater()

    def test_establecer_y_obtener_precios(self, qapp):
        dlg = _dialogo(precios=True)
        dlg.establecer_precios({"1": 25.5, "2": 30.0})
        precios = dlg.obtener_precios()
        assert precios["1"] == 25.5
        assert precios["2"] == 30.0
        assert precios["3"] == 0.0
        dlg.close()
        dlg.deleteLater()

    def test_total_muestra_pares_e_importe(self, qapp):
        dlg = _dialogo(precios=True)
        dlg.celdas["1"].setText("6")
        dlg.celdas["2"].setText("4")
        dlg.celdas_precios["1"].setText("25.5")
        dlg.celdas_precios["2"].setText("30.0")
        texto = dlg.lbl_total.text()
        assert "Total de pares: 10" in texto
        # 6*25.5 + 4*30.0 = 153 + 120 = 273
        assert "$273.00" in texto
        dlg.close()
        dlg.deleteLater()

    def test_limpiar_vacia_pares_y_precios(self, qapp):
        dlg = _dialogo(precios=True)
        dlg.celdas["1"].setText("6")
        dlg.celdas_precios["1"].setText("25.5")
        dlg._limpiar_tallas()
        assert dlg.obtener_valores()["1"] == 0
        assert dlg.obtener_precios()["1"] == 0.0
        dlg.close()
        dlg.deleteLater()

    def test_entero_en_celda_de_precio_se_interpreta_como_decimal(self, qapp):
        dlg = _dialogo(precios=True)
        dlg.celdas_precios["1"].setText("25")
        assert dlg.obtener_precios()["1"] == 25.0
        dlg.close()
        dlg.deleteLater()

    def test_con_precios_etiqueta_las_filas(self, qapp):
        dlg = _dialogo(precios=True)
        tabla = dlg.tabla
        assert tabla.cellWidget(0, 0).text() == "TALLA"
        assert tabla.cellWidget(1, 0).text() == "PARES"
        assert tabla.cellWidget(2, 0).text() == "PRECIO ($)"
        dlg.close()
        dlg.deleteLater()

    def test_con_precios_celda_de_precio_tiene_prefijo_moneda(self, qapp):
        from PySide6.QtWidgets import QLabel
        dlg = _dialogo(precios=True)
        contenedor = dlg.tabla.cellWidget(2, 1)  # fila precio, primer talla
        textos = [l.text() for l in contenedor.findChildren(QLabel)]
        assert "$" in textos
        dlg.close()
        dlg.deleteLater()

    def test_sin_precios_no_agrega_columna_de_etiquetas(self, qapp):
        dlg = _dialogo(precios=False)
        # Solo las columnas de tallas (COLUMNAS = 11), sin columna de etiquetas.
        assert dlg.tabla.columnCount() == 11
        dlg.close()
        dlg.deleteLater()

    def test_con_precios_agrega_columna_de_etiquetas(self, qapp):
        dlg = _dialogo(precios=True)
        # 11 columnas de tallas + 1 columna de etiquetas de fila.
        assert dlg.tabla.columnCount() == 12
        dlg.close()
        dlg.deleteLater()

    def test_enter_navega_a_la_siguiente_celda_de_precio(self, qapp):
        dlg = _dialogo(precios=True)
        primera = dlg.celdas_precios["1"]
        segunda = dlg.celdas_precios["2"]
        primera.setFocus()
        # Sin bucle de eventos activo, el foco no se asienta hasta procesar
        # los eventos pendientes (artefacto de pruebas headless).
        QApplication.processEvents()
        QTest.keyClick(primera, Qt.Key_Tab)
        assert segunda.hasFocus()
        dlg.close()
        dlg.deleteLater()

    def test_backtab_navega_a_la_celda_de_precio_anterior(self, qapp):
        dlg = _dialogo(precios=True)
        segunda = dlg.celdas_precios["2"]
        primera = dlg.celdas_precios["1"]
        segunda.setFocus()
        QApplication.processEvents()
        QTest.keyClick(segunda, Qt.Key_Backtab)
        assert primera.hasFocus()
        dlg.close()
        dlg.deleteLater()
