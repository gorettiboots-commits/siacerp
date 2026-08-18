"""Apartado 'Imprimir Etiquetas' de Programación.

Captura el folio de programación (folio_prog), muestra las tallas de la
línea con el número de copias (una etiqueta por par) y permite imprimir
directo a la etiquetadora con el controlador de Windows. Incluye edición
inline del diseño de la etiqueta (medidas y campos con vista previa en
tiempo real), botón 'Imprimir Muestra' para probar el diseño con datos de
ejemplo y botón 'Imprimir' para la línea cargada. El diseño replicado es
etiquetaa.qdf.qdf.
"""
from functools import partial

from PySide6.QtCore import QSize, QSizeF, Qt
from PySide6.QtGui import QPageSize, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog,
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
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
        self._cargando = False
        self.setWindowTitle("Imprimir Etiquetas")
        self.setMinimumSize(780, 680)
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
        self.tbl_copias.setMaximumHeight(150)
        self.tbl_copias.itemSelectionChanged.connect(self._previsualizar_seleccion)
        v.addWidget(self.tbl_copias)
        layout.addWidget(grupo)

        editor = QGroupBox("Diseño de la etiqueta (edición inline)")
        ev = QVBoxLayout(editor)
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
            sp.valueChanged.connect(self._previsualizar_seleccion)
        medidas.addRow("Ancho:", self.sp_ancho)
        medidas.addRow("Alto:", self.sp_alto)
        ev.addLayout(medidas)

        self.tbl_campos = QTableWidget(0, 7)
        self.tbl_campos.setHorizontalHeaderLabels(
            ["Visible", "Tipo", "Contenido", "X (mm)", "Y (mm)", "Tamaño", "Negrita"])
        self.tbl_campos.verticalHeader().setVisible(False)
        self.tbl_campos.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.tbl_campos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_campos.setMaximumHeight(200)
        ev.addWidget(self.tbl_campos)

        toolbar = QHBoxLayout()
        btn_agregar = QPushButton("Agregar campo")
        btn_agregar.setObjectName("btnSecondary")
        btn_agregar.clicked.connect(self._agregar_campo)
        btn_quitar = QPushButton("Quitar campo")
        btn_quitar.setObjectName("btnSecondary")
        btn_quitar.clicked.connect(self._quitar_campo)
        btn_guardar = QPushButton("Guardar Diseño")
        btn_guardar.setObjectName("btnPrimary")
        btn_guardar.clicked.connect(self._guardar_diseno)
        toolbar.addWidget(btn_agregar)
        toolbar.addWidget(btn_quitar)
        toolbar.addStretch()
        toolbar.addWidget(btn_guardar)
        ev.addLayout(toolbar)
        layout.addWidget(editor)

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
        btn_muestra = QPushButton("Imprimir Muestra")
        btn_muestra.setObjectName("btnSecondary")
        btn_muestra.clicked.connect(self._imprimir_muestra)
        self.btn_imprimir = QPushButton("Imprimir")
        self.btn_imprimir.setObjectName("btnPrimary")
        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.clicked.connect(self._imprimir)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        btns.addWidget(btn_muestra)
        btns.addStretch()
        btns.addWidget(btn_cerrar)
        btns.addWidget(self.btn_imprimir)
        layout.addLayout(btns)

        self._cargar_diseno()

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

    def _datos_muestra(self) -> dict:
        return {
            "modelo": "9201", "corte": "PIEL CRAZY", "color": "CAF",
            "talla": "12.0", "folio_prog": "873",
            "cliente": "LORENZO RUBIO", "pares": 12, "fecha_prog": "2026-08-05",
        }

    def _previsualizar_seleccion(self, *_args) -> None:
        if self._cargando or not hasattr(self, "tbl_campos") \
                or self.tbl_campos.rowCount() == 0:
            return
        self._diseno = self._leer_diseno()
        fila = self.tbl_copias.currentRow()
        if fila < 0 or not self._linea:
            datos = self._datos_muestra()
        else:
            talla = self.tbl_copias.item(fila, 0).text()
            pares = int(self.tbl_copias.item(fila, 1).text() or 0)
            datos = self._datos_talla(talla, pares)
        pix = render_label_pixmap(self._diseno, datos)
        _cargar_pixmap_en(self.lbl_vista, pix)

    # ---- Edición inline del diseño ----

    def _cargar_diseno(self) -> None:
        self._cargando = True
        try:
            self.sp_ancho.setValue(float(self._diseno.get("ancho_mm", 76.0)))
            self.sp_alto.setValue(float(self._diseno.get("alto_mm", 51.0)))
            campos = self._diseno.get("campos", [])
            self.tbl_campos.setRowCount(len(campos))
            for i, c in enumerate(campos):
                self._crear_fila(i, c)
        finally:
            self._cargando = False
        self._previsualizar_seleccion()

    def _crear_fila(self, fila: int, c: dict) -> None:
        chk = QCheckBox()
        chk.setChecked(bool(c.get("visible", True)))
        chk.toggled.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 0, chk)

        cmb_tipo = QComboBox()
        cmb_tipo.addItem("Texto fijo", "texto")
        cmb_tipo.addItem("Dato", "dato")
        cmb_tipo.setCurrentIndex(0 if c.get("tipo") == "texto" else 1)
        cmb_tipo.currentIndexChanged.connect(
            partial(self._tipo_cambia, fila))
        cmb_tipo.currentIndexChanged.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 1, cmb_tipo)
        self._set_contenido(fila, c)

        sp_x = QDoubleSpinBox()
        sp_x.setRange(0, 200)
        sp_x.setSuffix(" mm")
        sp_x.setValue(float(c.get("x_mm", 0)))
        sp_x.setDecimals(1)
        sp_x.valueChanged.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 3, sp_x)

        sp_y = QDoubleSpinBox()
        sp_y.setRange(0, 150)
        sp_y.setSuffix(" mm")
        sp_y.setValue(float(c.get("y_mm", 0)))
        sp_y.setDecimals(1)
        sp_y.valueChanged.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 4, sp_y)

        sp_size = QSpinBox()
        sp_size.setRange(6, 72)
        sp_size.setValue(int(c.get("size", 12)))
        sp_size.valueChanged.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 5, sp_size)

        chk_bold = QCheckBox()
        chk_bold.setChecked(bool(c.get("bold", False)))
        chk_bold.toggled.connect(self._previsualizar_seleccion)
        self.tbl_campos.setCellWidget(fila, 6, chk_bold)

    def _set_contenido(self, fila: int, c: dict) -> None:
        if c.get("tipo") == "dato":
            cmb = QComboBox()
            keys = [k for k, _ in DATOS_ETIQUETA]
            cmb.addItems(keys)
            idx = keys.index(c.get("dato")) if c.get("dato") in keys else 0
            cmb.setCurrentIndex(idx)
            cmb.currentIndexChanged.connect(self._previsualizar_seleccion)
            self.tbl_campos.setCellWidget(fila, 2, cmb)
        else:
            ed = QLineEdit(c.get("texto", ""))
            ed.textChanged.connect(self._previsualizar_seleccion)
            self.tbl_campos.setCellWidget(fila, 2, ed)

    def _tipo_cambia(self, fila: int, _idx: int = 0) -> None:
        if self._cargando:
            return
        cmb_tipo = self.tbl_campos.cellWidget(fila, 1)
        if not cmb_tipo:
            return
        actual = cmb_tipo.currentData()
        c = {"tipo": "dato" if actual == "dato" else "texto",
             "dato": DATOS_ETIQUETA[0][0],
             "texto": "", "x_mm": 0, "y_mm": 0, "size": 12,
             "bold": False, "visible": True}
        self._set_contenido(fila, c)

    def _leer_diseno(self) -> dict:
        campos = []
        for i in range(self.tbl_campos.rowCount()):
            chk = self.tbl_campos.cellWidget(i, 0)
            cmb_tipo = self.tbl_campos.cellWidget(i, 1)
            cont = self.tbl_campos.cellWidget(i, 2)
            sp_x = self.tbl_campos.cellWidget(i, 3)
            sp_y = self.tbl_campos.cellWidget(i, 4)
            sp_size = self.tbl_campos.cellWidget(i, 5)
            chk_bold = self.tbl_campos.cellWidget(i, 6)
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

    def _agregar_campo(self) -> None:
        fila = self.tbl_campos.rowCount()
        self.tbl_campos.insertRow(fila)
        self._crear_fila(fila, {"tipo": "texto", "texto": "",
                                "x_mm": 0, "y_mm": 0, "size": 12,
                                "bold": False, "visible": True})
        self._previsualizar_seleccion()

    def _quitar_campo(self) -> None:
        fila = self.tbl_campos.currentRow()
        if fila < 0:
            fila = self.tbl_campos.rowCount() - 1
        if fila < 0:
            return
        self.tbl_campos.removeRow(fila)
        self._previsualizar_seleccion()

    def _guardar_diseno(self) -> None:
        self._diseno = self._leer_diseno()
        self.etiquetas.guardar_diseno(self._diseno)
        QMessageBox.information(self, "Diseño", "Diseño de etiqueta guardado.")

    # ---- Impresión ----

    def _imprimir(self) -> None:
        if not self._linea:
            return
        self._diseno = self._leer_diseno()
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

    def _imprimir_muestra(self) -> None:
        self._diseno = self._leer_diseno()
        diseno = self._diseno
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(
            QSizeF(diseno.get("ancho_mm", 76.0),
                   diseno.get("alto_mm", 51.0)),
            QPageSize.Unit.Millimeter))
        printer.setFullPage(True)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        printer.setDocName("Etiqueta muestra SIAC")
        try:
            painter = QPainter(printer)
            if not painter.isActive():
                raise RuntimeError(
                    "No se pudo iniciar el painter sobre la impresora. "
                    "Revisa el driver y que la cola de impresión no esté en error.")
            px_per_mm = printer.resolution() / 25.4
            render_label(painter, diseno, self._datos_muestra(), px_per_mm)
            painter.end()
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir", f"{type(e).__name__}: {e}")
            return
        QMessageBox.information(self, "Impresión",
                                "Etiqueta de muestra enviada a la impresora.")
