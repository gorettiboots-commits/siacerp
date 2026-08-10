from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QHeaderView, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.export_utils import export_table_to_excel, print_table
from src.utils.table_utils import NumericItem, configurar_tabla_excel
from src.utils.ui_helpers import crear_tarjeta
from src.views.etiqueta_prueba_dialog import EtiquetaPruebaDialog
from src.views.etiquetas_dialog import EtiquetasDialog
from src.views.linea_detalle_dialog import LineaDetalleDialog


_ESTATUS = {
    "programado": "Programado",
    "programacion_incompleta": "Programación Incompleta",
    "en_proceso": "En proceso",
    "producido": "Producido",
}

_ESTATUS_COLOR = {
    "programado": Qt.darkGreen,
    "programacion_incompleta": Qt.darkYellow,
    "en_proceso": Qt.blue,
    "producido": Qt.darkMagenta,
}

_FACTORES_AGRUPAR = {
    "cliente": "Cliente",
    "modelo": "Modelo",
    "piel": "Piel",
    "color": "Color",
}


def _fmt_estatus(estatus: str) -> str:
    return _ESTATUS.get(estatus, estatus.replace("_", " ").capitalize())


class ProgramacionView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ProgramacionController()
        self._talla_cols: list[tuple[int, str]] = []
        self._setup_ui()
        self._cargar_semanas()

    def set_permisos(self, permisos) -> None:
        self.btn_estatus.setEnabled(tiene(permisos, "programacion", "editar"))
        self.btn_folio_pedido.setEnabled(tiene(permisos, "programacion", "editar"))
        self.btn_export.setEnabled(tiene(permisos, "programacion", "exportar"))
        self.btn_print.setEnabled(tiene(permisos, "programacion", "exportar"))
        self.btn_etiquetas.setEnabled(tiene(permisos, "programacion", "exportar"))
        self.btn_etiqueta_prueba.setEnabled(tiene(permisos, "programacion", "exportar"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QFrame()
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel("Programación Semanal")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(
            "Programación de producción por semana. El folio mostrado es el folio de "
            "programación, distinto al folio de pedido.")
        subtitle.setObjectName("sectionSubtitle")
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.btn_estatus = QPushButton("Cambiar Estatus")
        self.btn_estatus.setObjectName("btnSecondary")
        self.btn_estatus.clicked.connect(self._cambiar_estatus)

        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(self._imprimir)

        self.btn_etiquetas = QPushButton("Imprimir Etiquetas")
        self.btn_etiquetas.setObjectName("btnPrimary")
        self.btn_etiquetas.clicked.connect(self._imprimir_etiquetas)

        self.btn_etiqueta_prueba = QPushButton("Etiqueta de Prueba")
        self.btn_etiqueta_prueba.setObjectName("btnSecondary")
        self.btn_etiqueta_prueba.clicked.connect(self._imprimir_etiqueta_prueba)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.clicked.connect(self._exportar)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_estatus)
        hlayout.addWidget(self.btn_print)
        hlayout.addWidget(self.btn_etiquetas)
        hlayout.addWidget(self.btn_etiqueta_prueba)
        hlayout.addWidget(self.btn_export)

        layout.addWidget(header)

        self._cards_row = QHBoxLayout()
        layout.addLayout(self._cards_row)

        self._setup_toolbar()
        layout.addLayout(self._toolbar)
        layout.addLayout(self._toolbar_agrupar)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        configurar_tabla_excel(self.table)
        self.table.cellDoubleClicked.connect(self._ver_detalle)
        layout.addWidget(self.table)

    def _setup_toolbar(self) -> None:
        self._toolbar = QHBoxLayout()

        self.cmb_semana = QComboBox()
        self.cmb_semana.setMinimumWidth(220)
        self.cmb_semana.currentIndexChanged.connect(self._on_semana_cambiada)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por cliente, modelo, folio, piel o color...")
        self.txt_buscar.setMinimumWidth(280)
        self.txt_buscar.textChanged.connect(self._recargar_tabla)

        self.txt_folio_pedido = QLineEdit()
        self.txt_folio_pedido.setPlaceholderText("Buscar folio de pedido...")
        self.txt_folio_pedido.setMinimumWidth(180)
        self.txt_folio_pedido.textChanged.connect(self._recargar_tabla)

        self.cmb_estatus = QComboBox()
        self.cmb_estatus.addItem("Todos los estatus", "")
        for valor, label in _ESTATUS.items():
            self.cmb_estatus.addItem(label, valor)
        self.cmb_estatus.currentIndexChanged.connect(self._recargar_tabla)

        self.cmb_agrupar = QComboBox()
        self.cmb_agrupar.addItem("Sin agrupar", None)
        for valor, label in _FACTORES_AGRUPAR.items():
            self.cmb_agrupar.addItem(f"Agrupar por {label}", valor)
        self.cmb_agrupar.currentIndexChanged.connect(self._recargar_tabla)

        self.btn_folio_pedido = QPushButton("Asignar Folio Pedido")
        self.btn_folio_pedido.setObjectName("btnSecondary")
        self.btn_folio_pedido.clicked.connect(self._asignar_folio_pedido)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self._cargar_semanas)

        self._toolbar.addWidget(QLabel("Semana:"))
        self._toolbar.addWidget(self.cmb_semana)
        self._toolbar.addSpacing(12)
        self._toolbar.addWidget(self.txt_buscar)
        self._toolbar.addWidget(self.txt_folio_pedido)
        self._toolbar.addWidget(self.cmb_estatus)
        self._toolbar.addWidget(btn_refresh)
        self._toolbar.addStretch()

        self._toolbar_agrupar = QHBoxLayout()
        self._toolbar_agrupar.addWidget(QLabel("Agrupar:"))
        self._toolbar_agrupar.addWidget(self.cmb_agrupar)
        self._toolbar_agrupar.addWidget(self.btn_folio_pedido)
        self._toolbar_agrupar.addStretch()

    def _cargar_semanas(self) -> None:
        semanas = self.controller.listar_semanas()
        idx = self.cmb_semana.currentIndex()
        self.cmb_semana.blockSignals(True)
        self.cmb_semana.clear()
        self.cmb_semana.addItem("Todas las semanas", None)
        for s in semanas:
            self.cmb_semana.addItem(s["nombre"], s["id"])
        self.cmb_semana.blockSignals(False)
        if semanas:
            if 0 <= idx < self.cmb_semana.count():
                self.cmb_semana.setCurrentIndex(idx)
            else:
                self.cmb_semana.setCurrentIndex(self.cmb_semana.count() - 1)
        self._cargar_cards(semanas)
        self._on_semana_cambiada()

    def _cargar_cards(self, semanas: list[dict]) -> None:
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        semana_id = self.cmb_semana.currentData()
        tot = self.controller.totales_semana(semana_id)
        if semana_id is None:
            self._cards_row.addWidget(crear_tarjeta(
                "Semanas cargadas", str(len(semanas)), "#64748b"))
        else:
            self._cards_row.addWidget(crear_tarjeta(
                "Semanas cargadas", str(len(semanas)), "#64748b"))
        self._cards_row.addWidget(crear_tarjeta("Líneas", str(tot["lineas"]), "#4f46e5"))
        self._cards_row.addWidget(crear_tarjeta("Pares", str(tot["pares"]), "#059669"))
        self._cards_row.addWidget(crear_tarjeta("Clientes", str(tot["clientes"]), "#d97706"))
        self._cards_row.addStretch()

    def _on_semana_cambiada(self) -> None:
        self._cargar_cards(self.controller.listar_semanas())
        self._recargar_tabla()

    def _recargar_tabla(self) -> None:
        semana_id = self.cmb_semana.currentData()
        estatus = self.cmb_estatus.currentData() or ""
        termino = self.txt_buscar.text().strip()
        folio_pedido = self.txt_folio_pedido.text().strip()

        es_todas = semana_id is None
        tallas = self.controller.tallas_semana(semana_id)
        lineas = self.controller.lineas_con_tallas(
            semana_id, termino, estatus, folio_pedido)

        fixed = ([("semana", "Semana")] + self._FIXED_COLS if es_todas
                 else self._FIXED_COLS)
        self._fixed_cols = fixed

        n_tallas = len(tallas)
        n_cols = len(fixed) + n_tallas + 2
        self._talla_cols = list(enumerate(tallas, start=len(fixed)))

        self.table.setColumnCount(n_cols)
        headers = [h for _, h in fixed]
        headers += [t["talla"] for t in tallas]
        headers += ["Estatus", "ID"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setColumnHidden(n_cols - 1, True)

        _ANCHOS = {"semana": 130, "cliente": 220, "folio_prog": 90,
                   "folio_pedido": 115, "modelo": 90, "piel": 110,
                   "color": 130, "fecha_prog": 100, "total": 60}
        for col, (key, _h) in enumerate(fixed):
            self.table.setColumnWidth(col, _ANCHOS.get(key, 80))
        for c in range(n_tallas):
            self.table.setColumnWidth(len(fixed) + c, 46)
        self.table.setColumnWidth(n_cols - 2, 110)

        self.table.setSortingEnabled(False)
        self.table.clearContents()
        self.table.clearSpans()

        factor = self.cmb_agrupar.currentData()
        if factor:
            grupos = self._agrupar_lineas(lineas, factor)
            n_rows = sum(1 + len(ms) for _k, ms in grupos)
            self.table.setRowCount(n_rows)
            r = 0
            for clave, ms in grupos:
                self._set_fila_grupo(r, factor, clave, ms)
                r += 1
                for l in ms:
                    self._set_fila(r, l)
                    r += 1
        else:
            self.table.setRowCount(len(lineas))
            for i, l in enumerate(lineas):
                self._set_fila(i, l)
            self.table.setSortingEnabled(True)

    def _agrupar_lineas(self, lineas: list[dict],
                        factor: str) -> list[tuple[str, list[dict]]]:
        grupos: dict[str, list[dict]] = {}
        orden: list[str] = []
        for l in lineas:
            clave = str(l.get(factor, "") or "").strip() or "(sin valor)"
            if clave not in grupos:
                grupos[clave] = []
                orden.append(clave)
            grupos[clave].append(l)
        return [(k, grupos[k]) for k in orden]

    def _set_fila_grupo(self, r: int, factor: str, clave: str,
                        ms: list[dict]) -> None:
        total = sum(int(m.get("total_pares", 0) or 0) for m in ms)
        label = f"{_FACTORES_AGRUPAR[factor].upper()}: {clave}  " \
                f"({len(ms)} líneas · {total} pares)"
        self.table.setSpan(r, 0, 1, self.table.columnCount())
        item = QTableWidgetItem(label)
        f = item.font()
        f.setBold(True)
        item.setFont(f)
        item.setBackground(QColor("#e0e7ff"))
        item.setForeground(QColor("#1e293b"))
        self.table.setItem(r, 0, item)

    def _set_fila(self, i: int, l: dict) -> None:
        base_vals = {
            "semana": l.get("semana", ""),
            "cliente": l.get("cliente", ""),
            "folio_prog": l.get("folio_prog", ""),
            "folio_pedido": l.get("folio_pedido", ""),
            "modelo": l.get("modelo", ""),
            "piel": l.get("piel", ""),
            "color": l.get("color", ""),
            "fecha_prog": l.get("fecha_prog", "") or "",
            "total": str(l.get("total_pares", 0)),
        }
        for col, (key, _h) in enumerate(self._fixed_cols):
            if key == "total":
                item = NumericItem(l.get("total_pares", 0))
                item.setTextAlignment(Qt.AlignCenter)
            else:
                item = QTableWidgetItem(base_vals.get(key, ""))
            self.table.setItem(i, col, item)

        por_talla = {t["talla"]: t["pares"] for t in l.get("tallas", [])}
        for col, t in self._talla_cols:
            val = por_talla.get(t["talla"], 0)
            item = NumericItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, col, item)

        est = l.get("estatus", "programado")
        item_est = QTableWidgetItem(_fmt_estatus(est))
        item_est.setForeground(_ESTATUS_COLOR.get(est, Qt.black))
        self.table.setItem(i, len(self._fixed_cols) + len(self._talla_cols), item_est)
        self.table.setItem(i, self.table.columnCount() - 1,
                           QTableWidgetItem(str(l.get("id", ""))))

    _FIXED_COLS = [
        ("cliente", "Cliente"),
        ("folio_prog", "Folio Prog."),
        ("folio_pedido", "Folio Pedido"),
        ("modelo", "Modelo"),
        ("piel", "Piel"),
        ("color", "Color"),
        ("fecha_prog", "Fecha Prog."),
        ("total", "Pares"),
    ]

    def _cambiar_estatus(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        item_id = self.table.item(row, self.table.columnCount() - 1)
        if item_id is None or not item_id.text():
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación (no una fila de grupo).")
            return
        linea_id = int(item_id.text())
        linea = self.controller.obtener_linea(linea_id)
        if not linea:
            return
        actual = linea.get("estatus", "programado")
        opciones = [_ESTATUS[v] for v in _ESTATUS]
        seleccion, ok = QInputDialog.getItem(
            self, "Cambiar Estatus",
            f"Línea {linea.get('folio_prog', '')} - {linea.get('cliente', '')} "
            f"({linea.get('modelo', '')})",
            opciones, 0, False)
        if not ok:
            return
        nuevo = [v for v, label in _ESTATUS.items() if label == seleccion][0]
        if nuevo == actual:
            return
        self.controller.cambiar_estatus(linea_id, nuevo)
        self._recargar_tabla()

    def _asignar_folio_pedido(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        item_id = self.table.item(row, self.table.columnCount() - 1)
        if item_id is None or not item_id.text():
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación (no una fila de grupo).")
            return
        linea_id = int(item_id.text())
        linea = self.controller.obtener_linea(linea_id)
        if not linea:
            return
        actual = linea.get("folio_pedido", "") or ""
        nuevo, ok = QInputDialog.getText(
            self, "Asignar Folio de Pedido",
            f"Folio de pedido para {linea.get('cliente', '')} / "
            f"{linea.get('modelo', '')} ({linea.get('folio_prog', '')}):",
            QLineEdit.Normal, actual)
        if not ok:
            return
        nuevo = nuevo.strip()
        if nuevo == actual:
            return
        self.controller.asignar_folio_pedido(linea_id, nuevo)
        self._recargar_tabla()

    def _exportar(self) -> None:
        path = export_table_to_excel(self.table, "Programacion", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir(self) -> None:
        semana = self.cmb_semana.currentText()
        print_table(self.table, f"Programacion - {semana}", self)

    def _imprimir_etiquetas(self) -> None:
        dlg = EtiquetasDialog(self.controller, self)
        dlg.exec()

    def _imprimir_etiqueta_prueba(self) -> None:
        dlg = EtiquetaPruebaDialog(self)
        dlg.exec()

    def _ver_detalle(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        item_id = self.table.item(row, self.table.columnCount() - 1)
        if item_id is None or not item_id.text():
            return
        linea_id = int(item_id.text())
        linea = self.controller.obtener_linea_con_tallas(linea_id)
        if not linea:
            return
        dlg = LineaDetalleDialog(linea, self)
        dlg.exec()
