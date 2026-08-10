from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout, QFrame,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from src.controllers.clientes_controller import ClientesController
from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.export_utils import (
    export_pedido_cliente_excel, export_table_to_excel, print_pedido_cliente, print_table,
)
from src.utils.table_utils import NumericItem, configurar_tabla_excel
from src.views.dialogs import DialogMatrizTallas
from src.views.programar_pedido_dialog import ProgramarPedidoDialog


_ESTATUS = {
    "pendiente": "Pendiente",
    "programado": "Programado",
    "surtido": "Surtido",
    "cancelado": "Cancelado",
}


def _fmt_estatus(estatus: str) -> str:
    return _ESTATUS.get(estatus, estatus.replace("_", " ").capitalize())


class ClientesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ClientesController()
        self._setup_ui()
        self._load_pedidos()
        self._load_clientes()

    def set_permisos(self, permisos) -> None:
        self.btn_nuevo_pedido.setEnabled(tiene(permisos, "clientes", "crear"))
        self.btn_ver.setEnabled(tiene(permisos, "clientes", "ver"))
        self.btn_programar.setEnabled(tiene(permisos, "programacion", "editar"))
        self.btn_estatus.setEnabled(tiene(permisos, "clientes", "editar"))
        self.btn_cancelar.setEnabled(tiene(permisos, "clientes", "eliminar"))
        self.btn_export.setEnabled(tiene(permisos, "clientes", "exportar"))
        self.btn_print.setEnabled(tiene(permisos, "clientes", "exportar"))
        self.btn_nuevo_cli.setEnabled(tiene(permisos, "clientes", "crear"))
        self.btn_editar_cli.setEnabled(tiene(permisos, "clientes", "editar"))
        self.btn_desactivar_cli.setEnabled(tiene(permisos, "clientes", "eliminar"))
        self.btn_reactivar_cli.setEnabled(tiene(permisos, "clientes", "eliminar"))
        self.btn_export_cli.setEnabled(tiene(permisos, "clientes", "exportar"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QFrame()
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel("Clientes y Pedidos")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Catálogo de clientes y pedidos de venta por tallas")
        subtitle.setObjectName("sectionSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.btn_nuevo_pedido = QPushButton("+ Nuevo Pedido")
        self.btn_nuevo_pedido.setObjectName("btnPrimary")
        self.btn_nuevo_pedido.clicked.connect(self._nuevo_pedido)

        self.btn_clientes = QPushButton("Clientes")
        self.btn_clientes.setObjectName("btnSecondary")
        self.btn_clientes.clicked.connect(lambda: self.tabs.setCurrentIndex(1))

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_clientes)
        hlayout.addWidget(self.btn_nuevo_pedido)

        self.tabs = QTabWidget()
        self.tab_pedidos = QWidget()
        self.tab_clientes = QWidget()
        self.tabs.addTab(self.tab_pedidos, "Pedidos")
        self.tabs.addTab(self.tab_clientes, "Clientes")
        self._setup_tab_pedidos()
        self._setup_tab_clientes()

        layout.addWidget(header)
        layout.addWidget(self.tabs)

    def _setup_tab_pedidos(self) -> None:
        layout = QVBoxLayout(self.tab_pedidos)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.cmb_filtro_cliente = QComboBox()
        self.cmb_filtro_cliente.setMinimumWidth(200)
        self.cmb_filtro_cliente.currentIndexChanged.connect(
            self._aplicar_filtro_pedidos)
        self._rellenar_filtro_clientes()

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por folio, cliente o modelo...")
        self.txt_buscar.setMinimumWidth(300)
        self.txt_buscar.textChanged.connect(self._buscar_pedidos)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self._load_pedidos)

        self.btn_ver = QPushButton("Ver Detalle")
        self.btn_ver.setObjectName("btnSecondary")
        self.btn_ver.clicked.connect(self._ver_pedido)

        self.btn_programar = QPushButton("Programar")
        self.btn_programar.setObjectName("btnPrimary")
        self.btn_programar.clicked.connect(self._programar_pedido)

        self.btn_estatus = QPushButton("Cambiar Estatus")
        self.btn_estatus.setObjectName("btnSecondary")
        self.btn_estatus.clicked.connect(self._cambiar_estatus)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnDanger")
        self.btn_cancelar.clicked.connect(self._cancelar_pedido)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.clicked.connect(self._exportar)

        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(self._imprimir)

        toolbar.addWidget(QLabel("Cliente:"))
        toolbar.addWidget(self.cmb_filtro_cliente)
        toolbar.addWidget(self.txt_buscar)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        toolbar_acciones = QHBoxLayout()
        toolbar_acciones.addStretch()
        toolbar_acciones.addWidget(self.btn_ver)
        toolbar_acciones.addWidget(self.btn_programar)
        toolbar_acciones.addWidget(self.btn_estatus)
        toolbar_acciones.addWidget(self.btn_cancelar)
        toolbar_acciones.addWidget(self.btn_export)
        toolbar_acciones.addWidget(self.btn_print)
        layout.addLayout(toolbar_acciones)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Folio", "Cliente", "Fecha Pedido", "Fecha Programado", "Pares", "Estatus", "ID"])
        self.table.setColumnHidden(6, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        configurar_tabla_excel(self.table)
        self.table.doubleClicked.connect(self._ver_pedido)
        layout.addWidget(self.table)

    def _setup_tab_clientes(self) -> None:
        layout = QVBoxLayout(self.tab_clientes)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.txt_buscar_cli = QLineEdit()
        self.txt_buscar_cli.setPlaceholderText("Buscar cliente...")
        self.txt_buscar_cli.setMinimumWidth(300)
        self.txt_buscar_cli.textChanged.connect(self._buscar_clientes)

        btn_refresh_cli = QPushButton("Actualizar")
        btn_refresh_cli.setObjectName("btnPrimary")
        btn_refresh_cli.clicked.connect(self._load_clientes)

        self.btn_nuevo_cli = QPushButton("+ Nuevo Cliente")
        self.btn_nuevo_cli.setObjectName("btnPrimary")
        self.btn_nuevo_cli.clicked.connect(self._nuevo_cliente)
        self.btn_editar_cli = QPushButton("Editar")
        self.btn_editar_cli.setObjectName("btnSecondary")
        self.btn_editar_cli.clicked.connect(self._editar_cliente)
        self.btn_desactivar_cli = QPushButton("Desactivar")
        self.btn_desactivar_cli.setObjectName("btnDanger")
        self.btn_desactivar_cli.clicked.connect(self._desactivar_cliente)
        self.btn_reactivar_cli = QPushButton("Reactivar")
        self.btn_reactivar_cli.setObjectName("btnSecondary")
        self.btn_reactivar_cli.clicked.connect(self._reactivar_cliente)
        self.btn_export_cli = QPushButton("Exportar Excel")
        self.btn_export_cli.setObjectName("btnPrimary")
        self.btn_export_cli.clicked.connect(self._exportar_clientes)

        toolbar.addWidget(self.txt_buscar_cli)
        toolbar.addWidget(btn_refresh_cli)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        toolbar_acciones = QHBoxLayout()
        toolbar_acciones.addStretch()
        toolbar_acciones.addWidget(self.btn_nuevo_cli)
        toolbar_acciones.addWidget(self.btn_editar_cli)
        toolbar_acciones.addWidget(self.btn_desactivar_cli)
        toolbar_acciones.addWidget(self.btn_reactivar_cli)
        toolbar_acciones.addWidget(self.btn_export_cli)
        layout.addLayout(toolbar_acciones)

        self.table_cli = QTableWidget()
        self.table_cli.setColumnCount(7)
        self.table_cli.setHorizontalHeaderLabels(
            ["RFC", "Nombre", "Nombre Comercial", "Teléfono", "Email", "Dirección", "ID"])
        self.table_cli.setColumnHidden(6, True)
        self.table_cli.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_cli.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_cli.setSortingEnabled(True)
        self.table_cli.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        configurar_tabla_excel(self.table_cli)
        self.table_cli.doubleClicked.connect(self._editar_cliente)
        layout.addWidget(self.table_cli)

    # ---- Carga y búsqueda ----

    def _load_pedidos(self) -> None:
        try:
            cliente_id = self.cmb_filtro_cliente.currentData()
            pedidos = self.controller.listar_pedidos(cliente_id)
            self.table.setSortingEnabled(False)
            self.table.setRowCount(len(pedidos))
            for i, p in enumerate(pedidos):
                self._set_fila_pedido(i, p)
            self.table.setSortingEnabled(True)
        except Exception as e:
            print(f"Error: {e}")

    def _set_fila_pedido(self, i: int, p: dict) -> None:
        self.table.setItem(i, 0, QTableWidgetItem(p.get("folio", "")))
        self.table.setItem(i, 1, QTableWidgetItem(p.get("cliente_nombre", "")))
        self.table.setItem(i, 2, QTableWidgetItem(p.get("fecha_pedido", "")))
        self.table.setItem(i, 3, QTableWidgetItem(p.get("fecha_programado", "") or ""))
        item_pares = NumericItem(p.get("total_pares", 0))
        item_pares.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(i, 4, item_pares)
        est = p.get("estatus", "")
        item_est = QTableWidgetItem(_fmt_estatus(est))
        if est == "surtido":
            item_est.setForeground(Qt.darkGreen)
        elif est == "programado":
            item_est.setForeground(Qt.darkYellow)
        elif est == "cancelado":
            item_est.setForeground(Qt.red)
        self.table.setItem(i, 5, item_est)
        self.table.setItem(i, 6, QTableWidgetItem(str(p.get("id", ""))))

    def _load_clientes(self) -> None:
        try:
            clientes = self.controller.listar_clientes(solo_activos=False)
            self.table_cli.setSortingEnabled(False)
            self.table_cli.setRowCount(len(clientes))
            for i, c in enumerate(clientes):
                self._set_fila_cliente(i, c)
            self.table_cli.setSortingEnabled(True)
            self._rellenar_filtro_clientes()
        except Exception as e:
            print(f"Error: {e}")

    def _set_fila_cliente(self, i: int, c: dict) -> None:
        self.table_cli.setItem(i, 0, QTableWidgetItem(c.get("rfc", "")))
        self.table_cli.setItem(i, 1, QTableWidgetItem(c.get("nombre", "")))
        self.table_cli.setItem(i, 2, QTableWidgetItem(c.get("nombre_comercial", "") or ""))
        self.table_cli.setItem(i, 3, QTableWidgetItem(c.get("telefono", "") or ""))
        self.table_cli.setItem(i, 4, QTableWidgetItem(c.get("email", "") or ""))
        self.table_cli.setItem(i, 5, QTableWidgetItem(c.get("direccion", "") or ""))
        self.table_cli.setItem(i, 6, QTableWidgetItem(str(c.get("id", ""))))
        if not c.get("activo"):
            for col in range(7):
                item = self.table_cli.item(i, col)
                if item:
                    item.setForeground(Qt.gray)

    def _buscar_pedidos(self, texto: str) -> None:
        if not texto.strip():
            self._load_pedidos()
            return
        try:
            cliente_id = self.cmb_filtro_cliente.currentData()
            resultados = self.controller.buscar_pedidos(texto, cliente_id)
            self.table.setSortingEnabled(False)
            self.table.setRowCount(len(resultados))
            for i, p in enumerate(resultados):
                self._set_fila_pedido(i, p)
            self.table.setSortingEnabled(True)
        except Exception as e:
            print(f"Error: {e}")

    def _aplicar_filtro_pedidos(self) -> None:
        texto = self.txt_buscar.text().strip()
        if texto:
            self._buscar_pedidos(texto)
        else:
            self._load_pedidos()

    def _rellenar_filtro_clientes(self) -> None:
        if not hasattr(self, "cmb_filtro_cliente"):
            return
        actual = self.cmb_filtro_cliente.currentData()
        self.cmb_filtro_cliente.blockSignals(True)
        self.cmb_filtro_cliente.clear()
        self.cmb_filtro_cliente.addItem("Todos", None)
        for c in self.controller.listar_clientes(solo_activos=False):
            self.cmb_filtro_cliente.addItem(c["nombre"], c["id"])
        idx = self.cmb_filtro_cliente.findData(actual)
        self.cmb_filtro_cliente.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_filtro_cliente.blockSignals(False)

    def _buscar_clientes(self, texto: str) -> None:
        if not texto.strip():
            self._load_clientes()
            return
        try:
            resultados = self.controller.buscar_clientes(texto)
            self.table_cli.setSortingEnabled(False)
            self.table_cli.setRowCount(len(resultados))
            for i, c in enumerate(resultados):
                self._set_fila_cliente(i, c)
            self.table_cli.setSortingEnabled(True)
        except Exception as e:
            print(f"Error: {e}")

    # ---- Acciones de pedidos ----

    def _nuevo_pedido(self) -> None:
        dlg = _DialogPedidoCliente(self.controller)
        if dlg.exec():
            self._load_pedidos()

    def _ver_pedido(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        pedido_id = int(self.table.item(row, 6).text())
        dlg = _DialogVerPedido(self.controller, pedido_id)
        dlg.exec()

    def _programar_pedido(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        pedido_id = int(self.table.item(row, 6).text())
        dlg = ProgramarPedidoDialog(self.controller, ProgramacionController(),
                                    pedido_id, self)
        if dlg.exec():
            self._load_pedidos()
            folios = ", ".join(dlg.folios_generados)
            QMessageBox.information(
                self, "Programado",
                f"Se generaron los folios de programación: {folios}")

    def _cambiar_estatus(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        pedido_id = int(self.table.item(row, 6).text())
        actual = self.table.item(row, 5).text().lower()
        opciones = [_ESTATUS[k] for k in ("pendiente", "programado", "surtido")]
        if actual not in opciones:
            QMessageBox.warning(self, "Estatus", "Un pedido cancelado no se puede modificar.")
            return
        nuevo, ok = QInputDialog.getItem(
            self, "Cambiar Estatus", "Nuevo estatus del pedido:",
            opciones, opciones.index(actual) if actual in opciones else 0, False)
        if ok and nuevo:
            clave = [k for k, v in _ESTATUS.items() if v == nuevo][0]
            self.controller.cambiar_estatus(pedido_id, clave)
            self._load_pedidos()

    def _cancelar_pedido(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        est = self.table.item(row, 5).text().lower()
        if est in ("cancelado", "surtido"):
            QMessageBox.warning(self, "Estatus", "Solo se cancelan pedidos pendientes o programados.")
            return
        folio = self.table.item(row, 0).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Cancelar el pedido '{folio}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            pedido_id = int(self.table.item(row, 6).text())
            self.controller.cancelar_pedido(pedido_id)
            self._load_pedidos()

    def _exportar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            path = export_table_to_excel(self.table, "Pedidos_Cliente", self)
        else:
            pedido_id = int(self.table.item(row, 6).text())
            datos = self.controller.obtener_pedido(pedido_id)
            detalle = self.controller.obtener_detalle_pedido(pedido_id)
            path = export_pedido_cliente_excel(datos, detalle, self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            print_table(self.table, "Pedidos_Cliente", self)
        else:
            pedido_id = int(self.table.item(row, 6).text())
            datos = self.controller.obtener_pedido(pedido_id)
            detalle = self.controller.obtener_detalle_pedido(pedido_id)
            print_pedido_cliente(datos, detalle, self)

    # ---- Acciones de clientes ----

    def _nuevo_cliente(self) -> None:
        dlg = _DialogCliente(self.controller)
        if dlg.exec():
            self._load_clientes()

    def _editar_cliente(self) -> None:
        row = self.table_cli.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un cliente.")
            return
        cliente_id = int(self.table_cli.item(row, 6).text())
        dlg = _DialogCliente(self.controller, cliente_id)
        if dlg.exec():
            self._load_clientes()

    def _desactivar_cliente(self) -> None:
        row = self.table_cli.currentRow()
        if row < 0:
            return
        nombre = self.table_cli.item(row, 1).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            cliente_id = int(self.table_cli.item(row, 6).text())
            self.controller.desactivar_cliente(cliente_id)
            self._load_clientes()

    def _reactivar_cliente(self) -> None:
        row = self.table_cli.currentRow()
        if row < 0:
            return
        cliente_id = int(self.table_cli.item(row, 6).text())
        self.controller.reactivar_cliente(cliente_id)
        self._load_clientes()

    def _exportar_clientes(self) -> None:
        path = export_table_to_excel(self.table_cli, "Clientes", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")


class _DialogCliente(QDialog):
    def __init__(self, controller: ClientesController, cliente_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.cliente_id = cliente_id
        self.setWindowTitle("Nuevo Cliente" if cliente_id is None else "Editar Cliente")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._setup_ui()
        if cliente_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del cliente (obligatorio)")
        self.txt_rfc = QLineEdit()
        self.txt_rfc.setPlaceholderText("RFC (opcional)")
        self.txt_comercial = QLineEdit()
        self.txt_comercial.setPlaceholderText("Nombre comercial (marca o tienda)")
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Teléfono")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Correo electrónico")
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Dirección")
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("RFC:", self.txt_rfc)
        form.addRow("Nombre Comercial:", self.txt_comercial)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Email:", self.txt_email)
        form.addRow("Dirección:", self.txt_direccion)
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
        c = self.controller.obtener_cliente(self.cliente_id)
        if c:
            self.txt_nombre.setText(c.get("nombre", ""))
            self.txt_rfc.setText(c.get("rfc", ""))
            self.txt_comercial.setText(c.get("nombre_comercial", "") or "")
            self.txt_telefono.setText(c.get("telefono", "") or "")
            self.txt_email.setText(c.get("email", "") or "")
            self.txt_direccion.setText(c.get("direccion", "") or "")

    def _save(self) -> None:
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Campo requerido", "El nombre del cliente es obligatorio.")
            return
        try:
            if self.cliente_id:
                self.controller.actualizar_cliente(
                    self.cliente_id, nombre, self.txt_rfc.text().strip(),
                    self.txt_comercial.text().strip(), self.txt_telefono.text().strip(),
                    self.txt_email.text().strip(), self.txt_direccion.text().strip())
            else:
                self.controller.crear_cliente(
                    nombre, self.txt_rfc.text().strip(), self.txt_comercial.text().strip(),
                    self.txt_telefono.text().strip(), self.txt_email.text().strip(),
                    self.txt_direccion.text().strip())
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _DialogPedidoCliente(QDialog):
    def __init__(self, controller: ClientesController, pedido_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.pedido_id = pedido_id
        self.setWindowTitle("Nuevo Pedido de Cliente" if pedido_id is None else "Editar Pedido")
        self.setMinimumSize(840, 640)
        self.setModal(True)
        self._puntos_fila: dict[int, dict[int, int]] = {}
        self._setup_ui()
        if pedido_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_cliente = QComboBox()
        for c in self.controller.listar_clientes():
            self.cmb_cliente.addItem(c["nombre"], c["id"])

        self.txt_folio = QLineEdit()
        self.txt_folio.setText(self.controller.siguiente_folio())
        self.txt_folio.setReadOnly(True)

        self.dte_pedido = QDateEdit()
        self.dte_pedido.setCalendarPopup(True)
        self.dte_pedido.setDate(QDate.currentDate())

        self.dte_programado = QDateEdit()
        self.dte_programado.setCalendarPopup(True)
        self.dte_programado.setDate(QDate.currentDate())
        self.chk_sin_programar = QCheckBox("Sin fecha programada")
        self.chk_sin_programar.toggled.connect(
            lambda on: self.dte_programado.setEnabled(not on))

        self.cmb_estatus = QComboBox()
        for k in ("pendiente", "programado", "surtido"):
            self.cmb_estatus.addItem(_ESTATUS[k], k)

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")
        self.txt_obs.setMaximumHeight(60)

        form.addRow("Cliente:", self.cmb_cliente)
        form.addRow("Folio:", self.txt_folio)
        form.addRow("Fecha pedido:", self.dte_pedido)
        form.addRow("Fecha programado:", self.dte_programado)
        form.addRow("", self.chk_sin_programar)
        form.addRow("Estatus:", self.cmb_estatus)
        form.addRow("Observaciones:", self.txt_obs)
        layout.addLayout(form)

        det_label = QLabel("Detalle del pedido:")
        det_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(det_label)

        self.table_detalle = QTableWidget()
        self.table_detalle.setColumnCount(6)
        self.table_detalle.setHorizontalHeaderLabels(
            ["Modelo", "Piel", "Color", "Tallas", "Pares", "ID"])
        self.table_detalle.setColumnHidden(5, True)
        self.table_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_detalle.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_detalle.verticalHeader().setDefaultSectionSize(46)
        configurar_tabla_excel(self.table_detalle)
        self.table_detalle.setMinimumHeight(220)

        btn_add = QPushButton("+ Agregar Línea")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self._agregar_linea)
        btn_remove = QPushButton("Quitar Seleccionada")
        btn_remove.setObjectName("btnDanger")
        btn_remove.clicked.connect(self._quitar_linea)

        self.lbl_total = QLabel("Total de pares: 0")
        self.lbl_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #4f46e5;")

        toolbar = QHBoxLayout()
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_remove)
        toolbar.addStretch()
        toolbar.addWidget(self.lbl_total)
        layout.addWidget(self.table_detalle)
        layout.addLayout(toolbar)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Pedido")
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        pedido = self.controller.obtener_pedido(self.pedido_id)
        if not pedido:
            return
        idx = self.cmb_cliente.findData(pedido["cliente_id"])
        if idx >= 0:
            self.cmb_cliente.setCurrentIndex(idx)
        self.txt_folio.setText(pedido.get("folio", ""))
        self.dte_pedido.setDate(QDate.fromString(pedido.get("fecha_pedido", "") or "",
                                                 "yyyy-MM-dd"))
        prog = pedido.get("fecha_programado")
        if prog:
            self.dte_programado.setDate(QDate.fromString(prog, "yyyy-MM-dd"))
        else:
            self.chk_sin_programar.setChecked(True)
        idx = self.cmb_estatus.findData(pedido.get("estatus"))
        if idx >= 0:
            self.cmb_estatus.setCurrentIndex(idx)
        self.txt_obs.setPlainText(pedido.get("observaciones", "") or "")
        for d in self.controller.obtener_detalle_pedido(self.pedido_id):
            row = self.table_detalle.rowCount()
            self.table_detalle.insertRow(row)
            self._set_fila(row, d["modelo"], d.get("piel", ""), d.get("color", ""))
            self._puntos_fila[row] = {int(t["punto_id"]): int(t.get("pares", 0))
                                      for t in d.get("puntos", [])}
            self._actualizar_boton_tallas(row)

    def _set_fila(self, row: int, modelo: str, piel: str, color: str) -> None:
        self.table_detalle.setItem(row, 0, QTableWidgetItem(modelo))
        self.table_detalle.setItem(row, 1, QTableWidgetItem(piel))
        self.table_detalle.setItem(row, 2, QTableWidgetItem(color))
        btn = QPushButton("Configurar Tallas")
        btn.setObjectName("btnSecondary")
        btn.clicked.connect(lambda _=False, r=row: self._configurar_tallas(r))
        self.table_detalle.setCellWidget(row, 3, btn)
        self.table_detalle.setItem(row, 4, QTableWidgetItem("0"))
        self.table_detalle.setItem(row, 5, QTableWidgetItem("0"))

    def _actualizar_boton_tallas(self, row: int) -> None:
        matriz = self._puntos_fila.get(row, {})
        total = sum(matriz.values())
        btn = self.table_detalle.cellWidget(row, 3)
        if btn:
            btn.setText(f"Editar Tallas ({total} pr)")
        self.table_detalle.item(row, 4).setText(str(total))
        self._recalcular_total()

    def _agregar_linea(self) -> None:
        dlg = _DialogLineaPedido(self)
        if dlg.exec() == QDialog.Accepted:
            row = self.table_detalle.rowCount()
            self.table_detalle.insertRow(row)
            self._puntos_fila[row] = {}
            self._set_fila(row, dlg.modelo, dlg.piel, dlg.color)

    def _configurar_tallas(self, row: int) -> None:
        dlg = DialogMatrizTallas(self.controller, self._puntos_fila.get(row))
        if dlg.exec() == QDialog.Accepted:
            self._puntos_fila[row] = dlg.get_matriz()
            self._actualizar_boton_tallas(row)

    def _quitar_linea(self) -> None:
        row = self.table_detalle.currentRow()
        if row >= 0:
            self.table_detalle.removeRow(row)
            self._puntos_fila.pop(row, None)
            self._recalcular_total()

    def _recalcular_total(self) -> None:
        total = sum(sum(m.values()) for m in self._puntos_fila.values())
        self.lbl_total.setText(f"Total de pares: {total}")

    def _fecha_programado(self) -> str:
        if self.chk_sin_programar.isChecked():
            return ""
        return self.dte_programado.date().toString("yyyy-MM-dd")

    def _save(self) -> None:
        if self.cmb_cliente.currentData() is None:
            QMessageBox.warning(self, "Cliente requerido",
                                "Primero registre al menos un cliente.")
            return
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.warning(self, "Campo requerido", "El folio es obligatorio.")
            return
        detalle = []
        for row in range(self.table_detalle.rowCount()):
            modelo = self.table_detalle.item(row, 0).text().strip()
            if not modelo:
                continue
            puntos = self._puntos_fila.get(row, {})
            detalle.append({
                "modelo": modelo,
                "piel": self.table_detalle.item(row, 1).text().strip(),
                "color": self.table_detalle.item(row, 2).text().strip(),
                "puntos": [{"punto_id": pid, "pares": pr} for pid, pr in puntos.items()],
            })
        if not detalle:
            QMessageBox.warning(self, "Detalle vacío", "Agregue al menos una línea al pedido.")
            return
        cliente_id = self.cmb_cliente.currentData()
        fecha_pedido = self.dte_pedido.date().toString("yyyy-MM-dd")
        fecha_programado = self._fecha_programado()
        estatus = self.cmb_estatus.currentData()
        obs = self.txt_obs.toPlainText().strip()
        try:
            if self.pedido_id:
                self.controller.actualizar_pedido(
                    self.pedido_id, cliente_id, fecha_pedido, fecha_programado,
                    estatus, obs, detalle)
            else:
                self.controller.crear_pedido(
                    folio, cliente_id, fecha_pedido, fecha_programado,
                    estatus, obs, detalle)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _DialogLineaPedido(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Agregar Línea al Pedido")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.modelo = ""
        self.piel = ""
        self.color = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)
        self.txt_modelo = QLineEdit()
        self.txt_modelo.setPlaceholderText("Ej: RENATO GALAN (obligatorio)")
        self.txt_piel = QLineEdit()
        self.txt_piel.setPlaceholderText("Ej: PITÓN")
        self.txt_color = QLineEdit()
        self.txt_color.setPlaceholderText("Ej: NEGRO")
        form.addRow("Modelo:", self.txt_modelo)
        form.addRow("Piel:", self.txt_piel)
        form.addRow("Color:", self.txt_color)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("btnPrimary")
        btn_ok.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)

    def _save(self) -> None:
        modelo = self.txt_modelo.text().strip()
        if not modelo:
            QMessageBox.warning(self, "Campo requerido", "El modelo es obligatorio.")
            return
        self.modelo = modelo
        self.piel = self.txt_piel.text().strip()
        self.color = self.txt_color.text().strip()
        self.accept()


class _DialogVerPedido(QDialog):
    def __init__(self, controller: ClientesController, pedido_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.pedido_id = pedido_id
        self.setWindowTitle("Detalle del Pedido")
        self.setMinimumSize(720, 500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        pedido = self.controller.obtener_pedido(self.pedido_id)
        detalle = self.controller.obtener_detalle_pedido(self.pedido_id)

        info = QLabel()
        info.setWordWrap(True)
        info.setStyleSheet("color: #334155; font-size: 12px; padding: 10px;"
                           "background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
        lineas = []
        if pedido:
            lineas.append(
                f"<b>{pedido.get('folio', '')}</b> — {pedido.get('cliente_nombre', '')} "
                f"({_fmt_estatus(pedido.get('estatus', ''))})")
            lineas.append(f"Fecha pedido: {pedido.get('fecha_pedido', '')} | "
                          f"Programado: {pedido.get('fecha_programado') or 'Sin programar'}")
            if pedido.get("observaciones"):
                lineas.append(f"Observaciones: {pedido.get('observaciones')}")
        info.setText("<br/>".join(lineas))
        layout.addWidget(info)

        self.table = QTableWidget()
        columnas = []
        vistos: set[int] = set()
        for d in detalle:
            for t in d.get("puntos", []):
                if t["punto_id"] not in vistos:
                    vistos.add(t["punto_id"])
                    columnas.append(t)
        columnas.sort(key=lambda t: t.get("orden", 0))
        n = len(columnas)
        self.table.setColumnCount(4 + n)
        headers = ["Modelo", "Piel", "Color"] + [f"#{c['punto']}" for c in columnas] + ["Total"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        configurar_tabla_excel(self.table)
        self.table.setRowCount(len(detalle))
        for i, d in enumerate(detalle):
            por_talla = {int(t["punto_id"]): int(t.get("pares", 0)) for t in d.get("puntos", [])}
            self.table.setItem(i, 0, QTableWidgetItem(d.get("modelo", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("piel", "") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(d.get("color", "") or ""))
            total = 0
            for j, c in enumerate(columnas):
                pares = por_talla.get(int(c["punto_id"]), 0)
                total += pares
                self.table.setItem(i, 3 + j, QTableWidgetItem(str(pares or "")))
            self.table.setItem(i, 3 + n, QTableWidgetItem(str(total)))
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnPrimary")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)
