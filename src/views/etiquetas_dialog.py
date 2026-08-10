"""Apartado 'Imprimir Etiquetas' de Programación.

Captura el folio de programación (folio_prog), muestra las tallas de la
línea con el número de copias (una etiqueta por par) y permite imprimir
directo a la etiquetadora con el controlador de Windows, o editar el diseño
de la etiqueta (visor/editor) replicando etiquetaa.qdf.qdf.
"""
from PySide6.QtCore import QSize, QSizeF, Qt
from PySide6.QtGui import QPageSize, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.models.etiqueta_model import DATOS_ETIQUETA, EtiquetaModel
from src.utils.etiqueta_render import render_label, render_label_pixmap

_PREVIEW_W = 380
_PREVIEW_H = 256


def _cargar_pixmap_en(qlabel: QLabel, pixmap: QPixmap) -> None:
    qlabel.setPixmap(pixmap.scaled(
        QSize(_PREVIEW_W, _PREVIEW_H),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation))


class EtiquetasDialog(QDialog):
    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.etiquetas = EtiquetaModel()
        self._diseno = self.etiquetas.cargar_diseno()
        self._linea = None
        self.setWindowTitle("Imprimir Etiquetas")
        self.setMinimumWidth(760)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        captura = QHBoxLayout()
        captura.addWidget(QLabel("Folio Prog.:"))
        self.txt_folio = QLineEdit()
        self.txt_folio.setPlaceholderText("Ej. 873")
        self.txt_folio.setMinimumWidth(160)
        self.txt_folio.returnPressed.connect(self._buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setObjectName("btnPrimary")
        btn_buscar.clicked.connect(self._buscar)
        captura.addWidget(self.txt_folio)
        captura.addWidget(btn_buscar)
        captura.addStretch()
        layout.addLayout(captura)

        self.lbl_info = QLabel("Capture el folio de programación para cargar la línea.")
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)

        grupo = QGroupBox("Etiquetas por talla (una por par)")
        v = QVBoxLayout(grupo)
        self.tbl_copias = QTableWidget(0, 3)
        self.tbl_copias.setHorizontalHeaderLabels(["Talla", "Pares", "Copias"])
        self.tbl_copias.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_copias.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_copias.verticalHeader().setVisible(False)
        self.tbl_copias.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.tbl_copias.setMaximumHeight(180)
        self.tbl_copias.itemSelectionChanged.connect(self._previsualizar_seleccion)
        v.addWidget(self.tbl_copias)
        layout.addWidget(grupo)

        vista = QGroupBox("Vista previa de la etiqueta")
        vv = QHBoxLayout(vista)
        self.lbl_vista = QLabel("—")
        self.lbl_vista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vista.setFixedSize(_PREVIEW_W, _PREVIEW_H)
        self.lbl_vista.setStyleSheet(
            "border: 1px solid #cbd5e1; background: white; border-radius: 4px;")
        vv.addWidget(self.lbl_vista)
        vv.addStretch()
        layout.addWidget(vista)

        btns = QHBoxLayout()
        btn_editar = QPushButton("Editar Etiqueta")
        btn_editar.setObjectName("btnSecondary")
        btn_editar.clicked.connect(self._abrir_editor)
        self.btn_imprimir = QPushButton("Imprimir")
        self.btn_imprimir.setObjectName("btnPrimary")
        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        btns.addWidget(btn_editar)
        btns.addStretch()
        btns.addWidget(btn_cerrar)
        btns.addWidget(self.btn_imprimir)
        layout.addLayout(btns)

    # ---- Búsqueda de línea ----

    def _buscar(self) -> None:
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.information(self, "Folio", "Capture el folio de programación.")
            return
        linea = self.controller.buscar_linea_por_folio(folio)
        if not linea:
            QMessageBox.warning(self, "Sin resultados",
                                f"No se encontró una línea con folio prog. '{folio}'.")
            self._linea = None
            self.tbl_copias.setRowCount(0)
            self.btn_imprimir.setEnabled(False)
            self.lbl_info.setText("Capture el folio de programación para cargar la línea.")
            self.lbl_vista.setText("—")
            return
        linea = self.controller.obtener_linea_con_tallas(linea["id"])
        self._linea = linea
        self.lbl_info.setText(
            f"Folio: {linea.get('folio_prog', '')}   |   Cliente: "
            f"{linea.get('cliente', '')}   |   Modelo: {linea.get('modelo', '')}   |   "
            f"Piel: {linea.get('piel', '')}   |   Color: {linea.get('color', '')}")
        self._poblar_copias()
        self.btn_imprimir.setEnabled(True)

    def _poblar_copias(self) -> None:
        tallas = self._linea.get("tallas") or []
        if not tallas:
            tallas = [{"talla": "", "pares": 1}]
        self.tbl_copias.setRowCount(len(tallas))
        for i, t in enumerate(tallas):
            talla = str(t.get("talla", ""))
            pares = int(t.get("pares", 0) or 0)
            self.tbl_copias.setItem(i, 0, QTableWidgetItem(talla))
            self.tbl_copias.setItem(i, 1, QTableWidgetItem(str(pares)))
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(9999)
            spin.setValue(pares if pares > 0 else 1)
            spin.valueChanged.connect(self._previsualizar_seleccion)
            self.tbl_copias.setCellWidget(i, 2, spin)
        if self.tbl_copias.rowCount():
            self.tbl_copias.selectRow(0)

    # ---- Vista previa ----

    def _datos_talla(self, talla: str, pares: int) -> dict:
        linea = self._linea or {}
        return {
            "modelo": linea.get("modelo", ""),
            "corte": linea.get("piel", ""),
            "color": linea.get("color", ""),
            "talla": talla,
            "folio_prog": linea.get("folio_prog", ""),
            "cliente": linea.get("cliente", ""),
            "pares": pares,
            "fecha_prog": linea.get("fecha_prog", "") or "",
        }

    def _previsualizar_seleccion(self) -> None:
        if not self._linea:
            return
        fila = self.tbl_copias.currentRow()
        if fila < 0:
            return
        talla = self.tbl_copias.item(fila, 0).text()
        pares = int(self.tbl_copias.item(fila, 1).text() or 0)
        pix = render_label_pixmap(self._diseno, self._datos_talla(talla, pares))
        _cargar_pixmap_en(self.lbl_vista, pix)

    # ---- Impresión ----

    def _imprimir(self) -> None:
        if not self._linea:
            return
        filas = []
        for i in range(self.tbl_copias.rowCount()):
            talla = self.tbl_copias.item(i, 0).text()
            pares = int(self.tbl_copias.item(i, 1).text() or 0)
            spin = self.tbl_copias.cellWidget(i, 2)
            copias = spin.value() if spin else pares
            if copias > 0:
                filas.append((talla, pares, copias))
        if not filas:
            QMessageBox.information(self, "Copias",
                                    "Indique al menos una copia por talla.")
            return
        total = sum(c for _, _, c in filas)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(
            QSizeF(self._diseno.get("ancho_mm", 76.0),
                   self._diseno.get("alto_mm", 51.0)),
            QPageSize.Unit.Millimeter))
        printer.setFullPage(True)
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
            for talla, pares, copias in filas:
                datos = self._datos_talla(talla, pares)
                for _ in range(copias):
                    if n > 0:
                        printer.newPage()
                    render_label(painter, self._diseno, datos, px_per_mm)
                    n += 1
            painter.end()
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir", f"{type(e).__name__}: {e}")
            return
        QMessageBox.information(self, "Impresión",
                                f"Se enviaron {total} etiquetas a la impresora.")

    # ---- Editor ----

    def _abrir_editor(self) -> None:
        dlg = EtiquetaEditorDialog(self.etiquetas, self._diseno, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._diseno = self.etiquetas.cargar_diseno()
            self._previsualizar_seleccion()


class EtiquetaEditorDialog(QDialog):
    def __init__(self, etiquetas: EtiquetaModel, diseno: dict,
                 parent=None) -> None:
        super().__init__(parent)
        self.etiquetas = etiquetas
        self._diseno = diseno
        self.setWindowTitle("Editor de Etiqueta")
        self.setMinimumWidth(860)
        self.setMinimumHeight(520)
        self._setup_ui()
        self._cargar_diseno()
        self._preview()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        medidas = QFormLayout()
        self.sp_ancho = QDoubleSpinBox()
        self.sp_ancho.setRange(10, 200)
        self.sp_ancho.setSuffix(" mm")
        self.sp_ancho.setDecimals(1)
        self.sp_alto = QDoubleSpinBox()
        self.sp_alto.setRange(10, 150)
        self.sp_alto.setSuffix(" mm")
        self.sp_alto.setDecimals(1)
        for sp in (self.sp_ancho, self.sp_alto):
            sp.valueChanged.connect(self._preview)
        medidas.addRow("Ancho:", self.sp_ancho)
        medidas.addRow("Alto:", self.sp_alto)
        layout.addLayout(medidas)

        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(
            ["Visible", "Tipo", "Contenido", "X (mm)", "Y (mm)", "Tamaño", "Negrita"])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tbl)

        self.lbl_vista = QLabel("—")
        self.lbl_vista.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_vista.setFixedSize(_PREVIEW_W, _PREVIEW_H)
        self.lbl_vista.setStyleSheet(
            "border: 1px solid #cbd5e1; background: white; border-radius: 4px;")
        layout.addWidget(self.lbl_vista)

        btns = QDialogButtonBox()
        btn_guardar = btns.addButton("Guardar", QDialogButtonBox.AcceptRole)
        btn_guardar.setObjectName("btnPrimary")
        btns.addButton(QDialogButtonBox.Cancel)
        btns.accepted.connect(self._guardar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    # ---- Carga ----

    def _cargar_diseno(self) -> None:
        self.sp_ancho.setValue(float(self._diseno.get("ancho_mm", 76.0)))
        self.sp_alto.setValue(float(self._diseno.get("alto_mm", 51.0)))
        campos = self._diseno.get("campos", [])
        self.tbl.setRowCount(len(campos))
        for i, c in enumerate(campos):
            chk = QCheckBox()
            chk.setChecked(bool(c.get("visible", True)))
            chk.toggled.connect(self._preview)
            self.tbl.setCellWidget(i, 0, chk)

            cmb_tipo = QComboBox()
            cmb_tipo.addItem("Texto fijo", "texto")
            cmb_tipo.addItem("Dato", "dato")
            cmb_tipo.setCurrentIndex(0 if c.get("tipo") == "texto" else 1)
            cmb_tipo.currentIndexChanged.connect(self._tipo_cambia)
            cmb_tipo.currentIndexChanged.connect(self._preview)
            self.tbl.setCellWidget(i, 1, cmb_tipo)
            self._set_contenido(i, c)

            sp_x = QDoubleSpinBox()
            sp_x.setRange(0, 200)
            sp_x.setSuffix(" mm")
            sp_x.setValue(float(c.get("x_mm", 0)))
            sp_x.setDecimals(1)
            sp_x.valueChanged.connect(self._preview)
            self.tbl.setCellWidget(i, 3, sp_x)

            sp_y = QDoubleSpinBox()
            sp_y.setRange(0, 150)
            sp_y.setSuffix(" mm")
            sp_y.setValue(float(c.get("y_mm", 0)))
            sp_y.setDecimals(1)
            sp_y.valueChanged.connect(self._preview)
            self.tbl.setCellWidget(i, 4, sp_y)

            sp_size = QSpinBox()
            sp_size.setRange(6, 72)
            sp_size.setValue(int(c.get("size", 12)))
            sp_size.valueChanged.connect(self._preview)
            self.tbl.setCellWidget(i, 5, sp_size)

            chk_bold = QCheckBox()
            chk_bold.setChecked(bool(c.get("bold", False)))
            chk_bold.toggled.connect(self._preview)
            self.tbl.setCellWidget(i, 6, chk_bold)

    def _set_contenido(self, fila: int, c: dict) -> None:
        if c.get("tipo") == "dato":
            cmb = QComboBox()
            keys = [k for k, _ in DATOS_ETIQUETA]
            cmb.addItems(keys)
            idx = keys.index(c.get("dato")) if c.get("dato") in keys else 0
            cmb.setCurrentIndex(idx)
            cmb.currentIndexChanged.connect(self._preview)
            self.tbl.setCellWidget(fila, 2, cmb)
        else:
            ed = QLineEdit(c.get("texto", ""))
            ed.textChanged.connect(self._preview)
            self.tbl.setCellWidget(fila, 2, ed)

    def _tipo_cambia(self, _idx: int) -> None:
        fila = self.tbl.currentRow()
        if fila < 0:
            return
        cmb_tipo = self.tbl.cellWidget(fila, 1)
        actual = cmb_tipo.currentData()
        c = {"tipo": "dato" if actual == "dato" else "texto",
             "dato": DATOS_ETIQUETA[0][0],
             "texto": "", "x_mm": 0, "y_mm": 0, "size": 12,
             "bold": False, "visible": True}
        self._set_contenido(fila, c)

    # ---- Vista previa ----

    def _datos_muestra(self) -> dict:
        return {
            "modelo": "9201", "corte": "PIEL CRAZY", "color": "CAF",
            "talla": "12.0", "folio_prog": "873",
            "cliente": "LORENZO RUBIO", "pares": 12, "fecha_prog": "2026-08-05",
        }

    def _preview(self) -> None:
        diseno = self._leer_diseno()
        pix = render_label_pixmap(diseno, self._datos_muestra())
        _cargar_pixmap_en(self.lbl_vista, pix)

    # ---- Lectura / guardado ----

    def _leer_diseno(self) -> dict:
        campos = []
        for i in range(self.tbl.rowCount()):
            chk = self.tbl.cellWidget(i, 0)
            cmb_tipo = self.tbl.cellWidget(i, 1)
            cont = self.tbl.cellWidget(i, 2)
            sp_x = self.tbl.cellWidget(i, 3)
            sp_y = self.tbl.cellWidget(i, 4)
            sp_size = self.tbl.cellWidget(i, 5)
            chk_bold = self.tbl.cellWidget(i, 6)
            tipo = cmb_tipo.currentData() if cmb_tipo else "texto"
            c = {
                "tipo": tipo,
                "x_mm": float(sp_x.value() if sp_x else 0),
                "y_mm": float(sp_y.value() if sp_y else 0),
                "size": int(sp_size.value() if sp_size else 12),
                "bold": bool(chk_bold.isChecked() if chk_bold else False),
                "visible": bool(chk.isChecked() if chk else True),
            }
            if tipo == "dato":
                c["dato"] = cont.currentText() if isinstance(cont, QComboBox) else ""
            else:
                c["texto"] = cont.text() if isinstance(cont, QLineEdit) else ""
            campos.append(c)
        return {
            "ancho_mm": self.sp_ancho.value(),
            "alto_mm": self.sp_alto.value(),
            "campos": campos,
        }

    def _guardar(self) -> None:
        self.etiquetas.guardar_diseno(self._leer_diseno())
        self.accept()
