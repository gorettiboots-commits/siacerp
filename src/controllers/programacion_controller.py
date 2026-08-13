from datetime import date, datetime, timedelta

from src.models.clientes_model import PedidoClienteModel
from src.models.programacion_model import ProgramacionModel


class ProgramacionController:
    def __init__(self) -> None:
        self.model = ProgramacionModel()
        self.pedido_model = PedidoClienteModel()

    def listar_semanas(self) -> list[dict]:
        return self.model.listar_semanas()

    def listar_semanas_programar(self) -> list[dict]:
        """Semana actual y semanas restantes del año."""
        semanas = self.model.listar_semanas()
        if not semanas:
            return semanas
        hoy = date.today()
        for i, s in enumerate(semanas):
            try:
                ini = datetime.strptime(s["fecha_inicio"], "%Y-%m-%d").date()
            except (TypeError, ValueError):
                continue
            if ini <= hoy <= ini + timedelta(days=6):
                return semanas[i:]
        return semanas

    def obtener_semana(self, semana_id: int) -> dict | None:
        return self.model.obtener_semana(semana_id)

    def total_semanas(self) -> int:
        return self.model.total_semanas()

    def listar_lineas(self, semana_id: int, termino: str = "",
                      estatus: str = "", folio_pedido: str = "") -> list[dict]:
        return self.model.listar_lineas(semana_id, termino, estatus, folio_pedido)

    def lineas_con_tallas(self, semana_id: int, termino: str = "",
                          estatus: str = "", folio_pedido: str = "") -> list[dict]:
        return self.model.lineas_con_tallas(semana_id, termino, estatus,
                                            folio_pedido)

    def folios_pedido_semana(self, semana_id: int) -> list[dict]:
        return self.model.folios_pedido_semana(semana_id)

    def asignar_folio_pedido(self, linea_id: int, folio_pedido: str) -> None:
        self.model.asignar_folio_pedido(linea_id, folio_pedido)

    def tallas_semana(self, semana_id: int) -> list[dict]:
        return self.model.tallas_semana(semana_id)

    def totales_semana(self, semana_id: int) -> dict:
        return self.model.totales_semana(semana_id)

    def obtener_linea(self, linea_id: int) -> dict | None:
        return self.model.obtener_linea(linea_id)

    def obtener_linea_con_tallas(self, linea_id: int) -> dict | None:
        return self.model.obtener_linea_con_tallas(linea_id)

    def buscar_linea_por_folio(self, folio: str) -> dict | None:
        return self.model.buscar_linea_por_folio(folio)

    def cambiar_estatus(self, linea_id: int, estatus: str) -> None:
        self.model.cambiar_estatus(linea_id, estatus)

    def eliminar_linea(self, linea_id: int) -> None:
        self.model.eliminar_linea(linea_id)

    # ---- Programación desde pedidos ----

    def siguiente_folio_prog(self) -> str:
        return self.model.siguiente_folio_prog()

    def pares_programados_pedido(self, pedido_id: int) -> int:
        return self.model.suma_pares_pedido(pedido_id)

    def pares_programados_detalle(self, detalle_id: int) -> int:
        return self.model.pares_programados_detalle(detalle_id)

    def pares_programados_por_talla(self, detalle_id: int) -> dict[str, int]:
        return self.model.pares_programados_por_talla(detalle_id)

    def programar_pedido(self, pedido_id: int, folio_pedido: str, cliente: str,
                         total_pedido: int, semana_id: int, fecha_prog: str,
                         corridas: list[dict]) -> list[str]:
        """Crea un folio de programación por modelo; sincroniza el estatus."""
        folios: list[str] = []
        for c in corridas:
            folio = self.model.siguiente_folio_prog()
            tallas = [t for t in c.get("tallas", []) if int(t["pares"] or 0) > 0]
            if not tallas:
                continue
            total = sum(int(t["pares"] or 0) for t in tallas)
            self.model.crear_linea(
                semana_id=semana_id, folio_prog=folio, pedido_id=pedido_id,
                detalle_pedido_id=c["detalle_id"], folio_pedido=folio_pedido,
                cliente=cliente, modelo=c["modelo"], piel=c.get("piel", ""),
                color=c.get("color", ""), fecha_prog=fecha_prog,
                tallas=tallas, total_pares=total)
            folios.append(folio)
        if folios:
            self.model.sincronizar_estatus_pedido(pedido_id, total_pedido)
            self.pedido_model.cambiar_estatus(pedido_id, "programado")
        return folios
