"""Renderizado de etiquetas sobre QPainter (impresión y vista previa).

El diseño se guarda en la tabla etiqueta_config (JSON). Cada campo admite:
  - Posición y dimensiones: x_mm, y_mm, ancho_mm, alto_mm.
  - Borde/recuadro: borde_visible, borde_grosor_mm.
  - Tipografía: size (valor), label_size (etiqueta) cuando el campo tiene
    prefijo 'label', bold, cursiva.
  - Alineación: 'izquierda' | 'centro' | 'derecha'.
  - Visibilidad: visible.

Un campo de tipo 'dato' puede tener un prefijo 'label' (p. ej. "MODELO:")
que se dibuja con label_size y el valor con size, respetando la alineación.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap

_MARGEN_MM = 2.5
_TEXTO_ALTO_MM = 7.0

_ALINEACION = {
    "izquierda": Qt.AlignmentFlag.AlignLeft,
    "centro": Qt.AlignmentFlag.AlignHCenter,
    "derecha": Qt.AlignmentFlag.AlignRight,
}


def _valor_campo(campo: dict, datos: dict) -> str:
    if campo.get("tipo") == "texto":
        return str(campo.get("texto", ""))
    if campo.get("tipo") == "dato":
        v = datos.get(campo.get("dato", ""))
        return "" if v in (None, "") else str(v)
    return ""


def _fuente(campo: dict, size, px_per_mm: float) -> QFont:
    """Fuente con tamaño en px proporcional a la escala del painter.

    size es en puntos; 1pt = 0.3528mm. Se usa setPixelSize para que el texto
    quede igual en lienzo (painter escalado) e impresión (px_per_mm real)."""
    f = QFont(str(campo.get("familia", "Arial")))
    f.setPixelSize(max(1, int(round(float(size) * 0.3528 * px_per_mm))))
    f.setWeight(QFont.Weight.Bold if campo.get("bold") else QFont.Weight.Normal)
    f.setItalic(bool(campo.get("cursiva")))
    f.setUnderline(bool(campo.get("subrayado")))
    return f


def rect_campo_mm(diseno: dict, campo: dict) -> QRectF:
    """Rectángulo del campo en milímetros (usado por render y por el editor)."""
    ancho = float(diseno.get("ancho_mm", 76.0))
    x = float(campo.get("x_mm", 0))
    y = float(campo.get("y_mm", 0))
    w = float(campo.get("ancho_mm", ancho - x - 2))
    h = float(campo.get("alto_mm", _TEXTO_ALTO_MM))
    return QRectF(x, y, w, h)


def _dibujar_label_valor(painter: QPainter, campo: dict, label: str,
                         valor: str, rect: QRectF, px_per_mm: float) -> None:
    f_label = _fuente(campo, campo.get("label_size", campo.get("size", 12)),
                      px_per_mm)
    f_valor = _fuente(campo, campo.get("size", 12), px_per_mm)
    painter.setFont(f_label)
    wl = painter.fontMetrics().horizontalAdvance(label)
    painter.setFont(f_valor)
    wv = painter.fontMetrics().horizontalAdvance(valor)

    total = wl + wv
    alineacion = campo.get("alineacion", "izquierda")
    if alineacion == "derecha":
        x = rect.right() - total
    elif alineacion == "centro":
        x = rect.center().x() - total / 2.0
    else:
        x = rect.left()

    r_label = QRectF(x, rect.top(), wl, rect.height())
    r_valor = QRectF(x + wl, rect.top(), wv, rect.height())
    painter.setFont(f_label)
    painter.drawText(r_label,
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     label)
    painter.setFont(f_valor)
    painter.drawText(r_valor,
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     valor)


def _calcular_size_fit(painter: QPainter, campo: dict, texto: str,
                        rect: QRectF, px_per_mm: float,
                        default_size: float) -> float:
    """Calcula el tamaño de fuente (pt) que ajusta el texto al ancho del rect.

    Busca binaria entre 4pt y 200pt para que el texto quepa justo en el
    ancho del rectángulo (ancho de etiqueta menos borde)."""
    max_size = rect.height() / (0.3528 * px_per_mm)
    lo, hi = 4.0, min(max_size, 200.0)
    best = lo
    for _ in range(20):
        mid = (lo + hi) / 2.0
        f = _fuente(campo, mid, px_per_mm)
        painter.setFont(f)
        w = painter.fontMetrics().horizontalAdvance(texto)
        if w <= rect.width():
            best = mid
            lo = mid
        else:
            hi = mid
    return best


def _dibujar_plano(painter: QPainter, campo: dict, texto: str,
                   rect: QRectF, px_per_mm: float) -> None:
    if not texto:
        return
    size = float(campo.get("size", 12))
    if campo.get("auto_fit"):
        size = _calcular_size_fit(painter, campo, texto, rect, px_per_mm, size)
    painter.setFont(_fuente(campo, size, px_per_mm))
    al = _ALINEACION.get(campo.get("alineacion", "izquierda"),
                         Qt.AlignmentFlag.AlignLeft)
    painter.drawText(rect, al | Qt.AlignmentFlag.AlignVCenter, texto)


def _dibujar_contenido(painter: QPainter, campo: dict, datos: dict,
                       rect: QRectF, px_per_mm: float) -> None:
    label = str(campo.get("label", "") or "")
    valor = _valor_campo(campo, datos)
    painter.setPen(QPen(QColor(campo.get("color_texto", "#000000"))))

    angulo = int(campo.get("rotacion", 0) or 0) % 360
    if angulo:
        painter.save()
        painter.translate(rect.center().x(), rect.center().y())
        painter.rotate(angulo)
        rect = QRectF(-rect.width() / 2.0, -rect.height() / 2.0,
                      rect.width(), rect.height())

    if campo.get("tipo") == "dato" and label:
        if valor:
            _dibujar_label_valor(painter, campo, label, valor, rect, px_per_mm)
        else:
            _dibujar_plano(painter, campo, label, rect, px_per_mm)
    else:
        _dibujar_plano(painter, campo, valor, rect, px_per_mm)

    if angulo:
        painter.restore()


def render_label(painter: QPainter, diseno: dict, datos: dict,
                 px_per_mm: float) -> None:
    """Dibuja una etiqueta en la posición actual del painter.

    px_per_mm = ppp del dispositivo / 25.4 (ej. printer.resolution()/25.4).
    """
    ancho = float(diseno.get("ancho_mm", 76.0))
    alto = float(diseno.get("alto_mm", 51.0))
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
        rect = rect_campo_mm(diseno, campo)
        x = rect.x() * px_per_mm
        y = rect.y() * px_per_mm
        w = rect.width() * px_per_mm
        h = rect.height() * px_per_mm
        if campo.get("color_fondo"):
            painter.fillRect(QRectF(x, y, w, h),
                             QColor(campo.get("color_fondo")))
        if campo.get("borde_visible"):
            pen_b = QPen(QColor(campo.get("color_borde", "#000000")))
            pen_b.setWidthF(max(1.0,
                                float(campo.get("borde_grosor_mm", 0.3)) * px_per_mm))
            painter.setPen(pen_b)
            painter.drawRect(QRectF(x, y, w, h))
        _dibujar_contenido(painter, campo, datos, QRectF(x, y, w, h),
                           px_per_mm)
    painter.restore()


def render_label_pixmap(diseno: dict, datos: dict,
                        escala: float = 1.0) -> QPixmap:
    """Genera una vista previa de la etiqueta como QPixmap."""
    dpi = 300.0 * escala
    px_per_mm = dpi / 25.4
    ancho = int(round(float(diseno.get("ancho_mm", 76.0)) * px_per_mm))
    alto = int(round(float(diseno.get("alto_mm", 51.0)) * px_per_mm))
    img = QImage(ancho, alto, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.white)
    p = QPainter(img)
    render_label(p, diseno, datos, px_per_mm)
    p.end()
    return QPixmap.fromImage(img)
