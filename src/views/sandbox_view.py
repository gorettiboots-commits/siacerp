from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.components.tallas_matrix import MatrizTallasDialog
from src.views.sandbox_complex_grid import ComplexGridDemo
from src.views.sandbox_controles import ControlesPreview
from src.views.sandbox_editor_etiqueta import EditorEtiquetaPreview
from src.views.sandbox_notificaciones import NotificacionesDemo
from src.views.sandbox_preview_impresion import PreviewImpresionDemo


class SandboxView(QWidget):
    """Área de pruebas para componentes propios del sistema (solo admin).

    Es una demo: los componentes aprobados viven en `src/components/` y se
    registran en el catálogo (`src.components.listar_componentes()`).
    """

    def __init__(self) -> None:
        super().__init__()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        titulo = QLabel("Sandbox")
        titulo.setObjectName("sectionTitle")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Área de pruebas para componentes propios del sistema.")
        subtitulo.setObjectName("sectionSubtitle")
        layout.addWidget(subtitulo)

        tabs = QTabWidget()
        tabs.addTab(self._crear_tab_componentes(), "Componentes")
        tabs.addTab(ControlesPreview(self), "Controles del sistema (prototipo)")
        tabs.addTab(EditorEtiquetaPreview(self), "Editor de etiquetas (prototipo)")
        layout.addWidget(tabs, 1)

    def _crear_tab_componentes(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        btn_tallas = QPushButton("Controles de tallas")
        btn_tallas.setObjectName("btnPrimary")
        btn_tallas.setMinimumHeight(42)
        btn_tallas.setCursor(Qt.PointingHandCursor)
        btn_tallas.clicked.connect(self._abrir_tallas)
        layout.addWidget(btn_tallas, 0, Qt.AlignLeft)

        btn_grid = QPushButton("ComplexGrid (prototipo)")
        btn_grid.setObjectName("btnSecondary")
        btn_grid.setMinimumHeight(42)
        btn_grid.setCursor(Qt.PointingHandCursor)
        btn_grid.clicked.connect(self._abrir_complex_grid)
        layout.addWidget(btn_grid, 0, Qt.AlignLeft)

        btn_notif = QPushButton("Notificaciones flotantes (prototipo)")
        btn_notif.setObjectName("btnSecondary")
        btn_notif.setMinimumHeight(42)
        btn_notif.setCursor(Qt.PointingHandCursor)
        btn_notif.clicked.connect(self._abrir_notificaciones)
        layout.addWidget(btn_notif, 0, Qt.AlignLeft)

        btn_preview = QPushButton("Preview de impresión")
        btn_preview.setObjectName("btnPrimary")
        btn_preview.setMinimumHeight(42)
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.clicked.connect(self._abrir_preview)
        layout.addWidget(btn_preview, 0, Qt.AlignLeft)

        layout.addStretch()
        return widget

    def _abrir_tallas(self) -> None:
        dlg = MatrizTallasDialog(parent=self)
        dlg.exec()

    def _abrir_complex_grid(self) -> None:
        dlg = ComplexGridDemo(parent=self)
        dlg.exec()

    def _abrir_notificaciones(self) -> None:
        dlg = NotificacionesDemo(parent=self)
        dlg.exec()

    def _abrir_preview(self) -> None:
        dlg = PreviewImpresionDemo(parent=self)
        dlg.exec()
