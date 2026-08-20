from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.components.grid_hibrido import GridHibrido
from src.controllers.inventario_controller import InventarioController
from src.models.accesos_model import tiene
from src.views.dialogs import (
    DialogInsumo, DialogMovimientoMultiPartida, DialogMovimientoStock,
)


class StockView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.controller = InventarioController()
        self._setup_ui()
        self._load_insumos()

    def set_permisos(self, permisos) -> None:
        self.vista.establecer_boton_modulo(
            "nuevo", tiene(permisos, "inventario", "crear"))
        self.vista.establecer_boton_modulo(
            "movimiento", tiene(permisos, "inventario", "crear"))
        self.vista.set_exportar_visible(
            tiene(permisos, "inventario", "exportar"))
        self.grid_mov.set_exportar_visible(
            tiene(permisos, "inventario", "exportar"))
        self.grid_conflicto.set_exportar_visible(
            tiene(permisos, "inventario", "exportar"))

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

        hlayout.addLayout(title_col)
        hlayout.addStretch()

        self.tabs = QTabWidget()
        self.tab_insumos = QWidget()
        self.tab_movimientos = QWidget()
        self.tab_conflicto = QWidget()
        self.tabs.addTab(self.tab_insumos, "Insumos")
        self.tabs.addTab(self.tab_movimientos, "Movimientos")
        self.tabs.addTab(self.tab_conflicto, "Insumos en Conflicto")
        self._setup_tab_insumos()
        self._setup_tab_movimientos()
        self._setup_tab_conflicto()
        layout.addWidget(header)
        layout.addWidget(self.tabs)

    def _setup_tab_insumos(self) -> None:
        layout = QVBoxLayout(self.tab_insumos)
        layout.setContentsMargins(0, 8, 0, 0)

        self.vista = GridHibrido()
        self.vista.agregar_boton_toolbar(
            "nuevo", "+ Nuevo Insumo", "mas", "#ffffff", self._nuevo_insumo)
        self.vista.agregar_boton_toolbar(
            "movimiento", "Movimiento", "toggle", "#ffffff",
            self._registrar_movimiento)
        self.vista.agregar_boton_toolbar(
            "actualizar", "Actualizar", "buscar", "#1892D4", self._load_insumos)
        self.vista.set_columnas([
            {"key": "codigo", "titulo": "Codigo", "ancho": 120},
            {"key": "nombre", "titulo": "Nombre", "ancho": 220},
            {"key": "categoria", "titulo": "Categoria", "ancho": 140},
            {"key": "unidad_medida", "titulo": "Unidad", "ancho": 90},
            {"key": "stock_actual", "titulo": "Stock Actual", "ancho": 110, "tipo": "numero"},
            {"key": "stock_minimo", "titulo": "Stock Minimo", "ancho": 110, "tipo": "numero"},
        ])
        self.vista.set_renderers(
            fila=self._fila_insumo,
            claves=self._claves_insumo,
            estilo=self._estilo_insumo,
            tarjeta=self._tarjeta_insumo,
            lista=self._lista_insumo,
        )
        # Acciones en la columna del grid
        self.vista.set_acciones([
            {"texto": "Editar", "icono": "editar", "color": "#2563eb",
             "callback": lambda rec: self._editar_insumo_directo(rec)},
            {"texto": "Desactivar", "icono": "eliminar", "color": "#dc2626",
             "callback": lambda rec: self._desactivar_insumo_directo(rec)},
            {"texto": "Kardex", "icono": "inventario", "color": "#0d9488",
             "callback": lambda rec: self._imprimir_kardex_directo(rec)},
        ])
        self.vista.doubleClicked.connect(self._editar_insumo)
        layout.addWidget(self.vista)

    def _setup_tab_movimientos(self) -> None:
        layout = QVBoxLayout(self.tab_movimientos)
        layout.setContentsMargins(0, 8, 0, 0)

        self.grid_mov = GridHibrido()
        self.grid_mov.agregar_boton_toolbar(
            "documento", "Documento", "pdf", "#1892D4",
            self._imprimir_documento_movimiento)
        self.grid_mov.set_columnas([
            {"key": "folio", "titulo": "Folio", "ancho": 120},
            {"key": "created_at", "titulo": "Fecha", "ancho": 150},
            {"key": "insumo_nombre", "titulo": "Insumo", "ancho": 200},
            {"key": "tipo_movimiento", "titulo": "Tipo", "ancho": 100},
            {"key": "cantidad", "titulo": "Cantidad", "ancho": 100, "tipo": "numero"},
            {"key": "referencia_tipo", "titulo": "Referencia", "ancho": 130},
            {"key": "observaciones", "titulo": "Observaciones", "ancho": 200},
        ])
        self.grid_mov.set_renderers(fila=self._fila_mov, claves=self._claves_mov)
        layout.addWidget(self.grid_mov)

    def _setup_tab_conflicto(self) -> None:
        layout = QVBoxLayout(self.tab_conflicto)
        layout.setContentsMargins(0, 8, 0, 0)

        self.grid_conflicto = GridHibrido()
        self.grid_conflicto.agregar_boton_toolbar(
            "actualizar", "Actualizar", "buscar", "#1892D4",
            self._load_conflicto)
        self.grid_conflicto.set_columnas([
            {"key": "codigo", "titulo": "Codigo", "ancho": 120},
            {"key": "nombre", "titulo": "Nombre", "ancho": 220},
            {"key": "categoria", "titulo": "Categoria", "ancho": 140},
            {"key": "unidad_medida", "titulo": "Unidad", "ancho": 90},
            {"key": "stock_actual", "titulo": "Stock Actual", "ancho": 110, "tipo": "numero"},
            {"key": "stock_minimo", "titulo": "Stock Minimo", "ancho": 110, "tipo": "numero"},
            {"key": "deficit", "titulo": "Deficit", "ancho": 100, "tipo": "numero"},
        ])
        self.grid_conflicto.set_renderers(
            fila=self._fila_conflicto,
            claves=self._claves_conflicto,
            estilo=self._estilo_conflicto,
        )
        layout.addWidget(self.grid_conflicto)

    # ----------------------------------------------------------------
    # Renderers Insumos
    # ----------------------------------------------------------------

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
            "subtitulo": f"{ins.get('codigo', '')} . {ins.get('categoria', '')}",
            "badge": f"{stock} {unidad}",
        }

    def _lista_insumo(self, ins: dict) -> tuple:
        return (
            ins.get("nombre", ""),
            f"{ins.get('codigo', '')} . {ins.get('categoria', '')} . "
            f"{ins.get('stock_actual', 0)} {ins.get('unidad_medida', '')}",
        )

    # ----------------------------------------------------------------
    # Renderers Movimientos
    # ----------------------------------------------------------------

    def _fila_mov(self, m: dict) -> list[str]:
        return [
            m.get("folio", "") or m.get("observaciones", "") or "",
            m.get("created_at", ""),
            m.get("insumo_nombre", ""),
            m.get("tipo_movimiento", "").capitalize(),
            str(m.get("cantidad", 0)),
            m.get("referencia_tipo", "") or "",
            m.get("observaciones", "") or "",
        ]

    def _claves_mov(self, m: dict) -> list:
        return [
            m.get("folio", "") or m.get("observaciones", "") or "",
            m.get("created_at", ""),
            m.get("insumo_nombre", ""),
            m.get("tipo_movimiento", ""),
            float(m.get("cantidad", 0) or 0),
            m.get("referencia_tipo", "") or "",
            m.get("observaciones", "") or "",
        ]

    # ----------------------------------------------------------------
    # Renderers Insumos en Conflicto
    # ----------------------------------------------------------------

    def _fila_conflicto(self, ins: dict) -> list[str]:
        stock = float(ins.get("stock_actual", 0) or 0)
        stock_min = float(ins.get("stock_minimo", 0) or 0)
        deficit = stock_min - stock if stock < stock_min else 0
        return [
            ins.get("codigo", ""),
            ins.get("nombre", ""),
            ins.get("categoria", ""),
            ins.get("unidad_medida", ""),
            str(stock),
            str(stock_min),
            str(round(deficit, 2)),
        ]

    def _claves_conflicto(self, ins: dict) -> list:
        stock = float(ins.get("stock_actual", 0) or 0)
        stock_min = float(ins.get("stock_minimo", 0) or 0)
        deficit = stock_min - stock if stock < stock_min else 0
        return [
            ins.get("codigo", ""),
            (ins.get("nombre", "") or "").lower(),
            (ins.get("categoria", "") or "").lower(),
            ins.get("unidad_medida", ""),
            stock,
            stock_min,
            deficit,
        ]

    def _estilo_conflicto(self, ins: dict, item, col: int) -> None:
        stock = float(ins.get("stock_actual", 0) or 0)
        stock_min = float(ins.get("stock_minimo", 0) or 0)
        if stock < stock_min:
            if col in (4, 5):
                item.setForeground(Qt.red)
            if col == 6:
                item.setForeground(Qt.darkRed)

    # ----------------------------------------------------------------
    # Carga de datos
    # ----------------------------------------------------------------

    def _load_insumos(self) -> None:
        try:
            insumos = self.controller.listar_insumos()
            self.vista.set_datos(insumos)
            self._load_movimientos()
            self._load_conflicto()
        except Exception as e:
            print(f"Error: {e}")

    def _load_movimientos(self) -> None:
        try:
            movs = self.controller.listar_movimientos()
            self.grid_mov.set_datos(movs)
        except Exception as e:
            print(f"Error movimientos: {e}")

    def _load_conflicto(self) -> None:
        try:
            bajos = self.controller.stock_bajo()
            self.grid_conflicto.set_datos(bajos)
        except Exception as e:
            print(f"Error conflicto: {e}")

    # ----------------------------------------------------------------
    # Acciones Insumos (desde columna del grid)
    # ----------------------------------------------------------------

    def _editar_insumo_directo(self, rec: dict) -> None:
        dlg = DialogInsumo(self.controller, rec["id"])
        if dlg.exec():
            self._load_insumos()

    def _desactivar_insumo_directo(self, rec: dict) -> None:
        nombre = rec.get("nombre", "")
        resp = QMessageBox.question(
            self, "Confirmar", f"Desactivar '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self.controller.desactivar_insumo(rec["id"])
            self._load_insumos()

    def _imprimir_kardex_directo(self, rec: dict) -> None:
        from src.utils.kardex_print import imprimir_kardex
        movimientos = self.controller.listar_kardex(rec["id"])
        if not movimientos:
            QMessageBox.information(
                self, "Kardex", "El insumo no tiene movimientos.")
            return
        imprimir_kardex(rec, movimientos, self)

    # ----------------------------------------------------------------
    # Acciones Movimientos
    # ----------------------------------------------------------------

    def _imprimir_todas_movimientos(self) -> None:
        """Imprime todas las partidas visibles en el grid de movimientos."""
        self.grid_mov.imprimir()

    def _imprimir_documento_movimiento(self) -> None:
        """Imprime el documento del movimiento seleccionado por folio."""
        registro = self.grid_mov.registro_seleccionado()
        if not registro:
            QMessageBox.information(
                self, "Seleccionar",
                "Seleccione un movimiento de la lista.")
            return
        ref_tipo = registro.get("referencia_tipo", "")
        ref_id = registro.get("referencia_id")
        if ref_tipo == "movimiento" and ref_id:
            from src.utils.movimiento_print import imprimir_movimiento_documento
            imprimir_movimiento_documento(ref_id, self)
        else:
            QMessageBox.information(
                self, "Documento",
                "El registro seleccionado no tiene un documento asociado.")

    # ----------------------------------------------------------------
    # Acciones generales
    # ----------------------------------------------------------------

    def _nuevo_insumo(self) -> None:
        dlg = DialogInsumo(self.controller)
        if dlg.exec():
            self._load_insumos()

    def _editar_insumo(self) -> None:
        ins = self.vista.registro_seleccionado()
        if not ins:
            QMessageBox.information(
                self, "Seleccionar", "Seleccione un insumo.")
            return
        dlg = DialogInsumo(self.controller, ins["id"])
        if dlg.exec():
            self._load_insumos()

    def _registrar_movimiento(self) -> None:
        ins = self.vista.registro_seleccionado()
        dlg = DialogMovimientoMultiPartida(
            self.controller, ins["id"] if ins else None)
        if dlg.exec():
            mov_id = dlg.obtener_movimiento_id()
            if mov_id:
                resp = QMessageBox.question(
                    self, "Imprimir documento",
                    "Movimiento registrado. Desea imprimir el documento?",
                    QMessageBox.Yes | QMessageBox.No)
                if resp == QMessageBox.Yes:
                    from src.utils.movimiento_print import (
                        imprimir_movimiento_documento,
                    )
                    imprimir_movimiento_documento(mov_id, self)
            self._load_insumos()
