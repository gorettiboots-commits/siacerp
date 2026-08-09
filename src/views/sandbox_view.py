from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.components.tallas_matrix import MatrizTallasDialog


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

        btn_tallas = QPushButton("Controles de tallas")
        btn_tallas.setObjectName("btnPrimary")
        btn_tallas.setMinimumHeight(42)
        btn_tallas.setCursor(Qt.PointingHandCursor)
        btn_tallas.clicked.connect(self._abrir_tallas)
        layout.addWidget(btn_tallas, 0, Qt.AlignLeft)

        layout.addStretch()

    def _abrir_tallas(self) -> None:
        dlg = MatrizTallasDialog(parent=self)
        dlg.exec()
