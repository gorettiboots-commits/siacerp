from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea, QStackedWidget,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.utils.icons import mono_icon, tile_icon
from src.utils.table_utils import configurar_tabla_excel


class _ItemOrdenable(QTableWidgetItem):
    def __lt__(self, other) -> bool:
        a = self.data(Qt.UserRole)
        b = other.data(Qt.UserRole)
        if a is None and b is None:
            return super().__lt__(other)
        if a is None:
            return True
        if b is None:
            return False
        try:
            return a < b
        except TypeError:
            return super().__lt__(other)


class _Tarjeta(QFrame):
    clicked = Signal()
    doubleClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("odooCard")
        self.setCursor(Qt.PointingHandCursor)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._layout.setSpacing(6)
        self._icono = QLabel()
        self._icono.setFixedSize(46, 46)
        self._icono.setAlignment(Qt.AlignCenter)
        self._titulo = QLabel()
        self._titulo.setObjectName("cardTitle")
        self._titulo.setWordWrap(True)
        self._subtitulo = QLabel()
        self._subtitulo.setObjectName("sectionSubtitle")
        self._subtitulo.setWordWrap(True)
        self._badge = QLabel()
        self._badge.setObjectName("cardBadge")
        self._badge.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._icono)
        self._layout.addWidget(self._titulo)
        self._layout.addWidget(self._subtitulo)
        self._layout.addStretch()
        self._layout.addWidget(self._badge)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class OdooListView(QWidget):
    """Selector de vista estilo Odoo: Lista / Tabla / Iconos con ordenación por columna.

    La vista 'Tabla' permite ordenar haciendo clic en el encabezado
    (alterna ascendente/descendente con indicador de flecha).
    """
    doubleClicked = Signal()
    selectionChanged = Signal()

    def __init__(self, encabezados: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._encabezados = list(encabezados)
        self._fila_fn = None
        self._claves_fn = None
        self._estilo_fn = None
        self._tarjeta_fn = None
        self._lista_fn = None
        self._filtro_fn = None
        self._registros: list = []
        self._visibles: list = []
        self._seleccionado = None
        self._sort_col = -1
        self._sort_asc = True
        self._idx_lista = 0
        self._idx_tabla = 1
        self._idx_iconos = 2
        self._setup_ui()
        self.set_vista("tabla")

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        bar = QHBoxLayout()
        bar.addStretch()
        self._lbl_count = QLabel("")
        self._lbl_count.setObjectName("sectionSubtitle")
        bar.addWidget(self._lbl_count)
        bar.addSpacing(4)

        self._btn_lista = self._crear_boton_vista("lista", "Lista")
        self._btn_tabla = self._crear_boton_vista("tabla", "Tabla")
        self._btn_iconos = self._crear_boton_vista("iconos", "Iconos")
        grupo = QButtonGroup(self)
        grupo.setExclusive(True)
        for btn in (self._btn_lista, self._btn_tabla, self._btn_iconos):
            grupo.addButton(btn)
            bar.addWidget(btn)
        lay.addLayout(bar)

        self._stack = QStackedWidget()
        self._pag_lista = QListWidget()
        self._pag_lista.itemSelectionChanged.connect(self._sincronizar_seleccion)
        self._pag_lista.itemDoubleClicked.connect(lambda _it: self._emit_doble())
        self._stack.addWidget(self._pag_lista)

        self._pag_tabla = QTableWidget()
        self._pag_tabla.setColumnCount(len(self._encabezados) + 1)
        self._pag_tabla.setHorizontalHeaderLabels(self._encabezados + ["ID"])
        self._pag_tabla.setColumnHidden(len(self._encabezados), True)
        self._pag_tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self._pag_tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self._pag_tabla.setAlternatingRowColors(True)
        configurar_tabla_excel(self._pag_tabla)
        header = self._pag_tabla.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._on_header_clicked)
        self._pag_tabla.itemSelectionChanged.connect(self._sincronizar_seleccion)
        self._pag_tabla.cellDoubleClicked.connect(lambda _r, _c: self._emit_doble())
        self._stack.addWidget(self._pag_tabla)

        self._pag_iconos = QScrollArea()
        self._pag_iconos.setWidgetResizable(True)
        self._cont_iconos = QWidget()
        self._grid = QGridLayout(self._cont_iconos)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(12)
        self._grid.setAlignment(Qt.AlignTop)
        self._pag_iconos.setWidget(self._cont_iconos)
        self._stack.addWidget(self._pag_iconos)

        lay.addWidget(self._stack)

    def _crear_boton_vista(self, glifo: str, texto: str) -> QPushButton:
        btn = QPushButton(texto)
        btn.setObjectName("viewSwitch")
        btn.setIcon(mono_icon(glifo, 18, "#475569"))
        btn.setIconSize(btn.iconSize())
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _checked, v=texto.lower(): self.set_vista(v))
        return btn

    # ---- Configuración de renderizadores ----
    def set_renderers(self, fila=None, claves=None, estilo=None,
                      tarjeta=None, lista=None) -> None:
        self._fila_fn = fila
        self._claves_fn = claves
        self._estilo_fn = estilo
        self._tarjeta_fn = tarjeta
        self._lista_fn = lista

    # ---- Datos ----
    def set_datos(self, registros) -> None:
        self._registros = list(registros or [])
        self._aplicar_filtro()

    def set_filtro(self, fn) -> None:
        self._filtro_fn = fn
        if self._registros:
            self._aplicar_filtro()

    def _aplicar_filtro(self) -> None:
        if self._filtro_fn:
            self._visibles = [r for r in self._registros if self._filtro_fn(r)]
        else:
            self._visibles = list(self._registros)
        if self._sort_col >= 0:
            self._ordenar(self._sort_col, self._sort_asc, actualizar_indicator=False)
        self._render()

    # ---- Vistas ----
    def set_vista(self, vista: str) -> None:
        mapa = {
            "lista": (self._idx_lista, self._btn_lista),
            "tabla": (self._idx_tabla, self._btn_tabla),
            "iconos": (self._idx_iconos, self._btn_iconos),
        }
        idx, btn = mapa[vista]
        btn.setChecked(True)
        self._stack.setCurrentIndex(idx)
        if vista == "iconos":
            self._render_iconos()

    def vista_actual(self) -> str:
        return {self._idx_lista: "lista", self._idx_tabla: "tabla",
                self._idx_iconos: "iconos"}.get(self._stack.currentIndex(), "tabla")

    def registro_seleccionado(self):
        idx = self._stack.currentIndex()
        if idx == self._idx_iconos:
            return self._seleccionado
        row = self._pag_lista.currentRow() if idx == self._idx_lista else self._pag_tabla.currentRow()
        if 0 <= row < len(self._visibles):
            return self._visibles[row]
        return None

    @property
    def table(self) -> QTableWidget:
        return self._pag_tabla

    # ---- Render ----
    def _render(self) -> None:
        self._render_tabla()
        self._render_lista()
        self._render_iconos()
        n = len(self._visibles)
        self._lbl_count.setText(f"{n} registro{'s' if n != 1 else ''}")

    def _render_tabla(self) -> None:
        t = self._pag_tabla
        t.setRowCount(len(self._visibles))
        for i, rec in enumerate(self._visibles):
            fila = self._fila_fn(rec) if self._fila_fn else []
            claves = self._claves_fn(rec) if self._claves_fn else None
            for c in range(len(self._encabezados)):
                texto = fila[c] if c < len(fila) else ""
                item = _ItemOrdenable(str(texto))
                if claves and c < len(claves):
                    clave = claves[c]
                elif isinstance(texto, (int, float)):
                    clave = float(texto)
                else:
                    clave = str(texto).lower()
                item.setData(Qt.UserRole, clave)
                t.setItem(i, c, item)
            t.setItem(i, len(self._encabezados),
                      QTableWidgetItem(str(self._id_de(rec))))
            if self._estilo_fn:
                for c in range(len(self._encabezados)):
                    self._estilo_fn(rec, t.item(i, c), c)

    def _render_lista(self) -> None:
        l = self._pag_lista
        l.blockSignals(True)
        l.clear()
        for rec in self._visibles:
            if self._lista_fn:
                titulo, subtitulo = self._lista_fn(rec)
            else:
                fila = self._fila_fn(rec) if self._fila_fn else []
                titulo = str(fila[0]) if fila else ""
                subtitulo = "  |  ".join(str(x) for x in fila[1:])
            it = QListWidgetItem(f"{titulo}\n{subtitulo}")
            it.setToolTip(subtitulo)
            l.addItem(it)
        l.blockSignals(False)

    def _render_iconos(self) -> None:
        while self._grid.count():
            w = self._grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        cols = max(1, self._cont_iconos.width() // 230)
        for i, rec in enumerate(self._visibles):
            card = _Tarjeta()
            datos = self._tarjeta_fn(rec) if self._tarjeta_fn else {}
            tile = datos.get("tile")
            if tile:
                try:
                    pixmap = tile_icon(tile, 44).pixmap(44, 44)
                except KeyError:
                    pixmap = mono_icon(
                        tile, 44, datos.get("color", "#4f46e5")).pixmap(44, 44)
                card._icono.setPixmap(pixmap)
            else:
                card._icono.setPixmap(mono_icon(
                    datos.get("icono", "oc"), 44, datos.get("color", "#4f46e5")).pixmap(44, 44))
            card._titulo.setText(datos.get("titulo", ""))
            card._subtitulo.setText(datos.get("subtitulo", ""))
            badge = datos.get("badge", "")
            card._badge.setText(badge)
            card._badge.setVisible(bool(badge))
            card.setProperty("rec", rec)
            card.clicked.connect(lambda r=rec: self._seleccionar_tarjeta(r))
            card.doubleClicked.connect(self._emit_doble)
            self._grid.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._stack.currentIndex() == self._idx_iconos:
            self._render_iconos()

    # ---- Ordenación ----
    def _on_header_clicked(self, col: int) -> None:
        if col >= len(self._encabezados):
            return
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        self._ordenar(self._sort_col, self._sort_asc)

    def _ordenar(self, col: int, asc: bool, actualizar_indicator: bool = True) -> None:
        def clave(rec):
            claves = self._claves_fn(rec) if self._claves_fn else None
            if claves and col < len(claves):
                k = claves[col]
            else:
                fila = self._fila_fn(rec) if self._fila_fn else []
                k = fila[col] if col < len(fila) else ""
            if k is None:
                return (1, "")
            return (0, k)

        self._visibles.sort(key=clave, reverse=not asc)
        if actualizar_indicator:
            self._pag_tabla.horizontalHeader().setSortIndicator(
                col, Qt.AscendingOrder if asc else Qt.DescendingOrder)
        self._render()

    # ---- Selección ----
    def _seleccionar_tarjeta(self, rec) -> None:
        self._seleccionado = rec
        for i in range(self._grid.count()):
            w = self._grid.itemAt(i).widget()
            if isinstance(w, _Tarjeta):
                seleccionada = w.property("rec") is rec
                w.setProperty("selected", seleccionada)
                w.style().unpolish(w)
                w.style().polish(w)
        self.selectionChanged.emit()

    def _sincronizar_seleccion(self) -> None:
        self._seleccionado = self.registro_seleccionado()
        self.selectionChanged.emit()

    def _emit_doble(self) -> None:
        if self.registro_seleccionado() is not None:
            self.doubleClicked.emit()

    @staticmethod
    def _id_de(rec):
        return rec.get("id") if isinstance(rec, dict) else getattr(rec, "id", "")
