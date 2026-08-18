"""Sandbox: catálogo completo de controles y componentes del sistema.

Muestra en un solo lugar TODOS los widgets y componentes disponibles para
usar en las ventanas de la aplicación:

    - Widgets Qt estilizados por `src/utils/styles.qss` (entradas, combos,
      botones, marcas, tablas, tabs, etc.).
    - Componentes aprobados del catálogo en vivo (DatePicker,
      CampoHistorico, MatrizTallasWidget, OdooListView, SearchableComboBox).
    - Utilidades de UI (crear_boton, crear_tarjeta, crear_seccion,
      crear_header, configurar_tabla_excel).
    - Galería de iconos (tile_icon y mono_icon).

Es una demo (prototipo del Sandbox): los componentes aprobados viven en
`src/components/`; aquí solo se exponen para verlos y decidir su uso.
"""

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QRadioButton, QScrollArea, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QToolButton, QVBoxLayout,
    QWidget,
)

from src.components.campo_historico import CampoHistorico
from src.components.date_picker import DatePicker
from src.components.tallas_matrix import MatrizTallasWidget
from src.utils.icons import _GLIFOS, _TILES, mono_icon, tile_icon
from src.utils.odoo_list import OdooListView
from src.utils.table_utils import NumericItem, configurar_tabla_excel
from src.utils.ui_helpers import (
    SearchableComboBox, crear_boton, crear_header, crear_seccion, crear_tarjeta,
)

_DATOS_ODEO = [
    {"lote": "L-1001", "estilo": "Bota Vaquera", "linea": "Línea 1", "pares": 240},
    {"lote": "L-1002", "estilo": "Botín Clásico", "linea": "Línea 2", "pares": 180},
    {"lote": "L-1003", "estilo": "Tenis Urbano", "linea": "Línea 3", "pares": 320},
    {"lote": "L-1004", "estilo": "Mocasín Ejecutivo", "linea": "Línea 1", "pares": 96},
    {"lote": "L-1005", "estilo": "Huarache Tradicional", "linea": "Línea 4", "pares": 260},
]

_TALLAS_DEMO = [
    {"id": 1, "talla": "00"}, {"id": 2, "talla": "0"}, {"id": 3, "talla": "1"},
    {"id": 4, "talla": "1.5"}, {"id": 5, "talla": "2"}, {"id": 6, "talla": "2.5"},
    {"id": 7, "talla": "3"}, {"id": 8, "talla": "3.5"}, {"id": 9, "talla": "4"},
    {"id": 10, "talla": "4.5"}, {"id": 11, "talla": "5"}, {"id": 12, "talla": "5.5"},
]

_COLORES_ICONOS = ["#4f46e5", "#0d9488", "#ea580c", "#e11d48",
                   "#2563eb", "#7c3aed", "#0891b2", "#16a34a"]


def _etiqueta(seccion: QGroupBox, texto: str) -> None:
    lbl = QLabel(texto)
    lbl.setObjectName("sectionSubtitle")
    seccion.layout().addWidget(lbl)


class CatalogoControles(QWidget):
    """Galería interactiva de todos los controles disponibles del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        encabezado = crear_header("Catálogo de controles")
        layout.addWidget(encabezado)

        intro = QLabel(
            "Todos los widgets y componentes disponibles para construir "
            "ventanas: Qt estilizados, componentes aprobados del catálogo, "
            "utilidades e iconos.")
        intro.setObjectName("sectionSubtitle")
        intro.setContentsMargins(24, 8, 24, 4)
        intro.setWordWrap(True)
        layout.addWidget(intro)

        area = QScrollArea()
        area.setWidgetResizable(True)
        contenido = QWidget()
        cont_lay = QVBoxLayout(contenido)
        cont_lay.setContentsMargins(24, 12, 24, 24)
        cont_lay.setSpacing(16)

        cont_lay.addWidget(self._seccion_entradas())
        cont_lay.addWidget(self._seccion_seleccion())
        cont_lay.addWidget(self._seccion_botones())
        cont_lay.addWidget(self._seccion_marcas())
        cont_lay.addWidget(self._seccion_contenedores())
        cont_lay.addWidget(self._seccion_listas())
        cont_lay.addWidget(self._seccion_componentes())
        cont_lay.addWidget(self._seccion_iconos())
        cont_lay.addStretch()

        area.setWidget(contenido)
        layout.addWidget(area, 1)

    # ------------------------------------------------------------ secciones
    def _seccion_entradas(self) -> QGroupBox:
        grupo = QGroupBox("Entradas de texto")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(8)
        _etiqueta(grupo, "QLineEdit y QTextEdit con el estilo global del sistema.")

        fila1 = QHBoxLayout()
        fila1.addWidget(QLabel("Normal:"))
        edit_normal = QLineEdit()
        edit_normal.setPlaceholderText("Texto libre")
        edit_normal.setClearButtonEnabled(True)
        fila1.addWidget(edit_normal, 1)

        fila1.addWidget(QLabel("Contraseña:"))
        edit_pass = QLineEdit()
        edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        edit_pass.setPlaceholderText("••••••")
        fila1.addWidget(edit_pass, 1)
        lay.addLayout(fila1)

        fila2 = QHBoxLayout()
        fila2.addWidget(QLabel("Solo lectura:"))
        edit_ro = QLineEdit("Valor de solo lectura")
        edit_ro.setReadOnly(True)
        fila2.addWidget(edit_ro, 1)

        fila2.addWidget(QLabel("Deshabilitado:"))
        edit_dis = QLineEdit("Deshabilitado")
        edit_dis.setEnabled(False)
        fila2.addWidget(edit_dis, 1)
        lay.addLayout(fila2)

        fila3 = QHBoxLayout()
        fila3.addWidget(QLabel("CampoHistórico:"))
        campo_h = CampoHistorico()
        campo_h.setPlaceholderText("Escriba y salga para guardar histórico")
        fila3.addWidget(campo_h, 1)
        lay.addLayout(fila3)

        lay.addWidget(QLabel("QTextEdit:"))
        txt = QTextEdit()
        txt.setPlainText("Texto multilínea con el estilo de entrada del sistema.")
        txt.setFixedHeight(70)
        lay.addWidget(txt)
        return grupo

    def _seccion_seleccion(self) -> QGroupBox:
        grupo = QGroupBox("Selección y numéricos")
        lay = QGridLayout(grupo)
        lay.setSpacing(8)

        cmb = QComboBox()
        cmb.addItems(["Opción A", "Opción B", "Opción C"])
        lay.addWidget(QLabel("QComboBox:"), 0, 0)
        lay.addWidget(cmb, 0, 1)

        cmb_editable = QComboBox()
        cmb_editable.setEditable(True)
        cmb_editable.addItems(["Buscar…", "Opción 1", "Opción 2"])
        lay.addWidget(QLabel("Combo editable:"), 0, 2)
        lay.addWidget(cmb_editable, 0, 3)

        buscable = SearchableComboBox()
        buscable.set_items(["Café", "Negro", "Blanco", "Beige", "Azul Marino"])
        lay.addWidget(QLabel("Con búsqueda:"), 1, 0)
        lay.addWidget(buscable, 1, 1)

        spn = QSpinBox()
        spn.setRange(0, 9999)
        spn.setValue(120)
        lay.addWidget(QLabel("QSpinBox:"), 1, 2)
        lay.addWidget(spn, 1, 3)

        dspn = QDoubleSpinBox()
        dspn.setRange(0, 99999)
        dspn.setDecimals(2)
        dspn.setValue(99.90)
        lay.addWidget(QLabel("QDoubleSpinBox:"), 2, 0)
        lay.addWidget(dspn, 2, 1)

        dte = QDateEdit()
        dte.setCalendarPopup(True)
        dte.setDisplayFormat("dd/MM/yyyy")
        dte.setDate(QDate.currentDate())
        lay.addWidget(QLabel("QDateEdit:"), 2, 2)
        lay.addWidget(dte, 2, 3)

        picker = DatePicker()
        lay.addWidget(QLabel("DatePicker:"), 3, 0)
        lay.addWidget(picker, 3, 1)
        return grupo

    def _seccion_botones(self) -> QGroupBox:
        grupo = QGroupBox("Botones")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(10)
        _etiqueta(grupo, "Variantes de QPushButton definidas en styles.qss.")

        fila1 = QHBoxLayout()
        fila1.setSpacing(10)
        fila1.addWidget(crear_boton("Guardar", "btnPrimary"))
        fila1.addWidget(crear_boton("Cancelar", "btnSecondary"))
        fila1.addWidget(crear_boton("Aceptar", "btnSuccess"))
        fila1.addWidget(crear_boton("Eliminar", "btnDanger"))
        fila1.addWidget(crear_boton("Advertir", "btnWarning"))
        fila1.addStretch()
        lay.addLayout(fila1)

        fila2 = QHBoxLayout()
        fila2.setSpacing(10)
        fila2.addWidget(QLabel("btnModo / viewSwitch:"))
        for texto in ("Lista", "Tabla", "Iconos"):
            b = QPushButton(texto)
            b.setObjectName("viewSwitch")
            b.setCheckable(True)
            fila2.addWidget(b)
        fila2.addStretch()
        lay.addLayout(fila2)

        fila3 = QHBoxLayout()
        fila3.setSpacing(10)
        fila3.addWidget(QLabel("btnRowEdit / btnRowDel (iconos de fila):"))
        for nombre in ("btnRowEdit", "btnRowDel"):
            b = QToolButton()
            b.setObjectName(nombre)
            b.setIcon(mono_icon(
                "editar" if nombre == "btnRowEdit" else "eliminar", 18,
                "#1E4A8F" if nombre == "btnRowEdit" else "#A93A3A"))
            b.setIconSize(b.iconSize())
            b.setToolTip("Editar" if nombre == "btnRowEdit" else "Eliminar")
            b.setCursor(Qt.PointingHandCursor)
            fila3.addWidget(b)
        fila3.addStretch()
        lay.addLayout(fila3)

        fila4 = QHBoxLayout()
        fila4.setSpacing(10)
        fila4.addWidget(QLabel("navTool (barra de navegación):"))
        for texto in ("Órdenes", "Producción", "Stock"):
            b = QToolButton()
            b.setObjectName("navTool")
            b.setText(texto)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            fila4.addWidget(b)
        fila4.addStretch()
        lay.addLayout(fila4)
        return grupo

    def _seccion_marcas(self) -> QGroupBox:
        grupo = QGroupBox("Marcas (QCheckBox y QRadioButton)")
        lay = QHBoxLayout(grupo)
        lay.setSpacing(24)

        chk_lay = QVBoxLayout()
        chk1 = QCheckBox("Marcar todas")
        chk2 = QCheckBox("Incluir suelas")
        chk2.setChecked(True)
        chk3 = QCheckBox("Deshabilitado")
        chk3.setEnabled(False)
        chk_lay.addWidget(chk1)
        chk_lay.addWidget(chk2)
        chk_lay.addWidget(chk3)
        lay.addLayout(chk_lay)

        rad_lay = QVBoxLayout()
        for texto in ("Línea 1", "Línea 2", "Línea 3"):
            rad = QRadioButton(texto)
            if texto == "Línea 1":
                rad.setChecked(True)
            rad_lay.addWidget(rad)
        lay.addLayout(rad_lay)
        lay.addStretch()
        return grupo

    def _seccion_contenedores(self) -> QGroupBox:
        grupo = QGroupBox("Contenedores y agrupación")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(10)
        _etiqueta(grupo, "QGroupBox, QTabWidget, tarjetas (crear_tarjeta) "
                         "y secciones (crear_seccion).")

        tarjetas = QHBoxLayout()
        tarjetas.setSpacing(10)
        tarjetas.addWidget(crear_tarjeta("Órdenes activas", "12", "#2A5FB0"))
        tarjetas.addWidget(crear_tarjeta("Pares producidos", "1 240", "#3D9141"))
        tarjetas.addWidget(crear_tarjeta("Insumos bajos", "4", "#A93A3A"))
        lay.addLayout(tarjetas)

        tabs = QTabWidget()
        for nombre, texto in (("Datos", "Contenido de la pestaña Datos."),
                              ("Histórico", "Contenido de la pestaña Histórico.")):
            pag = QWidget()
            pag_lay = QVBoxLayout(pag)
            pag_lay.addWidget(QLabel(texto))
            tabs.addTab(pag, nombre)
        lay.addWidget(tabs)
        return grupo

    def _seccion_listas(self) -> QGroupBox:
        grupo = QGroupBox("Tablas y listados")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(10)
        _etiqueta(grupo, "QTableWidget (configurar_tabla_excel + NumericItem), "
                         "QListWidget y OdooListView.")

        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["Lote", "Estilo", "Línea", "Pares"])
        configurar_tabla_excel(tabla)
        for i, r in enumerate(_DATOS_ODEO):
            tabla.insertRow(tabla.rowCount())
            for col, clave in enumerate(("lote", "estilo", "linea", "pares")):
                valor = r[clave]
                item = (NumericItem(valor) if clave == "pares"
                        else QTableWidgetItem(str(valor)))
                tabla.setItem(i, col, item)
        tabla.setFixedHeight(140)
        lay.addWidget(tabla)

        lista = QListWidget()
        for r in _DATOS_ODEO[:3]:
            QListWidgetItem(f"{r['lote']} — {r['estilo']} ({r['pares']} pares)", lista)
        lista.setFixedHeight(88)
        lay.addWidget(lista)

        vista = OdooListView(["Lote", "Estilo", "Línea", "Pares"])
        vista.set_renderers(
            fila=lambda r: [r["lote"], r["estilo"], r["linea"], str(r["pares"])],
            claves=lambda r: [r["lote"], r["estilo"], r["linea"], float(r["pares"])],
            tarjeta=lambda r: {
                "tile": "oc", "titulo": r["lote"], "subtitulo": r["estilo"],
                "badge": f"{r['pares']} pares"},
        )
        vista.set_datos(_DATOS_ODEO)
        vista.setFixedHeight(240)
        lay.addWidget(vista)
        return grupo

    def _seccion_componentes(self) -> QGroupBox:
        grupo = QGroupBox("Componentes aprobados del catálogo")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(10)
        _etiqueta(grupo, "Instancias en vivo de los componentes registrados "
                         "en src.components.")

        lay.addWidget(QLabel("MatrizTallasWidget:"))
        matriz = MatrizTallasWidget(puntos=_TALLAS_DEMO, titulo="TALLAS (demo)")
        lay.addWidget(matriz)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("DatePicker:"))
        fila.addWidget(DatePicker())
        fila.addWidget(QLabel("CampoHistórico:"))
        fila.addWidget(CampoHistorico(), 1)
        lay.addLayout(fila)
        return grupo

    def _seccion_iconos(self) -> QGroupBox:
        grupo = QGroupBox("Galería de iconos (tile_icon y mono_icon)")
        lay = QVBoxLayout(grupo)
        lay.setSpacing(8)
        _etiqueta(grupo, "tile_icon (módulos) y mono_icon (glifos de acción).")

        tiles = QHBoxLayout()
        tiles.setSpacing(10)
        for clave in sorted(_TILES):
            celda = QVBoxLayout()
            icono = QLabel()
            icono.setPixmap(tile_icon(clave, 34).pixmap(34, 34))
            icono.setAlignment(Qt.AlignCenter)
            nombre = QLabel(clave)
            nombre.setAlignment(Qt.AlignCenter)
            nombre.setStyleSheet("font-size: 10px; color: #444444;")
            celda.addWidget(icono)
            celda.addWidget(nombre)
            tiles.addLayout(celda)
        tiles.addStretch()
        lay.addLayout(tiles)

        glifos = QGridLayout()
        glifos.setSpacing(10)
        col = 0
        fila = 0
        for clave in sorted(_GLIFOS):
            color = _COLORES_ICONOS[fila % len(_COLORES_ICONOS)]
            caja = QVBoxLayout()
            icono = QLabel()
            icono.setPixmap(mono_icon(clave, 26, color).pixmap(26, 26))
            icono.setAlignment(Qt.AlignCenter)
            nombre = QLabel(clave)
            nombre.setAlignment(Qt.AlignCenter)
            nombre.setStyleSheet("font-size: 10px; color: #444444;")
            caja.addWidget(icono)
            caja.addWidget(nombre)
            glifos.addLayout(caja, fila, col)
            col += 1
            if col >= 6:
                col = 0
                fila += 1
        lay.addLayout(glifos)
        return grupo
