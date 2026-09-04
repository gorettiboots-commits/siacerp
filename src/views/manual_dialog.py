"""
manual_dialog.py — Manual de Usuario navegable dentro del sistema.

Carga el HTML del manual web (manual/manual_usuario.html) en un
QTextBrowser, que renderiza el contenido exactamente igual a la version
web. La barra lateral permite navegar por secciones usando anchor links.
"""

import re
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QTextBrowser, QVBoxLayout, QWidget, QFrame,
)


# ── Colores del tema SIAC ──
_PRIMARY = "#2563eb"
_PRIMARY_DARK = "#1d4ed8"
_PRIMARY_LIGHT = "#dbeafe"
_GRAY_200 = "#e5e7eb"
_GRAY_500 = "#6b7280"
_GRAY_700 = "#374151"

# ── Estilos ──
_STYLE_SIDEBAR = f"""
    QListWidget {{
        background: white;
        border: none;
        border-right: 1px solid {_GRAY_200};
        font-size: 13px;
        padding: 4px 0;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 16px;
        border-left: 3px solid transparent;
        color: {_GRAY_700};
    }}
    QListWidget::item:hover {{
        background: {_PRIMARY_LIGHT};
        color: {_PRIMARY};
        border-left-color: {_PRIMARY};
    }}
    QListWidget::item:selected {{
        background: {_PRIMARY_LIGHT};
        color: {_PRIMARY_DARK};
        border-left-color: {_PRIMARY_DARK};
        font-weight: bold;
    }}
"""

# ── Secciones del manual (orden y claves anchor) ──
SECCIONES = [
    ("Inicio de Sesion", "inicio"),
    ("Dashboard", "dashboard"),
    ("Ordenes de Compra", "ordenes_compra"),
    ("Produccion", "produccion"),
    ("Inventario", "inventario"),
    ("Clientes y Pedidos", "clientes"),
    ("Programacion Semanal", "programacion"),
    ("Diagrama Gantt", "gantt"),
    ("Fichas Tecnicas", "fichas"),
    ("Configuracion", "configuracion"),
    ("Usuarios y Permisos", "usuarios"),
    ("Atajos de Teclado", "atajos"),
    ("Soporte", "soporte"),
]

_EMOJI = {
    "inicio": "\U0001f3e0",
    "dashboard": "\U0001f4ca",
    "ordenes_compra": "\U0001f6d2",
    "produccion": "\U0001f3ed",
    "inventario": "\U0001f4e6",
    "clientes": "\U0001f465",
    "programacion": "\U0001f4c5",
    "gantt": "\U0001f4c8",
    "fichas": "\U0001f4cb",
    "configuracion": "\u2699\ufe0f",
    "usuarios": "\U0001f510",
    "atajos": "\u2328\ufe0f",
    "soporte": "\U0001f4de",
}


def _encontrar_ruta_manual() -> Path | None:
    """Busca manual_usuario.html en varias ubicaciones posibles."""
    candidatas = [
        Path(__file__).resolve().parent.parent.parent / "manual" / "manual_usuario.html",
        Path(__file__).resolve().parent.parent / "manual" / "manual_usuario.html",
        Path(__file__).resolve().parent / "manual" / "manual_usuario.html",
        # Cuando esta empaquetado con PyInstaller
        Path(getattr(__import__("sys"), "frozen", False)
             and __import__("sys")._MEIPASS or __file__).parent.parent.parent
        / "manual" / "manual_usuario.html",
    ]
    for ruta in candidatas:
        if ruta.exists():
            return ruta
    return None


def _cargar_html_manual() -> str:
    """Carga el HTML completo del manual web."""
    ruta = _encontrar_ruta_manual()
    if ruta is None:
        return (
            "<html><body style='font-family:Segoe UI; padding:40px;'>"
            "<h2 style='color:#1d4ed8;'>Manual no encontrado</h2>"
            "<p>No se encontro el archivo manual_usuario.html.</p>"
            "</body></html>"
        )
    return ruta.read_text(encoding="utf-8")


def _extraer_seccion_del_html(html_completo: str, anchor: str) -> str:
    """Extrae una seccion del HTML buscando su id de anchor.
    Devuelve el HTML desde esa seccion hasta la siguiente."""
    # Buscar el div con id=anchor
    patron = r'<div\s+class="section"\s+id="' + re.escape(anchor) + r'"'
    match = re.search(patron, html_completo)
    if not match:
        # Buscar sin class="section" (portada usa id="portada")
        patron2 = r'id="' + re.escape(anchor) + r'"'
        match = re.search(patron2, html_completo)
    if not match:
        return ""
    inicio = match.start()
    # Buscar el siguiente id de seccion o el footer
    resto = html_completo[inicio:]
    # Buscar el siguiente <div class="section" id= o el footer
    siguiente = re.search(r'<div\s+class="section"\s+id="', resto[10:])
    if siguiente:
        fin = 10 + siguiente.start()
    else:
        # Buscar el footer
        footer = re.search(r'<div\s+style="text-align:center', resto)
        if footer:
            fin = footer.start()
        else:
            fin = len(resto)
    return resto[:fin]


def crear_boton_ayuda(seccion: str, color: str = "#6b7280") -> QPushButton:
    """Crea un boton "?" de ayuda contextual para una vista.

    Se coloca en el header de cada vista y abre el manual
    directamente en la seccion indicada.
    """
    btn = QPushButton("?")
    btn.setFixedSize(28, 28)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolTip(f"Ayuda: {seccion.replace('_', ' ').title()}")
    btn.setStyleSheet(
        f"QPushButton {{"
        f"  background: transparent; border: 1.5px solid {color};"
        f"  border-radius: 14px; color: {color}; font-size: 14px;"
        f"  font-weight: bold; padding: 0;"
        f"}}"
        f"QPushButton:hover {{"
        f"  background: {color}; color: white;"
        f"}}"
    )
    def _abrir():
        from PySide6.QtWidgets import QApplication
        parent = btn.window()
        dlg = ManualDialog(parent, seccion_inicial=seccion)
        dlg.exec()
    btn.clicked.connect(_abrir)
    return btn


class ManualDialog(QDialog):
    """Dialogo modal con manual de usuario navegable dentro del sistema.

    Renderiza el HTML del manual web en un QTextBrowser para garantizar
    que se ve identico a la version web.
    """

    def __init__(self, parent=None, seccion_inicial: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Manual de Usuario \u2014 SIAC ERP")
        self.setMinimumSize(960, 660)
        self.resize(1100, 740)
        self.setModal(True)
        self._seccion_inicial = seccion_inicial
        self._html_completo = _cargar_html_manual()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra lateral ──
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(260)
        sidebar_container.setStyleSheet(f"background:white;border-right:1px solid {_GRAY_200};")
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Titulo de la sidebar
        sidebar_header = QLabel("  Manual SIAC ERP")
        sidebar_header.setStyleSheet(
            f"padding:12px 16px;font-size:12px;font-weight:bold;"
            f"text-transform:uppercase;color:{_GRAY_500};letter-spacing:1px;"
            f"border-bottom:1px solid {_GRAY_200};"
        )
        sidebar_layout.addWidget(sidebar_header)

        self._sidebar = QListWidget()
        self._sidebar.setStyleSheet(_STYLE_SIDEBAR)
        self._sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._sidebar.currentRowChanged.connect(self._navegar_a)

        for titulo, anchor in SECCIONES:
            emoji = _EMOJI.get(anchor, "\U0001f4d6")
            item = QListWidgetItem(f"  {emoji}  {titulo}")
            item.setData(Qt.UserRole, anchor)
            self._sidebar.addItem(item)

        sidebar_layout.addWidget(self._sidebar, 1)

        layout.addWidget(sidebar_container)

        # ── Separador ──
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{_GRAY_200};")
        layout.addWidget(sep)

        # ── Area de contenido ──
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Barra superior
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet(f"background:white;border-bottom:1px solid {_GRAY_200};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self._titulo_label = QLabel("Inicio de Sesion")
        self._titulo_label.setStyleSheet(
            f"font-size:16px;font-weight:bold;color:{_PRIMARY_DARK};"
        )
        header_layout.addWidget(self._titulo_label)
        header_layout.addStretch()

        btnCerrar = QPushButton("Cerrar  (Esc)")
        btnCerrar.setFixedWidth(100)
        btnCerrar.setStyleSheet(
            f"QPushButton{{background:{_GRAY_200};border:1px solid {_GRAY_200};"
            f"border-radius:6px;padding:6px 12px;color:{_GRAY_700};}}"
            f"QPushButton:hover{{background:#cbd5e1;}}"
        )
        btnCerrar.clicked.connect(self.accept)
        header_layout.addWidget(btnCerrar)

        right_layout.addWidget(header)

        # QTextBrowser — renderiza HTML nativamente (igual que el navegador)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setReadOnly(True)
        # Inyectar CSS adicional para melhorar el renderizado en Qt
        self._browser.document().setDefaultStyleSheet(self._css_qt())
        right_layout.addWidget(self._browser, 1)

        layout.addLayout(right_layout, 1)

        # Seleccionar seccion inicial
        idx_inicial = 0
        if self._seccion_inicial:
            for i, (_, anchor) in enumerate(SECCIONES):
                if anchor == self._seccion_inicial:
                    idx_inicial = i
                    break
        self._sidebar.setCurrentRow(idx_inicial)

    def _css_qt(self) -> str:
        """CSS extra para mejorar el renderizado dentro de QTextBrowser.
        Solo usa propiedades soportadas por Qt's HTML engine."""
        return """
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #111827;
                line-height: 1.6;
                padding: 16px 20px;
            }
            h2 { color: #1d4ed8; font-size: 1.4em; margin: 16px 0 10px; padding-bottom: 6px; border-bottom: 2px solid #dbeafe; }
            h3 { color: #374151; font-size: 1.1em; margin: 14px 0 6px; }
            p { margin-bottom: 10px; color: #374151; }
            ul, ol { margin: 8px 0 8px 20px; }
            li { margin-bottom: 4px; color: #374151; }
            kbd { background: #f3f4f6; border: 1px solid #d1d5db; padding: 1px 6px; font-family: monospace; font-size: 0.9em; }
        """

    def _navegar_a(self, indice: int) -> None:
        """Cambia el contenido mostrado segun la seccion seleccionada."""
        if indice < 0 or indice >= len(SECCIONES):
            return
        titulo, anchor = SECCIONES[indice]
        emoji = _EMOJI.get(anchor, "\U0001f4d6")
        self._titulo_label.setText(f"{emoji}  {titulo}")

        # Si es la portada, mostrar el HTML completo con scroll al top
        if anchor == "inicio":
            # Mostrar portada + seccion de login
            html = self._html_completo
        else:
            # Extraer solo la seccion solicitada con su CSS
            seccion_html = _extraer_seccion_del_html(self._html_completo, anchor)
            if seccion_html:
                html = (
                    "<html><head><style>"
                    + self._css_qt()
                    + "</style></head><body>"
                    + seccion_html
                    + "</body></html>"
                )
            else:
                html = (
                    "<html><body style='padding:40px;'>"
                    f"<h2>Seccion no encontrada: {titulo}</h2>"
                    "</body></html>"
                )

        self._browser.setHtml(html)
        # Scroll al inicio
        sb = self._browser.verticalScrollBar()
        if sb:
            sb.setValue(0)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.accept()
        elif event.key() == Qt.Key_Down and self._sidebar.currentRow() < len(SECCIONES) - 1:
            self._sidebar.setCurrentRow(self._sidebar.currentRow() + 1)
        elif event.key() == Qt.Key_Up and self._sidebar.currentRow() > 0:
            self._sidebar.setCurrentRow(self._sidebar.currentRow() - 1)
        else:
            super().keyPressEvent(event)
