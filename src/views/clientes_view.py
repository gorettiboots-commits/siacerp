from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

from src.components.grid_hibrido import GridHibrido
from src.components.date_picker import DatePicker
from src.components.notificacion_flotante import notificar_flotante
from src.components.tallas_matrix import MatrizTallasDialog, MatrizTallasWidget
from src.controllers.clientes_controller import ClientesController
from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.icons import mono_icon
from src.utils.table_utils import configurar_tabla_excel
from src.utils.ui_helpers import load_styles
from src.views.programar_pedido_dialog import ProgramarPedidoDialog


_ESTATUS = {
    "pendiente": "Pendiente",
    "programado": "Programado",
    "surtido": "Surtido",
    "cancelado": "Cancelado",
}


def _fmt_estatus(estatus: str) -> str:
    return _ESTATUS.get(estatus, estatus.replace("_", " ").capitalize())


def _aplicar_estilo_forms(widget: QWidget) -> None:
    """Aplica el tema clásico Windows Forms (estilos.qss) al widget."""
    widget.setStyleSheet(load_styles())


class ClientesView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ClientesController()
        self._permiso_editar = True
        self._permiso_programar = True
        _aplicar_estilo_forms(self)
        self._setup_ui()
        self._load_pedidos()
        self._load_clientes()

    def set_permisos(self, permisos) -> None:
        self._permiso_editar = tiene(permisos, "clientes", "editar")
        self._permiso_programar = tiene(permisos, "programacion", "editar")
        self.vista.establecer_boton_modulo(
            "nuevo_pedido", tiene(permisos, "clientes", "crear"))
        self.grid_cli.establecer_boton_modulo(
            "nuevo_cliente", tiene(permisos, "clientes", "crear"))

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

        hlayout.addLayout(title_col)
        hlayout.addStretch()

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

        self.vista = GridHibrido()
        self.vista.agregar_boton_toolbar(
            "nuevo_pedido", "+ Nuevo Pedido", "mas", "#ffffff",
            self._nuevo_pedido)
        self.vista.set_columnas([
            {"key": "folio", "titulo": "Folio", "ancho": 110},
            {"key": "cliente_nombre", "titulo": "Cliente", "ancho": 220},
            {"key": "fecha_pedido", "titulo": "Fecha Pedido", "ancho": 110},
            {"key": "fecha_programado", "titulo": "Fecha Programado", "ancho": 120},
            {"key": "total_pares", "titulo": "Pares", "ancho": 80, "tipo": "numero"},
            {"key": "estatus", "titulo": "Estatus", "ancho": 120},
        ])
        self.vista.set_renderers(fila=self._fila_pedido, claves=self._claves_pedido,
                                 estilo=self._estilo_pedido)
        self.vista.set_acciones([
            {"texto": "Programar", "icono": "programacion", "color": "#0d9488",
             "habilitado": lambda rec: self._permiso_programar
             and rec.get("estatus") not in ("cancelado", "surtido"),
             "callback": self._programar_pedido},
            {"texto": "Editar", "icono": "editar", "color": "#2A5FB0",
             "habilitado": lambda rec: self._permiso_editar,
             "callback": self._editar_pedido},
            {"texto": "Cancelar", "icono": "eliminar", "color": "#C00000",
             "habilitado": lambda rec: self._permiso_editar
             and rec.get("estatus") not in ("cancelado", "surtido"),
             "callback": self._cancelar_pedido},
        ])
        self.vista.doubleClicked.connect(self._ver_pedido)
        layout.addWidget(self.vista)

    def _setup_tab_clientes(self) -> None:
        layout = QVBoxLayout(self.tab_clientes)
        layout.setContentsMargins(0, 8, 0, 0)

        self.grid_cli = GridHibrido()
        self.grid_cli.agregar_boton_toolbar(
            "nuevo_cliente", "+ Nuevo Cliente", "mas", "#ffffff",
            self._nuevo_cliente)
        self.grid_cli.set_columnas([
            {"key": "rfc", "titulo": "RFC", "ancho": 130},
            {"key": "nombre", "titulo": "Nombre", "ancho": 200},
            {"key": "nombre_comercial", "titulo": "Nombre Comercial", "ancho": 170},
            {"key": "telefono", "titulo": "Teléfono", "ancho": 110},
            {"key": "email", "titulo": "Email", "ancho": 180},
            {"key": "direccion", "titulo": "Dirección", "ancho": 220},
        ])
        self.grid_cli.set_renderers(estilo=self._estilo_cliente)
        self.grid_cli.set_acciones([
            {"texto": "Editar", "icono": "editar", "color": "#2A5FB0",
             "habilitado": lambda rec: self._permiso_editar,
             "callback": self._editar_cliente_rec},
            {"texto": lambda rec: "Desactivar" if rec.get("activo") else "Activar",
             "icono": "toggle", "color": "#C00000",
             "habilitado": lambda rec: self._permiso_editar,
             "callback": self._alternar_activo_cliente},
        ])
        self.grid_cli.doubleClicked.connect(self._editar_cliente)
        layout.addWidget(self.grid_cli)

    # ---- Carga y búsqueda ----

    def _load_pedidos(self) -> None:
        try:
            pedidos = self.controller.listar_pedidos()
            self.vista.set_datos(pedidos)
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    def _fila_pedido(p: dict) -> list[str]:
        return [
            p.get("folio", ""),
            p.get("cliente_nombre", ""),
            p.get("fecha_pedido", ""),
            p.get("fecha_programado", "") or "",
            str(p.get("total_pares", 0)),
            _fmt_estatus(p.get("estatus", "")),
        ]

    @staticmethod
    def _claves_pedido(p: dict) -> list:
        return [
            p.get("folio", ""),
            (p.get("cliente_nombre", "") or "").lower(),
            p.get("fecha_pedido", ""),
            p.get("fecha_programado", "") or "",
            float(p.get("total_pares", 0) or 0),
            p.get("estatus", ""),
        ]

    @staticmethod
    def _estilo_pedido(p: dict, item, col: int) -> None:
        if col != 5:
            return
        est = p.get("estatus", "")
        if est == "surtido":
            item.setForeground(Qt.darkGreen)
        elif est == "programado":
            item.setForeground(Qt.darkYellow)
        elif est == "cancelado":
            item.setForeground(Qt.red)

    def _load_clientes(self) -> None:
        try:
            clientes = self.controller.listar_clientes(solo_activos=False)
            self.grid_cli.set_datos(clientes)
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    def _estilo_cliente(c: dict, item, col: int) -> None:
        if not c.get("activo"):
            item.setForeground(Qt.gray)

    # ---- Acciones de pedidos ----

    def _nuevo_pedido(self) -> None:
        dlg = _DialogPedidoCliente(self.controller)
        if dlg.exec():
            self._load_pedidos()

    def _ver_pedido(self) -> None:
        rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        dlg = _DialogVerPedido(self.controller, rec["id"])
        dlg.exec()

    def _editar_pedido(self, rec=None) -> None:
        if rec is None:
            rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        dlg = _DialogPedidoCliente(self.controller, rec["id"])
        if dlg.exec():
            self._load_pedidos()

    def _cancelar_pedido(self, rec: dict | None = None) -> None:
        if rec is None:
            rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        if QMessageBox.question(
                self, "Cancelar pedido",
                f"¿Cancelar el pedido {rec.get('folio', '')}?") != QMessageBox.Yes:
            return
        try:
            self.controller.cancelar_pedido(rec["id"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo cancelar: {e}")
        self._load_pedidos()

    def _programar_pedido(self, rec: dict | None = None) -> None:
        if rec is None:
            rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        dlg = ProgramarPedidoDialog(self.controller, ProgramacionController(),
                                    rec["id"], self)
        if dlg.exec():
            self._load_pedidos()
            folios = ", ".join(dlg.folios_generados)
            notificar_flotante(
                f"Se generaron los folios de programación: {folios}",
                tipo="success", titulo="Programado", host=self)

    # ---- Acciones de clientes ----

    def _nuevo_cliente(self) -> None:
        dlg = _DialogCliente(self.controller)
        if dlg.exec():
            self._load_clientes()

    def _editar_cliente(self) -> None:
        rec = self.grid_cli.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un cliente.")
            return
        dlg = _DialogCliente(self.controller, rec["id"])
        if dlg.exec():
            self._load_clientes()

    def _editar_cliente_rec(self, rec: dict) -> None:
        dlg = _DialogCliente(self.controller, rec["id"])
        if dlg.exec():
            self._load_clientes()

    def _alternar_activo_cliente(self, rec: dict) -> None:
        if rec.get("activo"):
            if QMessageBox.question(
                    self, "Desactivar cliente",
                    f"¿Desactivar al cliente '{rec.get('nombre', '')}'?") \
                    != QMessageBox.Yes:
                return
            self.controller.desactivar_cliente(rec["id"])
        else:
            self.controller.reactivar_cliente(rec["id"])
        self._load_clientes()


class _DialogCliente(QDialog):
    def __init__(self, controller: ClientesController, cliente_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.cliente_id = cliente_id
        self.setWindowTitle("Nuevo Cliente" if cliente_id is None else "Editar Cliente")
        self.setMinimumWidth(420)
        self.setModal(True)
        _aplicar_estilo_forms(self)
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
        self.txt_nombre.setFocus()

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
        rfc = self.txt_rfc.text().strip().upper()
        email = self.txt_email.text().strip()
        if email and "@" not in email:
            QMessageBox.warning(self, "Datos inválidos",
                                "El correo electrónico no parece válido.")
            return
        try:
            if self.cliente_id:
                self.controller.actualizar_cliente(
                    self.cliente_id, nombre, rfc,
                    self.txt_comercial.text().strip(), self.txt_telefono.text().strip(),
                    email, self.txt_direccion.text().strip())
            else:
                self.controller.crear_cliente(
                    nombre, rfc, self.txt_comercial.text().strip(),
                    self.txt_telefono.text().strip(), email,
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
        _aplicar_estilo_forms(self)
        self._puntos_fila: dict[int, dict[int, int]] = {}
        self._prog = ProgramacionController()
        self._tiene_programacion = False
        if pedido_id:
            self._tiene_programacion = \
                self._prog.pares_programados_pedido(pedido_id) > 0
        self._setup_ui()
        if pedido_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        self.cmb_cliente = QComboBox()
        for c in self.controller.listar_clientes():
            self.cmb_cliente.addItem(c["nombre"], c["id"])

        self.txt_folio = QLineEdit()
        self.txt_folio.setText(self.controller.siguiente_folio())
        self.txt_folio.setReadOnly(True)

        self.txt_folio_pedido = QLineEdit()
        self.txt_folio_pedido.setPlaceholderText("Folio de pedido del cliente (opcional)")

        self.dte_pedido = DatePicker()
        self.dte_programado = DatePicker()
        self.chk_sin_programar = QCheckBox("Sin fecha programada")
        self.chk_sin_programar.toggled.connect(
            lambda on: self.dte_programado.setEnabled(not on))

        self.cmb_estatus = QComboBox()
        for k in ("pendiente", "programado", "surtido"):
            if k == "programado" and not self._tiene_programacion:
                continue
            self.cmb_estatus.addItem(_ESTATUS[k], k)

        self.txt_suela = QLineEdit()
        self.txt_suela.setPlaceholderText("Ej: PIEL CARA")

        self.txt_horma = QLineEdit()
        self.txt_horma.setPlaceholderText("Ej: H-7")

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")
        self.txt_obs.setMaximumHeight(60)

        grp_datos = QGroupBox("Datos del Pedido")
        grid_datos = QGridLayout(grp_datos)
        grid_datos.setHorizontalSpacing(16)
        grid_datos.setVerticalSpacing(10)
        grid_datos.setColumnStretch(1, 1)
        grid_datos.setColumnStretch(3, 1)

        grid_datos.addWidget(QLabel("Cliente:"), 0, 0)
        grid_datos.addWidget(self.cmb_cliente, 0, 1)
        grid_datos.addWidget(QLabel("Folio:"), 0, 2)
        grid_datos.addWidget(self.txt_folio, 0, 3)

        grid_datos.addWidget(QLabel("Folio Pedido:"), 1, 0)
        grid_datos.addWidget(self.txt_folio_pedido, 1, 1)
        grid_datos.addWidget(QLabel("Estatus:"), 1, 2)
        grid_datos.addWidget(self.cmb_estatus, 1, 3)

        grid_datos.addWidget(QLabel("Fecha pedido:"), 2, 0)
        grid_datos.addWidget(self.dte_pedido, 2, 1)
        grid_datos.addWidget(QLabel("Fecha programado:"), 2, 2)
        grid_datos.addWidget(self.dte_programado, 2, 3)

        grid_datos.addWidget(self.chk_sin_programar, 3, 0, 1, 4)
        layout.addWidget(grp_datos)

        grp_ficha = QGroupBox("Ficha Técnica")
        form_ficha = QFormLayout(grp_ficha)
        form_ficha.setSpacing(10)
        form_ficha.addRow("Suela:", self.txt_suela)
        form_ficha.addRow("Horma:", self.txt_horma)
        form_ficha.addRow("Observaciones:", self.txt_obs)
        layout.addWidget(grp_ficha)

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
        self.lbl_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #1F4E79;")

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
        self.txt_folio_pedido.setText(pedido.get("folio_pedido", "") or "")
        self.txt_suela.setText(pedido.get("suela", "") or "")
        self.txt_horma.setText(pedido.get("horma", "") or "")
        self.dte_pedido.establecer_fecha_bd(pedido.get("fecha_pedido", "") or "")
        prog = pedido.get("fecha_programado")
        if prog:
            self.dte_programado.establecer_fecha_bd(prog)
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
        btn = QToolButton()
        btn.setObjectName("btnFilaIcono")
        btn.setIcon(mono_icon("tabla", 16, "#4f46e5"))
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip("Configurar Tallas")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._on_click_configurar_tallas)
        self.table_detalle.setCellWidget(row, 3, btn)
        self.table_detalle.setItem(row, 4, QTableWidgetItem("0"))
        self.table_detalle.setItem(row, 5, QTableWidgetItem("0"))

    def _on_click_configurar_tallas(self) -> None:
        btn = self.sender()
        if not btn:
            return
        for r in range(self.table_detalle.rowCount()):
            if self.table_detalle.cellWidget(r, 3) is btn:
                self._configurar_tallas(r)
                break

    def _actualizar_boton_tallas(self, row: int) -> None:
        matriz = self._puntos_fila.get(row, {})
        total = sum(matriz.values())
        btn = self.table_detalle.cellWidget(row, 3)
        if btn:
            btn.setToolTip(f"Configurar Tallas ({total} pr)")
        item_pares = self.table_detalle.item(row, 4)
        if item_pares:
            item_pares.setText(str(total))
        self._recalcular_total()

    def _agregar_linea(self) -> None:
        dlg = _DialogLineaPedido(self.controller, self)
        if dlg.exec() == QDialog.Accepted:
            row = self.table_detalle.rowCount()
            self.table_detalle.insertRow(row)
            self._puntos_fila[row] = dict(dlg.pares)
            self._set_fila(row, dlg.modelo, dlg.piel, dlg.color)
            self._actualizar_boton_tallas(row)

    def _configurar_tallas(self, row: int) -> None:
        puntos = self.controller.listar_puntos()
        id_por_clave = {}
        for p in puntos:
            id_por_clave[str(p["punto"])] = p["id"]
            id_por_clave[str(p["id"])] = p["id"]
        actual = self._puntos_fila.get(row, {})
        inicial = {p["punto"]: int(actual.get(p["id"], 0) or 0) for p in puntos}
        dlg = MatrizTallasDialog(puntos=puntos, titulo="TALLAS DEL PEDIDO",
                                 parent=self)
        dlg.establecer_valores(inicial)
        if dlg.exec() == QDialog.Accepted:
            valores = dlg.obtener_valores()
            nueva = {}
            for t_str, n in valores.items():
                if int(n or 0) > 0 and str(t_str) in id_por_clave:
                    nueva[id_por_clave[str(t_str)]] = int(n)
            self._puntos_fila[row] = nueva
            self._actualizar_boton_tallas(row)

    def _quitar_linea(self) -> None:
        row = self.table_detalle.currentRow()
        if row >= 0:
            # Guardar el dict antes de eliminar la fila
            previo = dict(self._puntos_fila)
            total_prev = self.table_detalle.rowCount()
            self.table_detalle.removeRow(row)
            # Reindexar: copia las entradas omitiendo 'row', reasignando indices 0..n-2
            nuevos_puntos = {}
            idx = 0
            for r in range(total_prev):
                if r == row:
                    continue
                if r in previo:
                    nuevos_puntos[idx] = previo[r]
                idx += 1
            self._puntos_fila = nuevos_puntos
            self._recalcular_total()

    def _recalcular_total(self) -> None:
        total = sum(sum(m.values()) for m in self._puntos_fila.values())
        self.lbl_total.setText(f"Total de pares: {total}")

    def _fecha_programado(self) -> str:
        if self.chk_sin_programar.isChecked():
            return ""
        return self.dte_programado.fecha_bd()

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
        fecha_pedido = self.dte_pedido.fecha_bd()
        fecha_programado = self._fecha_programado()
        estatus = self.cmb_estatus.currentData()
        if estatus == "programado" and not self._tiene_programacion:
            QMessageBox.warning(
                self, "Estatus no permitido",
                "No se puede marcar 'Programado' a mano. Primero programe el "
                "pedido en una semana para generar sus folios de programación.")
            return
        obs = self.txt_obs.toPlainText().strip()
        folio_pedido = self.txt_folio_pedido.text().strip()
        suela = self.txt_suela.text().strip()
        horma = self.txt_horma.text().strip()
        try:
            if self.pedido_id:
                self.controller.actualizar_pedido(
                    self.pedido_id, cliente_id, fecha_pedido, fecha_programado,
                    estatus, obs, detalle, folio_pedido, suela, horma)
            else:
                self.controller.crear_pedido(
                    folio, cliente_id, fecha_pedido, fecha_programado,
                    estatus, obs, detalle, folio_pedido, suela, horma)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo guardar:\n{e}")
            return
        self.accept()


class _DialogLineaPedido(QDialog):
    def __init__(self, controller: ClientesController | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self.controller = controller or ClientesController()
        self.setWindowTitle("Agregar Línea al Pedido")
        self.setMinimumSize(700, 560)
        self.setModal(True)
        _aplicar_estilo_forms(self)
        self.modelo = ""
        self.piel = ""
        self.color = ""
        self.pares: dict[int, int] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)
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

        self.puntos = self.controller.listar_puntos()
        self.matriz = MatrizTallasWidget(
            puntos=self.puntos, titulo="PARES POR TALLA DE ESTA LÍNEA",
            parent=self)
        layout.addWidget(self.matriz, 1)

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
        self.txt_modelo.setFocus()

    def _save(self) -> None:
        modelo = self.txt_modelo.text().strip()
        if not modelo:
            QMessageBox.warning(self, "Campo requerido",
                                "El modelo es obligatorio.")
            return
        valores = self.matriz.obtener_valores()
        self.pares = {}
        for p in self.puntos:
            # obtener_valores() puede indexar por str(punto) o str(id)
            # según cómo se construyó el widget: intentamos ambas claves
            pares = int(valores.get(str(p["punto"]), 0) or 0)
            if pares == 0:
                pares = int(valores.get(str(p["id"]), 0) or 0)
            if pares > 0:
                self.pares[p["id"]] = pares
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
        _aplicar_estilo_forms(self)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        pedido = self.controller.obtener_pedido(self.pedido_id)
        detalle = self.controller.obtener_detalle_pedido(self.pedido_id)

        info = QLabel()
        info.setWordWrap(True)
        info.setStyleSheet("color: #000000; font-size: 12px; padding: 10px;"
                       "background: #FFFFE1; border: 1px solid #C0C0C0;")
        lineas = []
        if pedido:
            lineas.append(
                f"<b>{pedido.get('folio', '')}</b> — {pedido.get('cliente_nombre', '')} "
                f"({_fmt_estatus(pedido.get('estatus', ''))})")
            if pedido.get("folio_pedido"):
                lineas.append(f"Folio pedido: {pedido.get('folio_pedido')}")
            if pedido.get("suela") or pedido.get("horma"):
                lineas.append(f"Suela: {pedido.get('suela') or '—'} | "
                              f"Horma: {pedido.get('horma') or '—'}")
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
        fm = self.table.fontMetrics()
        for j in range(n):
            self.table.setColumnWidth(3 + j, fm.horizontalAdvance(headers[3 + j]) + 16)
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
