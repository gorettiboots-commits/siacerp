from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QDoubleSpinBox, QSpinBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.controllers.accesos_controller import AccesosController
from src.controllers.inventario_controller import InventarioController
from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.controllers.produccion_controller import ProduccionController
from src.models.accesos_model import ACCIONES, MODULOS, tiene
from src.utils.icons import tile_icon


_SECCIONES = [
    ("unidades", "Unidades de Medida",
     "Catálogo de unidades usadas en insumos y órdenes de compra."),
    ("areas", "Áreas de Producción",
     "Estaciones del taller por las que avanza la producción."),
    ("tallas", "Tallas de Variante",
     "Catálogo unificado de tallas/puntos, con generación en serie (corrida)."),
    ("colores", "Colores de Variante",
     "Colores y códigos cortos para variantes de insumo."),
    ("usuarios", "Usuarios y Accesos",
     "Usuarios del sistema y sus permisos por módulo."),
]


class _BotonSeccion(QPushButton):
    def sizeHint(self) -> QSize:
        hint = super().sizeHint()
        lay = self.layout()
        if lay is not None:
            hint = hint.expandedTo(lay.sizeHint())
        return hint


class _ConfigSidebar(QFrame):
    currentChanged = Signal(int)

    def __init__(self, secciones: list, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._botones: list[QPushButton] = []
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)

        for i, (key, nombre) in enumerate(secciones):
            btn = _BotonSeccion()
            btn.setObjectName("cfgSidebarItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            fila = QHBoxLayout(btn)
            fila.setContentsMargins(12, 10, 12, 10)
            fila.setSpacing(12)
            icono = QLabel()
            icono.setPixmap(tile_icon(key).pixmap(28, 28))
            fila.addWidget(icono)
            lbl = QLabel(nombre)
            lbl.setObjectName("cfgSidebarItemLabel")
            fila.addWidget(lbl)
            fila.addStretch()
            self._grupo.addButton(btn, i)
            layout.addWidget(btn)
            self._botones.append(btn)
            btn.installEventFilter(self)

        self._grupo.idClicked.connect(self._seleccionar)
        if self._botones:
            self._botones[0].setChecked(True)

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.KeyPress and obj in self._botones:
            if event.key() in (Qt.Key_Up, Qt.Key_Down):
                self._mover(-1 if event.key() == Qt.Key_Up else 1)
                return True
        return super().eventFilter(obj, event)

    def _mover(self, delta: int) -> None:
        actual = self._grupo.checkedId()
        actual = actual if actual >= 0 else 0
        self._seleccionar((actual + delta) % len(self._botones))

    def _seleccionar(self, index: int) -> None:
        self._botones[index].setChecked(True)
        self._botones[index].setFocus()
        self.currentChanged.emit(index)


class DialogConfiguracion(QDialog):
    def __init__(self, parent=None, permisos=None) -> None:
        super().__init__(parent)
        self.permisos = permisos or set()
        self.setObjectName("dlgConfiguracion")
        self.controller = OrdenesCompraController()
        self.prod_controller = ProduccionController()
        self.accesos_controller = AccesosController()
        self.inv_controller = InventarioController()
        self.setWindowTitle("Configuración")
        self.setMinimumSize(960, 620)
        self.resize(1020, 680)
        self.setModal(True)
        self._setup_ui()
        self._cargar()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        titulo = QLabel("Configuración")
        titulo.setObjectName("cfgDialogTitle")
        root.addWidget(titulo)

        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(0)

        secciones = list(_SECCIONES)
        if not tiene(self.permisos, "configuracion", "ver"):
            secciones = [s for s in secciones if s[0] != "unidades"
                         and s[0] != "areas" and s[0] != "tallas"
                         and s[0] != "colores"]
        if not tiene(self.permisos, "usuarios", "ver"):
            secciones = [s for s in secciones if s[0] != "usuarios"]
        self._secciones = secciones

        contenedor_side = QFrame()
        contenedor_side.setObjectName("cfgSidebar")
        contenedor_side.setFixedWidth(264)
        sb = QVBoxLayout(contenedor_side)
        sb.setContentsMargins(14, 6, 14, 12)
        sb.setSpacing(2)
        self.sidebar = _ConfigSidebar([(k, n) for k, n, _ in secciones], self)
        sb.addWidget(self.sidebar)
        sb.addStretch()

        self.stack = QStackedWidget()
        if secciones:
            for key, _, _ in secciones:
                self.stack.addWidget(self._crear_pagina(key))
        else:
            pag = QWidget()
            lay = QVBoxLayout(pag)
            msg = QLabel("No tiene permisos para ver ninguna sección de configuración.")
            msg.setAlignment(Qt.AlignCenter)
            lay.addWidget(msg)
            self.stack.addWidget(pag)

        contenedor = QFrame()
        contenedor.setObjectName("cfgContent")
        cl = QVBoxLayout(contenedor)
        cl.setContentsMargins(30, 18, 30, 18)
        cl.setSpacing(10)
        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setObjectName("cfgSectionTitle")
        self.lbl_subtitulo = QLabel("")
        self.lbl_subtitulo.setObjectName("cfgSectionSubtitle")
        divisor = QFrame()
        divisor.setObjectName("cfgDivider")
        divisor.setFixedHeight(1)
        cl.addWidget(self.lbl_titulo)
        cl.addWidget(self.lbl_subtitulo)
        cl.addWidget(divisor)
        cl.addWidget(self.stack, 1)

        cuerpo.addWidget(contenedor_side)
        cuerpo.addWidget(contenedor, 1)
        root.addLayout(cuerpo, 1)

        pie = QHBoxLayout()
        pie.setContentsMargins(16, 8, 16, 14)
        pie.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnPrimary")
        btn_cerrar.clicked.connect(self.accept)
        pie.addWidget(btn_cerrar)
        root.addLayout(pie)

        self.sidebar.currentChanged.connect(self._navegar)
        self._navegar(0)

    def _crear_pagina(self, key: str) -> QWidget:
        if key == "unidades":
            return _TabUnidades(self.controller, self.permisos)
        if key == "areas":
            return _TabEstaciones(self.prod_controller, self.permisos)
        if key == "tallas":
            return _TabTallas(self.inv_controller, self.permisos)
        if key == "colores":
            return _TabColores(self.inv_controller, self.permisos)
        if key == "usuarios":
            return _TabAccesos(self.accesos_controller, self.permisos)
        raise ValueError(f"Sección de configuración desconocida: {key}")

    def _navegar(self, index: int) -> None:
        if not self._secciones:
            return
        self.stack.setCurrentIndex(index)
        _, titulo, subtitulo = self._secciones[index]
        self.lbl_titulo.setText(titulo)
        self.lbl_subtitulo.setText(subtitulo)

    def _cargar(self) -> None:
        for i in range(self.stack.count()):
            pagina = self.stack.widget(i)
            recargar = getattr(pagina, "recargar", None)
            if callable(recargar):
                recargar()


class _TabUnidades(QWidget):
    def __init__(self, controller: OrdenesCompraController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.grid = ComplexGrid()
        self.grid.set_columnas([
            {"key": "nombre", "titulo": "Nombre", "ancho": 300},
            {"key": "abreviatura", "titulo": "Abreviatura", "ancho": 160},
        ])
        self.grid.set_renderers(estilo=self._estilo)
        self.grid.set_exportar_visible(
            tiene(self.permisos, "configuracion", "exportar"))
        self.grid.doubleClicked.connect(self._editar)
        layout.addWidget(self.grid)

        self.btn_add = QPushButton("+ Nueva Unidad")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self._crear)
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setObjectName("btnSecondary")
        self.btn_edit.clicked.connect(self._editar)
        self.btn_del = QPushButton("Desactivar")
        self.btn_del.setObjectName("btnDanger")
        self.btn_del.clicked.connect(self._desactivar)

        self.btn_add.setEnabled(tiene(self.permisos, "configuracion", "crear"))
        self.btn_edit.setEnabled(tiene(self.permisos, "configuracion", "editar"))
        self.btn_del.setEnabled(tiene(self.permisos, "configuracion", "eliminar"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)

    @staticmethod
    def _estilo(rec, item, col) -> None:
        if not rec.get("activo"):
            item.setForeground(Qt.gray)

    def recargar(self) -> None:
        unidades = self.controller.listar_unidades(solo_activos=False)
        self.grid.set_datos(unidades)

    def _crear(self) -> None:
        dlg = _DialogUnidad(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        rec = self.grid.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccione", "Seleccione una unidad de la lista.")
            return
        dlg = _DialogUnidad(self.controller, rec["id"])
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _desactivar(self) -> None:
        rec = self.grid.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccione", "Seleccione una unidad de la lista.")
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar la unidad '{rec['nombre']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.desactivar_unidad(rec["id"])
            self.recargar()


class _DialogUnidad(QDialog):
    def __init__(self, controller: OrdenesCompraController,
                 unidad_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.unidad_id = unidad_id
        self.setWindowTitle("Nueva Unidad" if unidad_id is None else "Editar Unidad")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()
        if unidad_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Decímetro Cuadrado")
        self.txt_abrev = QLineEdit()
        self.txt_abrev.setPlaceholderText("Ej: dm2")
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Abreviatura:", self.txt_abrev)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        for u in self.controller.listar_unidades(solo_activos=False):
            if u["id"] == self.unidad_id:
                self.txt_nombre.setText(u["nombre"])
                self.txt_abrev.setText(u["abreviatura"])
                break

    def _save(self) -> None:
        nombre = self.txt_nombre.text().strip()
        abrev = self.txt_abrev.text().strip()
        if not nombre or not abrev:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y abreviatura son obligatorios.")
            return
        try:
            if self.unidad_id:
                self.controller.actualizar_unidad(self.unidad_id, nombre, abrev)
            else:
                self.controller.crear_unidad(nombre, abrev)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _TabEstaciones(QWidget):
    def __init__(self, controller: ProduccionController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel(
            "Defina el orden en que las órdenes de producción avanzan por las áreas.\n"
            "La primera y la última área controlan el consumo de inventario y el alta de producto terminado."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.btn_add = QPushButton("+ Nueva Área")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(self._crear)
        self.btn_add.setEnabled(tiene(self.permisos, "configuracion", "crear"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_add)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.grid = ComplexGrid()
        self.grid.set_columnas([
            {"key": "orden", "titulo": "Orden", "ancho": 90, "tipo": "numero"},
            {"key": "nombre", "titulo": "Área", "ancho": 260},
            {"key": "descripcion", "titulo": "Descripción", "ancho": 320},
        ])
        self.grid.set_renderers(estilo=self._estilo)
        self.grid.set_acciones(self._acciones())
        self.grid.set_exportar_visible(
            tiene(self.permisos, "configuracion", "exportar"))
        self.grid.doubleClicked.connect(self._editar)
        layout.addWidget(self.grid)

    def _acciones(self) -> list:
        acciones = []
        if tiene(self.permisos, "configuracion", "editar"):
            acciones.append({"texto": "", "icono": "editar",
                             "color": "#4f46e5", "callback": self._editar})
        if tiene(self.permisos, "configuracion", "eliminar"):
            acciones.append({"texto": "", "icono": "eliminar",
                             "color": "#dc2626", "callback": self._eliminar})
        return acciones

    @staticmethod
    def _estilo(rec, item, col) -> None:
        if not rec.get("activo"):
            item.setForeground(Qt.gray)

    def recargar(self) -> None:
        estaciones = self.controller.listar_estaciones(solo_activos=False)
        self.grid.set_datos(estaciones)

    def _crear(self) -> None:
        dlg = _DialogEstacion(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self, rec: dict | None = None) -> None:
        if rec is None:
            rec = self.grid.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccione", "Seleccione un área de la lista.")
            return
        dlg = _DialogEstacion(self.controller, rec["id"])
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _eliminar(self, rec: dict | None = None) -> None:
        if rec is None:
            rec = self.grid.registro_seleccionado()
        if rec is None:
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Eliminar el área '{rec.get('nombre', '')}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        try:
            self.controller.eliminar_estacion(rec["id"])
        except Exception:
            QMessageBox.warning(
                self, "No se pudo eliminar",
                f"El área '{rec.get('nombre', '')}' está en uso por órdenes de producción y no se puede eliminar.")
            return
        self.recargar()


class _DialogEstacion(QDialog):
    def __init__(self, controller: ProduccionController,
                 estacion_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.estacion_id = estacion_id
        self.setWindowTitle("Nueva Área" if estacion_id is None else "Editar Área")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._setup_ui()
        if estacion_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Repasado")
        self.spn_orden = QSpinBox()
        self.spn_orden.setRange(1, 999)
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción opcional")
        form.addRow("Área:", self.txt_nombre)
        form.addRow("Orden:", self.spn_orden)
        form.addRow("Descripción:", self.txt_desc)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        for e in self.controller.listar_estaciones(solo_activos=False):
            if e["id"] == self.estacion_id:
                self.txt_nombre.setText(e["nombre"])
                self.spn_orden.setValue(e["orden"])
                self.txt_desc.setText(e.get("descripcion", "") or "")
                break

    def _save(self) -> None:
        nombre = self.txt_nombre.text().strip()
        orden = self.spn_orden.value()
        desc = self.txt_desc.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "El nombre del área es obligatorio.")
            return
        try:
            if self.estacion_id:
                self.controller.actualizar_estacion(self.estacion_id, nombre, orden, desc)
            else:
                self.controller.crear_estacion(nombre, orden, desc)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _TabTallas(QWidget):
    def __init__(self, controller: InventarioController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel(
            "Catálogo unificado de tallas/puntos (RD-1). Configure la corrida "
            "que necesita: genere en serie 'de X a Y talla' (pasos de medio "
            "punto). El orden se deriva del valor numérico (ya no existe el "
            "campo 'orden'). Las tallas activas se usan en compras y producción."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        serie_box = QGroupBox("Generar tallas en serie (corrida)")
        serie_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        serie_layout = QHBoxLayout(serie_box)
        serie_layout.setSpacing(8)

        serie_layout.addWidget(QLabel("De talla:"))
        self.spn_serie_desde = QDoubleSpinBox()
        self.spn_serie_desde.setRange(0, 99)
        self.spn_serie_desde.setSingleStep(0.5)
        self.spn_serie_desde.setDecimals(1)
        self.spn_serie_desde.setValue(22)
        serie_layout.addWidget(self.spn_serie_desde)

        serie_layout.addWidget(QLabel("a talla:"))
        self.spn_serie_hasta = QDoubleSpinBox()
        self.spn_serie_hasta.setRange(0, 99)
        self.spn_serie_hasta.setSingleStep(0.5)
        self.spn_serie_hasta.setDecimals(1)
        self.spn_serie_hasta.setValue(31)
        serie_layout.addWidget(self.spn_serie_hasta)

        btn_generar = QPushButton("Generar")
        btn_generar.setObjectName("btnPrimary")
        btn_generar.clicked.connect(self._generar_serie)
        serie_layout.addWidget(btn_generar)
        serie_layout.addStretch()
        layout.addWidget(serie_box)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ID", "Talla"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        configurar_tabla_excel(self.table)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.doubleClicked.connect(self._editar)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("+ Nueva Talla")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self._crear)
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setObjectName("btnSecondary")
        self.btn_edit.clicked.connect(self._editar)
        self.btn_del = QPushButton("Desactivar")
        self.btn_del.setObjectName("btnSecondary")
        self.btn_del.clicked.connect(self._desactivar)
        self.btn_activar = QPushButton("Activar")
        self.btn_activar.setObjectName("btnSecondary")
        self.btn_activar.clicked.connect(self._activar)
        self.btn_vaciar = QPushButton("Vaciar lista")
        self.btn_vaciar.setObjectName("btnDanger")
        self.btn_vaciar.clicked.connect(self._vaciar)

        self.btn_add.setEnabled(tiene(self.permisos, "configuracion", "crear"))
        self.btn_edit.setEnabled(tiene(self.permisos, "configuracion", "editar"))
        self.btn_del.setEnabled(tiene(self.permisos, "configuracion", "eliminar"))
        self.btn_activar.setEnabled(tiene(self.permisos, "configuracion", "editar"))
        self.btn_vaciar.setEnabled(tiene(self.permisos, "configuracion", "eliminar"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_del)
        toolbar.addWidget(self.btn_activar)
        toolbar.addWidget(self.btn_vaciar)
        toolbar.addStretch()
        layout.addLayout(toolbar)

    def recargar(self) -> None:
        tallas = self.controller.listar_tallas(solo_activos=False)
        self.table.setRowCount(len(tallas))
        for i, p in enumerate(tallas):
            self.table.setItem(i, 0, QTableWidgetItem(str(p["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(p["talla"]))
            if not p["activo"]:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setForeground(Qt.gray)

    def _generar_serie(self) -> None:
        desde = self.spn_serie_desde.value()
        hasta = self.spn_serie_hasta.value()
        if desde > hasta:
            desde, hasta = hasta, desde
        creados = self.controller.generar_tallas(desde, hasta)
        total = len(self.controller.listar_tallas(solo_activos=False))
        QMessageBox.information(
            self, "Tallas generadas",
            f"Corrida de talla {desde:g} a {hasta:g} lista.\n"
            f"{creados} nuevas; el resto ya existía (se reactivaron).\n"
            f"Total en catálogo: {total}.",
        )
        self.recargar()

    def _crear(self) -> None:
        dlg = _DialogTalla(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione una talla de la lista.")
            return
        dlg = _DialogTalla(self.controller, int(self.table.item(row, 0).text()))
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _filas_seleccionadas(self) -> list[int]:
        filas = sorted({i.row() for i in self.table.selectedIndexes()})
        if not filas:
            QMessageBox.information(self, "Seleccione", "Seleccione al menos una talla de la lista.")
        return filas

    def _desactivar(self) -> None:
        filas = self._filas_seleccionadas()
        if not filas:
            return
        nombres = ", ".join(self.table.item(r, 1).text() for r in filas)
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar las tallas seleccionadas?\n{nombres}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            for r in filas:
                self.controller.desactivar_talla(int(self.table.item(r, 0).text()))
            self.recargar()

    def _activar(self) -> None:
        filas = self._filas_seleccionadas()
        if not filas:
            return
        for r in filas:
            self.controller.activar_talla(int(self.table.item(r, 0).text()))
        self.recargar()

    def _vaciar(self) -> None:
        total = len(self.controller.listar_tallas(solo_activos=False))
        if total == 0:
            QMessageBox.information(self, "Lista vacía", "El catálogo de tallas ya está vacío.")
            return
        resp = QMessageBox.warning(
            self, "Vaciar lista",
            f"Esto eliminará TODAS las tallas del catálogo ({total}).\n"
            "Las tallas usadas en órdenes de compra o producción no se podrán "
            "eliminar.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                eliminados = self.controller.vaciar_tallas()
            except Exception as e:
                QMessageBox.warning(self, "Error",
                    f"No se pudo vaciar la lista:\n{e}\n\n"
                    "Verifique que ninguna talla esté en uso en órdenes.")
                return
            QMessageBox.information(self, "Lista vaciada",
                f"Se eliminaron {eliminados} tallas del catálogo.")
            self.recargar()


class _DialogTalla(QDialog):
    def __init__(self, controller: InventarioController, talla_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.talla_id = talla_id
        self.setWindowTitle("Nueva Talla" if talla_id is None else "Editar Talla")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()
        if talla_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_talla = QLineEdit()
        self.txt_talla.setPlaceholderText("Ej: 22, 22.5, 00")
        form.addRow("Talla:", self.txt_talla)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        for p in self.controller.listar_tallas(solo_activos=False):
            if p["id"] == self.talla_id:
                self.txt_talla.setText(p["talla"])
                break

    def _save(self) -> None:
        talla = self.txt_talla.text().strip()
        if not talla:
            QMessageBox.warning(self, "Campo requerido", "La talla es obligatoria.")
            return
        try:
            if self.talla_id:
                self.controller.actualizar_talla(self.talla_id, talla)
            else:
                self.controller.crear_talla(talla)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _TabColores(QWidget):
    def __init__(self, controller: InventarioController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel(
            "Catálogo de colores para variantes de insumo. "
            "El 'código' corto se usa en el código generado (ej: NEG -> INS-0001-NEG)."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.grid = ComplexGrid()
        self.grid.set_columnas([
            {"key": "nombre", "titulo": "Nombre", "ancho": 240},
            {"key": "codigo", "titulo": "Código", "ancho": 140},
            {"key": "orden", "titulo": "Orden", "ancho": 100, "tipo": "numero"},
        ])
        self.grid.set_renderers(estilo=self._estilo)
        self.grid.set_exportar_visible(
            tiene(self.permisos, "configuracion", "exportar"))
        self.grid.doubleClicked.connect(self._editar)
        layout.addWidget(self.grid)

        self.btn_add = QPushButton("+ Nuevo Color")
        self.btn_add.setObjectName("btnPrimary")
        self.btn_add.clicked.connect(self._crear)
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setObjectName("btnSecondary")
        self.btn_edit.clicked.connect(self._editar)
        self.btn_del = QPushButton("Desactivar")
        self.btn_del.setObjectName("btnDanger")
        self.btn_del.clicked.connect(self._desactivar)

        self.btn_add.setEnabled(tiene(self.permisos, "configuracion", "crear"))
        self.btn_edit.setEnabled(tiene(self.permisos, "configuracion", "editar"))
        self.btn_del.setEnabled(tiene(self.permisos, "configuracion", "eliminar"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)

    @staticmethod
    def _estilo(rec, item, col) -> None:
        if not rec.get("activo"):
            item.setForeground(Qt.gray)

    def recargar(self) -> None:
        colores = self.controller.listar_colores(solo_activos=False)
        self.grid.set_datos(colores)

    def _crear(self) -> None:
        dlg = _DialogColor(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        rec = self.grid.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccione", "Seleccione un color de la lista.")
            return
        dlg = _DialogColor(self.controller, rec["id"])
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _desactivar(self) -> None:
        rec = self.grid.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccione", "Seleccione un color de la lista.")
            return
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar el color '{rec['nombre']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.desactivar_color(rec["id"])
            self.recargar()


class _DialogColor(QDialog):
    def __init__(self, controller: InventarioController, color_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.color_id = color_id
        self.setWindowTitle("Nuevo Color" if color_id is None else "Editar Color")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()
        if color_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Negro")
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Código corto, ej: NEG")
        self.spn_orden = QSpinBox()
        self.spn_orden.setRange(0, 999)
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Código:", self.txt_codigo)
        form.addRow("Orden:", self.spn_orden)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        for c in self.controller.listar_colores(solo_activos=False):
            if c["id"] == self.color_id:
                self.txt_nombre.setText(c["nombre"])
                self.txt_codigo.setText(c["codigo"])
                self.spn_orden.setValue(c["orden"])
                break

    def _save(self) -> None:
        nombre = self.txt_nombre.text().strip()
        codigo = self.txt_codigo.text().strip()
        if not nombre or not codigo:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y código son obligatorios.")
            return
        try:
            if self.color_id:
                self.controller.actualizar_color(self.color_id, nombre, codigo, self.spn_orden.value())
            else:
                self.controller.crear_color(nombre, codigo, self.spn_orden.value())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _TabAccesos(QWidget):
    def __init__(self, controller: AccesosController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._usuario_id = None
        self._checks: dict[tuple, QCheckBox] = {}
        self._setup_ui()
        self.recargar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel(
            "Cada usuario tiene sus propios permisos por módulo y acción.\n"
            "Seleccione un usuario y marque los accesos que se le otorgan."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.grid = ComplexGrid()
        self.grid.set_columnas([
            {"key": "username", "titulo": "Usuario", "ancho": 180},
            {"key": "nombre_completo", "titulo": "Nombre", "ancho": 260},
            {"key": "rol", "titulo": "Rol", "ancho": 130},
            {"key": "activo", "titulo": "Estatus", "ancho": 110},
        ])
        self.grid.set_renderers(fila=self._fila, claves=self._fila,
                                estilo=self._estilo)
        self.grid.set_exportar_visible(tiene(self.permisos, "usuarios", "exportar"))
        self.grid.selectionChanged.connect(self._on_seleccion)
        layout.addWidget(self.grid)

        self.btn_nuevo = QPushButton("+ Nuevo Usuario")
        self.btn_nuevo.setObjectName("btnPrimary")
        self.btn_nuevo.clicked.connect(self._crear_usuario)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("btnSecondary")
        self.btn_editar.clicked.connect(self._editar_usuario)
        self.btn_password = QPushButton("Cambiar Contraseña")
        self.btn_password.setObjectName("btnSecondary")
        self.btn_password.clicked.connect(self._cambiar_password)
        self.btn_toggle = QPushButton("Activar / Desactivar")
        self.btn_toggle.setObjectName("btnDanger")
        self.btn_toggle.clicked.connect(self._toggle_usuario)

        self.btn_nuevo.setEnabled(tiene(self.permisos, "usuarios", "crear"))
        can_edit = tiene(self.permisos, "usuarios", "editar")
        self.btn_editar.setEnabled(can_edit)
        self.btn_password.setEnabled(can_edit)
        self.btn_toggle.setEnabled(tiene(self.permisos, "usuarios", "eliminar"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.btn_nuevo)
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_password)
        toolbar.addWidget(self.btn_toggle)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        box = QGroupBox("Permisos de acceso")
        box_layout = QVBoxLayout(box)

        grid = QGridLayout()
        grid.setSpacing(6)
        for col, (_, label) in enumerate(ACCIONES, start=1):
            h = QLabel(label)
            h.setStyleSheet("font-weight: bold; color: #475569;")
            h.setAlignment(Qt.AlignCenter)
            grid.addWidget(h, 0, col)
        for row, (modulo, label) in enumerate(MODULOS, start=1):
            m = QLabel(label)
            m.setStyleSheet("font-weight: 600; color: #1e293b;")
            grid.addWidget(m, row, 0)
            for col, (accion, _) in enumerate(ACCIONES, start=1):
                chk = QCheckBox()
                self._checks[(modulo, accion)] = chk
                grid.addWidget(chk, row, col, Qt.AlignCenter)
        box_layout.addLayout(grid)

        self.lbl_admin = QLabel("El administrador tiene acceso total al sistema.")
        self.lbl_admin.setStyleSheet("color: #4f46e5; font-style: italic;")
        self.lbl_admin.hide()
        box_layout.addWidget(self.lbl_admin)
        layout.addWidget(box)

        self.btn_guardar = QPushButton("Guardar Permisos")
        self.btn_guardar.setObjectName("btnPrimary")
        self.btn_guardar.setEnabled(can_edit)
        self.btn_guardar.clicked.connect(self._guardar_permisos)
        layout.addWidget(self.btn_guardar, 0, Qt.AlignLeft)

    @staticmethod
    def _fila(rec) -> list:
        return [
            str(rec.get("username", "")),
            str(rec.get("nombre_completo", "")),
            "Administrador" if rec.get("rol") == "admin" else "Operador",
            "Activo" if rec.get("activo") else "Inactivo",
        ]

    @staticmethod
    def _estilo(rec, item, col) -> None:
        if not rec.get("activo"):
            item.setForeground(Qt.gray)

    def recargar(self) -> None:
        objetivo = self._usuario_id
        usuarios = self.controller.listar_usuarios()
        self.grid.set_datos(usuarios)
        fila = -1
        for i, u in enumerate(self.grid.datos_visibles()):
            if objetivo is not None and u["id"] == objetivo:
                fila = i
                break
        if fila < 0 and self.grid.table.rowCount() > 0:
            fila = 0
        if fila >= 0:
            self.grid.table.selectRow(fila)

    def _on_seleccion(self) -> None:
        rec = self.grid.registro_seleccionado()
        if rec is None:
            self._usuario_id = None
            return
        self._usuario_id = rec["id"]
        es_admin = bool(rec.get("rol") == "admin")
        if es_admin:
            for chk in self._checks.values():
                chk.setChecked(True)
                chk.setEnabled(False)
            self.lbl_admin.show()
        else:
            concedidos = self.controller.permisos_usuario(self._usuario_id)
            for (modulo, accion), chk in self._checks.items():
                chk.setChecked(f"{modulo}.{accion}" in concedidos)
                chk.setEnabled(True)
            self.lbl_admin.hide()

    def _guardar_permisos(self) -> None:
        if self._usuario_id is None:
            QMessageBox.information(self, "Seleccione", "Seleccione un usuario de la lista.")
            return
        user = self.controller.obtener_usuario(self._usuario_id)
        if user and user.get("rol") == "admin":
            QMessageBox.information(self, "Sin cambios", "El administrador siempre tiene acceso total.")
            return
        concedidas = {f"{m}.{a}" for (m, a), chk in self._checks.items() if chk.isChecked()}
        self.controller.guardar_permisos(self._usuario_id, concedidas)
        QMessageBox.information(self, "Guardado", "Permisos actualizados correctamente.")

    def _crear_usuario(self) -> None:
        dlg = _DialogUsuario(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar_usuario(self) -> None:
        if not self._validar_seleccion():
            return
        dlg = _DialogUsuario(self.controller, self._usuario_id)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _cambiar_password(self) -> None:
        if not self._validar_seleccion():
            return
        dlg = _DialogPassword(self.controller, self._usuario_id)
        if dlg.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Listo", "Contraseña actualizada.")

    def _toggle_usuario(self) -> None:
        if not self._validar_seleccion():
            return
        user = self.controller.obtener_usuario(self._usuario_id)
        if user.get("rol") == "admin":
            QMessageBox.warning(self, "No permitido", "El administrador no se puede desactivar.")
            return
        nuevo = 0 if user["activo"] else 1
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿{'Desactivar' if nuevo == 0 else 'Reactivar'} al usuario "
            f"'{user['username']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.set_activo(self._usuario_id, bool(nuevo))
            self.recargar()

    def _validar_seleccion(self) -> bool:
        if self._usuario_id is None:
            QMessageBox.information(self, "Seleccione", "Seleccione un usuario de la lista.")
            return False
        return True


class _DialogUsuario(QDialog):
    def __init__(self, controller: AccesosController,
                 usuario_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.setWindowTitle("Nuevo Usuario" if usuario_id is None else "Editar Usuario")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()
        if usuario_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Nombre de usuario para iniciar sesión")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        if self.usuario_id:
            self.txt_pass.setPlaceholderText("Déjelo vacío para conservar la actual")
        else:
            self.txt_pass.setPlaceholderText("Contraseña de acceso")
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItem("Operador", "operador")
        self.cmb_rol.addItem("Administrador", "admin")
        form.addRow("Usuario:", self.txt_username)
        form.addRow("Nombre completo:", self.txt_nombre)
        form.addRow("Contraseña:", self.txt_pass)
        form.addRow("Rol:", self.cmb_rol)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        user = self.controller.obtener_usuario(self.usuario_id)
        if not user:
            return
        self.txt_username.setText(user["username"])
        self.txt_nombre.setText(user["nombre_completo"])
        idx = self.cmb_rol.findData(user["rol"])
        if idx >= 0:
            self.cmb_rol.setCurrentIndex(idx)

    def _save(self) -> None:
        username = self.txt_username.text().strip()
        nombre = self.txt_nombre.text().strip()
        password = self.txt_pass.text()
        rol = self.cmb_rol.currentData()
        if not username or not nombre:
            QMessageBox.warning(self, "Campos requeridos", "Usuario y nombre son obligatorios.")
            return
        try:
            if self.usuario_id:
                self.controller.actualizar_usuario(self.usuario_id, username, nombre, rol)
                if password:
                    self.controller.cambiar_password(self.usuario_id, password)
            else:
                if not password:
                    QMessageBox.warning(
                        self, "Campo requerido",
                        "La contraseña es obligatoria para un nuevo usuario.")
                    return
                self.controller.crear_usuario(username, password, nombre, rol)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _DialogPassword(QDialog):
    def __init__(self, controller: AccesosController, usuario_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.usuario_id = usuario_id
        self.setWindowTitle("Cambiar Contraseña")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_nueva = QLineEdit()
        self.txt_nueva.setEchoMode(QLineEdit.Password)
        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.Password)
        form.addRow("Nueva contraseña:", self.txt_nueva)
        form.addRow("Confirmar:", self.txt_confirmar)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self) -> None:
        nueva = self.txt_nueva.text()
        confirmar = self.txt_confirmar.text()
        if not nueva:
            QMessageBox.warning(self, "Campo requerido", "Escriba la nueva contraseña.")
            return
        if nueva != confirmar:
            QMessageBox.warning(self, "No coinciden", "Las contraseñas no coinciden.")
            return
        try:
            self.controller.cambiar_password(self.usuario_id, nueva)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()
