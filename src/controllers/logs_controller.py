from src.database.db_manager import DatabaseManager
from src.utils.logs import limpiar_logs


class LogsController:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar_logs(self, filtros: dict | None = None) -> list[dict]:
        where = []
        params: list = []
        filtros = filtros or {}

        termino = (filtros.get("termino") or "").strip()
        if termino:
            where.append(
                "(usuario LIKE ? OR modulo LIKE ? OR accion LIKE ? "
                "OR entidad LIKE ? OR detalle LIKE ? OR datos LIKE ?)")
            p = f"%{termino}%"
            params += [p, p, p, p, p, p]

        modulo = filtros.get("modulo")
        if modulo:
            where.append("modulo = ?")
            params.append(modulo)

        accion = filtros.get("accion")
        if accion:
            where.append("accion = ?")
            params.append(accion)

        nivel = filtros.get("nivel")
        if nivel:
            where.append("nivel = ?")
            params.append(nivel)

        usuario = filtros.get("usuario")
        if usuario:
            where.append("usuario_id = ?")
            params.append(usuario)

        desde = filtros.get("desde")
        if desde:
            where.append("fecha >= ?")
            params.append(f"{desde} 00:00:00")

        hasta = filtros.get("hasta")
        if hasta:
            where.append("fecha <= ?")
            params.append(f"{hasta} 23:59:59")

        sql = "SELECT * FROM logs_sistema"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT 2000"
        return self.db.fetch_all(sql, tuple(params))

    def modulos_registrados(self) -> list[str]:
        rows = self.db.fetch_all(
            "SELECT DISTINCT modulo FROM logs_sistema ORDER BY modulo")
        return [r["modulo"] for r in rows]

    def acciones_registradas(self, modulo: str | None = None) -> list[str]:
        if modulo:
            rows = self.db.fetch_all(
                "SELECT DISTINCT accion FROM logs_sistema WHERE modulo = ? ORDER BY accion",
                (modulo,))
        else:
            rows = self.db.fetch_all(
                "SELECT DISTINCT accion FROM logs_sistema ORDER BY accion")
        return [r["accion"] for r in rows]

    def usuarios_registrados(self) -> list[dict]:
        return self.db.fetch_all(
            "SELECT DISTINCT usuario_id, usuario FROM logs_sistema "
            "WHERE usuario_id IS NOT NULL ORDER BY usuario")

    def limpiar(self) -> int:
        return limpiar_logs()
