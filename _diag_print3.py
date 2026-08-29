"""Diagnóstico 3: verificar el límite de ~2MB de QWebEngineView.setHtml."""
import os, sys
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)

png = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082")
import base64
b64 = base64.b64encode(png).decode()

for objetivo_mb in (1, 3):
    # repetir la imagen hasta alcanzar el tamaño objetivo
    reps = int(objetivo_mb * 1024 * 1024 / len(b64))
    html = ("<html><body><h1>TEST</h1>" +
            f"<img src='data:image/png;base64,{b64}'/>" * reps +
            "</body></html>")
    web = QWebEngineView()
    loop = QEventLoop()
    resultado = {}

    def _cargado(ok):
        # medir el tamaño REAL del DOM cargado
        web.page().runJavaScript(
            "document.body.children.length",
            lambda n: (resultado.update({"n": n}), loop.quit()))
    web.loadFinished.connect(_cargado)
    QTimer.singleShot(10000, loop.quit)
    web.setHtml(html)
    loop.exec()
    print(f"HTML de ~{objetivo_mb} MB ({len(html)/1024/1024:.1f} MB): "
          f"loadFinished ok={resultado.get('n')}")
