from typing import Optional
from src.database.db_manager import DatabaseManager


class InsumoModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM insumos"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre"
        return self.db.fetch_all(query)

    def buscar(self, termino: str) -> list[dict]:
        q = "%" + termino + "%"
        return self.db.fetch_all(
            "SELECT * FROM insumos WHERE activo = 1 AND (codigo LIKE ? OR nombre LIKE ? OR categoria LIKE ?) ORDER BY nombre",
            (q, q, q),
        )

    def obtener(self, insumo_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM insumos WHERE id = ?", (insumo_id,))

    def existe_codigo(self, codigo: str) -> bool:
        row = self.db.fetch_one("SELECT id FROM insumos WHERE codigo = ?", (codigo,))
        return row is not None

    def crear(self, codigo: str, nombre: str, categoria: str, unidad: str = "pieza",
              stock_minimo: float = 0) -> int:
        cursor = self.db.execute(
            "INSERT INTO insumos (codigo, nombre, categoria, unidad_medida, stock_minimo) VALUES (?, ?, ?, ?, ?)",
            (codigo, nombre, categoria, unidad, stock_minimo),
        )
        return cursor.lastrowid

    def actualizar(self, insumo_id: int, codigo: str, nombre: str, categoria: str,
                    unidad: str, stock_minimo: float) -> None:
        self.db.execute(
            "UPDATE insumos SET codigo=?, nombre=?, categoria=?, unidad_medida=?, stock_minimo=?, updated_at=datetime('now') WHERE id=?",
            (codigo, nombre, categoria, unidad, stock_minimo, insumo_id),
        )

    def desactivar(self, insumo_id: int) -> None:
        self.db.execute("UPDATE insumos SET activo=0, updated_at=datetime('now') WHERE id=?", (insumo_id,))

    def actualizar_stock(self, insumo_id: int, cantidad: float) -> None:
        self.db.execute(
            "UPDATE insumos SET stock_actual = stock_actual + ?, updated_at = datetime('now') WHERE id = ?",
            (cantidad, insumo_id),
        )

    def stock_bajo(self) -> list[dict]:
        return self.db.fetch_all(
            "SELECT * FROM insumos WHERE activo = 1 AND stock_actual <= stock_minimo ORDER BY (stock_minimo - stock_actual) DESC"
        )

    def listar_de_proveedor(self, proveedor_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT i.* FROM proveedor_insumos pi
               JOIN insumos i ON i.id = pi.insumo_id
               WHERE pi.proveedor_id = ? AND pi.activo = 1 AND i.activo = 1
               ORDER BY i.nombre""",
            (proveedor_id,),
        )

    def listar_sin_proveedor(self) -> list[dict]:
        return self.db.fetch_all(
            """SELECT * FROM insumos WHERE activo = 1
               AND NOT EXISTS (SELECT 1 FROM proveedor_insumos pi WHERE pi.insumo_id = insumos.id)
               ORDER BY nombre"""
        )


class ListaMaterialesModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def obtener_por_modelo(self, modelo_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT lm.*, i.nombre as insumo_nombre, i.unidad_medida
               FROM lista_materiales lm
               JOIN insumos i ON i.id = lm.insumo_id
               WHERE lm.modelo_id = ?""",
            (modelo_id,),
        )


class MovimientoInventarioModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, insumo_id: Optional[int] = None) -> list[dict]:
        if insumo_id:
            return self.db.fetch_all(
                "SELECT m.*, i.nombre as insumo_nombre FROM movimiento_inventario m JOIN insumos i ON i.id = m.insumo_id WHERE m.insumo_id = ? ORDER BY m.created_at DESC",
                (insumo_id,),
            )
        return self.db.fetch_all(
            "SELECT m.*, i.nombre as insumo_nombre FROM movimiento_inventario m JOIN insumos i ON i.id = m.insumo_id ORDER BY m.created_at DESC LIMIT 500"
        )

    def registrar(self, insumo_id: int, tipo: str, cantidad: float,
                  ref_tipo: Optional[str] = None, ref_id: Optional[int] = None,
                  obs: str = "") -> int:
        cursor = self.db.execute(
            "INSERT INTO movimiento_inventario (insumo_id, tipo_movimiento, cantidad, referencia_tipo, referencia_id, observaciones) VALUES (?, ?, ?, ?, ?, ?)",
            (insumo_id, tipo, cantidad, ref_tipo, ref_id, obs),
        )
        return cursor.lastrowid
