"""Componente reutilizable del sistema: vista previa de impresión (WYSIWYG).

Aprobado desde el Sandbox. Muestra cómo se verá un reporte ANTES de
imprimirlo o exportarlo a PDF: renderiza el mismo HTML que generan los
reportes del sistema sobre una "hoja" simulada (fondo gris, hoja blanca
centrada con la proporción real de la página) y ofrece controles de tamaño
de página, orientación, zoom, impresión y exportación a PDF.

Uso:
    from src.components import obtener_componente

    PreviewImpresion = obtener_componente("preview_impresion")
    dlg = PreviewImpresion(html, titulo="Reporte de inventario", parent=self)
    dlg.exec()

O bien, con la función de conveniencia:
    from src.components.preview_impresion import previsualizar_html

    previsualizar_html(html, titulo="Reporte", parent=self)

El `html` debe ser el mismo que se enviaría a imprimir: los reportes del
sistema lo generan en `src/utils/export_utils.py` (`_oc_receipt_html`,
`_table_to_html`, etc.). El PDF se genera por la misma vía que la impresión
(QTextDocument), así que lo que se ve es lo que sale.
"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QDesktopServices, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QTextBrowser, QToolButton, QVBoxLayout, QWidget,
)

# WebEngine se crea de forma perezosa dentro del diálogo (es pesado y solo
# debe cargarse cuando el usuario abre el preview). Si no está disponible o
# falla al iniciarse, se usa QTextBrowser como fallback ligero.
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: F401
    _HAS_WEBENGINE = True
except ImportError:  # pragma: no cover
    _HAS_WEBENGINE = False


PAGINAS = {
    "Carta (Letter)": QPageSize.Letter,
    "Oficio (Legal)": QPageSize.Legal,
    "A4": QPageSize.A4,
}


def _crear_motor(html: str, parent: QWidget):
    """Crea el motor de render: WebEngine (WYSIWYG) o QTextBrowser."""
    if _HAS_WEBENGINE:
        try:
            view = QWebEngineView(parent)
            view.setHtml(html)
            view.setZoomFactor(1.0)
            return view, True
        except Exception:  # pragma: no cover — fallback defensivo
            pass
    browser = QTextBrowser(parent)
    browser.setHtml(html)
    browser.setOpenExternalLinks(True)
    return browser, False


class _Hoja(QWidget):
    """Área gris con una 'hoja' blanca centrada que simula la página impresa.

    El contenido se coloca centrado y el alto lo dicta el propio contenido
    (proporción de hoja real); el scroll vertical aparece si hace falta.
    """

    def __init__(self, contenido: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._contenido = contenido
        self.setStyleSheet("background-color: #c9ccd1;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.addWidget(self._contenido, 0, Qt.AlignHCenter | Qt.AlignTop)


class PreviewImpresion(QDialog):
    """Vista previa de impresión para un documento HTML (WYSIWYG).

    Recibe el mismo HTML que generan los reportes del sistema y lo muestra
    sobre una hoja simulada. Desde aquí se puede imprimir o exportar a PDF.

    Controles públicos:
        cmb_pagina       QComboBox — tamaño de página (Carta/Oficio/A4).
        cmb_orientacion  QComboBox — Vertical/Horizontal.
    """

    def __init__(self, html: str, titulo: str = "Vista previa de impresión",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._html = html
        self.setWindowTitle(titulo)
        self.resize(1000, 700)
        self.setModal(True)
        self._setup_ui()
        self._actualizar_hoja()

    # ------------------------------------------------------------- UI
    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        toolbar = self._crear_toolbar()
        lay.addWidget(toolbar)

        # Motor de render: WebEngine (WYSIWYG) o QTextBrowser (fallback ligero
        # sin CSS completo — solo se usa si WebEngine no está disponible).
        self._contenido, self._wysiwyg = _crear_motor(self._html, self)
        self._web = self._contenido if self._wysiwyg else None
        if not self._wysiwyg:
            self._lbl_aviso.setText(
                "Vista simplificada: el motor de render completo no está "
                "disponible en este equipo.")
            self._lbl_aviso.setVisible(True)

        # La hoja blanca que simula la página impresa.
        self._hoja = _Hoja(self._contenido, self)
        self._hoja._contenido.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #cbd5e1;"
        )

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._hoja)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(
            "QScrollArea { background-color: #c9ccd1; border: none; }")
        lay.addWidget(self._scroll, 1)

        # El ancho del visor recién creado aún no es el real: se recalcula en
        # cuanto el diálogo queda mostrado y en cada cambio de tamaño.
        self._zoom = 1.0
        QTimer.singleShot(0, self._actualizar_hoja)

    def _crear_toolbar(self) -> QWidget:
        bar = QWidget(self)
        bar.setObjectName("headerBar")
        barlay = QHBoxLayout(bar)
        barlay.setContentsMargins(12, 8, 12, 8)
        barlay.setSpacing(8)

        titulo = QLabel("Vista previa de impresión")
        titulo.setObjectName("sectionTitle")
        barlay.addWidget(titulo)
        barlay.addStretch()

        self._lbl_aviso = QLabel("")
        self._lbl_aviso.setStyleSheet(
            "color: #b45309; font-size: 11px; font-weight: 600;")
        self._lbl_aviso.setVisible(False)
        barlay.addWidget(self._lbl_aviso)
        barlay.addSpacing(8)

        barlay.addWidget(QLabel("Página:"))
        self.cmb_pagina = QComboBox()
        self.cmb_pagina.addItems(list(PAGINAS))
        self.cmb_pagina.setCurrentText("Carta (Letter)")
        self.cmb_pagina.currentIndexChanged.connect(self._actualizar_hoja)
        barlay.addWidget(self.cmb_pagina)

        barlay.addWidget(QLabel("Orientación:"))
        self.cmb_orientacion = QComboBox()
        self.cmb_orientacion.addItems(["Vertical", "Horizontal"])
        self.cmb_orientacion.currentIndexChanged.connect(self._actualizar_hoja)
        barlay.addWidget(self.cmb_orientacion)

        barlay.addSpacing(8)

        self._btn_zoom = QLabel("100%")
        self._btn_zoom.setStyleSheet("color: #475569; font-size: 12px;")
        barlay.addWidget(self._btn_zoom)

        for texto, fn in [("−", self._zoom_out), ("+", self._zoom_in),
                          ("Imprimir", self._imprimir),
                          ("Exportar PDF", self._exportar_pdf)]:
            if texto in ("−", "+"):
                btn = QToolButton()
                btn.setText(texto)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setToolTip("Ajustar zoom")
                btn.setAutoRaise(True)
            else:
                btn = QPushButton(texto)
                btn.setObjectName("btnSecondary" if texto == "Imprimir" else "btnPrimary")
                btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(fn)
            barlay.addWidget(btn)

        return bar

    # -------------------------------------------------------- Hoja
    def _actualizar_hoja(self) -> None:
        if not hasattr(self, "_hoja"):
            return
        # Ancho disponible real del visor (ya con su layout aplicado).
        disponible = self._scroll.viewport().width() - 48
        if disponible < 100:
            return

        # Proporción de una hoja real (carta/A4): ancho fijo a escala y alto
        # según la proporción, aplicando el zoom elegido por el usuario.
        ancho_base = 1000 if self.cmb_orientacion.currentText() == "Horizontal" else 760
        ancho = min(int(ancho_base * self._zoom), max(240, disponible))
        alto = int(ancho * 1.414)  # proporción carta/A4

        self._hoja._contenido.setFixedSize(ancho, alto)
        if self._web is not None:
            self._web.setFixedSize(ancho, alto)
            self._web.setZoomFactor(1.0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._actualizar_hoja()

    def _zoom_in(self) -> None:
        self._zoom = min(2.0, self._zoom + 0.25)
        self._actualizar_hoja()
        self._btn_zoom.setText(f"{int(self._zoom * 100)}%")

    def _zoom_out(self) -> None:
        self._zoom = max(0.5, self._zoom - 0.25)
        self._actualizar_hoja()
        self._btn_zoom.setText(f"{int(self._zoom * 100)}%")

    # -------------------------------------------------------- Impresión
    def _printer(self, para_pdf: bool = False) -> QPrinter:
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(PAGINAS[self.cmb_pagina.currentText()])
        orientacion = (QPageLayout.Landscape
                       if self.cmb_orientacion.currentText() == "Horizontal"
                       else QPageLayout.Portrait)
        printer.setPageOrientation(orientacion)
        if para_pdf:
            printer.setOutputFormat(QPrinter.PdfFormat)
        return printer

    def _imprimir(self) -> None:
        printer = self._printer()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QDialog.Accepted:
            self._renderizar(printer)

    def _exportar_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar PDF", "reporte.pdf", "PDF (*.pdf)")
        if not path:
            return
        printer = self._printer(para_pdf=True)
        printer.setOutputFileName(path)
        self._renderizar(printer)
        QMessageBox.information(self, "PDF generado",
                                f"El documento se exportó a:\n{path}")
        QDesktopServices.openUrl(path)

    def _renderizar(self, printer: QPrinter) -> None:
        from PySide6.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(self._html)
        doc.print_(printer)


def previsualizar_html(html: str, titulo: str = "Vista previa de impresión",
                       parent: QWidget | None = None) -> None:
    """Abre la vista previa de impresión de un documento HTML (modal).

    Es la vía recomendada para que los reportes del sistema ofrezcan
    "Vista previa" antes de imprimir o exportar:

        from src.components.preview_impresion import previsualizar_html

        previsualizar_html(html, titulo="Recibo de Orden de Compra", parent=self)
    """
    dlg = PreviewImpresion(html, titulo=titulo, parent=parent)
    dlg.exec()
