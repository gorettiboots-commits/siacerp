"""Modelo de la ficha técnica por modelo ("Hoja de especificación de diseño").

La ficha técnica consolida en una fila por modelo las características de
diseño del calzado (materiales de corte, bordados, suela, empaque, etc.)
tal como se capturan en la plantilla `Ficha tecnica.xlsx`. Además guarda
las fotos de las piezas (producto terminado, tubo, chinela, talón, suela).
"""
from typing import Any

from src.database.db_manager import DatabaseManager

# Campos de característica de la ficha (etiqueta visible, columna).
# El orden define el orden de aparición en el diálogo y el PDF.
CAMPOS_FICHA: list[tuple[str, str]] = [
    ("Cintilla", "cintilla"),
    ("Carnuza (Chinela)", "carnuza_chinela"),
    ("Forro", "forro"),
    ("Piel-Corte 1", "piel_corte_1"),
    ("Piel-Corte 2", "piel_corte_2"),
    ("Piel-Corte 3", "piel_corte_3"),
    ("Piel-Corte 4", "piel_corte_4"),
    ("Entretela Tubo", "entretela_tubo"),
    ("Entretela Chinela", "entretela_chinela"),
    ("Entretela Talón", "entretela_talon"),
    ("Rebajado Tubo", "rebajado_tubo"),
    ("Rebajado Chinela", "rebajado_chinela"),
    ("Rebajado Talón", "rebajado_talon"),
    ("Bordado Tubo", "bordado_tubo"),
    ("Bordado Chinela", "bordado_chinela"),
    ("Bordado Calzador", "bordado_calzador"),
    ("Bordado Oreja", "bordado_oreja"),
    ("Bordado Logo", "bordado_logo"),
    ("Hilo de Bordado Tubo", "hilo_bordado_tubo"),
    ("Hilo de Bordado Chinela", "hilo_bordado_chinela"),
    ("Hilo de Bordado Calzador", "hilo_bordado_calzador"),
    ("Hilo de Bordado Oreja", "hilo_bordado_oreja"),
    ("Hilo de Logo", "hilo_logo"),
    ("Hilo de Armado", "hilo_armado"),
    ("Hilo de Sobrecostura", "hilo_sobrecostura"),
    ("Vivo", "vivo"),
    ("Ribete", "ribete"),
    ("Estoperol", "estoperol"),
    ("Herraje", "herraje"),
    ("ACC 1", "acc_1"),
    ("ACC 2", "acc_2"),
    ("ACC 3", "acc_3"),
    ("ACC 4", "acc_4"),
    ("Puntera", "puntera"),
    ("Planta", "planta"),
    ("Contrafuerte", "contrafuerte"),
    ("Casco", "casco"),
    ("Suela", "suela"),
    ("Cambrellón", "cambrellon"),
    ("Cerco", "cerco"),
    ("Herradura", "herradura"),
    ("Landis", "landis"),
    ("Espinazo", "espinazo"),
    ("Firme", "firme"),
    ("Tacón", "tacon"),
    ("Stein", "stein"),
    ("Acabado", "acabado"),
    ("Cierre", "cierre"),
    ("Cantos", "cantos"),
    ("Plantilla", "plantilla"),
    ("Transfer", "transfer"),
    ("Caja", "caja"),
    ("Serigrafía", "serigrafia"),
    ("Bolsa", "bolsa"),
    ("Soporte", "soporte"),
    ("Asadera", "asadera"),
    ("Papel Relleno", "papel_relleno"),
    ("Colgante", "colgante"),
    ("Grabado de Suela", "grabado_suela"),
    ("Barranca", "barranca"),
]

CAMPOS_ENCABEZADO: list[tuple[str, str]] = [
    ("Proyecto", "proyecto"),
    ("Etapa", "etapa"),
    ("ID de Diseño", "id_diseno"),
    ("Ref. Cliente", "ref_cliente"),
    ("Color / Nombre", "color_nombre"),
]

TIPOS_FOTO: list[tuple[str, str]] = [
    ("Producto terminado", "producto"),
    ("Tubo", "tubo"),
    ("Chinela", "chinela"),
    ("Talón", "talon"),
    ("Suela", "suela"),
]


class FichaTecnicaModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def _columnas_caracteristica(self) -> list[str]:
        return [col for _, col in CAMPOS_FICHA]

    def obtener(self, modelo_id: int) -> dict | None:
        """Ficha del modelo con sus campos de característica (sin fotos)."""
        return self.db.fetch_one(
            "SELECT * FROM fichas_tecnicas WHERE modelo_id = ?", (modelo_id,))

    def obtener_fotos(self, modelo_id: int) -> dict[str, bytes | None]:
        """Devuelve {tipo_foto: imagen_blob} para el modelo."""
        filas = self.db.fetch_all(
            "SELECT tipo_foto, imagen FROM ficha_tecnica_fotos WHERE modelo_id = ?",
            (modelo_id,))
        return {f["tipo_foto"]: f["imagen"] for f in filas}

    def obtener_foto(self, modelo_id: int, tipo_foto: str) -> bytes | None:
        fila = self.db.fetch_one(
            "SELECT imagen FROM ficha_tecnica_fotos WHERE modelo_id = ? AND tipo_foto = ?",
            (modelo_id, tipo_foto))
        return fila["imagen"] if fila else None

    def guardar(self, modelo_id: int, datos: dict) -> None:
        """Inserta o actualiza la ficha del modelo.

        `datos` contiene las columnas de la tabla (encabezado + característica).
        """
        existente = self.db.fetch_one(
            "SELECT modelo_id FROM fichas_tecnicas WHERE modelo_id = ?",
            (modelo_id,))
        if existente:
            columnas = self._columnas_datos(datos)
            asignaciones = ", ".join(f"{c} = ?" for c in columnas)
            valores = [datos.get(c, "") for c in columnas]
            self.db.execute(
                f"UPDATE fichas_tecnicas SET {asignaciones}, "
                "updated_at = datetime('now') WHERE modelo_id = ?",
                (*valores, modelo_id))
        else:
            columnas = self._columnas_datos(datos)
            nombres = ", ".join(columnas)
            marcadores = ", ".join("?" for _ in columnas)
            valores = [datos.get(c, "") for c in columnas]
            self.db.execute(
                f"INSERT INTO fichas_tecnicas (modelo_id, {nombres}) "
                f"VALUES (?, {marcadores})",
                (modelo_id, *valores))

    def _columnas_datos(self, datos: dict) -> list[str]:
        permitidas = (
            [c for _, c in CAMPOS_ENCABEZADO]
            + self._columnas_caracteristica()
            + ["comentarios", "realizo", "recibio"]
        )
        return [c for c in permitidas if c in datos]

    def valores_historicos(self, columna: str) -> list[str]:
        """Valores distintos no vacíos que otros modelos tienen en *columna*.

        Sirve como autocompletado contextual: muestra textos que el usuario
        ya capturó previamente en la misma campo de otra ficha.
        """
        if columna not in self._columnas_caracteristica():
            return []
        filas = self.db.fetch_all(
            f"SELECT DISTINCT {columna} FROM fichas_tecnicas "
            f"WHERE {columna} != '' AND {columna} IS NOT NULL "
            f"ORDER BY {columna}",
        )
        return [f[columna] for f in filas]

    def insumos_activos(self) -> list[dict]:
        """Catálogo de insumos activos para poblar los combos."""
        return self.db.fetch_all(
            "SELECT id, codigo, nombre, categoria "
            "FROM insumos WHERE activo = 1 ORDER BY nombre")

    def guardar_foto(self, modelo_id: int, tipo_foto: str,
                     imagen: bytes | None) -> None:
        """Guarda o reemplaza la foto de un tipo (o la borra si es None)."""
        if imagen is None:
            self.db.execute(
                "DELETE FROM ficha_tecnica_fotos WHERE modelo_id = ? AND tipo_foto = ?",
                (modelo_id, tipo_foto))
            return
        self.db.execute(
            "INSERT INTO ficha_tecnica_fotos (modelo_id, tipo_foto, imagen) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(modelo_id, tipo_foto) DO UPDATE SET imagen = excluded.imagen",
            (modelo_id, tipo_foto, imagen))
