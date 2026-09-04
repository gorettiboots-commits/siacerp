"""Pruebas de exportación e importación de conjuntos de datos (respaldos).

Cubre:
    - Definición de conjuntos: tablas existentes y orden de dependencia.
    - Conversión de valores (BLOB/base64, fechas, decimales).
    - Exportación a archivo + inspección sin importar.
    - Importación en modo Agregar (roundtrip: exportar, borrar, restaurar).
    - Importación en modo Reemplazar sobre una tabla segura.
    - Rechazo de archivos inválidos y de identificadores no confiables.

Se ejecutan headless (QT_QPA_PLATFORM=offscreen) contra la BD de desarrollo;
solo tocan tablas seguras (historico_campos) y limpian al terminar.
"""

import json

import pytest

from src.database.db_manager import DatabaseManager
from src.models.historico_campos_model import HistoricoCamposModel
from src.utils.respaldo_bd_utils import (
    CONJUNTOS, _json_a_valor, _valor_a_json, exportar_conjuntos,
    importar_conjuntos, inspeccionar_archivo, listar_conjuntos,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")

_CAMPO = "test_respaldo_bd"


@pytest.fixture(scope="module", autouse=True)
def _esquema():
    DatabaseManager().initialize_schema()


@pytest.fixture(autouse=True)
def _limpiar():
    yield
    HistoricoCamposModel().borrar(_CAMPO)


# ------------------------------------------------------------- conjuntos
class TestConjuntos:
    def test_todas_las_tablas_existen(self):
        db = DatabaseManager()
        for conjunto in CONJUNTOS:
            for tabla in conjunto["tablas"]:
                fila = db.fetch_one(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name=?", (tabla,))
                assert fila is not None, f"Tabla inexistente: {tabla}"

    def test_sin_tablas_repetidas(self):
        todas = [t for c in CONJUNTOS for t in c["tablas"]]
        assert len(todas) == len(set(todas))

    def test_listar_conjuntos_regresa_filas(self):
        conjuntos = listar_conjuntos()
        assert len(conjuntos) == len(CONJUNTOS)
        for c in conjuntos:
            assert c["filas"] >= 0 and c["nombre"] and c["clave"]


# ------------------------------------------------------------ conversión
class TestConversion:
    def test_blob_roundtrip(self):
        import base64
        datos = b"\x89PNG\r\n\x1a\nimagen"
        codificado = _valor_a_json(datos)
        assert set(codificado) == {"__blob__"}
        assert base64.b64decode(codificado["__blob__"]) == datos
        assert _json_a_valor(codificado) == datos

    def test_valores_simples_pasan_sin_cambios(self):
        assert _valor_a_json(5) == 5
        assert _valor_a_json("texto") == "texto"
        assert _valor_a_json(None) is None
        assert _json_a_valor(3.5) == 3.5


# -------------------------------------------------------------- exportar
class TestExportar:
    def test_exporta_y_inspecciona(self, tmp_path):
        ruta = str(tmp_path / "respaldo.json")
        resumen = exportar_conjuntos(["sistema"], ruta)
        assert resumen["filas"] >= 0
        assert "historico_campos" in resumen["tablas"]
        info = inspeccionar_archivo(ruta)
        assert "sistema" in info["conjuntos"]
        assert set(info["conjuntos"]) == {"sistema"}
        assert info["generado"]

    def test_sin_conjuntos_lanza_error(self, tmp_path):
        with pytest.raises(ValueError):
            exportar_conjuntos([], str(tmp_path / "x.json"))

    def test_archivo_invalido_lanza_error(self, tmp_path):
        ruta = tmp_path / "mal.json"
        ruta.write_text("{no es json", encoding="utf-8")
        with pytest.raises(ValueError):
            inspeccionar_archivo(str(ruta))

    def test_json_ajeno_lanza_error(self, tmp_path):
        ruta = tmp_path / "ajeno.json"
        ruta.write_text('{"hola": 1}', encoding="utf-8")
        with pytest.raises(ValueError):
            inspeccionar_archivo(str(ruta))


# -------------------------------------------------------------- importar
class TestImportar:
    def test_roundtrip_agregar_restaura_borrado(self, tmp_path):
        modelo = HistoricoCamposModel()
        modelo.borrar(_CAMPO)
        modelo.registrar(_CAMPO, "VALOR-UNICO-RESPALDO")
        ruta = str(tmp_path / "respaldo.json")
        exportar_conjuntos(["sistema"], ruta)

        modelo.borrar(_CAMPO)
        assert [f["valor"] for f in modelo.listar_por_campo(_CAMPO)] == []

        resumen = importar_conjuntos(ruta, ["sistema"], reemplazar=False)
        assert resumen["importadas"] >= 0
        valores = [f["valor"] for f in modelo.listar_por_campo(_CAMPO)]
        assert "VALOR-UNICO-RESPALDO" in valores

    def test_reemplazar_sustituye_contenido(self, tmp_path):
        modelo = HistoricoCamposModel()
        modelo.borrar(_CAMPO)
        modelo.registrar(_CAMPO, "VIEJO")

        # Archivo artesanal: conjunto propio que solo toca historico_campos
        doc = {
            "aplicacion": "SIAC ERP",
            "version_archivo": 1,
            "generado": "2026-08-24T00:00:00",
            "motor": "sqlite",
            "conjuntos": {"prueba": ["historico_campos"]},
            "datos": {"historico_campos": {
                "columnas": ["campo", "valor", "updated_at"],
                "filas": [
                    [_CAMPO, "NUEVO-1", "2026-08-24 00:00:00"],
                    [_CAMPO, "NUEVO-2", "2026-08-24 00:00:01"],
                ],
            }},
        }
        ruta = tmp_path / "artesanal.json"
        ruta.write_text(json.dumps(doc), encoding="utf-8")

        resumen = importar_conjuntos(str(ruta), ["prueba"], reemplazar=True)
        assert resumen["importadas"] == 2
        valores = [f["valor"] for f in modelo.listar_por_campo(_CAMPO)]
        # listar_por_campo ordena por updated_at descendente
        assert sorted(valores) == ["NUEVO-1", "NUEVO-2"]
        modelo.borrar(_CAMPO)

    def test_agregar_no_duplica(self, tmp_path):
        modelo = HistoricoCamposModel()
        modelo.borrar(_CAMPO)
        modelo.registrar(_CAMPO, "EXISTENTE")
        doc = {
            "aplicacion": "SIAC ERP",
            "version_archivo": 1,
            "generado": "2026-08-24T00:00:00",
            "motor": "sqlite",
            "conjuntos": {"prueba": ["historico_campos"]},
            "datos": {"historico_campos": {
                "columnas": ["campo", "valor", "updated_at"],
                "filas": [[_CAMPO, "EXISTENTE", "2026-08-24 00:00:00"]],
            }},
        }
        ruta = tmp_path / "dup.json"
        ruta.write_text(json.dumps(doc), encoding="utf-8")
        importar_conjuntos(str(ruta), ["prueba"], reemplazar=False)
        valores = [f["valor"] for f in modelo.listar_por_campo(_CAMPO)]
        assert valores.count("EXISTENTE") == 1
        modelo.borrar(_CAMPO)

    def test_tabla_desconocida_se_omite_con_error(self, tmp_path):
        doc = {
            "aplicacion": "SIAC ERP",
            "version_archivo": 1,
            "generado": "2026-08-24T00:00:00",
            "motor": "sqlite",
            "conjuntos": {"prueba": ["tabla_inexistente_xyz"]},
            "datos": {"tabla_inexistente_xyz": {
                "columnas": ["id"], "filas": [[1]]}},
        }
        ruta = tmp_path / "desconocida.json"
        ruta.write_text(json.dumps(doc), encoding="utf-8")
        resumen = importar_conjuntos(str(ruta), ["prueba"], reemplazar=False)
        assert resumen["importadas"] == 0
        assert any("tabla_inexistente_xyz" in e for e in resumen["errores"])

    def test_columna_inyectada_se_filtra(self, tmp_path):
        modelo = HistoricoCamposModel()
        modelo.borrar(_CAMPO)
        doc = {
            "aplicacion": "SIAC ERP",
            "version_archivo": 1,
            "generado": "2026-08-24T00:00:00",
            "motor": "sqlite",
            "conjuntos": {"prueba": ["historico_campos"]},
            "datos": {"historico_campos": {
                "columnas": ["campo", "valor", "campo; DROP TABLE usuarios--"],
                "filas": [[_CAMPO, "X", None]],
            }},
        }
        ruta = tmp_path / "inyeccion.json"
        ruta.write_text(json.dumps(doc), encoding="utf-8")
        resumen = importar_conjuntos(str(ruta), ["prueba"], reemplazar=False)
        assert resumen["importadas"] == 1
        valores = [f["valor"] for f in modelo.listar_por_campo(_CAMPO)]
        assert valores == ["X"]
        modelo.borrar(_CAMPO)

    def test_conjunto_ausente_en_archivo_lanza_error(self, tmp_path):
        ruta = tmp_path / "vacio.json"
        ruta.write_text(json.dumps({
            "aplicacion": "SIAC ERP", "version_archivo": 1,
            "generado": "2026-08-24T00:00:00", "motor": "sqlite",
            "conjuntos": {}, "datos": {}}), encoding="utf-8")
        with pytest.raises(ValueError):
            importar_conjuntos(str(ruta), ["clientes"], reemplazar=False)
