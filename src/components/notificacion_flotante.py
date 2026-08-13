"""Componente aprobado: notificaciones flotantes (toasts).

Aprobado desde el Sandbox (antes prototipo en `src/views/sandbox_notificaciones.py`).
Tarjetas translúcidas que se apilan en una esquina de la ventana activa (o de
un host fijo), con cierre automático o manual, animación de entrada/salida y
callback opcional al hacer clic. Cuando el sistema quiera informar de algo al
usuario de forma no bloqueante, se usa este componente.

Tipos: "info", "success", "warning", "error".

Uso rápido (elemento singleton):
    from src.components.notificacion_flotante import notificar_flotante
    notificar_flotante("Documento guardado", tipo="success", titulo="Inventario")

Uso con control directo (instancia propia):
    notif = NotificacionesFlotantes(host=ventana, esquina="br")
    notif.notificar("Mensaje", tipo="warning", duracion=5.0)

Posición:
- Por defecto se ancla como overlay de la ventana activa (visible siempre sobre
  el contenido) en la pantalla de esa ventana.
- Se puede fijar un host con `set_host(widget)` y la esquina con `esquina`
  ("br", "tr", "bl", "tl").
"""

from PySide6.QtCore import (
    QEasingCurve, QEvent, QPropertyAnimation, QRect, Qt, QTimer,
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
    QToolButton, QVBoxLayout, QWidget,
)

from src.utils.icons import mono_icon

_PAD = 12  # aire alrededor de la pila (la tarjeta es translúcida)

_TIPOS = {
    "info": {"color": "#2563eb", "icono": "info"},
    "success": {"color": "#16a34a", "icono": "ok"},
    "warning": {"color": "#d97706", "icono": "alerta"},
    "error": {"color": "#dc2626", "icono": "error"},
}


class _CardNotificacion(QFrame):
    """Tarjeta individual de notificación."""

    def __init__(self, notificador, mensaje, tipo, titulo, on_click,
                 parent=None) -> None:
        super().__init__(parent)
        self._notificador = notificador
        self._on_click = on_click
        self._cerrada = False

        cfg = _TIPOS.get(tipo, _TIPOS["info"])
        self._color = cfg["color"]

        self._efecto_opacidad = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._efecto_opacidad)
        self._efecto_opacidad.setOpacity(1.0)

        self._caja = QFrame(self)
        self._caja.setObjectName("toastCard")
        self._caja.setStyleSheet(f"""
            QFrame#toastCard {{
                background: {self._color};
                border-radius: 10px;
            }}
            QFrame#toastCard QLabel#toastTitulo {{
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
            }}
            QFrame#toastCard QLabel#toastMsg {{
                color: rgba(255, 255, 255, 0.92);
                font-size: 11px;
            }}
            QFrame#toastCard QToolButton#toastCerrar {{
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 15px;
                font-weight: 700;
                padding: 2px;
            }}
            QFrame#toastCard QToolButton#toastCerrar:hover {{
                background: rgba(255, 255, 255, 0.18);
                border-radius: 6px;
            }}
        """)

        lay = QHBoxLayout(self._caja)
        lay.setContentsMargins(14, 11, 8, 11)
        lay.setSpacing(10)

        self._icono = QLabel()
        self._icono.setFixedSize(22, 22)
        self._icono.setPixmap(mono_icon(cfg["icono"], 22, "#ffffff").pixmap(22, 22))
        lay.addWidget(self._icono)

        cuerpo = QVBoxLayout()
        cuerpo.setSpacing(1)
        self._titulo = QLabel(titulo or tipo.capitalize())
        self._titulo.setObjectName("toastTitulo")
        self._mensaje = QLabel(mensaje)
        self._mensaje.setObjectName("toastMsg")
        self._mensaje.setWordWrap(True)
        cuerpo.addWidget(self._titulo)
        cuerpo.addWidget(self._mensaje)
        lay.addLayout(cuerpo, 1)

        self._btn_cerrar = QToolButton()
        self._btn_cerrar.setObjectName("toastCerrar")
        self._btn_cerrar.setText("✕")
        self._btn_cerrar.setCursor(Qt.PointingHandCursor)
        self._btn_cerrar.clicked.connect(self.cerrar)
        lay.addWidget(self._btn_cerrar)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._caja.setGeometry(self.rect())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and not self._cerrada:
            if self._on_click:
                self._on_click()
            self.cerrar()
        super().mousePressEvent(event)

    def cerrar(self) -> None:
        if self._cerrada:
            return
        self._cerrada = True
        self._notificador._remover(self)


class NotificacionesFlotantes(QWidget):
    """Pila de notificaciones anclada a un host (o flotante por defecto)."""

    def __init__(self, host: QWidget | None = None, ancho: int = 360,
                 margen: int = 16, separacion: int = 10,
                 esquina: str = "br") -> None:
        super().__init__(None)
        self._ancho = ancho
        self._margen = margen
        self._separacion = separacion
        self._esquina = esquina
        self._cards: list[_CardNotificacion] = []
        self._animaciones: list = []
        self._host: QWidget | None = None
        self._modo = "flotante"

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        if host is not None:
            self.set_host(host)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._seguir_ancla)
        self._timer.start()

        self.destroyed.connect(self._detener_todo)

    def _detener_todo(self) -> None:
        try:
            self._timer.stop()
        except RuntimeError:
            pass
        for anim in list(self._animaciones):
            try:
                anim.stop()
            except RuntimeError:
                pass
        self._animaciones.clear()

    def closeEvent(self, event) -> None:
        self._detener_todo()
        super().closeEvent(event)

    # ------------------------------------------------------------- Anclaje
    def set_host(self, host: QWidget) -> None:
        """Fija el widget sobre el que se dibujan las notificaciones (overlay)."""
        if self._host is host:
            return
        if self._host is not None:
            self._host.removeEventFilter(self)
        self._host = host
        self._modo = "overlay"
        self.setParent(host)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_TranslucentBackground)
        host.installEventFilter(self)
        if self._cards:
            self._reflotar(animar=False)
            self.show()
            self.raise_()

    def set_esquina(self, esquina: str) -> None:
        if esquina in ("br", "tr", "bl", "tl"):
            self._esquina = esquina
            self._reflotar(animar=False)

    # ------------------------------------------------------------------ API
    def notificar(self, mensaje: str, tipo: str = "info", titulo: str | None = None,
                  duracion: float = 4.0, on_click=None) -> None:
        # Si no hay host, ancla a la ventana activa para garantizar visibilidad.
        if self._host is None:
            ventana = QApplication.activeWindow()
            if ventana is not None:
                self.set_host(ventana)

        card = _CardNotificacion(self, mensaje, tipo, titulo, on_click, self)
        card.setFixedWidth(self._ancho)
        card._caja.adjustSize()
        card.setFixedHeight(card._caja.sizeHint().height())
        self._cards.append(card)
        card.show()

        self._reflotar(animar=False)
        self.show()
        self.raise_()

        destino = card.geometry()
        t = 60 if self._esquina.endswith("r") else -60
        card.setGeometry(destino.translated(t, 0))
        card._efecto_opacidad.setOpacity(0.0)

        anim_pos = QPropertyAnimation(card, b"geometry", self)
        anim_pos.setEndValue(destino)
        anim_pos.setDuration(240)
        anim_pos.setEasingCurve(QEasingCurve.OutCubic)
        anim_pos.start()

        anim_op = QPropertyAnimation(card._efecto_opacidad, b"opacity", self)
        anim_op.setEndValue(1.0)
        anim_op.setDuration(240)
        anim_op.setEasingCurve(QEasingCurve.OutCubic)
        anim_op.start()

        self._animaciones.extend([anim_pos, anim_op])

        # El conteo inicia después de la animación de entrada: el tiempo visible
        # de la tarjeta es realmente `duracion`. El timer es hijo de la tarjeta
        # para que se destruya con ella y nunca dispare sobre una ya borrada.
        if duracion and duracion > 0:
            timer = QTimer(card)
            timer.setSingleShot(True)
            timer.timeout.connect(card.cerrar)
            timer.start(int(duracion * 1000) + 240)

    def cerrar_todas(self) -> None:
        for card in list(self._cards):
            card.cerrar()

    @property
    def visibles(self) -> int:
        return len(self._cards)

    # ------------------------------------------------------------- Posición
    def _geo_base(self) -> QRect:
        if self._modo == "overlay" and self._host is not None:
            return QRect(0, 0, self._host.width(), self._host.height())
        ventana = QApplication.activeWindow()
        pantalla = None
        if ventana is not None and ventana.windowHandle() is not None:
            pantalla = ventana.windowHandle().screen()
        if pantalla is None:
            pantalla = (QApplication.screenAt(QCursor.pos())
                        or QApplication.primaryScreen())
        if pantalla is None:
            return QRect(0, 0, 800, 600)
        return pantalla.availableGeometry()

    def _reflotar(self, animar: bool = True) -> None:
        activas = [c for c in self._cards if not c._cerrada]
        if not activas:
            return
        geo = self._geo_base()
        w = self._ancho
        altos = [c.height() for c in activas]
        n = len(activas)
        total = sum(altos) + self._separacion * (n - 1)
        m = self._margen

        if self._esquina.startswith("b"):
            y_card = geo.bottom() - m - total
        else:
            y_card = geo.top() + m
        if self._esquina.endswith("l"):
            x_card = geo.left() + m
        else:
            x_card = geo.right() - m - w

        x0 = x_card - _PAD
        y0 = y_card - _PAD
        w0 = w + 2 * _PAD
        h0 = total + 2 * _PAD
        self.setGeometry(x0, y0, w0, h0)

        for i, card in enumerate(activas):
            y = _PAD + sum(altos[:i]) + self._separacion * i
            destino = QRect(_PAD, y, w, altos[i])
            if animar and card.geometry() != destino:
                anim = QPropertyAnimation(card, b"geometry", self)
                anim.setEndValue(destino)
                anim.setDuration(180)
                anim.setEasingCurve(QEasingCurve.OutCubic)
                anim.start()
                self._animaciones.append(anim)
            else:
                card.setGeometry(destino)

    def _seguir_ancla(self) -> None:
        if not self._cards or self._modo == "overlay":
            return
        if any(c._cerrada for c in self._cards):
            return  # en medio de una animación de cierre
        self._reflotar(animar=False)

    def eventFilter(self, obj, event) -> bool:
        if (obj is self._host and self._cards
                and event.type() in (QEvent.Resize, QEvent.Move)):
            self._reflotar(animar=False)
        return super().eventFilter(obj, event)

    # --------------------------------------------------------------- Cierre
    def _remover(self, card: _CardNotificacion) -> None:
        if card not in self._cards:
            return
        anim_op = QPropertyAnimation(card._efecto_opacidad, b"opacity", self)
        anim_op.setEndValue(0.0)
        anim_op.setDuration(200)
        anim_op.setEasingCurve(QEasingCurve.InCubic)
        anim_pos = QPropertyAnimation(card, b"geometry", self)
        anim_pos.setEndValue(card.geometry().translated(60, 0))
        anim_pos.setDuration(200)
        anim_pos.setEasingCurve(QEasingCurve.InCubic)

        def _limpiar():
            # Detener las animaciones antes de borrar la tarjeta: si el efecto
            # de opacidad aún está en vuelo al destruirla, Qt corrompe el heap
            # y el proceso muere (segfault) en la siguiente creación de widget.
            anim_op.stop()
            anim_pos.stop()
            if card in self._cards:
                self._cards.remove(card)
            card.deleteLater()
            self._reflotar(animar=True)
            if not self._cards:
                self.hide()
            elif self._modo == "overlay":
                self.raise_()

        anim_pos.finished.connect(_limpiar)
        anim_op.finished.connect(lambda: None)
        anim_pos.start()
        anim_op.start()
        self._animaciones.extend([anim_pos, anim_op])


_instancia: NotificacionesFlotantes | None = None


def notificar_flotante(mensaje: str, tipo: str = "info", titulo: str | None = None,
                       duracion: float = 4.0, on_click=None,
                       host: QWidget | None = None, esquina: str | None = None) -> None:
    """Envía una notificación flotante (elemento singleton)."""
    global _instancia
    if _instancia is None:
        _instancia = NotificacionesFlotantes(host=host,
                                             esquina=esquina or "br")
    elif esquina is not None:
        _instancia.set_esquina(esquina)
    if host is not None:
        _instancia.set_host(host)
    _instancia.notificar(mensaje, tipo=tipo, titulo=titulo,
                         duracion=duracion, on_click=on_click)
