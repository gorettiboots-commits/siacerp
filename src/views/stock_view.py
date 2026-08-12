from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.controllers.inventario_controller import InventarioController
from src.models.accesos_model import tiene
from src.views.dialogs import DialogInsumo, DialogMovimientoStock
from src.views.table_widget import GorettiTable


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

        self.table = GorettiTable(
            columns=[
                {"key": "codigo", "label": "Código", "width": 130},
                {"key": "nombre", "label": "Nombre", "stretch": True},
                {"key": "categoria", "label": "Categoría", "width": 150},
                {"key": "unidad_medida", "label": "Unidad", "width": 110},
                {"key": "stock_actual", "label": "Stock Actual", "width": 120, "align": "right"},
                {"key": "stock_minimo", "label": "Stock Mínimo", "width": 120, "align": "right"},
            ],
            id_key="id",
            image_resolver=self.controller.obtener_imagen_insumo,
            title_key=["codigo", "nombre"],
            subtitle_key=["categoria"],
            foreground_fn=self._color_celda_insumo,
            show_mode_selector=True,
        )
        self.table.recordDoubleClicked.connect(self._editar_insumo)
        self.table.set_group_options([("Categoría", "categoria")])
        layout.addWidget(self.table)

    def _color_celda_insumo(self, record: dict, key: str) -> QColor | None:
        stock = record.get("stock_actual", 0) or 0
        minimo = record.get("stock_minimo", 0) or 0
        if minimo > 0 and stock <= minimo and key in ("stock_actual", "stock_minimo"):
            return QColor("#dc2626")
        return None

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

        self.table_mov = GorettiTable(
            columns=[
                {"key": "created_at", "label": "Fecha", "width": 170},
                {"key": "insumo_nombre", "label": "Insumo", "stretch": True},
                {"key": "tipo_movimiento", "label": "Tipo", "width": 120, "align": "center"},
                {"key": "cantidad", "label": "Cantidad", "width": 110, "align": "right"},
                {"key": "referencia_tipo", "label": "Referencia", "width": 160},
                {"key": "observaciones", "label": "Observaciones", "width": 220},
            ],
            id_key="id",
        )
        layout.addWidget(self.table_mov)

    def _load_insumos(self) -> None:
        try:
            insumos = self.controller.listar_insumos()
            self.table.set_records(insumos)
            self._load_movimientos()
        except Exception as e:
            print(f"Error: {e}")

    def _load_movimientos(self) -> None:
        try:
            movs = self.controller.listar_movimientos()
            datos = []
            for m in movs:
                folio = m.get("referencia_folio", "")
                if m.get("referencia_tipo") in ("orden_compra", "orden_produccion"):
                    folio = folio or ""
                datos.append({
                    "id": m.get("id"),
                    "created_at": m.get("created_at", ""),
                    "insumo_nombre": m.get("insumo_nombre", ""),
                    "tipo_movimiento": m.get("tipo_movimiento", "").capitalize(),
                    "cantidad": m.get("cantidad", 0),
                    "referencia_tipo": folio,
                    "observaciones": m.get("observaciones", "") or "",
                })
            self.table_mov.set_records(datos)
        except Exception as e:
            print(f"Error movimientos: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_insumos()
            return
        try:
            resultados = self.controller.buscar_insumos(texto)
            self.table.set_records(resultados)
        except Exception as e:
            print(f"Error búsqueda: {e}")

    def _nuevo_insumo(self) -> None:
        dlg = DialogInsumo(self.controller)
        if dlg.exec():
            self._load_insumos()

    def _editar_insumo(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un insumo.")
            return
        insumo_id = int(record["id"])
        dlg = DialogInsumo(self.controller, insumo_id)
        if dlg.exec():
            self._load_insumos()

    def _desactivar_insumo(self) -> None:
        record = self.table.current_record()
        if record is None:
            return
        nombre = record.get("nombre", "")
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_insumo(int(record["id"]))
            self._load_insumos()

    def _registrar_movimiento(self) -> None:
        record = self.table.current_record()
        insumo_id = int(record["id"]) if record else None
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
        path = self.table.exportar_excel("Insumos", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir_insumos(self) -> None:
        self.table.imprimir("Insumos", self)

    def _exportar_movimientos(self) -> None:
        path = self.table_mov.exportar_excel("Movimientos_Inventario", self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")

    def _imprimir_movimientos(self) -> None:
        self.table_mov.imprimir("Movimientos_Inventario", self)
