import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture(scope="session", autouse=True)
def _apagado_qt_sin_segfault(qapp):
    """Detiene timers y destruye widgets antes de que el intérprete cierre.

    Evita el segfault (exit 139) de PySide6 al finalizar la sesión: los
    QTimer de cierre automático aún activos y los widgets vivos provocan que
    shiboken destruya objetos C++ en mal orden durante el shutdown.
    """
    yield
    app = QApplication.instance()
    if app is None:
        return
    QApplication.processEvents()
    for w in list(QApplication.topLevelWidgets()):
        w.close()
    for w in list(QApplication.allWidgets()):
        w.deleteLater()
    QApplication.sendPostedEvents(None, 0)
    QApplication.processEvents()
    app.quit()
