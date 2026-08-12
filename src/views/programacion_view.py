from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.export_utils import export_table_to_excel
from src.utils.programacion_print import abrir_programacion_html
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

_PRODUCCION_INICIADA = ("en_proceso", "producido")


def _fmt_estatus(estatus: str) -> str:
    return _ESTATUS.get(estatus, estatus.replace("_", " ").capitalize())


class ProgramacionView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ProgramacionController()
        self._factor_actual: str | None = None
        self._lineas_actuales: list[dict] = []
        self._col_estatus = 0
        self._permiso_eliminar = True
        self._setup_ui()
        self._cargar_semanas()

    def set_permisos(self, permisos) -> None:
        self._permiso_eliminar = tiene(permisos, "programacion", "eliminar")
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

        self.vista = ComplexGrid()
        self.vista.set_buscador_visible(False)
        self.vista.set_exportar_visible(False)
        self.vista.set_agrupar_visible(False)
        self.vista.set_renderers(fila=self._fila_linea, claves=self._claves_linea,
                                 estilo=self._estilo_linea, lista=self._lista_linea,
                                 tarjeta=self._tarjeta_linea)
        self.vista.set_acciones([
            {"texto": "Eliminar", "icono": "eliminar", "color": "#dc2626",
             "habilitado": lambda rec: self._permiso_eliminar and rec.get(
                 "estatus", "programado") not in _PRODUCCION_INICIADA,
             "callback": self._eliminar_linea},
        ])
        self.vista.set_grupo_fn(self._grupo_label)
        self.vista.doubleClicked.connect(self._ver_detalle)
        layout.addWidget(self.vista)

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
        lineas = self.controller.lineas_con_tallas(
            semana_id, termino, estatus, folio_pedido)

        self._factor_actual = self.cmb_agrupar.currentData()

        cols = []
        if es_todas:
            cols.append({"key": "semana", "titulo": "Semana", "ancho": 130})
        for key, titulo in self._FIXED_COLS:
            cols.append({"key": key, "titulo": titulo,
                         "ancho": self._ANCHOS.get(key, 80)})
        cols.append({"key": "corrida", "titulo": "Corrida", "ancho": 150})
        cols.append({"key": "estatus", "titulo": "Estatus", "ancho": 110})
        self._col_estatus = len(cols) - 1

        self.vista.set_columnas(cols)
        self.vista.set_datos(lineas)
        self.vista.set_agrupacion(self._factor_actual)
        self._lineas_actuales = lineas

    def _grupo_label(self, valor, recs: list[dict]) -> str:
        total = sum(int(r.get("total_pares", 0) or 0) for r in recs)
        factor = _FACTORES_AGRUPAR.get(self._factor_actual, "Cliente")
        texto = str(valor or "").strip() or "(sin valor)"
        return f"{factor.upper()}: {texto}  ({len(recs)} líneas · {total} pares)"

    @staticmethod
    def _fmt_talla(talla) -> str:
        try:
            v = float(talla)
            return str(int(v)) if v == int(v) else str(v)
        except (TypeError, ValueError):
            return str(talla)

    @staticmethod
    def _valor_talla(talla):
        try:
            return (0, float(talla))
        except (TypeError, ValueError):
            return (1, str(talla))

    def _texto_corrida(self, l: dict) -> str:
        tallas = [t for t in l.get("tallas", []) if t.get("talla") is not None]
        if not tallas:
            return ""
        parejas = sorted(
            (self._valor_talla(t["talla"]), self._fmt_talla(t["talla"]))
            for t in tallas)
        return f"del {parejas[0][1]} al {parejas[-1][1]}"

    def _fila_linea(self, l: dict) -> list[str]:
        fila = []
        es_todas = self.cmb_semana.currentData() is None
        if es_todas:
            fila.append(l.get("semana", ""))
        base = {
            "cliente": l.get("cliente", ""),
            "folio_prog": l.get("folio_prog", ""),
            "folio_pedido": l.get("folio_pedido", ""),
            "modelo": l.get("modelo", ""),
            "piel": l.get("piel", ""),
            "color": l.get("color", ""),
            "fecha_prog": l.get("fecha_prog", "") or "",
            "total": str(l.get("total_pares", 0)),
        }
        fila += [base.get(key, "") for key, _ in self._FIXED_COLS]
        fila.append(self._texto_corrida(l))
        fila.append(_fmt_estatus(l.get("estatus", "programado")))
        return fila

    def _claves_linea(self, l: dict) -> list:
        claves = []
        es_todas = self.cmb_semana.currentData() is None
        if es_todas:
            claves.append(l.get("semana", ""))
        base = {
            "cliente": (l.get("cliente", "") or "").lower(),
            "folio_prog": l.get("folio_prog", ""),
            "folio_pedido": l.get("folio_pedido", ""),
            "modelo": l.get("modelo", ""),
            "piel": l.get("piel", ""),
            "color": l.get("color", ""),
            "fecha_prog": l.get("fecha_prog", "") or "",
            "total": float(l.get("total_pares", 0) or 0),
        }
        claves += [base.get(key, "") for key, _ in self._FIXED_COLS]
        tallas = [t for t in l.get("tallas", []) if t.get("talla") is not None]
        if tallas:
            clave_corrida = min(self._valor_talla(t["talla"]) for t in tallas)
        else:
            clave_corrida = (1, "")
        claves.append(clave_corrida)
        claves.append(l.get("estatus", "programado"))
        return claves

    def _estilo_linea(self, l: dict, item, col: int) -> None:
        if col != self._col_estatus:
            return
        item.setForeground(_ESTATUS_COLOR.get(l.get("estatus", "programado"), Qt.black))

    @staticmethod
    def _lista_linea(l: dict) -> tuple[str, str]:
        return (f"{l.get('folio_prog', '')} · {l.get('cliente', '')}",
                f"{l.get('modelo', '')} / {l.get('piel', '')} / {l.get('color', '')} "
                f"· {l.get('total_pares', 0)} pares")

    @staticmethod
    def _tarjeta_linea(l: dict) -> dict:
        return {
            "icono": "oc",
            "titulo": l.get("folio_prog", ""),
            "subtitulo": f"{l.get('cliente', '')} / {l.get('modelo', '')}",
            "badge": _fmt_estatus(l.get("estatus", "programado")),
            "color": "#4f46e5",
        }

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

    _ANCHOS = {"semana": 130, "cliente": 220, "folio_prog": 90,
               "folio_pedido": 115, "modelo": 90, "piel": 110,
               "color": 130, "fecha_prog": 100, "total": 60}

    def _cambiar_estatus(self) -> None:
        rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        linea_id = rec["id"]
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
        rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        linea_id = rec["id"]
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

    def _eliminar_linea(self, rec=None) -> None:
        if rec is None:
            rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        linea = self.controller.obtener_linea(rec["id"])
        if not linea:
            return
        if linea.get("estatus", "programado") in _PRODUCCION_INICIADA:
            QMessageBox.warning(
                self, "No se puede eliminar",
                "Esta línea ya inició un proceso de producción y no se puede "
                "eliminar.")
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar la línea {linea.get('folio_prog', '')} — "
            f"{linea.get('cliente', '')} / {linea.get('modelo', '')}?",
            QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        self.controller.eliminar_linea(linea["id"])
        self._on_semana_cambiada()

    def _exportar(self) -> None:
        path = export_table_to_excel(self.vista.table, "Programacion", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir(self) -> None:
        es_todas = self.cmb_semana.currentData() is None
        titulo = f"PROGRAMACIÓN SEMANAL — {self.cmb_semana.currentText()}"
        abrir_programacion_html(self._lineas_actuales, titulo=titulo,
                                incluir_semana=es_todas)

    def _imprimir_etiquetas(self) -> None:
        dlg = EtiquetasDialog(self.controller, self)
        dlg.exec()

    def _imprimir_etiqueta_prueba(self) -> None:
        dlg = EtiquetaPruebaDialog(self)
        dlg.exec()

    def _ver_detalle(self) -> None:
        rec = self.vista.registro_seleccionado()
        if rec is None:
            return
        linea = self.controller.obtener_linea_con_tallas(rec["id"])
        if not linea:
            return
        dlg = LineaDetalleDialog(linea, self)
        dlg.exec()
