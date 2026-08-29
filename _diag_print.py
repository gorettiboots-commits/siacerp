"""Diagnóstico: reproduce el pipeline completo de impresión de ficha técnica."""
import os, sys
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from src.utils.ficha_tecnica_print import _html

modelo = {"codigo": "MDL-001", "nombre": "Bota Test"}
ficha = {c: f"valor-{c}" for _, c in __import__(
    "src.models.ficha_tecnica_model", fromlist=["CAMPOS_FICHA"]).CAMPOS_FICHA}
png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082")
fotos = {t: png for t in ("producto", "tubo", "chinela", "talon", "suela")}
mats = [{"nombre": "Piel", "cantidad": 2.5, "unidad": "dm", "costo": 60.5}]

html = _html(modelo, ficha, fotos, mats)
print(f"HTML generado: {len(html)} chars")
open("_diag_ficha.html", "w", encoding="utf-8").write(html)

# Pipeline idéntico al del componente: WebEngine -> printToPdf
from PySide6.QtCore import QEventLoop, QTimer, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWebEngineWidgets import QWebEngineView

web = QWebEngineView()
loop = QEventLoop()
estado = {"ok": False}

def _terminado(_ruta, exito):
    estado["ok"] = exito
    loop.quit()

def _cargado(_ok):
    lay = QPageLayout(QPageSize(QPageSize.Letter), QPageLayout.Portrait,
                      QMarginsF(0, 0, 0, 0), QPageLayout.Millimeter)
    web.page().printToPdf("_diag_out.pdf", lay)

web.pdfPrintingFinished.connect(_terminado)
web.loadFinished.connect(_cargado)
QTimer.singleShot(20000, loop.quit)
web.setHtml(html)
loop.exec()

print("printToPdf ok:", estado["ok"])
if not os.path.exists("_diag_out.pdf"):
    print("ERROR: no se generó el PDF")
    sys.exit(1)
print("PDF size:", os.path.getsize("_diag_out.pdf"))

# Inspección del PDF resultante
from PySide6.QtPdf import QPdfDocument
doc = QPdfDocument()
r = doc.load("_diag_out.pdf")
print("load:", r, "| páginas:", doc.pageCount())
img = doc.render(0, __import__("PySide6.QtCore", fromlist=["QSize"]).QSize(850, 1100))
# contar píxeles no blancos
nonwhite = 0
total = img.width() * img.height()
for y in range(0, img.height(), 7):
    for x in range(0, img.width(), 7):
        c = img.pixelColor(x, y)
        if not (c.red() > 245 and c.green() > 245 and c.blue() > 245):
            nonwhite += 1
muestreados = len(range(0, img.height(), 7)) * len(range(0, img.width(), 7))
print(f"Página 1: {nonwhite}/{muestreados} píxeles muestreados con contenido "
      f"({100*nonwhite/muestreados:.1f}%)")
