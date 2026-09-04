from datetime import date, datetime, timedelta

from src.models.clientes_model import PedidoClienteModel
from src.models.produccion_model import OrdenProduccionModel
from src.models.programacion_model import ProgramacionModel
from src.utils.folios import siguiente_folio
from src.utils.logs import registrar_log


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

    def asignar_folio_prog(self, linea_id: int, folio_prog: str) -> None:
        self.model.asignar_folio_prog(linea_id, folio_prog)

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
        """Crea un folio de programación por modelo y genera OP automáticamente."""
        folios: list[str] = []
        ops_generadas: list[int] = []
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

            # ── Generar Orden de Producción automáticamente ──
            op_id = self._crear_op_desde_corrida(
                c, tallas, total, fecha_prog, folio_pedido, cliente)
            if op_id:
                ops_generadas.append(op_id)

        if folios:
            self.model.sincronizar_estatus_pedido(pedido_id, total_pedido)
            self.pedido_model.cambiar_estatus(pedido_id, "programado")

        if ops_generadas:
            registrar_log(
                "produccion", "crear_desde_programacion", "orden_produccion",
                None, datos={"ops": ops_generadas, "folios_prog": folios})

        return folios

    def _crear_op_desde_corrida(self, corrida: dict, tallas: list[dict],
                                total_pares: int, fecha_prog: str,
                                folio_pedido: str, cliente: str) -> int | None:
        """Crea una orden de producción a partir de una corrida programada.

        Returns:
            ID de la OP creada o None si no se pudo crear.
        """
        modelo = corrida.get("modelo", "")
        color = corrida.get("color", "")
        piel = corrida.get("piel", "")

        # Buscar o crear la variante base
        variante_id = self.model.crear_variante_si_no_existe(modelo, color, piel)
        if not variante_id:
            # Si el modelo no existe, no se puede crear la OP
            return None

        # Generar folio OP
        folio_op = siguiente_folio("ordenes_produccion", "folio", "OP")

        # Construir matriz de tallas para la OP
        matriz_tallas = []
        for t in tallas:
            talla_id = self.model.buscar_talla_id(t["talla"])
            if talla_id and int(t["pares"] or 0) > 0:
                matriz_tallas.append({
                    "talla_id": talla_id,
                    "pares": int(t["pares"]),
                })

        if not matriz_tallas:
            return None

        # Crear la OP usando el model directamente
        op_model = OrdenProduccionModel()
        op_id = op_model.crear(
            folio=folio_op,
            variante_id=variante_id,
            total_pares=total_pares,
            fecha_inicio=fecha_prog,
            fecha_entrega="",
            prioridad="normal",
            observaciones=f"Generada desde programación {corrida.get('modelo', '')} "
                          f"- Pedido: {folio_pedido} - Cliente: {cliente}",
        )

        # Agregar tallas a la OP
        for m in matriz_tallas:
            op_model.agregar_talla(op_id, m["talla_id"], m["pares"])

        return op_id
