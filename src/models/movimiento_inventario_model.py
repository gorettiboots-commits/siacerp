from typing import Optional
from src.database.db_manager import DatabaseManager
from src.utils.empresa_context import donde_empresa, parametros_empresa


class MovimientoInventarioGrupoModel:
    """Modelo para grupos de movimientos de inventario (multi-partida).

    Cada grupo representa un documento de movimiento (salida o cambio de
    ubicación) que puede contener 1 a N partidas (insumos con cantidades).
    """

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def registrar_grupo(self, folio: str, tipo: str, observaciones: str,
                        partidas: list[dict]) -> int:
        """Registra un grupo de movimientos (header + detalle).

        Parameters
        ----------
        folio : str
            Folio secuencial (MVI-XXXX).
        tipo : str
            'salida' o 'cambio_ubicacion'.
        observaciones : str
            Observaciones generales del movimiento.
        partidas : list[dict]
            Lista de dicts con keys: insumo_id, cantidad, observaciones (opt).

        Returns
        -------
        int
            El ID del grupo creado.
        """
        cursor = self.db.execute(
            "INSERT INTO movimientos_inventario (folio, tipo_movimiento, "
            "observaciones) VALUES (?, ?, ?)",
            (folio, tipo, observaciones),
        )
        mov_id = cursor.lastrowid
        for p in partidas:
            self.db.execute(
                "INSERT INTO detalle_movimiento_inventario "
                "(movimiento_id, insumo_id, cantidad, observaciones) "
                "VALUES (?, ?, ?, ?)",
                (mov_id, p['insumo_id'], p['cantidad'],
                 p.get('observaciones', '')),
            )
        return mov_id

    def obtener_grupo(self, movimiento_id: int) -> Optional[dict]:
        """Retorna header + detalle de un grupo de movimientos."""
        header = self.db.fetch_one(
            "SELECT * FROM movimientos_inventario WHERE id = ?",
            (movimiento_id,),
        )
        if not header:
            return None
        detalle = self.db.fetch_all(
            """SELECT d.*, i.codigo as insumo_codigo,
                      i.nombre as insumo_nombre, i.unidad_medida
               FROM detalle_movimiento_inventario d
               JOIN insumos i ON i.id = d.insumo_id
               WHERE d.movimiento_id = ?
               ORDER BY d.id""",
            (movimiento_id,),
        )
        header['detalle'] = detalle
        return header

    def listar_grupos(self, limite: int = 200) -> list[dict]:
        """Lista grupos de movimientos (más recientes primero)."""
        where_emp = donde_empresa()
        params = parametros_empresa()
        return self.db.fetch_all(
            f"SELECT * FROM movimientos_inventario WHERE 1=1 {where_emp}"
            " ORDER BY created_at DESC LIMIT ?",
            (*params, limite),
        )

    def obtener_por_grupo(self, movimiento_id: int) -> list[dict]:
        """Movimientos del kardex que pertenecen a un grupo."""
        return self.db.fetch_all(
            """SELECT m.*, i.nombre as insumo_nombre
               FROM movimiento_inventario m
               JOIN insumos i ON i.id = m.insumo_id
               WHERE m.referencia_tipo = 'movimiento'
                 AND m.referencia_id = ?
               ORDER BY m.id""",
            (movimiento_id,),
        )
