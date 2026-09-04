"""Diagnóstico 2: flujo exacto de PreviewImpresion (vista compartida)."""
import os, sys
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter

app = QApplication(sys.argv)

from src.utils.ficha_tecnica_print import _html
from src.components.preview_impresion import PreviewImpresion, _HAS_WEBENGINE

modelo = {"codigo": "MDL-001", "nombre": "Bota Test"}
ficha = {c: f"valor-{c}" for _, c in __import__(
    "src.models.ficha_tecnica_model", fromlist=["CAMPOS_FICHA"]).CAMPOS_FICHA}
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082")
fotos = {t: png for t in ("producto", "tubo", "chinela", "talon", "suela")}
mats = [{"nombre": "Piel", "cantidad": 2.5, "unidad": "dm", "costo": 60.5}]

html = _html(modelo, ficha, fotos, mats)
print("WebEngine disponible:", _HAS_WEBENGINE)

dlg = PreviewImpresion(html, titulo="Test")
dlg.show()

# Esperar a que la carga inicial termine (como un usuario que abre y da clic)
loop = QApplication.instance()
from PySide6.QtCore import QEventLoop
w1 = QEventLoop()
QTimer.singleShot(3000, w1.quit)   # dar tiempo a la carga inicial
w1.exec()

def _pdf_ok(path):
    from PySide6.QtPdf import QPdfDocument
    doc = QPdfDocument()
    r = doc.load(path)
    img = doc.render(0, __import__("PySide6.QtCore", fromlist=["QSize"]).QSize(850, 1100))
    nonwhite = sum(
        1 for y in range(0, img.height(), 7) for x in range(0, img.width(), 7)
        if not (img.pixelColor(x, y).red() > 245 and
                img.pixelColor(x, y).green() > 245 and
                img.pixelColor(x, y).blue() > 245))
    muestreados = len(range(0, img.height(), 7)) * len(range(0, img.width(), 7))
    print(f"  {os.path.basename(path)}: load={r}, paginas={doc.pageCount()}, "
          f"contenido={100*nonwhite/muestreados:.1f}%")

# Caso A: exportar tras carga completa (flujo normal)
printer_a = QPrinter(QPrinter.HighResolution)
printer_a.setOutputFormat(QPrinter.PdfFormat)
printer_a.setPageSize(QPageSize(QPageSize.Letter))
printer_a.setOutputFileName("_diag_casoA.pdf")
try:
    dlg._renderizar(printer_a)
    _pdf_ok("_diag_casoA.pdf")
except Exception as e:
    print("Caso A EXCEPCION:", e)

# Caso B: exportar INMEDIATAMENTE sin esperar carga (usuario rápido)
dlg2 = PreviewImpresion(html, titulo="Test2")
dlg2.show()
printer_b = QPrinter(QPrinter.HighResolution)
printer_b.setOutputFormat(QPrinter.PdfFormat)
printer_b.setPageSize(QPageSize(QPageSize.Letter))
printer_b.setOutputFileName("_diag_casoB.pdf")

def _caso_b():
    try:
        dlg2._renderizar(printer_b)
        _pdf_ok("_diag_casoB.pdf")
    except Exception as e:
        print("Caso B EXCEPCION:", e)
    app.quit()

QTimer.singleShot(50, _caso_b)
app.exec()
print("fin")
