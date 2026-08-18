from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.components.tallas_matrix import MatrizTallasDialog
from src.controllers.clientes_controller import ClientesController
from src.controllers.programacion_controller import ProgramacionController
from src.models.accesos_model import tiene
from src.utils.table_utils import configurar_tabla_excel
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
        self._permiso_editar = True
        self._setup_ui()
        self._load_pedidos()
        self._load_clientes()

    def set_permisos(self, permisos) -> None:
        self._permiso_editar = tiene(permisos, "clientes", "editar")
        self.btn_nuevo_pedido.setEnabled(tiene(permisos, "clientes", "crear"))
        self.btn_programas.setEnabled(tiene(permisos, "programacion", "editar"))
        self.btn_nuevo_cli.setEnabled(tiene(permisos, "clientes", "crear"))

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

        self.btn_programas = QPushButton("Programas")
        self.btn_programas.setObjectName("btnPrimary")
        self.btn_programas.clicked.connect(self._programar_pedido)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_programas)
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

        self.vista = ComplexGrid()
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
            {"texto": "Editar", "icono": "editar", "color": "#4f46e5",
             "habilitado": lambda rec: self._permiso_editar,
             "callback": self._editar_pedido},
        ])
        self.vista.doubleClicked.connect(self._ver_pedido)
        layout.addWidget(self.vista)

    def _setup_tab_clientes(self) -> None:
        layout = QVBoxLayout(self.tab_clientes)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self.btn_nuevo_cli = QPushButton("+ Nuevo Cliente")
        self.btn_nuevo_cli.setObjectName("btnPrimary")
        self.btn_nuevo_cli.clicked.connect(self._nuevo_cliente)
        toolbar.addWidget(self.btn_nuevo_cli)
        layout.addLayout(toolbar)

        self.grid_cli = ComplexGrid()
        self.grid_cli.set_columnas([
            {"key": "rfc", "titulo": "RFC", "ancho": 130},
            {"key": "nombre", "titulo": "Nombre", "ancho": 200},
            {"key": "nombre_comercial", "titulo": "Nombre Comercial", "ancho": 170},
            {"key": "telefono", "titulo": "Teléfono", "ancho": 110},
            {"key": "email", "titulo": "Email", "ancho": 180},
            {"key": "direccion", "titulo": "Dirección", "ancho": 220},
        ])
        self.grid_cli.set_renderers(estilo=self._estilo_cliente)
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

    def _programar_pedido(self) -> None:
        rec = self.vista.registro_seleccionado()
        if rec is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un pedido.")
            return
        dlg = ProgramarPedidoDialog(self.controller, ProgramacionController(),
                                    rec["id"], self)
        if dlg.exec():
            self._load_pedidos()
            folios = ", ".join(dlg.folios_generados)
            QMessageBox.information(
                self, "Programado",
                f"Se generaron los folios de programación: {folios}")

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

        self.cmb_cliente = QComboBox()
        for c in self.controller.listar_clientes():
            self.cmb_cliente.addItem(c["nombre"], c["id"])

        self.txt_folio = QLineEdit()
        self.txt_folio.setText(self.controller.siguiente_folio())
        self.txt_folio.setReadOnly(True)

        self.txt_folio_pedido = QLineEdit()
        self.txt_folio_pedido.setPlaceholderText("Folio de pedido del cliente (opcional)")

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

        self.txt_suela = QLineEdit()
        self.txt_suela.setPlaceholderText("Ej: PIEL CARA")

        self.txt_horma = QLineEdit()
        self.txt_horma.setPlaceholderText("Ej: H-7")

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")
        self.txt_obs.setMaximumHeight(60)

        grp_datos = QGroupBox("Datos del Pedido")
        grp_datos.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
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
        grp_ficha.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
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
        self.txt_folio_pedido.setText(pedido.get("folio_pedido", "") or "")
        self.txt_suela.setText(pedido.get("suela", "") or "")
        self.txt_horma.setText(pedido.get("horma", "") or "")
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
        puntos = self.controller.listar_puntos()
        id_por_talla = {p["punto"]: p["id"] for p in puntos}
        actual = self._puntos_fila.get(row, {})
        inicial = {p["punto"]: int(actual.get(p["id"], 0) or 0) for p in puntos}
        dlg = MatrizTallasDialog(puntos=puntos, titulo="TALLAS DEL PEDIDO",
                                 parent=self)
        dlg.establecer_valores(inicial)
        if dlg.exec() == QDialog.Accepted:
            valores = dlg.obtener_valores()
            self._puntos_fila[row] = {id_por_talla[t]: n
                                      for t, n in valores.items() if n > 0}
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
