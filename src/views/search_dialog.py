"""Diálogo de búsqueda global (Command Palette) — Ctrl+K.

Busca en todos los módulos del sistema y permite navegar directamente
al resultado seleccionado.
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QVBoxLayout, QWidget,
)

from src.utils.icons import mono_icon


_FUENTES: list[dict] = []


def _registrar_fuentes() -> None:
    if _FUENTES:
        return
    try:
        from src.controllers.ordenes_compra_controller import (
            OrdenesCompraController)
        ctrl_oc = OrdenesCompraController()
        _FUENTES.append({
            "modulo": "Órdenes de Compra",
            "icono": "oc", "color": "#1892D4",
            "buscar": lambda t: ctrl_oc.buscar_ordenes(t),
            "etiquetar": lambda r: (
                f"{r.get('folio', '')} — "
                f"{r.get('proveedor_nombre', r.get('nombre', ''))}"),
            "accion": lambda r: ("ordenes_compra", r),
        })
    except Exception:
        pass

    try:
        from src.controllers.produccion_controller import ProduccionController
        ctrl_prod = ProduccionController()
        _FUENTES.append({
            "modulo": "Órdenes de Producción",
            "icono": "produccion", "color": "#16A34A",
            "buscar": lambda t: ctrl_prod.buscar_ops(t),
            "etiquetar": lambda r: (
                f"{r.get('folio', '')} — "
                f"{r.get('modelo_nombre', r.get('nombre', ''))}"),
            "accion": lambda r: ("produccion", r),
        })
        _FUENTES.append({
            "modulo": "Modelos",
            "icono": "produccion", "color": "#16A34A",
            "buscar": lambda t: ctrl_prod.buscar_modelos(t),
            "etiquetar": lambda r: (
                f"{r.get('codigo', '')} — {r.get('nombre', '')}"),
            "accion": lambda r: ("produccion", r),
        })
    except Exception:
        pass

    try:
        from src.controllers.inventario_controller import InventarioController
        ctrl_inv = InventarioController()
        _FUENTES.append({
            "modulo": "Inventario (Insumos)",
            "icono": "inventario", "color": "#E3C14D",
            "buscar": lambda t: ctrl_inv.buscar_insumos(t),
            "etiquetar": lambda r: (
                f"{r.get('codigo', '')} — {r.get('nombre', '')}"),
            "accion": lambda r: ("inventario", r),
        })
    except Exception:
        pass

    try:
        from src.controllers.clientes_controller import ClientesController
        ctrl_cli = ClientesController()
        _FUENTES.append({
            "modulo": "Clientes",
            "icono": "clientes", "color": "#77307E",
            "buscar": lambda t: ctrl_cli.buscar_clientes(t),
            "etiquetar": lambda r: (
                f"{r.get('nombre', '')} "
                f"({r.get('nombre_comercial', '')})"),
            "accion": lambda r: ("clientes", r),
        })
        _FUENTES.append({
            "modulo": "Pedidos",
            "icono": "clientes", "color": "#77307E",
            "buscar": lambda t: ctrl_cli.buscar_pedidos(t),
            "etiquetar": lambda r: (
                f"{r.get('folio', '')} — "
                f"{r.get('cliente_nombre', r.get('nombre', ''))}"),
            "accion": lambda r: ("clientes", r),
        })
    except Exception:
        pass


class _BuscadorHilo(QThread):
    resultados = Signal(list)

    def __init__(self, termino: str, parent=None) -> None:
        super().__init__(parent)
        self._termino = termino

    def run(self) -> None:
        todos: list[dict] = []
        for fuente in _FUENTES:
            try:
                items = fuente["buscar"](self._termino)
                for item in (items or []):
                    todos.append({
                        "texto": fuente["etiquetar"](item),
                        "modulo": fuente["modulo"],
                        "icono": fuente["icono"],
                        "color": fuente["color"],
                        "registro": item,
                        "accion": fuente["accion"],
                    })
            except Exception:
                continue
        self.resultados.emit(todos)


class DialogBuscadorGlobal(QDialog):
    """Command Palette estilo VS Code / Spotlight.

    Abre con Ctrl+K, busca en todos los módulos, navega con Enter/Doble clic.
    """

    # Señal: (nombre_modulo, registro)
    navegar = Signal(str, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Buscador Global")
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(600)
        self.setFixedHeight(480)
        self._hilo: _BuscadorHilo | None = None
        self._resultado_actual: list[dict] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        container = QWidget()
        container.setObjectName("searchPalette")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        search_row = QHBoxLayout()
        lbl_icon = QLabel()
        lbl_icon.setPixmap(mono_icon("buscar", 20, "#64748b").pixmap(20, 20))
        search_row.addWidget(lbl_icon)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setObjectName("searchInput")
        self.txt_buscar.setPlaceholderText(
            "Buscar en OC, Producción, Inventario, Clientes...")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.textChanged.connect(self._buscar)
        search_row.addWidget(self.txt_buscar, 1)
        lay.addLayout(search_row)

        self.lbl_hint = QLabel("Escriba para buscar en todos los módulos")
        self.lbl_hint.setObjectName("searchHint")
        lay.addWidget(self.lbl_hint)

        self.lista = QListWidget()
        self.lista.setObjectName("searchResults")
        self.lista.setUniformItemSizes(True)
        self.lista.itemDoubleClicked.connect(self._ejecutar)
        lay.addWidget(self.lista, 1)

        outer.addWidget(container)

        self.txt_buscar.returnPressed.connect(self._ejecutar_seleccion)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.txt_buscar.clear()
        self.lista.clear()
        self.lbl_hint.setText("Escriba para buscar en todos los módulos")
        self.txt_buscar.setFocus()

    def _buscar(self, texto: str) -> None:
        if self._hilo and self._hilo.isRunning():
            self._hilo.terminate()
            self._hilo.wait()
        termino = texto.strip()
        if not termino:
            self.lista.clear()
            self.lbl_hint.setText("Escriba para buscar en todos los módulos")
            self._resultado_actual.clear()
            return
        if len(termino) < 2:
            self.lbl_hint.setText("Escriba al menos 2 caracteres...")
            return
        self.lbl_hint.setText("Buscando...")
        _registrar_fuentes()
        self._hilo = _BuscadorHilo(termino, self)
        self._hilo.resultados.connect(self._mostrar_resultados)
        self._hilo.start()

    def _mostrar_resultados(self, items: list[dict]) -> None:
        self._resultado_actual = items
        self.lista.clear()
        if not items:
            self.lbl_hint.setText("Sin resultados")
            return
        self.lbl_hint.setText(f"{len(items)} resultado(s) encontrado(s)")
        modulo_actual = ""
        for item in items:
            if item["modulo"] != modulo_actual:
                modulo_actual = item["modulo"]
                sep = QListWidgetItem(f"── {modulo_actual} ──")
                sep.setFlags(Qt.ItemFlag.NoItemFlags)
                sep.setData(Qt.ItemDataRole.UserRole, None)
                font = sep.font()
                font.setBold(True)
                sep.setFont(font)
                self.lista.addItem(sep)
            icono = mono_icon(item["icono"], 18, item["color"])
            wi = QListWidgetItem(icono, item["texto"])
            wi.setData(Qt.ItemDataRole.UserRole, item)
            self.lista.addItem(wi)

    def _ejecutar_seleccion(self) -> None:
        item = self.lista.currentItem()
        if item:
            self._ejecutar(item)

    def _ejecutar(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        modulo = data.get("modulo", "")
        registro = data.get("registro", {})
        mod_map = {
            "Órdenes de Compra": "ordenes_compra",
            "Órdenes de Producción": "produccion",
            "Modelos": "produccion",
            "Inventario (Insumos)": "inventario",
            "Clientes": "clientes",
            "Pedidos": "clientes",
        }
        mod_clave = mod_map.get(modulo, modulo)
        self.navegar.emit(mod_clave, registro)
        self.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            rows = self.lista.count()
            if rows == 0:
                return
            curr = self.lista.currentRow()
            if event.key() == Qt.Key.Key_Up:
                nueva = max(0, curr - 1)
            else:
                nueva = min(rows - 1, curr + 1)
            self.lista.setCurrentRow(nueva)
            return
        super().keyPressEvent(event)
