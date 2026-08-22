"""Componente propio aprobado: GridHibrido.

Combina el motor de datos de ComplexGrid con una toolbar de 1 fila:
  [acciones módulo...] [separator] [Buscar | Imprimir | Vista previa | Exportar]
Y barra de estado inferior. Sin panel de formulario lateral.

Todos los botones (módulo y grid) son QToolButton con el mismo formato:
icono arriba, texto abajo, 72x48.

API pública:
    agregar_boton_toolbar(nombre, texto, icono, color, callback)
    eliminar_boton_toolbar(nombre)
    agregar_widget_toolbar(widget)
    agregar_separador_toolbar()
    set_columnas([...])
    set_datos(registros)
    ...
    Señales: doubleClicked, selectionChanged
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QToolButton, QVBoxLayout, QWidget,
)

from src.utils.icons import mono_icon

TEAL_CLARO = "#7EBCB1"
TEAL_OSCURO = "#07756A"
GRIS_TOOLBAR = "#E4E9ED"
GRIS_BORDE = "#A9A9A9"
ROJO = "#C93744"
AZUL_ACCION = "#1892D4"
VERDE = "#16A34A"
PURPURA = "#77307E"
TEAL_ICONO = "#22A8C6"

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
QToolButton#hgModBtn {{
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #1F2937;
    font-weight: 600;
    font-size: 11px;
    padding: 4px 8px;
}}
QToolButton#hgModBtn:hover {{ background: #C9D4D6; }}
QToolButton#hgModBtn:disabled {{ color: #9CA3AF; }}
QLineEdit#hgSearch {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: #111111;
    padding: 4px 8px;
    selection-background-color: {TEAL_OSCURO};
    selection-color: #ffffff;
    min-height: 20px;
}}
QLineEdit#hgSearch:focus {{ border: 1px solid {TEAL_OSCURO}; }}
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


class GridHibrido(QWidget):
    """Grid híbrido: motor ComplexGrid + toolbar 1 fila + status bar.

    Toolbar única con botones QToolButton uniformes.
    """

    doubleClicked = Signal()
    selectionChanged = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from src.components import obtener_componente
        self._ComplexGrid = obtener_componente("complexGrid")
        self._botones_toolbar: dict[str, QToolButton] = {}
        self.setStyleSheet(_QSS)
        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._crear_toolbar())

        self._grid = self._ComplexGrid()
        root.addWidget(self._grid, 1)

        root.addWidget(self._crear_barra_estado())

    def _crear_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("hgToolbar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)

        self._lay_izq = QHBoxLayout()
        self._lay_izq.setSpacing(6)
        row.addLayout(self._lay_izq)

        self._sep_modulo = QFrame()
        self._sep_modulo.setFrameShape(QFrame.VLine)
        self._sep_modulo.setFixedHeight(24)
        self._sep_modulo.setStyleSheet(f"color: {GRIS_BORDE};")
        row.addWidget(self._sep_modulo)
        self._sep_modulo.hide()

        row.addStretch()

        self._btn_buscar_toggle = self._crear_tool_btn(
            "Buscar", "buscar", AZUL_ACCION, self._toggle_buscar,
            checkable=True)
        row.addWidget(self._btn_buscar_toggle)

        self._btn_imprimir = self._crear_tool_btn(
            "Imprimir", "imprimir", TEAL_ICONO, self._on_imprimir)
        row.addWidget(self._btn_imprimir)

        self._btn_pdf = self._crear_tool_btn(
            "Vista previa", "pdf", PURPURA, self._on_pdf)
        row.addWidget(self._btn_pdf)

        self._btn_excel = self._crear_tool_btn(
            "Exportar", "exportar", VERDE, self._on_excel)
        row.addWidget(self._btn_excel)

        self._txt_buscar = QLineEdit()
        self._txt_buscar.setObjectName("hgSearch")
        self._txt_buscar.setPlaceholderText("Buscar...")
        self._txt_buscar.setFixedWidth(260)
        self._txt_buscar.setClearButtonEnabled(True)
        self._txt_buscar.textChanged.connect(self._on_buscar_texto)
        self._txt_buscar.hide()
        row.addWidget(self._txt_buscar)

        return bar

    def _crear_tool_btn(self, texto: str, icono: str, color: str,
                        fn, checkable: bool = False) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("hgToolBtn")
        btn.setText(texto)
        btn.setIcon(mono_icon(icono, 24, color))
        btn.setIconSize(QSize(24, 24))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setFixedSize(72, 48)
        btn.setCheckable(checkable)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(fn)
        return btn

    def _crear_mod_btn(self, nombre: str, texto: str, icono: str,
                       color: str, callback) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("hgModBtn")
        btn.setText(texto)
        btn.setIcon(mono_icon(icono, 24, color))
        btn.setIconSize(QSize(24, 24))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setFixedSize(72, 48)
        btn.setCursor(Qt.PointingHandCursor)
        if callback:
            btn.clicked.connect(callback)
        self._botones_toolbar[nombre] = btn
        return btn

    # ---------------------------------------------------------- API toolbar
    def agregar_boton_toolbar(self, nombre: str, texto: str, icono: str,
                              color: str, callback=None) -> QToolButton:
        """Agrega un botón al toolbar (lado izquierdo), mismo formato que
        Buscar/Imprimir/Exportar.

        Args:
            nombre: clave interna para boton_modulo() / establecer_boton_modulo()
            texto: texto visible debajo del icono
            icono: clave de icono (icons.py)
            color: color hex del icono
            callback: función al hacer clic (opcional)

        Returns:
            QToolButton creado (para configuración adicional)
        """
        btn = self._crear_mod_btn(nombre, texto, icono, color, callback)
        self._lay_izq.addWidget(btn)
        self._sep_modulo.setVisible(True)
        return btn

    def agregar_widget_toolbar(self, widget: QWidget) -> None:
        """Agrega un widget custom al toolbar (lado izquierdo)."""
        self._lay_izq.addWidget(widget)
        self._sep_modulo.setVisible(True)

    def agregar_separador_toolbar(self) -> None:
        """Agrega un separador visual al toolbar."""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet(f"color: {GRIS_BORDE};")
        self._lay_izq.addWidget(sep)

    def boton_toolbar(self, nombre: str) -> QToolButton | None:
        """Obtiene un botón del toolbar por su nombre."""
        return self._botones_toolbar.get(nombre)

    def establecer_boton_toolbar(self, nombre: str, habilitado: bool) -> None:
        """Habilita/deshabilita un botón del toolbar por su nombre."""
        btn = self._botones_toolbar.get(nombre)
        if btn:
            btn.setEnabled(habilitado)

    # compat: aliases antiguos
    def boton_modulo(self, nombre: str) -> QToolButton | None:
        return self.boton_toolbar(nombre)

    def establecer_boton_modulo(self, nombre: str, habilitado: bool) -> None:
        self.establecer_boton_toolbar(nombre, habilitado)

    # ---------------------------------------------------------- status bar
    def _crear_barra_estado(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("hgStatus")
        frame.setFixedHeight(30)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 4, 12, 4)
        self._lbl_status = QLabel("Listo")
        self._lbl_status.setObjectName("hgStatusLabel")
        lay.addWidget(self._lbl_status)
        lay.addStretch()
        self._lbl_total = QLabel("")
        self._lbl_total.setObjectName("hgStatusLabel")
        lay.addWidget(self._lbl_total)
        return frame

    # ---------------------------------------------------------- señales internas
    def _conectar_senales(self) -> None:
        self._grid.doubleClicked.connect(self.doubleClicked)
        self._grid.selectionChanged.connect(self._on_seleccion)

    def _on_seleccion(self) -> None:
        self._actualizar_status()
        self.selectionChanged.emit()

    def _actualizar_status(self) -> None:
        visibles = self._grid.datos_visibles()
        n = len(visibles)
        self._lbl_total.setText(
            f"{n} registro{'s' if n != 1 else ''}")

    # ---------------------------------------------------------- toolbar grid
    def _toggle_buscar(self) -> None:
        if self._txt_buscar.isVisible():
            self._txt_buscar.hide()
            self._grid.buscar("")
        else:
            self._txt_buscar.show()
            self._txt_buscar.setFocus()

    def _on_buscar_texto(self, texto: str) -> None:
        self._grid.buscar(texto)

    def _on_imprimir(self) -> None:
        self._grid.imprimir()

    def _on_pdf(self) -> None:
        self._grid.exportar_pdf()

    def _on_excel(self) -> None:
        self._grid.exportar_excel()

    # ---------------------------------------------------------- API pública (proxy)
    def set_imprimir_callback(self, fn) -> None:
        try:
            self._btn_imprimir.clicked.disconnect()
        except RuntimeError:
            pass
        self._btn_imprimir.clicked.connect(fn)

    def set_columnas(self, columnas: list[dict]) -> None:
        self._grid.set_columnas(columnas)

    def set_datos(self, registros) -> None:
        self._grid.set_datos(registros)
        self._actualizar_status()

    def set_renderers(self, fila=None, claves=None, tarjeta=None, lista=None,
                      estilo=None) -> None:
        self._grid.set_renderers(fila, claves, tarjeta, lista, estilo)

    def set_matriz_handler(self, fn) -> None:
        self._grid.set_matriz_handler(fn)

    def set_acciones(self, acciones: list[dict]) -> None:
        self._grid.set_acciones(acciones)

    def set_filtros(self, filtros: list) -> None:
        self._grid.set_filtros(filtros)

    def set_agrupacion(self, clave: str | None) -> None:
        self._grid.set_agrupacion(clave)

    def set_vista(self, vista: str) -> None:
        self._grid.set_vista(vista)

    def set_exportar_visible(self, visible: bool) -> None:
        self._btn_excel.setVisible(visible)
        self._btn_pdf.setVisible(visible)
        self._btn_imprimir.setVisible(visible)

    def set_buscador_visible(self, visible: bool) -> None:
        self._btn_buscar_toggle.setVisible(visible)
        if not visible:
            self._txt_buscar.hide()
            self._grid.buscar("")

    def set_agrupar_visible(self, visible: bool) -> None:
        self._grid.set_agrupar_visible(visible)

    def set_widget_izquierda(self, widget: QWidget) -> None:
        self._grid.set_widget_izquierda(widget)

    def set_plantilla_excel(self, ruta: str | None, inicio: str = "A3") -> None:
        self._grid.set_plantilla_excel(ruta, inicio)

    def set_reporte_config(self, config: dict) -> None:
        self._grid.set_reporte_config(config)

    def set_grupo_fn(self, fn) -> None:
        self._grid.set_grupo_fn(fn)

    def buscar(self, texto: str) -> None:
        self._grid.buscar(texto)
        self._txt_buscar.setText(texto)

    def registro_seleccionado(self):
        return self._grid.registro_seleccionado()

    def datos_visibles(self) -> list:
        return self._grid.datos_visibles()

    def registros_seleccionados(self) -> list:
        return self._grid.registros_seleccionados()

    def exportar_excel(self) -> None:
        self._grid.exportar_excel()

    def exportar_pdf(self) -> None:
        self._grid.exportar_pdf()

    def imprimir(self) -> None:
        self._grid.imprimir()

    @property
    def table(self):
        return self._grid.table

    @property
    def grid_interno(self):
        """Referencia al ComplexGrid interno (para configuración avanzada)."""
        return self._grid

    @property
    def _acciones(self) -> list:
        return self._grid._acciones

    @property
    def _filtros(self) -> list:
        return self._grid._filtros

    @property
    def _visibles(self) -> list:
        return self._grid._visibles
