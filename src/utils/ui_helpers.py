import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QCompleter, QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)


class SearchableComboBox(QComboBox):
    """ComboBox editable con búsqueda inline: filtra las opciones al escribir
    y permite capturar un valor nuevo si ninguna opción coincide."""

    def __init__(self, parent: QWidget | None = None,
                 placeholder: str = "Buscar…") -> None:
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setMaxVisibleItems(12)
        self.lineEdit().setPlaceholderText(placeholder)
        self._completer = QCompleter(self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setModel(self.model())
        self.setCompleter(self._completer)
        self._completer.activated.connect(self._on_completer_activated)

    def _on_completer_activated(self, text: str) -> None:
        idx = self.findText(text, Qt.MatchFixedString)
        if idx >= 0:
            self.setCurrentIndex(idx)

    def set_items(self, items) -> None:
        self.clear()
        for it in items:
            self.addItem(str(it))

    def set_current_data(self, data) -> None:
        idx = self.findData(data)
        if idx >= 0:
            self.setCurrentIndex(idx)


def load_styles() -> str:
    path = Path(__file__).resolve().parent / "styles.qss"
    if path.exists():
        with open(str(path), "r", encoding="utf-8") as f:
            text = f.read()
        assets = Path(__file__).resolve().parent.parent / "views" / "assets"
        return text.replace("@ASSETS@", assets.as_posix())
    return ""


def crear_tarjeta(titulo: str, valor: str, color: str = "#4f46e5") -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    # El fondo/borde/radio lo define styles.qss (QFrame#card): aquí solo
    # se mantienen los estilos tipográficos de los textos.

    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(10)

    lbl_titulo = QLabel(titulo)
    lbl_titulo.setObjectName("cardTitle")
    lbl_titulo.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")

    lbl_valor = QLabel(valor)
    lbl_valor.setObjectName("cardValue")
    lbl_valor.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color};")

    layout.addWidget(lbl_titulo)
    layout.addWidget(lbl_valor)

    return card


def crear_boton(texto: str, object_name: str = "btnPrimary",
                icono: str | None = None) -> QPushButton:
    btn = QPushButton(texto)
    btn.setObjectName(object_name)
    btn.setMinimumHeight(38)
    if icono:
        btn.setText(f"{icono}  {texto}")
    return btn


def crear_seccion(titulo: str, subtitulo: str = "") -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 16)

    lbl_titulo = QLabel(titulo)
    lbl_titulo.setObjectName("sectionTitle")

    layout.addWidget(lbl_titulo)

    if subtitulo:
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setObjectName("sectionSubtitle")
        layout.addWidget(lbl_sub)

    return container


def crear_header(titulo: str, parent: QWidget | None = None) -> QFrame:
    header = QFrame(parent)
    header.setObjectName("headerBar")
    # El fondo/borde lo define styles.qss (QFrame#headerBar).
    layout = QHBoxLayout(header)
    layout.setContentsMargins(24, 18, 24, 18)

    lbl = QLabel(titulo)
    lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b;")

    layout.addWidget(lbl)
    layout.addStretch()

    return header


def obtener_geometria_pantalla(widget: QWidget | None = None):
    """Devuelve la geometría disponible (ancho y alto utilizable sin barra de tareas)."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QGuiApplication
    
    screen = None
    if widget is not None:
        try:
            window = widget.window()
            if window and window.windowHandle():
                screen = window.windowHandle().screen()
        except Exception:
            screen = None

    if screen is None:
        screen = QGuiApplication.primaryScreen()

    if screen is not None:
        return screen.availableGeometry()

    app = QApplication.instance()
    if app and app.primaryScreen():
        return app.primaryScreen().availableGeometry()

    from PySide6.QtCore import QRect
    return QRect(0, 0, 1366, 768)


def adaptar_dialogo_a_pantalla(dialog: QWidget, factor_ancho: float = 0.95, factor_alto: float = 0.92) -> None:
    """Calcula la resolución disponible y limita el tamaño del formulario/diálogo para que nada se salga."""
    geom = obtener_geometria_pantalla(dialog)
    max_w = int(geom.width() * factor_ancho)
    max_h = int(geom.height() * factor_alto)

    # Restringir tamaño máximo al área segura de la pantalla
    dialog.setMaximumSize(max_w, max_h)

    # Si el tamaño actual o mínimo excede la pantalla, ajustarlo proporcionalmente
    w = min(dialog.width(), max_w)
    h = min(dialog.height(), max_h)

    min_w = min(dialog.minimumWidth(), max_w)
    min_h = min(dialog.minimumHeight(), max_h)
    dialog.setMinimumSize(min_w, min_h)
    dialog.resize(w, h)


def instalar_adaptador_resolucion_global() -> None:
    """Instala un hook global en QDialog para autoajustar y centrar cualquier formulario antes de pintarse."""
    from PySide6.QtWidgets import QDialog

    orig_show_event = QDialog.showEvent

    def _show_event_adaptado(self, event):
        try:
            adaptar_dialogo_a_pantalla(self)
        except Exception:
            pass
        return orig_show_event(self, event)

    QDialog.showEvent = _show_event_adaptado

