"""Editor interactivo de diseño de etiqueta.

- LabelCanvas: lienzo que dibuja la etiqueta en tiempo real, permite arrastrar
  (drag & drop) los elementos con el mouse y emite señales de selección/arrastre.
- PanelPropiedadesCampo: formulario con coordenadas, dimensiones, borde,
  tipografía (tamaños de etiqueta y valor), estilo, alineación y visibilidad
  del elemento seleccionado.

El diseño es el mismo JSON persistido en etiqueta_config (EtiquetaModel).
"""
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QColorDialog, QComboBox, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFontComboBox, QFormLayout, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QRadioButton, QSpinBox, QStackedWidget, QTabWidget,
    QVBoxLayout, QWidget,
)

from src.models.etiqueta_model import (
    ALTO_ETIQUETA_MM, ANCHO_ETIQUETA_MM, DATOS_ETIQUETA,
)
from src.utils.etiqueta_render import render_label, rect_campo_mm


def normalizar_campo(campo: dict, ancho_etiqueta: float = 76.0) -> dict:
    """Completa un campo de diseño con todos los atributos por defecto."""
    c = dict(campo)
    tipo = c.get("tipo", "texto")
    c.setdefault("tipo", "texto")
    c.setdefault("texto", "")
    c.setdefault("dato", DATOS_ETIQUETA[0][0])
    if "origen" not in c:
        c["origen"] = "dato" if tipo == "dato" else "texto"
    c.setdefault("name", "")
    c.setdefault("descripcion", "")
    c.setdefault("status", "enabled")
    c.setdefault("x_mm", 0.0)
    c.setdefault("y_mm", 0.0)
    c.setdefault("ancho_mm", float(ancho_etiqueta) - float(c.get("x_mm", 0)) - 2)
    c.setdefault("alto_mm", 7.0)
    c.setdefault("size", 12)
    c.setdefault("label_size", 12)
    c.setdefault("label", "")
    c.setdefault("familia", "Arial")
    c.setdefault("bold", False)
    c.setdefault("cursiva", False)
    c.setdefault("subrayado", False)
    c.setdefault("alineacion", "izquierda")
    c.setdefault("color_texto", "#000000")
    c.setdefault("color_fondo", "")
    c.setdefault("color_borde", "#000000")
    c.setdefault("rotacion", 0)
    c.setdefault("borde_visible", False)
    c.setdefault("borde_grosor_mm", 0.3)
    c.setdefault("visible", True)
    return c


def normalizar_diseno(diseno: dict) -> dict:
    d = dict(diseno)
    d["ancho_mm"] = ANCHO_ETIQUETA_MM
    d["alto_mm"] = ALTO_ETIQUETA_MM
    d["campos"] = [normalizar_campo(c, ANCHO_ETIQUETA_MM) for c in d.get("campos", [])]
    return d


def texto_campo(campo: dict) -> str:
    """Texto de referencia de un campo para listas/selector de elementos."""
    if campo.get("tipo") == "dato":
        base = dict(DATOS_ETIQUETA).get(campo.get("dato", ""), campo.get("dato", ""))
        return f"{campo.get('label', '') or base}: {base}"
    return campo.get("texto", "")


class LabelCanvas(QWidget):
    """Lienzo interactivo: dibuja la etiqueta y permite arrastrar y
    redimensionar (stretch) los elementos con el mouse."""

    campoSeleccionado = Signal(int)
    campoArrastrado = Signal(int, float, float)
    campoRedimensionado = Signal(int)
    campoDobleClic = Signal(int)

    _HANDLE_SIZE = 9
    _HANDLE_ORDEN = ("tl", "tr", "br", "bl", "t", "r", "b", "l")
    _MIN_MM = 2.0
    _CURSOR_HANDLE = {
        "tl": Qt.CursorShape.SizeFDiagCursor,
        "tr": Qt.CursorShape.SizeBDiagCursor,
        "br": Qt.CursorShape.SizeFDiagCursor,
        "bl": Qt.CursorShape.SizeBDiagCursor,
        "t": Qt.CursorShape.SizeVerCursor,
        "b": Qt.CursorShape.SizeVerCursor,
        "l": Qt.CursorShape.SizeHorCursor,
        "r": Qt.CursorShape.SizeHorCursor,
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._diseno: dict | None = None
        self._datos: dict | None = None
        self._sel = -1
        self._drag_idx = -1
        self._resize: tuple | None = None
        self.setMinimumSize(360, 240)
        self.setMouseTracking(True)

    def set_contenido(self, diseno: dict, datos: dict) -> None:
        self._diseno = diseno
        self._datos = datos
        self._sel = min(self._sel, len(diseno.get("campos", [])) - 1)
        self.update()

    def seleccionar(self, idx: int) -> None:
        self._sel = idx
        self.update()

    def _geometria(self) -> tuple[float, float, float, float, float]:
        ancho = float(self._diseno.get("ancho_mm", 76.0)) if self._diseno else 76.0
        alto = float(self._diseno.get("alto_mm", 51.0)) if self._diseno else 51.0
        escala = min((self.width() - 24) / ancho, (self.height() - 24) / alto)
        escala = max(escala, 0.5)
        off_x = (self.width() - ancho * escala) / 2.0
        off_y = (self.height() - alto * escala) / 2.0
        return ancho, alto, escala, off_x, off_y

    def _widget_a_mm(self, px: float, py: float) -> tuple[float, float]:
        _, _, escala, off_x, off_y = self._geometria()
        return (px - off_x) / escala, (py - off_y) / escala

    def _hit_test(self, x_mm: float, y_mm: float) -> int:
        if not self._diseno:
            return -1
        campos = self._diseno.get("campos", [])
        for i in range(len(campos) - 1, -1, -1):
            c = campos[i]
            if not c.get("visible", True):
                continue
            if rect_campo_mm(self._diseno, c).contains(x_mm, y_mm):
                return i
        return -1

    def _puntos_agarre_px(self, campo: dict) -> dict[str, QPointF]:
        """Puntos (en px del widget) de los 8 mangos de redimensionado."""
        _, _, escala, off_x, off_y = self._geometria()
        r = rect_campo_mm(self._diseno, campo)

        def px(x: float, y: float) -> QPointF:
            return QPointF(off_x + x * escala, off_y + y * escala)

        return {
            "tl": px(r.left(), r.top()),
            "t": px(r.center().x(), r.top()),
            "tr": px(r.right(), r.top()),
            "r": px(r.right(), r.center().y()),
            "br": px(r.right(), r.bottom()),
            "b": px(r.center().x(), r.bottom()),
            "bl": px(r.left(), r.bottom()),
            "l": px(r.left(), r.center().y()),
        }

    def _hit_handle(self, pos: QPointF) -> str | None:
        if self._sel < 0 or not self._diseno:
            return None
        campos = self._diseno.get("campos", [])
        if self._sel >= len(campos):
            return None
        tol = self._HANDLE_SIZE / 2.0 + 3.0
        for key in self._HANDLE_ORDEN:
            p = self._puntos_agarre_px(campos[self._sel])[key]
            if abs(pos.x() - p.x()) <= tol and abs(pos.y() - p.y()) <= tol:
                return key
        return None

    def _cursor_para(self, pos: QPointF) -> Qt.CursorShape:
        h = self._hit_handle(pos)
        return self._CURSOR_HANDLE.get(h, Qt.CursorShape.ArrowCursor)

    def _aplicar_resize(self, pos: QPointF) -> None:
        if not self._resize or not self._diseno:
            return
        handle, x0, y0, w0, h0 = self._resize
        mx, my = self._widget_a_mm(pos.x(), pos.y())
        ancho = float(self._diseno.get("ancho_mm", 76.0))
        alto = float(self._diseno.get("alto_mm", 51.0))

        if handle in ("tl", "l", "bl"):
            nx = mx
            nw = x0 + w0 - mx
        elif handle in ("tr", "r", "br"):
            nx = x0
            nw = mx - x0
        else:
            nx = x0
            nw = w0

        if handle in ("tl", "t", "tr"):
            ny = my
            nh = y0 + h0 - my
        elif handle in ("bl", "b", "br"):
            ny = y0
            nh = my - y0
        else:
            ny = y0
            nh = h0

        nw = max(nw, self._MIN_MM)
        nh = max(nh, self._MIN_MM)
        nx = max(0.0, min(nx, ancho - nw))
        ny = max(0.0, min(ny, alto - nh))
        nw = min(nw, ancho - nx)
        nh = min(nh, alto - ny)
        nx, ny, nw, nh = (round(nx, 1), round(ny, 1),
                          round(nw, 1), round(nh, 1))

        campos = self._diseno.get("campos", [])
        if self._sel >= len(campos):
            return
        c = campos[self._sel]
        actual = (float(c.get("x_mm", x0)), float(c.get("y_mm", y0)),
                  float(c.get("ancho_mm", w0)), float(c.get("alto_mm", h0)))
        if (nx, ny, nw, nh) != actual:
            c["x_mm"] = nx
            c["y_mm"] = ny
            c["ancho_mm"] = nw
            c["alto_mm"] = nh
            self.campoRedimensionado.emit(self._sel)
        self.update()

    def paintEvent(self, _event) -> None:
        if not self._diseno:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#eef2f7"))

        ancho, alto, escala, off_x, off_y = self._geometria()
        painter.fillRect(QRectF(off_x, off_y, ancho * escala, alto * escala),
                         Qt.GlobalColor.white)
        painter.save()
        painter.translate(off_x, off_y)
        render_label(painter, self._diseno, self._datos, escala)
        painter.restore()

        if 0 <= self._sel < len(self._diseno.get("campos", [])):
            c = self._diseno["campos"][self._sel]
            r = rect_campo_mm(self._diseno, c)
            pen = QPen(QColor("#3b82f6"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRectF(off_x + r.x() * escala,
                                    off_y + r.y() * escala,
                                    r.width() * escala, r.height() * escala))
            s = self._HANDLE_SIZE
            for p in self._puntos_agarre_px(c).values():
                painter.fillRect(QRectF(p.x() - s / 2.0, p.y() - s / 2.0, s, s),
                                 QColor("#3b82f6"))
                painter.setPen(QPen(QColor("white"), 1))
                painter.drawRect(QRectF(p.x() - s / 2.0, p.y() - s / 2.0, s, s))
        painter.setPen(QPen(QColor("#cbd5e1")))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def mousePressEvent(self, event) -> None:
        if not self._diseno:
            event.accept()
            return
        handle = self._hit_handle(event.position())
        if handle:
            c = self._diseno["campos"][self._sel]
            r = rect_campo_mm(self._diseno, c)
            self._resize = (handle, float(c.get("x_mm", r.x())),
                            float(c.get("y_mm", r.y())), r.width(), r.height())
            self._drag_idx = -1
            event.accept()
            return
        x_mm, y_mm = self._widget_a_mm(event.position().x(), event.position().y())
        idx = self._hit_test(x_mm, y_mm)
        self._sel = idx
        self._drag_idx = idx
        self.campoSeleccionado.emit(idx)
        self.update()
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if not self._diseno:
            event.accept()
            return
        if self._resize is not None:
            self._aplicar_resize(event.position())
            event.accept()
            return
        if self._drag_idx < 0:
            self.setCursor(self._cursor_para(event.position()))
            event.accept()
            return
        x_mm, y_mm = self._widget_a_mm(event.position().x(), event.position().y())
        ancho = float(self._diseno.get("ancho_mm", 76.0))
        alto = float(self._diseno.get("alto_mm", 51.0))
        campos = self._diseno.get("campos", [])
        if self._drag_idx >= len(campos):
            event.accept()
            return
        c = campos[self._drag_idx]
        r = rect_campo_mm(self._diseno, c)
        nx = round(max(0.0, min(ancho - r.width(), x_mm - r.width() / 2.0)), 1)
        ny = round(max(0.0, min(alto - r.height(), y_mm - r.height() / 2.0)), 1)
        if nx != float(c.get("x_mm", 0)) or ny != float(c.get("y_mm", 0)):
            c["x_mm"] = nx
            c["y_mm"] = ny
            self.campoArrastrado.emit(self._drag_idx, nx, ny)
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        if not self._diseno:
            event.accept()
            return
        x_mm, y_mm = self._widget_a_mm(event.position().x(), event.position().y())
        idx = self._hit_test(x_mm, y_mm)
        if idx >= 0:
            self._sel = idx
            self._drag_idx = -1
            self.campoSeleccionado.emit(idx)
            self.campoDobleClic.emit(idx)
            self.update()
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_idx = -1
        self._resize = None
        event.accept()


class PanelPropiedadesCampo(QWidget):
    """Formulario de propiedades del elemento de etiqueta seleccionado."""

    campoCambiado = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._idx = -1
        self._cargando = False
        self._campo = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            "QGroupBox { font-size: 11px; }"
            "QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, "
            "QCheckBox, QPushButton { font-size: 11px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        grp = QGroupBox("Elemento seleccionado")
        grid = QGridLayout(grp)
        grid.setContentsMargins(6, 8, 6, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)

        def compacto(w) -> QWidget:
            w.setMinimumWidth(84)
            return w

        self.chk_visible = QCheckBox("Mostrar en la etiqueta")
        self.chk_visible.toggled.connect(self._emitir)
        grid.addWidget(self.chk_visible, 0, 0, 1, 4)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItem("Texto fijo", "texto")
        self.cmb_tipo.addItem("Dato del pedido", "dato")
        self.cmb_tipo.currentIndexChanged.connect(self._tipo_cambia)
        grid.addWidget(QLabel("Tipo:"), 1, 0)
        grid.addWidget(compacto(self.cmb_tipo), 1, 1, 1, 3)

        self.txt_contenido = QLineEdit()
        self.txt_contenido.textChanged.connect(self._emitir)
        self.cmb_dato = QComboBox()
        for key, label in DATOS_ETIQUETA:
            self.cmb_dato.addItem(label, key)
        self.cmb_dato.currentIndexChanged.connect(self._emitir)
        self.stack_contenido = QStackedWidget()
        self.stack_contenido.addWidget(self.txt_contenido)
        self.stack_contenido.addWidget(self.cmb_dato)
        grid.addWidget(QLabel("Contenido:"), 2, 0)
        grid.addWidget(self.stack_contenido, 2, 1, 1, 3)

        self.txt_label = QLineEdit()
        self.txt_label.setPlaceholderText("Prefijo, ej: MODELO:")
        self.txt_label.textChanged.connect(self._emitir)
        grid.addWidget(QLabel("Etiqueta:"), 3, 0)
        grid.addWidget(self.txt_label, 3, 1, 1, 3)

        self.sp_label_size = QSpinBox()
        self.sp_label_size.setRange(8, 72)
        self.sp_label_size.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Label:"), 4, 0)
        grid.addWidget(compacto(self.sp_label_size), 4, 1)

        self.sp_size = QSpinBox()
        self.sp_size.setRange(8, 72)
        self.sp_size.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Valor:"), 4, 2)
        grid.addWidget(compacto(self.sp_size), 4, 3)

        self.cmb_alineacion = QComboBox()
        self.cmb_alineacion.addItem("Izquierda", "izquierda")
        self.cmb_alineacion.addItem("Centro", "centro")
        self.cmb_alineacion.addItem("Derecha", "derecha")
        self.cmb_alineacion.currentIndexChanged.connect(self._emitir)
        grid.addWidget(QLabel("Alineación:"), 5, 0)
        grid.addWidget(self.cmb_alineacion, 5, 1, 1, 3)

        self.chk_bold = QCheckBox("Negrita")
        self.chk_bold.toggled.connect(self._emitir)
        self.chk_cursiva = QCheckBox("Cursiva")
        self.chk_cursiva.toggled.connect(self._emitir)
        grid.addWidget(self.chk_bold, 6, 0, 1, 2)
        grid.addWidget(self.chk_cursiva, 6, 2, 1, 2)

        self.sp_x = QDoubleSpinBox()
        self.sp_x.setRange(0, 300)
        self.sp_x.setDecimals(1)
        self.sp_x.setSuffix(" mm")
        self.sp_x.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Pos X:"), 7, 0)
        grid.addWidget(compacto(self.sp_x), 7, 1)

        self.sp_y = QDoubleSpinBox()
        self.sp_y.setRange(0, 200)
        self.sp_y.setDecimals(1)
        self.sp_y.setSuffix(" mm")
        self.sp_y.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Pos Y:"), 7, 2)
        grid.addWidget(compacto(self.sp_y), 7, 3)

        self.sp_ancho = QDoubleSpinBox()
        self.sp_ancho.setRange(1, 300)
        self.sp_ancho.setDecimals(1)
        self.sp_ancho.setSuffix(" mm")
        self.sp_ancho.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Ancho:"), 8, 0)
        grid.addWidget(compacto(self.sp_ancho), 8, 1)

        self.sp_alto = QDoubleSpinBox()
        self.sp_alto.setRange(1, 200)
        self.sp_alto.setDecimals(1)
        self.sp_alto.setSuffix(" mm")
        self.sp_alto.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Alto:"), 8, 2)
        grid.addWidget(compacto(self.sp_alto), 8, 3)

        self.chk_borde = QCheckBox("Mostrar recuadro/borde")
        self.chk_borde.toggled.connect(self._emitir)
        grid.addWidget(self.chk_borde, 9, 0, 1, 4)

        self.sp_borde = QDoubleSpinBox()
        self.sp_borde.setRange(0.05, 3.0)
        self.sp_borde.setDecimals(2)
        self.sp_borde.setSuffix(" mm")
        self.sp_borde.valueChanged.connect(self._emitir)
        grid.addWidget(QLabel("Grosor:"), 10, 0)
        grid.addWidget(compacto(self.sp_borde), 10, 1)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        layout.addWidget(grp)
        layout.addStretch()
        self._habilitar(False)

    def _habilitar(self, on: bool) -> None:
        for w in (self.chk_visible, self.cmb_tipo, self.stack_contenido,
                  self.txt_label, self.sp_label_size, self.sp_size,
                  self.chk_bold, self.chk_cursiva, self.cmb_alineacion,
                  self.sp_x, self.sp_y, self.sp_ancho, self.sp_alto,
                  self.chk_borde, self.sp_borde):
            w.setEnabled(on)

    def _emitir(self, *_args) -> None:
        if not self._cargando:
            self.campoCambiado.emit()

    def _tipo_cambia(self, *_args) -> None:
        self.stack_contenido.setCurrentIndex(
            0 if self.cmb_tipo.currentData() == "texto" else 1)
        self._emitir()

    def cargar_campo(self, idx: int, campo: dict | None, ancho_etiqueta: float) -> None:
        """Muestra las propiedades del campo (o vacía el panel si es None)."""
        self._cargando = True
        try:
            self._idx = idx if campo is not None else -1
            self._campo = normalizar_campo(campo, ancho_etiqueta) if campo else None
            if campo is None:
                self._habilitar(False)
                return
            c = self._campo
            self._habilitar(True)
            self.chk_visible.setChecked(bool(c.get("visible", True)))
            idx_tipo = 1 if c.get("tipo") == "dato" else 0
            self.cmb_tipo.setCurrentIndex(idx_tipo)
            self.stack_contenido.setCurrentIndex(idx_tipo)
            if idx_tipo == 1:
                k = c.get("dato", "")
                i = self.cmb_dato.findData(k)
                self.cmb_dato.setCurrentIndex(i if i >= 0 else 0)
            else:
                self.txt_contenido.setText(c.get("texto", ""))
            self.txt_label.setText(c.get("label", ""))
            self.sp_label_size.setValue(int(c.get("label_size", c.get("size", 12))))
            self.sp_size.setValue(int(c.get("size", 12)))
            self.chk_bold.setChecked(bool(c.get("bold", False)))
            self.chk_cursiva.setChecked(bool(c.get("cursiva", False)))
            i = self.cmb_alineacion.findData(c.get("alineacion", "izquierda"))
            self.cmb_alineacion.setCurrentIndex(i if i >= 0 else 0)
            self.sp_x.setValue(float(c.get("x_mm", 0)))
            self.sp_y.setValue(float(c.get("y_mm", 0)))
            self.sp_ancho.setValue(float(c.get("ancho_mm", 10)))
            self.sp_alto.setValue(float(c.get("alto_mm", 7)))
            self.chk_borde.setChecked(bool(c.get("borde_visible", False)))
            self.sp_borde.setValue(float(c.get("borde_grosor_mm", 0.3)))
        finally:
            self._cargando = False

    def leer_campo(self, ancho_etiqueta: float) -> dict:
        """Devuelve el campo con los valores del formulario.

        Parte de la última versión cargada para conservar atributos que el
        panel no expone (name, descripcion, colores, rotación, etc.)."""
        c = dict(self._campo) if self._campo else {}
        tipo = self.cmb_tipo.currentData() if self.cmb_tipo.isEnabled() else c.get("tipo", "texto")
        if tipo == "dato":
            c["tipo"] = "dato"
            c["dato"] = self.cmb_dato.currentData()
        else:
            c["tipo"] = "texto"
            c["texto"] = self.txt_contenido.text()
        c["label"] = self.txt_label.text()
        c["label_size"] = int(self.sp_label_size.value())
        c["size"] = int(self.sp_size.value())
        c["bold"] = bool(self.chk_bold.isChecked())
        c["cursiva"] = bool(self.chk_cursiva.isChecked())
        c["alineacion"] = self.cmb_alineacion.currentData() or "izquierda"
        c["x_mm"] = float(self.sp_x.value())
        c["y_mm"] = float(self.sp_y.value())
        c["ancho_mm"] = float(self.sp_ancho.value())
        c["alto_mm"] = float(self.sp_alto.value())
        c["borde_visible"] = bool(self.chk_borde.isChecked())
        c["borde_grosor_mm"] = float(self.sp_borde.value())
        c["visible"] = bool(self.chk_visible.isChecked())
        return normalizar_campo(c, ancho_etiqueta)


def _titulo_propiedades(campo: dict) -> str:
    if campo.get("borde_visible"):
        return "Box Properties"
    if campo.get("tipo") == "dato":
        return "Data Properties"
    return "Text Properties"


class DialogoPropiedadesCampo(QDialog):
    """Diálogo modal de propiedades de un elemento, organizado en pestañas.

    Pestañas: General, Data, Font, Color y Position. Al aceptar devuelve el
    campo modificado vía ``campo_resultado()``.
    """

    def __init__(self, campo: dict, ancho_etiqueta: float = 76.0,
                 parent=None) -> None:
        super().__init__(parent)
        self._ancho = ancho_etiqueta
        self._campo = normalizar_campo(campo, ancho_etiqueta)
        self.setWindowTitle(_titulo_propiedades(self._campo))
        self.setMinimumWidth(460)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_general(), "General")
        self.tabs.addTab(self._tab_data(), "Data")
        self.tabs.addTab(self._tab_fuente(), "Font")
        self.tabs.addTab(self._tab_color(), "Color")
        self.tabs.addTab(self._tab_posicion(), "Position")
        layout.addWidget(self.tabs)

        self.btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Help)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.btns.helpRequested.connect(self._ayuda)
        layout.addWidget(self.btns)

    # ---- Pestañas ----

    def _tab_general(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.txt_name = QLineEdit()
        self.txt_name.setText(self._campo.get("name", ""))
        self.txt_desc = QPlainTextEdit()
        self.txt_desc.setPlainText(self._campo.get("descripcion", ""))
        self.txt_desc.setMaximumHeight(90)

        self.rd_enabled = QRadioButton("Enabled")
        self.rd_disabled = QRadioButton("Disabled")
        self.rd_conditional = QRadioButton("Conditional")
        self._grp_status = QButtonGroup(self)
        for r in (self.rd_enabled, self.rd_disabled, self.rd_conditional):
            self._grp_status.addButton(r)
        estado = self._campo.get("status", "enabled")
        (self.rd_enabled if estado == "enabled"
         else self.rd_disabled if estado == "disabled"
         else self.rd_conditional).setChecked(True)
        fila_status = QWidget()
        h = QHBoxLayout(fila_status)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.rd_enabled)
        h.addWidget(self.rd_disabled)
        h.addWidget(self.rd_conditional)

        form.addRow("Name:", self.txt_name)
        form.addRow("Description:", self.txt_desc)
        form.addRow("Status:", fila_status)
        return w

    def _tab_data(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.cmb_origen = QComboBox()
        self.cmb_origen.addItem("Texto estático", "texto")
        self.cmb_origen.addItem("Variable de base de datos", "dato")
        self.cmb_origen.addItem("Expresión/Fórmula", "expresion")
        self.cmb_origen.currentIndexChanged.connect(self._origen_cambia)

        self.txt_texto = QLineEdit()
        self.txt_texto.setText(self._campo.get("texto", ""))
        self.cmb_dato2 = QComboBox()
        for key, label in DATOS_ETIQUETA:
            self.cmb_dato2.addItem(label, key)
        k = self._campo.get("dato", "")
        i = self.cmb_dato2.findData(k)
        self.cmb_dato2.setCurrentIndex(i if i >= 0 else 0)
        self.txt_expresion = QLineEdit()
        self.txt_expresion.setText(self._campo.get("texto", ""))

        self.stack_data = QStackedWidget()
        self.stack_data.addWidget(self.txt_texto)
        self.stack_data.addWidget(self.cmb_dato2)
        self.stack_data.addWidget(self.txt_expresion)

        self.txt_label2 = QLineEdit()
        self.txt_label2.setText(self._campo.get("label", ""))

        form.addRow("Origen:", self.cmb_origen)
        form.addRow("Contenido:", self.stack_data)
        form.addRow("Prefijo/Label:", self.txt_label2)

        if self._campo.get("tipo") == "dato":
            self.cmb_origen.setCurrentIndex(1)
        elif self._campo.get("origen") == "expresion":
            self.cmb_origen.setCurrentIndex(2)
        else:
            self.cmb_origen.setCurrentIndex(0)
        return w

    def _tab_fuente(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.cmb_familia = QFontComboBox()
        self.cmb_familia.setCurrentFont(QFont(self._campo.get("familia", "Arial")))
        self.sp_size = QSpinBox()
        self.sp_size.setRange(8, 96)
        self.sp_size.setValue(int(self._campo.get("size", 12)))
        self.sp_label_size = QSpinBox()
        self.sp_label_size.setRange(8, 96)
        self.sp_label_size.setValue(int(self._campo.get("label_size", 12)))
        self.chk_bold = QCheckBox("Negrita (Bold)")
        self.chk_bold.setChecked(bool(self._campo.get("bold", False)))
        self.chk_cursiva = QCheckBox("Cursiva (Italic)")
        self.chk_cursiva.setChecked(bool(self._campo.get("cursiva", False)))
        self.chk_subrayado = QCheckBox("Subrayado (Underline)")
        self.chk_subrayado.setChecked(bool(self._campo.get("subrayado", False)))
        self.cmb_alineacion = QComboBox()
        self.cmb_alineacion.addItem("Izquierda", "izquierda")
        self.cmb_alineacion.addItem("Centro", "centro")
        self.cmb_alineacion.addItem("Derecha", "derecha")
        i = self.cmb_alineacion.findData(self._campo.get("alineacion", "izquierda"))
        self.cmb_alineacion.setCurrentIndex(i if i >= 0 else 0)

        fila_estilo = QWidget()
        h = QHBoxLayout(fila_estilo)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.chk_bold)
        h.addWidget(self.chk_cursiva)
        h.addWidget(self.chk_subrayado)

        form.addRow("Font Family:", self.cmb_familia)
        form.addRow("Size:", self.sp_size)
        form.addRow("Label Size:", self.sp_label_size)
        form.addRow("Style:", fila_estilo)
        form.addRow("Alignment:", self.cmb_alineacion)
        return w

    def _tab_color(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.btn_color_texto = QPushButton()
        self.btn_color_fondo = QPushButton()
        self._actualizar_swatch(self.btn_color_texto,
                                self._campo.get("color_texto", "#000000"))
        self._actualizar_swatch(self.btn_color_fondo,
                                self._campo.get("color_fondo") or "#FFFFFF")
        self.btn_color_texto.clicked.connect(lambda: self._elegir_color("color_texto"))
        self.btn_color_fondo.clicked.connect(lambda: self._elegir_color("color_fondo"))
        form.addRow("Color de texto:", self.btn_color_texto)
        form.addRow("Color de fondo:", self.btn_color_fondo)
        return w

    def _tab_posicion(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.sp_x = QDoubleSpinBox()
        self.sp_x.setRange(0, 300)
        self.sp_x.setDecimals(1)
        self.sp_x.setSuffix(" mm")
        self.sp_x.setValue(float(self._campo.get("x_mm", 0)))
        self.sp_y = QDoubleSpinBox()
        self.sp_y.setRange(0, 200)
        self.sp_y.setDecimals(1)
        self.sp_y.setSuffix(" mm")
        self.sp_y.setValue(float(self._campo.get("y_mm", 0)))
        self.sp_w = QDoubleSpinBox()
        self.sp_w.setRange(1, 300)
        self.sp_w.setDecimals(1)
        self.sp_w.setSuffix(" mm")
        self.sp_w.setValue(float(self._campo.get("ancho_mm", 10)))
        self.sp_h = QDoubleSpinBox()
        self.sp_h.setRange(1, 200)
        self.sp_h.setDecimals(1)
        self.sp_h.setSuffix(" mm")
        self.sp_h.setValue(float(self._campo.get("alto_mm", 7)))

        self.cmb_rotacion = QComboBox()
        for grados in (0, 90, 180, 270):
            self.cmb_rotacion.addItem(f"{grados}°", grados)
        i = self.cmb_rotacion.findData(int(self._campo.get("rotacion", 0) or 0) % 360)
        self.cmb_rotacion.setCurrentIndex(i if i >= 0 else 0)

        self.chk_borde = QCheckBox("Mostrar borde / marco")
        self.chk_borde.setChecked(bool(self._campo.get("borde_visible", False)))
        self.sp_borde_grosor = QDoubleSpinBox()
        self.sp_borde_grosor.setRange(0.05, 3.0)
        self.sp_borde_grosor.setDecimals(2)
        self.sp_borde_grosor.setSuffix(" mm")
        self.sp_borde_grosor.setValue(float(self._campo.get("borde_grosor_mm", 0.3)))
        self.btn_color_borde = QPushButton()
        self._actualizar_swatch(self.btn_color_borde,
                                self._campo.get("color_borde", "#000000"))
        self.btn_color_borde.clicked.connect(lambda: self._elegir_color("color_borde"))
        self.chk_borde.toggled.connect(self._borde_cambia)

        form.addRow("X:", self.sp_x)
        form.addRow("Y:", self.sp_y)
        form.addRow("Width:", self.sp_w)
        form.addRow("Height:", self.sp_h)
        form.addRow("Rotación:", self.cmb_rotacion)
        form.addRow("", self.chk_borde)
        form.addRow("Border width:", self.sp_borde_grosor)
        form.addRow("Border color:", self.btn_color_borde)
        self._borde_cambia()
        return w

    # ---- Helpers de la UI ----

    def _origen_cambia(self, *_args) -> None:
        self.stack_data.setCurrentIndex(self.cmb_origen.currentIndex())

    def _borde_cambia(self, *_args) -> None:
        on = self.chk_borde.isChecked()
        self.sp_borde_grosor.setEnabled(on)
        self.btn_color_borde.setEnabled(on)

    def _actualizar_swatch(self, btn: QPushButton, color_hex: str) -> None:
        col = QColor(color_hex)
        luminancia = (0.299 * col.red() + 0.587 * col.green()
                      + 0.114 * col.blue())
        btn.setText(color_hex.upper())
        btn.setStyleSheet(
            f"background-color: {color_hex}; "
            f"color: {'black' if luminancia > 140 else 'white'};")

    def _elegir_color(self, clave: str) -> None:
        actual = self._campo.get(clave) or "#FFFFFF"
        col = QColorDialog.getColor(QColor(actual), self, "Seleccionar color")
        if not col.isValid():
            return
        hex_color = col.name()
        self._campo[clave] = hex_color
        btn = {"color_texto": self.btn_color_texto,
               "color_fondo": self.btn_color_fondo,
               "color_borde": self.btn_color_borde}[clave]
        self._actualizar_swatch(btn, hex_color)

    def _ayuda(self) -> None:
        QMessageBox.information(
            self, "Ayuda",
            "Define las propiedades del elemento de la etiqueta.\n\n"
            "General: nombre, descripción y estado.\n"
            "Data: origen del contenido (texto, variable o expresión).\n"
            "Font: tipografía, tamaño y estilo.\n"
            "Color: color de texto y de fondo.\n"
            "Position: coordenadas, dimensiones, rotación y borde.\n\n"
            "Al pulsar OK los cambios se aplican al elemento en el lienzo.")

    # ---- Resultado ----

    def campo_resultado(self) -> dict:
        c = dict(self._campo)
        c["name"] = self.txt_name.text().strip()
        c["descripcion"] = self.txt_desc.toPlainText()
        if self.rd_disabled.isChecked():
            c["status"] = "disabled"
        elif self.rd_conditional.isChecked():
            c["status"] = "conditional"
        else:
            c["status"] = "enabled"
        c["visible"] = c["status"] != "disabled"

        origen = self.cmb_origen.currentData()
        if origen == "dato":
            c["tipo"] = "dato"
            c["dato"] = self.cmb_dato2.currentData()
            c["origen"] = "dato"
        else:
            c["tipo"] = "texto"
            c["texto"] = (self.txt_expresion.text() if origen == "expresion"
                          else self.txt_texto.text())
            c["origen"] = "expresion" if origen == "expresion" else "texto"
        c["label"] = self.txt_label2.text()

        c["familia"] = self.cmb_familia.currentFont().family()
        c["size"] = int(self.sp_size.value())
        c["label_size"] = int(self.sp_label_size.value())
        c["bold"] = bool(self.chk_bold.isChecked())
        c["cursiva"] = bool(self.chk_cursiva.isChecked())
        c["subrayado"] = bool(self.chk_subrayado.isChecked())
        c["alineacion"] = self.cmb_alineacion.currentData() or "izquierda"

        c["x_mm"] = float(self.sp_x.value())
        c["y_mm"] = float(self.sp_y.value())
        c["ancho_mm"] = float(self.sp_w.value())
        c["alto_mm"] = float(self.sp_h.value())
        c["rotacion"] = int(self.cmb_rotacion.currentData())
        c["borde_visible"] = bool(self.chk_borde.isChecked())
        c["borde_grosor_mm"] = float(self.sp_borde_grosor.value())
        c["color_borde"] = self._campo.get("color_borde", "#000000")
        return normalizar_campo(c, self._ancho)
