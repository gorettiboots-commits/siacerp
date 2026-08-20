"""Pruebas del componente MatrizPreviewWidget (vista previa read-only).

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest

from src.components.matriz_preview import MatrizPreviewWidget

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


_DATOS = {
    "corrida": "del 22 al 25",
    "pares": {"22": 10, "23": 12, "24": 8, "25": 0},
}


class TestMatrizPreviewWidget:
    def test_crea_widget_con_datos(self, qapp):
        w = MatrizPreviewWidget(_DATOS)
        assert w is not None
        w.deleteLater()

    def test_muestra_corrida(self, qapp):
        w = MatrizPreviewWidget(_DATOS)
        labels = w.findChildren(type(w).__mro__[0])
        from PySide6.QtWidgets import QLabel
        lbls = w.findChildren(QLabel)
        textos = [l.text() for l in lbls]
        assert "del 22 al 25" in textos
        w.deleteLater()

    def test_muestra_total(self, qapp):
        w = MatrizPreviewWidget(_DATOS)
        from PySide6.QtWidgets import QLabel
        lbls = w.findChildren(QLabel)
        textos = [l.text() for l in lbls]
        assert any("30" in t for t in textos)
        w.deleteLater()

    def test_tabla_dimensiones(self, qapp):
        w = MatrizPreviewWidget(_DATOS)
        from PySide6.QtWidgets import QTableWidget
        tablas = w.findChildren(QTableWidget)
        assert len(tablas) == 1
        tabla = tablas[0]
        assert tabla.rowCount() == 2
        assert tabla.columnCount() == 4
        w.deleteLater()

    def test_sin_datos_muestra_mensaje(self, qapp):
        w = MatrizPreviewWidget({"corrida": "sin datos", "pares": {}})
        from PySide6.QtWidgets import QLabel
        lbls = w.findChildren(QLabel)
        textos = [l.text() for l in lbls]
        assert any("Sin datos" in t for t in textos)
        w.deleteLater()

    def test_sin_corrida_no_muestra_label_superior(self, qapp):
        w = MatrizPreviewWidget({"pares": {"22": 5}})
        from PySide6.QtWidgets import QLabel, QTableWidget
        tablas = w.findChildren(QTableWidget)
        assert len(tablas) == 1
        assert tablas[0].columnCount() == 1
        w.deleteLater()

    def test_mas_de_11_tallas_multiples_bloques(self, qapp):
        pares = {f"{i}": i * 2 for i in range(15)}
        w = MatrizPreviewWidget({"corrida": "del 0 al 14", "pares": pares})
        from PySide6.QtWidgets import QTableWidget
        tablas = w.findChildren(QTableWidget)
        assert len(tablas) == 2
        assert tablas[0].columnCount() == 11
        assert tablas[1].columnCount() == 4
        w.deleteLater()
