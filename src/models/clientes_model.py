from typing import Optional

from src.database.db_manager import DatabaseManager
from src.utils.empresa_context import donde_empresa, parametros_empresa


class ClienteModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        where_emp = donde_empresa()
        params = parametros_empresa()
        query = "SELECT * FROM clientes WHERE 1=1"
        if solo_activos:
            query += " AND activo = 1"
        query += where_emp
        query += " ORDER BY nombre"
        return self.db.fetch_all(query, tuple(params))

    def buscar(self, termino: str) -> list[dict]:
        q = "%" + termino + "%"
        where_emp = donde_empresa()
        params: list = [q, q, q] + parametros_empresa()
        return self.db.fetch_all(
            "SELECT * FROM clientes WHERE activo=1 AND "
            "(nombre LIKE ? OR rfc LIKE ? OR nombre_comercial LIKE ?)"
            + where_emp + " ORDER BY nombre",
            tuple(params),
        )

    def obtener(self, cliente_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM clientes WHERE id = ?", (cliente_id,))

    def crear(self, nombre: str, rfc: str = "", nombre_comercial: str = "",
              telefono: str = "", email: str = "", direccion: str = "") -> int:
        cursor = self.db.execute(
            "INSERT INTO clientes (nombre, rfc, nombre_comercial, telefono, email, direccion) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (nombre, rfc, nombre_comercial, telefono, email, direccion),
        )
        return cursor.lastrowid

    def actualizar(self, cliente_id: int, nombre: str, rfc: str = "",
                   nombre_comercial: str = "", telefono: str = "",
                   email: str = "", direccion: str = "") -> None:
        self.db.execute(
            "UPDATE clientes SET nombre=?, rfc=?, nombre_comercial=?, telefono=?, "
            "email=?, direccion=? WHERE id=?",
            (nombre, rfc, nombre_comercial, telefono, email, direccion, cliente_id),
        )

    def desactivar(self, cliente_id: int) -> None:
        self.db.execute("UPDATE clientes SET activo=0 WHERE id=?", (cliente_id,))

    def reactivar(self, cliente_id: int) -> None:
        self.db.execute("UPDATE clientes SET activo=1 WHERE id=?", (cliente_id,))


class PedidoClienteModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, cliente_id: int | None = None) -> list[dict]:
        query = (
            "SELECT pc.*, c.nombre as cliente_nombre "
            "FROM pedidos_cliente pc "
            "JOIN clientes c ON c.id = pc.cliente_id"
        )
        params: list = []
        if cliente_id:
            query += " WHERE pc.cliente_id = ?"
            params.append(cliente_id)
        query += " ORDER BY pc.created_at DESC, pc.id DESC"
        return self.db.fetch_all(query, tuple(params))

    def buscar(self, termino: str, cliente_id: int | None = None) -> list[dict]:
        q = "%" + termino + "%"
        where_emp = donde_empresa('pc')
        query = (
            "SELECT pc.*, c.nombre as cliente_nombre "
            "FROM pedidos_cliente pc "
            "JOIN clientes c ON c.id = pc.cliente_id "
            "WHERE (pc.folio LIKE ? OR c.nombre LIKE ? OR EXISTS ("
            "    SELECT 1 FROM detalle_pedido_cliente d "
            "    WHERE d.pedido_id = pc.id AND d.modelo LIKE ?))"
            + where_emp
        )
        params: list = [q, q, q] + parametros_empresa()
        if cliente_id:
            query += " AND pc.cliente_id = ?"
            params.append(cliente_id)
        query += " ORDER BY pc.created_at DESC, pc.id DESC"
        return self.db.fetch_all(query, tuple(params))

    def obtener(self, pedido_id: int) -> Optional[dict]:
        return self.db.fetch_one(
            """SELECT pc.*, c.nombre as cliente_nombre, c.rfc as cliente_rfc,
                      c.nombre_comercial as cliente_comercial, c.telefono as cliente_telefono,
                      c.email as cliente_email, c.direccion as cliente_direccion
               FROM pedidos_cliente pc
               JOIN clientes c ON c.id = pc.cliente_id
               WHERE pc.id = ?""",
            (pedido_id,),
        )

    def obtener_detalle(self, pedido_id: int) -> list[dict]:
        detalle = self.db.fetch_all(
            "SELECT * FROM detalle_pedido_cliente WHERE pedido_id = ? ORDER BY id",
            (pedido_id,),
        )
        return self._con_puntos(detalle)

    def _con_puntos(self, detalle: list[dict]) -> list[dict]:
        """Adjunta los pares por talla usando el catálogo unificado (RD-1).

        Conserva las claves históricas `punto`/`punto_id` (la talla y su id en
        `tallas_catalogo`) para no romper a los consumidores existentes.
        """
        if not detalle:
            return detalle
        ids = ",".join(str(d["id"]) for d in detalle)
        rows = self.db.fetch_all(
            f"""SELECT dt.detalle_id, dt.pares, t.talla AS punto, t.id AS punto_id
                FROM detalle_pedido_cliente_puntos dt
                JOIN tallas_catalogo t ON t.id = dt.talla_id
                WHERE dt.detalle_id IN ({ids})
                ORDER BY CAST(t.talla AS REAL), t.talla"""
        )
        por_detalle: dict[int, list[dict]] = {}
        for r in rows:
            por_detalle.setdefault(r["detalle_id"], []).append({
                "punto_id": r["punto_id"],
                "punto": r["punto"],
                "pares": r["pares"],
            })
        for d in detalle:
            d["puntos"] = por_detalle.get(d["id"], [])
        return detalle

    def listar_puntos(self) -> list[dict]:
        """Tallas activas del catálogo unificado (alias `punto` = talla)."""
        return self.db.fetch_all(
            "SELECT id, talla AS punto, activo FROM tallas_catalogo "
            "WHERE activo = 1 ORDER BY CAST(talla AS REAL), talla")

    def crear(self, folio: str, cliente_id: int, fecha_pedido: str,
              fecha_programado: str = "", estatus: str = "pendiente",
              observaciones: str = "", folio_pedido: str = "",
              suela: str = "", horma: str = "") -> int:
        cursor = self.db.execute(
            "INSERT INTO pedidos_cliente (folio, folio_pedido, cliente_id, fecha_pedido, "
            "fecha_programado, estatus, suela, horma, observaciones) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (folio, folio_pedido, cliente_id, fecha_pedido, fecha_programado,
             estatus, suela, horma, observaciones),
        )
        return cursor.lastrowid

    def agregar_detalle(self, pedido_id: int, modelo: str, piel: str = "",
                        color: str = "", puntos: list[dict] | None = None) -> int:
        cursor = self.db.execute(
            "INSERT INTO detalle_pedido_cliente (pedido_id, modelo, piel, color) VALUES (?, ?, ?, ?)",
            (pedido_id, modelo, piel, color),
        )
        detalle_id = cursor.lastrowid
        for p in (puntos or []):
            if p.get("pares", 0) > 0:
                self.db.execute(
                    "INSERT OR REPLACE INTO detalle_pedido_cliente_puntos (detalle_id, talla_id, pares) VALUES (?, ?, ?)",
                    (detalle_id, p["punto_id"], p["pares"]),
                )
        return detalle_id

    def actualizar(self, pedido_id: int, cliente_id: int, fecha_pedido: str,
                   fecha_programado: str = "", estatus: str = "pendiente",
                   observaciones: str = "", folio_pedido: str = "",
                   suela: str = "", horma: str = "") -> None:
        self.db.execute(
            "UPDATE pedidos_cliente SET cliente_id=?, fecha_pedido=?, fecha_programado=?, "
            "estatus=?, observaciones=?, folio_pedido=?, suela=?, horma=? WHERE id=?",
            (cliente_id, fecha_pedido, fecha_programado, estatus, observaciones,
             folio_pedido, suela, horma, pedido_id),
        )

    def cambiar_estatus(self, pedido_id: int, estatus: str) -> None:
        self.db.execute(
            "UPDATE pedidos_cliente SET estatus=? WHERE id=?", (estatus, pedido_id)
        )

    def cancelar(self, pedido_id: int) -> None:
        self.db.execute(
            "UPDATE pedidos_cliente SET estatus='cancelado' WHERE id=? AND estatus != 'surtido'",
            (pedido_id,),
        )
