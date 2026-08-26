"""Modelo del Dashboard del sistema.

Consolida indicadores clave de los módulos (órdenes de compra, producción,
inventario, producto terminado y clientes) en consultas agregadas de solo
lectura. Compatible con SQLite y PostgreSQL: solo SQL estándar y placeholders,
sin funciones propias de un motor.
"""
from datetime import datetime

from src.database.db_manager import DatabaseManager


class DashboardModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    # ------------------------------------------------------------------
    # Indicadores clave
    # ------------------------------------------------------------------

    def obtener_resumen(self) -> dict:
        """Conteos e importes clave de todo el sistema en una sola pasada."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        mes = datetime.now().strftime("%Y-%m")

        def uno(sql: str, params: tuple = ()) -> float:
            fila = self.db.fetch_one(sql, params)
            return list(fila.values())[0] if fila else 0

        return {
            "oc_pendientes": uno(
                "SELECT COUNT(*) FROM ordenes_compra WHERE estatus = 'pendiente'"),
            "oc_mes": uno(
                "SELECT COUNT(*) FROM ordenes_compra "
                "WHERE substr(fecha_emision, 1, 7) = ?", (mes,)),
            "oc_importe_mes": uno(
                "SELECT COALESCE(SUM(total), 0) FROM ordenes_compra "
                "WHERE substr(fecha_emision, 1, 7) = ?", (mes,)),
            "op_planeadas": uno(
                "SELECT COUNT(*) FROM ordenes_produccion WHERE estatus = 'planeada'"),
            "op_produccion": uno(
                "SELECT COUNT(*) FROM ordenes_produccion WHERE estatus = 'en_produccion'"),
            "op_terminadas_mes": uno(
                "SELECT COUNT(*) FROM ordenes_produccion WHERE estatus = 'terminada' "
                "AND substr(fecha_entrega, 1, 7) = ?", (mes,)),
            "insumos_bajo_stock": uno(
                "SELECT COUNT(*) FROM insumos "
                "WHERE activo = 1 AND stock_actual <= stock_minimo"),
            "modelos_activos": uno(
                "SELECT COUNT(*) FROM modelos WHERE activo = 1"),
            "pares_pt": uno(
                "SELECT COALESCE(SUM(pares), 0) FROM inventario_pt"),
            "clientes_activos": uno(
                "SELECT COUNT(*) FROM clientes WHERE activo = 1"),
            "movimientos_hoy": uno(
                "SELECT COUNT(*) FROM movimiento_inventario "
                "WHERE substr(created_at, 1, 10) = ?", (hoy,)),
        }

    # ------------------------------------------------------------------
    # Detalles para las tablas del dashboard
    # ------------------------------------------------------------------

    def obtener_ultimas_oc(self, limite: int = 8) -> list[dict]:
        return self.db.fetch_all(
            """SELECT oc.folio, oc.estatus, oc.tipo, oc.total, oc.fecha_emision,
                      p.nombre AS proveedor_nombre
               FROM ordenes_compra oc
               LEFT JOIN proveedores p ON p.id = oc.proveedor_id
               ORDER BY oc.id DESC LIMIT ?""",
            (limite,))

    def obtener_ops_en_curso(self, limite: int = 8) -> list[dict]:
        return self.db.fetch_all(
            """SELECT op.folio, op.estatus, op.prioridad, op.total_pares,
                      op.fecha_entrega, v.codigo_variante,
                      m.nombre AS modelo_nombre
               FROM ordenes_produccion op
               LEFT JOIN variantes v ON v.id = op.variante_id
               LEFT JOIN modelos m ON m.id = v.modelo_id
               WHERE op.estatus != 'terminada'
               ORDER BY op.fecha_entrega ASC LIMIT ?""",
            (limite,))

    def obtener_stock_bajo(self, limite: int = 10) -> list[dict]:
        return self.db.fetch_all(
            """SELECT codigo, nombre, stock_actual, stock_minimo, unidad_medida
               FROM insumos
               WHERE activo = 1 AND stock_actual <= stock_minimo
               ORDER BY (stock_actual - stock_minimo) ASC LIMIT ?""",
            (limite,))

    def obtener_movimientos_recientes(self, limite: int = 10) -> list[dict]:
        return self.db.fetch_all(
            """SELECT m.created_at, m.tipo_movimiento, m.cantidad,
                      i.nombre AS insumo_nombre, i.unidad_medida
               FROM movimiento_inventario m
               JOIN insumos i ON i.id = m.insumo_id
               ORDER BY m.id DESC LIMIT ?""",
            (limite,))

    def obtener_compras_por_mes(self, meses: int = 6) -> list[dict]:
        """Total de compras por mes (últimos *meses* con actividad)."""
        filas = self.db.fetch_all(
            """SELECT substr(fecha_emision, 1, 7) AS mes,
                      SUM(total) AS total
               FROM ordenes_compra
               GROUP BY substr(fecha_emision, 1, 7)
               ORDER BY mes DESC LIMIT ?""",
            (meses,))
        return list(reversed(filas))
