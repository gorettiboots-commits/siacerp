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

    def generar(self, desde: float, hasta: float) -> int:
        if desde > hasta:
            desde, hasta = hasta, desde
        existentes = {r["punto"] for r in self.db.fetch_all("SELECT punto FROM puntos_catalogo")}
        creados = 0
        for i in range(int(desde * 2), int(hasta * 2) + 1):
            valor = i / 2
            punto = self._formatear_punto(valor)
            orden = valor + 1
            if punto not in existentes:
                self.db.execute(
                    "INSERT INTO puntos_catalogo (punto, orden) VALUES (?, ?)",
                    (punto, orden),
                )
                creados += 1
            else:
                self.db.execute(
                    "UPDATE puntos_catalogo SET activo=1, orden=? WHERE punto=?",
                    (orden, punto),
                )
        return creados

    @staticmethod
    def _formatear_punto(valor: float) -> str:
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
