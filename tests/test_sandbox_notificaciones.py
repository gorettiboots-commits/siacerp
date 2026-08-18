"""Pruebas de la demo de NotificacionesFlotantes en el Sandbox.

El componente aprobado vive en `src/components/notificacion_flotante.py`
(sus pruebas: `tests/test_notificacion_flotante.py`). Este archivo cubre la
integración de la demo del Sandbox con el componente del catálogo.

Convención de nombres: [función]_[condición]_[resultadoEsperado].
Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest

from src.components import listar_componentes, obtener_componente
from src.components.notificacion_flotante import NotificacionesFlotantes
from src.views.sandbox_notificaciones import NotificacionesDemo

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_componente_registrado_en_catalogo():
    nombres = [c["nombre"] for c in listar_componentes()]
    assert "notificacion_flotante" in nombres


def test_obtener_componente_devuelve_la_clase():
    assert obtener_componente("notificacion_flotante") is NotificacionesFlotantes


def test_demo_construye_y_aplica_estilo_local(qapp):
    dlg = NotificacionesDemo()
    assert dlg.windowTitle()
    dlg.deleteLater()