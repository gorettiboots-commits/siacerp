"""Apartado 'Imprimir Etiquetas' de Programación.

Ofrece dos modos de impresión de etiquetas:

- **Flejes (Cajas)**: tabla de partidas. Cada partida indica el texto del
  label y la cantidad de etiquetas; la etiqueta es solo el texto a lo ancho
  total de la etiqueta y se imprime tantas veces como indique la cantidad.
- **Partidas**: captura manual de modelo, corte y color, más una matriz de
  tallas con la cantidad de etiquetas por punto/talla. Imprime con el diseño
  guardado (etiquetaa.qdf.qdf), una etiqueta por copia, usando modelo, corte,
  color y talla.

Ambos modos imprimen directo a la etiquetadora con el controlador de Windows
(impresora real o virtual según Configuración).
"""
from PySide6.QtCore import QSizeF
from PySide6.QtGui import QPageSize, QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QVBoxLayout,
)

from src.components.notificacion_flotante import notificar_flotante
from src.components.tallas_matrix import MatrizTallasWidget
from src.models.etiqueta_model import EtiquetaModel
from src.utils.etiqueta_render import render_label
from src.utils.impresion_virtual import dialogo_impresion

_MARGEN_MM = 4.0


def crear_diseno_fleje(diseno_base: dict, texto: str) -> dict:
    """Diseño de etiqueta 'fleje': solo el texto centrado a lo ancho total."""
    ancho = float(diseno_base.get("ancho_mm", 76.0))
    alto = float(diseno_base.get("alto_mm", 51.0))
    return {
        "ancho_mm": ancho,
        "alto_mm": alto,
        "campos": [{
            "tipo": "texto", "texto": texto,
            "x_mm": _MARGEN_MM, "y_mm": _MARGEN_MM,
            "ancho_mm": ancho - 2 * _MARGEN_MM,
            "alto_mm": alto - 2 * _MARGEN_MM,
            "size": 14, "bold": True, "cursiva": False,
            "auto_fit": True,
            "alineacion": "centro", "borde_visible": False, "visible": True,
        }],
    }


def _imprimir_copias(parent, filas: list[tuple[dict, dict, int]]) -> int:
    """Envía a impresión las copias indicadas.

    `filas`: lista de (diseno, datos, copias). Cada par (diseno, datos) se
    imprime `copias` veces en páginas sucesivas. Devuelve el total impreso.
    """
    diseno = filas[0][0] if filas else {}
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setPageSize(QPageSize(
        QSizeF(float(diseno.get("ancho_mm", 76.0)),
               float(diseno.get("alto_mm", 51.0))),
        QPageSize.Unit.Millimeter))
    printer.setFullPage(True)
    printer.setDocName("Etiquetas SIAC")

    total = sum(copias for _diseno, _datos, copias in filas)

    def pintar(p: QPrinter) -> None:
        painter = QPainter(p)
        if not painter.isActive():
            raise RuntimeError(
                "No se pudo iniciar el painter sobre la impresora. "
                "Revisa el driver y que la cola de impresión no esté en error.")
        px_per_mm = p.resolution() / 25.4
        n = 0
        for diseno_etiqueta, datos, copias in filas:
            for _ in range(copias):
                if n > 0:
                    p.newPage()
                render_label(painter, diseno_etiqueta, datos, px_per_mm)
                n += 1
        painter.end()

    try:
        estado = dialogo_impresion(printer, parent, pintar)
    except Exception as e:
        QMessageBox.critical(parent, "Error al imprimir", f"{type(e).__name__}: {e}")
        return 0
    if estado == "impreso":
        notificar_flotante(f"Se enviaron {total} etiquetas a la impresora.",
                           tipo="success", titulo="Impresión", host=parent)
    elif estado == "simulado":
        notificar_flotante("Simulación en pantalla: no se envió a la impresora.",
                           tipo="info", titulo="Impresora virtual", host=parent)
    return total


class DialogEtiquetasFlejes(QDialog):
    """Partidas de etiquetas para flejes/cajas.

    Cada fila define el texto del label y la cantidad de etiquetas. La
    etiqueta es solo el texto centrado a lo ancho total de la etiqueta.
    """

    def __init__(self, diseno: dict, parent=None) -> None:
        super().__init__(parent)
        self._diseno_base = diseno
        self.setWindowTitle("Etiquetas para Flejes (Cajas)")
        self.setMinimumSize(560, 420)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("Agregue las partidas: el texto que dirá la etiqueta y "
                      "la cantidad de etiquetas con ese texto.")
        info.setObjectName("sectionSubtitle")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.tbl_partidas = QTableWidget(0, 2)
        self.tbl_partidas.setHorizontalHeaderLabels(["Texto de la etiqueta", "Cantidad"])
        self.tbl_partidas.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_partidas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_partidas.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl_partidas)

        toolbar = QHBoxLayout()
        btn_agregar = QPushButton("Agregar partida")
        btn_agregar.setObjectName("btnSecondary")
        btn_agregar.clicked.connect(self._agregar_partida)
        btn_quitar = QPushButton("Quitar partida")
        btn_quitar.setObjectName("btnSecondary")
        btn_quitar.clicked.connect(self._quitar_partida)
        toolbar.addWidget(btn_agregar)
        toolbar.addWidget(btn_quitar)
        toolbar.addStretch()
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setObjectName("btnPrimary")
        btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        toolbar.addWidget(btn_cerrar)
        toolbar.addWidget(btn_imprimir)
        layout.addLayout(toolbar)

        self._agregar_partida()

    def _agregar_partida(self) -> None:
        fila = self.tbl_partidas.rowCount()
        self.tbl_partidas.insertRow(fila)
        ed = QLineEdit()
        ed.setPlaceholderText("Texto de la etiqueta")
        self.tbl_partidas.setCellWidget(fila, 0, ed)
        spin = QSpinBox()
        spin.setRange(1, 99999)
        spin.setValue(1)
        self.tbl_partidas.setCellWidget(fila, 1, spin)
        ed.setFocus()

    def _quitar_partida(self) -> None:
        fila = self.tbl_partidas.currentRow()
        if fila >= 0:
            self.tbl_partidas.removeRow(fila)
        if self.tbl_partidas.rowCount() == 0:
            self._agregar_partida()

    def _diseno_fleje(self, texto: str) -> dict:
        return crear_diseno_fleje(self._diseno_base, texto)

    def _imprimir(self) -> None:
        filas = []
        for i in range(self.tbl_partidas.rowCount()):
            ed = self.tbl_partidas.cellWidget(i, 0)
            spin = self.tbl_partidas.cellWidget(i, 1)
            texto = ed.text().strip() if ed else ""
            cantidad = spin.value() if spin else 1
            if texto:
                filas.append((self._diseno_fleje(texto), {}, cantidad))
        if not filas:
            QMessageBox.information(self, "Partidas",
                                    "Agregue al menos una partida con texto.")
            return
        _imprimir_copias(self, filas)


class DialogEtiquetasPartidas(QDialog):
    """Etiquetas por partidas: matriz de tallas con cantidad por punto.

    Captura manualmente modelo, corte y color, y la cantidad de etiquetas por
    cada talla en la matriz. Imprime con el diseño guardado, una etiqueta por
    copia.
    """

    def __init__(self, diseno: dict, parent=None) -> None:
        super().__init__(parent)
        self._diseno = diseno
        self.setWindowTitle("Etiquetas por Partidas")
        self.setMinimumSize(760, 600)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        self.txt_modelo = QLineEdit()
        self.txt_corte = QLineEdit()
        self.txt_color = QLineEdit()
        form.addRow("Modelo:", self.txt_modelo)
        form.addRow("Corte:", self.txt_corte)
        form.addRow("Color:", self.txt_color)
        layout.addLayout(form)

        self.matriz = MatrizTallasWidget(titulo="CANTIDAD DE ETIQUETAS POR TALLA")
        layout.addWidget(self.matriz, 1)

        bar = QHBoxLayout()
        bar.addStretch()
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setObjectName("btnPrimary")
        btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        bar.addWidget(btn_cerrar)
        bar.addWidget(btn_imprimir)
        layout.addLayout(bar)

    def _imprimir(self) -> None:
        modelo = self.txt_modelo.text().strip()
        corte = self.txt_corte.text().strip()
        color = self.txt_color.text().strip()
        if not modelo or not corte or not color:
            QMessageBox.information(self, "Datos",
                                    "Capture modelo, corte y color.")
            return
        valores = self.matriz.obtener_valores()
        filas = []
        for p in self.matriz.tallas:
            clave = str(p.get("id", ""))
            cantidad = int(valores.get(clave, 0) or 0)
            if cantidad > 0:
                talla = str(p.get("talla", "") or "")
                datos = {"modelo": modelo, "corte": corte, "color": color,
                         "talla": talla}
                filas.append((self._diseno, datos, cantidad))
        if not filas:
            QMessageBox.information(self, "Cantidades",
                                    "Indique al menos una cantidad por talla.")
            return
        _imprimir_copias(self, filas)


class EtiquetasDialog(QDialog):
    """Selector de modo de impresión de etiquetas de Programación."""

    def __init__(self, controller=None, parent=None) -> None:
        super().__init__(parent)
        self.etiquetas = EtiquetaModel()
        self._diseno = self.etiquetas.cargar_diseno()
        self.setWindowTitle("Imprimir Etiquetas")
        self.setMinimumSize(420, 260)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel("Seleccione el tipo de etiquetas a imprimir:")
        info.setObjectName("sectionSubtitle")
        layout.addWidget(info)

        btn_flejes = QPushButton("Flejes (Cajas)")
        btn_flejes.setObjectName("btnPrimary")
        btn_flejes.setMinimumHeight(52)
        btn_flejes.clicked.connect(self._abrir_flejes)
        layout.addWidget(btn_flejes)

        btn_partidas = QPushButton("Partidas")
        btn_partidas.setObjectName("btnPrimary")
        btn_partidas.setMinimumHeight(52)
        btn_partidas.clicked.connect(self._abrir_partidas)
        layout.addWidget(btn_partidas)

        bar = QHBoxLayout()
        bar.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        bar.addWidget(btn_cerrar)
        layout.addLayout(bar)

    def _abrir_flejes(self) -> None:
        dlg = DialogEtiquetasFlejes(self._diseno, self)
        dlg.exec()

    def _abrir_partidas(self) -> None:
        dlg = DialogEtiquetasPartidas(self._diseno, self)
        dlg.exec()