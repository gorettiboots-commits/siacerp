import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget


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
