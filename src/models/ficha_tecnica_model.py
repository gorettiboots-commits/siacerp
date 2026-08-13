"""Modelo de acceso a datos de la ficha técnica (boleto técnico / kardex).

La ficha técnica amplía cada `modelos` con sus boletos técnicos por sección
(CORTE, PESPUNTE & PRELIMINARES, MONTADO/AVÍOS & ACABADO, etc.) sin modificar
`modelos`, `variantes` ni `lista_materiales`. Las imágenes se guardan como
BLOB en la tabla `fichas_tecnicas.imagen`.
"""

from typing import Optional

from src.database.db_manager import DatabaseManager


class FichaTecnicaModel:
    """CRUD de fichas técnicas. Solo SQL (reglas A-02, D-04/D-05)."""

    _COLUMNAS = (
        "id", "modelo_id", "estilo_sistema", "estilo_muestra", "marca",
        "talla", "genero", "horma", "moldura", "construccion", "corrida",
        "scallop", "tacon", "notas", "imagen", "fuente_archivo", "activo",
        "created_at", "updated_at",
    )

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def obtener_por_modelo(self, modelo_id: int) -> Optional[dict]:
        """Devuelve la ficha (encabezado) de un modelo, si existe."""
        return self.db.fetch_one(
            "SELECT * FROM fichas_tecnicas WHERE modelo_id = ? AND activo = 1",
            (modelo_id,),
        )

    def obtener_imagen(self, ficha_id: int) -> Optional[bytes]:
        row = self.db.fetch_one("SELECT imagen FROM fichas_tecnicas WHERE id = ?", (ficha_id,))
        return row["imagen"] if row else None

    def obtener_completa(self, modelo_id: int) -> Optional[dict]:
        """Devuelve la ficha completa: encabezado + secciones + detalle."""
        ficha = self.obtener_por_modelo(modelo_id)
        if not ficha:
            return None
        ficha["secciones"] = self.db.fetch_all(
            "SELECT id, nombre, orden FROM ficha_tecnica_secciones "
            "WHERE ficha_id = ? ORDER BY orden, id",
            (ficha["id"],),
        )
        for sec in ficha["secciones"]:
            sec["detalle"] = self.db.fetch_all(
                "SELECT componente, descripcion, proveedor, comentarios "
                "FROM ficha_tecnica_detalle WHERE seccion_id = ? "
                "ORDER BY orden, id",
                (sec["id"],),
            )
        return ficha

    def eliminar_por_modelo(self, modelo_id: int) -> None:
        """Borra la ficha y sus secciones/detalle (para re-importar limpio)."""
        ficha = self.obtener_por_modelo(modelo_id)
        if not ficha:
            return
        ficha_id = ficha["id"]
        secciones = self.db.fetch_all(
            "SELECT id FROM ficha_tecnica_secciones WHERE ficha_id = ?", (ficha_id,))
        for sec in secciones:
            self.db.execute(
                "DELETE FROM ficha_tecnica_detalle WHERE seccion_id = ?", (sec["id"],))
        self.db.execute(
            "DELETE FROM ficha_tecnica_secciones WHERE ficha_id = ?", (ficha_id,))
        self.db.execute("DELETE FROM fichas_tecnicas WHERE id = ?", (ficha_id,))

    def guardar(
        self,
        modelo_id: int,
        datos: dict,
        secciones: list[dict],
        imagen: Optional[bytes],
        fuente_archivo: str = "",
    ) -> int:
        """Inserta la ficha con sus secciones/detalle. Devuelve `id`."""
        ficha_id = self.db.execute(
            "INSERT INTO fichas_tecnicas ("
            " modelo_id, estilo_sistema, estilo_muestra, marca, talla, genero,"
            " horma, moldura, construccion, corrida, scallop, tacon, notas,"
            " imagen, fuente_archivo)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                modelo_id,
                datos.get("estilo_sistema"),
                datos.get("estilo_muestra"),
                datos.get("marca"),
                datos.get("talla"),
                datos.get("genero"),
                datos.get("horma"),
                datos.get("moldura"),
                datos.get("construccion"),
                datos.get("corrida"),
                datos.get("scallop"),
                datos.get("tacon"),
                datos.get("notas"),
                imagen,
                fuente_archivo,
            ),
        ).lastrowid

        for orden_sec, seccion in enumerate(secciones):
            sec_id = self.db.execute(
                "INSERT INTO ficha_tecnica_secciones (ficha_id, nombre, orden)"
                " VALUES (?,?,?)",
                (ficha_id, seccion.get("nombre", ""), orden_sec + 1),
            ).lastrowid
            for orden_det, fila in enumerate(seccion.get("detalle", [])):
                self.db.execute(
                    "INSERT INTO ficha_tecnica_detalle ("
                    " seccion_id, componente, descripcion, proveedor,"
                    " comentarios, orden) VALUES (?,?,?,?,?,?)",
                    (
                        sec_id,
                        fila.get("componente"),
                        fila.get("descripcion"),
                        fila.get("proveedor"),
                        fila.get("comentarios"),
                        orden_det + 1,
                    ),
                )
        return ficha_id
