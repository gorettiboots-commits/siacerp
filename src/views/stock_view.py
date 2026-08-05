from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.controllers.inventario_controller import InventarioController
from src.models.accesos_model import tiene
from src.utils.export_utils import export_table_to_excel, print_table
from src.views.dialogs import DialogInsumo, DialogMovimientoStock


class StockView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = InventarioController()
        self._setup_ui()
        self._load_insumos()

    def set_permisos(self, permisos) -> None:
        self.btn_nuevo.setEnabled(tiene(permisos, "inventario", "crear"))
        self.btn_movimiento.setEnabled(tiene(permisos, "inventario", "crear"))
        self.btn_editar.setEnabled(tiene(permisos, "inventario", "editar"))
        self.btn_eliminar.setEnabled(tiene(permisos, "inventario", "eliminar"))
        self.btn_export.setEnabled(tiene(permisos, "inventario", "exportar"))
        self.btn_print.setEnabled(tiene(permisos, "inventario", "exportar"))
        self.btn_export_mov.setEnabled(tiene(permisos, "inventario", "exportar"))
        self.btn_print_mov.setEnabled(tiene(permisos, "inventario", "exportar"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QFrame()
        hlayout = QHBoxLayout(header)
        hlayout.setContentsMargins(0, 0, 0, 0)

        title_col = QVBoxLayout()
        title = QLabel("Inventario de Insumos")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Control de materia prima, movimientos y alertas de stock")
        subtitle.setObjectName("sectionSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.btn_nuevo = QPushButton("+ Nuevo Insumo")
        self.btn_nuevo.setObjectName("btnPrimary")
        self.btn_nuevo.clicked.connect(self._nuevo_insumo)
        self.btn_movimiento = QPushButton("Movimiento")
        self.btn_movimiento.setObjectName("btnWarning")
        self.btn_movimiento.clicked.connect(self._registrar_movimiento)
        self.btn_stock_bajo = QPushButton("Alertas")
        self.btn_stock_bajo.setObjectName("btnDanger")
        self.btn_stock_bajo.clicked.connect(self._mostrar_stock_bajo)

        hlayout.addLayout(title_col)
        hlayout.addStretch()
        hlayout.addWidget(self.btn_stock_bajo)
        hlayout.addWidget(self.btn_movimiento)
        hlayout.addWidget(self.btn_nuevo)

        self.tabs = QTabWidget()
        self.tab_insumos = QWidget()
        self.tab_movimientos = QWidget()
        self.tabs.addTab(self.tab_insumos, "Insumos")
        self.tabs.addTab(self.tab_movimientos, "Movimientos")
        self._setup_tab_insumos()
        self._setup_tab_movimientos()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

    def _setup_tab_insumos(self) -> None:
        layout = QVBoxLayout(self.tab_insumos)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar insumo por código, nombre o categoría...")
        self.txt_buscar.setMinimumWidth(300)
        self.txt_buscar.textChanged.connect(self._buscar)

        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setObjectName("btnSecondary")
        self.btn_editar.clicked.connect(self._editar_insumo)
        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setObjectName("btnDanger")
        self.btn_eliminar.clicked.connect(self._desactivar_insumo)

        self.btn_export = QPushButton("Exportar Excel")
        self.btn_export.setObjectName("btnPrimary")
        self.btn_export.clicked.connect(self._exportar_insumos)
        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(self._imprimir_insumos)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("btnPrimary")
        btn_refresh.clicked.connect(self._load_insumos)

        toolbar.addWidget(self.txt_buscar)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_eliminar)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_print)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Categoría", "Unidad", "Stock Actual",
            "Stock Mínimo", "ID"
        ])
        self.table.setColumnHidden(6, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._editar_insumo)
        layout.addWidget(self.table)

    def _setup_tab_movimientos(self) -> None:
        layout = QVBoxLayout(self.tab_movimientos)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.btn_export_mov = QPushButton("Exportar Excel")
        self.btn_export_mov.setObjectName("btnPrimary")
        self.btn_export_mov.clicked.connect(self._exportar_movimientos)
        self.btn_print_mov = QPushButton("Imprimir")
        self.btn_print_mov.setObjectName("btnSecondary")
        self.btn_print_mov.clicked.connect(self._imprimir_movimientos)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_mov)
        toolbar.addWidget(self.btn_print_mov)
        layout.addLayout(toolbar)

        self.table_mov = QTableWidget()
        self.table_mov.setColumnCount(6)
        self.table_mov.setHorizontalHeaderLabels([
            "Fecha", "Insumo", "Tipo", "Cantidad", "Referencia", "Observaciones"
        ])
        self.table_mov.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_mov.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_mov.setAlternatingRowColors(True)
        self.table_mov.horizontalHeader().setStretchLastSection(True)
        self.table_mov.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_mov.setStyleSheet(self.table.styleSheet())
        layout.addWidget(self.table_mov)

    def _set_fila_insumo(self, i: int, ins: dict) -> None:
        stock = ins.get("stock_actual", 0)
        stock_min = ins.get("stock_minimo", 0)
        self.table.setItem(i, 0, QTableWidgetItem(ins.get("codigo", "")))
        self.table.setItem(i, 1, QTableWidgetItem(ins.get("nombre", "")))
        self.table.setItem(i, 2, QTableWidgetItem(ins.get("categoria", "")))
        self.table.setItem(i, 3, QTableWidgetItem(ins.get("unidad_medida", "")))
        self.table.setItem(i, 4, QTableWidgetItem(str(stock)))
        self.table.setItem(i, 5, QTableWidgetItem(str(stock_min)))
        self.table.setItem(i, 6, QTableWidgetItem(str(ins.get("id", ""))))
        if stock <= stock_min and stock_min > 0:
            self.table.item(i, 4).setForeground(Qt.red)
            self.table.item(i, 5).setForeground(Qt.red)

    def _load_insumos(self) -> None:
        try:
            insumos = self.controller.listar_insumos()
            self.table.setRowCount(len(insumos))
            for i, ins in enumerate(insumos):
                self._set_fila_insumo(i, ins)
            self._load_movimientos()
        except Exception as e:
            print(f"Error: {e}")

    def _load_movimientos(self) -> None:
        try:
            movs = self.controller.listar_movimientos()
            self.table_mov.setRowCount(len(movs))
            for i, m in enumerate(movs):
                self.table_mov.setItem(i, 0, QTableWidgetItem(m.get("created_at", "")))
                self.table_mov.setItem(i, 1, QTableWidgetItem(m.get("insumo_nombre", "")))
                self.table_mov.setItem(i, 2, QTableWidgetItem(m.get("tipo_movimiento", "").capitalize()))
                self.table_mov.setItem(i, 3, QTableWidgetItem(str(m.get("cantidad", 0))))
                self.table_mov.setItem(i, 4, QTableWidgetItem(m.get("referencia_tipo", "") or ""))
                self.table_mov.setItem(i, 5, QTableWidgetItem(m.get("observaciones", "") or ""))
        except Exception as e:
            print(f"Error movimientos: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_insumos()
            return
        try:
            resultados = self.controller.buscar_insumos(texto)
            self.table.setRowCount(len(resultados))
            for i, ins in enumerate(resultados):
                self._set_fila_insumo(i, ins)
        except Exception as e:
            print(f"Error búsqueda: {e}")

    def _nuevo_insumo(self) -> None:
        dlg = DialogInsumo(self.controller)
        if dlg.exec():
            self._load_insumos()

    def _editar_insumo(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar", "Seleccione un insumo.")
            return
        insumo_id = int(self.table.item(row, 6).text())
        dlg = DialogInsumo(self.controller, insumo_id)
        if dlg.exec():
            self._load_insumos()

    def _desactivar_insumo(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        nombre = self.table.item(row, 1).text()
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_insumo(int(self.table.item(row, 6).text()))
            self._load_insumos()

    def _registrar_movimiento(self) -> None:
        row = self.table.currentRow()
        insumo_id = int(self.table.item(row, 6).text()) if row >= 0 else None
        dlg = DialogMovimientoStock(self.controller, insumo_id)
        if dlg.exec():
            self._load_insumos()

    def _mostrar_stock_bajo(self) -> None:
        bajos = self.controller.stock_bajo()
        if not bajos:
            QMessageBox.information(self, "Stock", "No hay insumos con stock bajo.")
            return
        msg = "=== INSUMOS CON STOCK BAJO ===\n\n"
        for ins in bajos:
            msg += f"{ins['codigo']} - {ins['nombre']}: {ins['stock_actual']} / {ins['stock_minimo']} {ins['unidad_medida']}\n"
        QMessageBox.warning(self, f"Alertas de Stock ({len(bajos)})", msg)

    def _exportar_insumos(self) -> None:
        path = export_table_to_excel(self.table, "Insumos", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir_insumos(self) -> None:
        print_table(self.table, "Insumos", self)

    def _exportar_movimientos(self) -> None:
        path = export_table_to_excel(self.table_mov, "Movimientos_Inventario", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir_movimientos(self) -> None:
        print_table(self.table_mov, "Movimientos_Inventario", self)
