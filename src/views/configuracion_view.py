from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
    QWidget,
)

from src.controllers.accesos_controller import AccesosController
from src.controllers.inventario_controller import InventarioController
from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.controllers.produccion_controller import ProduccionController
from src.models.accesos_model import ACCIONES, MODULOS, tiene


class DialogConfiguracion(QDialog):
    def __init__(self, parent=None, permisos=None) -> None:
        super().__init__(parent)
        self.permisos = permisos or set()
        self.controller = OrdenesCompraController()
        self.prod_controller = ProduccionController()
        self.accesos_controller = AccesosController()
        self.inv_controller = InventarioController()
        self.setWindowTitle("Configuración")
        self.setMinimumSize(780, 580)
        self.setModal(True)
        self._setup_ui()
        self._cargar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        if tiene(self.permisos, "configuracion", "ver"):
            self.tab_unidades = _TabUnidades(self.controller, self.permisos)
            self.tabs.addTab(self.tab_unidades, "Unidades de Medida")
            self.tab_estaciones = _TabEstaciones(self.prod_controller, self.permisos)
            self.tabs.addTab(self.tab_estaciones, "Áreas de Producción")
            self.tab_puntos = _TabPuntos(self.inv_controller, self.permisos)
            self.tabs.addTab(self.tab_puntos, "Puntos de Variante")
            self.tab_colores = _TabColores(self.inv_controller, self.permisos)
            self.tabs.addTab(self.tab_colores, "Colores de Variante")

        if tiene(self.permisos, "usuarios", "ver"):
            self.tab_accesos = _TabAccesos(self.accesos_controller, self.permisos)
            self.tabs.addTab(self.tab_accesos, "Usuarios y Accesos")

        layout.addWidget(self.tabs)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnPrimary")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

    def _cargar(self) -> None:
        if hasattr(self, "tab_unidades"):
            self.tab_unidades.recargar()
        if hasattr(self, "tab_estaciones"):
            self.tab_estaciones.recargar()
        if hasattr(self, "tab_puntos"):
            self.tab_puntos.recargar()
        if hasattr(self, "tab_colores"):
            self.tab_colores.recargar()


class _TabUnidades(QWidget):
    def __init__(self, controller: OrdenesCompraController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Abreviatura"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self._editar)

        layout.addWidget(self.table)

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

    def recargar(self) -> None:
        unidades = self.controller.listar_unidades(solo_activos=False)
        self.table.setRowCount(len(unidades))
        for i, u in enumerate(unidades):
            self.table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(u["nombre"]))
            self.table.setItem(i, 2, QTableWidgetItem(u["abreviatura"]))
            if not u["activo"]:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setForeground(Qt.gray)

    def _crear(self) -> None:
        dlg = _DialogUnidad(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione una unidad de la lista.")
            return
        unidad_id = int(self.table.item(row, 0).text())
        dlg = _DialogUnidad(self.controller, unidad_id)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _desactivar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione una unidad de la lista.")
            return
        unidad_id = int(self.table.item(row, 0).text())
        nombre = self.table.item(row, 1).text()
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar la unidad '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.desactivar_unidad(unidad_id)
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

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Orden", "Área", "Descripción", "ID"])
        self.table.setColumnHidden(3, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self._editar)

        layout.addWidget(self.table)

        self.btn_add = QPushButton("+ Nueva Área")
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

    def recargar(self) -> None:
        estaciones = self.controller.listar_estaciones(solo_activos=False)
        self.table.setRowCount(len(estaciones))
        for i, e in enumerate(estaciones):
            self.table.setItem(i, 0, QTableWidgetItem(str(e.get("orden", 0))))
            self.table.setItem(i, 1, QTableWidgetItem(e.get("nombre", "")))
            self.table.setItem(i, 2, QTableWidgetItem(e.get("descripcion", "") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(str(e.get("id", ""))))
            if not e.get("activo"):
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setForeground(Qt.gray)

    def _crear(self) -> None:
        dlg = _DialogEstacion(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un área de la lista.")
            return
        estacion_id = int(self.table.item(row, 3).text())
        dlg = _DialogEstacion(self.controller, estacion_id)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _desactivar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un área de la lista.")
            return
        estacion_id = int(self.table.item(row, 3).text())
        nombre = self.table.item(row, 1).text()
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar el área '{nombre}'?\nLas órdenes que ya la usan conservan su avance.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.desactivar_estacion(estacion_id)
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


class _TabPuntos(QWidget):
    def __init__(self, controller: InventarioController, permisos=None) -> None:
        super().__init__()
        self.controller = controller
        self.permisos = permisos or set()
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        hint = QLabel(
            "Catálogo de puntos disponibles para generar variantes de insumo "
            "(se usan en los selectores 'desde' y 'hasta' de la captura y "
            "como tallas/puntos en las órdenes de compra)."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        serie_box = QGroupBox("Generar puntos en serie")
        serie_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        serie_layout = QHBoxLayout(serie_box)
        serie_layout.setSpacing(8)

        serie_layout.addWidget(QLabel("Desde:"))
        self.spn_serie_desde = QSpinBox()
        self.spn_serie_desde.setRange(0, 99)
        self.spn_serie_desde.setValue(0)
        serie_layout.addWidget(self.spn_serie_desde)

        serie_layout.addWidget(QLabel("hasta:"))
        self.spn_serie_hasta = QSpinBox()
        self.spn_serie_hasta.setRange(0, 99)
        self.spn_serie_hasta.setValue(21)
        serie_layout.addWidget(self.spn_serie_hasta)

        btn_generar = QPushButton("Generar")
        btn_generar.setObjectName("btnPrimary")
        btn_generar.clicked.connect(self._generar_serie)
        serie_layout.addWidget(btn_generar)
        serie_layout.addStretch()
        layout.addWidget(serie_box)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Punto", "Orden"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.doubleClicked.connect(self._editar)
        layout.addWidget(self.table)

        self.btn_add = QPushButton("+ Nuevo Punto")
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
        puntos = self.controller.listar_puntos(solo_activos=False)
        self.table.setRowCount(len(puntos))
        for i, p in enumerate(puntos):
            self.table.setItem(i, 0, QTableWidgetItem(str(p["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(p["punto"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(p["orden"])))
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
        creados = self.controller.generar_puntos(desde, hasta)
        total = len(self.controller.listar_puntos(solo_activos=False))
        QMessageBox.information(
            self, "Puntos generados",
            f"Puntos {desde:02d} a {hasta:02d} listos.\n"
            f"{creados} nuevos; el resto ya existía (se reactivaron).\n"
            f"Total en catálogo: {total}.",
        )
        self.recargar()

    def _crear(self) -> None:
        dlg = _DialogPunto(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un punto de la lista.")
            return
        dlg = _DialogPunto(self.controller, int(self.table.item(row, 0).text()))
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _filas_seleccionadas(self) -> list[int]:
        filas = sorted({i.row() for i in self.table.selectedIndexes()})
        if not filas:
            QMessageBox.information(self, "Seleccione", "Seleccione al menos un punto de la lista.")
        return filas

    def _desactivar(self) -> None:
        filas = self._filas_seleccionadas()
        if not filas:
            return
        nombres = ", ".join(self.table.item(r, 1).text() for r in filas)
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar los puntos seleccionados?\n{nombres}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            for r in filas:
                self.controller.desactivar_punto(int(self.table.item(r, 0).text()))
            self.recargar()

    def _activar(self) -> None:
        filas = self._filas_seleccionadas()
        if not filas:
            return
        for r in filas:
            self.controller.activar_punto(int(self.table.item(r, 0).text()))
        self.recargar()

    def _vaciar(self) -> None:
        total = len(self.controller.listar_puntos(solo_activos=False))
        if total == 0:
            QMessageBox.information(self, "Lista vacía", "El catálogo de puntos ya está vacío.")
            return
        resp = QMessageBox.warning(
            self, "Vaciar lista",
            f"Esto eliminará TODOS los puntos del catálogo ({total}).\n"
            "Los puntos usados en órdenes de compra no se podrán eliminar.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            try:
                eliminados = self.controller.vaciar_puntos()
            except Exception as e:
                QMessageBox.warning(self, "Error",
                    f"No se pudo vaciar la lista:\n{e}\n\n"
                    "Verifique que ningún punto esté en uso en órdenes de compra.")
                return
            QMessageBox.information(self, "Lista vaciada",
                f"Se eliminaron {eliminados} puntos del catálogo.")
            self.recargar()


class _DialogPunto(QDialog):
    def __init__(self, controller: InventarioController, punto_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.punto_id = punto_id
        self.setWindowTitle("Nuevo Punto" if punto_id is None else "Editar Punto")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._setup_ui()
        if punto_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_punto = QLineEdit()
        self.txt_punto.setPlaceholderText("Ej: 00, 13")
        self.spn_orden = QSpinBox()
        self.spn_orden.setRange(0, 999)
        form.addRow("Punto:", self.txt_punto)
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
        for p in self.controller.listar_puntos(solo_activos=False):
            if p["id"] == self.punto_id:
                self.txt_punto.setText(p["punto"])
                self.spn_orden.setValue(p["orden"])
                break

    def _save(self) -> None:
        punto = self.txt_punto.text().strip()
        if not punto:
            QMessageBox.warning(self, "Campo requerido", "El punto es obligatorio.")
            return
        try:
            if self.punto_id:
                self.controller.actualizar_punto(self.punto_id, punto, self.spn_orden.value())
            else:
                self.controller.crear_punto(punto, self.spn_orden.value())
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

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Código", "Orden"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self._editar)
        layout.addWidget(self.table)

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

    def recargar(self) -> None:
        colores = self.controller.listar_colores(solo_activos=False)
        self.table.setRowCount(len(colores))
        for i, c in enumerate(colores):
            self.table.setItem(i, 0, QTableWidgetItem(str(c["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(c["nombre"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["codigo"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(c["orden"])))
            if not c["activo"]:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setForeground(Qt.gray)

    def _crear(self) -> None:
        dlg = _DialogColor(self.controller)
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _editar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un color de la lista.")
            return
        dlg = _DialogColor(self.controller, int(self.table.item(row, 0).text()))
        if dlg.exec() == QDialog.Accepted:
            self.recargar()

    def _desactivar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un color de la lista.")
            return
        nombre = self.table.item(row, 1).text()
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Desactivar el color '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.controller.desactivar_color(int(self.table.item(row, 0).text()))
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

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Usuario", "Nombre", "Rol", "Estatus"])
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_seleccion)
        layout.addWidget(self.table)

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

    def recargar(self) -> None:
        seleccionado = self._usuario_id
        usuarios = self.controller.listar_usuarios()
        self.table.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self.table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(u["username"]))
            self.table.setItem(i, 2, QTableWidgetItem(u["nombre_completo"]))
            rol = "Administrador" if u["rol"] == "admin" else "Operador"
            self.table.setItem(i, 3, QTableWidgetItem(rol))
            self.table.setItem(i, 4, QTableWidgetItem("Activo" if u["activo"] else "Inactivo"))
            if not u["activo"]:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setForeground(Qt.gray)
        if seleccionado is not None:
            for i in range(self.table.rowCount()):
                if int(self.table.item(i, 0).text()) == seleccionado:
                    self.table.selectRow(i)
                    return
        if self.table.rowCount() > 0:
            self.table.selectRow(0)

    def _on_seleccion(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            self._usuario_id = None
            return
        self._usuario_id = int(self.table.item(row, 0).text())
        user = self.controller.obtener_usuario(self._usuario_id)
        es_admin = bool(user and user.get("rol") == "admin")
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
