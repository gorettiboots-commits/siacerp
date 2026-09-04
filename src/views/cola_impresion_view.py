"""Cola de impresión de etiquetas (escritorio).

Recibe las solicitudes que la app móvil envía a Supabase (`impresiones_etiqueta`
con estatus 'pendiente') y las muestra en una tabla para imprimir o ver en
pantalla. Al imprimir una solicitud:
- se marca como 'impresa' en Supabase (sale de la cola) y
- se guarda en el histórico local (`impresiones_historico`) para reimpresión.

Pestaña "Histórico": solicitudes ya impresas, con opción de reimprimir.
"""
import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.utils.etiqueta_render import render_label_pixmap
from src.utils.logs import get_usuario_actual
from src.views.etiquetas_dialog import _imprimir_copias, crear_diseno_fleje


def _resumen_payload(payload: dict) -> str:
    """Texto corto de la solicitud: partidas (o flejes) y total de etiquetas."""
    tipo = payload.get("tipo", "partidas")
    if tipo == "flejes":
        partidas = payload.get("partidas_fleje", [])
        total = sum(int(p.get("cantidad", 0) or 0) for p in partidas)
        detalle = ", ".join(
            f"{p.get('texto', '')} x{p.get('cantidad', 0)}"
            for p in partidas if p.get("texto"))
        return f"Flejes: {detalle}  ·  Total: {total}" if detalle else f"Flejes ({total})"
    partidas = payload.get("partidas", [])
    total = sum(int(p.get("cantidad", 0) or 0) for p in partidas)
    detalle = ", ".join(
        f"{p.get('modelo', '')}/{p.get('corte', '')}/{p.get('color', '')} "
        f"talla {p.get('talla', '')} x{p.get('cantidad', 0)}"
        for p in partidas if p.get("modelo"))
    return f"Partidas: {detalle}  ·  Total: {total}" if detalle else f"Partidas ({total})"


def _filas_impresion(payload: dict, diseno: dict) -> list[tuple[dict, dict, int]]:
    """Convierte el payload de una solicitud en filas (diseno, datos, copias)."""
    tipo = payload.get("tipo", "partidas")
    filas: list[tuple[dict, dict, int]] = []
    if tipo == "flejes":
        for p in payload.get("partidas_fleje", []):
            texto = str(p.get("texto", "")).strip()
            cantidad = int(p.get("cantidad", 0) or 0)
            if texto and cantidad > 0:
                filas.append((crear_diseno_fleje(diseno, texto), {}, cantidad))
    else:
        for p in payload.get("partidas", []):
            cantidad = int(p.get("cantidad", 0) or 0)
            if cantidad > 0:
                datos = {
                    "modelo": str(p.get("modelo", "")),
                    "corte": str(p.get("corte", "")),
                    "color": str(p.get("color", "")),
                    "talla": str(p.get("talla", "")),
                }
                filas.append((diseno, datos, cantidad))
    return filas


class DialogColaImpresion(QDialog):
    """Cola de impresión: solicitudes del móvil pendientes + histórico local."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self._controller = controller
        self._etiqueta_model = None  # import perezoso para evitar ciclos
        self.setWindowTitle("Cola de Impresión")
        self.setMinimumSize(860, 520)
        self.resize(980, 560)
        self._setup_ui()
        self._cargar_cola()
        self._cargar_historicos()

    # ------------------------------------------------------------- UI
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        encabezado = QLabel(
            "Solicitudes de impresión enviadas desde la app móvil. Al "
            "imprimir se salen de la cola y quedan en el histórico.")
        encabezado.setObjectName("sectionSubtitle")
        encabezado.setWordWrap(True)
        layout.addWidget(encabezado)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._tab_cola = self._crear_tab_cola()
        self._tab_hist = self._crear_tab_historico()
        self.tabs.addTab(self._tab_cola, "Cola (pendientes)")
        self.tabs.addTab(self._tab_hist, "Histórico")

        bar = QHBoxLayout()
        bar.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        bar.addWidget(btn_cerrar)
        layout.addLayout(bar)

    def _crear_tab_cola(self) -> QWidget:
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.tbl_cola = QTableWidget(0, 4)
        self.tbl_cola.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Solicitado", "Detalle"])
        self.tbl_cola.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_cola.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_cola.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_cola.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tbl_cola.verticalHeader().setVisible(False)
        self.tbl_cola.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_cola.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        lay.addWidget(self.tbl_cola, 1)

        bar = QHBoxLayout()
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setObjectName("btnSecondary")
        btn_actualizar.clicked.connect(self._cargar_cola)
        btn_preview = QPushButton("Vista previa")
        btn_preview.setObjectName("btnSecondary")
        btn_preview.clicked.connect(self._vista_previa_cola)
        btn_imprimir = QPushButton("Imprimir")
        btn_imprimir.setObjectName("btnPrimary")
        btn_imprimir.clicked.connect(self._imprimir_seleccion_cola)
        bar.addWidget(btn_actualizar)
        bar.addStretch()
        bar.addWidget(btn_preview)
        bar.addWidget(btn_imprimir)
        lay.addLayout(bar)
        return tab

    def _crear_tab_historico(self) -> QWidget:
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self.tbl_hist = QTableWidget(0, 5)
        self.tbl_hist.setHorizontalHeaderLabels(
            ["ID", "Tipo", "Impreso en", "Reimpresiones", "Detalle"])
        self.tbl_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_hist.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_hist.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tbl_hist.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tbl_hist.verticalHeader().setVisible(False)
        self.tbl_hist.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_hist.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        lay.addWidget(self.tbl_hist, 1)

        bar = QHBoxLayout()
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setObjectName("btnSecondary")
        btn_actualizar.clicked.connect(self._cargar_historicos)
        btn_preview = QPushButton("Vista previa")
        btn_preview.setObjectName("btnSecondary")
        btn_preview.clicked.connect(self._vista_previa_historico)
        btn_reimprimir = QPushButton("Reimprimir")
        btn_reimprimir.setObjectName("btnPrimary")
        btn_reimprimir.clicked.connect(self._reimprimir_seleccion)
        bar.addWidget(btn_actualizar)
        bar.addStretch()
        bar.addWidget(btn_preview)
        bar.addWidget(btn_reimprimir)
        lay.addLayout(bar)
        return tab

    # ------------------------------------------------------- Datos
    def _diseno_guardado(self) -> dict:
        from src.models.etiqueta_model import EtiquetaModel
        if self._etiqueta_model is None:
            self._etiqueta_model = EtiquetaModel()
        return self._etiqueta_model.cargar_diseno()

    def _cargar_cola(self) -> None:
        if not self._controller.configurado():
            self._cola_items = []
            self.tbl_cola.setRowCount(1)
            self.tbl_cola.setItem(
                0, 0, QTableWidgetItem("—"))
            self.tbl_cola.setItem(0, 1, QTableWidgetItem(""))
            self.tbl_cola.setItem(0, 2, QTableWidgetItem(""))
            self.tbl_cola.setItem(
                0, 3, QTableWidgetItem(
                    "Supabase no configurado: defina SUPABASE_URL y "
                    "SUPABASE_ANON_KEY (variables de entorno) o la sección "
                    "[supabase] de config.ini."))
            return
        try:
            cola = self._controller.listar_cola()
        except Exception as e:
            QMessageBox.warning(self, "Cola de impresión", str(e))
            cola = []
        self._cola_items = cola
        self.tbl_cola.setRowCount(len(cola))
        for i, item in enumerate(cola):
            payload = item.get("payload") or {}
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (ValueError, TypeError):
                    payload = {}
            tipo = str(payload.get("tipo", "partidas"))
            solicitado = str(item.get("creada_en") or payload.get("solicitado_en") or "")
            self.tbl_cola.setItem(i, 0, QTableWidgetItem(str(item.get("id", ""))))
            self.tbl_cola.setItem(i, 1, QTableWidgetItem("Flejes" if tipo == "flejes" else "Partidas"))
            self.tbl_cola.setItem(i, 2, QTableWidgetItem(solicitado))
            self.tbl_cola.setItem(i, 3, QTableWidgetItem(_resumen_payload(payload)))
        self.tbl_cola.resizeRowsToContents()

    def _cargar_historicos(self) -> None:
        try:
            historicos = self._controller.listar_historicos()
        except Exception as e:
            QMessageBox.warning(self, "Histórico", str(e))
            historicos = []
        self._hist_items = historicos
        self.tbl_hist.setRowCount(len(historicos))
        for i, item in enumerate(historicos):
            payload = item.get("payload") or {}
            tipo = str(payload.get("tipo", "partidas"))
            self.tbl_hist.setItem(i, 0, QTableWidgetItem(str(item.get("id", ""))))
            self.tbl_hist.setItem(i, 1, QTableWidgetItem("Flejes" if tipo == "flejes" else "Partidas"))
            self.tbl_hist.setItem(i, 2, QTableWidgetItem(str(item.get("impreso_en", ""))))
            self.tbl_hist.setItem(i, 3, QTableWidgetItem(str(item.get("reimpresiones", 0))))
            self.tbl_hist.setItem(i, 4, QTableWidgetItem(_resumen_payload(payload)))
        self.tbl_hist.resizeRowsToContents()

    def _solicitud_seleccionada_cola(self) -> dict | None:
        fila = self.tbl_cola.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Cola de impresión",
                                    "Seleccione una solicitud de la cola.")
            return None
        return self._cola_items[fila]

    def _solicitud_seleccionada_hist(self) -> dict | None:
        fila = self.tbl_hist.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Histórico",
                                    "Seleccione una solicitud del histórico.")
            return None
        return self._hist_items[fila]

    # ------------------------------------------------------- Acciones
    def _payload_de(self, solicitud: dict) -> dict:
        payload = solicitud.get("payload") or {}
        if isinstance(payload, str):
            try:
                return json.loads(payload)
            except (ValueError, TypeError):
                return {}
        return payload

    def _vista_previa_cola(self) -> None:
        solicitud = self._solicitud_seleccionada_cola()
        if solicitud is None:
            return
        self._mostrar_preview(solicitud)

    def _vista_previa_historico(self) -> None:
        solicitud = self._solicitud_seleccionada_hist()
        if solicitud is None:
            return
        self._mostrar_preview(solicitud)

    def _mostrar_preview(self, solicitud: dict) -> None:
        payload = self._payload_de(solicitud)
        filas = _filas_impresion(payload, self._diseno_guardado())
        if not filas:
            QMessageBox.information(self, "Vista previa",
                                    "La solicitud no tiene partidas con cantidad.")
            return
        # Muestra una imagen de la primera etiqueta de cada (diseno, datos).
        from PySide6.QtWidgets import QScrollArea, QWidget
        dlg = QDialog(self)
        dlg.setWindowTitle("Vista previa de etiquetas")
        dlg.setMinimumSize(640, 520)
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        vistos: set[Any] = set()
        for diseno, datos, _copias in filas:
            clave = (json.dumps(diseno, sort_keys=True),
                     json.dumps(datos, sort_keys=True))
            if clave in vistos:
                continue
            vistos.add(clave)
            pixmap = render_label_pixmap(diseno, datos, escala=1.0)
            lbl = QLabel()
            lbl.setPixmap(pixmap.scaled(
                380, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl.setAlignment(Qt.AlignCenter)
            txt = QLabel(
                " · ".join(f"{k}: {v}" for k, v in datos.items()) or
                json.dumps(diseno.get("campos", [{}])[0].get("texto", "")))
            txt.setAlignment(Qt.AlignCenter)
            txt.setStyleSheet("color: #475569; font-size: 12px;")
            lay.addWidget(lbl)
            lay.addWidget(txt)
        scroll = QScrollArea()
        scroll.setWidget(cont)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(dlg)
        outer.addWidget(scroll)
        btn = QPushButton("Cerrar")
        btn.setObjectName("btnPrimary")
        btn.clicked.connect(dlg.accept)
        outer.addWidget(btn, 0, Qt.AlignCenter)
        dlg.exec()

    def _imprimir_seleccion_cola(self) -> None:
        solicitud = self._solicitud_seleccionada_cola()
        if solicitud is None:
            return
        payload = self._payload_de(solicitud)
        filas = _filas_impresion(payload, self._diseno_guardado())
        if not filas:
            QMessageBox.information(self, "Imprimir",
                                    "La solicitud no tiene partidas con cantidad.")
            return
        _imprimir_copias(self, filas)
        # La solicitud ya salió de la cola en Supabase y queda en el histórico.
        usuario = (get_usuario_actual() or {}).get("username")
        try:
            self._controller.guardar_historico(
                solicitud.get("id"), payload.get("tipo", "partidas"), payload,
                str(solicitud.get("creada_en") or payload.get("solicitado_en") or ""),
                usuario)
            self._controller.marcar_impresa(solicitud.get("id"))
        except Exception as e:
            QMessageBox.warning(self, "Cola de impresión",
                                f"Se imprimió, pero no se pudo actualizar la cola: {e}")
        self._cargar_cola()
        self._cargar_historicos()

    def _reimprimir_seleccion(self) -> None:
        solicitud = self._solicitud_seleccionada_hist()
        if solicitud is None:
            return
        payload = self._payload_de(solicitud)
        filas = _filas_impresion(payload, self._diseno_guardado())
        if not filas:
            QMessageBox.information(self, "Reimprimir",
                                    "La solicitud no tiene partidas con cantidad.")
            return
        _imprimir_copias(self, filas)
        try:
            self._controller.registrar_reimpresion(int(solicitud.get("id", 0)))
        except Exception:
            pass
        self._cargar_historicos()
