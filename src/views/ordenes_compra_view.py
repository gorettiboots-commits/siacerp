from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.components.notificacion_flotante import notificar_flotante
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

        self.btn_factura = QPushButton("Ingresar Factura")
        self.btn_factura.setObjectName("btnPrimary")
        self.btn_factura.clicked.connect(self._nueva_factura)

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

        self.vista = ComplexGrid()
        self.vista.set_columnas([
            {"key": "folio", "titulo": "Folio", "ancho": 110},
            {"key": "tipo", "titulo": "Tipo", "ancho": 120},
            {"key": "proveedores", "titulo": "Proveedor", "ancho": 220},
            {"key": "fecha_emision", "titulo": "Fecha", "ancho": 110},
            {"key": "total", "titulo": "Total", "ancho": 110, "tipo": "numero"},
            {"key": "estatus", "titulo": "Estatus", "ancho": 130},
        ])
        self.vista.set_renderers(
            fila=self._fila_orden,
            claves=self._claves_orden,
            estilo=self._estilo_orden,
            tarjeta=self._tarjeta_orden,
            lista=self._lista_orden,
        )
        self.vista.set_buscador_visible(False)
        self.vista.set_exportar_visible(False)
        self.vista.doubleClicked.connect(self._ver_orden)
        layout.addWidget(self.vista)

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

        self.grid_prov = ComplexGrid()
        self.grid_prov.set_columnas([
            {"key": "rfc", "titulo": "RFC", "ancho": 120},
            {"key": "nombre", "titulo": "Nombre", "ancho": 200},
            {"key": "nombre_comercial", "titulo": "Nombre Comercial", "ancho": 160},
            {"key": "telefono", "titulo": "Teléfono", "ancho": 110},
            {"key": "email", "titulo": "Email", "ancho": 180},
            {"key": "direccion", "titulo": "Dirección", "ancho": 220},
        ])
        self.grid_prov.set_buscador_visible(False)
        self.grid_prov.set_exportar_visible(False)
        self.grid_prov.doubleClicked.connect(self._editar_proveedor)
        layout.addWidget(self.grid_prov)

    def _load_ordenes(self) -> None:
        try:
            ordenes = self.controller.listar_ordenes()
            self.vista.set_datos(ordenes)
            self._load_proveedores()
        except Exception as e:
            print(f"Error: {e}")

    def _fila_orden(self, oc: dict) -> list[str]:
        tipo = oc.get("tipo", "orden")
        return [
            oc.get("folio", ""),
            "Factura" if tipo == "factura" else "Orden de Compra",
            oc.get("proveedores", ""),
            oc.get("fecha_emision", ""),
            f"${oc.get('total', 0):.2f}",
            oc.get("estatus", "").replace("_", " ").capitalize(),
        ]

    def _claves_orden(self, oc: dict) -> list:
        return [
            oc.get("folio", ""),
            oc.get("tipo", "orden"),
            (oc.get("proveedores", "") or "").lower(),
            oc.get("fecha_emision", "") or "",
            float(oc.get("total", 0) or 0),
            oc.get("estatus", ""),
        ]

    def _estilo_orden(self, oc: dict, item, col: int) -> None:
        tipo = oc.get("tipo", "orden")
        estatus = oc.get("estatus", "")
        if tipo == "factura" or estatus == "recibida":
            item.setBackground(QColor("#daf2d0"))
        if col == 5:
            if "recibida" in estatus:
                item.setForeground(Qt.darkGreen if estatus == "recibida" else Qt.darkYellow)
            elif estatus == "cancelada":
                item.setForeground(Qt.red)

    def _tarjeta_orden(self, oc: dict) -> dict:
        est = oc.get("estatus", "").replace("_", " ").capitalize()
        return {
            "tile": "oc",
            "titulo": oc.get("folio", ""),
            "subtitulo": oc.get("proveedores", ""),
            "badge": f"{est} · ${oc.get('total', 0):.2f}",
        }

    def _lista_orden(self, oc: dict) -> tuple:
        return (
            oc.get("folio", ""),
            f"{oc.get('proveedores', '')} · {oc.get('fecha_emision', '')} · ${oc.get('total', 0):.2f}",
        )

    def _load_proveedores(self) -> None:
        try:
            proveedores = self.controller.listar_proveedores()
            self.grid_prov.set_datos(proveedores)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ordenes()
            return
        try:
            resultados = self.controller.buscar_ordenes(texto)
            self.vista.set_datos(resultados)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_proveedores(self, texto: str) -> None:
        if not texto.strip():
            self._load_proveedores()
            return
        try:
            resultados = self.controller.buscar_proveedores(texto)
            self.grid_prov.set_datos(resultados)
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_orden(self) -> None:
        dlg = DialogOrdenCompra(self.controller)
        if dlg.exec():
            self._load_ordenes()

    def _nueva_factura(self) -> None:
        dlg = DialogOrdenCompra(self.controller, tipo="factura")
        if dlg.exec():
            self._load_ordenes()

    def _ver_orden(self) -> None:
        oc = self.vista.registro_seleccionado()
        if not oc:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        dlg = DialogVerOrden(self.controller, oc["id"])
        dlg.exec()

    def _recibir_orden(self) -> None:
        oc = self.vista.registro_seleccionado()
        if not oc:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        if oc.get("tipo") == "factura":
            QMessageBox.warning(self, "Estatus", "Las facturas no se reciben en inventario.")
            return
        estatus = oc.get("estatus", "")
        if "recibida" in estatus:
            QMessageBox.warning(self, "Estatus", "Esta orden ya fue recibida.")
            return
        if estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "No se puede recibir una orden cancelada.")
            return
        dlg = DialogRecibirOrden(self.controller, oc["id"])
        if dlg.exec():
            notificar_flotante("Orden recibida. Stock actualizado.",
                               tipo="success", titulo="Éxito", host=self)
            self._load_ordenes()

    def _cancelar_orden(self) -> None:
        oc = self.vista.registro_seleccionado()
        if not oc:
            QMessageBox.information(self, "Seleccionar", "Seleccione una orden.")
            return
        estatus = oc.get("estatus", "")
        if "recibida" in estatus or estatus == "cancelada":
            QMessageBox.warning(self, "Estatus", "Solo se pueden cancelar órdenes pendientes.")
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Cancelar '{oc['folio']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.cancelar_orden(oc["id"])
            self._load_ordenes()

    def _exportar(self) -> None:
        oc = self.vista.registro_seleccionado()
        if not oc:
            path = export_table_to_excel(self.vista.table, "Ordenes_Compra", self)
        else:
            datos = self.controller.obtener_orden(oc["id"])
            detalle = self.controller.obtener_detalle_orden(oc["id"])
            path = export_orden_compra_excel(datos, detalle, self)
        if path:
            notificar_flotante(f"Excel guardado en:\n{path}",
                               tipo="success", titulo="Exportado", host=self)

    def _imprimir(self) -> None:
        oc = self.vista.registro_seleccionado()
        if not oc:
            print_table(self.vista.table, "Ordenes_Compra", self)
        else:
            datos = self.controller.obtener_orden(oc["id"])
            detalle = self.controller.obtener_detalle_orden(oc["id"])
            print_orden_compra(datos, detalle, self)

    def _exportar_proveedores(self) -> None:
        path = export_table_to_excel(self.grid_prov.table, "Proveedores", self)
        if path:
            notificar_flotante(f"Excel guardado en:\n{path}",
                               tipo="success", titulo="Exportado", host=self)

    def _gestionar_proveedores(self) -> None:
        self.tabs.setCurrentIndex(1)

    def _nuevo_proveedor(self) -> None:
        dlg = DialogProveedor(self.controller)
        if dlg.exec():
            self._load_proveedores()

    def _editar_proveedor(self) -> None:
        prov = self.grid_prov.registro_seleccionado()
        if not prov:
            QMessageBox.information(self, "Seleccionar", "Seleccione un proveedor.")
            return
        dlg = DialogProveedor(self.controller, prov["id"])
        if dlg.exec():
            self._load_proveedores()

    def _desactivar_proveedor(self) -> None:
        prov = self.grid_prov.registro_seleccionado()
        if not prov:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{prov['nombre']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_proveedor(prov["id"])
            self._load_proveedores()
