from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.models.accesos_model import tiene
from src.utils.export_utils import export_orden_compra_excel, print_orden_compra
from src.views.dialogs import DialogOrdenCompra, DialogProveedor, DialogRecibirOrden, DialogVerOrden
from src.views.table_widget import GorettiTable


def _tipo_documento(tipo: str) -> str:
    if tipo == "factura":
        return "Factura"
    if tipo == "remision":
        return "Remisión"
    return "Orden de Compra"


class OrdenesCompraView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = OrdenesCompraController()
        self._setup_ui()
        self._load_ordenes()

    def set_permisos(self, permisos) -> None:
        self.btn_nueva.setEnabled(tiene(permisos, "ordenes_compra", "crear"))
        self.btn_factura.setEnabled(tiene(permisos, "ordenes_compra", "crear"))
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

        self.btn_factura = QPushButton("Ingresar Inventario")
        self.btn_factura.setObjectName("btnPrimary")
        self.btn_factura.clicked.connect(self._ingresar_inventario)

        self.btn_proveedor = QPushButton("Proveedores")
        self.btn_proveedor.setObjectName("btnSecondary")
        self.btn_proveedor.clicked.connect(self._gestionar_proveedores)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_proveedor)
        hlayout.addWidget(self.btn_factura)
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

        self.table = GorettiTable(
            columns=[
                {"key": "folio", "label": "Folio", "width": 130},
                {"key": "tipo", "label": "Tipo", "width": 130},
                {"key": "proveedores", "label": "Proveedor", "stretch": True},
                {"key": "fecha_emision", "label": "Fecha", "width": 170},
                {"key": "total", "label": "Total", "width": 120, "align": "right"},
                {"key": "estatus", "label": "Estatus", "width": 130},
            ],
            id_key="id",
            background_fn=self._color_fila_orden,
            foreground_fn=self._color_estatus,
            show_mode_selector=True,
        )
        self.table.recordDoubleClicked.connect(self._ver_orden)
        self.table.set_group_options([("Tipo", "tipo"), ("Estatus", "estatus")])
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

        self.table_prov = GorettiTable(
            columns=[
                {"key": "rfc", "label": "RFC", "width": 150},
                {"key": "nombre", "label": "Nombre", "stretch": True},
                {"key": "nombre_comercial", "label": "Nombre Comercial", "width": 170},
                {"key": "telefono", "label": "Teléfono", "width": 120},
                {"key": "email", "label": "Email", "width": 180},
                {"key": "direccion", "label": "Dirección", "width": 220},
            ],
            id_key="id",
        )
        self.table_prov.recordDoubleClicked.connect(self._editar_proveedor)
        layout.addWidget(self.table_prov)

    def _color_fila_orden(self, record: dict) -> QColor | None:
        if record.get("_tipo_raw") == "factura" or record.get("estatus") == "Recibida":
            return QColor("#daf2d0")
        return None

    def _color_estatus(self, record: dict, key: str) -> QColor | None:
        if key != "estatus":
            return None
        est = record.get("estatus", "")
        if "Recibida" in est:
            return Qt.darkGreen if est == "Recibida" else Qt.darkYellow
        if est == "Cancelada":
            return Qt.red
        return None

    def _load_ordenes(self) -> None:
        try:
            ordenes = self.controller.listar_ordenes()
            self.table.set_records([self._fila_orden(oc) for oc in ordenes])
            self._load_proveedores()
        except Exception as e:
            print(f"Error: {e}")

    def _fila_orden(self, oc: dict) -> dict:
        return {
            "id": oc.get("id"),
            "folio": oc.get("folio", ""),
            "tipo": _tipo_documento(oc.get("tipo", "orden")),
            "_tipo_raw": oc.get("tipo", "orden"),
            "proveedores": oc.get("proveedores", ""),
            "fecha_emision": oc.get("fecha_emision", ""),
            "total": f"${oc.get('total', 0):.2f}",
            "estatus": oc.get("estatus", "").replace("_", " ").capitalize(),
        }

    def _load_proveedores(self) -> None:
        try:
            proveedores = self.controller.listar_proveedores()
            self.table_prov.set_records(proveedores)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ordenes()
            return
        try:
            resultados = self.controller.buscar_ordenes(texto)
            self.table.set_records([self._fila_orden(oc) for oc in resultados])
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_proveedores(self, texto: str) -> None:
        if not texto.strip():
            self._load_proveedores()
            return
        try:
            resultados = self.controller.buscar_proveedores(texto)
            self.table_prov.set_records(resultados)
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_orden(self) -> None:
        dlg = DialogOrdenCompra(self.controller)
        if dlg.exec():
            self._load_ordenes()

    def _nueva_factura(self) -> None:
        self._ingresar_inventario()

    def _ingresar_inventario(self) -> None:
        opcion, ok = QInputDialog.getItem(
            self, "Ingresar Inventario", "Tipo de documento de ingreso:",
            ["Factura", "Remisión"], 0, False)
        if not ok:
            return
        tipo = "factura" if opcion == "Factura" else "remision"
        dlg = DialogOrdenCompra(self.controller, tipo=tipo)
        if dlg.exec():
            self._load_ordenes()

    def _ver_orden(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        dlg = DialogVerOrden(self.controller, int(record["id"]))
        dlg.exec()

    def _recibir_orden(self) -> None:
        record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        if record["tipo"] in ("Factura", "Remisión"):
            QMessageBox.warning(self, "Estatus",
                                "Los documentos de ingreso (factura/remisión) ya se registran en inventario.")
            return
        estatus = record["estatus"].lower()
        if "recibida" in estatus:
            QMessageBox.warning(self, "Estatus", "Esta orden ya fue recibida.")
            return
        if estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "No se puede recibir una orden cancelada.")
            return
        dlg = DialogRecibirOrden(self.controller, int(record["id"]))
        if dlg.exec():
            QMessageBox.information(self, "Éxito", "Orden recibida. Stock actualizado.")
            self._load_ordenes()

    def _cancelar_orden(self) -> None:
        record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        estatus = record["estatus"].lower()
        if "recibida" in estatus or estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "Solo se pueden cancelar órdenes pendientes.")
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Cancelar '{record['folio']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.cancelar_orden(int(record["id"]))
            self._load_ordenes()

    def _exportar(self) -> None:
        record = self.table.current_record()
        if record is None:
            path = self.table.exportar_excel("Ordenes_Compra", self)
        else:
            oc_id = int(record["id"])
            datos = self.controller.obtener_orden(oc_id)
            detalle = self.controller.obtener_detalle_orden(oc_id)
            path = export_orden_compra_excel(datos, detalle, self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir(self) -> None:
        record = self.table.current_record()
        if record is None:
            self.table.imprimir("Ordenes_Compra", self)
        else:
            oc_id = int(record["id"])
            datos = self.controller.obtener_orden(oc_id)
            detalle = self.controller.obtener_detalle_orden(oc_id)
            print_orden_compra(datos, detalle, self)

    def _exportar_proveedores(self) -> None:
        path = self.table_prov.exportar_excel("Proveedores", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _gestionar_proveedores(self) -> None:
        self.tabs.setCurrentIndex(1)

    def _nuevo_proveedor(self) -> None:
        dlg = DialogProveedor(self.controller)
        if dlg.exec():
            self._load_proveedores()

    def _editar_proveedor(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table_prov.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un proveedor.")
            return
        dlg = DialogProveedor(self.controller, int(record["id"]))
        if dlg.exec():
            self._load_proveedores()

    def _desactivar_proveedor(self) -> None:
        record = self.table_prov.current_record()
        if record is None:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{record['nombre']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_proveedor(int(record["id"]))
            self._load_proveedores()
