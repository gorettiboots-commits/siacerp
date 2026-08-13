"""Etiqueta térmica de calzado (75 x 45 mm, proporción ~5:3).

Layout según especificación:
  A) Columna izquierda (60% del ancho), interlineado MUY compacto, desde el
     borde superior hasta casi el inferior:
       - "MODELO: <modelo>"  (18pt, negrita, una sola línea)
       - "CORTE:"            (18pt, negrita)
       - "  <corte>"         (16pt, negrita, indentado, condensado si aplica)
       - "COLOR:"            (18pt, negrita)
       - "  <color>"         (16pt, negrita, indentado, condensado si aplica)
  B) Columna derecha (40% del ancho):
       - Encabezado "TALLA" (20pt, negrita) centrado sobre el recuadro.
       - Recuadro cuadrado negro (borde ~0.3 mm) en la esquina inferior
         derecha (~35% ancho x ~60% alto) con la talla centrada en grande.

Fondo blanco, sin márgenes exteriores ni bordes del lienzo; fuente Arial
negra en negrita. Los textos se auto-ajustan (tamaño/condensación) para que
no haya saltos de línea y el recuadro quede sin espacio sobrante.

Render con QPainter: imprime directo (QPrinter + controlador de Windows) o
genera PDF vectorial e imagen.
"""
from PySide6.QtCore import QRectF, QSizeF, Qt
from PySide6.QtGui import QFont, QImage, QPageSize, QPainter, QPen, QPixmap
from PySide6.QtPrintSupport import QPrinter

ANCHO_MM = 75.0
ALTO_MM = 45.0

_FUENTE = "Arial"


def datos_prueba() -> dict:
    return {
        "modelo": "9272",
        "corte": "PIEL CERA",
        "color": "CAMEL TUBO CAMEL",
        "talla": "26.0",
    }


def _font(size: float, bold: bool, stretch: int = 100) -> QFont:
    f = QFont(_FUENTE, float(size))
    f.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    if stretch != 100:
        f.setStretch(stretch)
    return f


def _texto_fit(painter: QPainter, texto: str, max_w_mm: float,
               px_per_mm: float, size_max: int, bold: bool,
               stretch: int = 100, condensar: bool = False) -> None:
    """Ajusta el texto para que entre en max_w_mm sin saltar de línea.

    Con condensar=True primero condensa horizontalmente manteniendo el tamaño
    (stretch 100->55); solo reduce el tamaño si aun así no cabe.
    """
    if not texto:
        return
    max_w = max_w_mm * px_per_mm
    if condensar:
        for st in range(stretch, 55, -5):
            f = _font(size_max, bold, st)
            painter.setFont(f)
            if painter.fontMetrics().horizontalAdvance(texto) <= max_w:
                return
    for size in range(int(size_max), 5, -1):
        f = _font(size, bold, stretch)
        painter.setFont(f)
        if painter.fontMetrics().horizontalAdvance(texto) <= max_w:
            return
    painter.setFont(_font(5, bold, stretch))


def render_etiqueta_termica(painter: QPainter, px_per_mm: float,
                            datos: dict) -> None:
    """Dibuja la etiqueta térmica en la posición actual del painter.

    px_per_mm = ppp del dispositivo / 25.4 (ej. printer.resolution()/25.4).
    """
    s = px_per_mm
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    pen = QPen(Qt.GlobalColor.black)
    pen.setWidthF(max(1.0, 0.3 * s))
    painter.setPen(pen)

    # ---- Columna izquierda (60% ancho, bloque compacto de arriba a abajo) ----
    x0 = 5.0 * s
    w_left = 40.0 * s  # x0 .. x0+40 mm (evita tocar el recuadro de la derecha)

    _texto_fit(painter, f"MODELO: {datos.get('modelo', '')}",
               w_left / s, px_per_mm, 18, True, 100)
    painter.drawText(QRectF(x0, 1.5 * s, w_left, 8.0 * s),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     f"MODELO: {datos.get('modelo', '')}")

    _texto_fit(painter, "CORTE:", w_left / s, px_per_mm, 18, True, 100)
    painter.drawText(QRectF(x0, 9.5 * s, w_left, 8.0 * s),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     "CORTE:")

    corte = str(datos.get("corte", ""))
    _texto_fit(painter, corte, w_left / s, px_per_mm, 18, True, 85,
               condensar=True)
    painter.drawText(QRectF(x0, 17.5 * s, w_left, 7.5 * s),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     corte)

    _texto_fit(painter, "COLOR:", w_left / s, px_per_mm, 18, True, 100)
    painter.drawText(QRectF(x0, 25.5 * s, w_left, 8.0 * s),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     "COLOR:")

    color = str(datos.get("color", ""))
    _texto_fit(painter, color, w_left / s, px_per_mm, 18, True, 85,
               condensar=True)
    painter.drawText(QRectF(x0, 33.5 * s, w_left, 7.5 * s),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     color)

    # ---- Columna derecha (40% ancho): TALLA + recuadro ----
    bx = 47.0 * s
    by = 16.5 * s
    bs = 27.0 * s

    _texto_fit(painter, "TALLA", bs / s, px_per_mm, 24, True, 100)
    painter.drawText(QRectF(bx, 2.0 * s, bs, 8.5 * s),
                     Qt.AlignmentFlag.AlignCenter, "TALLA")

    painter.setPen(pen)
    painter.drawRect(QRectF(bx, by, bs, bs))

    talla = str(datos.get("talla", ""))
    _texto_fit(painter, talla, (bs - 2.0 * s) / s, px_per_mm, 53, True, 100,
               condensar=True)
    painter.drawText(QRectF(bx, by, bs, bs), Qt.AlignmentFlag.AlignCenter, talla)

    painter.restore()


def render_etiqueta_termica_pixmap(datos: dict,
                                   escala: float = 1.0) -> QPixmap:
    """Genera una vista previa de la etiqueta como QPixmap."""
    dpi = 300.0 * escala
    px_per_mm = dpi / 25.4
    w = int(round(ANCHO_MM * px_per_mm))
    h = int(round(ALTO_MM * px_per_mm))
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.white)
    p = QPainter(img)
    render_etiqueta_termica(p, px_per_mm, datos)
    p.end()
    return QPixmap.fromImage(img)


def configurar_printer(printer: QPrinter) -> None:
    """Aplica el tamaño 75x45 mm a un QPrinter (impresión o PDF)."""
    printer.setPageSize(QPageSize(QSizeF(ANCHO_MM, ALTO_MM),
                                  QPageSize.Unit.Millimeter))
    printer.setFullPage(True)
    printer.setDocName("Etiqueta SIAC")


def imprimir_etiqueta(printer: QPrinter, datos: dict) -> str:
    """Pinta la etiqueta sobre el QPrinter y envía el trabajo.

    Devuelve '' si todo salió bien; en otro caso el mensaje de error (para que
    la GUI lo muestre en vez de fallar en silencio).
    """
    try:
        p = QPainter(printer)
        if not p.isActive():
            return ("No se pudo iniciar el painter sobre la impresora. "
                    "Revisa el driver y que la cola de impresión no esté en error.")
        render_etiqueta_termica(p, printer.resolution() / 25.4, datos)
        p.end()
        return ""
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def etiqueta_termica_pdf(path: str, datos: dict | None = None) -> None:
    """Genera un PDF vectorial con la etiqueta lista para imprimir."""
    datos = datos or datos_prueba()
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    configurar_printer(printer)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(path)
    p = QPainter(printer)
    render_etiqueta_termica(p, printer.resolution() / 25.4, datos)
    p.end()
