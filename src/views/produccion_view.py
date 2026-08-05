from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.controllers.inventario_controller import InventarioController
from src.controllers.produccion_controller import ProduccionController
from src.models.accesos_model import tiene
from src.utils.export_utils import export_table_to_excel, print_table
from src.views.dialogs import (
    DialogBOM, DialogModelo, DialogOrdenProduccion,
    DialogSeguimientoOP, DialogVariante,
)


class ProduccionView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = ProduccionController()
        self.inv_controller = InventarioController()
        self._permisos: set = set()
        self._setup_ui()
        self._load_ops()

    def set_permisos(self, permisos) -> None:
        self._permisos = permisos or set()
        self.btn_nueva_op.setEnabled(tiene(self._permisos, "produccion", "crear"))
        self.btn_seguimiento.setEnabled(tiene(self._permisos, "produccion", "ver"))
        self.btn_avanzar.setEnabled(tiene(self._permisos, "produccion", "editar"))
        self.btn_export.setEnabled(tiene(self._permisos, "produccion", "exportar"))
        self.btn_print.setEnabled(tiene(self._permisos, "produccion", "exportar"))
        self.btn_nuevo_m.setEnabled(tiene(self._permisos, "produccion", "crear"))
        self.btn_editar_m.setEnabled(tiene(self._permisos, "produccion", "editar"))
        self.btn_desactivar_m.setEnabled(tiene(self._permisos, "produccion", "eliminar"))
        self.btn_export_m.setEnabled(tiene(self._permisos, "produccion", "exportar"))
        self.btn_nuevo_v.setEnabled(tiene(self._permisos, "produccion", "crear"))
        self.btn_editar_v.setEnabled(tiene(self._permisos, "produccion", "editar"))
        self.btn_desactivar_v.setEnabled(tiene(self._permisos, "produccion", "eliminar"))
        self.btn_export_v.setEnabled(tiene(self._permisos, "produccion", "exportar"))
        self.btn_editar_bom.setEnabled(
            tiene(self._permisos, "produccion", "editar") and hasattr(self, "_modelo_bom_id"))
        self.btn_export_pt.setEnabled(tiene(self._permisos, "produccion", "exportar"))
        self.btn_print_pt.setEnabled(tiene(self._permisos, "produccion", "exportar"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QFrame()
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel("Producción")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Órdenes de producción, catálogos y seguimiento de línea")
        subtitle.setObjectName("sectionSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.btn_nueva_op = QPushButton("+ Nueva OP")
        self.btn_nueva_op.setObjectName("btnPrimary")
        self.btn_nueva_op.clicked.connect(self._nueva_op)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_nueva_op)

        self.tabs = QTabWidget()
        self.tab_kanban = QWidget()
        self.tab_ops = QWidget()
        self.tab_catalogos = QWidget()
        self.tab_pt = QWidget()
        self.tabs.addTab(self.tab_kanban, "Kanban")
        self.tabs.addTab(self.tab_ops, "Órdenes de Producción")
        self.tabs.addTab(self.tab_catalogos, "Catálogos")
        self.tabs.addTab(self.tab_pt, "Producto Terminado")
        self._setup_tab_kanban()
        self._setup_tab_ops()
        self._setup_tab_catalogos()
        self._setup_tab_pt()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

    def _setup_tab_kanban(self) -> None:
        from src.views.kanban_view import KanbanView
        self.kanban = KanbanView(self.controller, on_change=self._load_ops)
        layout = QVBoxLayout(self.tab_kanban)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.kanban)

    def _setup_tab_ops(self) -> None:
        layout = QVBoxLayout(self.tab_ops)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar OP por folio, modelo o variante...")
        self.txt_buscar.setMinimumWidth(300)
        self.txt_buscar.textChanged.connect(self._buscar)

        self.btn_seguimiento = QPushButton("Ver Seguimiento")
        self.btn_seguimiento.setObjectName("btnSecondary")
        self.btn_seguimiento.clicked.connect(self._ver_seguimiento)
        self.btn_avanzar = QPushButton("Avanzar Estación")
        self.btn_avanzar.setObjectName("btnSuccess")
        self.btn_avanzar.clicked.connect(self._avanzar_desde_tabla)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.clicked.connect(lambda: self._exportar_tabla(self.table, "Ordenes_Produccion"))
        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(lambda: print_table(self.table, "Ordenes_Produccion", self))

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self._load_ops)

        toolbar.addWidget(self.txt_buscar)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_seguimiento)
        toolbar.addWidget(self.btn_avanzar)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_print)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Folio", "Modelo", "Variante", "Pares", "F. Inicio",
            "F. Entrega", "Prioridad", "Estatus", "ID",
        ])
        self.table.setColumnHidden(8, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._ver_seguimiento)
        layout.addWidget(self.table)

    def _setup_tab_catalogos(self) -> None:
        layout = QVBoxLayout(self.tab_catalogos)
        layout.setContentsMargins(0, 8, 0, 0)

        subtabs = QTabWidget()
        tab_modelos = QWidget()
        tab_variantes = QWidget()
        tab_bom = QWidget()
        subtabs.addTab(tab_modelos, "Modelos")
        subtabs.addTab(tab_variantes, "Variantes")
        subtabs.addTab(tab_bom, "Lista de Materiales")
        layout.addWidget(subtabs)

        # Modelos
        mlayout = QVBoxLayout(tab_modelos)
        mtoolbar = QHBoxLayout()
        self.txt_buscar_m = QLineEdit()
        self.txt_buscar_m.setPlaceholderText("Buscar modelo...")
        self.txt_buscar_m.textChanged.connect(self._buscar_modelos)
        self.btn_nuevo_m = QPushButton("+ Nuevo Modelo")
        self.btn_nuevo_m.setObjectName("btnPrimary")
        self.btn_nuevo_m.clicked.connect(self._nuevo_modelo)
        self.btn_editar_m = QPushButton("Editar")
        self.btn_editar_m.setObjectName("btnSecondary")
        self.btn_editar_m.clicked.connect(self._editar_modelo)
        self.btn_desactivar_m = QPushButton("Desactivar")
        self.btn_desactivar_m.setObjectName("btnDanger")
        self.btn_desactivar_m.clicked.connect(self._desactivar_modelo)
        self.btn_export_m = QPushButton("Exportar Excel")
        self.btn_export_m.setObjectName("btnPrimary")
        self.btn_export_m.clicked.connect(lambda: self._exportar_tabla(self.table_modelos, "Modelos"))
        mtoolbar.addWidget(self.txt_buscar_m)
        mtoolbar.addStretch()
        mtoolbar.addWidget(self.btn_nuevo_m)
        mtoolbar.addWidget(self.btn_editar_m)
        mtoolbar.addWidget(self.btn_desactivar_m)
        mtoolbar.addWidget(self.btn_export_m)
        mlayout.addLayout(mtoolbar)

        self.table_modelos = QTableWidget()
        self.table_modelos.setColumnCount(4)
        self.table_modelos.setHorizontalHeaderLabels(["Código", "Nombre", "Descripción", "ID"])
        self.table_modelos.setColumnHidden(3, True)
        self.table_modelos.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_modelos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_modelos.setAlternatingRowColors(True)
        self.table_modelos.horizontalHeader().setStretchLastSection(True)
        self.table_modelos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_modelos.doubleClicked.connect(self._editar_modelo)
        self.table_modelos.setStyleSheet(self.table.styleSheet())
        mlayout.addWidget(self.table_modelos)

        # Variantes
        vlayout = QVBoxLayout(tab_variantes)
        vtoolbar = QHBoxLayout()
        self.txt_buscar_v = QLineEdit()
        self.txt_buscar_v.setPlaceholderText("Buscar variante...")
        self.txt_buscar_v.textChanged.connect(self._buscar_variantes)
        self.btn_nuevo_v = QPushButton("+ Nueva Variante")
        self.btn_nuevo_v.setObjectName("btnPrimary")
        self.btn_nuevo_v.clicked.connect(self._nueva_variante)
        self.btn_editar_v = QPushButton("Editar")
        self.btn_editar_v.setObjectName("btnSecondary")
        self.btn_editar_v.clicked.connect(self._editar_variante)
        self.btn_desactivar_v = QPushButton("Desactivar")
        self.btn_desactivar_v.setObjectName("btnDanger")
        self.btn_desactivar_v.clicked.connect(self._desactivar_variante)
        self.btn_export_v = QPushButton("Exportar Excel")
        self.btn_export_v.setObjectName("btnPrimary")
        self.btn_export_v.clicked.connect(lambda: self._exportar_tabla(self.table_variantes, "Variantes"))
        vtoolbar.addWidget(self.txt_buscar_v)
        vtoolbar.addStretch()
        vtoolbar.addWidget(self.btn_nuevo_v)
        vtoolbar.addWidget(self.btn_editar_v)
        vtoolbar.addWidget(self.btn_desactivar_v)
        vtoolbar.addWidget(self.btn_export_v)
        vlayout.addLayout(vtoolbar)

        self.table_variantes = QTableWidget()
        self.table_variantes.setColumnCount(5)
        self.table_variantes.setHorizontalHeaderLabels(["Código", "Modelo", "Color", "Piel", "ID"])
        self.table_variantes.setColumnHidden(4, True)
        self.table_variantes.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_variantes.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_variantes.setAlternatingRowColors(True)
        self.table_variantes.horizontalHeader().setStretchLastSection(True)
        self.table_variantes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_variantes.doubleClicked.connect(self._editar_variante)
        self.table_variantes.setStyleSheet(self.table.styleSheet())
        vlayout.addWidget(self.table_variantes)

        # BOM
        blayout = QVBoxLayout(tab_bom)
        blayout.addWidget(QLabel("Seleccione un modelo en la tabla de modelos:"))
        self.cmb_bom_modelo = QLineEdit()
        self.cmb_bom_modelo.setReadOnly(True)
        self.cmb_bom_modelo.setPlaceholderText("(seleccione un modelo)")
        self.btn_editar_bom = QPushButton("Editar Lista de Materiales")
        self.btn_editar_bom.setObjectName("btnPrimary")
        self.btn_editar_bom.setMinimumHeight(40)
        self.btn_editar_bom.clicked.connect(self._editar_bom)
        self.btn_editar_bom.setEnabled(False)
        self.table_bom = QTableWidget()
        self.table_bom.setColumnCount(4)
        self.table_bom.setHorizontalHeaderLabels(["Insumo", "Cant. por Par", "Unidad", "Stock Actual"])
        self.table_bom.horizontalHeader().setStretchLastSection(True)
        self.table_bom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_bom.setEditTriggers(QTableWidget.NoEditTriggers)
        blayout.addWidget(self.cmb_bom_modelo)
        blayout.addWidget(self.btn_editar_bom)
        blayout.addWidget(self.table_bom)
        self.table_modelos.itemSelectionChanged.connect(self._on_modelo_selected)

    def _setup_tab_pt(self) -> None:
        layout = QVBoxLayout(self.tab_pt)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.btn_export_pt = QPushButton("Exportar Excel")
        self.btn_export_pt.setObjectName("btnPrimary")
        self.btn_export_pt.clicked.connect(lambda: self._exportar_tabla(self.table_pt, "Producto_Terminado"))
        self.btn_print_pt = QPushButton("Imprimir")
        self.btn_print_pt.setObjectName("btnSecondary")
        self.btn_print_pt.clicked.connect(lambda: print_table(self.table_pt, "Producto_Terminado", self))

        btn_refresh_pt = QPushButton("Actualizar")
        btn_refresh_pt.setObjectName("btnPrimary")
        btn_refresh_pt.clicked.connect(self._load_pt)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_pt)
        toolbar.addWidget(self.btn_print_pt)
        toolbar.addWidget(btn_refresh_pt)
        layout.addLayout(toolbar)

        self.table_pt = QTableWidget()
        self.table_pt.setColumnCount(6)
        self.table_pt.setHorizontalHeaderLabels([
            "Modelo", "Variante", "Color", "Piel", "Talla", "Pares"
        ])
        self.table_pt.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_pt.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_pt.setAlternatingRowColors(True)
        self.table_pt.horizontalHeader().setStretchLastSection(True)
        self.table_pt.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_pt.setStyleSheet(self.table.styleSheet())
        layout.addWidget(self.table_pt)

    def _load_ops(self) -> None:
        try:
            ops = self.controller.listar_ops()
            if hasattr(self, "kanban"):
                self.kanban.recargar()
            self.table.setRowCount(len(ops))
            for i, op in enumerate(ops):
                self.table.setItem(i, 0, QTableWidgetItem(op.get("folio", "")))
                self.table.setItem(i, 1, QTableWidgetItem(op.get("modelo_nombre", "")))
                self.table.setItem(i, 2, QTableWidgetItem(op.get("codigo_variante", "")))
                self.table.setItem(i, 3, QTableWidgetItem(str(op.get("total_pares", 0))))
                self.table.setItem(i, 4, QTableWidgetItem(op.get("fecha_inicio", "") or ""))
                self.table.setItem(i, 5, QTableWidgetItem(op.get("fecha_entrega", "") or ""))
                self.table.setItem(i, 6, QTableWidgetItem(op.get("prioridad", "").capitalize()))
                est_item = QTableWidgetItem(op.get("estatus", "").replace("_", " ").capitalize())
                est = op.get("estatus", "")
                if est == "terminada":
                    est_item.setForeground(Qt.darkGreen)
                elif "produccion" in est:
                    est_item.setForeground(Qt.darkYellow)
                elif est == "planeada":
                    est_item.setForeground(Qt.blue)
                self.table.setItem(i, 7, est_item)
                self.table.setItem(i, 8, QTableWidgetItem(str(op.get("id", ""))))
            self._load_catalogos()
            self._load_pt()
        except Exception as e:
            print(f"Error: {e}")

    def _load_catalogos(self) -> None:
        try:
            modelos = self.controller.listar_modelos()
            self.table_modelos.setRowCount(len(modelos))
            for i, m in enumerate(modelos):
                self.table_modelos.setItem(i, 0, QTableWidgetItem(m.get("codigo", "")))
                self.table_modelos.setItem(i, 1, QTableWidgetItem(m.get("nombre", "")))
                self.table_modelos.setItem(i, 2, QTableWidgetItem(m.get("descripcion", "") or ""))
                self.table_modelos.setItem(i, 3, QTableWidgetItem(str(m.get("id", ""))))
            variantes = self.controller.listar_variantes()
            self.table_variantes.setRowCount(len(variantes))
            for i, v in enumerate(variantes):
                self.table_variantes.setItem(i, 0, QTableWidgetItem(v.get("codigo_variante", "")))
                self.table_variantes.setItem(i, 1, QTableWidgetItem(v.get("modelo_nombre", "")))
                self.table_variantes.setItem(i, 2, QTableWidgetItem(v.get("color", "")))
                self.table_variantes.setItem(i, 3, QTableWidgetItem(v.get("piel", "")))
                self.table_variantes.setItem(i, 4, QTableWidgetItem(str(v.get("id", ""))))
        except Exception as e:
            print(f"Error catálogos: {e}")

    def _load_pt(self) -> None:
        try:
            pts = self.controller.listar_pt()
            self.table_pt.setRowCount(len(pts))
            for i, p in enumerate(pts):
                self.table_pt.setItem(i, 0, QTableWidgetItem(p.get("modelo_nombre", "")))
                self.table_pt.setItem(i, 1, QTableWidgetItem(p.get("codigo_variante", "")))
                self.table_pt.setItem(i, 2, QTableWidgetItem(p.get("color", "")))
                self.table_pt.setItem(i, 3, QTableWidgetItem(p.get("piel", "")))
                self.table_pt.setItem(i, 4, QTableWidgetItem(p.get("talla", "")))
                self.table_pt.setItem(i, 5, QTableWidgetItem(str(p.get("pares", 0))))
        except Exception as e:
            print(f"Error PT: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ops()
            return
        try:
            resultados = self.controller.buscar_ops(texto)
            self.table.setRowCount(len(resultados))
            for i, op in enumerate(resultados):
                self.table.setItem(i, 0, QTableWidgetItem(op.get("folio", "")))
                self.table.setItem(i, 1, QTableWidgetItem(op.get("modelo_nombre", "")))
                self.table.setItem(i, 2, QTableWidgetItem(op.get("codigo_variante", "")))
                self.table.setItem(i, 3, QTableWidgetItem(str(op.get("total_pares", 0))))
                self.table.setItem(i, 4, QTableWidgetItem(op.get("fecha_inicio", "") or ""))
                self.table.setItem(i, 5, QTableWidgetItem(op.get("fecha_entrega", "") or ""))
                self.table.setItem(i, 6, QTableWidgetItem(op.get("prioridad", "")))
                self.table.setItem(i, 7, QTableWidgetItem(op.get("estatus", "")))
                self.table.setItem(i, 8, QTableWidgetItem(str(op.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_modelos(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_modelos(texto)
            self.table_modelos.setRowCount(len(res))
            for i, m in enumerate(res):
                self.table_modelos.setItem(i, 0, QTableWidgetItem(m.get("codigo", "")))
                self.table_modelos.setItem(i, 1, QTableWidgetItem(m.get("nombre", "")))
                self.table_modelos.setItem(i, 2, QTableWidgetItem(m.get("descripcion", "") or ""))
                self.table_modelos.setItem(i, 3, QTableWidgetItem(str(m.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_variantes(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_variantes(texto)
            self.table_variantes.setRowCount(len(res))
            for i, v in enumerate(res):
                self.table_variantes.setItem(i, 0, QTableWidgetItem(v.get("codigo_variante", "")))
                self.table_variantes.setItem(i, 1, QTableWidgetItem(v.get("modelo_nombre", "")))
                self.table_variantes.setItem(i, 2, QTableWidgetItem(v.get("color", "")))
                self.table_variantes.setItem(i, 3, QTableWidgetItem(v.get("piel", "")))
                self.table_variantes.setItem(i, 4, QTableWidgetItem(str(v.get("id", ""))))
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_op(self) -> None:
        dlg = DialogOrdenProduccion(self.controller)
        if dlg.exec():
            self._load_ops()

    def _ver_seguimiento(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        op_id = int(self.table.item(row, 8).text())
        dlg = DialogSeguimientoOP(self.controller, op_id)
        dlg.exec()
        self._load_ops()

    def _avanzar_desde_tabla(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        op_id = int(self.table.item(row, 8).text())
        dlg = DialogSeguimientoOP(self.controller, op_id)
        dlg.exec()
        self._load_ops()

    def _nuevo_modelo(self) -> None:
        dlg = DialogModelo(self.controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_modelo(self) -> None:
        row = self.table_modelos.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un modelo.")
            return
        modelo_id = int(self.table_modelos.item(row, 3).text())
        dlg = DialogModelo(self.controller, modelo_id)
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_modelo(self) -> None:
        row = self.table_modelos.currentRow()
        if row < 0:
            return
        nombre = self.table_modelos.item(row, 1).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_modelo(int(self.table_modelos.item(row, 3).text()))
            self._load_catalogos()

    def _nueva_variante(self) -> None:
        dlg = DialogVariante(self.controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_variante(self) -> None:
        row = self.table_variantes.currentRow()
        if row < 0:
            return
        v_id = int(self.table_variantes.item(row, 4).text())
        dlg = DialogVariante(self.controller, v_id)
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_variante(self) -> None:
        row = self.table_variantes.currentRow()
        if row < 0:
            return
        cod = self.table_variantes.item(row, 0).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar variante '{cod}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_variante(int(self.table_variantes.item(row, 4).text()))
            self._load_catalogos()

    def _on_modelo_selected(self) -> None:
        row = self.table_modelos.currentRow()
        if row >= 0:
            modelo_id = int(self.table_modelos.item(row, 3).text())
            nombre = self.table_modelos.item(row, 1).text()
            self.cmb_bom_modelo.setText(f"[{self.table_modelos.item(row, 0).text()}] {nombre}")
            self.btn_editar_bom.setEnabled(tiene(self._permisos, "produccion", "editar"))
            self._modelo_bom_id = modelo_id
            self._modelo_bom_nombre = nombre
            self._cargar_bom(modelo_id)
        else:
            self.cmb_bom_modelo.clear()
            self.btn_editar_bom.setEnabled(False)
            self.table_bom.setRowCount(0)

    def _cargar_bom(self, modelo_id: int) -> None:
        bom = self.controller.obtener_bom(modelo_id)
        self.table_bom.setRowCount(len(bom))
        for i, b in enumerate(bom):
            self.table_bom.setItem(i, 0, QTableWidgetItem(b.get("insumo_nombre", "")))
            self.table_bom.setItem(i, 1, QTableWidgetItem(str(b.get("cantidad_por_par", 0))))
            self.table_bom.setItem(i, 2, QTableWidgetItem(b.get("unidad_medida", "")))
            self.table_bom.setItem(i, 3, QTableWidgetItem(str(b.get("stock_actual", 0))))

    def _editar_bom(self) -> None:
        if hasattr(self, "_modelo_bom_id"):
            dlg = DialogBOM(self.controller, self.inv_controller,
                             self._modelo_bom_id, self._modelo_bom_nombre)
            if dlg.exec():
                self._cargar_bom(self._modelo_bom_id)

    def _exportar_tabla(self, table: QTableWidget, nombre: str) -> None:
        path = export_table_to_excel(table, nombre, self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")
