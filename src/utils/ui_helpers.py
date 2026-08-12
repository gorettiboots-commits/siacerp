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
