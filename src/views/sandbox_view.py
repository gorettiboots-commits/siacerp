from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QPushButton, QScrollArea, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.components import listar_componentes
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

        label_cat = QLabel("Catálogo de componentes aprobados del sistema")
        label_cat.setObjectName("sectionSubtitle")
        layout.addWidget(label_cat)

        scroll = QScrollArea(widget)
        scroll.setWidgetResizable(True)
        cont = QWidget()
        grid = QGridLayout(cont)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setSpacing(10)

        componentes = listar_componentes()
        if not componentes:
            grid.addWidget(QLabel("No hay componentes registrados."), 0, 0)
        for i, comp in enumerate(componentes):
            grid.addWidget(self._crear_tarjeta_componente(comp), i // 2, i % 2)

        scroll.setWidget(cont)
        layout.addWidget(scroll, 1)

        label_demo = QLabel("Prototipos de demostración")
        label_demo.setObjectName("sectionSubtitle")
        layout.addWidget(label_demo)

        btn_tallas = QPushButton("Matriz de tallas (probar)")
        btn_tallas.setObjectName("btnPrimary")
        btn_tallas.setMinimumHeight(38)
        btn_tallas.setCursor(Qt.PointingHandCursor)
        btn_tallas.clicked.connect(self._abrir_tallas)
        layout.addWidget(btn_tallas, 0, Qt.AlignLeft)

        btn_grid = QPushButton("ComplexGrid (probar)")
        btn_grid.setObjectName("btnSecondary")
        btn_grid.setMinimumHeight(38)
        btn_grid.setCursor(Qt.PointingHandCursor)
        btn_grid.clicked.connect(self._abrir_complex_grid)
        layout.addWidget(btn_grid, 0, Qt.AlignLeft)

        btn_notif = QPushButton("Notificaciones flotantes (probar)")
        btn_notif.setObjectName("btnSecondary")
        btn_notif.setMinimumHeight(38)
        btn_notif.setCursor(Qt.PointingHandCursor)
        btn_notif.clicked.connect(self._abrir_notificaciones)
        layout.addWidget(btn_notif, 0, Qt.AlignLeft)

        btn_preview = QPushButton("Preview de impresión (probar)")
        btn_preview.setObjectName("btnPrimary")
        btn_preview.setMinimumHeight(38)
        btn_preview.setCursor(Qt.PointingHandCursor)
        btn_preview.clicked.connect(self._abrir_preview)
        layout.addWidget(btn_preview, 0, Qt.AlignLeft)

        return widget

    def _crear_tarjeta_componente(self, comp: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        nombre = QLabel(comp["nombre"])
        nombre.setObjectName("sectionTitle")
        layout.addWidget(nombre)

        desc = QLabel(comp["descripcion"])
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()
        return card

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
