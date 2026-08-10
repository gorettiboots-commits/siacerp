from src.models.clientes_model import ClienteModel, PedidoClienteModel
from src.utils.folios import siguiente_folio


class ClientesController:
    def __init__(self) -> None:
        self.cliente_model = ClienteModel()
        self.pedido_model = PedidoClienteModel()

    # ---- Clientes ----

    def listar_clientes(self, solo_activos: bool = True) -> list[dict]:
        return self.cliente_model.listar(solo_activos)

    def buscar_clientes(self, termino: str) -> list[dict]:
        return self.cliente_model.buscar(termino)

    def obtener_cliente(self, cliente_id: int) -> dict | None:
        return self.cliente_model.obtener(cliente_id)

    def crear_cliente(self, nombre: str, rfc: str = "", nombre_comercial: str = "",
                      telefono: str = "", email: str = "", direccion: str = "") -> int:
        return self.cliente_model.crear(nombre, rfc, nombre_comercial,
                                        telefono, email, direccion)

    def actualizar_cliente(self, cliente_id: int, nombre: str, rfc: str = "",
                           nombre_comercial: str = "", telefono: str = "",
                           email: str = "", direccion: str = "") -> None:
        self.cliente_model.actualizar(cliente_id, nombre, rfc, nombre_comercial,
                                      telefono, email, direccion)

    def desactivar_cliente(self, cliente_id: int) -> None:
        self.cliente_model.desactivar(cliente_id)

    def reactivar_cliente(self, cliente_id: int) -> None:
        self.cliente_model.reactivar(cliente_id)

    # ---- Pedidos de cliente ----

    def listar_pedidos(self, cliente_id: int | None = None) -> list[dict]:
        return self.pedido_model.listar(cliente_id)

    def buscar_pedidos(self, termino: str,
                       cliente_id: int | None = None) -> list[dict]:
        return self.pedido_model.buscar(termino, cliente_id)

    def obtener_pedido(self, pedido_id: int) -> dict | None:
        return self.pedido_model.obtener(pedido_id)

    def obtener_detalle_pedido(self, pedido_id: int) -> list[dict]:
        return self.pedido_model.obtener_detalle(pedido_id)

    def listar_puntos(self) -> list[dict]:
        return self.pedido_model.listar_puntos()

    def siguiente_folio(self) -> str:
        return siguiente_folio("pedidos_cliente", "folio", "PED")

    def _total_pares(self, detalle: list[dict]) -> int:
        return sum(
            int(p.get("pares", 0) or 0)
            for d in detalle for p in (d.get("puntos") or [])
        )

    def crear_pedido(self, folio: str, cliente_id: int, fecha_pedido: str,
                     fecha_programado: str = "", estatus: str = "pendiente",
                     observaciones: str = "", detalle: list[dict] | None = None) -> int:
        pedido_id = self.pedido_model.crear(
            folio, cliente_id, fecha_pedido, fecha_programado, estatus, observaciones)
        self._guardar_detalle(pedido_id, detalle or [])
        return pedido_id

    def actualizar_pedido(self, pedido_id: int, cliente_id: int, fecha_pedido: str,
                          fecha_programado: str = "", estatus: str = "pendiente",
                          observaciones: str = "", detalle: list[dict] | None = None) -> None:
        self.pedido_model.actualizar(
            pedido_id, cliente_id, fecha_pedido, fecha_programado, estatus, observaciones)
        self.pedido_model.db.execute(
            "DELETE FROM detalle_pedido_cliente WHERE pedido_id = ?", (pedido_id,))
        self._guardar_detalle(pedido_id, detalle or [])

    def _guardar_detalle(self, pedido_id: int, detalle: list[dict]) -> None:
        total = 0
        for d in detalle:
            self.pedido_model.agregar_detalle(
                pedido_id, d["modelo"], d.get("piel", ""), d.get("color", ""),
                d.get("puntos"),
            )
            total += self._total_pares([d])
        self.pedido_model.db.execute(
            "UPDATE pedidos_cliente SET total_pares=? WHERE id=?", (total, pedido_id))

    def cambiar_estatus(self, pedido_id: int, estatus: str) -> None:
        self.pedido_model.cambiar_estatus(pedido_id, estatus)

    def cancelar_pedido(self, pedido_id: int) -> None:
        self.pedido_model.cancelar(pedido_id)
