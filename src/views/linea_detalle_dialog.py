"""Diálogo de detalle de una línea de programación con editor de etiqueta.

Muestra los datos de la línea y, en el área de impresión, permite:
  - Editar Modelo/Corte/Color (solo afectan la impresión) y capturar la
    cantidad de pares por talla con MatrizTallasWidget.
  - Diseñar el layout de la etiqueta en vivo: lienzo con arrastre (drag &
    drop) y redimensionado; cada elemento se edita con doble clic
    (propiedades, coordenadas, borde, tipografía, color, etc.) y la plantilla
    se guarda en etiqueta_config.
  - Imprimir una muestra con los datos actuales, imprimir todas las etiquetas
    o exportar a PDF, respetando exactamente el layout definido en la
    plantilla.
"""
from PySide6.QtCore import QSizeF, Qt
from PySide6.QtGui import QPageSize, QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.components.editor_etiqueta import (
    DialogoPropiedadesCampo, LabelCanvas, normalizar_diseno,
)
from src.components.notificacion_flotante import notificar_flotante
from src.components.tallas_matrix import MatrizTallasWidget
from src.models.etiqueta_model import EtiquetaModel
from src.utils.etiqueta_render import render_label

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
        self._valores: dict[str, int] = self._valores_iniciales()
        self._talla_actual = ""
        self.etiquetas = EtiquetaModel()
        self._diseno = normalizar_diseno(self.etiquetas.cargar_diseno())
        self.setWindowTitle("Detalle de Línea — Editor de Etiqueta")
        self.setMinimumSize(1000, 660)
        self._setup_ui()

    def _valores_iniciales(self) -> dict[str, int]:
        valores: dict[str, int] = {}
        for t in self._linea.get("tallas") or []:
            talla = str(t.get("talla", "") or "").strip()
            if talla:
                valores[talla] = int(t.get("pares", 0) or 0)
        return valores

    def _puntos_linea(self) -> list[dict]:
        tallas = self._linea.get("tallas") or []
        return [
            {"id": i, "punto": str(t.get("talla", "")).strip()}
            for i, t in enumerate(tallas)
            if str(t.get("talla", "")).strip()
        ]

    # ---- UI ----

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        datos = QFormLayout()
        campos = [
            ("Folio Prog.:", self._linea.get("folio_prog", "")),
            ("Cliente:", self._linea.get("cliente", "")),
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

        grp_datos = QWidget()
        form = QFormLayout(grp_datos)
        self.txt_modelo = QLineEdit(str(self._linea.get("modelo", "") or ""))
        self.txt_corte = QLineEdit(str(self._linea.get("piel", "") or ""))
        self.txt_color = QLineEdit(str(self._linea.get("color", "") or ""))
        for etiqueta, txt in (("Modelo:", self.txt_modelo),
                              ("Corte:", self.txt_corte),
                              ("Color:", self.txt_color)):
            txt.textChanged.connect(self._refrescar_vista)
            form.addRow(etiqueta, txt)
        layout.addWidget(grp_datos)

        self.matriz = MatrizTallasWidget(self._puntos_linea(), "PARES A IMPRIMIR")
        self.matriz.establecer_valores(self._valores)
        self.matriz.valoresCambiados.connect(self._on_matriz_cambio)
        self.matriz.celdaSeleccionada.connect(self._on_celda_seleccionada)
        layout.addWidget(self.matriz)

        lbl_nota = QLabel(
            "Modelo/Corte/Color editados y pares por talla solo afectan la "
            "impresión; no se guardan. El diseño de la etiqueta sí se puede "
            "guardar como plantilla.")
        lbl_nota.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(lbl_nota)

        self.canvas = LabelCanvas()
        self.canvas.campoDobleClic.connect(self._editar_campo)
        layout.addWidget(self.canvas, 1)

        btns = QHBoxLayout()
        btn_pdf = QPushButton("Guardar PDF")
        btn_pdf.setObjectName("btnSecondary")
        btn_pdf.clicked.connect(self._guardar_pdf)
        btn_muestra = QPushButton("Imprimir Muestra")
        btn_muestra.setObjectName("btnSecondary")
        btn_muestra.clicked.connect(self._imprimir_muestra)
        btn_guardar = QPushButton("Guardar Plantilla / Formato")
        btn_guardar.setObjectName("btnPrimary")
        btn_guardar.clicked.connect(self._guardar_plantilla)
        btn_imprimir = QPushButton("Imprimir Etiquetas")
        btn_imprimir.setObjectName("btnPrimary")
        btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        btns.addWidget(btn_pdf)
        btns.addWidget(btn_muestra)
        btns.addWidget(btn_guardar)
        btns.addStretch()
        btns.addWidget(btn_cerrar)
        btns.addWidget(btn_imprimir)
        layout.addLayout(btns)

        if self._diseno["campos"]:
            self.canvas.seleccionar(0)
        self._refrescar_vista()

    # ---- Datos de la etiqueta ----

    def _talla_seleccionada(self) -> str:
        if self._talla_actual:
            return self._talla_actual
        for talla, cantidad in self._valores.items():
            if int(cantidad or 0) > 0:
                return talla
        for talla in self._valores:
            return talla
        return ""

    def _datos_etiqueta(self, talla: str | None = None) -> dict:
        return {
            "modelo": self.txt_modelo.text(),
            "corte": self.txt_corte.text(),
            "color": self.txt_color.text(),
            "talla": talla if talla is not None else self._talla_seleccionada(),
            "folio_prog": self._linea.get("folio_prog", ""),
            "cliente": self._linea.get("cliente", ""),
            "pares": sum(int(v or 0) for v in self._valores.values()),
            "fecha_prog": self._linea.get("fecha_prog", "") or "",
        }

    def _refrescar_vista(self, *_args) -> None:
        if hasattr(self, "canvas"):
            self.canvas.set_contenido(self._diseno, self._datos_etiqueta())

    def _on_matriz_cambio(self) -> None:
        self._valores = self.matriz.obtener_valores()
        self._refrescar_vista()

    def _on_celda_seleccionada(self, talla: str) -> None:
        self._talla_actual = talla
        self._refrescar_vista()

    # ---- Editor de diseño ----

    def _ancho_etiqueta(self) -> float:
        return float(self._diseno.get("ancho_mm", 76.0))

    def _editar_campo(self, idx: int) -> None:
        """Abre el diálogo de propiedades por doble clic y aplica los cambios."""
        campos = self._diseno.get("campos", [])
        if not (0 <= idx < len(campos)):
            return
        dlg = DialogoPropiedadesCampo(campos[idx], self._ancho_etiqueta(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            campos[idx] = dlg.campo_resultado()
            self._refrescar_vista()

    def _guardar_plantilla(self) -> None:
        self.etiquetas.guardar_diseno(self._diseno)
        notificar_flotante(
            "La plantilla de etiqueta quedó guardada. Se cargará en las "
            "próximas aperturas.",
            tipo="success", titulo="Plantilla guardada", host=self)

    # ---- Impresión / PDF (respeta el layout) ----

    def _filas_impresion(self) -> list[tuple[str, int]]:
        return [
            (talla, int(cantidad or 0))
            for talla, cantidad in self.matriz.obtener_valores().items()
            if int(cantidad or 0) > 0
        ]

    def _printer(self) -> QPrinter:
        p = QPrinter(QPrinter.PrinterMode.HighResolution)
        self._configurar_impresora(p)
        return p

    def _configurar_impresora(self, p: QPrinter) -> None:
        """Aplica el tamaño de página y full-page.

        Se llama también después del QPrintDialog: en Windows el diálogo puede
        reiniciar la configuración del QPrinter a la del controlador."""
        p.setPageSize(QPageSize(
            QSizeF(self._ancho_etiqueta(),
                   float(self._diseno.get("alto_mm", 51.0))),
            QPageSize.Unit.Millimeter))
        p.setFullPage(True)

    def _imprimir(self) -> None:
        filas = self._filas_impresion()
        if not filas:
            QMessageBox.information(self, "Cantidad",
                                    "Indique al menos una cantidad por talla.")
            return
        total = sum(c for _, c in filas)
        printer = self._printer()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._configurar_impresora(printer)
        printer.setDocName("Etiquetas SIAC")
        try:
            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError(
                    "No se pudo iniciar el painter sobre la impresora. "
                    "Revisa el driver y que la cola de impresión no esté en error.")
            px_per_mm = printer.resolution() / 25.4
            n = 0
            for talla, cantidad in filas:
                datos = self._datos_etiqueta(talla)
                for _ in range(cantidad):
                    if n > 0 and not printer.newPage():
                        raise RuntimeError(
                            "La impresora no aceptó una nueva página. "
                            "Revisa el driver y el tamaño del papel.")
                    render_label(painter, self._diseno, datos, px_per_mm)
                    n += 1
            if not painter.end():
                raise RuntimeError(
                    "No se pudo cerrar el trabajo de impresión. "
                    "Revisa la cola de impresión de Windows.")
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir",
                                 f"{type(e).__name__}: {e}")
            return
        notificar_flotante(f"Se enviaron {total} etiquetas a la impresora.",
                           tipo="success", titulo="Impresión", host=self)

    def _imprimir_muestra(self) -> None:
        """Imprime una sola etiqueta de muestra con los datos actuales."""
        printer = self._printer()
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._configurar_impresora(printer)
        printer.setDocName("Etiqueta muestra SIAC")
        try:
            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError(
                    "No se pudo iniciar el painter sobre la impresora. "
                    "Revisa el driver y que la cola de impresión no esté en error.")
            render_label(painter, self._diseno, self._datos_etiqueta(),
                         printer.resolution() / 25.4)
            if not painter.end():
                raise RuntimeError(
                    "No se pudo cerrar el trabajo de impresión. "
                    "Revisa la cola de impresión de Windows.")
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir",
                                 f"{type(e).__name__}: {e}")
            return
        notificar_flotante("Etiqueta de muestra enviada a la impresora.",
                           tipo="success", titulo="Impresión", host=self)

    def _guardar_pdf(self) -> None:
        talla = self._talla_seleccionada()
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar etiqueta PDF", f"etiqueta_{talla}.pdf", "PDF (*.pdf)")
        if not path:
            return
        printer = self._printer()
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        try:
            painter = QPainter(printer)
            render_label(painter, self._diseno, self._datos_etiqueta(),
                         printer.resolution() / 25.4)
            painter.end()
        except Exception as e:
            QMessageBox.critical(self, "Error al generar PDF",
                                 f"{type(e).__name__}: {e}")
            return
        QMessageBox.information(self, "PDF", f"Etiqueta guardada en:\n{path}")
