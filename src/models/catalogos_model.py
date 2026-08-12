from src.database.db_manager import DatabaseManager


class TallasModel:
    """Catálogo unificado de tallas/puntos (RD-1).

    Un solo catálogo configurable, sin campo `orden`: el orden se deriva del
    valor numérico. La generación en serie crea la "corrida" de tallas
    (de X a Y, en pasos de medio punto).
    """

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM tallas_catalogo"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY CAST(talla AS REAL), talla"
        return self.db.fetch_all(query)

    def crear(self, talla: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO tallas_catalogo (talla) VALUES (?)",
            (talla,),
        )
        return cursor.lastrowid

    def actualizar(self, talla_id: int, talla: str) -> None:
        self.db.execute(
            "UPDATE tallas_catalogo SET talla=? WHERE id=?",
            (talla, talla_id),
        )

    def desactivar(self, talla_id: int) -> None:
        self.db.execute(
            "UPDATE tallas_catalogo SET activo=0 WHERE id=?", (talla_id,)
        )

    def activar(self, talla_id: int) -> None:
        self.db.execute(
            "UPDATE tallas_catalogo SET activo=1 WHERE id=?", (talla_id,)
        )

    def vaciar(self) -> int:
        cursor = self.db.execute("DELETE FROM tallas_catalogo")
        return cursor.rowcount

    def generar(self, desde: float, hasta: float) -> int:
        if desde > hasta:
            desde, hasta = hasta, desde
        existentes = {r["talla"] for r in
                      self.db.fetch_all("SELECT talla FROM tallas_catalogo")}
        creados = 0
        for i in range(int(desde * 2), int(hasta * 2) + 1):
            valor = i / 2
            talla = self._formatear_talla(valor)
            if talla not in existentes:
                self.db.execute(
                    "INSERT INTO tallas_catalogo (talla) VALUES (?)",
                    (talla,),
                )
                creados += 1
            else:
                self.db.execute(
                    "UPDATE tallas_catalogo SET activo=1 WHERE talla=?",
                    (talla,),
                )
        return creados

    @staticmethod
    def _formatear_talla(valor: float) -> str:
        entero = int(valor)
        if valor == entero:
            return f"{entero:02d}"
        return f"{entero:02d}.5"


class ColoresModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM colores_catalogo"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY orden, nombre"
        return self.db.fetch_all(query)

    def crear(self, nombre: str, codigo: str, orden: int) -> int:
        cursor = self.db.execute(
            "INSERT INTO colores_catalogo (nombre, codigo, orden) VALUES (?, ?, ?)",
            (nombre, codigo, orden),
        )
        return cursor.lastrowid

    def actualizar(self, color_id: int, nombre: str, codigo: str, orden: int) -> None:
        self.db.execute(
            "UPDATE colores_catalogo SET nombre=?, codigo=?, orden=? WHERE id=?",
            (nombre, codigo, orden, color_id),
        )

    def desactivar(self, color_id: int) -> None:
        self.db.execute(
            "UPDATE colores_catalogo SET activo=0 WHERE id=?", (color_id,)
        )
