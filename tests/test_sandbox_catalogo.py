"""Pruebas de la demo del catálogo de controles en el Sandbox.

Cubre la construcción de `CatalogoControles` (`src/views/sandbox_catalogo.py`)
que muestra todos los widgets y componentes disponibles del sistema.

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest

from src.views.sandbox_catalogo import CatalogoControles

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_catalogo_construye_correctamente(qapp):
    cat = CatalogoControles()
    assert cat is not None
    cat.deleteLater()


def test_catalogo_incluye_grupos_de_controles(qapp):
    cat = CatalogoControles()
    titulos = [g.title() for g in cat.findChildren(object) if hasattr(g, "title")]
    titulos = [t for t in titulos if t]
    for esperado in ("Entradas de texto", "Selección y numéricos", "Botones",
                     "Marcas (QCheckBox y QRadioButton)",
                     "Contenedores y agrupación",
                     "Tablas y listados", "Componentes aprobados del catálogo",
                     "Galería de iconos"):
        assert any(t.startswith(esperado) for t in titulos), \
            f"Falta la sección: {esperado}"
    cat.deleteLater()


def test_catalogo_instancia_componentes_en_vivo(qapp):
    from src.components.campo_historico import CampoHistorico
    from src.components.date_picker import DatePicker
    from src.components.tallas_matrix import MatrizTallasWidget
    from src.utils.odoo_list import OdooListView
    from src.utils.ui_helpers import SearchableComboBox

    cat = CatalogoControles()
    assert cat.findChildren(CampoHistorico)
    assert cat.findChildren(DatePicker)
    assert cat.findChildren(MatrizTallasWidget)
    assert cat.findChildren(OdooListView)
    assert cat.findChildren(SearchableComboBox)
    cat.deleteLater()
