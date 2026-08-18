"""Prototipo híbrido: ComplexGrid + estética de ControlesPreview.

Combina el motor de datos de ComplexGrid (multi-vistas, búsqueda, agrupación,
ordenamiento, acciones, exportación) con la estética del prototipo de sandbox:
toolbar con botones coloridos, panel de formulario/detalle lateral,
barra de estado inferior y paleta teal.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from src.components import obtener_componente
from src.utils.icons import mono_icon

ComplexGrid = obtener_componente("complexGrid")

# Paleta teal (de ControlesPreview)
TEAL_CLARO = "#7EBCB1"
TEAL_OSCURO = "#07756A"
CIAN_CLARO = "#B2DFDB"
GRIS_TOOLBAR = "#E4E9ED"
GRIS_BORDE = "#A9A9A9"
TEXTO_OSCURO = "#111111"
ROJO = "#C93744"
AZUL_ACCION = "#1892D4"
VERDE = "#16A34A"
PURPURA = "#77307E"
NARANJA = "#EF7218"
TEAL_ICONO = "#22A8C6"

# Datos demo (estilo fábrica de calzado)
_DATOS_DEMO = [
    {"lote": "L-1001", "estilo": "Bota Vaquera 7\"", "linea": "Línea 1",
     "color": "Café", "pares": 240, "estatus": "en_produccion"},
    {"lote": "L-1002", "estilo": "Botín Clásico", "linea": "Línea 2",
     "color": "Negro", "pares": 180, "estatus": "pendiente"},
    {"lote": "L-1003", "estilo": "Tenis Urbano", "linea": "Línea 3",
     "color": "Blanco", "pares": 320, "estatus": "completado"},
    {"lote": "L-1004", "estilo": "Sandalia Playa", "linea": "Línea 4",
     "color": "Beige", "pares": 150, "estatus": "pendiente"},
    {"lote": "L-1005", "estilo": "Mocasín Ejecutivo", "linea": "Línea 1",
     "color": "Azul Marino", "pares": 96, "estatus": "en_produccion"},
    {"lote": "L-1006", "estilo": "Bota Industrial", "linea": "Línea 5",
     "color": "Café Oscuro", "pares": 210, "estatus": "completado"},
    {"lote": "L-1007", "estilo": "Zapatilla Casual", "linea": "Línea 2",
     "color": "Rojo", "pares": 175, "estatus": "en_produccion"},
    {"lote": "L-1008", "estilo": "Charol Fiesta", "linea": "Línea 3",
     "color": "Negro", "pares": 88, "estatus": "pendiente"},
    {"lote": "L-1009", "estilo": "Huarache Tradicional", "linea": "Línea 4",
     "color": "Café", "pares": 260, "estatus": "completado"},
    {"lote": "L-1010", "estilo": "Botín Caminata", "linea": "Línea 5",
     "color": "Gris", "pares": 120, "estatus": "pendiente"},
]

_LINEAS = ["Línea 1", "Línea 2", "Línea 3", "Línea 4", "Línea 5"]
_COLORES = ["Negro", "Café", "Blanco", "Azul Marino", "Rojo", "Beige",
            "Gris", "Café Oscuro"]

_ESTILOS_MAP = {
    "pendiente": {"bg": "#FFF7CC", "fg": "#5C4A00"},
    "en_produccion": {"bg": "#DCE9FB", "fg": "#1E4A8F"},
    "completado": {"bg": "#DDF0DF", "fg": "#2E6E31"},
}

_QSS = f"""
QFrame#hgToolbar {{
    background: {GRIS_TOOLBAR};
    border: 1px solid {GRIS_BORDE};
    border-radius: 4px;
}}
QToolButton#hgToolBtn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #1F2937;
    font-weight: 600;
    font-size: 11px;
    padding: 4px 8px;
}}
QToolButton#hgToolBtn:hover {{ background: #C9D4D6; }}
QToolButton#hgToolBtn:checked {{
    background: {TEAL_OSCURO};
    color: #ffffff;
}}
QGroupBox#hgFormPanel {{
    background: #F4F6F7;
    border: 1px solid #9AA5AE;
    border-radius: 4px;
    margin-top: 12px;
    font-size: 12px;
}}
QGroupBox#hgFormPanel::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEAL_OSCURO};
    font-weight: 700;
    font-size: 12px;
}}
QLabel#hgLabel {{
    color: #404040;
    font-weight: 700;
    font-size: 12px;
}}
QLineEdit#hgInput, QComboBox#hgInput, QSpinBox#hgInput {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: {TEXTO_OSCURO};
    padding: 4px 6px;
    selection-background-color: {TEAL_OSCURO};
    selection-color: #ffffff;
    min-height: 20px;
}}
QLineEdit#hgInput:focus, QComboBox#hgInput:focus, QSpinBox#hgInput:focus {{
    border: 1px solid {TEAL_OSCURO};
}}
QPushButton#hgBtnPrimary {{
    background: {TEAL_OSCURO};
    color: #ffffff;
    border: none;
    border-radius: 3px;
    font-weight: 700;
    padding: 6px 16px;
    font-size: 12px;
}}
QPushButton#hgBtnPrimary:hover {{
    background: {TEAL_CLARO};
}}
QPushButton#hgBtnGray {{
    background: {GRIS_TOOLBAR};
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: #1F2937;
    font-weight: 600;
    padding: 7px 16px;
    font-size: 12px;
}}
QPushButton#hgBtnGray:hover {{ background: #D2D2D2; }}
QPushButton#hgBtnDanger {{
    background: #ffffff;
    border: 2px solid {ROJO};
    border-radius: 3px;
    color: #1F2937;
    font-weight: 700;
    padding: 6px 16px;
    font-size: 12px;
}}
QPushButton#hgBtnDanger:hover {{ background: #FDECEC; }}
QFrame#hgStatus {{
    background: {TEAL_OSCURO};
    border-radius: 4px;
}}
QLabel#hgStatusLabel {{
    color: #ffffff;
    font-weight: 600;
    font-size: 12px;
}}
"""


class _ToolBtn:
    """Factory para botones de toolbar estilo prototipo."""

    @staticmethod
    def crear(texto: str, icono: QIcon, fn, checkable: bool = False):
        from PySide6.QtWidgets import QToolButton
        btn = QToolButton()
        btn.setObjectName("hgToolBtn")
        btn.setText(texto)
        btn.setIcon(icono)
        btn.setIconSize(QSize(26, 26))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setFixedSize(78, 52)
        btn.setCheckable(checkable)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(fn)
        return btn


class GridHibridoDemo(QWidget):
    """Prototipo híbrido: motor ComplexGrid + estética ControlesPreview."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._datos = list(_DATOS_DEMO)
        self._fila_seleccionada: int | None = None
        self.setStyleSheet(_QSS)
        self._setup_ui()
        self._cargar_datos()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(self._crear_toolbar())
        body = QHBoxLayout()
        body.setSpacing(8)
        self.grid = ComplexGrid()
        body.addWidget(self.grid, 1)
        body.addWidget(self._crear_panel_formulario(), 0)
        root.addLayout(body, 1)
        root.addWidget(self._crear_barra_estado())

    # ---------------------------------------------------------- toolbar
    def _crear_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("hgToolbar")
        bar.setFixedHeight(64)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        from PySide6.QtWidgets import QToolButton

        lay.addWidget(_ToolBtn.crear(
            "Buscar", mono_icon("buscar", 26, AZUL_ACCION),
            self._toggle_buscar, checkable=True))
        lay.addWidget(_ToolBtn.crear(
            "Imprimir", mono_icon("imprimir", 26, TEAL_ICONO),
            self._imprimir))
        lay.addWidget(_ToolBtn.crear(
            "Vista previa", mono_icon("ver", 26, PURPURA),
            self._vista_previa))
        lay.addWidget(_ToolBtn.crear(
            "Exportar", mono_icon("excel", 26, VERDE),
            self._exportar_excel))
        lay.addStretch()

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar lote, estilo, color...")
        self.txt_buscar.setFixedWidth(260)
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.returnPressed.connect(self._buscar)
        self.txt_buscar.hide()
        lay.addWidget(self.txt_buscar)

        return bar

    # ---------------------------------------------------------- formulario
    def _crear_panel_formulario(self) -> QGroupBox:
        panel = QGroupBox("Detalles")
        panel.setObjectName("hgFormPanel")
        panel.setFixedWidth(320)
        lay = QVBoxLayout(panel)
        lay.setSpacing(6)

        self.txt_lote = QLineEdit()
        self.txt_lote.setObjectName("hgInput")
        self.txt_lote.setPlaceholderText("Ej: L-1011")
        lay.addLayout(self._fila("Lote:", self.txt_lote))

        self.txt_estilo = QLineEdit()
        self.txt_estilo.setObjectName("hgInput")
        self.txt_estilo.setPlaceholderText("Ej: Bota Vaquera")
        lay.addLayout(self._fila("Estilo:", self.txt_estilo))

        self.cmb_linea = QComboBox()
        self.cmb_linea.setObjectName("hgInput")
        self.cmb_linea.addItems(_LINEAS)
        lay.addLayout(self._fila("Línea:", self.cmb_linea))

        self.cmb_color = QComboBox()
        self.cmb_color.setObjectName("hgInput")
        self.cmb_color.addItems(_COLORES)
        lay.addLayout(self._fila("Color:", self.cmb_color))

        self.spn_pares = QSpinBox()
        self.spn_pares.setObjectName("hgInput")
        self.spn_pares.setRange(0, 99999)
        lay.addLayout(self._fila("Pares:", self.spn_pares))

        lay.addSpacing(8)
        btns = QHBoxLayout()
        btn_nuevo = QPushButton("Nuevo")
        btn_nuevo.setObjectName("hgBtnGray")
        btn_nuevo.clicked.connect(self._nuevo)
        btns.addWidget(btn_nuevo)
        btn_editar = QPushButton("Editar")
        btn_editar.setObjectName("hgBtnDanger")
        btn_editar.clicked.connect(self._editar)
        btns.addWidget(btn_editar)
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.setObjectName("hgBtnPrimary")
        btn_aceptar.clicked.connect(self._aceptar)
        btns.addWidget(btn_aceptar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("hgBtnGray")
        btn_cancelar.clicked.connect(self._cancelar)
        btns.addWidget(btn_cancelar)
        lay.addLayout(btns)

        lay.addStretch()
        return panel

    @staticmethod
    def _fila(label_text: str, widget: QWidget) -> QHBoxLayout:
        lbl = QLabel(label_text)
        lbl.setObjectName("hgLabel")
        lbl.setMinimumWidth(52)
        row = QHBoxLayout()
        row.addWidget(lbl)
        row.addWidget(widget, 1)
        return row

    # ---------------------------------------------------------- status bar
    def _crear_barra_estado(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("hgStatus")
        frame.setFixedHeight(32)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 4, 12, 4)
        self.lbl_status = QLabel("Listo")
        self.lbl_status.setObjectName("hgStatusLabel")
        lay.addWidget(self.lbl_status)
        lay.addStretch()
        self.lbl_total = QLabel("")
        self.lbl_total.setObjectName("hgStatusLabel")
        lay.addWidget(self.lbl_total)
        return frame

    # ---------------------------------------------------------- grid setup
    def _cargar_datos(self) -> None:
        self.grid.set_columnas([
            {"key": "lote", "titulo": "Lote", "ancho": 90},
            {"key": "estilo", "titulo": "Estilo", "ancho": 200},
            {"key": "linea", "titulo": "Línea", "ancho": 100},
            {"key": "color", "titulo": "Color", "ancho": 100},
            {"key": "pares", "titulo": "Pares", "ancho": 80, "tipo": "numero"},
            {"key": "estatus", "titulo": "Estatus", "ancho": 120},
        ])
        self.grid.set_renderers(
            fila=lambda r: [r["lote"], r["estilo"], r["linea"],
                            r["color"], str(r["pares"]), r["estatus"]],
            claves=lambda r: [r["lote"], r["estilo"], r["linea"],
                              r["color"], r["pares"], r["estatus"]],
            tarjeta=lambda r: {
                "tile": r["lote"][:2],
                "icono": "inventario",
                "color": _ESTILOS_MAP.get(r["estatus"], {}).get(
                    "fg", TEAL_OSCURO),
                "titulo": r["estilo"],
                "subtitulo": f"{r['lote']}  ·  {r['color']}",
                "badge": f"{r['pares']} pares",
            },
            lista=lambda r: (r["estilo"],
                             f"{r['lote']}  |  {r['linea']}  |  "
                             f"{r['color']}  |  {r['pares']} pares"),
            estilo=self._estilo_fila,
        )
        self.grid.set_acciones([
            {"texto": "Editar", "icono": "editar", "color": "#4f46e5",
             "callback": self._editar_registro},
            {"texto": "Eliminar", "icono": "eliminar", "color": "#dc2626",
             "callback": self._eliminar_registro},
        ])
        self.grid.set_reporte_config({
            "titulo": "Reporte de Producción",
            "subtitulo": "Lotes y estilos en proceso",
        })
        self.grid.set_datos(self._datos)
        self.grid.set_vista("tabla")
        self.grid.selectionChanged.connect(self._on_seleccion)
        self._actualizar_status()

    def _estilo_fila(self, rec: dict, item, col: int) -> None:
        estilo = _ESTILOS_MAP.get(rec.get("estatus", ""), {})
        if col == 5 and estilo:
            item.setBackground(QColor(estilo["bg"]))
            item.setForeground(QColor(estilo["fg"]))
            item.setTextAlignment(Qt.AlignCenter)

    # ---------------------------------------------------------- acciones
    def _toggle_buscar(self) -> None:
        if self.txt_buscar.isVisible():
            self.txt_buscar.hide()
            self.grid.buscar("")
        else:
            self.txt_buscar.show()
            self.txt_buscar.setFocus()

    def _buscar(self) -> None:
        self.grid.buscar(self.txt_buscar.text())

    def _imprimir(self) -> None:
        self.grid.imprimir()

    def _vista_previa(self) -> None:
        self.grid.exportar_pdf()

    def _exportar_excel(self) -> None:
        self.grid.exportar_excel()

    def _nuevo(self) -> None:
        self._limpiar_forma()
        self.lbl_status.setText("Creando nuevo registro...")

    def _editar(self) -> None:
        reg = self.grid.registro_seleccionado()
        if reg is None:
            self.lbl_status.setText("Seleccione un registro para editar.")
            return
        self._cargar_forma(reg)
        self.lbl_status.setText(f"Editando {reg['lote']} — {reg['estilo']}")

    def _aceptar(self) -> None:
        lote = self.txt_lote.text().strip()
        estilo = self.txt_estilo.text().strip()
        if not lote or not estilo:
            self.lbl_status.setText("Lote y Estilo son obligatorios.")
            return
        registro = {
            "lote": lote, "estilo": estilo,
            "linea": self.cmb_linea.currentText(),
            "color": self.cmb_color.currentText(),
            "pares": self.spn_pares.value(),
            "estatus": "pendiente",
        }
        if self._fila_seleccionada is not None:
            self._datos[self._fila_seleccionada] = registro
            self.lbl_status.setText(f"Registro {lote} actualizado.")
        else:
            self._datos.append(registro)
            self.lbl_status.setText(f"Registro {lote} agregado.")
        self.grid.set_datos(self._datos)
        self._limpiar_forma()
        self._actualizar_status()

    def _cancelar(self) -> None:
        self._limpiar_forma()
        self.lbl_status.setText("Listo")

    def _editar_registro(self, rec: dict) -> None:
        idx = next((i for i, r in enumerate(self._datos)
                     if r["lote"] == rec["lote"]), None)
        if idx is not None:
            self._fila_seleccionada = idx
            self._cargar_forma(rec)
            self.lbl_status.setText(f"Editando {rec['lote']}")

    def _eliminar_registro(self, rec: dict) -> None:
        self._datos = [r for r in self._datos if r["lote"] != rec["lote"]]
        self.grid.set_datos(self._datos)
        self._limpiar_forma()
        self._actualizar_status()
        self.lbl_status.setText(f"Registro {rec['lote']} eliminado.")

    def _on_seleccion(self) -> None:
        reg = self.grid.registro_seleccionado()
        if reg:
            idx = next((i for i, r in enumerate(self._datos)
                         if r["lote"] == reg["lote"]), None)
            self._fila_seleccionada = idx
            self._cargar_forma(reg)

    def _cargar_forma(self, rec: dict) -> None:
        self.txt_lote.setText(rec["lote"])
        self.txt_estilo.setText(rec["estilo"])
        self.cmb_linea.setCurrentText(rec["linea"])
        self.cmb_color.setCurrentText(rec["color"])
        self.spn_pares.setValue(rec["pares"])

    def _limpiar_forma(self) -> None:
        self._fila_seleccionada = None
        self.txt_lote.clear()
        self.txt_estilo.clear()
        self.cmb_linea.setCurrentIndex(0)
        self.cmb_color.setCurrentIndex(0)
        self.spn_pares.setValue(0)
        self.lbl_status.setText("Listo")

    def _actualizar_status(self) -> None:
        visibles = self.grid.datos_visibles()
        total_pares = sum(r["pares"] for r in visibles)
        self.lbl_total.setText(
            f"{len(visibles)} lotes  ·  {total_pares} pares totales")
