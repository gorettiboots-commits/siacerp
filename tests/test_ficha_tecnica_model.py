import sqlite3

import pytest

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class _BDTemporal:
    """Mini DatabaseManager sobre una BD sqlite temporal (mismos métodos)."""

    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute(
            "CREATE TABLE modelos (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "codigo TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL, "
            "descripcion TEXT, imagen BLOB, activo INTEGER NOT NULL DEFAULT 1, "
            "created_at TEXT DEFAULT (datetime('now')), "
            "updated_at TEXT DEFAULT (datetime('now')))")
        cur.execute(
            "CREATE TABLE fichas_tecnicas (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "modelo_id INTEGER NOT NULL, estilo_sistema TEXT, estilo_muestra TEXT, "
            "marca TEXT, talla TEXT, genero TEXT, horma TEXT, moldura TEXT, "
            "construccion TEXT, corrida TEXT, scallop TEXT, tacon TEXT, notas TEXT, "
            "imagen BLOB, fuente_archivo TEXT, activo INTEGER NOT NULL DEFAULT 1, "
            "created_at TEXT DEFAULT (datetime('now')), "
            "updated_at TEXT DEFAULT (datetime('now')))")
        cur.execute(
            "CREATE TABLE ficha_tecnica_secciones (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "ficha_id INTEGER NOT NULL, nombre TEXT NOT NULL, "
            "orden INTEGER NOT NULL DEFAULT 0)")
        cur.execute(
            "CREATE TABLE ficha_tecnica_detalle (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "seccion_id INTEGER NOT NULL, componente TEXT, descripcion TEXT, "
            "proveedor TEXT, comentarios TEXT, orden INTEGER NOT NULL DEFAULT 0)")
        self.conn.commit()

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
def bd(tmp_path, monkeypatch):
    from src.models import ficha_tecnica_model as mod_modelo
    bd = _BDTemporal(str(tmp_path / "ficha_tec_test.db"))
    monkeypatch.setattr(mod_modelo, "DatabaseManager", lambda: bd)
    return bd


class TestFichaTecnicaModel:
    def test_guardar_y_obtener_completa(self, bd):
        from src.models.ficha_tecnica_model import FichaTecnicaModel
        bd.execute("INSERT INTO modelos (codigo, nombre) VALUES (?, ?)",
                   ("GBC-01", "BOTIN CHIMU"))
        modelo_id = bd.fetch_one(
            "SELECT id FROM modelos WHERE codigo = ?", ("GBC-01",))["id"]
        f = FichaTecnicaModel()
        ficha_id = f.guardar(
            modelo_id,
            datos={"estilo_sistema": "GBC-01", "marca": "GORETTI",
                   "genero": "DAMA", "construccion": "PEGADO"},
            secciones=[{
                "nombre": "CORTE",
                "detalle": [
                    {"componente": "PIEL", "descripcion": "GORA TAN",
                     "proveedor": "SULTANA", "comentarios": "DOBLADILLO"},
                    {"componente": "SUELA", "descripcion": "INTEGRAL",
                     "proveedor": "", "comentarios": ""},
                ],
            }],
            imagen=b"\x89PNG\r\n\x1a\n",
            fuente_archivo="prueba.xlsx",
        )
        assert ficha_id > 0

        ficha = f.obtener_completa(modelo_id)
        assert ficha is not None
        assert ficha["marca"] == "GORETTI"
        assert ficha["estilo_sistema"] == "GBC-01"
        assert ficha["fuente_archivo"] == "prueba.xlsx"
        assert len(ficha["secciones"]) == 1
        assert ficha["secciones"][0]["nombre"] == "CORTE"
        assert len(ficha["secciones"][0]["detalle"]) == 2
        assert ficha["secciones"][0]["detalle"][1]["componente"] == "SUELA"

        assert f.obtener_imagen(ficha_id) == b"\x89PNG\r\n\x1a\n"

    def test_obtener_por_modelo_inexistente(self, bd):
        from src.models.ficha_tecnica_model import FichaTecnicaModel
        assert FichaTecnicaModel().obtener_por_modelo(999) is None

    def test_eliminar_por_modelo_limpia_secciones_y_detalle(self, bd):
        from src.models.ficha_tecnica_model import FichaTecnicaModel
        bd.execute("INSERT INTO modelos (codigo, nombre) VALUES (?, ?)",
                   ("GBC-02", "OTRO"))
        modelo_id = bd.fetch_one(
            "SELECT id FROM modelos WHERE codigo = ?", ("GBC-02",))["id"]
        f = FichaTecnicaModel()
        f.guardar(modelo_id, {"marca": "G"},
                  secciones=[{"nombre": "CORTE",
                              "detalle": [{"componente": "A"}]}],
                  imagen=None)
        assert f.obtener_por_modelo(modelo_id) is not None
        f.eliminar_por_modelo(modelo_id)
        assert f.obtener_por_modelo(modelo_id) is None
        n_sec = bd.fetch_one("SELECT COUNT(*) AS n FROM ficha_tecnica_secciones")["n"]
        n_det = bd.fetch_one("SELECT COUNT(*) AS n FROM ficha_tecnica_detalle")["n"]
        assert n_sec == 0
        assert n_det == 0
