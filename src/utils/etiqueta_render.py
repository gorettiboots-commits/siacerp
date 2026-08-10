"""Renderizado de etiquetas 76x51 mm sobre QPainter (impresión y vista previa).

Replica el diseño de 'etiquetaa.qdf.qdf' (Label Matrix): un rectángulo de
borde y campos de texto Arial. El diseño se edita desde la app y se guarda
en la tabla etiqueta_config.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QImage, QPainter, QPen, QPixmap

_MARGEN_MM = 2.5
_TEXTO_ALTO_MM = 7.0


def _valor_campo(campo: dict, datos: dict) -> str:
    if campo.get("tipo") == "texto":
        return str(campo.get("texto", ""))
    if campo.get("tipo") == "dato":
        v = datos.get(campo.get("dato", ""))
        return "" if v in (None, "") else str(v)
    return ""


def render_label(painter: QPainter, diseno: dict, datos: dict,
                 px_per_mm: float) -> None:
    """Dibuja una etiqueta en la posición actual del painter.

    px_per_mm = ppp del dispositivo / 25.4 (ej. printer.resolution()/25.4).
    """
    ancho = diseno.get("ancho_mm", 76.0)
    alto = diseno.get("alto_mm", 51.0)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    pen = QPen(Qt.GlobalColor.black)
    pen.setWidthF(max(1.0, 0.35 * px_per_mm))
    painter.setPen(pen)
    m = _MARGEN_MM * px_per_mm
    painter.drawRect(QRectF(m, m, ancho * px_per_mm - 2 * m,
                            alto * px_per_mm - 2 * m))

    for campo in diseno.get("campos", []):
        if not campo.get("visible", True):
            continue
        txt = _valor_campo(campo, datos)
        if not txt:
            continue
        font = QFont("Arial", float(campo.get("size", 12)))
        font.setWeight(QFont.Weight.Bold if campo.get("bold") else QFont.Weight.Normal)
        painter.setFont(font)
        x = float(campo.get("x_mm", 0)) * px_per_mm
        y = float(campo.get("y_mm", 0)) * px_per_mm
        w = ancho * px_per_mm - x - 2 * px_per_mm
        h = _TEXTO_ALTO_MM * px_per_mm
        painter.drawText(
            QRectF(x, y, w, h),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            | Qt.TextFlag.TextWordWrap,
            txt,
        )
    painter.restore()


def render_label_pixmap(diseno: dict, datos: dict,
                        escala: float = 1.0) -> QPixmap:
    """Genera una vista previa de la etiqueta como QPixmap."""
    dpi = 300.0 * escala
    px_per_mm = dpi / 25.4
    ancho = int(round(diseno.get("ancho_mm", 76.0) * px_per_mm))
    alto = int(round(diseno.get("alto_mm", 51.0) * px_per_mm))
    img = QImage(ancho, alto, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.white)
    p = QPainter(img)
    render_label(p, diseno, datos, px_per_mm)
    p.end()
    return QPixmap.fromImage(img)
