"""Componente aprobado: creador/editor de etiquetas (estilo Windows Forms).

API pública
-----------
- ``EditorEtiquetaWidget`` (QWidget): editor completo de diseño de etiqueta.
  Conserva la toolbar general en la barra superior (acciones, tamaño del
  lienzo y nombre/lista de diseños). El lienzo ocupa el ancho restante y el
  lateral derecho usa secciones colapsables de acordeón (_PanelColapsable):
  ``Herramientas de campo`` (botones +Texto/+Dato/Duplicar/Quitar),
  ``Campos`` (tabla de campos del diseño) y ``Elemento seleccionado``
  (propiedades del campo activo); al expandir una se cierran las demás.
  Atributos relevantes:
    - ``modelo`` (EtiquetaModel): acceso a los diseños guardados en BD.
    - ``canvas`` (LabelCanvas): lienzo interactivo (arrastre y mangos).
    - ``panel`` (PanelPropiedadesCampo): propiedades del campo seleccionado.
    - ``tbl_campos`` (QTableWidget): listado de campos del diseño.
    - ``sp_ancho`` / ``sp_alto`` (QDoubleSpinBox): tamaño de lienzo en mm.
    - ``txt_nombre`` (QLineEdit): nombre del diseño para guardar en BD.
    - ``cmb_disenos`` (QComboBox): diseños guardados en la base de datos.
  Métodos de acción: ``_nuevo()``, ``_aplicar_tamano()``, ``_guardar_en_bd()``,
  ``_cargar_de_bd()``, ``_eliminar_de_bd()``, ``_agregar_campo(tipo)``,
  ``_duplicar_campo()``, ``_quitar_campo()``.

- ``DialogoEditorEtiqueta`` (QDialog): diálogo que envuelve el widget y se
  abre a pantalla completa (``abrir_fullscreen()``) para que los datos se
  vean con tamaño adecuado; botón "Cerrar" para salir.

El diseño se guarda con nombre en la tabla ``etiqueta_config`` (claves
``diseno:<nombre>``) para no generar archivos sueltos en disco.
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDialog, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget,
)

from src.components.editor_etiqueta import (
    DialogoPropiedadesCampo, LabelCanvas, PanelPropiedadesCampo,
    normalizar_campo, normalizar_diseno, texto_campo,
)
from src.models.etiqueta_model import DEFAULT_DISENO, EtiquetaModel
from src.utils.icons import mono_icon

# ---------------------------------------------------------------- paleta ---
TEAL_CLARO = "#7EBCB1"
TEAL_OSCURO = "#07756A"
CIAN_CLARO = "#B2DFDB"
GRIS_TOOLBAR = "#E4E9ED"
GRIS_BORDE = "#A9A9A9"
GRIS_LINEA = "#D6D6D6"
TEXTO_OSCURO = "#111111"
ROJO = "#C93744"
ROJO_OSCURO = "#A32D3A"
AZUL_ACCION = "#1892D4"
PURPURA = "#77307E"
TEAL_ICONO = "#22A8C6"

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
QLineEdit#ctlInput, QComboBox#ctlInput, QDoubleSpinBox#ctlInput {{
    background: #ffffff;
    border: 1px solid {GRIS_BORDE};
    border-radius: 3px;
    color: {TEXTO_OSCURO};
    padding: 4px 6px;
    selection-background-color: {TEAL_OSCURO};
    selection-color: #ffffff;
    min-height: 20px;
}}
QLineEdit#ctlInput:focus, QComboBox#ctlInput:focus, QDoubleSpinBox#ctlInput:focus {{
    border: 1px solid {TEAL_OSCURO};
}}
QLineEdit#ctlInput:disabled, QComboBox#ctlInput:disabled,
QDoubleSpinBox#ctlInput:disabled {{
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
QDoubleSpinBox#ctlInput::up-button, QDoubleSpinBox#ctlInput::down-button {{
    border: none;
    background: #EDEFF1;
    width: 18px;
}}
QDoubleSpinBox#ctlInput::up-arrow, QDoubleSpinBox#ctlInput::down-arrow {{
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
}}
QDoubleSpinBox#ctlInput::up-arrow {{
    border-bottom: 5px solid #555555; margin-top: 4px;
}}
QDoubleSpinBox#ctlInput::down-arrow {{
    border-top: 5px solid #555555; margin-bottom: 4px;
}}
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
QFrame#ctlColapsable {{
    background: #F4F6F7;
    border: 1px solid #9AA5AE;
    border-radius: 4px;
}}
QPushButton#ctlColapsableHeader {{
    background: #E4ECEF;
    border: none;
    border-bottom: 1px solid #9AA5AE;
    border-radius: 4px 4px 0 0;
    color: #1F2937;
    font-weight: 700;
    font-size: 12px;
    padding: 7px 10px;
    text-align: left;
}}
QPushButton#ctlColapsableHeader:hover {{ background: #D6E6E9; }}
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

_DATOS_MUESTRA = {
    "modelo": "9201", "corte": "PIEL CRAZY", "color": "CAF",
    "talla": "12.0", "folio_prog": "873", "cliente": "LORENZO RUBIO",
    "pares": 12, "fecha_prog": "2026-08-05",
}


class _PanelColapsable(QFrame):
    """Sección lateral plegable: encabezado con título + cuerpo colapsable.

    Al pulsar el encabezado se pliega/despliega el contenido para que el
    lienzo aproveche el espacio horizontal cuando no se usa un panel. Si se
    entrega ``on_alternar``, se invoca al expandir (acordeón: el propietario
    pliega las demás secciones).
    """

    def __init__(self, titulo: str, contenido: QWidget,
                 expandido: bool = True,
                 on_alternar=None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ctlColapsable")
        self._titulo = titulo
        self._expandido = expandido
        self._on_alternar = on_alternar

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.btn_cabecera = QPushButton()
        self.btn_cabecera.setObjectName("ctlColapsableHeader")
        self.btn_cabecera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cabecera.clicked.connect(self._alternar)
        self._actualizar_texto()
        lay.addWidget(self.btn_cabecera)

        self._cuerpo = QWidget()
        cuerpo_lay = QVBoxLayout(self._cuerpo)
        cuerpo_lay.setContentsMargins(0, 0, 0, 0)
        cuerpo_lay.addWidget(contenido)
        lay.addWidget(self._cuerpo)
        self._cuerpo.setVisible(expandido)

    def _actualizar_texto(self) -> None:
        flecha = "▼" if self._expandido else "▶"
        self.btn_cabecera.setText(f"{flecha} {self._titulo}")

    def plegar(self) -> None:
        if not self._expandido:
            return
        self._expandido = False
        self._cuerpo.setVisible(False)
        self._actualizar_texto()

    def _alternar(self) -> None:
        self._expandido = not self._expandido
        self._cuerpo.setVisible(self._expandido)
        self._actualizar_texto()
        if self._expandido and self._on_alternar is not None:
            self._on_alternar(self)


class EditorEtiquetaWidget(QWidget):
    """Creador/editor de etiquetas estilo Windows Forms (componente aprobado)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.modelo = EtiquetaModel()
        self._diseno = normalizar_diseno(self.modelo.cargar_diseno())
        self._idx = -1
        self._cargando = False
        self.setMinimumHeight(560)
        self.setStyleSheet(_QSS)
        self._setup_ui()
        self._recargar_lista_disenos()
        self._refrescar()

    # ------------------------------------------------------------- interfaz
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(self._crear_toolbar())

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)
        cuerpo.addWidget(self._crear_panel_lienzo(), 1)
        cuerpo.addWidget(self._crear_panel_lateral())
        root.addLayout(cuerpo, 1)

        root.addWidget(self._crear_barra_estado())

    def _tool_btn(self, texto: str, icono: QIcon, fn) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("ctlTool")
        btn.setText(texto)
        btn.setIcon(icono)
        btn.setIconSize(QSize(26, 26))
        btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        btn.setFixedSize(92, 52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda _=False: fn())
        return btn

    def _crear_label(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setObjectName("ctlLabel")
        return lbl

    def _crear_toolbar(self) -> QFrame:
        """Barra superior con acciones generales (no colapsable)."""
        bar = QFrame()
        bar.setObjectName("ctlToolbar")
        bar.setFixedHeight(72)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        lay.addWidget(self._tool_btn(
            "Nuevo", mono_icon("mas", 26, TEAL_OSCURO), self._nuevo))
        lay.addWidget(self._tool_btn(
            "Guardar en BD", mono_icon("exportar", 26, AZUL_ACCION),
            self._guardar_en_bd))
        lay.addWidget(self._tool_btn(
            "Cargar", mono_icon("ver", 26, PURPURA), self._cargar_de_bd))
        lay.addWidget(self._tool_btn(
            "Eliminar", mono_icon("eliminar", 26, ROJO), self._eliminar_de_bd))

        lay.addStretch()

        lay.addWidget(self._crear_label("Lienzo:"))
        self.sp_ancho = QDoubleSpinBox()
        self.sp_ancho.setObjectName("ctlInput")
        self.sp_ancho.setRange(10, 300)
        self.sp_ancho.setDecimals(1)
        self.sp_ancho.setSuffix(" mm")
        self.sp_ancho.setFixedWidth(86)
        lay.addWidget(self.sp_ancho)
        self.sp_alto = QDoubleSpinBox()
        self.sp_alto.setObjectName("ctlInput")
        self.sp_alto.setRange(10, 200)
        self.sp_alto.setDecimals(1)
        self.sp_alto.setSuffix(" mm")
        self.sp_alto.setFixedWidth(86)
        lay.addWidget(self.sp_alto)

        lay.addSpacing(10)
        lay.addWidget(self._crear_label("Diseño:"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setObjectName("ctlInput")
        self.txt_nombre.setPlaceholderText("Nombre del diseño…")
        self.txt_nombre.setFixedWidth(170)
        lay.addWidget(self.txt_nombre)
        self.cmb_disenos = QComboBox()
        self.cmb_disenos.setObjectName("ctlInput")
        self.cmb_disenos.setFixedWidth(150)
        lay.addWidget(self.cmb_disenos)
        return bar

    def _crear_panel_lienzo(self) -> QGroupBox:
        panel = QGroupBox("Lienzo — arrastre para mover, mangos para redimensionar")
        v = QVBoxLayout(panel)
        self.canvas = LabelCanvas()
        self.canvas.campoSeleccionado.connect(self._on_campo_seleccionado)
        self.canvas.campoArrastrado.connect(self._on_campo_geometria)
        self.canvas.campoRedimensionado.connect(self._on_campo_geometria)
        self.canvas.campoDobleClic.connect(self._editar_campo_dialog)
        v.addWidget(self.canvas, 1)
        return panel

    def _crear_panel_toolbar_campos(self) -> QWidget:
        """Sección colapsable con los botones de edición de campos."""
        contenido = QWidget()
        v = QVBoxLayout(contenido)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(8)

        btn_texto = QPushButton("+ Texto")
        btn_texto.setObjectName("ctlBtnGray")
        btn_texto.clicked.connect(lambda: self._agregar_campo("texto"))
        btn_dato = QPushButton("+ Dato")
        btn_dato.setObjectName("ctlBtnGray")
        btn_dato.clicked.connect(lambda: self._agregar_campo("dato"))
        btn_duplicar = QPushButton("Duplicar")
        btn_duplicar.setObjectName("ctlBtnGray")
        btn_duplicar.clicked.connect(self._duplicar_campo)
        btn_quitar = QPushButton("Quitar")
        btn_quitar.setObjectName("ctlBtnDanger")
        btn_quitar.clicked.connect(self._quitar_campo)
        grid_btns = QGridLayout()
        grid_btns.setHorizontalSpacing(6)
        grid_btns.setVerticalSpacing(6)
        grid_btns.addWidget(btn_texto, 0, 0)
        grid_btns.addWidget(btn_dato, 0, 1)
        grid_btns.addWidget(btn_duplicar, 1, 0)
        grid_btns.addWidget(btn_quitar, 1, 1)
        v.addLayout(grid_btns)

        return _PanelColapsable("Herramientas de campo", contenido,
                                on_alternar=self._on_alternar_colapsable)

    def _crear_panel_campos(self) -> QWidget:
        """Sección colapsable: lista de campos que componen el diseño."""
        contenido = QWidget()
        v = QVBoxLayout(contenido)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(8)

        self.tbl_campos = QTableWidget(0, 6)
        self.tbl_campos.setObjectName("ctlTable")
        self.tbl_campos.setHorizontalHeaderLabels(
            ["Tipo", "Contenido", "X", "Y", "Ancho", "Alto"])
        self.tbl_campos.verticalHeader().setVisible(False)
        self.tbl_campos.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_campos.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_campos.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_campos.setMaximumHeight(190)
        self.tbl_campos.itemSelectionChanged.connect(self._on_tabla_seleccion)
        v.addWidget(self.tbl_campos)

        return _PanelColapsable("Campos", contenido,
                                on_alternar=self._on_alternar_colapsable)

    def _crear_panel_elemento(self) -> QWidget:
        """Sección colapsable: propiedades del elemento seleccionado."""
        self.panel = PanelPropiedadesCampo()
        self.panel.campoCambiado.connect(self._on_panel_cambio)
        contenido = QWidget()
        v = QVBoxLayout(contenido)
        v.setContentsMargins(10, 8, 10, 8)
        v.setSpacing(0)
        v.addWidget(self.panel)
        return _PanelColapsable("Elemento seleccionado", contenido,
                                on_alternar=self._on_alternar_colapsable,
                                expandido=False)

    def _crear_panel_lateral(self) -> QWidget:
        """Columna lateral derecha con secciones colapsables en acordeón."""
        panel = QWidget()
        panel.setFixedWidth(360)
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(8)
        self._colapsables = [
            self._crear_panel_toolbar_campos(),
            self._crear_panel_campos(),
            self._crear_panel_elemento(),
        ]
        for c in self._colapsables:
            v.addWidget(c)
        v.addStretch()
        return panel

    def _on_alternar_colapsable(self, activo: _PanelColapsable) -> None:
        """Acordeón: al expandir una sección se pliegan las demás."""
        for c in self._colapsables:
            if c is not activo:
                c.plegar()

    def _crear_barra_estado(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("ctlStatus")
        bar.setFixedHeight(30)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self.lbl_tamano = QLabel()
        self.lbl_tamano.setObjectName("ctlStatusLabel")
        self.lbl_campos = QLabel()
        self.lbl_campos.setObjectName("ctlStatusLabel")
        self.lbl_mensaje = QLabel("Listo")
        self.lbl_mensaje.setObjectName("ctlStatusLabel")

        for lbl in (self.lbl_tamano, self.lbl_campos):
            lay.addWidget(lbl)
            sep = QFrame()
            sep.setObjectName("ctlSep")
            sep.setFixedSize(1, 16)
            lay.addWidget(sep)
        lay.addStretch()
        lay.addWidget(self.lbl_mensaje)
        return bar

    # ------------------------------------------------------------- acciones
    def _nuevo(self) -> None:
        self._diseno = normalizar_diseno(dict(DEFAULT_DISENO))
        self._idx = -1
        self.txt_nombre.clear()
        self._refrescar()
        self.lbl_mensaje.setText("Nuevo diseño — aún sin guardar en BD")

    def _ancho(self) -> float:
        return float(self._diseno.get("ancho_mm", 76.0))

    def _aplicar_tamano(self) -> None:
        ancho = float(self.sp_ancho.value())
        alto = float(self.sp_alto.value())
        self._diseno = normalizar_diseno(self._diseno, ancho, alto)
        self._refrescar()
        self.lbl_mensaje.setText(
            f"Tamaño de lienzo: {ancho:g} × {alto:g} mm")

    def _guardar_en_bd(self) -> None:
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.information(self, "Guardar diseño",
                                    "Indique un nombre para el diseño.")
            return
        self.modelo.guardar_diseno_nombre(nombre, self._diseno)
        self._recargar_lista_disenos(nombre)
        self.lbl_mensaje.setText(
            f"Diseño '{nombre}' guardado en la base de datos")

    def _cargar_de_bd(self) -> None:
        nombre = self.cmb_disenos.currentData()
        if not nombre:
            QMessageBox.information(self, "Cargar diseño",
                                    "Seleccione un diseño guardado.")
            return
        diseno = self.modelo.cargar_diseno_nombre(nombre)
        if not diseno:
            return
        self._diseno = normalizar_diseno(diseno)
        self.txt_nombre.setText(nombre)
        self._idx = -1
        self._refrescar()
        self.lbl_mensaje.setText(f"Diseño '{nombre}' cargado desde la BD")

    def _eliminar_de_bd(self) -> None:
        nombre = self.cmb_disenos.currentData()
        if not nombre:
            QMessageBox.information(self, "Eliminar diseño",
                                    "Seleccione un diseño guardado.")
            return
        if QMessageBox.question(
                self, "Eliminar diseño",
                f"¿Eliminar el diseño '{nombre}' de la base de datos?") \
                != QMessageBox.StandardButton.Yes:
            return
        self.modelo.eliminar_diseno(nombre)
        self._recargar_lista_disenos()
        self.lbl_mensaje.setText(f"Diseño '{nombre}' eliminado de la BD")

    def _recargar_lista_disenos(self, seleccionar: str = "") -> None:
        actual = seleccionar or self.cmb_disenos.currentData()
        self.cmb_disenos.blockSignals(True)
        self.cmb_disenos.clear()
        for d in self.modelo.listar_disenos():
            nombre = d["clave"].split(":", 1)[-1]
            self.cmb_disenos.addItem(nombre, nombre)
        if actual:
            i = self.cmb_disenos.findData(actual)
            self.cmb_disenos.setCurrentIndex(i if i >= 0 else -1)
        self.cmb_disenos.blockSignals(False)

    # ---- Campos del diseño ----

    def _agregar_campo(self, tipo: str) -> None:
        ancho = self._ancho()
        campos = self._diseno.get("campos", [])
        y = 8.0
        if campos:
            ultimo = campos[-1]
            y = round(float(ultimo.get("y_mm", 0))
                      + float(ultimo.get("alto_mm", 7)) + 2, 1)
        campo = normalizar_campo(
            {"tipo": tipo, "x_mm": 7.0, "y_mm": y,
             "ancho_mm": max(20.0, ancho - 14), "alto_mm": 7.0,
             "texto": "Texto nuevo", "size": 12, "label_size": 12},
            ancho)
        if tipo == "dato":
            campo["dato"] = "modelo"
            campo["label"] = "MODELO:"
            campo["texto"] = ""
        campos.append(campo)
        self._idx = len(campos) - 1
        self._refrescar()
        self.lbl_mensaje.setText(
            f"Campo {'dato' if tipo == 'dato' else 'texto'} agregado")

    def _duplicar_campo(self) -> None:
        campos = self._diseno.get("campos", [])
        if not (0 <= self._idx < len(campos)):
            return
        import copy
        nuevo = copy.deepcopy(campos[self._idx])
        nuevo["y_mm"] = round(float(nuevo.get("y_mm", 0))
                              + float(nuevo.get("alto_mm", 7)) + 2, 1)
        campos.insert(self._idx + 1, nuevo)
        self._idx += 1
        self._refrescar()

    def _quitar_campo(self) -> None:
        campos = self._diseno.get("campos", [])
        if not (0 <= self._idx < len(campos)):
            return
        campos.pop(self._idx)
        self._idx = min(self._idx, len(campos) - 1)
        self._refrescar()
        self.lbl_mensaje.setText("Campo quitado")

    def _editar_campo_dialog(self, idx: int) -> None:
        campos = self._diseno.get("campos", [])
        if not (0 <= idx < len(campos)):
            return
        dlg = DialogoPropiedadesCampo(campos[idx], self._ancho(), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            campos[idx] = dlg.campo_resultado()
            self._idx = idx
            self._refrescar()

    # ---- Conexiones de señales ----

    def _on_campo_seleccionado(self, idx: int) -> None:
        self._idx = idx
        campos = self._diseno.get("campos", [])
        if 0 <= idx < len(campos):
            self.panel.cargar_campo(idx, campos[idx], self._ancho())
            self.tbl_campos.selectRow(idx)

    def _on_campo_geometria(self, idx: int, *_args) -> None:
        self._idx = idx
        campos = self._diseno.get("campos", [])
        if 0 <= idx < len(campos):
            self.panel.cargar_campo(idx, campos[idx], self._ancho())
            self._pintar_fila(idx, campos[idx])

    def _on_tabla_seleccion(self) -> None:
        fila = self.tbl_campos.currentRow()
        if fila >= 0 and fila != self._idx:
            self._on_campo_seleccionado(fila)

    def _on_panel_cambio(self) -> None:
        if self._cargando or self._idx < 0:
            return
        campos = self._diseno.get("campos", [])
        if not (0 <= self._idx < len(campos)):
            return
        campos[self._idx] = self.panel.leer_campo(self._ancho())
        self._pintar_fila(self._idx, campos[self._idx])
        self.canvas.set_contenido(self._diseno, _DATOS_MUESTRA)

    # ---- Refresco de la vista ----

    def _pintar_fila(self, fila: int, c: dict) -> None:
        tipo = "Dato" if c.get("tipo") == "dato" else "Texto"
        contenido = texto_campo(c)
        for col, valor in ((0, tipo), (1, contenido),
                           (2, f"{float(c.get('x_mm', 0)):g}"),
                           (3, f"{float(c.get('y_mm', 0)):g}"),
                           (4, f"{float(c.get('ancho_mm', 0)):g}"),
                           (5, f"{float(c.get('alto_mm', 0)):g}")):
            item = QTableWidgetItem(valor)
            if col in (2, 3, 4, 5):
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tbl_campos.setItem(fila, col, item)

    def _refrescar(self) -> None:
        self._cargando = True
        try:
            self.sp_ancho.setValue(float(self._diseno.get("ancho_mm", 76.0)))
            self.sp_alto.setValue(float(self._diseno.get("alto_mm", 51.0)))
            campos = self._diseno.get("campos", [])
            self.tbl_campos.setRowCount(len(campos))
            for i, c in enumerate(campos):
                self._pintar_fila(i, c)
            if 0 <= self._idx < len(campos):
                self.panel.cargar_campo(self._idx, campos[self._idx],
                                        self._ancho())
            else:
                self.panel.cargar_campo(-1, None, self._ancho())
            self.canvas.set_contenido(self._diseno, _DATOS_MUESTRA)
            self.lbl_tamano.setText(
                f"{float(self._diseno.get('ancho_mm', 76)):g} × "
                f"{float(self._diseno.get('alto_mm', 51)):g} mm")
            self.lbl_campos.setText(f"{len(campos)} campos")
        finally:
            self._cargando = False


class DialogoEditorEtiqueta(QDialog):
    """Diálogo a pantalla completa con el editor de etiquetas (aprobado).

    Uso:
        dlg = DialogoEditorEtiqueta(parent)
        dlg.abrir_fullscreen()   # muestra maximizado y espera cierre
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Crear / Editar Etiqueta")
        self.editor = EditorEtiquetaWidget(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self.editor, 1)

        barra = QFrame()
        barra.setObjectName("ctlStatus")
        barra.setFixedHeight(44)
        lay = QHBoxLayout(barra)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.addStretch()
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setObjectName("btnPrimary")
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.clicked.connect(self.accept)
        lay.addWidget(self.btn_cerrar)
        root.addWidget(barra)

    def abrir_fullscreen(self) -> int:
        """Muestra el diálogo maximizado (pantalla completa) y espera cierre."""
        self.showMaximized()
        return self.exec()
