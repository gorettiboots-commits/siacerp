"""Pruebas del componente aprobado: NotificacionesFlotantes (toasts).

Cubre la API pública del catálogo `notificacion_flotante`: tipos, notificar,
posición por esquina, cierre automático/manual, interacción al hacer clic y la
función singleton `notificar_flotante`.

Convención de nombres: [función]_[condición]_[resultadoEsperado].
Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest
from PySide6.QtCore import QEvent, QPointF, QRect, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

import src.components.notificacion_flotante as mod
from src.components.notificacion_flotante import (
    NotificacionesFlotantes,
    notificar_flotante,
)
from src.utils.icons import _GLIFOS

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture
def host(qapp):
    widget = QWidget()
    widget.resize(900, 600)
    widget.show()
    QTest.qWait(80)
    yield widget
    widget.close()
    widget.deleteLater()
    QTest.qWait(60)


@pytest.fixture(autouse=True)
def limpiar_singleton(monkeypatch):
    monkeypatch.setattr(mod, "_instancia", None)


def borde_izquierdo(notificador, card):
    return card.mapTo(notificador._host, card.rect().topLeft()).x()


def borde_superior(notificador, card):
    return card.mapTo(notificador._host, card.rect().topLeft()).y()


def borde_derecho(notificador, card):
    return card.mapTo(notificador._host, card.rect().topRight()).x()


def borde_inferior(notificador, card):
    return card.mapTo(notificador._host, card.rect().bottomLeft()).y()


# ------------------------------------------------------------------ _TIPOS
class TestTipos:
    def test_tipos_mapping_cuatro_tipos_esperados(self):
        assert set(mod._TIPOS) == {"info", "success", "warning", "error"}

    def test_tipos_cada_uno_tiene_color_e_icono(self):
        for cfg in mod._TIPOS.values():
            assert cfg["color"].startswith("#")
            assert cfg["icono"] in _GLIFOS

    def test_tarjeta_tipo_desconocido_cae_a_info(self, qapp):
        notificador = NotificacionesFlotantes(host=None)
        notificador.notificar("mensaje", tipo="desconocido")
        assert notificador._cards[0]._color == mod._TIPOS["info"]["color"]


# ------------------------------------------------------------ notificar()
class TestNotificar:
    def test_notificar_agrega_tarjeta_visible(self, host):
        notificador = NotificacionesFlotantes(host=host, ancho=360)
        notificador.notificar("mensaje", duracion=30)
        assert notificador.visibles == 1
        assert notificador._cards[0].isVisible()
        assert notificador._cards[0].width() == 360

    def test_notificar_mensaje_vacio_no_falla(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("", duracion=30)
        assert notificador.visibles == 1

    def test_notificar_varias_tarjetas_todas_visibles(self, host):
        notificador = NotificacionesFlotantes(host=host)
        for i in range(4):
            notificador.notificar(f"mensaje {i}", duracion=30)
        QTest.qWait(400)
        assert notificador.visibles == 4
        assert all(c.isVisible() for c in notificador._cards)

    def test_notificar_sin_host_se_queda_flotante_o_ancla(self, qapp):
        notificador = NotificacionesFlotantes(host=None)
        notificador.notificar("mensaje", duracion=30)
        assert notificador.visibles == 1
        assert notificador._modo in ("flotante", "overlay")


# ---------------------------------------------------------------- Posición
class TestPosicionamiento:
    def test_apilado_esquina_br_respeta_margen_derecho(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="br",
                                              ancho=360, margen=16)
        for _ in range(3):
            notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        for card in notificador._cards:
            margen_real = host.width() - borde_derecho(notificador, card)
            assert 12 <= margen_real <= 20
        assert notificador._cards[0].y() < notificador._cards[1].y()
        assert notificador._cards[1].y() < notificador._cards[2].y()

    def test_apilado_esquina_br_tarjeta_inferior_cerca_del_borde(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="br",
                                              margen=16)
        for _ in range(3):
            notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        ultima = notificador._cards[-1]
        distancia = host.height() - borde_inferior(notificador, ultima)
        assert abs(distancia - 16) <= 5

    def test_apilado_esquina_tl_se_coloca_arriba_izquierda(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="tl",
                                              margen=16)
        notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        card = notificador._cards[0]
        assert 12 <= borde_izquierdo(notificador, card) <= 20
        assert 12 <= borde_superior(notificador, card) <= 20

    def test_apilado_esquina_tr_tarjetas_decrecen_hacia_abajo(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="tr",
                                              margen=16)
        for _ in range(2):
            notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        assert notificador._cards[0].y() < notificador._cards[1].y()
        for card in notificador._cards:
            assert borde_derecho(notificador, card) >= host.width() - 20

    def test_reflota_al_redimensionar_host(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="br",
                                              ancho=360, margen=16)
        notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        host.resize(1200, 700)
        QTest.qWait(200)
        card = notificador._cards[0]
        assert 1180 <= borde_derecho(notificador, card) <= 1192

    def test_geo_base_overlay_devuelve_rect_del_host(self, host):
        notificador = NotificacionesFlotantes(host=host)
        assert notificador._geo_base() == QRect(0, 0, host.width(),
                                                host.height())

    def test_geo_base_flotante_devuelve_rect_con_dimensiones(self, qapp):
        notificador = NotificacionesFlotantes(host=None)
        geo = notificador._geo_base()
        assert geo.width() > 0
        assert geo.height() > 0

    def test_set_esquina_invalida_no_la_cambia(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="br")
        notificador.set_esquina("zz")
        assert notificador._esquina == "br"

    def test_set_esquina_valida_reflota(self, host):
        notificador = NotificacionesFlotantes(host=host, esquina="br")
        notificador.notificar("mensaje", duracion=30)
        QTest.qWait(500)
        notificador.set_esquina("tl")
        QTest.qWait(300)
        card = notificador._cards[0]
        assert borde_izquierdo(notificador, card) < 20
        assert borde_superior(notificador, card) < 20


# ----------------------------------------------------------------- Cierre
class TestCierre:
    def test_cierre_automatico_elimina_tarjeta_y_oculta_overlay(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("mensaje", duracion=0.2)
        QTest.qWait(1200)
        assert notificador.visibles == 0
        assert notificador.isHidden()

    def test_cierre_manual_reflota_tarjeta_restante(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("a", duracion=30)
        notificador.notificar("b", duracion=30)
        QTest.qWait(300)
        notificador._cards[0].cerrar()
        QTest.qWait(350)
        assert notificador.visibles == 1
        assert notificador._cards[0].y() < 30

    def test_cierre_doble_es_idempotente(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("mensaje", duracion=30)
        card = notificador._cards[0]
        card.cerrar()
        card.cerrar()
        assert card._cerrada
        QTest.qWait(400)
        assert notificador.visibles == 0

    def test_cerrar_todas_vacia_y_oculta_overlay(self, host):
        notificador = NotificacionesFlotantes(host=host)
        for i in range(3):
            notificador.notificar(f"mensaje {i}", duracion=30)
        QTest.qWait(300)
        notificador.cerrar_todas()
        QTest.qWait(800)
        assert notificador.visibles == 0
        assert notificador.isHidden()

    def test_duracion_cero_desactiva_cierre_automatico(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("mensaje", duracion=0)
        QTest.qWait(1200)
        assert notificador.visibles == 1


# ---------------------------------------------------------- Interacción
class TestInteraccion:
    def test_tarjeta_on_click_dispara_callback_y_cierra(self, host):
        notificador = NotificacionesFlotantes(host=host)
        clics = {"n": 0}

        def al_clic():
            clics["n"] += 1

        notificador.notificar("mensaje", duracion=0, on_click=al_clic)
        card = notificador._cards[0]
        evento = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(5, 5),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        card.mousePressEvent(evento)
        assert clics["n"] == 1
        assert card._cerrada

    def test_tarjeta_click_sin_callback_solo_cierra(self, host):
        notificador = NotificacionesFlotantes(host=host)
        notificador.notificar("mensaje", duracion=0)
        card = notificador._cards[0]
        evento = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(5, 5),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        card.mousePressEvent(evento)
        assert card._cerrada


# --------------------------------------------------------- notificar_flotante
class TestNotificarFlotante:
    def test_notificar_flotante_reutiliza_instancia_singleton(self, qapp):
        notificar_flotante("primera", duracion=30)
        instancia_1 = mod._instancia
        notificar_flotante("segunda", duracion=30)
        assert mod._instancia is instancia_1
        assert instancia_1.visibles == 2

    def test_notificar_flotante_aplica_esquina_pedida(self, qapp):
        notificar_flotante("mensaje", duracion=30, esquina="tl")
        assert mod._instancia._esquina == "tl"

    def test_notificar_flotante_cambia_host(self, qapp, host):
        otro_host = QWidget()
        otro_host.resize(500, 400)
        notificar_flotante("mensaje", duracion=30, host=host)
        notificar_flotante("otro", duracion=30, host=otro_host)
        assert mod._instancia._host is otro_host


class TestCardNotificacion:
    def test_card_altura_coincide_con_su_contenido(self, qapp):
        notificador = NotificacionesFlotantes(host=None)
        notificador.notificar("mensaje corto", duracion=30)
        card = notificador._cards[0]
        assert card.height() == card._caja.sizeHint().height()
