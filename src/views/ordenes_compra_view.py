from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.models.accesos_model import tiene
from src.utils.export_utils import (
    export_orden_compra_excel, export_table_to_excel, print_orden_compra, print_table,
)
from src.views.dialogs import DialogOrdenCompra, DialogProveedor, DialogRecibirOrden, DialogVerOrden


class OrdenesCompraView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = OrdenesCompraController()
        self._setup_ui()
        self._load_ordenes()

    def set_permisos(self, permisos) -> None:
        self.btn_nueva.setEnabled(tiene(permisos, "ordenes_compra", "crear"))
        self.btn_recibir.setEnabled(tiene(permisos, "ordenes_compra", "crear"))
        self.btn_cancelar.setEnabled(tiene(permisos, "ordenes_compra", "eliminar"))
        self.btn_export.setEnabled(tiene(permisos, "ordenes_compra", "exportar"))
        self.btn_print.setEnabled(tiene(permisos, "ordenes_compra", "exportar"))
        self.btn_nuevo_prov.setEnabled(tiene(permisos, "ordenes_compra", "crear"))
        self.btn_editar_prov.setEnabled(tiene(permisos, "ordenes_compra", "editar"))
        self.btn_desactivar_prov.setEnabled(tiene(permisos, "ordenes_compra", "eliminar"))
        self.btn_export_prov.setEnabled(tiene(permisos, "ordenes_compra", "exportar"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QFrame()
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel("Órdenes de Compra")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Gestión de compras, proveedores y recepción de insumos")
        subtitle.setObjectName("sectionSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.btn_nueva = QPushButton("+ Nueva Orden")
        self.btn_nueva.setObjectName("btnPrimary")
        self.btn_nueva.clicked.connect(self._nueva_orden)

        self.btn_proveedor = QPushButton("Proveedores")
        self.btn_proveedor.setObjectName("btnSecondary")
        self.btn_proveedor.clicked.connect(self._gestionar_proveedores)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_proveedor)
        hlayout.addWidget(self.btn_nueva)

        self.tabs = QTabWidget()
        self.tab_ordenes = QWidget()
        self.tab_proveedores = QWidget()
        self.tabs.addTab(self.tab_ordenes, "Órdenes")
        self.tabs.addTab(self.tab_proveedores, "Proveedores")
        self._setup_tab_ordenes()
        self._setup_tab_proveedores()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

    def _setup_tab_ordenes(self) -> None:
        layout = QVBoxLayout(self.tab_ordenes)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por folio, insumo o proveedor...")
        self.txt_buscar.setMinimumWidth(300)
        self.txt_buscar.textChanged.connect(self._buscar)

        btn_ver = QPushButton("Ver Detalle")
        btn_ver.setObjectName("btnSecondary")
        btn_ver.clicked.connect(self._ver_orden)

        self.btn_recibir = QPushButton("Recibir Orden")
        self.btn_recibir.setObjectName("btnSuccess")
        self.btn_recibir.clicked.connect(self._recibir_orden)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnDanger")
        self.btn_cancelar.clicked.connect(self._cancelar_orden)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.clicked.connect(self._exportar)

        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(self._imprimir)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self._load_ordenes)

        toolbar.addWidget(self.txt_buscar)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(btn_ver)
        toolbar.addWidget(self.btn_recibir)
        toolbar.addWidget(self.btn_cancelar)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_print)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Folio", "Proveedor", "Fecha", "Total", "Estatus", "ID"])
        self.table.setColumnHidden(5, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._ver_orden)
        layout.addWidget(self.table)

    def _setup_tab_proveedores(self) -> None:
        layout = QVBoxLayout(self.tab_proveedores)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.txt_buscar_prov = QLineEdit()
        self.txt_buscar_prov.setPlaceholderText("Buscar proveedor...")
        self.txt_buscar_prov.setMinimumWidth(300)
        self.txt_buscar_prov.textChanged.connect(self._buscar_proveedores)

        self.btn_nuevo_prov = QPushButton("+ Nuevo Proveedor")
        self.btn_nuevo_prov.setObjectName("btnPrimary")
        self.btn_nuevo_prov.clicked.connect(self._nuevo_proveedor)
        self.btn_editar_prov = QPushButton("Editar")
        self.btn_editar_prov.setObjectName("btnSecondary")
        self.btn_editar_prov.clicked.connect(self._editar_proveedor)
        self.btn_desactivar_prov = QPushButton("Desactivar")
        self.btn_desactivar_prov.setObjectName("btnDanger")
        self.btn_desactivar_prov.clicked.connect(self._desactivar_proveedor)
        self.btn_export_prov = QPushButton("Exportar Excel")
        self.btn_export_prov.setObjectName("btnPrimary")
        self.btn_export_prov.clicked.connect(self._exportar_proveedores)
        btn_refresh_prov = QPushButton("Actualizar")
        btn_refresh_prov.setObjectName("btnPrimary")
        btn_refresh_prov.clicked.connect(self._load_proveedores)

        toolbar.addWidget(self.txt_buscar_prov)
        toolbar.addWidget(btn_refresh_prov)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_nuevo_prov)
        toolbar.addWidget(self.btn_editar_prov)
        toolbar.addWidget(self.btn_desactivar_prov)
        toolbar.addWidget(self.btn_export_prov)
        layout.addLayout(toolbar)

        self.table_prov = QTableWidget()
        self.table_prov.setColumnCount(7)
        self.table_prov.setHorizontalHeaderLabels(
            ["RFC", "Nombre", "Nombre Comercial", "Teléfono", "Email", "Dirección", "ID"])
        self.table_prov.setColumnHidden(6, True)
        self.table_prov.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_prov.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_prov.setAlternatingRowColors(True)
        self.table_prov.horizontalHeader().setStretchLastSection(True)
        self.table_prov.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_prov.doubleClicked.connect(self._editar_proveedor)
        self.table_prov.setStyleSheet(self.table.styleSheet())
        layout.addWidget(self.table_prov)

    def _load_ordenes(self) -> None:
        try:
            ordenes = self.controller.listar_ordenes()
            self.table.setRowCount(len(ordenes))
            for i, oc in enumerate(ordenes):
                self.table.setItem(i, 0, QTableWidgetItem(oc.get("folio", "")))
                self.table.setItem(i, 1, QTableWidgetItem(oc.get("proveedores", "")))
                self.table.setItem(i, 2, QTableWidgetItem(oc.get("fecha_emision", "")))
                self.table.setItem(i, 3, QTableWidgetItem(f"${oc.get('total', 0):.2f}"))
                est = oc.get("estatus", "").replace("_", " ").capitalize()
                item_est = QTableWidgetItem(est)
                if "recibida" in oc.get("estatus", ""):
                    item_est.setForeground(Qt.darkGreen if est == "Recibida" else Qt.darkYellow)
                elif est == "Cancelada":
                    item_est.setForeground(Qt.red)
                self.table.setItem(i, 4, item_est)
                self.table.setItem(i, 5, QTableWidgetItem(str(oc.get("id", ""))))
            self._load_proveedores()
        except Exception as e:
            print(f"Error: {e}")

    def _load_proveedores(self) -> None:
        try:
            proveedores = self.controller.listar_proveedores()
            self.table_prov.setRowCount(len(proveedores))
            for i, p in enumerate(proveedores):
                self.table_prov.setItem(i, 0, QTableWidgetItem(p.get("rfc", "")))
                self.table_prov.setItem(i, 1, QTableWidgetItem(p.get("nombre", "")))
                self.table_prov.setItem(i, 2, QTableWidgetItem(p.get("nombre_comercial", "")))
                self.table_prov.setItem(i, 3, QTableWidgetItem(p.get("telefono", "")))
                self.table_prov.setItem(i, 4, QTableWidgetItem(p.get("email", "")))
                self.table_prov.setItem(i, 5, QTableWidgetItem(p.get("direccion", "")))
                self.table_prov.setItem(i, 6, QTableWidgetItem(str(p.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ordenes()
            return
        try:
            resultados = self.controller.buscar_ordenes(texto)
            self.table.setRowCount(len(resultados))
            for i, oc in enumerate(resultados):
                self.table.setItem(i, 0, QTableWidgetItem(oc.get("folio", "")))
                self.table.setItem(i, 1, QTableWidgetItem(oc.get("proveedores", "")))
                self.table.setItem(i, 2, QTableWidgetItem(oc.get("fecha_emision", "")))
                self.table.setItem(i, 3, QTableWidgetItem(f"${oc.get('total', 0):.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(oc.get("estatus", "").replace("_", " ").capitalize()))
                self.table.setItem(i, 5, QTableWidgetItem(str(oc.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_proveedores(self, texto: str) -> None:
        if not texto.strip():
            self._load_proveedores()
            return
        try:
            resultados = self.controller.buscar_proveedores(texto)
            self.table_prov.setRowCount(len(resultados))
            for i, p in enumerate(resultados):
                self.table_prov.setItem(i, 0, QTableWidgetItem(p.get("rfc", "")))
                self.table_prov.setItem(i, 1, QTableWidgetItem(p.get("nombre", "")))
                self.table_prov.setItem(i, 2, QTableWidgetItem(p.get("nombre_comercial", "")))
                self.table_prov.setItem(i, 3, QTableWidgetItem(p.get("telefono", "")))
                self.table_prov.setItem(i, 4, QTableWidgetItem(p.get("email", "")))
                self.table_prov.setItem(i, 5, QTableWidgetItem(p.get("direccion", "")))
                self.table_prov.setItem(i, 6, QTableWidgetItem(str(p.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_orden(self) -> None:
        dlg = DialogOrdenCompra(self.controller)
        if dlg.exec():
            self._load_ordenes()

    def _ver_orden(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        oc_id = int(self.table.item(row, 5).text())
        dlg = DialogVerOrden(self.controller, oc_id)
        dlg.exec()

    def _recibir_orden(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        estatus = self.table.item(row, 4).text().lower()
        if "recibida" in estatus:
            QMessageBox.warning(self, "Estatus", "Esta orden ya fue recibida.")
            return
        if estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "No se puede recibir una orden cancelada.")
            return
        oc_id = int(self.table.item(row, 5).text())
        dlg = DialogRecibirOrden(self.controller, oc_id)
        if dlg.exec():
            QMessageBox.information(self, "Éxito", "Orden recibida. Stock actualizado.")
            self._load_ordenes()

    def _cancelar_orden(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        estatus = self.table.item(row, 4).text().lower()
        if "recibida" in estatus or estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "Solo se pueden cancelar órdenes pendientes.")
            return
        folio = self.table.item(row, 0).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Cancelar orden '{folio}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            oc_id = int(self.table.item(row, 5).text())
            self.controller.cancelar_orden(oc_id)
            self._load_ordenes()

    def _exportar(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            path = export_table_to_excel(self.table, "Ordenes_Compra", self)
        else:
            oc_id = int(self.table.item(row, 5).text())
            datos = self.controller.obtener_orden(oc_id)
            detalle = self.controller.obtener_detalle_orden(oc_id)
            path = export_orden_compra_excel(datos, detalle, self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            print_table(self.table, "Ordenes_Compra", self)
        else:
            oc_id = int(self.table.item(row, 5).text())
            datos = self.controller.obtener_orden(oc_id)
            detalle = self.controller.obtener_detalle_orden(oc_id)
            print_orden_compra(datos, detalle, self)

    def _exportar_proveedores(self) -> None:
        path = export_table_to_excel(self.table_prov, "Proveedores", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _gestionar_proveedores(self) -> None:
        self.tabs.setCurrentIndex(1)

    def _nuevo_proveedor(self) -> None:
        dlg = DialogProveedor(self.controller)
        if dlg.exec():
            self._load_proveedores()

    def _editar_proveedor(self) -> None:
        row = self.table_prov.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un proveedor.")
            return
        proveedor_id = int(self.table_prov.item(row, 5).text())
        dlg = DialogProveedor(self.controller, proveedor_id)
        if dlg.exec():
            self._load_proveedores()

    def _desactivar_proveedor(self) -> None:
        row = self.table_prov.currentRow()
        if row < 0:
            return
        nombre = self.table_prov.item(row, 1).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            proveedor_id = int(self.table_prov.item(row, 5).text())
            self.controller.desactivar_proveedor(proveedor_id)
            self._load_proveedores()
