"""Vista del Dashboard del sistema.

Pantalla de resumen con indicadores clave (tarjetas KPI), una gráfica de
barras de compras por mes y tablas de detalle: últimas órdenes de compra,
órdenes de producción en curso, insumos con stock bajo y movimientos
recientes de inventario. Todos los datos llegan vía `DashboardController`
(A-01: la vista nunca toca la BD).
"""
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.controllers.dashboard_controller import DashboardController


class TarjetaKPI(QFrame):
    """Tarjeta de indicador clave: valor grande + título + detalle.

    Si se le asigna un módulo destino (`destino`), es clicable y emite
    `clic` al presionarla para navegar al módulo correspondiente.
    """

    clic = Signal()

    def __init__(self, titulo: str, color: str = "#0D9488",
                 parent: QWidget | None = None,
                 destino: str | None = None,
                 tooltip_destino: str = "") -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(96)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(2)

        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_valor = QLabel("—")
        self.lbl_valor.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #0f172a;")
        lay.addWidget(self.lbl_valor)

        self.lbl_detalle = QLabel("")
        self.lbl_detalle.setStyleSheet("color: #64748b; font-size: 11px;")
        lay.addWidget(self.lbl_detalle)

        if destino:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip(tooltip_destino or f"Ir a {titulo}")
            # Activa el estilo hover del tema (styles.qss: borde teal + fondo)
            self.setProperty("clicable", True)

    def establecer(self, valor: str, detalle: str = "") -> None:
        self.lbl_valor.setText(valor)
        self.lbl_detalle.setText(detalle)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (API Qt)
        if event.button() == Qt.LeftButton:
            self.clic.emit()
        super().mousePressEvent(event)


class GraficaBarras(QWidget):
    """Gráfica de barras simple dibujada con QPainter (sin dependencias)."""

    def __init__(self, titulo: str, color: str = "#1892D4",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._titulo = titulo
        self._color = QColor(color)
        self._datos: list[tuple[str, float]] = []
        self.setMinimumHeight(220)

    def establecer_datos(self, datos: list[tuple[str, float]]) -> None:
        self._datos = datos
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 (API Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(10, 30, -10, -34)

        p.setPen(QPen(QColor("#0f172a")))
        f = self.font()
        f.setBold(True)
        p.setFont(f)
        p.drawText(10, 20, self._titulo)

        if not self._datos:
            p.setPen(QPen(QColor("#94a3b8")))
            p.drawText(rect, Qt.AlignCenter, "Sin datos")
            p.end()
            return

        maximo = max(v for _, v in self._datos) or 1.0
        n = len(self._datos)
        ancho_barra = max(18, int(rect.width() / n * 0.55))
        paso = rect.width() / n

        f_peq = self.font()
        f_peq.setPointSize(max(7, f.pointSize() - 3))
        p.setFont(f_peq)

        for i, (etiqueta, valor) in enumerate(self._datos):
            alto = int(rect.height() * (valor / maximo))
            x = int(rect.left() + i * paso + (paso - ancho_barra) / 2)
            y = rect.bottom() - alto
            p.setBrush(self._color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(x, y, ancho_barra, alto, 4, 4)
            # Valor encima de la barra y etiqueta debajo
            p.setPen(QPen(QColor("#334155")))
            texto_valor = f"{valor:,.0f}" if valor >= 1 else "0"
            p.drawText(x - 14, y - 6, ancho_barra + 28, 14,
                       Qt.AlignCenter, texto_valor)
            p.drawText(x - 20, rect.bottom() + 4, ancho_barra + 40, 14,
                       Qt.AlignCenter, etiqueta)
        p.end()


def _tabla_simple(columnas: list[str], anchos: list[int]) -> QTableWidget:
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.setAlternatingRowColors(True)
    for c, ancho in enumerate(anchos):
        tabla.setColumnWidth(c, ancho)
    return tabla


def _fila(tabla: QTableWidget, valores: list[str],
          alineaciones: dict[int, Qt.AlignmentFlag] | None = None) -> None:
    r = tabla.rowCount()
    tabla.insertRow(r)
    alineaciones = alineaciones or {}
    for c, texto in enumerate(valores):
        item = QTableWidgetItem(texto)
        if c in alineaciones:
            item.setTextAlignment(alineaciones[c])
        tabla.setItem(r, c, item)


class DashboardView(QWidget):
    """Pantalla principal del Dashboard del sistema.

    Emite `navegar_modulo(clave)` cuando el usuario hace clic en una tarjeta
    KPI; la ventana principal decide cómo navegar (respetando permisos).
    """

    navegar_modulo = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = DashboardController()
        self._setup_ui()
        self.recargar()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        contenido = QWidget()
        cl = QVBoxLayout(contenido)
        cl.setContentsMargins(16, 12, 16, 16)
        cl.setSpacing(12)

        # Encabezado -----------------------------------------------------
        fila_header = QHBoxLayout()
        titulo = QLabel("Dashboard")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        self.lbl_fecha = QLabel("")
        self.lbl_fecha.setStyleSheet("color: #64748b;")
        btn_actualizar = QPushButton("⟳ Actualizar")
        btn_actualizar.setObjectName("btnSecondary")
        btn_actualizar.setCursor(Qt.PointingHandCursor)
        btn_actualizar.clicked.connect(self.recargar)
        fila_header.addWidget(titulo)
        fila_header.addStretch()
        fila_header.addWidget(self.lbl_fecha)
        fila_header.addWidget(btn_actualizar)
        cl.addLayout(fila_header)

        # Tarjetas KPI ----------------------------------------------------
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(10)
        # Cada tarjeta KPI navega a su módulo al hacer clic.
        self.card_oc = TarjetaKPI("OC pendientes", "#1892D4",
                                  destino="ordenes_compra",
                                  tooltip_destino="Ver Órdenes de Compra")
        self.card_oc_mes = TarjetaKPI("Compras del mes", "#2563EB",
                                      destino="ordenes_compra",
                                      tooltip_destino="Ver Órdenes de Compra")
        self.card_op = TarjetaKPI("Producción en curso", "#16A34A",
                                  destino="produccion",
                                  tooltip_destino="Ver Producción")
        self.card_bajo = TarjetaKPI("Insumos stock bajo", "#DC2626",
                                    destino="inventario",
                                    tooltip_destino="Ver Inventario")
        self.card_pt = TarjetaKPI("Pares en PT", "#E3C14D",
                                  destino="produccion",
                                  tooltip_destino="Ver Producto Terminado")
        self.card_mov = TarjetaKPI("Movimientos hoy", "#77307E",
                                   destino="inventario",
                                   tooltip_destino="Ver Inventario")
        destinos = {
            self.card_oc: "ordenes_compra", self.card_oc_mes: "ordenes_compra",
            self.card_op: "produccion", self.card_bajo: "inventario",
            self.card_pt: "produccion", self.card_mov: "inventario",
        }
        for c, card in enumerate([self.card_oc, self.card_oc_mes,
                                  self.card_op, self.card_bajo,
                                  self.card_pt, self.card_mov]):
            card.clic.connect(
                lambda modulo=destinos[card]: self.navegar_modulo.emit(modulo))
            grid_kpi.addWidget(card, 0, c)
        cl.addLayout(grid_kpi)

        # Fila media: gráfica + últimas OC ---------------------------------
        fila_media = QHBoxLayout()
        fila_media.setSpacing(10)

        grp_grafica = QFrame()
        grp_grafica.setObjectName("card")
        gl = QVBoxLayout(grp_grafica)
        gl.setContentsMargins(8, 8, 8, 8)
        self.grafica_compras = GraficaBarras("Compras por mes (importe $)")
        gl.addWidget(self.grafica_compras)
        fila_media.addWidget(grp_grafica, 2)

        grp_oc = QFrame()
        grp_oc.setObjectName("card")
        ol = QVBoxLayout(grp_oc)
        ol.setContentsMargins(8, 8, 8, 8)
        lbl_oc = QLabel("Últimas Órdenes de Compra")
        lbl_oc.setStyleSheet("font-weight: bold; color: #334155;")
        self.tabla_oc = _tabla_simple(
            ["Folio", "Proveedor", "Estatus", "Total", "Fecha"],
            [90, 170, 110, 100, 90])
        ol.addWidget(lbl_oc)
        ol.addWidget(self.tabla_oc)
        fila_media.addWidget(grp_oc, 3)
        cl.addLayout(fila_media, 2)

        # Fila inferior: OPs + stock bajo + movimientos --------------------
        fila_inf = QHBoxLayout()
        fila_inf.setSpacing(10)

        grp_op = QFrame()
        grp_op.setObjectName("card")
        opl = QVBoxLayout(grp_op)
        opl.setContentsMargins(8, 8, 8, 8)
        lbl_op = QLabel("Órdenes de Producción en curso")
        lbl_op.setStyleSheet("font-weight: bold; color: #334155;")
        self.tabla_op = _tabla_simple(
            ["Folio", "Modelo", "Variante", "Pares", "Entrega"],
            [80, 150, 120, 60, 85])
        opl.addWidget(lbl_op)
        opl.addWidget(self.tabla_op)
        fila_inf.addWidget(grp_op, 3)

        grp_bajo = QFrame()
        grp_bajo.setObjectName("card")
        bl = QVBoxLayout(grp_bajo)
        bl.setContentsMargins(8, 8, 8, 8)
        lbl_bajo = QLabel("Insumos con stock bajo o crítico")
        lbl_bajo.setStyleSheet("font-weight: bold; color: #b91c1c;")
        self.tabla_bajo = _tabla_simple(
            ["Código", "Insumo", "Stock", "Mínimo"], [80, 190, 70, 70])
        bl.addWidget(lbl_bajo)
        bl.addWidget(self.tabla_bajo)
        fila_inf.addWidget(grp_bajo, 3)

        grp_mov = QFrame()
        grp_mov.setObjectName("card")
        ml = QVBoxLayout(grp_mov)
        ml.setContentsMargins(8, 8, 8, 8)
        lbl_mov = QLabel("Movimientos recientes de inventario")
        lbl_mov.setStyleSheet("font-weight: bold; color: #334155;")
        self.tabla_mov = _tabla_simple(
            ["Fecha", "Tipo", "Insumo", "Cantidad"], [130, 75, 160, 75])
        ml.addWidget(lbl_mov)
        ml.addWidget(self.tabla_mov)
        fila_inf.addWidget(grp_mov, 3)
        cl.addLayout(fila_inf, 3)

        area.setWidget(contenido)
        raiz.addWidget(area)

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def recargar(self) -> None:
        """Vuelve a consultar todos los indicadores y detalles."""
        self.lbl_fecha.setText(
            datetime.now().strftime("Actualizado: %d/%m/%Y %H:%M"))
        try:
            resumen = self.controller.obtener_resumen()
            self.card_oc.establecer(
                str(resumen.get("oc_pendientes", 0)), "por recibir")
            self.card_oc_mes.establecer(
                f"${resumen.get('oc_importe_mes', 0):,.0f}",
                f"{resumen.get('oc_mes', 0)} OC este mes")
            self.card_op.establecer(
                str(resumen.get("op_produccion", 0)),
                f"{resumen.get('op_planeadas', 0)} planeadas")
            self.card_bajo.establecer(
                str(resumen.get("insumos_bajo_stock", 0)), "requieren compra")
            self.card_pt.establecer(
                f"{resumen.get('pares_pt', 0):,.0f}",
                f"{resumen.get('modelos_activos', 0)} modelos activos")
            self.card_mov.establecer(
                str(resumen.get("movimientos_hoy", 0)),
                f"{resumen.get('clientes_activos', 0)} clientes activos")

            self.grafica_compras.establecer_datos([
                (d.get("mes", ""), float(d.get("total", 0) or 0))
                for d in self.controller.obtener_compras_por_mes()])

            self.tabla_oc.setRowCount(0)
            for oc in self.controller.obtener_ultimas_oc():
                _fila(self.tabla_oc, [
                    oc.get("folio") or "", oc.get("proveedor_nombre") or "",
                    oc.get("estatus") or "", f"${float(oc.get('total', 0) or 0):,.2f}",
                    (oc.get("fecha_emision") or "")[:10]],
                    {3: Qt.AlignRight | Qt.AlignVCenter})

            self.tabla_op.setRowCount(0)
            for op in self.controller.obtener_ops_en_curso():
                entrega = (op.get("fecha_entrega") or "—")[:10]
                _fila(self.tabla_op, [
                    op.get("folio") or "", op.get("modelo_nombre") or "",
                    op.get("codigo_variante") or "",
                    f"{op.get('total_pares', 0):,.0f}", entrega],
                    {3: Qt.AlignRight | Qt.AlignVCenter})

            self.tabla_bajo.setRowCount(0)
            for ins in self.controller.obtener_stock_bajo():
                _fila(self.tabla_bajo, [
                    ins.get("codigo") or "", ins.get("nombre") or "",
                    f"{float(ins.get('stock_actual', 0) or 0):,.1f}",
                    f"{float(ins.get('stock_minimo', 0) or 0):,.1f} "
                    f"{ins.get('unidad_medida') or ''}".strip()],
                    {2: Qt.AlignRight | Qt.AlignVCenter})

            self.tabla_mov.setRowCount(0)
            for mov in self.controller.obtener_movimientos_recientes():
                _fila(self.tabla_mov, [
                    (mov.get("created_at") or "")[:16],
                    mov.get("tipo_movimiento") or "",
                    mov.get("insumo_nombre") or "",
                    f"{float(mov.get('cantidad', 0) or 0):,.1f} "
                    f"{mov.get('unidad_medida') or ''}".strip()])
        except Exception as e:
            self.card_oc.establecer("Error", str(e)[:60])
