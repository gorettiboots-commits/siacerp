from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.components.grid_hibrido import GridHibrido
from src.components.notificacion_flotante import notificar_flotante
from src.components.preview_impresion import PreviewImpresion
from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.export_utils import exportar_programacion_excel
from src.utils.programacion_print import generar_html_programacion
from src.utils.ui_helpers import crear_tarjeta
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
        self.vista.establecer_boton_modulo(
            "asignar_folio",
            tiene(permisos, "programacion", "editar"))
        self.vista.set_exportar_visible(
            tiene(permisos, "programacion", "exportar"))

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

        hlayout.addLayout(title_col)
        hlayout.addStretch()

        self._cards_row = QHBoxLayout()
        hlayout.addLayout(self._cards_row)

        layout.addWidget(header)

        self._crear_widgets_toolbar()

        self.vista = GridHibrido()
        self.vista.set_imprimir_callback(self._imprimir)
        self.vista.agregar_widget_toolbar(QLabel("Semana:"))
        self.vista.agregar_widget_toolbar(self.cmb_semana)
        self.vista.agregar_separador_toolbar()
        self.vista.agregar_boton_toolbar(
            "actualizar", "Actualizar", "buscar", "#1892D4",
            self._cargar_semanas)
        self.vista.agregar_boton_toolbar(
            "asignar_folio", "Asignar Folio Programación", "editar", "#1892D4",
            self._asignar_folio_prog)
        self.vista.set_widget_izquierda(self._agrupar_widget)
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
        header = self.vista.table.horizontalHeader()
        header.setStyleSheet(
            "QHeaderView::section { background-color:#4f46e5; color:#ffffff; "
            "border:none; border-right:1px solid #a0a0a0; "
            "border-bottom:1px solid #a0a0a0; font-weight:bold; padding:5px 6px; }")
        layout.addWidget(self.vista)

    def _crear_widgets_toolbar(self) -> None:
        self.cmb_semana = QComboBox()
        self.cmb_semana.setMinimumWidth(220)
        self.cmb_semana.currentIndexChanged.connect(self._on_semana_cambiada)

        self.cmb_agrupar = QComboBox()
        self.cmb_agrupar.addItem("Sin agrupar", None)
        for valor, label in _FACTORES_AGRUPAR.items():
            self.cmb_agrupar.addItem(f"Agrupar por {label}", valor)
        self.cmb_agrupar.currentIndexChanged.connect(self._recargar_tabla)

        self._agrupar_widget = QWidget()
        agrupar_layout = QHBoxLayout(self._agrupar_widget)
        agrupar_layout.setContentsMargins(0, 0, 0, 0)
        agrupar_layout.setSpacing(6)
        agrupar_layout.addWidget(QLabel("Agrupar:"))
        agrupar_layout.addWidget(self.cmb_agrupar)

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

    def _on_semana_cambiada(self) -> None:
        self._cargar_cards(self.controller.listar_semanas())
        self._recargar_tabla()

    def _recargar_tabla(self) -> None:
        semana_id = self.cmb_semana.currentData()
        es_todas = semana_id is None
        lineas = self.controller.lineas_con_tallas(semana_id)

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

    def _asignar_folio_prog(self) -> None:
        rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar",
                                    "Seleccione una línea de la programación.")
            return
        linea_id = rec["id"]
        linea = self.controller.obtener_linea(linea_id)
        if not linea:
            return
        actual = linea.get("folio_prog", "") or ""
        nuevo, ok = QInputDialog.getText(
            self, "Asignar Folio de Programación",
            f"Folio de programación para {linea.get('cliente', '')} / "
            f"{linea.get('modelo', '')}:",
            QLineEdit.Normal, actual)
        if not ok:
            return
        nuevo = nuevo.strip()
        if nuevo == actual:
            return
        self.controller.asignar_folio_prog(linea_id, nuevo)
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
        es_todas = self.cmb_semana.currentData() is None
        titulo = f"PROGRAMACIÓN SEMANAL — {self.cmb_semana.currentText()}"
        grupos = None
        if self._factor_actual:
            agrupadas: dict = {}
            for l in self._lineas_actuales:
                valor = self._valor_agrupar(l, self._factor_actual)
                agrupadas.setdefault(valor, []).append(l)
            orden = sorted(agrupadas.keys(), key=lambda v: str(v).lower())
            grupos = [(self._grupo_label(v, agrupadas[v]), agrupadas[v])
                      for v in orden]
        path = exportar_programacion_excel(
            self._lineas_actuales, titulo=titulo, incluir_semana=es_todas,
            parent=self, grupos=grupos)
        if path:
            notificar_flotante(f"Excel guardado en:\n{path}",
                               tipo="success", titulo="Exportado", host=self)

    @staticmethod
    def _valor_agrupar(l: dict, key: str):
        return l.get(key, "")

    def _imprimir(self) -> None:
        """Vista previa de impresión del reporte (PreviewImpresion)."""
        es_todas = self.cmb_semana.currentData() is None
        titulo = f"PROGRAMACIÓN SEMANAL — {self.cmb_semana.currentText()}"
        html = generar_html_programacion(
            self._lineas_actuales, titulo=titulo,
            incluir_semana=es_todas, auto_imprimir=False)
        dlg = PreviewImpresion(html, titulo=titulo, parent=self)
        dlg.cmb_orientacion.setCurrentText("Horizontal")
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
