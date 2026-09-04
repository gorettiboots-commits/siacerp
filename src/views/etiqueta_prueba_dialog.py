"""Diálogo 'Imprimir Etiqueta de Prueba'.

Muestra la vista previa de la etiqueta térmica 75x45 mm y permite enviarla
directo a la etiquetadora (controlador de Windows) o guardarla como PDF.
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtPrintSupport import QPrintPreviewDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout,
)

from src.components.notificacion_flotante import notificar_flotante
from src.utils.etiqueta_termica import (
    ANCHO_MM, ALTO_MM, configurar_printer, datos_prueba, etiqueta_termica_pdf,
    imprimir_etiqueta, render_etiqueta_termica, render_etiqueta_termica_pixmap,
)
from src.utils.impresion_virtual import dialogo_impresion

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

        def pintar(p: QPrinter) -> None:
            err = imprimir_etiqueta(p, self._datos)
            if err:
                raise RuntimeError(err)

        try:
            estado = dialogo_impresion(printer, self, pintar)
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir", str(e))
            return
        if estado == "impreso":
            notificar_flotante("Etiqueta de prueba enviada a la impresora.",
                               tipo="success", titulo="Impresión", host=self)
        elif estado == "simulado":
            notificar_flotante("Simulación en pantalla: no se envió a la impresora.",
                               tipo="info", titulo="Impresora virtual", host=self)

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
