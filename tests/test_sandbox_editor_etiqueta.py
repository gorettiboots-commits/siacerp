"""Pruebas del componente aprobado 'editor_etiqueta' (y su demo del sandbox).

Cubre:
    - Registro en el catálogo (regla C-02/C-07).
    - Tamaño de lienzo configurable (ancho/alto en mm).
    - Agregar/quitar campos de texto y dato.
    - Guardado de diseños con nombre en la base de datos (etiqueta_config),
      sin generar archivos sueltos en disco.
    - Diálogo a pantalla completa con el editor.

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import sqlite3

import pytest
from PySide6.QtTest import QTest

from src.components import listar_componentes, obtener_componente
from src.components.editor_etiqueta import normalizar_diseno
from src.components.editor_etiqueta_widget import (
    DialogoEditorEtiqueta, EditorEtiquetaWidget,
)
from src.models.etiqueta_model import DEFAULT_DISENO, EtiquetaModel
from src.views.sandbox_editor_etiqueta import EditorEtiquetaPreview

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class _BDTemporal:
    """Mini DatabaseManager sobre una BD sqlite temporal (mismos métodos)."""

    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE etiqueta_config ("
            "clave TEXT PRIMARY KEY, valor TEXT NOT NULL, "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')))")

    def execute(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        self.conn.commit()
        return c

    def fetch_one(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        row = c.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]


@pytest.fixture
def editor(qapp, tmp_path, monkeypatch):
    # El widget consulta la BD al construirse; apuntamos el modelo a una BD
    # temporal ANTES de instanciarlo para no tocar la BD real del proyecto.
    from src.models import etiqueta_model as mod_modelo
    bd = _BDTemporal(str(tmp_path / "etiquetas_test.db"))
    monkeypatch.setattr(mod_modelo, "DatabaseManager", lambda: bd)
    w = EditorEtiquetaWidget()
    w.show()
    QTest.qWait(60)
    yield w
    w.close()
    w.deleteLater()


# ------------------------------------------------- Catálogo
class TestCatalogo:
    def test_editor_etiqueta_esta_registrado(self):
        nombres = [c["nombre"] for c in listar_componentes()]
        assert "editor_etiqueta" in nombres
        assert "editor_etiqueta_dialog" in nombres

    def test_obtener_componente_devuelve_la_clase(self):
        assert obtener_componente("editor_etiqueta") is EditorEtiquetaWidget
        assert obtener_componente("editor_etiqueta_dialog") is DialogoEditorEtiqueta

    def test_sandbox_reutiliza_el_componente_aprobado(self):
        # La demo del sandbox es el mismo widget del catálogo (sin duplicar).
        assert EditorEtiquetaPreview is EditorEtiquetaWidget


# ------------------------------------------------- Diálogo fullscreen
class TestDialogo:
    def test_dialogo_contiene_el_editor(self, qapp, tmp_path, monkeypatch):
        from src.models import etiqueta_model as mod_modelo
        bd = _BDTemporal(str(tmp_path / "dialogo_test.db"))
        monkeypatch.setattr(mod_modelo, "DatabaseManager", lambda: bd)
        dlg = DialogoEditorEtiqueta()
        assert isinstance(dlg.editor, EditorEtiquetaWidget)
        assert dlg.btn_cerrar is not None
        dlg.close()
        dlg.deleteLater()

    def test_abrir_fullscreen_maximiza(self, qapp, tmp_path, monkeypatch):
        from src.models import etiqueta_model as mod_modelo
        bd = _BDTemporal(str(tmp_path / "dialogo_test.db"))
        monkeypatch.setattr(mod_modelo, "DatabaseManager", lambda: bd)
        dlg = DialogoEditorEtiqueta()
        dlg.showMaximized()
        QTest.qWait(60)
        assert dlg.isMaximized()
        dlg.close()
        dlg.deleteLater()


# ------------------------------------------------- Tamaño de lienzo
class TestTamanoLienzo:
    def test_cambiar_tamano_lienzo_actualiza_diseno(self, editor):
        editor.sp_ancho.setValue(100.0)
        editor.sp_alto.setValue(70.0)
        editor._aplicar_tamano()
        assert float(editor._diseno["ancho_mm"]) == 100.0
        assert float(editor._diseno["alto_mm"]) == 70.0
        assert editor.lbl_tamano.text() == "100 × 70 mm"

    def test_normalizar_diseno_respeta_tamano_guardado(self):
        diseno = dict(DEFAULT_DISENO)
        diseno["ancho_mm"] = 120.0
        diseno["alto_mm"] = 60.0
        normalizado = normalizar_diseno(diseno)
        assert float(normalizado["ancho_mm"]) == 120.0
        assert float(normalizado["alto_mm"]) == 60.0

    def test_normalizar_diseno_usa_default_sin_tamano(self):
        normalizado = normalizar_diseno({"campos": []})
        assert float(normalizado["ancho_mm"]) == 76.0
        assert float(normalizado["alto_mm"]) == 51.0


# ------------------------------------------------- Campos
class TestCampos:
    def test_agregar_campo_texto(self, editor):
        antes = editor.tbl_campos.rowCount()
        editor._agregar_campo("texto")
        assert editor.tbl_campos.rowCount() == antes + 1
        assert editor._diseno["campos"][-1]["tipo"] == "texto"

    def test_agregar_campo_dato(self, editor):
        editor._agregar_campo("dato")
        assert editor._diseno["campos"][-1]["tipo"] == "dato"
        assert editor._diseno["campos"][-1]["dato"] == "modelo"

    def test_quitar_campo(self, editor):
        editor._agregar_campo("texto")
        editor._idx = editor.tbl_campos.rowCount() - 1
        antes = editor.tbl_campos.rowCount()
        editor._quitar_campo()
        assert editor.tbl_campos.rowCount() == antes - 1

    def test_duplicar_campo(self, editor):
        editor._agregar_campo("texto")
        editor._idx = editor.tbl_campos.rowCount() - 1
        antes = editor.tbl_campos.rowCount()
        editor._duplicar_campo()
        assert editor.tbl_campos.rowCount() == antes + 1


# ------------------------------------------------- Guardado en BD
class TestGuardadoBD:
    def test_guardar_y_recuperar_diseno_nombre(self, editor):
        nombre = "etiqueta_prueba"
        editor.txt_nombre.setText(nombre)
        editor._guardar_en_bd()
        guardados = editor.modelo.listar_disenos()
        assert len(guardados) == 1
        assert guardados[0]["clave"] == f"diseno:{nombre}"
        recuperado = editor.modelo.cargar_diseno_nombre(nombre)
        assert recuperado is not None
        assert "campos" in recuperado

    def test_guardar_actualiza_en_vez_de_duplicar(self, editor):
        editor.txt_nombre.setText("mismo_nombre")
        editor._guardar_en_bd()
        editor.sp_ancho.setValue(90.0)
        editor._aplicar_tamano()
        editor._guardar_en_bd()
        assert len(editor.modelo.listar_disenos()) == 1

    def test_eliminar_diseno(self, editor):
        editor.txt_nombre.setText("a_eliminar")
        editor._guardar_en_bd()
        assert len(editor.modelo.listar_disenos()) == 1
        editor.modelo.eliminar_diseno("a_eliminar")
        assert len(editor.modelo.listar_disenos()) == 0

    def test_nuevo_restablece_diseno_por_defecto(self, editor):
        editor._nuevo()
        assert float(editor._diseno["ancho_mm"]) == 76.0
        assert editor.txt_nombre.text() == ""


# ------------------------------------------------- Modelo (aislado)
class TestEtiquetaModel:
    def test_modelo_guardado_no_crea_archivos(self, tmp_path):
        """El diseño vive en la BD; la carpeta queda sin archivos sueltos."""
        bd = _BDTemporal(str(tmp_path / "modelo_test.db"))
        modelo = EtiquetaModel()
        modelo.db = bd
        modelo.guardar_diseno_nombre("plantilla", dict(DEFAULT_DISENO))
        archivos = [p.name for p in tmp_path.iterdir()]
        assert archivos == ["modelo_test.db"]
