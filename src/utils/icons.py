from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_TILES = {
    "empresa": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#7c3aed"/>
          <path d="M20 44V22a2 2 0 0 1 2-2h20a2 2 0 0 1 2 2v22"
                fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"/>
          <path d="M16 44h32" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
          <rect x="28" y="14" width="8" height="6" rx="1" fill="#ffffff"/>
          <path d="M28 32h8M28 38h8" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round"/>
        </svg>""",
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
    "tallas": """
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
    "oc": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#4f46e5"/>
          <path d="M24 16h14l8 8v22a2 2 0 0 1-2 2H24a2 2 0 0 1-2-2V18a2 2 0 0 1 2-2z"
                fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"/>
          <path d="M38 16v8h8M27 34h14M27 41h10"
                stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
        </svg>""",
    "produccion": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#0d9488"/>
          <circle cx="32" cy="32" r="9" fill="none" stroke="#ffffff" stroke-width="3"/>
          <circle cx="32" cy="32" r="3" fill="#ffffff"/>
          <path d="M32 17v6M32 41v6M17 32h6M41 32h6M22.6 22.6l4.2 4.2M37.2 37.2l4.2 4.2M41.4 22.6l-4.2 4.2M26.8 37.2l-4.2 4.2"
                stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
        </svg>""",
    "inventario": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#ea580c"/>
          <path d="M20 24l12-6 12 6v16l-12 6-12-6z" fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"/>
          <path d="M20 24l12 6 12-6M32 30v16" fill="none" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"/>
        </svg>""",
    "logs": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#7c3aed"/>
          <path d="M20 24l-6 8 6 8M44 24l6 8-6 8" fill="none"
                stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M37 16l-8 32" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "impresion": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#0891b2"/>
          <rect x="18" y="30" width="28" height="18" rx="3" fill="none" stroke="#ffffff" stroke-width="3"/>
          <rect x="24" y="15" width="16" height="13" fill="none" stroke="#ffffff" stroke-width="3"/>
          <path d="M24 30v8h16v-8M26 38v8h12v-8" fill="#0891b2" stroke="#ffffff" stroke-width="3"/>
        </svg>""",
    "basedatos": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="4" y="4" width="56" height="56" rx="14" fill="#0f766e"/>
          <ellipse cx="32" cy="19" rx="15" ry="6" fill="none" stroke="#ffffff" stroke-width="3"/>
          <path d="M17 19v26c0 3.3 6.7 6 15 6s15-2.7 15-6V19"
                fill="none" stroke="#ffffff" stroke-width="3"/>
          <path d="M17 32c0 3.3 6.7 6 15 6s15-2.7 15-6"
                fill="none" stroke="#ffffff" stroke-width="3"/>
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
    "clientes": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M14 28h36l-4 26H18z" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M14 28L19 12h26l5 16" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M24 54v-16h16v16" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M24 34c2-6 14-6 16 0" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "programacion": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="12" y="10" width="40" height="46" rx="6" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M12 24h40" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M22 10v8M42 10v8" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
          <path d="M22 32h4M30 32h4M38 32h4M22 40h4M30 40h4M38 40h4" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
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
    "filas": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="8" y="12" width="48" height="40" rx="5" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M8 23h48M24 12v40M40 12v40" fill="none" stroke="#COLOR" stroke-width="2.6"/>
        </svg>""",
    "lista": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="12" cy="18" r="2.8" fill="#COLOR"/>
          <circle cx="12" cy="32" r="2.8" fill="#COLOR"/>
          <circle cx="12" cy="46" r="2.8" fill="#COLOR"/>
          <path d="M22 18h32M22 32h32M22 46h32" stroke="#COLOR" stroke-width="4" stroke-linecap="round"/>
        </svg>""",
    "tabla": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="12" y="12" width="40" height="40" rx="4" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M12 24h40M12 38h40M24 12v40M38 12v40" stroke="#COLOR" stroke-width="3.5"/>
        </svg>""",
    "iconos": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="12" y="12" width="18" height="18" rx="4" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="34" y="12" width="18" height="18" rx="4" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="12" y="34" width="18" height="18" rx="4" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="34" y="34" width="18" height="18" rx="4" fill="none" stroke="#COLOR" stroke-width="3.5"/>
        </svg>""",
    "sandbox": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M10 18h44M16 18v8a16 16 0 0 0 32 0v-8M14 50h36" fill="none"
                stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M24 18v6a8 8 0 0 0 16 0v-6M28 38l8 8M28 46l8-8" fill="none"
                stroke="#COLOR" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
    "buscar": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="27" cy="27" r="13" fill="none" stroke="#COLOR" stroke-width="4"/>
          <path d="M37 37l14 14" stroke="#COLOR" stroke-width="4" stroke-linecap="round"/>
        </svg>""",
    "exportar": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M14 36v14a4 4 0 0 0 4 4h28a4 4 0 0 0 4-4V36M32 8v30M20 26l12 12 12-12"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
    "pdf": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M20 10h16l10 10v34H20z" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M36 10v10h10M26 32h14M26 40h14M26 48h9" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round"/>
        </svg>""",
    "imprimir": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M20 20V8h24v12M20 48h-6a4 4 0 0 1-4-4V28a6 6 0 0 1 6-6h28a6 6 0 0 1 6 6v16a4 4 0 0 1-4 4h-6"
                fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
          <rect x="22" y="38" width="20" height="16" rx="2" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M46 24a2 2 0 1 1 0 .1" stroke="#COLOR" stroke-width="3.5"/>
        </svg>""",
    "ver": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M8 32s9-16 24-16 24 16 24 16-9 16-24 16S8 32 8 32z" fill="none"
                stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <circle cx="32" cy="32" r="7" fill="none" stroke="#COLOR" stroke-width="3.5"/>
        </svg>""",
    "mas": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M32 14v36M14 32h36" stroke="#COLOR" stroke-width="4.5" stroke-linecap="round"/>
        </svg>""",
    "dashboard": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="10" y="10" width="20" height="16" rx="3" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="34" y="10" width="20" height="28" rx="3" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="10" y="30" width="20" height="24" rx="3" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <rect x="34" y="42" width="20" height="12" rx="3" fill="none" stroke="#COLOR" stroke-width="3.5"/>
        </svg>""",
    "info": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="20" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M32 28v14M32 21v.01" stroke="#COLOR" stroke-width="4.5" stroke-linecap="round"/>
        </svg>""",
    "ok": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="20" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M23 33l7 7 13-15" fill="none" stroke="#COLOR" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
    "alerta": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <path d="M32 12l22 38H10z" fill="none" stroke="#COLOR" stroke-width="3.5" stroke-linejoin="round"/>
          <path d="M32 30v14M32 50v.01" stroke="#COLOR" stroke-width="4.5" stroke-linecap="round"/>
        </svg>""",
    "error": """
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="20" fill="none" stroke="#COLOR" stroke-width="3.5"/>
          <path d="M24 24l16 16M40 24L24 40" stroke="#COLOR" stroke-width="4" stroke-linecap="round"/>
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


def _cuerpo_svg(svg: str) -> str:
    """Extrae el contenido interno de un SVG (sin el wrapper <svg>...</svg>)."""
    inicio = svg.find(">") + 1
    fin = svg.rfind("</svg>")
    if inicio == 0 or fin == -1:
        return svg
    return svg[inicio:fin]


def tile_icon_color(key: str, size: int = 16, color: str = "#4f46e5") -> QIcon:
    """Tile de acción: glifo blanco sobre rectángulo de fondo con el color dado."""
    glifo = _GLIFOS.get(key, _GLIFOS["mas"])
    cuerpo = _cuerpo_svg(glifo).replace("#COLOR", "#ffffff")
    svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
          <rect x="2" y="2" width="60" height="60" rx="14" fill="{color}"/>
          {cuerpo}
        </svg>"""
    icon = QIcon()
    icon.addPixmap(_render_svg(svg, size))
    return icon


def mono_icon(key: str, size: int = 24, color: str = "#cbd5e1") -> QIcon:
    icon = QIcon()
    icon.addPixmap(_render_svg(_GLIFOS[key].replace("#COLOR", color), size))
    return icon
