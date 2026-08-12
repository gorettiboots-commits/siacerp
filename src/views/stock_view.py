from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.controllers.inventario_controller import InventarioController
from src.models.accesos_model import tiene
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
        self.vista.set_exportar_visible(tiene(permisos, "inventario", "exportar"))
        self.grid_mov.set_exportar_visible(tiene(permisos, "inventario", "exportar"))

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

        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_editar)
        toolbar.addWidget(self.btn_eliminar)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_print)
        layout.addLayout(toolbar)

        self.vista = ComplexGrid()
        self.vista.set_columnas([
            {"key": "codigo", "titulo": "Código", "ancho": 120},
            {"key": "nombre", "titulo": "Nombre", "ancho": 220},
            {"key": "categoria", "titulo": "Categoría", "ancho": 140},
            {"key": "unidad_medida", "titulo": "Unidad", "ancho": 90},
            {"key": "stock_actual", "titulo": "Stock Actual", "ancho": 110, "tipo": "numero"},
            {"key": "stock_minimo", "titulo": "Stock Mínimo", "ancho": 110, "tipo": "numero"},
        ])
        self.vista.set_renderers(
            fila=self._fila_insumo,
            claves=self._claves_insumo,
            estilo=self._estilo_insumo,
            tarjeta=self._tarjeta_insumo,
            lista=self._lista_insumo,
        )
        self.vista.doubleClicked.connect(self._editar_insumo)
        layout.addWidget(self.vista)

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

        self.grid_mov = ComplexGrid()
        self.grid_mov.set_columnas([
            {"key": "created_at", "titulo": "Fecha", "ancho": 150},
            {"key": "insumo_nombre", "titulo": "Insumo", "ancho": 200},
            {"key": "tipo_movimiento", "titulo": "Tipo", "ancho": 100},
            {"key": "cantidad", "titulo": "Cantidad", "ancho": 100, "tipo": "numero"},
            {"key": "referencia_tipo", "titulo": "Referencia", "ancho": 130},
            {"key": "observaciones", "titulo": "Observaciones", "ancho": 240},
        ])
        self.grid_mov.set_renderers(fila=self._fila_mov, claves=self._claves_mov)
        layout.addWidget(self.grid_mov)

    def _fila_insumo(self, ins: dict) -> list[str]:
        return [
            ins.get("codigo", ""),
            ins.get("nombre", ""),
            ins.get("categoria", ""),
            ins.get("unidad_medida", ""),
            str(ins.get("stock_actual", 0)),
            str(ins.get("stock_minimo", 0)),
        ]

    def _claves_insumo(self, ins: dict) -> list:
        return [
            ins.get("codigo", ""),
            (ins.get("nombre", "") or "").lower(),
            (ins.get("categoria", "") or "").lower(),
            ins.get("unidad_medida", ""),
            float(ins.get("stock_actual", 0) or 0),
            float(ins.get("stock_minimo", 0) or 0),
        ]

    def _estilo_insumo(self, ins: dict, item, col: int) -> None:
        stock = ins.get("stock_actual", 0)
        stock_min = ins.get("stock_minimo", 0)
        if stock <= stock_min and stock_min > 0 and col in (4, 5):
            item.setForeground(Qt.red)

    def _tarjeta_insumo(self, ins: dict) -> dict:
        stock = ins.get("stock_actual", 0)
        unidad = ins.get("unidad_medida", "")
        return {
            "tile": "inventario",
            "titulo": ins.get("nombre", ""),
            "subtitulo": f"{ins.get('codigo', '')} · {ins.get('categoria', '')}",
            "badge": f"{stock} {unidad}",
        }

    def _lista_insumo(self, ins: dict) -> tuple:
        return (
            ins.get("nombre", ""),
            f"{ins.get('codigo', '')} · {ins.get('categoria', '')} · "
            f"{ins.get('stock_actual', 0)} {ins.get('unidad_medida', '')}",
        )

    def _fila_mov(self, m: dict) -> list[str]:
        return [
            m.get("created_at", ""),
            m.get("insumo_nombre", ""),
            m.get("tipo_movimiento", "").capitalize(),
            str(m.get("cantidad", 0)),
            m.get("referencia_tipo", "") or "",
            m.get("observaciones", "") or "",
        ]

    def _claves_mov(self, m: dict) -> list:
        return [
            m.get("created_at", ""),
            m.get("insumo_nombre", ""),
            m.get("tipo_movimiento", ""),
            float(m.get("cantidad", 0) or 0),
            m.get("referencia_tipo", "") or "",
            m.get("observaciones", "") or "",
        ]

    def _load_insumos(self) -> None:
        try:
            insumos = self.controller.listar_insumos()
            self.vista.set_datos(insumos)
            self._load_movimientos()
        except Exception as e:
            print(f"Error: {e}")

    def _load_movimientos(self) -> None:
        try:
            movs = self.controller.listar_movimientos()
            self.grid_mov.set_datos(movs)
        except Exception as e:
            print(f"Error movimientos: {e}")

    def _nuevo_insumo(self) -> None:
        dlg = DialogInsumo(self.controller)
        if dlg.exec():
            self._load_insumos()

    def _editar_insumo(self) -> None:
        ins = self.vista.registro_seleccionado()
        if not ins:
            QMessageBox.information(self, "Seleccionar", "Seleccione un insumo.")
            return
        dlg = DialogInsumo(self.controller, ins["id"])
        if dlg.exec():
            self._load_insumos()

    def _desactivar_insumo(self) -> None:
        ins = self.vista.registro_seleccionado()
        if not ins:
            return
        nombre = ins.get("nombre", "")
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{nombre}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_insumo(ins["id"])
            self._load_insumos()

    def _registrar_movimiento(self) -> None:
        ins = self.vista.registro_seleccionado()
        dlg = DialogMovimientoStock(self.controller, ins["id"] if ins else None)
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
        self.vista.exportar_excel()

    def _imprimir_insumos(self) -> None:
        self.vista.imprimir()

    def _exportar_movimientos(self) -> None:
        self.grid_mov.exportar_excel()

    def _imprimir_movimientos(self) -> None:
        self.grid_mov.imprimir()
