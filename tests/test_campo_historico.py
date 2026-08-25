"""Pruebas del componente aprobado 'campo_historico'.

Cubre:
    - Registro en el catálogo (regla C-02/C-07).
    - Deducción automática de la clave del campo (label, placeholder,
      objectName, propiedad explícita, sin clave).
    - Activación en campos habilitados y omisión de los que no aplican.
    - Registro/borrado del histórico en `historico_campos`.
    - Aplicación global (walker + instalador de eventos) y autocompletado.

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QGridLayout, QLabel, QLineEdit,
    QVBoxLayout, QWidget,
)

from src.components import listar_componentes, obtener_componente
from src.components.campo_historico import (
    CampoHistorico, InstaladorHistorico, aplicar_historico,
    habilitar_campo, obtener_clave_campo,
)
from src.models.historico_campos_model import HistoricoCamposModel

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

_CAMPO = "test_historico_campos"


@pytest.fixture(scope="session", autouse=True)
def _esquema_historico():
    """Asegura que `historico_campos` exista en la BD (como en el arranque)."""
    from src.database.db_manager import DatabaseManager

    DatabaseManager().initialize_schema()


@pytest.fixture(autouse=True)
def _limpiar_historico():
    yield
    HistoricoCamposModel().borrar(_CAMPO)


@pytest.fixture
def modelo(qapp):
    return HistoricoCamposModel()


# ------------------------------------------------- Catálogo
class TestCatalogo:
    def test_campo_historico_esta_registrado(self):
        nombres = [c["nombre"] for c in listar_componentes()]
        assert "campo_historico" in nombres

    def test_obtener_componente_devuelve_la_clase(self):
        assert obtener_componente("campo_historico") is CampoHistorico


# ------------------------------------------------- Deducción de clave
class TestClaveCampo:
    def test_label_de_form_layout(self, qapp):
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Modelo:", edit)
        assert obtener_clave_campo(edit) == "Modelo"

    def test_label_de_grid_layout(self, qapp):
        grid = QGridLayout(container := QWidget())
        etiqueta = QLabel("Piel:")
        edit = QLineEdit()
        grid.addWidget(etiqueta, 0, 0)
        grid.addWidget(edit, 0, 1)
        assert obtener_clave_campo(edit) == "Piel"

    def test_placeholder_sin_parentesis(self, qapp):
        edit = QLineEdit()
        edit.setPlaceholderText("Ej: RENATO GALAN (obligatorio)")
        assert obtener_clave_campo(edit) == "Ej: RENATO GALAN"

    def test_object_name(self, qapp):
        edit = QLineEdit()
        edit.setObjectName("txt_codigo")
        assert obtener_clave_campo(edit) == "txt_codigo"

    def test_propiedad_explicita_tiene_prioridad(self, qapp):
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Dirección:", edit)
        edit.setProperty("_claveCampo", "direccion_manual")
        assert obtener_clave_campo(edit) == "direccion_manual"

    def test_sin_clave_devuelve_none(self, qapp):
        edit = QLineEdit()
        assert obtener_clave_campo(edit) is None


# ------------------------------------------------- Activación del campo
class TestHabilitar:
    def test_campo_habilitado_queda_activo(self, modelo):
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Nombre:", edit)
        assert habilitar_campo(edit, modelo) == "Nombre"
        assert edit.property("_campoHistoricoAplicado") == "Nombre"
        assert edit.completer() is not None
        container.deleteLater()

    def test_deshabilitado_se_omite(self, modelo):
        edit = QLineEdit()
        edit.setEnabled(False)
        assert habilitar_campo(edit, modelo) is None

    def test_solo_lectura_se_omite(self, modelo):
        edit = QLineEdit()
        edit.setReadOnly(True)
        assert habilitar_campo(edit, modelo) is None

    def test_contrasena_se_omite(self, modelo):
        edit = QLineEdit()
        edit.setEchoMode(QLineEdit.Password)
        assert habilitar_campo(edit, modelo) is None

    def test_es_idempotente(self, modelo):
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Teléfono:", edit)
        assert habilitar_campo(edit, modelo) == "Teléfono"
        assert habilitar_campo(edit, modelo) == "Teléfono"
        container.deleteLater()


# ------------------------------------------------- Histórico en BD
class TestHistorico:
    def test_registrar_y_listar(self, modelo):
        modelo.registrar(_CAMPO, "PIEL CARA")
        modelo.registrar(_CAMPO, "PIEL TERNERA")
        modelo.registrar(_CAMPO, "PIEL CARA")
        valores = [fila["valor"] for fila in modelo.listar_por_campo(_CAMPO)]
        assert valores == ["PIEL CARA", "PIEL TERNERA"]

    def test_no_registra_vacios(self, modelo):
        modelo.registrar(_CAMPO, "")
        modelo.registrar(_CAMPO, "   ")
        assert modelo.listar_por_campo(_CAMPO) == []

    def test_borrar_por_campo(self, modelo):
        modelo.registrar(_CAMPO, "A")
        modelo.registrar(_CAMPO, "B")
        modelo.borrar(_CAMPO)
        assert modelo.listar_por_campo(_CAMPO) == []


# ------------------------------------------------- Comportamiento del widget
class TestComportamiento:
    def test_captura_se_registra_al_salir(self, modelo):
        modelo.borrar("Suela")
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Suela:", edit)
        habilitar_campo(edit, modelo)
        edit.setText("PIEL CARA")
        edit.editingFinished.emit()
        valores = [fila["valor"] for fila in modelo.listar_por_campo("Suela")]
        assert valores == ["PIEL CARA"]
        container.deleteLater()
        modelo.borrar("Suela")

    def test_campo_historico_subclase(self, modelo):
        edit = CampoHistorico("clave_manual")
        assert edit.property("_campoHistoricoAplicado") == "clave_manual"
        edit.deleteLater()

    def test_historico_se_despliega_solo_al_escribir(self, modelo):
        modelo.borrar("Suela")
        modelo.registrar("Suela", "PIEL CARA")
        modelo.registrar("Suela", "PIEL TERNERA")
        form = QFormLayout(container := QWidget())
        edit = QLineEdit()
        form.addRow("Suela:", edit)
        habilitar_campo(edit, modelo)
        container.show()
        popup = edit.completer().popup()

        # Al recibir foco NO se despliega nada
        QApplication.sendEvent(edit, QEvent(QEvent.FocusIn))
        QTest.qWait(60)
        assert not popup.isVisible()

        # Al hacer clic NO se despliega nada
        clic = QMouseEvent(QEvent.MouseButtonRelease, QPointF(5, 5),
                           QPointF(5, 5), Qt.LeftButton, Qt.LeftButton,
                           Qt.NoModifier)
        QApplication.sendEvent(edit, clic)
        QTest.qWait(60)
        assert not popup.isVisible()

        # Al comenzar a escribir el histórico se despliega filtrado
        edit.setFocus()
        QTest.keyClicks(edit, "CAR")
        QTest.qWait(60)
        assert popup.isVisible()
        container.deleteLater()
        modelo.borrar("Suela")


# ------------------------------------------------- Aplicación global
class TestAplicacionGlobal:
    def test_walker_aplica_en_arbol(self, modelo):
        dialogo = QDialog()
        layout = QVBoxLayout(dialogo)
        form = QFormLayout()
        form.addRow("Cliente:", QLineEdit())
        form.addRow("Folio:", QLineEdit())
        layout.addLayout(form)
        aplicados = aplicar_historico(dialogo, modelo)
        assert aplicados == 2
        dialogo.deleteLater()

    def test_walker_salta_no_habilitados(self, modelo):
        dialogo = QDialog()
        layout = QVBoxLayout(dialogo)
        ed1, ed2 = QLineEdit(), QLineEdit()
        ed2.setEnabled(False)
        layout.addWidget(ed1)
        layout.addWidget(ed2)
        # Sin clave identificable en ambos -> ninguno aplica.
        assert aplicar_historico(dialogo, modelo) == 0
        dialogo.deleteLater()

    def test_instalador_aplica_al_mostrar_dialogo(self, modelo):
        InstaladorHistorico.instalar()
        dialogo = QDialog()
        form = QFormLayout(dialogo)
        form.addRow("Dirección:", QLineEdit())
        dialogo.show()
        aplicados = [edit for edit in dialogo.findChildren(QLineEdit)
                     if edit.property("_campoHistoricoAplicado")]
        assert len(aplicados) == 1
        dialogo.deleteLater()