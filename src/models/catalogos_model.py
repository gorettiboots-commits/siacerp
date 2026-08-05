from src.database.db_manager import DatabaseManager


class PuntosModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM puntos_catalogo"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY orden"
        return self.db.fetch_all(query)

    def crear(self, punto: str, orden: int) -> int:
        cursor = self.db.execute(
            "INSERT INTO puntos_catalogo (punto, orden) VALUES (?, ?)",
            (punto, orden),
        )
        return cursor.lastrowid

    def actualizar(self, punto_id: int, punto: str, orden: int) -> None:
        self.db.execute(
            "UPDATE puntos_catalogo SET punto=?, orden=? WHERE id=?",
            (punto, orden, punto_id),
        )

    def desactivar(self, punto_id: int) -> None:
        self.db.execute(
            "UPDATE puntos_catalogo SET activo=0 WHERE id=?", (punto_id,)
        )

    def activar(self, punto_id: int) -> None:
        self.db.execute(
            "UPDATE puntos_catalogo SET activo=1 WHERE id=?", (punto_id,)
        )

    def vaciar(self) -> int:
        cursor = self.db.execute("DELETE FROM puntos_catalogo")
        return cursor.rowcount

    def generar(self, desde: int, hasta: int) -> int:
        if desde > hasta:
            desde, hasta = hasta, desde
        existentes = {r["punto"] for r in self.db.fetch_all("SELECT punto FROM puntos_catalogo")}
        creados = 0
        for n in range(desde, hasta + 1):
            punto = f"{n:02d}"
            if punto not in existentes:
                self.db.execute(
                    "INSERT INTO puntos_catalogo (punto, orden) VALUES (?, ?)",
                    (punto, n + 1),
                )
                creados += 1
            else:
                self.db.execute(
                    "UPDATE puntos_catalogo SET activo=1, orden=? WHERE punto=?",
                    (n + 1, punto),
                )
        return creados


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
