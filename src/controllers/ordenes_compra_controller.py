from src.models.orden_compra_model import (
    OrdenCompraModel, ProveedorInsumosModel, ProveedorModel, UnidadesMedidaModel,
)
from src.models.inventario_model import InsumoModel


class OrdenesCompraController:
    def __init__(self) -> None:
        self.proveedor_model = ProveedorModel()
        self.oc_model = OrdenCompraModel()
        self.insumo_model = InsumoModel()
        self.prov_insumo_model = ProveedorInsumosModel()
        self.unidades_model = UnidadesMedidaModel()

    def listar_unidades(self, solo_activos: bool = True) -> list[dict]:
        return self.unidades_model.listar(solo_activos)

    def crear_unidad(self, nombre: str, abreviatura: str) -> int:
        return self.unidades_model.crear(nombre, abreviatura)

    def actualizar_unidad(self, unidad_id: int, nombre: str, abreviatura: str) -> None:
        self.unidades_model.actualizar(unidad_id, nombre, abreviatura)

    def desactivar_unidad(self, unidad_id: int) -> None:
        self.unidades_model.desactivar(unidad_id)

    def listar_insumos_proveedor(self, proveedor_id: int) -> list[dict]:
        return self.prov_insumo_model.listar(proveedor_id)

    def listar_insumos_proveedor_por_insumo(self, insumo_id: int) -> list[dict]:
        return self.prov_insumo_model.listar_por_insumo(insumo_id)

    def guardar_insumos_proveedor(self, proveedor_id: int, items: list[dict]) -> None:
        self.prov_insumo_model.guardar(proveedor_id, items)

    def listar_proveedores(self) -> list[dict]:
        return self.proveedor_model.listar()

    def buscar_proveedores(self, termino: str) -> list[dict]:
        return self.proveedor_model.buscar(termino)

    def obtener_proveedor(self, proveedor_id: int) -> dict | None:
        return self.proveedor_model.obtener(proveedor_id)

    def crear_proveedor(self, rfc: str, nombre: str, telefono: str = "",
                        email: str = "", direccion: str = "",
                        nombre_comercial: str = "") -> int:
        return self.proveedor_model.crear(rfc, nombre, telefono, email, direccion,
                                          nombre_comercial)

    def actualizar_proveedor(self, proveedor_id: int, rfc: str, nombre: str,
                             telefono: str, email: str, direccion: str,
                             nombre_comercial: str = "") -> None:
        self.proveedor_model.actualizar(proveedor_id, rfc, nombre, telefono, email,
                                        direccion, nombre_comercial)

    def desactivar_proveedor(self, proveedor_id: int) -> None:
        self.proveedor_model.desactivar(proveedor_id)

    def listar_ordenes(self) -> list[dict]:
        return self.oc_model.listar()

    def buscar_ordenes(self, termino: str) -> list[dict]:
        return self.oc_model.buscar(termino)

    def obtener_orden(self, oc_id: int) -> dict | None:
        return self.oc_model.obtener(oc_id)

    def folio_existe(self, folio: str) -> bool:
        return self.oc_model.folio_existe(folio)

    def obtener_detalle_orden(self, oc_id: int) -> list[dict]:
        return self.oc_model.obtener_detalle(oc_id)

    def listar_tallas(self) -> list[dict]:
        return self.oc_model.listar_tallas()

    def crear_orden(self, folio: str, detalle: list[dict] | None = None,
                    observaciones: str = "", proveedor_id: int | None = None,
                    metodo_pago: str = "Transferencia bancaria",
                    solo_remision: bool = False, tipo: str = "orden") -> int:
        oc_id = self.oc_model.crear(folio, observaciones, proveedor_id,
                                    metodo_pago, solo_remision, tipo)
        if detalle:
            for d in detalle:
                self.oc_model.agregar_detalle(
                    oc_id, d["insumo_id"], d["cantidad"], d["precio"],
                    d.get("proveedor_id", proveedor_id),
                    d.get("tallas"),
                )
        total = sum(d["cantidad"] * d["precio"] for d in (detalle or []))
        self.oc_model.db.execute(
            "UPDATE ordenes_compra SET total=? WHERE id=?", (total, oc_id)
        )
        return oc_id

    def cancelar_orden(self, oc_id: int) -> None:
        self.oc_model.cancelar(oc_id)

    def recibir_orden(self, oc_id: int) -> None:
        self.oc_model.recibir(oc_id)
