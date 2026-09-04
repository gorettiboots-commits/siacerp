"""Diagrama Gantt de produccion.

Filas = Ordenes de Produccion
Columnas = Dias del mes
Colores = Estacion de produccion (historico)

Cada barra muestra el recorrido de una OP por las estaciones,
manteniendo el color de cada etapa en el historial.
"""
from datetime import date, datetime, timedelta

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSpinBox, QVBoxLayout, QWidget,
)

from src.controllers.produccion_controller import ProduccionController

# Colores por estacion (index = orden de la estacion)
COLOR_ESTACION = [
    "#6366f1",  # Corte — indigo
    "#f59e0b",  # Pespunte — amber
    "#ef4444",  # Montado — red
    "#10b981",  # Ensuelado — emerald
    "#3b82f6",  # Acabado — blue
    "#8b5cf6",  # Empaque — violet
    "#14b8a6",  # extra 1 — teal
    "#f97316",  # extra 2 — orange
]

COLOR_PLANEADA = "#94a3b8"   # gris
COLOR_TERMINADA = "#22c55e"  # verde

# Dimensiones
ROW_HEIGHT = 36
DAY_WIDTH = 38
LABEL_WIDTH = 260
HEADER_HEIGHT = 40


class GanttCanvas(QWidget):
    """Widget interno que dibuja el diagrama Gantt."""

    op_doble_clic = Signal(int)  # emite op_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.ops: list[dict] = []
        self.barras: dict[int, list[dict]] = {}  # op_id -> [{estacion, inicio, fin, color}]
        self.fecha_inicio: date = date.today().replace(day=1)
        self.dias_mes: int = 31
        self._mapa_estaciones: dict[int, tuple[str, int, str]] = {}
        self.setMouseTracking(True)
        self._tooltip_op: dict | None = None
        self._tooltip_rect: QRect | None = None

    def _dia_col(self, d: date) -> int:
        delta = (d - self.fecha_inicio).days
        return delta

    def calcular_tamano(self) -> None:
        ancho = LABEL_WIDTH + self.dias_mes * DAY_WIDTH + 20
        alto = HEADER_HEIGHT + len(self.ops) * ROW_HEIGHT + 20
        self.setMinimumSize(ancho, alto)
        self.setMaximumHeight(alto)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Fondo
        painter.fillRect(0, 0, w, h, QColor("#ffffff"))

        if not self.ops:
            painter.setPen(QPen(QColor("#94a3b8")))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Sin ordenes de produccion para mostrar")
            return

        # ── Encabezado de dias ──
        painter.setPen(QPen(QColor("#e2e8f0")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))

        for dia in range(1, self.dias_mes + 1):
            x = LABEL_WIDTH + (dia - 1) * DAY_WIDTH
            d = self.fecha_inicio.replace(day=dia)

            # Fondo del encabezado
            es_hoy = (d == date.today())
            es_finde = d.weekday() >= 5
            if es_hoy:
                painter.fillRect(x, 0, DAY_WIDTH, HEADER_HEIGHT, QColor("#eff6ff"))
            elif es_finde:
                painter.fillRect(x, 0, DAY_WIDTH, HEADER_HEIGHT, QColor("#f8fafc"))

            # Linea vertical del dia
            painter.setPen(QPen(QColor("#e2e8f0")))
            painter.drawLine(x, HEADER_HEIGHT, x, h)

            # Texto del dia
            if es_hoy:
                painter.setPen(QPen(QColor("#1e40af")))
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            else:
                painter.setPen(QPen(QColor("#475569")))
                painter.setFont(QFont("Segoe UI", 9))

            # Nombre del dia abreviado
            nombres = ["L", "M", "X", "J", "V", "S", "D"]
            nombre_dia = nombres[d.weekday()]
            painter.drawText(x, 2, DAY_WIDTH, HEADER_HEIGHT // 2, Qt.AlignCenter, nombre_dia)
            painter.drawText(x, HEADER_HEIGHT // 2, DAY_WIDTH, HEADER_HEIGHT // 2, Qt.AlignCenter, str(dia))

        # Linea inferior del encabezado
        painter.setPen(QPen(QColor("#cbd5e1"), 2))
        painter.drawLine(0, HEADER_HEIGHT, w, HEADER_HEIGHT)

        # ── Filas de OPs ──
        painter.setFont(QFont("Segoe UI", 9))
        hoy = date.today()

        for i, op in enumerate(self.ops):
            y = HEADER_HEIGHT + i * ROW_HEIGHT
            op_id = op["id"]

            # Fondo alternado
            if i % 2 == 1:
                painter.fillRect(0, y, w, ROW_HEIGHT, QColor("#f8fafc"))

            # Fondo de fila si es hoy la fecha de inicio
            try:
                fi = datetime.strptime(op.get("fecha_inicio", ""), "%Y-%m-%d").date() if op.get("fecha_inicio") else None
            except (TypeError, ValueError):
                fi = None
            if fi and fi == hoy:
                painter.fillRect(0, y, w, ROW_HEIGHT, QColor("#eff6ff"))

            # Separador horizontal
            painter.setPen(QPen(QColor("#f1f5f9")))
            painter.drawLine(0, y + ROW_HEIGHT, w, y + ROW_HEIGHT)

            # ── Label de la OP ──
            painter.setPen(QPen(QColor("#1e293b")))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(8, y, LABEL_WIDTH - 8, ROW_HEIGHT, Qt.AlignVCenter, op.get("folio", ""))

            painter.setPen(QPen(QColor("#64748b")))
            painter.setFont(QFont("Segoe UI", 8))
            modelo = op.get("modelo_nombre", "")
            variante = op.get("codigo_variante", "")
            texto_det = f"{modelo} · {variante}"
            painter.drawText(8, y + ROW_HEIGHT // 2, LABEL_WIDTH - 8, ROW_HEIGHT // 2, Qt.AlignVCenter, texto_det)

            # ── Barras del Gantt ──
            barras = self.barras.get(op_id, [])
            if barras:
                bar_y = y + 6
                bar_h = ROW_HEIGHT - 12

                for b in barras:
                    col_ini = self._dia_col(b["inicio"])
                    col_fin = self._dia_col(b["fin"])
                    if col_fin < 0 or col_ini >= self.dias_mes:
                        continue
                    col_ini = max(0, col_ini)
                    col_fin = min(self.dias_mes - 1, col_fin)

                    bx = LABEL_WIDTH + col_ini * DAY_WIDTH
                    bw = (col_fin - col_ini + 1) * DAY_WIDTH
                    if bw < DAY_WIDTH:
                        bw = DAY_WIDTH

                    color = QColor(b["color"])
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(color.darker(120), 1))
                    painter.drawRoundedRect(bx + 1, bar_y, bw - 2, bar_h, 4, 4)

                    # Texto dentro de la barra
                    if bw > 60:
                        painter.setPen(QPen(QColor("#ffffff")))
                        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                        painter.drawText(bx + 1, bar_y, bw - 2, bar_h, Qt.AlignCenter, b["estacion"])
            else:
                # OP planeada sin seguimiento
                painter.setPen(QPen(QColor("#94a3b8")))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(
                    LABEL_WIDTH, y, self.dias_mes * DAY_WIDTH, ROW_HEIGHT,
                    Qt.AlignCenter, "Sin seguimiento")

        painter.end()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position() if hasattr(event, 'position') else event.pos()
        mx, my = int(pos.x()), int(pos.y())
        if my < HEADER_HEIGHT:
            self._tooltip_op = None
            self._tooltip_rect = None
            self.setToolTip("")
            return

        fila = (my - HEADER_HEIGHT) // ROW_HEIGHT
        if fila < 0 or fila >= len(self.ops):
            self._tooltip_op = None
            self._tooltip_rect = None
            self.setToolTip("")
            return

        op = self.ops[fila]
        barras = self.barras.get(op["id"], [])

        # Verificar si el mouse esta sobre una barra
        for b in barras:
            col_ini = self._dia_col(b["inicio"])
            col_fin = self._dia_col(b["fin"])
            col_ini = max(0, col_ini)
            col_fin = min(self.dias_mes - 1, col_fin)
            bx = LABEL_WIDTH + col_ini * DAY_WIDTH
            bw = (col_fin - col_ini + 1) * DAY_WIDTH
            bar_y = HEADER_HEIGHT + fila * ROW_HEIGHT + 6
            bar_h = ROW_HEIGHT - 12

            if bx <= mx <= bx + bw and bar_y <= my <= bar_y + bar_h:
                texto = (
                    f"{op.get('folio', '')} — {op.get('modelo_nombre', '')}\n"
                    f"Estacion: {b['estacion']}\n"
                    f"Desde: {b['inicio'].strftime('%d/%m/%Y')}\n"
                    f"Hasta: {b['fin'].strftime('%d/%m/%Y')}"
                )
                self.setToolTip(texto)
                self._tooltip_op = op
                return

        self.setToolTip(f"{op.get('folio', '')} — {op.get('modelo_nombre', '')} · {op.get('codigo_variante', '')}")
        self._tooltip_op = op

    def mouseDoubleClickEvent(self, event) -> None:
        pos = event.position() if hasattr(event, 'position') else event.pos()
        my = int(pos.y())
        if my < HEADER_HEIGHT:
            return
        fila = (my - HEADER_HEIGHT) // ROW_HEIGHT
        if 0 <= fila < len(self.ops):
            self.op_doble_clic.emit(self.ops[fila]["id"])


class GanttView(QWidget):
    """Vista principal del diagrama Gantt de produccion."""

    def __init__(self, controller: ProduccionController, on_change=None) -> None:
        super().__init__()
        self.controller = controller
        self.on_change = on_change
        self._mes_actual = date.today().month
        self._anio_actual = date.today().year
        self._setup_ui()
        self.recargar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        hint = QLabel("Diagrama Gantt — Doble clic para ver seguimiento de la OP.")
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        toolbar.addWidget(hint)
        toolbar.addStretch()

        # Navegacion de mes
        btn_prev = QPushButton("\u25C0")
        btn_prev.setFixedSize(28, 28)
        btn_prev.setStyleSheet(
            "QPushButton { border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background: #f1f5f9; }")
        btn_prev.clicked.connect(self._mes_anterior)
        toolbar.addWidget(btn_prev)

        self.lbl_mes = QLabel()
        self.lbl_mes.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b; min-width: 140px;")
        self.lbl_mes.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self.lbl_mes)

        btn_next = QPushButton("\u25B6")
        btn_next.setFixedSize(28, 28)
        btn_next.setStyleSheet(
            "QPushButton { border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background: #f1f5f9; }")
        btn_next.clicked.connect(self._mes_siguiente)
        toolbar.addWidget(btn_next)

        btn_hoy = QPushButton("Hoy")
        btn_hoy.setStyleSheet(
            "QPushButton { border: 1px solid #3b82f6; color: #3b82f6; border-radius: 4px; "
            "padding: 2px 10px; font-size: 11px; }"
            "QPushButton:hover { background: #eff6ff; }")
        btn_hoy.clicked.connect(self._ir_hoy)
        toolbar.addWidget(btn_hoy)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self.recargar)
        toolbar.addWidget(btn_refresh)

        layout.addLayout(toolbar)

        # Leyenda de colores
        self.legend_frame = QFrame()
        self.legend_frame.setStyleSheet(
            "QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; }")
        legend_layout = QHBoxLayout(self.legend_frame)
        legend_layout.setContentsMargins(10, 4, 10, 4)
        legend_layout.setSpacing(14)
        legend_layout.addWidget(QLabel("Leyenda:"))
        self._legend_labels = []
        legend_layout.addStretch()
        layout.addWidget(self.legend_frame)

        # Canvas con scroll
        self.canvas = GanttCanvas()
        self.canvas.op_doble_clic.connect(self._on_doble_clic)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll, 1)

    def _actualizar_leyenda(self) -> None:
        # Limpiar leyenda anterior
        lay = self.legend_frame.layout()
        for lbl in self._legend_labels:
            lay.removeWidget(lbl)
            lbl.deleteLater()
        self._legend_labels = []

        def _add_circle(color_hex: str, texto: str) -> None:
            lbl = QLabel()
            lbl.setText(f"  {texto}")
            lbl.setStyleSheet(
                f"font-size: 11px; color: #334155;")
            pixmap = lbl.grab()  # dummy
            # Usar un QLabel con indicador de color
            widget = QLabel()
            widget.setStyleSheet(
                f"background-color: {color_hex}; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px;")
            widget.setFixedSize(10, 10)
            container = QLabel(f" {texto}")
            container.setStyleSheet("font-size: 11px; color: #334155;")
            row = QHBoxLayout()
            row.setSpacing(4)
            row.setContentsMargins(0, 0, 8, 0)
            row.addWidget(widget)
            row.addWidget(container)
            wrapper = QWidget()
            wrapper.setLayout(row)
            lay.insertWidget(lay.count() - 1, wrapper)
            self._legend_labels.append(wrapper)

        estaciones = self.controller.listar_estaciones()
        for i, est in enumerate(estaciones):
            color = COLOR_ESTACION[i % len(COLOR_ESTACION)]
            _add_circle(color, est["nombre"])
        _add_circle(COLOR_PLANEADA, "Planeada")
        _add_circle(COLOR_TERMINADA, "Terminada")

    def _actualizar_titulo_mes(self) -> None:
        nombres = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        self.lbl_mes.setText(f"{nombres[self._mes_actual]} {self._anio_actual}")

    def _mes_anterior(self) -> None:
        if self._mes_actual == 1:
            self._mes_actual = 12
            self._anio_actual -= 1
        else:
            self._mes_actual -= 1
        self.recargar()

    def _mes_siguiente(self) -> None:
        if self._mes_actual == 12:
            self._mes_actual = 1
            self._anio_actual += 1
        else:
            self._mes_actual += 1
        self.recargar()

    def _ir_hoy(self) -> None:
        hoy = date.today()
        self._mes_actual = hoy.month
        self._anio_actual = hoy.year
        self.recargar()

    def recargar(self) -> None:
        self._actualizar_titulo_mes()
        self._actualizar_leyenda()

        # Calcular rango de fechas del mes
        try:
            self.canvas.fecha_inicio = date(self._anio_actual, self._mes_actual, 1)
        except ValueError:
            self.canvas.fecha_inicio = date.today().replace(day=1)

        # Dias en el mes
        if self._mes_actual == 12:
            siguiente = date(self._anio_actual + 1, 1, 1)
        else:
            siguiente = date(self._anio_actual, self._mes_actual + 1, 1)
        self.canvas.dias_mes = (siguiente - self.canvas.fecha_inicio).days

        # Cargar OPs
        try:
            self.canvas.ops = self.controller.listar_ops()
        except Exception:
            self.canvas.ops = []

        # Construir mapa de estaciones
        mapa_est = {}
        estaciones = self.controller.listar_estaciones()
        for i, est in enumerate(estaciones):
            mapa_est[est["id"]] = (est["nombre"], est["orden"], COLOR_ESTACION[i % len(COLOR_ESTACION)])
        self.canvas._mapa_estaciones = mapa_est

        # Cargar barras desde seguimiento_produccion
        self.canvas.barras = {}
        for op in self.canvas.ops:
            op_id = op["id"]
            try:
                seguimiento = self.controller.obtener_seguimiento(op_id)
            except Exception:
                seguimiento = []

            barras_op = []
            for seg in seguimiento:
                fecha_ent = seg.get("fecha_entrada")
                estatus = seg.get("estatus", "pendiente")
                estacion_nombre = seg.get("estacion_nombre", "")
                estacion_orden = seg.get("orden", 0)

                # Determinar color
                if estatus == "completado" and fecha_ent:
                    fecha_sal = seg.get("fecha_salida")
                    if not fecha_sal:
                        fecha_sal = fecha_ent
                    try:
                        inicio = datetime.strptime(str(fecha_ent)[:10], "%Y-%m-%d").date()
                        fin = datetime.strptime(str(fecha_sal)[:10], "%Y-%m-%d").date()
                    except (TypeError, ValueError):
                        continue

                    # Color de la estacion
                    color = COLOR_ESTACION[(estacion_orden - 1) % len(COLOR_ESTACION)]
                    barras_op.append({
                        "estacion": estacion_nombre,
                        "inicio": inicio,
                        "fin": fin,
                        "color": color,
                    })
                elif estatus == "en_proceso" and fecha_ent:
                    try:
                        inicio = datetime.strptime(str(fecha_ent)[:10], "%Y-%m-%d").date()
                    except (TypeError, ValueError):
                        continue
                    fin = date.today()
                    color = COLOR_ESTACION[(estacion_orden - 1) % len(COLOR_ESTACION)]
                    barras_op.append({
                        "estacion": estacion_nombre,
                        "inicio": inicio,
                        "fin": fin,
                        "color": color,
                    })

            if barras_op:
                self.canvas.barras[op_id] = barras_op

        self.canvas.calcular_tamano()
        self.canvas.update()

    def _on_doble_clic(self, op_id: int) -> None:
        from src.views.dialogs import DialogSeguimientoOP
        dlg = DialogSeguimientoOP(self.controller, op_id)
        dlg.exec()
        self.recargar()
        if self.on_change:
            self.on_change()
