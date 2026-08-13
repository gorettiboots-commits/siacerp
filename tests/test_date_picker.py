"""Pruebas del componente aprobado 'date_picker'.

Cubre:
    - Registro en el catálogo (regla C-02/C-07).
    - Formato de visualización dd/MM/yyyy y popup de calendario.
    - Conversión ISO para base de datos (fecha_bd / establecer_fecha_bd).

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest
from PySide6.QtCore import QDate

from src.components import listar_componentes, obtener_componente
from src.components.date_picker import DatePicker

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def picker(qapp):
    w = DatePicker(QDate(2026, 8, 12))
    yield w
    w.deleteLater()


# ------------------------------------------------- Catálogo
class TestCatalogo:
    def test_date_picker_esta_registrado(self):
        nombres = [c["nombre"] for c in listar_componentes()]
        assert "date_picker" in nombres

    def test_obtener_componente_devuelve_la_clase(self):
        assert obtener_componente("date_picker") is DatePicker


# ------------------------------------------------- Comportamiento
class TestDatePicker:
    def test_formato_vista_dd_mm_yyyy(self, picker):
        assert picker.displayFormat() == "dd/MM/yyyy"

    def test_calendario_emergente(self, picker):
        assert picker.calendarPopup()

    def test_fecha_bd_formato_iso(self, picker):
        assert picker.fecha_bd() == "2026-08-12"

    def test_establecer_fecha_bd_iso(self, picker):
        picker.establecer_fecha_bd("2026-01-31")
        assert picker.fecha_bd() == "2026-01-31"

    def test_establecer_fecha_bd_con_hora(self, picker):
        picker.establecer_fecha_bd("2026-02-15 14:30:00")
        assert picker.fecha_bd() == "2026-02-15"

    def test_establecer_fecha_bd_vacio_no_cambia(self, picker):
        picker.establecer_fecha_bd("")
        assert picker.fecha_bd() == "2026-08-12"

    def test_fecha_por_defecto_hoy(self, qapp):
        w = DatePicker()
        assert w.date() == QDate.currentDate()
        w.deleteLater()
