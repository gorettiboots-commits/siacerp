from src.models.catalogos_model import ColoresModel, TallasModel
from src.models.inventario_model import (
    InsumoModel, ListaMaterialesModel, MovimientoInventarioModel,
)
from src.models.orden_compra_model import UnidadesMedidaModel


class InventarioController:
    def __init__(self) -> None:
        self.insumo_model = InsumoModel()
        self.bom_model = ListaMaterialesModel()
        self.mov_model = MovimientoInventarioModel()
        self.unidades_model = UnidadesMedidaModel()
        self.tallas_model = TallasModel()
        self.colores_model = ColoresModel()

    def existe_codigo_insumo(self, codigo: str) -> bool:
        return self.insumo_model.existe_codigo(codigo)

    def listar_tallas(self, solo_activos: bool = True) -> list[dict]:
        return self.tallas_model.listar(solo_activos)

    def crear_talla(self, talla: str) -> int:
        return self.tallas_model.crear(talla)

    def actualizar_talla(self, talla_id: int, talla: str) -> None:
        self.tallas_model.actualizar(talla_id, talla)

    def desactivar_talla(self, talla_id: int) -> None:
        self.tallas_model.desactivar(talla_id)

    def activar_talla(self, talla_id: int) -> None:
        self.tallas_model.activar(talla_id)

    def vaciar_tallas(self) -> int:
        return self.tallas_model.vaciar()

    def generar_tallas(self, desde: float, hasta: float) -> int:
        return self.tallas_model.generar(desde, hasta)

    def listar_colores(self, solo_activos: bool = True) -> list[dict]:
        return self.colores_model.listar(solo_activos)

    def crear_color(self, nombre: str, codigo: str, orden: int) -> int:
        return self.colores_model.crear(nombre, codigo, orden)

    def actualizar_color(self, color_id: int, nombre: str, codigo: str, orden: int) -> None:
        self.colores_model.actualizar(color_id, nombre, codigo, orden)

    def desactivar_color(self, color_id: int) -> None:
        self.colores_model.desactivar(color_id)

    def listar_unidades(self) -> list[dict]:
        return self.unidades_model.listar()

    def listar_insumos(self) -> list[dict]:
        return self.insumo_model.listar()

    def buscar_insumos(self, termino: str) -> list[dict]:
        return self.insumo_model.buscar(termino)

    def obtener_insumo(self, insumo_id: int) -> dict | None:
        return self.insumo_model.obtener(insumo_id)

    def obtener_imagen_insumo(self, insumo_id: int) -> bytes | None:
        return self.insumo_model.obtener_imagen(insumo_id)

    def crear_insumo(self, codigo: str, nombre: str, categoria: str,
                     unidad: str = "pieza", stock_minimo: float = 0,
                     imagen: bytes | None = None) -> int:
        return self.insumo_model.crear(codigo, nombre, categoria, unidad, stock_minimo, imagen)

    def actualizar_insumo(self, insumo_id: int, codigo: str, nombre: str,
                           categoria: str, unidad: str, stock_minimo: float,
                           imagen: bytes | None = None) -> None:
        self.insumo_model.actualizar(insumo_id, codigo, nombre, categoria, unidad, stock_minimo, imagen)

    def desactivar_insumo(self, insumo_id: int) -> None:
        self.insumo_model.desactivar(insumo_id)

    def stock_bajo(self) -> list[dict]:
        return self.insumo_model.stock_bajo()

    def listar_insumos_de_proveedor(self, proveedor_id: int) -> list[dict]:
        return self.insumo_model.listar_de_proveedor(proveedor_id)

    def listar_insumos_sin_proveedor(self) -> list[dict]:
        return self.insumo_model.listar_sin_proveedor()

    def obtener_bom(self, modelo_id: int) -> list[dict]:
        return self.bom_model.obtener_por_modelo(modelo_id)

    def listar_movimientos(self, insumo_id: int | None = None) -> list[dict]:
        return self.mov_model.listar(insumo_id)

    def registrar_movimiento(self, insumo_id: int, tipo: str, cantidad: float,
                              ref_tipo: str | None = None, ref_id: int | None = None,
                              obs: str = "") -> int:
        result = self.mov_model.registrar(insumo_id, tipo, cantidad, ref_tipo, ref_id, obs)
        signo = cantidad if tipo == "entrada" else -cantidad
        self.insumo_model.actualizar_stock(insumo_id, signo)
        return result
