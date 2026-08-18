"""Demo del componente aprobado: NotificacionesFlotantes.

El componente aprobado vive en `src/components/notificacion_flotante.py` y se
registra en el catálogo (`src.components.listar_componentes()` → "notificacion_flotante").
Este archivo es solo una demo que usa el componente aprobado.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from src.components.notificacion_flotante import notificar_flotante


class NotificacionesDemo(QDialog):
    """Demo del componente de notificaciones flotantes."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Notificaciones flotantes — componente aprobado")
        self.resize(520, 340)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        titulo = QLabel("Notificaciones flotantes (componente aprobado)")
        titulo.setObjectName("sectionTitle")
        titulo.setWordWrap(True)
        lay.addWidget(titulo)

        subtitulo = QLabel(
            "Tarjetas que se apilan en la esquina, con cierre automático o "
            "manual, animación y callback al hacer clic.")
        subtitulo.setObjectName("sectionSubtitle")
        subtitulo.setWordWrap(True)
        lay.addWidget(subtitulo)

        def _btn(texto, fn):
            btn = QPushButton(texto)
            btn.setObjectName("btnSecondary")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(fn)
            return btn

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.addWidget(_btn("Info", self._demo_info), 0, 0)
        grid.addWidget(_btn("Éxito", self._demo_ok), 0, 1)
        grid.addWidget(_btn("Advertencia", self._demo_warning), 0, 2)
        grid.addWidget(_btn("Error", self._demo_error), 1, 0)
        grid.addWidget(_btn("Pila (5)", self._demo_pila), 1, 1)
        grid.addWidget(_btn("Con clic", self._demo_clic), 1, 2)
        lay.addLayout(grid)

        esquina_label = QLabel("Esquina de apilado:")
        esquina_label.setObjectName("sectionSubtitle")
        lay.addWidget(esquina_label)

        grid2 = QGridLayout()
        grid2.setSpacing(8)
        corners = [
            ("Arriba-der.", "tr"), ("Abajo-der.", "br"),
            ("Arriba-izq.", "tl"), ("Abajo-izq.", "bl"),
        ]
        for i, (texto, esquina) in enumerate(corners):
            btn = _btn(texto, lambda _c, e=esquina: notificar_flotante(
                f"Esquina {e}", tipo="info", titulo="Posición",
                host=self, esquina=e, duracion=3.0))
            grid2.addWidget(btn, i // 2, i % 2)
        lay.addLayout(grid2)
        lay.addStretch()

        bar = QHBoxLayout()
        bar.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnPrimary")
        btn_cerrar.clicked.connect(self.accept)
        bar.addWidget(btn_cerrar)
        lay.addLayout(bar)

    def _demo_info(self) -> None:
        notificar_flotante("Base de datos sincronizada correctamente.",
                           tipo="info", titulo="Sincronización", host=self)

    def _demo_ok(self) -> None:
        notificar_flotante("El documento OC-0001 se guardó sin errores.",
                           tipo="success", titulo="Inventario", host=self)

    def _demo_warning(self) -> None:
        notificar_flotante("Hay 12 insumos por debajo del stock mínimo.",
                           tipo="warning", titulo="Stock bajo", host=self)

    def _demo_error(self) -> None:
        notificar_flotante("No se pudo exportar el reporte. Verifique la ruta.",
                           tipo="error", titulo="Exportación", host=self)

    def _demo_pila(self) -> None:
        for i in range(1, 6):
            notificar_flotante(f"Mensaje apilado número {i} de 5.",
                               tipo="info" if i % 2 else "warning",
                               titulo=f"Pila #{i}", duracion=6.0, host=self)

    def _demo_clic(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        notificar_flotante("Haz clic sobre esta notificación.",
                           tipo="success", titulo="Interactiva",
                           duracion=0, host=self,
                           on_click=lambda: QMessageBox.information(
                               self, "Clic", "¡Notificación clickeable!"))
