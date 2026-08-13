"""Sandbox: vista previa interactiva de los controles del sistema.

Prototipo visual estilo Visual Studio / WinForms para validar el diseño
antes de aplicarlo globalmente. No toca la lógica real del sistema: toda la
información es dummy y las acciones solo simulan el comportamiento.

Secciones (paleta extraída de las imágenes de referencia):
    1. Tabla / DataGrid: encabezado teal claro (#7EBCB1) con texto blanco en
       negrita, filas blancas, fila seleccionada en cian claro (#B2DFDB).
       Columnas Lote, Estilo, Línea, Color, Pares.
    2. Formulario "Detalles": campos de texto, combos y selector de fecha
       blancos con borde gris fino; etiquetas en negrita; acciones rápidas
       (botón circular rojo 'X' para limpiar y botón azul de búsqueda).
    3. Barra de herramientas: botones con ícono plano colorido + texto
       (Buscar, Imprimir, Vista previa, Vales) sobre fondo gris claro;
       botón activo resaltado en teal oscuro.
    4. Botones de acción: gris estándar y principales con ícono + texto
       ("Aceptar" con check verde y borde azul, "Editar" con 'X' roja).
    5. Panel agrupador "Detalles" y barra de estado inferior teal oscuro
       (#07756A) con texto blanco (tareas y pares totales).
"""

from PySide6.QtCore import QDate, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QToolButton, QVBoxLayout, QWidget,
)

from src.components.date_picker import DatePicker
from src.utils.icons import mono_icon
from src.views.sandbox_notificaciones import notificar_flotante

# ---------------------------------------------------------------- paleta ---
# Colores extraídos de las imágenes de referencia del prompt de Sandbox.
TEAL_CLARO = "#7EBCB1"    # encabezado de tabla (banda teal claro con texto blanco)
TEAL_OSCURO = "#07756A"   # barra de estado / botón activo / acentos
CIAN_CLARO = "#B2DFDB"    # fila seleccionada / paneles teal claro
GRIS_TOOLBAR = "#E4E9ED"  # barra de herramientas (gris claro azulado)
GRIS_BORDE = "#A9A9A9"
GRIS_LINEA = "#D6D6D6"
TEXTO_OSCURO = "#111111"
ROJO = "#C93744"
ROJO_OSCURO = "#A32D3A"
AZUL_ACCION = "#1892D4"
VERDE = "#16A34A"
DORADO = "#E3C14D"
PURPURA = "#77307E"
NARANJA = "#EF7218"
TEAL_ICONO = "#22A8C6"

_DATOS = [
    {"lote": "L-1001", "estilo": "Bota Vaquera 7\"", "linea": "Línea 1",
     "color": "Café", "pares": 240},
    {"lote": "L-1002", "estilo": "Botín Clásico", "linea": "Línea 2",
     "color": "Negro", "pares": 180},
    {"lote": "L-1003", "estilo": "Tenis Urbano", "linea": "Línea 3",
     "color": "Blanco", "pares": 320},
    {"lote": "L-1004", "estilo": "Sandalia Playa", "linea": "Línea 4",
     "color": "Beige", "pares": 150},
    {"lote": "L-1005", "estilo": "Mocasín Ejecutivo", "linea": "Línea 1",
     "color": "Azul Marino", "pares": 96},
    {"lote": "L-1006", "estilo": "Bota Industrial", "linea": "Línea 5",
     "color": "Café Oscuro", "pares": 210},
    {"lote": "L-1007", "estilo": "Zapatilla Casual", "linea": "Línea 2",
     "color": "Rojo", "pares": 175},
    {"lote": "L-1008", "estilo": "Charol Fiesta", "linea": "Línea 3",
     "color": "Negro", "pares": 88},
    {"lote": "L-1009", "estilo": "Huarache Tradicional", "linea": "Línea 4",
     "color": "Café", "pares": 260},
    {"lote": "L-1010", "estilo": "Botín Caminata", "linea": "Línea 5",
     "color": "Gris", "pares": 120},
]

_LINEAS = ["Línea 1", "Línea 2", "Línea 3", "Línea 4", "Línea 5"]
_COLORES = ["Negro", "Café", "Blanco", "Azul Marino", "Rojo", "Beige",
            "Gris", "Café Oscuro"]

_QSS = f"""
QFrame#ctlToolbar {{
    background: {GRIS_TOOLBAR};
    border: 1px solid {GRIS_BORDE};
    border-radius: 4px;
}}
QToolButton#ctlTool {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #1F2937;
    font-weight: 600;
    font-size: 11px;
    padding: 4px 8px;
}}
QToolButton#ctlTool:hover {{ background: #C9D4D6; }}
QToolButton#ctlTool:checked {{
    background: {TEAL_OSCURO};
    color: #ffffff;
}}
QGroupBox#ctlPanel {{
    background: #F4F6F7;
    border: 1px solid #9AA5AE;
    border-radius: 4px;
    margin-top: 12px;
    font-size: 12px;
}}
QGroupBox#ctlPanel::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEAL_OSCURO};
    font-weight: 700;
    font-size: 12px;
}}
QLabel#ctlLabel {{
    color: #404040;
    font-weight: 700;
    font-size: 12px;
}}
QLineEdit#ctlInput, QComboBox#ctlInput, QDateEdit#ctlInput,
QSpinBox#ctlInput {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: {TEXTO_OSCURO};
    padding: 4px 6px;
    selection-background-color: {TEAL_OSCURO};
    selection-color: #ffffff;
    min-height: 20px;
}}
QLineEdit#ctlInput:focus, QComboBox#ctlInput:focus, QDateEdit#ctlInput:focus,
QSpinBox#ctlInput:focus {{
    border: 1px solid {TEAL_OSCURO};
}}
QLineEdit#ctlInput:disabled, QComboBox#ctlInput:disabled,
QDateEdit#ctlInput:disabled, QSpinBox#ctlInput:disabled {{
    background: #F3F4F6;
    color: #6B7280;
}}
QComboBox#ctlInput::drop-down {{ border: none; width: 20px; }}
QComboBox#ctlInput::down-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #555555;
    margin-right: 6px;
}}
QComboBox#ctlInput QAbstractItemView {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    selection-background-color: {CIAN_CLARO};
    selection-color: {TEXTO_OSCURO};
}}
QSpinBox#ctlInput::up-button, QSpinBox#ctlInput::down-button {{
    border: none;
    background: #EDEFF1;
    width: 18px;
}}
QSpinBox#ctlInput::up-arrow, QSpinBox#ctlInput::down-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
}}
QSpinBox#ctlInput::up-arrow {{
    border-bottom: 5px solid #555555; margin-top: 4px;
}}
QSpinBox#ctlInput::down-arrow {{
    border-top: 5px solid #555555; margin-bottom: 4px;
}}
QDateEdit#ctlInput::drop-down {{ border: none; width: 22px; }}
QDateEdit#ctlInput::down-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #555555;
    margin-right: 7px;
}}
QPushButton#ctlClear {{
    background: {ROJO};
    color: #ffffff;
    border: none;
    border-radius: 11px;
    min-width: 22px; max-width: 22px;
    min-height: 22px; max-height: 22px;
    font-weight: 700;
    font-size: 13px;
}}
QPushButton#ctlClear:hover {{ background: {ROJO_OSCURO}; }}
QPushButton#ctlSearch {{
    background: {AZUL_ACCION};
    border: none;
    border-radius: 4px;
    min-width: 30px; max-width: 30px;
    min-height: 28px; max-height: 28px;
}}
QPushButton#ctlSearch:hover {{ background: #1565C0; }}
QPushButton#ctlBtnGray {{
    background: {GRIS_TOOLBAR};
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: #1F2937;
    font-weight: 600;
    padding: 7px 16px;
    font-size: 12px;
}}
QPushButton#ctlBtnGray:hover {{ background: #D2D2D2; }}
QPushButton#ctlBtnGray:pressed {{ background: #C4C4C4; }}
QPushButton#ctlBtnPrimary {{
    background: #ffffff;
    border: 2px solid {AZUL_ACCION};
    border-radius: 3px;
    color: #1F2937;
    font-weight: 700;
    padding: 6px 16px;
    font-size: 12px;
}}
QPushButton#ctlBtnPrimary:hover {{ background: #EAF4FE; }}
QPushButton#ctlBtnDanger {{
    background: #ffffff;
    border: 2px solid {ROJO};
    border-radius: 3px;
    color: #1F2937;
    font-weight: 700;
    padding: 6px 16px;
    font-size: 12px;
}}
QPushButton#ctlBtnDanger:hover {{ background: #FDECEC; }}
QTableWidget#ctlTable {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    gridline-color: {GRIS_LINEA};
    alternate-background-color: #ffffff;
}}
QTableWidget#ctlTable::item {{
    background: #ffffff;
    color: {TEXTO_OSCURO};
    border: none;
    padding: 2px 6px;
}}
QTableWidget#ctlTable::item:selected {{
    background: {CIAN_CLARO};
    color: {TEXTO_OSCURO};
}}
QHeaderView::section {{
    background: {TEAL_CLARO};
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-right: 1px solid #6FA89F;
    padding: 6px 8px;
}}
QFrame#ctlStatus {{
    background: {TEAL_OSCURO};
    border-radius: 4px;
}}
QLabel#ctlStatusLabel {{
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
}}
QFrame#ctlSep {{
    background: rgba(255, 255, 255, 0.45);
}}
"""


def _icono_x(color: str = ROJO, size: int = 20) -> QIcon:
    """Ícono plano de 'X' roja (acción de editar/limpiar)."""
    pm = _pixmap_base(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(max(2.2, size * 0.14))
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    m = size * 0.22
    p.drawLine(QRectF(m, m, size - 2 * m, size - 2 * m).topLeft(),
               QRectF(m, m, size - 2 * m, size - 2 * m).bottomRight())
    p.drawLine(QRectF(m, m, size - 2 * m, size - 2 * m).topRight(),
               QRectF(m, m, size - 2 * m, size - 2 * m).bottomLeft())
    p.end()
    return QIcon(pm)


def _icono_vales(color: str = NARANJA, size: int = 26) -> QIcon:
    """Ícono plano de vale/ticket (barra de herramientas)."""
    pm = _pixmap_base(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(color))
    w, h = size * 0.6, size * 0.72
    x, y = (size - w) / 2, (size - h) / 2
    r = size * 0.08
    p.drawRoundedRect(QRectF(x, y, w, h), r, r)
    # muescas laterales (simulan el corte del ticket)
    p.setCompositionMode(QPainter.CompositionMode_Clear)
    p.drawEllipse(QRectF(x - size * 0.06, y + h * 0.28, size * 0.12, size * 0.12))
    p.drawEllipse(QRectF(x + w - size * 0.06, y + h * 0.28, size * 0.12, size * 0.12))
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
    # líneas del ticket
    p.setPen(QPen(QColor("#FFFFFF")))
    p.setBrush(Qt.NoBrush)
    lw = size * 0.045
    p.setPen(QPen(QColor("#FFFFFF"), lw))
    for i, fx in enumerate((0.18, 0.42, 0.66)):
        p.drawLine(QRectF(x, y, w, h).topLeft() + QPointF(w * fx, h * 0.62),
                   QRectF(x, y, w, h).topLeft() + QPointF(w * fx, h * 0.62)
                   + QPointF(w * 0.16, 0))
    p.end()
    return QIcon(pm)


def _pixmap_base(size: int):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    return pm


class ControlesPreview(QWidget):
    """Vista previa interactiva de controles con datos dummy."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._datos: list[dict] = [dict(r) for r in _DATOS]
        self._fila_editando: int | None = None
        self._vales = 12
        self.setMinimumHeight(520)
        self.setStyleSheet(_QSS)
        self._setup_ui()
        self._recargar_tabla()
        self._actualizar_estado()

    # ------------------------------------------------------------ interfaz
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(self._crear_toolbar())

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        cuerpo.addWidget(self._crear_formulario())
        cuerpo.addWidget(self._crear_tabla_area(), 1)
        root.addLayout(cuerpo, 1)

        root.addWidget(self._crear_barra_estado())

    def _crear_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("ctlToolbar")
        bar.setFixedHeight(64)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        self._btn_buscar_tool = self._tool_btn(
            "Buscar", mono_icon("buscar", 26, AZUL_ACCION),
            self._buscar, checkable=True)
        lay.addWidget(self._btn_buscar_tool)
        lay.addWidget(self._tool_btn("Imprimir", mono_icon("imprimir", 26, TEAL_ICONO),
                                     self._imprimir))
        lay.addWidget(self._tool_btn("Vista previa", mono_icon("ver", 26, PURPURA),
                                     self._vista_previa))
        lay.addWidget(self._tool_btn("Vales", _icono_vales(color=NARANJA, size=26),
                                     self._toggle_vales, checkable=True))

        lay.addStretch()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setObjectName("ctlInput")
        self.txt_buscar.setPlaceholderText("Buscar lote o estilo…")
        self.txt_buscar.setFixedWidth(230)
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.returnPressed.connect(self._buscar)
        lay.addWidget(self.txt_buscar)
        return bar

    def _tool_btn(self, texto: str, icono: QIcon, fn, checkable: bool = False):
        btn = QToolButton()
        btn.setObjectName("ctlTool")
        btn.setText(texto)
        btn.setIcon(icono)
        btn.setIconSize(QSize(26, 26))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setCheckable(checkable)
        btn.setFixedSize(78, 52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _=False, b=btn: self._accion_tool(btn, fn))
        return btn

    def _accion_tool(self, btn: QToolButton, fn) -> None:
        if fn is None:
            return
        if btn.isCheckable():
            fn(btn.isChecked())
        else:
            fn()

    def _crear_formulario(self) -> QGroupBox:
        panel = QGroupBox("Detalles")
        panel.setObjectName("ctlPanel")
        panel.setFixedWidth(360)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 18, 14, 14)
        lay.setSpacing(10)

        self.txt_lote = QLineEdit()
        self.txt_lote.setObjectName("ctlInput")
        self.txt_lote.setPlaceholderText("Ej: L-1011")
        self.txt_estilo = QLineEdit()
        self.txt_estilo.setObjectName("ctlInput")
        self.txt_estilo.setPlaceholderText("Ej: Bota Vaquera")

        self.cmb_linea = QComboBox()
        self.cmb_linea.setObjectName("ctlInput")
        self.cmb_linea.addItems(_LINEAS)
        self.cmb_color = QComboBox()
        self.cmb_color.setObjectName("ctlInput")
        self.cmb_color.addItems(_COLORES)
        self.spn_pares = QSpinBox()
        self.spn_pares.setObjectName("ctlInput")
        self.spn_pares.setRange(0, 99999)
        self.spn_pares.setValue(0)
        self.dte_fecha = DatePicker()
        self.dte_fecha.setObjectName("ctlInput")

        def fila(label, widget):
            fila_lay = QHBoxLayout()
            fila_lay.setSpacing(8)
            lbl = QLabel(label)
            lbl.setObjectName("ctlLabel")
            lbl.setMinimumWidth(52)
            fila_lay.addWidget(lbl)
            fila_lay.addWidget(widget, 1)
            return fila_lay

        lay.addLayout(fila("Lote:", self.txt_lote))
        acc_lote = QHBoxLayout()
        acc_lote.setSpacing(6)
        acc_lote.addWidget(self._btn_limpiar(self.txt_lote))
        acc_lote.addWidget(self._btn_buscar_campo())
        lay.addLayout(acc_lote)

        lay.addLayout(fila("Estilo:", self.txt_estilo))
        acc_estilo = QHBoxLayout()
        acc_estilo.setSpacing(6)
        acc_estilo.addWidget(self._btn_limpiar(self.txt_estilo))
        lay.addLayout(acc_estilo)

        lay.addLayout(fila("Línea:", self.cmb_linea))
        lay.addLayout(fila("Color:", self.cmb_color))
        lay.addLayout(fila("Pares:", self.spn_pares))
        lay.addLayout(fila("Fecha:", self.dte_fecha))

        lay.addSpacing(6)
        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addWidget(self._boton("Nuevo", None, self._nuevo, "ctlBtnGray"))
        btns.addWidget(self._boton("Editar", _icono_x(ROJO, 18), self._editar,
                                   "ctlBtnDanger"))
        btns.addWidget(self._boton("Aceptar", mono_icon("ok", 18, VERDE),
                                   self._aceptar, "ctlBtnPrimary"))
        btns.addWidget(self._boton("Cancelar", None, self._cancelar, "ctlBtnGray"))
        lay.addLayout(btns)
        return panel

    def _btn_limpiar(self, campo: QLineEdit) -> QPushButton:
        btn = QPushButton("✕")
        btn.setObjectName("ctlClear")
        btn.setToolTip("Limpiar campo")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: (campo.clear(), campo.setFocus()))
        return btn

    def _btn_buscar_campo(self) -> QPushButton:
        btn = QPushButton()
        btn.setObjectName("ctlSearch")
        btn.setIcon(mono_icon("buscar", 16, "#FFFFFF"))
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip("Buscar este lote")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._buscar_desde_lote)
        return btn

    def _boton(self, texto: str, icono, fn, object_name: str) -> QPushButton:
        btn = QPushButton(texto)
        btn.setObjectName(object_name)
        if icono is not None:
            btn.setIcon(icono)
            btn.setIconSize(QSize(18, 18))
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(fn)
        return btn

    def _crear_tabla_area(self) -> QGroupBox:
        panel = QGroupBox("Programación de producción")
        panel.setObjectName("ctlPanel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 18, 10, 10)
        lay.setSpacing(8)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setObjectName("ctlTable")
        self.tabla.setHorizontalHeaderLabels(
            ["Lote", "Estilo", "Línea", "Color", "Pares"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.setShowGrid(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.verticalHeader().setDefaultSectionSize(30)
        self.tabla.itemSelectionChanged.connect(self._on_seleccion)
        lay.addWidget(self.tabla, 1)
        return panel

    def _crear_barra_estado(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("ctlStatus")
        bar.setFixedHeight(30)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self.lbl_tareas = QLabel()
        self.lbl_tareas.setObjectName("ctlStatusLabel")
        self.lbl_pares = QLabel()
        self.lbl_pares.setObjectName("ctlStatusLabel")
        self.lbl_vales = QLabel()
        self.lbl_vales.setObjectName("ctlStatusLabel")
        self.lbl_mensaje = QLabel("Listo")
        self.lbl_mensaje.setObjectName("ctlStatusLabel")

        for lbl in (self.lbl_tareas, self.lbl_pares, self.lbl_vales):
            lay.addWidget(lbl)
            sep = QFrame()
            sep.setObjectName("ctlSep")
            sep.setFixedSize(1, 16)
            lay.addWidget(sep)
        lay.addStretch()
        lay.addWidget(self.lbl_mensaje)
        return bar

    # ------------------------------------------------------------- datos
    def _recargar_tabla(self, filtro: str = "") -> None:
        self.tabla.setRowCount(0)
        filtro = filtro.strip().lower()
        fila_tabla = 0
        for r in self._datos:
            if filtro and filtro not in r["lote"].lower() \
                    and filtro not in r["estilo"].lower():
                continue
            self.tabla.insertRow(self.tabla.rowCount())
            for col, clave in enumerate(("lote", "estilo", "linea", "color",
                                         "pares")):
                texto = str(r[clave])
                item = QTableWidgetItem(texto)
                if clave == "pares":
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla.setItem(fila_tabla, col, item)
            fila_tabla += 1
        self._actualizar_estado()

    def _on_seleccion(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        filas_visibles = [i for i, r in enumerate(self._datos)
                          if self._fila_visible(r)]
        if fila < len(filas_visibles):
            self._cargar_fila_en_forma(filas_visibles[fila])

    def _fila_visible(self, r: dict) -> bool:
        filtro = self._filtro_actual()
        if not filtro:
            return True
        return filtro in r["lote"].lower() or filtro in r["estilo"].lower()

    def _filtro_actual(self) -> str:
        return self.txt_buscar.text().strip().lower()

    def _cargar_fila_en_forma(self, indice: int) -> None:
        r = self._datos[indice]
        self._fila_editando = indice
        self.txt_lote.setText(r["lote"])
        self.txt_estilo.setText(r["estilo"])
        self.cmb_linea.setCurrentText(r["linea"])
        self.cmb_color.setCurrentText(r["color"])
        self.spn_pares.setValue(int(r["pares"]))
        self.lbl_mensaje.setText(f"Editando {r['lote']} — {r['estilo']}")

    def _limpiar_forma(self) -> None:
        self._fila_editando = None
        self.txt_lote.clear()
        self.txt_estilo.clear()
        self.cmb_linea.setCurrentIndex(0)
        self.cmb_color.setCurrentIndex(0)
        self.spn_pares.setValue(0)
        self.dte_fecha.setDate(QDate.currentDate())
        self.tabla.clearSelection()
        self.lbl_mensaje.setText("Listo")

    # ----------------------------------------------------------- acciones
    def _nuevo(self) -> None:
        self._limpiar_forma()
        numeros = []
        for r in self._datos:
            try:
                numeros.append(int(r["lote"].replace("L-", "")))
            except ValueError:
                pass
        siguiente = (max(numeros) + 1) if numeros else 1011
        self.txt_lote.setText(f"L-{siguiente}")
        self.txt_estilo.setFocus()
        self.lbl_mensaje.setText("Nuevo registro — capture los datos y Aceptar")

    def _editar(self) -> None:
        fila = self.tabla.currentRow()
        if fila < 0:
            notificar_flotante("Seleccione una fila de la tabla para editar.",
                               tipo="warning", titulo="Editar")
            return
        self._on_seleccion()
        self.txt_estilo.setFocus()
        self.lbl_mensaje.setText("Editando registro seleccionado")

    def _aceptar(self) -> None:
        lote = self.txt_lote.text().strip()
        if not lote:
            notificar_flotante("El lote es obligatorio para guardar.",
                               tipo="error", titulo="Detalles")
            return
        fila = self._fila_editando
        if fila is not None and fila < len(self._datos):
            self._datos[fila].update({
                "lote": lote,
                "estilo": self.txt_estilo.text().strip(),
                "linea": self.cmb_linea.currentText(),
                "color": self.cmb_color.currentText(),
                "pares": self.spn_pares.value(),
            })
            notificar_flotante(f"Registro {lote} actualizado.",
                               tipo="success", titulo="Detalles")
        else:
            self._datos.append({
                "lote": lote,
                "estilo": self.txt_estilo.text().strip(),
                "linea": self.cmb_linea.currentText(),
                "color": self.cmb_color.currentText(),
                "pares": self.spn_pares.value(),
            })
            notificar_flotante(f"Registro {lote} agregado.",
                               tipo="success", titulo="Detalles")
        self._recargar_tabla(self._filtro_actual())
        self._fila_editando = None
        self.lbl_mensaje.setText(f"Guardado: {lote}")

    def _cancelar(self) -> None:
        self._limpiar_forma()
        self.lbl_mensaje.setText("Cambios descartados")

    def _buscar(self) -> None:
        filtro = self._filtro_actual()
        self._recargar_tabla(filtro)
        self._btn_buscar_tool.setChecked(bool(filtro))
        n = self.tabla.rowCount()
        if not filtro:
            self.lbl_mensaje.setText("Listo")
            return
        if n == 0:
            self.lbl_mensaje.setText("Sin resultados para la búsqueda")
            notificar_flotante("Sin resultados para la búsqueda.",
                               tipo="info", titulo="Buscar")
        else:
            self.lbl_mensaje.setText(f"{n} resultado(s) para la búsqueda")

    def _buscar_desde_lote(self) -> None:
        self.txt_buscar.setText(self.txt_lote.text().strip())
        self._buscar()

    def _imprimir(self) -> None:
        notificar_flotante("Vista de impresión preparada (2 páginas).",
                           tipo="info", titulo="Imprimir")

    def _vista_previa(self) -> None:
        notificar_flotante("Vista previa generada correctamente.",
                           tipo="success", titulo="Vista previa")

    def _toggle_vales(self, activo: bool) -> None:
        if activo:
            self.lbl_mensaje.setText(f"Vales activos: {self._vales} vales")
            notificar_flotante(f"Se muestran {self._vales} vales.",
                               tipo="info", titulo="Vales")
        else:
            self.lbl_mensaje.setText("Vales ocultos")
            notificar_flotante("Vales ocultos.", tipo="info", titulo="Vales")

    def _actualizar_estado(self) -> None:
        totales = len(self._datos)
        pares = sum(int(r["pares"] or 0) for r in self._datos)
        self.lbl_tareas.setText(f"{totales} tareas")
        self.lbl_pares.setText(f"{pares:,} pares")
        self.lbl_vales.setText(f"Vales: {self._vales}")
