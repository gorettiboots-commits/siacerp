from PySide6.QtCore import QByteArray, QMimeData, Qt
from PySide6.QtGui import QColor, QDrag
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout,
    QWidget,
)

from src.controllers.produccion_controller import ProduccionController

COLORS = [
    ("#6366f1", "#eef2ff"),  # indigo
    ("#f59e0b", "#fffbeb"),  # amber
    ("#ef4444", "#fef2f2"),  # red
    ("#10b981", "#ecfdf5"),  # emerald
    ("#3b82f6", "#eff6ff"),  # blue
    ("#8b5cf6", "#f5f3ff"),  # violet
    ("#14b8a6", "#f0fdfa"),  # teal
    ("#f97316", "#fff7ed"),  # orange
    ("#ec4899", "#fdf2f8"),  # pink
    ("#84cc16", "#f7fee7"),  # lime
]


class _KanbanCard(QFrame):
    def __init__(self, op: dict, accent: str, accent_bg: str, parent=None) -> None:
        super().__init__(parent)
        self.op_id = op["id"]
        self.setObjectName("kanbanCard")
        self.setCursor(Qt.OpenHandCursor)
        self.setStyleSheet(f"""
            QFrame#kanbanCard {{
                background-color: #ffffff; border: 1px solid #e2e8f0;
                border-left: 4px solid {accent}; border-radius: 8px;
            }}
            QFrame#kanbanCard:hover {{ border: 1px solid {accent}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        folio = QLabel(op.get("folio", ""))
        folio.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
        layout.addWidget(folio)

        modelo = QLabel(f"{op.get('modelo_nombre', '')} · {op.get('codigo_variante', '')}")
        modelo.setStyleSheet("font-size: 11px; color: #475569;")
        modelo.setWordWrap(True)
        layout.addWidget(modelo)

        det = QLabel(f"{op.get('color', '')}/{op.get('piel', '')}  ·  {op.get('total_pares', 0)} pares")
        det.setStyleSheet("font-size: 11px; color: #64748b;")
        layout.addWidget(det)

        if op.get("fecha_entrega"):
            fe = QLabel(f"Entrega: {op.get('fecha_entrega')}")
            fe.setStyleSheet("font-size: 10px; color: #94a3b8;")
            layout.addWidget(fe)

        prioridad = op.get("prioridad", "normal")
        badge = QLabel(prioridad.capitalize())
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(64)
        badge.setStyleSheet(self._prioridad_style(prioridad))
        layout.addWidget(badge)

    @staticmethod
    def _prioridad_style(prioridad: str) -> str:
        colors = {
            "baja": ("#64748b", "#f1f5f9"),
            "normal": ("#3b82f6", "#eff6ff"),
            "alta": ("#f59e0b", "#fffbeb"),
            "urgente": ("#ef4444", "#fef2f2"),
        }
        fg, bg = colors.get(prioridad, colors["normal"])
        return f"color: {fg}; background-color: {bg}; border-radius: 8px; font-size: 10px; padding: 2px;"

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setData("application/x-siacerp-op", QByteArray(str(self.op_id).encode()))
            drag.setMimeData(mime)
            self.setCursor(Qt.ClosedHandCursor)
            drag.exec_(Qt.MoveAction)
            self.setCursor(Qt.OpenHandCursor)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        parent = self.parentWidget()
        if parent and hasattr(parent, "open_seguimiento"):
            parent.open_seguimiento(self.op_id)
        super().mouseDoubleClickEvent(event)


class _KanbanColumn(QFrame):
    def __init__(self, title: str, estacion_id, accent: str, accent_bg: str,
                 view: "KanbanView") -> None:
        super().__init__()
        self.view = view
        self.estacion_id = estacion_id
        self.setObjectName("kanbanColumn")
        self.setAcceptDrops(True)
        self.setFixedWidth(240)
        self.setStyleSheet(f"""
            QFrame#kanbanColumn {{
                background-color: {accent_bg}; border: 1px solid #e2e8f0;
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QHBoxLayout()
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {accent}; border-radius: 5px;")
        self.lbl_count = QLabel("0")
        self.lbl_count.setStyleSheet(
            f"background-color: {accent}; color: #ffffff; border-radius: 9px;"
            "font-size: 11px; font-weight: bold; padding: 2px 7px;")
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #334155;")
        header.addWidget(dot)
        header.addWidget(title_label, 1)
        header.addWidget(self.lbl_count)
        layout.addLayout(header)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(self.cards_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        layout.addWidget(scroll, 1)

    def add_card(self, op: dict, accent: str, accent_bg: str) -> None:
        card = _KanbanCard(op, accent, accent_bg)
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self.lbl_count.setText(str(self.cards_layout.count() - 1))

    def clear(self) -> None:
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.lbl_count.setText("0")

    def open_seguimiento(self, op_id: int) -> None:
        self.view.open_seguimiento(op_id)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-siacerp-op"):
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-siacerp-op"):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        raw = event.mimeData().data("application/x-siacerp-op").data().decode()
        op_id = int(raw)
        self.view.on_card_dropped(op_id, self.estacion_id)
        event.acceptProposedAction()


class KanbanView(QWidget):
    def __init__(self, controller: ProduccionController, on_change=None) -> None:
        super().__init__()
        self.controller = controller
        self.on_change = on_change
        self.columns: list[_KanbanColumn] = []
        self._columns_by_key: dict = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        hint = QLabel(
            "Arrastra una orden a la siguiente área para avanzarla. "
            "Doble clic para ver seguimiento."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.setObjectName("btnPrimary")
        self.btn_refresh.clicked.connect(self.recargar)
        toolbar.addWidget(hint)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #4f46e5; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        self._container = QWidget()
        self._columns_layout = QHBoxLayout(self._container)
        self._columns_layout.setContentsMargins(0, 0, 0, 0)
        self._columns_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._container)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll, 1)

        self._build_columns()

    def _build_columns(self) -> None:
        for col in self.columns:
            self._columns_layout.removeWidget(col)
            col.deleteLater()
        self.columns = []
        self._columns_by_key = {}

        estaciones = self.controller.listar_estaciones()

        def nueva_columna(key, titulo, color_idx) -> _KanbanColumn:
            accent, accent_bg = COLORS[color_idx % len(COLORS)]
            col = _KanbanColumn(titulo, key, accent, accent_bg, self)
            self.columns.append(col)
            self._columns_by_key[key] = col
            self._columns_layout.addWidget(col)
            return col

        nueva_columna("planeada", "Planeadas", 0)
        for i, est in enumerate(estaciones):
            nueva_columna(est["id"], est["nombre"], i + 1)
        nueva_columna("terminada", "Terminadas", 8)
        self._columns_layout.addStretch()

    def recargar(self) -> None:
        try:
            ops = self.controller.listar_ops()
        except Exception as e:
            self.lbl_status.setText(f"Error al cargar: {e}")
            return
        for col in self.columns:
            col.clear()
        for op in ops:
            try:
                pos = self.controller.posicion_op(op["id"])
            except Exception:
                pos = {"columna": "planeada"}
            col = self._columns_by_key.get(pos.get("columna"))
            if col is None:
                col = self._columns_by_key.get("planeada")
            idx = self.columns.index(col)
            accent, accent_bg = COLORS[idx % len(COLORS)]
            col.add_card(op, accent, accent_bg)
        self.lbl_status.setText("")

    def on_card_dropped(self, op_id: int, target_key) -> None:
        ok = self.controller.mover_en_kanban(op_id, target_key)
        if ok:
            self.lbl_status.setText("Orden avanzada correctamente.")
            self.recargar()
            if self.on_change:
                self.on_change()
        else:
            self.lbl_status.setText("Solo se puede arrastrar hacia la siguiente área.")

    def open_seguimiento(self, op_id: int) -> None:
        from src.views.dialogs import DialogSeguimientoOP
        dlg = DialogSeguimientoOP(self.controller, op_id)
        dlg.exec()
        self.recargar()
        if self.on_change:
            self.on_change()
