from datetime import date, datetime, timedelta
from typing import Optional

from src.database.db_manager import DatabaseManager


_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo",
    6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre",
    11: "Noviembre", 12: "Diciembre",
}


def _lunes(d: date) -> date:
    return d - timedelta(days=d.weekday())


class ProgramacionModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    # ---- Semanas ----

    def asegurar_semanas(self) -> None:
        """Genera las semanas faltantes desde la última existente hasta fin
        de año (lunes a sábado). Idempotente."""
        fila = self.db.fetch_one(
            "SELECT MAX(fecha_inicio) AS f, MAX(orden) AS o "
            "FROM programacion_semana WHERE activo = 1")
        ultimo = None
        orden_max = 0
        if fila and fila["f"]:
            try:
                ultimo = datetime.strptime(fila["f"], "%Y-%m-%d").date()
            except (TypeError, ValueError):
                ultimo = None
            orden_max = int(fila["o"] or 0)
        hoy = date.today()
        inicio = _lunes(hoy)
        if ultimo:
            inicio = max(inicio, _lunes(ultimo) + timedelta(days=7))
        fin_anio = date(hoy.year, 12, 31)
        k = 0
        while inicio <= fin_anio:
            fin = inicio + timedelta(days=5)
            if fin.month == inicio.month:
                nombre = (f"{inicio.day:02d}-{fin.day:02d} "
                          f"{_MESES[inicio.month]} {inicio.year}")
            else:
                nombre = (f"{inicio.day:02d} {_MESES[inicio.month]} "
                          f"{inicio.year} - {fin.day:02d} "
                          f"{_MESES[fin.month]} {fin.year}")
            self.db.execute(
                "INSERT INTO programacion_semana (nombre, fecha_inicio, orden) "
                "VALUES (?, ?, ?)",
                (nombre, inicio.isoformat(), orden_max + k + 1))
            inicio += timedelta(days=7)
            k += 1

    def listar_semanas(self) -> list[dict]:
        self.asegurar_semanas()
        return self.db.fetch_all(
            "SELECT * FROM programacion_semana WHERE activo = 1 "
            "ORDER BY fecha_inicio, orden")

    def obtener_semana(self, semana_id: int) -> Optional[dict]:
        return self.db.fetch_one(
            "SELECT * FROM programacion_semana WHERE id = ?", (semana_id,))

    def total_semanas(self) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM programacion_semana WHERE activo = 1")
        return int(row["n"]) if row else 0

    # ---- Líneas ----

    def listar_lineas(self, semana_id: int | None, termino: str = "",
                      estatus: str = "", folio_pedido: str = "") -> list[dict]:
        """Lista líneas; semana_id=None devuelve todas las semanas del año."""
        query = (
            "SELECT pl.*, s.nombre AS semana "
            "FROM programacion_lineas pl "
            "JOIN programacion_semana s ON s.id = pl.semana_id"
        )
        condiciones: list[str] = []
        params: list = []
        if semana_id:
            condiciones.append("pl.semana_id = ?")
            params.append(semana_id)
        if termino:
            q = "%" + termino + "%"
            condiciones.append(
                "(pl.cliente LIKE ? OR pl.modelo LIKE ? "
                "OR pl.folio_prog LIKE ? OR pl.piel LIKE ? OR pl.color LIKE ?)")
            params += [q, q, q, q, q]
        if folio_pedido:
            q = "%" + folio_pedido + "%"
            condiciones.append("pl.folio_pedido LIKE ?")
            params.append(q)
        if estatus:
            condiciones.append("pl.estatus = ?")
            params.append(estatus)
        if condiciones:
            query += " WHERE " + " AND ".join(condiciones)
        query += " ORDER BY s.fecha_inicio, s.orden, pl.orden, pl.id"
        return self.db.fetch_all(query, tuple(params))

    def obtener_linea(self, linea_id: int) -> Optional[dict]:
        return self.db.fetch_one(
            "SELECT * FROM programacion_lineas WHERE id = ?", (linea_id,))

    def buscar_linea_por_folio(self, folio: str) -> Optional[dict]:
        return self.db.fetch_one(
            "SELECT * FROM programacion_lineas WHERE folio_prog = ?",
            (folio.strip(),))

    def obtener_linea_con_tallas(self, linea_id: int) -> Optional[dict]:
        linea = self.db.fetch_one(
            "SELECT pl.*, p.suela, p.observaciones "
            "FROM programacion_lineas pl "
            "LEFT JOIN pedidos_cliente p ON p.id = pl.pedido_id "
            "WHERE pl.id = ?",
            (linea_id,))
        if not linea:
            return None
        linea["tallas"] = self.db.fetch_all(
            "SELECT talla, pares FROM programacion_linea_tallas "
            "WHERE linea_id = ? ORDER BY orden", (linea_id,))
        return linea

    def cambiar_estatus(self, linea_id: int, estatus: str) -> None:
        self.db.execute(
            "UPDATE programacion_lineas SET estatus = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (estatus, linea_id),
        )

    def asignar_folio_prog(self, linea_id: int, folio_prog: str) -> None:
        self.db.execute(
            "UPDATE programacion_lineas SET folio_prog = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (folio_prog.strip(), linea_id),
        )

    def asignar_folio_pedido(self, linea_id: int, folio_pedido: str) -> None:
        self.db.execute(
            "UPDATE programacion_lineas SET folio_pedido = ?, "
            "updated_at = datetime('now') WHERE id = ?",
            (folio_pedido.strip(), linea_id),
        )

    def eliminar_linea(self, linea_id: int) -> None:
        self.db.execute(
            "DELETE FROM programacion_linea_tallas WHERE linea_id = ?",
            (linea_id,))
        self.db.execute(
            "DELETE FROM programacion_lineas WHERE id = ?", (linea_id,))

    # ---- Programación desde pedidos ----

    def siguiente_folio_prog(self) -> str:
        """Devuelve el siguiente folio de programación numérico (1001, 1002, ...)."""
        filas = self.db.fetch_all("SELECT folio_prog FROM programacion_lineas")
        maximo = 0
        for f in filas:
            v = f["folio_prog"]
            if v and str(v).isdigit():
                maximo = max(maximo, int(v))
        return str(maximo + 1)

    def suma_pares_pedido(self, pedido_id: int) -> int:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(total_pares), 0) AS n "
            "FROM programacion_lineas WHERE pedido_id = ?", (pedido_id,))
        return int(row["n"]) if row else 0

    def pares_programados_detalle(self, detalle_id: int) -> int:
        row = self.db.fetch_one(
            "SELECT COALESCE(SUM(total_pares), 0) AS n "
            "FROM programacion_lineas WHERE detalle_pedido_id = ?", (detalle_id,))
        return int(row["n"]) if row else 0

    def pares_programados_por_talla(self, detalle_id: int) -> dict[str, int]:
        filas = self.db.fetch_all(
            """SELECT lt.talla, COALESCE(SUM(lt.pares), 0) AS n
               FROM programacion_linea_tallas lt
               JOIN programacion_lineas pl ON pl.id = lt.linea_id
               WHERE pl.detalle_pedido_id = ?
               GROUP BY lt.talla""", (detalle_id,))
        return {f["talla"]: int(f["n"]) for f in filas}

    def crear_linea(self, semana_id: int, folio_prog: str, pedido_id: int,
                    detalle_pedido_id: int, folio_pedido: str, cliente: str,
                    modelo: str, piel: str, color: str, fecha_prog: str,
                    tallas: list[dict], total_pares: int) -> int:
        orden = 0
        row = self.db.fetch_one(
            "SELECT COALESCE(MAX(orden), 0) AS n "
            "FROM programacion_lineas WHERE semana_id = ?", (semana_id,))
        if row:
            orden = int(row["n"]) + 1
        cur = self.db.execute(
            """INSERT INTO programacion_lineas
               (semana_id, orden, folio_prog, folio_pedido, cliente, modelo,
                piel, color, fecha_prog, total_pares, estatus, pedido_id,
                detalle_pedido_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'programacion_incompleta',
                       ?, ?)""",
            (semana_id, orden, folio_prog, folio_pedido, cliente, modelo,
             piel, color, fecha_prog, total_pares, pedido_id, detalle_pedido_id))
        linea_id = cur.lastrowid
        for t in tallas:
            self.db.execute(
                """INSERT INTO programacion_linea_tallas (linea_id, talla, orden, pares)
                   VALUES (?, ?, ?, ?)""",
                (linea_id, t["talla"], float(t["talla"]), t["pares"]))
        return linea_id

    def sincronizar_estatus_pedido(self, pedido_id: int,
                                   total_pedido: int) -> str:
        """Si el pedido quedó cubierto, todas sus líneas pasan a 'programado';
        en otro caso quedan como 'programacion_incompleta'."""
        programado = self.suma_pares_pedido(pedido_id)
        nuevo = "programado" if programado >= total_pedido else "programacion_incompleta"
        self.db.execute(
            "UPDATE programacion_lineas SET estatus = ?, "
            "updated_at = datetime('now') WHERE pedido_id = ?",
            (nuevo, pedido_id))
        return nuevo

    def folios_pedido_semana(self, semana_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT folio_pedido, COUNT(*) AS lineas,
                      COALESCE(SUM(total_pares), 0) AS pares
               FROM programacion_lineas
               WHERE semana_id = ? AND folio_pedido != ''
               GROUP BY folio_pedido
               ORDER BY folio_pedido""",
            (semana_id,),
        )

    # ---- Tallas ----

    def lineas_con_tallas(self, semana_id: int | None, termino: str = "",
                          estatus: str = "", folio_pedido: str = "") -> list[dict]:
        lineas = self.listar_lineas(semana_id, termino, estatus, folio_pedido)
        if not lineas:
            return lineas
        ids = ",".join(str(l["id"]) for l in lineas)
        rows = self.db.fetch_all(
            f"""SELECT lt.linea_id, lt.talla, lt.pares
                FROM programacion_linea_tallas lt
                WHERE lt.linea_id IN ({ids})
                ORDER BY lt.orden"""
        )
        por_linea: dict[int, list[dict]] = {}
        for r in rows:
            por_linea.setdefault(r["linea_id"], []).append(
                {"talla": r["talla"], "pares": r["pares"]})
        for l in lineas:
            l["tallas"] = por_linea.get(l["id"], [])
        return lineas

    def tallas_semana(self, semana_id: int | None) -> list[dict]:
        where = "WHERE pl.semana_id = ?" if semana_id else ""
        params = (semana_id,) if semana_id else ()
        return self.db.fetch_all(
            f"""SELECT lt.talla, MIN(lt.orden) AS orden
               FROM programacion_linea_tallas lt
               JOIN programacion_lineas pl ON pl.id = lt.linea_id
               {where}
               GROUP BY lt.talla
               ORDER BY orden""",
            params,
        )

    def totales_semana(self, semana_id: int | None) -> dict:
        where = "WHERE semana_id = ?" if semana_id else ""
        params = (semana_id,) if semana_id else ()
        row = self.db.fetch_one(
            f"""SELECT COUNT(*) AS lineas,
                      COALESCE(SUM(total_pares), 0) AS pares,
                      COUNT(DISTINCT cliente) AS clientes
               FROM programacion_lineas
               {where}""",
            params,
        )
        return {
            "lineas": int(row["lineas"]) if row else 0,
            "pares": int(row["pares"]) if row else 0,
            "clientes": int(row["clientes"]) if row else 0,
        }
