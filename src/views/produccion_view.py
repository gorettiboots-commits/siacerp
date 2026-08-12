from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.controllers.inventario_controller import InventarioController
from src.controllers.produccion_controller import ProduccionController
from src.models.accesos_model import tiene
from src.views.dialogs import (
    DialogBOM, DialogModelo, DialogOrdenProduccion,
    DialogSeguimientoOP, DialogVariante,
)
from src.views.table_widget import GorettiTable


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
        self.btn_print.clicked.connect(lambda: self.table.imprimir("Ordenes_Produccion", self))

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

        self.table = GorettiTable(
            columns=[
                {"key": "folio", "label": "Folio", "width": 120},
                {"key": "modelo_nombre", "label": "Modelo", "stretch": True},
                {"key": "codigo_variante", "label": "Variante", "width": 140},
                {"key": "total_pares", "label": "Pares", "width": 90, "align": "right"},
                {"key": "fecha_inicio", "label": "F. Inicio", "width": 160},
                {"key": "fecha_entrega", "label": "F. Entrega", "width": 160},
                {"key": "prioridad", "label": "Prioridad", "width": 110, "align": "center"},
                {"key": "estatus", "label": "Estatus", "width": 140},
            ],
            id_key="id",
            foreground_fn=self._color_estatus_op,
        )
        self.table.recordDoubleClicked.connect(self._ver_seguimiento)
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

        self.table_modelos = GorettiTable(
            columns=[
                {"key": "codigo", "label": "Código", "width": 130},
                {"key": "nombre", "label": "Nombre", "stretch": True},
                {"key": "descripcion", "label": "Descripción", "width": 300},
            ],
            id_key="id",
        )
        self.table_modelos.recordDoubleClicked.connect(self._editar_modelo)
        self.table_modelos.currentRecordChanged.connect(self._on_modelo_selected)
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

        self.table_variantes = GorettiTable(
            columns=[
                {"key": "codigo_variante", "label": "Código", "width": 140},
                {"key": "modelo_nombre", "label": "Modelo", "stretch": True},
                {"key": "talla", "label": "Talla", "width": 100, "align": "center"},
                {"key": "color", "label": "Color", "width": 130},
                {"key": "piel", "label": "Piel", "width": 130},
            ],
            id_key="id",
        )
        self.table_variantes.recordDoubleClicked.connect(self._editar_variante)
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
        self.table_bom = GorettiTable(
            columns=[
                {"key": "insumo_nombre", "label": "Insumo", "stretch": True},
                {"key": "cantidad_por_par", "label": "Cant. por Par", "width": 140, "align": "right"},
                {"key": "unidad_medida", "label": "Unidad", "width": 100, "align": "center"},
                {"key": "stock_actual", "label": "Stock Actual", "width": 120, "align": "right"},
            ],
            id_key="id",
        )
        blayout.addWidget(self.cmb_bom_modelo)
        blayout.addWidget(self.btn_editar_bom)
        blayout.addWidget(self.table_bom)

    def _setup_tab_pt(self) -> None:
        layout = QVBoxLayout(self.tab_pt)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.btn_export_pt = QPushButton("Exportar Excel")
        self.btn_export_pt.setObjectName("btnPrimary")
        self.btn_export_pt.clicked.connect(lambda: self._exportar_tabla(self.table_pt, "Producto_Terminado"))
        self.btn_print_pt = QPushButton("Imprimir")
        self.btn_print_pt.setObjectName("btnSecondary")
        self.btn_print_pt.clicked.connect(lambda: self.table_pt.imprimir("Producto_Terminado", self))

        btn_refresh_pt = QPushButton("Actualizar")
        btn_refresh_pt.setObjectName("btnPrimary")
        btn_refresh_pt.clicked.connect(self._load_pt)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_pt)
        toolbar.addWidget(self.btn_print_pt)
        toolbar.addWidget(btn_refresh_pt)
        layout.addLayout(toolbar)

        self.table_pt = GorettiTable(
            columns=[
                {"key": "modelo_nombre", "label": "Modelo", "stretch": True},
                {"key": "codigo_variante", "label": "Variante", "width": 150},
                {"key": "color", "label": "Color", "width": 130},
                {"key": "piel", "label": "Piel", "width": 130},
                {"key": "talla", "label": "Talla", "width": 100, "align": "center"},
                {"key": "pares", "label": "Pares", "width": 100, "align": "right"},
            ],
            id_key="id",
        )
        layout.addWidget(self.table_pt)

    def _load_ops(self) -> None:
        try:
            ops = self.controller.listar_ops()
            if hasattr(self, "kanban"):
                self.kanban.recargar()
            self.table.set_records([self._fila_op(op) for op in ops])
            self._load_catalogos()
            self._load_pt()
        except Exception as e:
            print(f"Error: {e}")

    def _fila_op(self, op: dict) -> dict:
        return {
            "id": op.get("id"),
            "folio": op.get("folio", ""),
            "modelo_nombre": op.get("modelo_nombre", ""),
            "codigo_variante": op.get("codigo_variante", ""),
            "total_pares": op.get("total_pares", 0),
            "fecha_inicio": op.get("fecha_inicio", "") or "",
            "fecha_entrega": op.get("fecha_entrega", "") or "",
            "prioridad": op.get("prioridad", "").capitalize(),
            "estatus": op.get("estatus", "").replace("_", " ").capitalize(),
        }

    def _color_estatus_op(self, record: dict, key: str) -> QColor | None:
        if key != "estatus":
            return None
        est = record.get("estatus", "")
        if est == "Terminada":
            return Qt.darkGreen
        if "Produccion" in est:
            return Qt.darkYellow
        if est == "Planeada":
            return Qt.blue
        return None

    def _load_catalogos(self) -> None:
        try:
            modelos = self.controller.listar_modelos()
            self.table_modelos.set_records(modelos)
            variantes = self.controller.listar_variantes()
            self.table_variantes.set_records(variantes)
        except Exception as e:
            print(f"Error catálogos: {e}")

    def _load_pt(self) -> None:
        try:
            pts = self.controller.listar_pt()
            self.table_pt.set_records(pts)
        except Exception as e:
            print(f"Error PT: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ops()
            return
        try:
            resultados = self.controller.buscar_ops(texto)
            self.table.set_records([self._fila_op(op) for op in resultados])
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_modelos(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_modelos(texto)
            self.table_modelos.set_records(res)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_variantes(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_variantes(texto)
            self.table_variantes.set_records(res)
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_op(self) -> None:
        dlg = DialogOrdenProduccion(self.controller)
        if dlg.exec():
            self._load_ops()

    def _ver_seguimiento(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        dlg = DialogSeguimientoOP(self.controller, int(record["id"]))
        dlg.exec()
        self._load_ops()

    def _avanzar_desde_tabla(self) -> None:
        record = self.table.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        dlg = DialogSeguimientoOP(self.controller, int(record["id"]))
        dlg.exec()
        self._load_ops()

    def _nuevo_modelo(self) -> None:
        dlg = DialogModelo(self.controller, self.inv_controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_modelo(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table_modelos.current_record()
        if record is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un modelo.")
            return
        dlg = DialogModelo(self.controller, self.inv_controller, int(record["id"]))
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_modelo(self) -> None:
        record = self.table_modelos.current_record()
        if record is None:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{record['nombre']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_modelo(int(record["id"]))
            self._load_catalogos()

    def _nueva_variante(self) -> None:
        dlg = DialogVariante(self.controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_variante(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table_variantes.current_record()
        if record is None:
            return
        dlg = DialogVariante(self.controller, int(record["id"]))
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_variante(self) -> None:
        record = self.table_variantes.current_record()
        if record is None:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar variante '{record['codigo_variante']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_variante(int(record["id"]))
            self._load_catalogos()

    def _on_modelo_selected(self, record: dict | None = None) -> None:
        if not isinstance(record, dict):
            record = self.table_modelos.current_record()
        if record is None:
            self.cmb_bom_modelo.clear()
            self.btn_editar_bom.setEnabled(False)
            self.table_bom.set_records([])
            return
        modelo_id = int(record["id"])
        self.cmb_bom_modelo.setText(f"[{record.get('codigo', '')}] {record.get('nombre', '')}")
        self.btn_editar_bom.setEnabled(tiene(self._permisos, "produccion", "editar"))
        self._modelo_bom_id = modelo_id
        self._modelo_bom_nombre = record.get("nombre", "")
        self._cargar_bom(modelo_id)

    def _cargar_bom(self, modelo_id: int) -> None:
        bom = self.controller.obtener_bom(modelo_id)
        self.table_bom.set_records(bom)

    def _editar_bom(self) -> None:
        if hasattr(self, "_modelo_bom_id"):
            dlg = DialogBOM(self.controller, self.inv_controller,
                             self._modelo_bom_id, self._modelo_bom_nombre)
            if dlg.exec():
                self._cargar_bom(self._modelo_bom_id)

    def _exportar_tabla(self, table: GorettiTable, nombre: str) -> None:
        path = table.exportar_excel(nombre, self)
        if path:
            QMessageBox.information(self, "Exportado", f"Excel guardado en:\n{path}")
