"""Diálogo 'Imprimir Etiqueta de Prueba'.

Muestra la vista previa de la etiqueta térmica 75x45 mm y permite enviarla
directo a la etiquetadora (controlador de Windows) o guardarla como PDF.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout,
)

from src.components.notificacion_flotante import notificar_flotante
from src.utils.etiqueta_termica import (
    ANCHO_MM, ALTO_MM, configurar_printer, datos_prueba, etiqueta_termica_pdf,
    imprimir_etiqueta, render_etiqueta_termica, render_etiqueta_termica_pixmap,
)

_PREVIEW_W = 380
_PREVIEW_H = 256


class EtiquetaPruebaDialog(QDialog):
    def __init__(self, parent=None, datos: dict | None = None) -> None:
        super().__init__(parent)
        self._datos = datos or datos_prueba()
        self.setWindowTitle("Etiqueta de Prueba")
        self.setMinimumWidth(480)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.lbl_vista = QLabel()
        self.lbl_vista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vista.setFixedSize(_PREVIEW_W, _PREVIEW_H)
        self.lbl_vista.setStyleSheet(
            "border: 1px solid #cbd5e1; background: white; border-radius: 4px;")
        self._actualizar_vista()
        layout.addWidget(self.lbl_vista)

        btns = QHBoxLayout()
        btn_pdf = QPushButton("Guardar PDF")
        btn_pdf.setObjectName("btnSecondary")
        btn_pdf.clicked.connect(self._guardar_pdf)
        btn_preview = QPushButton("Vista previa de impresión")
        btn_preview.setObjectName("btnSecondary")
        btn_preview.clicked.connect(self._vista_previa)
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setObjectName("btnPrimary")
        btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        btns.addWidget(btn_pdf)
        btns.addWidget(btn_preview)
        btns.addStretch()
        btns.addWidget(btn_cerrar)
        btns.addWidget(btn_imprimir)
        layout.addLayout(btns)

    def _actualizar_vista(self) -> None:
        pix = render_etiqueta_termica_pixmap(self._datos)
        self.lbl_vista.setPixmap(pix.scaled(
            QSize(_PREVIEW_W, _PREVIEW_H),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def _imprimir(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_printer(printer)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        err = imprimir_etiqueta(printer, self._datos)
        if err:
            QMessageBox.critical(self, "Error al imprimir", err)
        else:
            notificar_flotante("Etiqueta de prueba enviada a la impresora.",
                               tipo="success", titulo="Impresión", host=self)

    def _vista_previa(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_printer(printer)
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(
            lambda p: render_etiqueta_termica(p, p.resolution() / 25.4,
                                              self._datos))
        dlg.exec()

    def _guardar_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar etiqueta PDF", "etiqueta_prueba.pdf", "PDF (*.pdf)")
        if not path:
            return
        etiqueta_termica_pdf(path, self._datos)
        notificar_flotante(f"Etiqueta guardada en:\n{path}",
                           tipo="success", titulo="PDF", host=self)
