from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from src.components.complex_grid import ComplexGrid
from src.components.notificacion_flotante import notificar_flotante
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
        self.btn_export.clicked.connect(lambda: self._exportar_tabla(self.vista.table, "Ordenes_Produccion"))
        self.btn_print = QPushButton("Imprimir")
        self.btn_print.setObjectName("btnSecondary")
        self.btn_print.clicked.connect(lambda: print_table(self.vista.table, "Ordenes_Produccion", self))

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

        self.vista = ComplexGrid()
        self.vista.set_columnas([
            {"key": "folio", "titulo": "Folio", "ancho": 110},
            {"key": "modelo_nombre", "titulo": "Modelo", "ancho": 150},
            {"key": "codigo_variante", "titulo": "Variante", "ancho": 140},
            {"key": "total_pares", "titulo": "Pares", "ancho": 80, "tipo": "numero"},
            {"key": "fecha_inicio", "titulo": "F. Inicio", "ancho": 100},
            {"key": "fecha_entrega", "titulo": "F. Entrega", "ancho": 100},
            {"key": "prioridad", "titulo": "Prioridad", "ancho": 90},
            {"key": "estatus", "titulo": "Estatus", "ancho": 110},
        ])
        self.vista.set_renderers(
            fila=self._fila_op,
            claves=self._claves_op,
            estilo=self._estilo_op,
            tarjeta=self._tarjeta_op,
            lista=self._lista_op,
        )
        self.vista.set_buscador_visible(False)
        self.vista.set_exportar_visible(False)
        self.vista.doubleClicked.connect(self._ver_seguimiento)
        layout.addWidget(self.vista)

    def _fila_op(self, op: dict) -> list[str]:
        return [
            op.get("folio", ""),
            op.get("modelo_nombre", ""),
            op.get("codigo_variante", ""),
            str(op.get("total_pares", 0)),
            op.get("fecha_inicio", "") or "",
            op.get("fecha_entrega", "") or "",
            op.get("prioridad", "").capitalize(),
            op.get("estatus", "").replace("_", " ").capitalize(),
        ]

    def _claves_op(self, op: dict) -> list:
        return [
            op.get("folio", ""),
            (op.get("modelo_nombre", "") or "").lower(),
            op.get("codigo_variante", ""),
            float(op.get("total_pares", 0) or 0),
            op.get("fecha_inicio", "") or "",
            op.get("fecha_entrega", "") or "",
            op.get("prioridad", ""),
            op.get("estatus", ""),
        ]

    def _estilo_op(self, op: dict, item, col: int) -> None:
        if col == 7:
            est = op.get("estatus", "")
            if est == "terminada":
                item.setForeground(Qt.darkGreen)
            elif "produccion" in est:
                item.setForeground(Qt.darkYellow)
            elif est == "planeada":
                item.setForeground(Qt.blue)

    def _tarjeta_op(self, op: dict) -> dict:
        est = op.get("estatus", "").replace("_", " ").capitalize()
        return {
            "tile": "produccion",
            "titulo": op.get("folio", ""),
            "subtitulo": f"{op.get('modelo_nombre', '')} · {op.get('codigo_variante', '')}",
            "badge": f"{est} · {op.get('total_pares', 0)} pares",
        }

    def _lista_op(self, op: dict) -> tuple:
        return (
            f"{op.get('folio', '')} · {op.get('prioridad', '').capitalize()}",
            f"{op.get('modelo_nombre', '')} · {op.get('codigo_variante', '')} · "
            f"{op.get('total_pares', 0)} pares · {op.get('fecha_entrega', '') or '—'}",
        )

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
        self.btn_export_m.clicked.connect(lambda: self._exportar_tabla(self.grid_modelos.table, "Modelos"))
        mtoolbar.addWidget(self.txt_buscar_m)
        mtoolbar.addStretch()
        mtoolbar.addWidget(self.btn_nuevo_m)
        mtoolbar.addWidget(self.btn_editar_m)
        mtoolbar.addWidget(self.btn_desactivar_m)
        mtoolbar.addWidget(self.btn_export_m)
        mlayout.addLayout(mtoolbar)

        self.grid_modelos = ComplexGrid()
        self.grid_modelos.set_columnas([
            {"key": "codigo", "titulo": "Código", "ancho": 140},
            {"key": "nombre", "titulo": "Nombre", "ancho": 220},
            {"key": "descripcion", "titulo": "Descripción", "ancho": 320},
        ])
        self.grid_modelos.set_buscador_visible(False)
        self.grid_modelos.set_exportar_visible(False)
        self.grid_modelos.doubleClicked.connect(self._editar_modelo)
        self.grid_modelos.selectionChanged.connect(self._on_modelo_selected)
        mlayout.addWidget(self.grid_modelos)

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
        self.btn_export_v.clicked.connect(lambda: self._exportar_tabla(self.grid_variantes.table, "Variantes"))
        vtoolbar.addWidget(self.txt_buscar_v)
        vtoolbar.addStretch()
        vtoolbar.addWidget(self.btn_nuevo_v)
        vtoolbar.addWidget(self.btn_editar_v)
        vtoolbar.addWidget(self.btn_desactivar_v)
        vtoolbar.addWidget(self.btn_export_v)
        vlayout.addLayout(vtoolbar)

        self.grid_variantes = ComplexGrid()
        self.grid_variantes.set_columnas([
            {"key": "codigo_variante", "titulo": "Código", "ancho": 160},
            {"key": "modelo_nombre", "titulo": "Modelo", "ancho": 150},
            {"key": "talla", "titulo": "Talla", "ancho": 80},
            {"key": "color", "titulo": "Color", "ancho": 110},
            {"key": "piel", "titulo": "Piel", "ancho": 120},
        ])
        self.grid_variantes.set_buscador_visible(False)
        self.grid_variantes.set_exportar_visible(False)
        self.grid_variantes.doubleClicked.connect(self._editar_variante)
        vlayout.addWidget(self.grid_variantes)

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
        self.grid_bom = ComplexGrid()
        self.grid_bom.set_columnas([
            {"key": "insumo_nombre", "titulo": "Insumo", "ancho": 260},
            {"key": "cantidad_por_par", "titulo": "Cant. por Par",
             "ancho": 100, "tipo": "numero"},
            {"key": "unidad_medida", "titulo": "Unidad", "ancho": 100},
            {"key": "stock_actual", "titulo": "Stock Actual",
             "ancho": 110, "tipo": "numero"},
        ])
        self.grid_bom.set_buscador_visible(False)
        self.grid_bom.set_exportar_visible(False)
        blayout.addWidget(self.cmb_bom_modelo)
        blayout.addWidget(self.btn_editar_bom)
        blayout.addWidget(self.grid_bom)

    def _setup_tab_pt(self) -> None:
        layout = QVBoxLayout(self.tab_pt)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        self.btn_export_pt = QPushButton("Exportar Excel")
        self.btn_export_pt.setObjectName("btnPrimary")
        self.btn_export_pt.clicked.connect(lambda: self._exportar_tabla(self.grid_pt.table, "Producto_Terminado"))
        self.btn_print_pt = QPushButton("Imprimir")
        self.btn_print_pt.setObjectName("btnSecondary")
        self.btn_print_pt.clicked.connect(lambda: print_table(self.grid_pt.table, "Producto_Terminado", self))

        btn_refresh_pt = QPushButton("Actualizar")
        btn_refresh_pt.setObjectName("btnPrimary")
        btn_refresh_pt.clicked.connect(self._load_pt)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_pt)
        toolbar.addWidget(self.btn_print_pt)
        toolbar.addWidget(btn_refresh_pt)
        layout.addLayout(toolbar)

        self.grid_pt = ComplexGrid()
        self.grid_pt.set_columnas([
            {"key": "modelo_nombre", "titulo": "Modelo", "ancho": 180},
            {"key": "codigo_variante", "titulo": "Variante", "ancho": 160},
            {"key": "color", "titulo": "Color", "ancho": 120},
            {"key": "piel", "titulo": "Piel", "ancho": 120},
            {"key": "talla", "titulo": "Talla", "ancho": 80},
            {"key": "pares", "titulo": "Pares", "ancho": 90, "tipo": "numero"},
        ])
        self.grid_pt.set_buscador_visible(False)
        self.grid_pt.set_exportar_visible(False)
        layout.addWidget(self.grid_pt)

    def _load_ops(self) -> None:
        try:
            ops = self.controller.listar_ops()
            if hasattr(self, "kanban"):
                self.kanban.recargar()
            self.vista.set_datos(ops)
            self._load_catalogos()
            self._load_pt()
        except Exception as e:
            print(f"Error: {e}")

    def _load_catalogos(self) -> None:
        try:
            modelos = self.controller.listar_modelos()
            self.grid_modelos.set_datos(modelos)
            variantes = self.controller.listar_variantes()
            self.grid_variantes.set_datos(variantes)
        except Exception as e:
            print(f"Error catálogos: {e}")

    def _load_pt(self) -> None:
        try:
            pts = self.controller.listar_pt()
            self.grid_pt.set_datos(pts)
        except Exception as e:
            print(f"Error PT: {e}")

    def _buscar(self, texto: str) -> None:
        if not texto.strip():
            self._load_ops()
            return
        try:
            resultados = self.controller.buscar_ops(texto)
            self.vista.set_datos(resultados)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_modelos(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_modelos(texto)
            self.grid_modelos.set_datos(res)
        except Exception as e:
            print(f"Error: {e}")

    def _buscar_variantes(self, texto: str) -> None:
        if not texto.strip():
            self._load_catalogos()
            return
        try:
            res = self.controller.buscar_variantes(texto)
            self.grid_variantes.set_datos(res)
        except Exception as e:
            print(f"Error: {e}")

    def _nueva_op(self) -> None:
        dlg = DialogOrdenProduccion(self.controller)
        if dlg.exec():
            self._load_ops()

    def _ver_seguimiento(self) -> None:
        op = self.vista.registro_seleccionado()
        if not op:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        dlg = DialogSeguimientoOP(self.controller, op["id"])
        dlg.exec()
        self._load_ops()

    def _avanzar_desde_tabla(self) -> None:
        op = self.vista.registro_seleccionado()
        if not op:
            QMessageBox.information(self, "Seleccionar", "Seleccione una OP.")
            return
        dlg = DialogSeguimientoOP(self.controller, op["id"])
        dlg.exec()
        self._load_ops()

    def _nuevo_modelo(self) -> None:
        dlg = DialogModelo(self.controller, self.inv_controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_modelo(self) -> None:
        m = self.grid_modelos.registro_seleccionado()
        if m is None:
            QMessageBox.information(self, "Seleccionar", "Seleccione un modelo.")
            return
        dlg = DialogModelo(self.controller, self.inv_controller, m["id"])
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_modelo(self) -> None:
        m = self.grid_modelos.registro_seleccionado()
        if m is None:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar '{m['nombre']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_modelo(m["id"])
            self._load_catalogos()

    def _nueva_variante(self) -> None:
        dlg = DialogVariante(self.controller)
        if dlg.exec():
            self._load_catalogos()

    def _editar_variante(self) -> None:
        v = self.grid_variantes.registro_seleccionado()
        if v is None:
            return
        dlg = DialogVariante(self.controller, v["id"])
        if dlg.exec():
            self._load_catalogos()

    def _desactivar_variante(self) -> None:
        v = self.grid_variantes.registro_seleccionado()
        if v is None:
            return
        resp = QMessageBox.question(self, "Confirmar", f"¿Desactivar variante '{v['codigo_variante']}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_variante(v["id"])
            self._load_catalogos()

    def _on_modelo_selected(self) -> None:
        m = self.grid_modelos.registro_seleccionado()
        if m is not None:
            self.cmb_bom_modelo.setText(f"[{m.get('codigo', '')}] {m.get('nombre', '')}")
            self.btn_editar_bom.setEnabled(tiene(self._permisos, "produccion", "editar"))
            self._modelo_bom_id = m["id"]
            self._modelo_bom_nombre = m.get("nombre", "")
            self._cargar_bom(m["id"])
        else:
            self.cmb_bom_modelo.clear()
            self.btn_editar_bom.setEnabled(False)
            self.grid_bom.set_datos([])

    def _cargar_bom(self, modelo_id: int) -> None:
        bom = self.controller.obtener_bom(modelo_id)
        self.grid_bom.set_datos(bom)

    def _editar_bom(self) -> None:
        if hasattr(self, "_modelo_bom_id"):
            dlg = DialogBOM(self.controller, self.inv_controller,
                             self._modelo_bom_id, self._modelo_bom_nombre)
            if dlg.exec():
                self._cargar_bom(self._modelo_bom_id)

    def _exportar_tabla(self, table, nombre: str) -> None:
        path = export_table_to_excel(table, nombre, self)
        if path:
            notificar_flotante(f"Excel guardado en:\n{path}",
                               tipo="success", titulo="Exportado", host=self)
