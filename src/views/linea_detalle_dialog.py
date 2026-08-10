"""Diálogo de detalle de una línea de programación.

Muestra los datos de la línea y, en la parte de impresión, una tabla
Modelo | Corte | Color | Talla | Cantidad con edición inline. Las ediciones
solo afectan la impresión; no se guardan. Imprime una etiqueta por par con el
formato de la etiqueta de prueba (75x45 mm).
"""
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from src.utils.etiqueta_termica import (
    configurar_printer, etiqueta_termica_pdf, render_etiqueta_termica,
    render_etiqueta_termica_pixmap,
)

_PREVIEW_W = 380
_PREVIEW_H = 256

_ESTATUS = {
    "programado": "Programado",
    "programacion_incompleta": "Programación Incompleta",
    "en_proceso": "En proceso",
    "producido": "Producido",
}


class LineaDetalleDialog(QDialog):
    def __init__(self, linea: dict, parent=None) -> None:
        super().__init__(parent)
        self._linea = linea
        self.setWindowTitle("Detalle de Línea")
        self.setMinimumWidth(680)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        datos = QFormLayout()
        campos = [
            ("Folio Prog.:", self._linea.get("folio_prog", "")),
            ("Cliente:", self._linea.get("cliente", "")),
            ("Modelo:", self._linea.get("modelo", "")),
            ("Piel:", self._linea.get("piel", "")),
            ("Color:", self._linea.get("color", "")),
            ("Fecha Prog.:", self._linea.get("fecha_prog", "") or "—"),
            ("Estatus:", _ESTATUS.get(
                self._linea.get("estatus", ""),
                self._linea.get("estatus", "") or "—")),
        ]
        for etiqueta, valor in campos:
            lbl = QLabel(str(valor))
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-weight: bold;")
            datos.addRow(f"<b>{etiqueta}</b>", lbl)
        layout.addLayout(datos)

        self.tbl_etiquetas = QTableWidget(0, 5)
        self.tbl_etiquetas.setHorizontalHeaderLabels(
            ["Modelo", "Corte", "Color", "Talla", "Cantidad"])
        self.tbl_etiquetas.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed)
        self.tbl_etiquetas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_etiquetas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.tbl_etiquetas.setMaximumHeight(200)
        self.tbl_etiquetas.itemChanged.connect(self._previsualizar)
        self.tbl_etiquetas.currentCellChanged.connect(self._previsualizar)
        layout.addWidget(self.tbl_etiquetas)

        lbl_nota = QLabel(
            "Las ediciones en esta tabla solo afectan la impresión; no se guardan.")
        lbl_nota.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_nota)

        self.lbl_vista = QLabel()
        self.lbl_vista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vista.setFixedSize(_PREVIEW_W, _PREVIEW_H)
        self.lbl_vista.setStyleSheet(
            "border: 1px solid #cbd5e1; background: white; border-radius: 4px;")
        layout.addWidget(self.lbl_vista)

        self._poblar_tabla()
        self._previsualizar()

        btns = QHBoxLayout()
        btn_pdf = QPushButton("Guardar PDF")
        btn_pdf.setObjectName("btnSecondary")
        btn_pdf.clicked.connect(self._guardar_pdf)
        btn_preview = QPushButton("Vista previa de impresión")
        btn_preview.setObjectName("btnSecondary")
        btn_preview.clicked.connect(self._vista_previa)
        btn_imprimir = QPushButton("Imprimir Etiquetas")
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

    def _poblar_tabla(self) -> None:
        tallas = self._linea.get("tallas") or []
        if not tallas:
            tallas = [{"talla": "", "pares": 1}]
        self.tbl_etiquetas.setRowCount(len(tallas))
        for i, t in enumerate(tallas):
            modelo = str(self._linea.get("modelo", "") or "")
            corte = str(self._linea.get("piel", "") or "")
            color = str(self._linea.get("color", "") or "")
            talla = str(t.get("talla", ""))
            pares = int(t.get("pares", 0) or 0)
            for col, valor in ((0, modelo), (1, corte), (2, color)):
                item = QTableWidgetItem(valor)
                self.tbl_etiquetas.setItem(i, col, item)
            item_talla = QTableWidgetItem(talla)
            item_talla.setFlags(Qt.ItemFlag.ItemIsEnabled
                                | Qt.ItemFlag.ItemIsSelectable)
            self.tbl_etiquetas.setItem(i, 3, item_talla)
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(9999)
            spin.setValue(pares if pares > 0 else 1)
            spin.valueChanged.connect(self._previsualizar)
            self.tbl_etiquetas.setCellWidget(i, 4, spin)
        if self.tbl_etiquetas.rowCount():
            self.tbl_etiquetas.setCurrentCell(0, 0)

    def _datos_fila(self, row: int) -> dict:
        if row < 0:
            return {}
        return {
            "modelo": self.tbl_etiquetas.item(row, 0).text(),
            "corte": self.tbl_etiquetas.item(row, 1).text(),
            "color": self.tbl_etiquetas.item(row, 2).text(),
            "talla": self.tbl_etiquetas.item(row, 3).text(),
        }

    def _fila_seleccionada(self) -> int:
        return self.tbl_etiquetas.currentRow()

    def _previsualizar(self) -> None:
        if not hasattr(self, "lbl_vista"):
            return
        datos = self._datos_fila(self._fila_seleccionada())
        pix = render_etiqueta_termica_pixmap(datos)
        self.lbl_vista.setPixmap(pix.scaled(
            QSize(_PREVIEW_W, _PREVIEW_H),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    def _filas_impresion(self) -> list[tuple[str, str, str, str, int]]:
        filas = []
        for row in range(self.tbl_etiquetas.rowCount()):
            spin = self.tbl_etiquetas.cellWidget(row, 4)
            cantidad = spin.value() if spin else 0
            if cantidad > 0:
                d = self._datos_fila(row)
                filas.append((d["modelo"], d["corte"], d["color"],
                              d["talla"], cantidad))
        return filas

    def _imprimir(self) -> None:
        filas = self._filas_impresion()
        if not filas:
            QMessageBox.information(self, "Cantidad",
                                    "Indique al menos una cantidad por talla.")
            return
        total = sum(c for _, _, _, _, c in filas)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_printer(printer)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        printer.setDocName("Etiquetas SIAC")
        try:
            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError(
                    "No se pudo iniciar el painter sobre la impresora. "
                    "Revisa el driver y que la cola de impresión no esté en error.")
            px_per_mm = printer.resolution() / 25.4
            n = 0
            for modelo, corte, color, talla, cantidad in filas:
                datos = {"modelo": modelo, "corte": corte,
                         "color": color, "talla": talla}
                for _ in range(cantidad):
                    if n > 0:
                        printer.newPage()
                    render_etiqueta_termica(painter, px_per_mm, datos)
                    n += 1
            painter.end()
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir",
                                 f"{type(e).__name__}: {e}")
            return
        QMessageBox.information(
            self, "Impresión",
            f"Se enviaron {total} etiquetas a la impresora.")

    def _vista_previa(self) -> None:
        datos = self._datos_fila(self._fila_seleccionada())
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_printer(printer)
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(
            lambda p: render_etiqueta_termica(p, p.resolution() / 25.4, datos))
        dlg.exec()

    def _guardar_pdf(self) -> None:
        datos = self._datos_fila(self._fila_seleccionada())
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar etiqueta PDF", f"etiqueta_{datos['talla']}.pdf",
            "PDF (*.pdf)")
        if not path:
            return
        etiqueta_termica_pdf(path, datos)
        QMessageBox.information(self, "PDF", f"Etiqueta guardada en:\n{path}")
