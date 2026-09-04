"""Diagnóstico final: ficha con fotos de tamaño real por el flujo completo."""
import os, sys
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop, QBuffer
from PySide6.QtGui import QImage, QColor

app = QApplication(sys.argv)

# Foto simulada de cámara: 2448x3264 con ruido (PNG pesado, varios MB)
import random
random.seed(1)
img = QImage(2448, 3264, QImage.Format_RGB32)
for y in range(0, 3264, 3):
    for x in range(0, 2448, 3):
        c = QColor(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        for dy in range(3):
            for dx in range(3):
                img.setPixelColor(min(x+dx,2447), min(y+dy,3263), c)
buf = QBuffer(); buf.open(QBuffer.WriteOnly)
img.save(buf, "PNG")
foto_bytes = bytes(buf.data())
print(f"Foto simulada: {len(foto_bytes)/1024/1024:.1f} MB")

from src.utils.ficha_tecnica_print import _html
modelo = {"codigo": "MDL-001", "nombre": "Bota Test"}
ficha = {c: f"valor-{c}" for _, c in __import__(
    "src.models.ficha_tecnica_model", fromlist=["CAMPOS_FICHA"]).CAMPOS_FICHA}
fotos = {t: foto_bytes for t in ("producto", "tubo", "chinela", "talon", "suela")}
mats = [{"nombre": "Piel", "cantidad": 2.5, "unidad": "dm", "costo": 60.5}]

html = _html(modelo, ficha, fotos, mats)
print(f"HTML generado: {len(html)/1024/1024:.2f} MB")

from PySide6.QtPrintSupport import QPrinter
from PySide6.QtCore import QSize
from PySide6.QtGui import QPageSize

def contenido_pdf(path):
    from PySide6.QtPdf import QPdfDocument
    doc = QPdfDocument()
    doc.load(path)
    img = doc.render(0, QSize(850, 1100))
    nonwhite = sum(
        1 for y in range(0, img.height(), 7) for x in range(0, img.width(), 7)
        if not (img.pixelColor(x, y).red() > 245 and
                img.pixelColor(x, y).green() > 245 and
                img.pixelColor(x, y).blue() > 245))
    m = len(range(0, img.height(), 7)) * len(range(0, img.width(), 7))
    return f"paginas={doc.pageCount()}, contenido={100*nonwhite/m:.1f}%"

from src.components.preview_impresion import PreviewImpresion

# Caso A: exportar tras carga completa
dlg = PreviewImpresion(html, titulo="Test grande")
dlg.show()
w1 = QEventLoop(); QTimer.singleShot(6000, w1.quit); w1.exec()

pr_a = QPrinter(QPrinter.HighResolution)
pr_a.setOutputFormat(QPrinter.PdfFormat)
pr_a.setPageSize(QPageSize(QPageSize.Letter))
pr_a.setOutputFileName("_diag_grande_A.pdf")
try:
    dlg._renderizar(pr_a)
    print("Caso A (tras carga):", contenido_pdf("_diag_grande_A.pdf"))
except Exception as e:
    print("Caso A EXCEPCION:", e)

# Caso B: exportar inmediatamente (carga aún en curso)
dlg2 = PreviewImpresion(html, titulo="Test grande 2")
dlg2.show()
pr_b = QPrinter(QPrinter.HighResolution)
pr_b.setOutputFormat(QPrinter.PdfFormat)
pr_b.setPageSize(QPageSize(QPageSize.Letter))
pr_b.setOutputFileName("_diag_grande_B.pdf")

def _caso_b():
    try:
        dlg2._renderizar(pr_b)
        print("Caso B (inmediato):", contenido_pdf("_diag_grande_B.pdf"))
    except Exception as e:
        print("Caso B EXCEPCION:", e)
    app.quit()

QTimer.singleShot(100, _caso_b)
app.exec()
print("fin")
