"""Control de tabla reutilizable (homologación de controles).

Modos de vista:
- "filas":  tabla clásica con renglones.
- "lista":  lista vertical con miniatura del registro.
- "iconos": rejilla de iconos con la imagen del registro.

Características:
- Ancho de columnas ajustable por arrastre o doble clic (autoajuste al contenido).
- Ordenamiento por columna al hacer clic en el encabezado (ascendente/descendente).
- Agrupación por un campo (opcional: set_group_key / set_group_options).
- Imagen del registro con respaldo a "default.jpg" en la raíz del proyecto.
"""

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QListView,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

_MODOS = ("filas", "lista", "iconos")
_RECORD_ROLE = Qt.UserRole + 1

from src.utils.icons import mono_icon

_RAIZ_PROYECTO = Path(__file__).resolve().parents[2]


def _valor_orden(value) -> tuple:
    """Convierte un valor a una tupla comparable para ordenar columnas."""
    if value is None:
        return (0, "")
    if isinstance(value, (int, float)):
        return (1, value)
    texto = str(value).strip()
    if not texto:
        return (0, "")
    numero = texto.replace("$", "").replace(",", "").replace(" ", "")
    try:
        return (1, float(numero))
    except ValueError:
        return (2, texto.lower())


class _ItemLista(QWidget):
    """Renglón de la vista "lista": miniatura + título + subtítulo."""

    def __init__(self, pixmap: QPixmap, titulo: str, subtitulo: str,
                 parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(12)

        img = QLabel()
        img.setFixedSize(48, 48)
        if not pixmap.isNull():
            img.setPixmap(pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        img.setStyleSheet("background: transparent;")
        lay.addWidget(img)

        col = QVBoxLayout()
        col.setSpacing(0)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-weight: 600; color: #1e293b; font-size: 13px;")
        lbl_titulo.setWordWrap(True)
        col.addWidget(lbl_titulo)
        if subtitulo:
            lbl_sub = QLabel(subtitulo)
            lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
            col.addWidget(lbl_sub)
        lay.addLayout(col, 1)


class GorettiTable(QWidget):
    """Tabla reutilizable con vistas filas/lista/iconos, ordenamiento, agrupación
    y redimensionado de columnas estilo Excel."""

    recordDoubleClicked = Signal(object)
    currentRecordChanged = Signal(object)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        columns: Optional[list[dict]] = None,
        mode: str = "filas",
        id_key: str = "id",
        title_key=None,
        subtitle_key=None,
        image_key: Optional[str] = None,
        image_resolver: Optional[Callable] = None,
        default_image: str = "default.jpg",
        sortable: bool = True,
        selection_mode: str = "single",
        image_size=(48, 48),
        background_fn: Optional[Callable] = None,
        foreground_fn: Optional[Callable] = None,
        show_mode_selector: bool = False,
        alternating: bool = True,
        row_height: Optional[int] = None,
    ) -> None:
        super().__init__(parent)
        self._columns = list(columns or [])
        self._records: list[dict] = []
        self._display: list[dict] = []
        self._mode = "filas"
        self._id_key = id_key
        self._title_key = title_key
        self._subtitle_key = subtitle_key
        self._image_key = image_key
        self._image_resolver = image_resolver
        self._default_image = default_image
        self._sortable = sortable
        self._sort_col: Optional[int] = None
        self._sort_order = Qt.AscendingOrder
        self._group_key: Optional[str] = None
        self._selection_mode = selection_mode
        self._image_size = QSize(*image_size)
        self._background_fn = background_fn
        self._foreground_fn = foreground_fn
        self._alternating = alternating
        self._row_height = row_height
        self._cache_pixmap: dict = {}

        self._default_pixmap = self._cargar_imagen_default()

        self._setup_ui()
        self.set_mode(mode)
        self._modo_selector_visible = show_mode_selector
        self._toolbar_modos.setVisible(show_mode_selector)

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._toolbar_modos = self._crear_toolbar()
        layout.addWidget(self._toolbar_modos)

        self._stack = QStackedWidget()
        self.table = QTableWidget()
        self.list = QListWidget()
        self._stack.addWidget(self.table)
        self._stack.addWidget(self.list)
        layout.addWidget(self._stack, 1)

        self._configurar_tabla()
        self._configurar_lista()

    def _crear_toolbar(self) -> QWidget:
        bar = QWidget()
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self._grupo_modos = QButtonGroup(self)
        self._grupo_modos.setExclusive(True)
        self._btn_modos: dict[int, QPushButton] = {}
        for idx, (texto, modo) in enumerate((("filas", "filas"), ("lista", "lista"), ("iconos", "iconos"))):
            btn = QPushButton()
            btn.setObjectName("btnModo")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"Vista de {texto}")
            btn.setIcon(mono_icon(modo, 18, "#4f46e5"))
            btn.setIconSize(QSize(18, 18))
            btn.setFixedSize(38, 32)
            self._grupo_modos.addButton(btn, idx)
            self._btn_modos[idx] = btn
            lay.addWidget(btn)
        self._grupo_modos.idClicked.connect(self._on_modo_clicked)

        lay.addStretch()

        self._cmb_grupo = QComboBox()
        self._cmb_grupo.addItem("Agrupar por: (ninguno)", None)
        self._cmb_grupo.currentIndexChanged.connect(self._on_grupo_changed)
        self._cmb_grupo.setVisible(False)
        lay.addWidget(self._cmb_grupo)
        return bar

    def _configurar_tabla(self) -> None:
        table = self.table
        table.setColumnCount(len(self._columns))
        table.setHorizontalHeaderLabels([c.get("label", "") for c in self._columns])

        header = table.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        if self._sortable:
            header.sectionClicked.connect(self._on_header_clicked)

        col_flex: Optional[int] = None
        for col, cfg in enumerate(self._columns):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            if cfg.get("stretch"):
                col_flex = col
            if cfg.get("width"):
                table.setColumnWidth(col, int(cfg["width"]))
            if cfg.get("hidden"):
                table.setColumnHidden(col, True)

        if col_flex is not None:
            header.setSectionResizeMode(col_flex, QHeaderView.Stretch)
            header.setStretchLastSection(False)
        else:
            header.setStretchLastSection(True)

        table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        if self._row_height:
            table.verticalHeader().setDefaultSectionSize(self._row_height)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(
            QAbstractItemView.SingleSelection
            if self._selection_mode == "single"
            else QAbstractItemView.ExtendedSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(self._alternating)
        table.doubleClicked.connect(self._on_tabla_doble)
        table.currentItemChanged.connect(self._on_tabla_item)

    def _configurar_lista(self) -> None:
        lst = self.list
        lst.setSelectionMode(
            QAbstractItemView.SingleSelection
            if self._selection_mode == "single"
            else QAbstractItemView.ExtendedSelection)
        lst.currentItemChanged.connect(self._on_lista_item)
        lst.itemDoubleClicked.connect(self._on_lista_doble)

    # ------------------------------------------------------------- modos

    def set_mode(self, mode: str) -> None:
        if mode not in _MODOS:
            raise ValueError(f"Modo de vista no válido: {mode}")
        self._mode = mode
        self._stack.setCurrentIndex(0 if mode == "filas" else 1)
        self._sincronizar_botones_modo()
        if mode in ("lista", "iconos"):
            self._aplicar_modo_lista()
            self._render_lista()

    def mode(self) -> str:
        return self._mode

    def set_modo_selector_visible(self, visible: bool) -> None:
        self._modo_selector_visible = visible
        self._toolbar_modos.setVisible(visible)

    def _sincronizar_botones_modo(self) -> None:
        idx = {"filas": 0, "lista": 1, "iconos": 2}.get(self._mode, 0)
        btn = self._btn_modos.get(idx)
        if btn is not None:
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

    def _on_modo_clicked(self, idx: int) -> None:
        self.set_mode(_MODOS[idx])

    # ---------------------------------------------------------- agrupación

    def set_group_key(self, key: Optional[str]) -> None:
        self._group_key = key or None
        self._render()
        self._sincronizar_cmb_grupo()

    def group_key(self) -> Optional[str]:
        return self._group_key

    def set_group_options(self, options) -> None:
        """options: lista de tuplas (etiqueta, key) para el selector visual."""
        self._cmb_grupo.blockSignals(True)
        self._cmb_grupo.clear()
        self._cmb_grupo.addItem("Agrupar por: (ninguno)", None)
        for etiqueta, key in options:
            self._cmb_grupo.addItem(etiqueta, key)
        idx = self._cmb_grupo.findData(self._group_key)
        self._cmb_grupo.setCurrentIndex(idx if idx >= 0 else 0)
        self._cmb_grupo.blockSignals(False)
        self._cmb_grupo.setVisible(True)

    def _sincronizar_cmb_grupo(self) -> None:
        idx = self._cmb_grupo.findData(self._group_key)
        if idx >= 0:
            self._cmb_grupo.blockSignals(True)
            self._cmb_grupo.setCurrentIndex(idx)
            self._cmb_grupo.blockSignals(False)

    def _on_grupo_changed(self, idx: int) -> None:
        self.set_group_key(self._cmb_grupo.itemData(idx))

    # ------------------------------------------------------------- datos

    def set_records(self, records: list[dict]) -> None:
        self._records = list(records or [])
        self._cache_pixmap.clear()
        self._render()

    def records(self) -> list[dict]:
        return list(self._display)

    def _render(self) -> None:
        self._display = self._aplicar_orden(self._records)
        if self._mode == "filas":
            self._render_tabla()
        else:
            self._render_lista()

    def _aplicar_orden(self, records: list[dict]) -> list[dict]:
        skey = None
        if self._sort_col is not None and 0 <= self._sort_col < len(self._columns):
            skey = self._columns[self._sort_col].get("key")
        reverse = self._sort_order == Qt.DescendingOrder

        if self._group_key:
            grupos: dict = {}
            for r in records:
                grupos.setdefault(_valor_orden(r.get(self._group_key)), []).append(r)
            resultado: list[dict] = []
            for gval in sorted(grupos.keys()):
                items = grupos[gval]
                if skey:
                    items = sorted(items, key=lambda r: _valor_orden(r.get(skey)),
                                   reverse=reverse)
                resultado.extend(items)
            return resultado

        if skey:
            return sorted(records, key=lambda r: _valor_orden(r.get(skey)), reverse=reverse)
        return list(records)

    # ------------------------------------------------------------ render

    def _render_tabla(self) -> None:
        table = self.table
        table.setSortingEnabled(False)
        table.clearSpans()
        table.clearContents()

        if self._group_key:
            grupos: list = []
            primera = True
            clave_prev = None
            for r in self._display:
                val = r.get(self._group_key)
                if primera or _valor_orden(val) != _valor_orden(clave_prev):
                    grupos.append([val, []])
                    clave_prev = val
                    primera = False
                grupos[-1][1].append(r)

            table.setRowCount(sum(len(g[1]) for g in grupos) + len(grupos))
            row = 0
            for gval, items in grupos:
                item = QTableWidgetItem(self._etiqueta_valor(gval))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setForeground(QColor("#475569"))
                item.setBackground(QColor("#eef2ff"))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                table.setSpan(row, 0, 1, table.columnCount())
                table.setItem(row, 0, item)
                row += 1
                for r in items:
                    self._llenar_fila(row, r)
                    row += 1
        else:
            table.setRowCount(len(self._display))
            for row, r in enumerate(self._display):
                self._llenar_fila(row, r)

        if self._sort_col is not None:
            table.horizontalHeader().setSortIndicator(self._sort_col, self._sort_order)

    def _llenar_fila(self, row: int, record: dict) -> None:
        for col, cfg in enumerate(self._columns):
            factory = cfg.get("widget")
            if callable(factory):
                widget = factory(record, row)
                if widget is not None:
                    self.table.setCellWidget(row, col, widget)
                continue
            valor = record.get(cfg.get("key"), "")
            texto = "" if valor is None else str(valor)
            item = QTableWidgetItem(texto)
            if col == 0:
                item.setData(_RECORD_ROLE, record)
            alineacion = cfg.get("align")
            if alineacion == "right":
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            elif alineacion == "center":
                item.setTextAlignment(Qt.AlignCenter)
            if self._background_fn:
                color_bg = self._background_fn(record)
                if color_bg is not None:
                    item.setBackground(color_bg)
            if self._foreground_fn:
                color_fg = self._foreground_fn(record, cfg.get("key"))
                if color_fg is not None:
                    item.setForeground(color_fg)
            self.table.setItem(row, col, item)

    def _render_lista(self) -> None:
        lst = self.list
        lst.clear()
        for record in self._display:
            pix = self._record_pixmap(record)
            item = QListWidgetItem()
            item.setData(_RECORD_ROLE, record)
            if self._mode == "iconos":
                item.setText(self._etiqueta_registro(record))
                item.setIcon(QIcon(pix))
                item.setSizeHint(QSize(140, 150))
                lst.addItem(item)
            else:
                widget = _ItemLista(pix, self._etiqueta_registro(record),
                                    self._subtitulo_registro(record))
                item.setSizeHint(widget.sizeHint())
                lst.addItem(item)
                lst.setItemWidget(item, widget)

    def _aplicar_modo_lista(self) -> None:
        lst = self.list
        if self._mode == "iconos":
            lst.setViewMode(QListView.IconMode)
            lst.setIconSize(QSize(96, 96))
            lst.setGridSize(QSize(140, 150))
            lst.setMovement(QListView.Static)
            lst.setResizeMode(QListView.Adjust)
            lst.setSpacing(8)
            lst.setWordWrap(True)
        else:
            lst.setViewMode(QListView.ListMode)
            lst.setIconSize(QSize(48, 48))
            lst.setMovement(QListView.Static)
            lst.setResizeMode(QListView.Adjust)
            lst.setSpacing(2)
            lst.setWordWrap(False)

    # ----------------------------------------------------------- eventos

    def _on_header_clicked(self, col: int) -> None:
        if not self._sortable or col >= len(self._columns):
            return
        if self._sort_col == col:
            self._sort_order = (Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder
                                else Qt.AscendingOrder)
        else:
            self._sort_col = col
            self._sort_order = Qt.AscendingOrder
        self._render()

    def _on_tabla_doble(self, index) -> None:
        rec = self.row_record(index.row())
        if rec is not None:
            self.recordDoubleClicked.emit(rec)

    def _on_tabla_item(self, current, previous) -> None:
        rec = self.row_record(current.row()) if current is not None else None
        self.currentRecordChanged.emit(rec)

    def _on_lista_item(self, current, previous) -> None:
        rec = current.data(_RECORD_ROLE) if current is not None else None
        self.currentRecordChanged.emit(rec)

    def _on_lista_doble(self, item) -> None:
        rec = item.data(_RECORD_ROLE) if item is not None else None
        if rec is not None:
            self.recordDoubleClicked.emit(rec)

    # ----------------------------------------------------------- acceso

    def row_record(self, row: int) -> Optional[dict]:
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        return item.data(_RECORD_ROLE)

    def current_record(self) -> Optional[dict]:
        if self._mode == "filas":
            return self.row_record(self.table.currentRow())
        item = self.list.currentItem()
        return item.data(_RECORD_ROLE) if item is not None else None

    def selected_records(self) -> list[dict]:
        if self._mode == "filas":
            filas = sorted({idx.row() for idx in self.table.selectedIndexes()})
            return [r for r in (self.row_record(f) for f in filas) if r is not None]
        return [it.data(_RECORD_ROLE) for it in self.list.selectedItems()]

    def select_record(self, record: dict) -> None:
        if self._mode == "filas":
            for row in range(self.table.rowCount()):
                if self.row_record(row) == record:
                    self.table.selectRow(row)
                    return
        else:
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item is not None and item.data(_RECORD_ROLE) == record:
                    self.list.setCurrentItem(item)
                    return

    # ------------------------------------------------ celdas y edición

    def _columna(self, key: str) -> Optional[int]:
        for i, cfg in enumerate(self._columns):
            if cfg.get("key") == key:
                return i
        return None

    def row_count(self) -> int:
        return self.table.rowCount()

    def current_row(self) -> int:
        return self.table.currentRow()

    def cell_widget(self, row: int, key: str):
        col = self._columna(key)
        if col is None:
            return None
        return self.table.cellWidget(row, col)

    def cell_text(self, row: int, key: str) -> str:
        col = self._columna(key)
        if col is None:
            return ""
        item = self.table.item(row, col)
        return item.text() if item else ""

    def set_cell_text(self, row: int, key: str, text) -> None:
        col = self._columna(key)
        if col is None:
            return
        item = self.table.item(row, col)
        if item is not None:
            item.setText(str(text))

    def add_row(self, record: dict) -> None:
        self._records.append(record)
        self._display.append(record)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._llenar_fila(row, record)

    def remove_row(self, row: int) -> None:
        if 0 <= row < len(self._display):
            self._records.remove(self._display.pop(row))
        self.table.removeRow(row)

    # ------------------------------------------------------ exportación

    def exportar_excel(self, titulo: str, parent: QWidget) -> Optional[str]:
        from src.utils.export_utils import export_table_to_excel
        return export_table_to_excel(self.table, titulo, parent)

    def imprimir(self, titulo: str, parent: QWidget) -> None:
        from src.utils.export_utils import print_table
        print_table(self.table, titulo, parent)

    # ----------------------------------------------------------- helpers

    def _cargar_imagen_default(self) -> QPixmap:
        ruta = _RAIZ_PROYECTO / self._default_image
        pix = QPixmap(str(ruta))
        if pix.isNull() and self._default_image:
            pix = QPixmap()
        return pix

    def _record_pixmap(self, record: dict) -> QPixmap:
        rid = record.get(self._id_key)
        if rid is not None and rid in self._cache_pixmap:
            return self._cache_pixmap[rid]

        data = None
        if self._image_key:
            data = record.get(self._image_key)
        if not data and self._image_resolver:
            try:
                data = self._image_resolver(rid)
            except Exception:
                data = None

        pix = QPixmap()
        if data:
            pix.loadFromData(bytes(data))
        if pix.isNull():
            pix = self._default_pixmap

        if rid is not None:
            self._cache_pixmap[rid] = pix
        return pix

    def _etiqueta_valor(self, val) -> str:
        if val is None or str(val).strip() == "":
            return "(Vacío)"
        return str(val)

    def _etiqueta_registro(self, record: dict) -> str:
        keys = self._title_key
        if keys is None:
            keys = [self._columns[0]["key"]] if self._columns else []
        if isinstance(keys, str):
            keys = [keys]
        partes = [str(record.get(k, "")) for k in keys]
        partes = [p for p in partes if p.strip()]
        return " - ".join(partes) if partes else "(sin título)"

    def _subtitulo_registro(self, record: dict) -> str:
        keys = self._subtitle_key
        if not keys:
            return ""
        if isinstance(keys, str):
            keys = [keys]
        partes = [str(record.get(k, "")) for k in keys]
        partes = [p for p in partes if p.strip()]
        return " · ".join(partes) if partes else ""
