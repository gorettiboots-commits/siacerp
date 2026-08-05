from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_TILES = {
    "unidades": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#6366f1"/>
          <rect x="13" y="27" width="38" height="12" rx="2" fill="#ffffff"/>
          <path d="M19 27v5M26 27v8.5M33 27v5M40 27v8.5M47 27v5"
                stroke="#6366f1" stroke-width="2.2" stroke-linecap="round"/>
        </svg>""",
    "areas": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#ea580c"/>
          <path d="M46 21h5v11h-5z" fill="#ffffff"/>
          <path d="M13 34l6-11 6 11 8-11 6 11h4v12H13z" fill="#ffffff"/>
        </svg>""",
    "puntos": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#0d9488"/>
          <circle cx="23" cy="24" r="4.5" fill="#ffffff"/>
          <circle cx="41" cy="24" r="4.5" fill="#ffffff"/>
          <circle cx="23" cy="40" r="4.5" fill="#ffffff"/>
          <circle cx="41" cy="40" r="4.5" fill="#ffffff"/>
        </svg>""",
    "colores": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#e11d48"/>
          <path d="M31 14c-9.4 0-17 7.2-17 16.4 0 8.8 7.2 16 16.2 16h1.9c2.7 0 4.4-2 4.4-4.2 0-1.3-.5-2.2-1.3-3.1-.7-.9-1-1.7-1-2.7 0-2.3 1.9-4.2 4.2-4.2h3.5c5.2 0 8.2-3.9 8.2-9.8C50 19.9 41.6 14 31 14z" fill="#ffffff"/>
          <circle cx="23" cy="27" r="2.8" fill="#e11d48"/>
          <circle cx="32" cy="23" r="2.8" fill="#e11d48"/>
          <circle cx="41" cy="28" r="2.8" fill="#e11d48"/>
        </svg>""",
    "usuarios": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#2563eb"/>
          <circle cx="24" cy="25" r="8" fill="#ffffff"/>
          <path d="M11 46c.6-7.2 6-10 13-10s12.4 2.8 13 10"
                fill="none" stroke="#ffffff" stroke-width="3.4" stroke-linecap="round"/>
          <rect x="38" y="24" width="14" height="12" rx="3" fill="#ffffff"/>
          <path d="M42 24v-4a3 3 0 0 1 6 0v4"
                fill="none" stroke="#2563eb" stroke-width="2.4"/>
        </svg>""",
}

_GLIFOS = {
    "oc": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M22 10h20l10 10v34H22z" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M42 10v10h10" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M28 30h18M28 38h18M28 46h12" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "produccion": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="13" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <circle cx="32" cy="32" r="4" fill="#COLOR"/>
          <path d="M32 13v5M32 46v5M13 32h5M46 32h5M19.6 19.6l3.5 3.5M40.9 40.9l3.5 3.5M44.4 19.6l-3.5 3.5M23.1 40.9l-3.5 3.5"
                stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "inventario": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M16 24l16-8 16 8v18l-16 8-16-8z" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M16 24l16 8 16-8M32 32v18" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
        </svg>""",
    "logout": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M26 14H16a4 4 0 0 0-4 4v28a4 4 0 0 0 4 4h10"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M36 20l12 12-12 12M48 32H24"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
    "toggle": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M16 22h32M16 32h32M16 42h32" stroke="#COLOR" stroke-width="4.5" stroke-linecap="round"/>
        </svg>""",
    "editar": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M14 50l4.5-18.5L44.5 5.5a5 5 0 0 1 7 7L25.5 38.5 14 50z"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M40 10l10 10M14 50l10 2" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "eliminar": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M14 20h36M28 20v-6a4 4 0 0 1 4-4h0a4 4 0 0 1 4 4v6M22 20l2.5 32a4 4 0 0 0 4 3.6h7a4 4 0 0 0 4-3.6L42 20M27 28v16M37 28v16"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
}


def _render_svg(svg: str, size: int) -> QPixmap:
    scale = 2
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.setDevicePixelRatio(scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return pixmap


def tile_icon(key: str, size: int = 28) -> QIcon:
    icon = QIcon()
    icon.addPixmap(_render_svg(_TILES[key], size))
    return icon


def mono_icon(key: str, size: int = 24, color: str = "#cbd5e1") -> QIcon:
    icon = QIcon()
    icon.addPixmap(_render_svg(_GLIFOS[key].replace("#COLOR", color), size))
    return icon
