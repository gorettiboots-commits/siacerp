from src.models.catalogos_model import ColoresModel, PuntosModel
from src.models.inventario_model import (
    InsumoModel, ListaMaterialesModel, MovimientoInventarioModel,
)
from src.models.orden_compra_model import UnidadesMedidaModel
from src.utils.logs import registrar_log


class InventarioController:
    def __init__(self) -> None:
        self.insumo_model = InsumoModel()
        self.bom_model = ListaMaterialesModel()
        self.mov_model = MovimientoInventarioModel()
        self.unidades_model = UnidadesMedidaModel()
        self.puntos_model = PuntosModel()
        self.colores_model = ColoresModel()

    def existe_codigo_insumo(self, codigo: str) -> bool:
        return self.insumo_model.existe_codigo(codigo)

    def listar_puntos(self, solo_activos: bool = True) -> list[dict]:
        return self.puntos_model.listar(solo_activos)

    def crear_punto(self, punto: str, orden: int) -> int:
        punto_id = self.puntos_model.crear(punto, orden)
        registrar_log("configuracion", "crear", "punto", punto_id,
                      datos={"punto": punto, "orden": orden})
        return punto_id

    def actualizar_punto(self, punto_id: int, punto: str, orden: int) -> None:
        self.puntos_model.actualizar(punto_id, punto, orden)
        registrar_log("configuracion", "editar", "punto", punto_id,
                      datos={"punto": punto, "orden": orden})

    def desactivar_punto(self, punto_id: int) -> None:
        self.puntos_model.desactivar(punto_id)
        registrar_log("configuracion", "eliminar", "punto", punto_id)

    def activar_punto(self, punto_id: int) -> None:
        self.puntos_model.activar(punto_id)
        registrar_log("configuracion", "activar", "punto", punto_id)

    def vaciar_puntos(self) -> int:
        eliminados = self.puntos_model.vaciar()
        registrar_log("configuracion", "eliminar", "puntos", None,
                      datos={"eliminados": eliminados})
        return eliminados

    def generar_puntos(self, desde: float, hasta: float) -> int:
        creados = self.puntos_model.generar(desde, hasta)
        registrar_log("configuracion", "crear", "puntos", None,
                      datos={"desde": desde, "hasta": hasta, "creados": creados})
        return creados

    def listar_colores(self, solo_activos: bool = True) -> list[dict]:
        return self.colores_model.listar(solo_activos)

    def crear_color(self, nombre: str, codigo: str, orden: int) -> int:
        color_id = self.colores_model.crear(nombre, codigo, orden)
        registrar_log("configuracion", "crear", "color", color_id,
                      datos={"nombre": nombre, "codigo": codigo, "orden": orden})
        return color_id

    def actualizar_color(self, color_id: int, nombre: str, codigo: str, orden: int) -> None:
        self.colores_model.actualizar(color_id, nombre, codigo, orden)
        registrar_log("configuracion", "editar", "color", color_id,
                      datos={"nombre": nombre, "codigo": codigo, "orden": orden})

    def desactivar_color(self, color_id: int) -> None:
        self.colores_model.desactivar(color_id)
        registrar_log("configuracion", "eliminar", "color", color_id)

    def listar_unidades(self) -> list[dict]:
        return self.unidades_model.listar()

    def listar_insumos(self) -> list[dict]:
        return self.insumo_model.listar()

    def listar_categorias(self, excluir_id: int | None = None) -> list[str]:
        return self.insumo_model.listar_categorias(excluir_id)

    def buscar_insumos_por_nombre(self, nombre: str, excluir_id: int | None = None) -> list[dict]:
        return self.insumo_model.buscar_por_nombre(nombre, excluir_id)

    def buscar_insumos(self, termino: str) -> list[dict]:
        return self.insumo_model.buscar(termino)

    def obtener_insumo(self, insumo_id: int) -> dict | None:
        return self.insumo_model.obtener(insumo_id)

    def obtener_imagen_insumo(self, insumo_id: int) -> bytes | None:
        return self.insumo_model.obtener_imagen(insumo_id)

    def crear_insumo(self, codigo: str, nombre: str, categoria: str,
                     unidad: str = "pieza", stock_minimo: float = 0,
                     imagen: bytes | None = None) -> int:
        insumo_id = self.insumo_model.crear(codigo, nombre, categoria, unidad, stock_minimo, imagen)
        registrar_log("inventario", "crear", "insumo", insumo_id,
                      datos={"codigo": codigo, "nombre": nombre, "categoria": categoria,
                             "unidad": unidad, "stock_minimo": stock_minimo,
                             "imagen": bool(imagen)})
        return insumo_id

    def actualizar_insumo(self, insumo_id: int, codigo: str, nombre: str,
                           categoria: str, unidad: str, stock_minimo: float,
                           imagen: bytes | None = None) -> None:
        self.insumo_model.actualizar(insumo_id, codigo, nombre, categoria, unidad, stock_minimo, imagen)
        registrar_log("inventario", "editar", "insumo", insumo_id,
                      datos={"codigo": codigo, "nombre": nombre, "categoria": categoria,
                             "unidad": unidad, "stock_minimo": stock_minimo,
                             "imagen": bool(imagen)})

    def desactivar_insumo(self, insumo_id: int) -> None:
        self.insumo_model.desactivar(insumo_id)
        registrar_log("inventario", "eliminar", "insumo", insumo_id)

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
        registrar_log("inventario", "movimiento", "insumo", insumo_id,
                      datos={"tipo": tipo, "cantidad": cantidad, "signo_stock": signo,
                             "referencia_tipo": ref_tipo, "referencia_id": ref_id,
                             "observaciones": obs})
        return result
