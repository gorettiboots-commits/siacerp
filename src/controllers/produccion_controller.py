from src.models.produccion_model import (
    EstacionModel, InventarioPTModel, ListaMaterialesModel, ModeloModel,
    OrdenProduccionModel, VarianteModel,
)
from src.models.orden_compra_model import UnidadesMedidaModel
from src.utils.logs import registrar_log


class ProduccionController:
    def __init__(self) -> None:
        self.modelo_model = ModeloModel()
        self.variante_model = VarianteModel()
        self.op_model = OrdenProduccionModel()
        self.bom_model = ListaMaterialesModel()
        self.pt_model = InventarioPTModel()
        self.estacion_model = EstacionModel()
        self.unidades_model = UnidadesMedidaModel()

    def listar_unidades(self) -> list[dict]:
        return self.unidades_model.listar()

    # -- Áreas / Estaciones de producción --
    def listar_estaciones(self, solo_activos: bool = True) -> list[dict]:
        return self.estacion_model.listar(solo_activos)

    def crear_estacion(self, nombre: str, orden: int, descripcion: str = "") -> int:
        estacion_id = self.estacion_model.crear(nombre, orden, descripcion)
        registrar_log("configuracion", "crear", "estacion", estacion_id,
                      datos={"nombre": nombre, "orden": orden, "descripcion": descripcion})
        return estacion_id

    def actualizar_estacion(self, estacion_id: int, nombre: str, orden: int, descripcion: str) -> None:
        self.estacion_model.actualizar(estacion_id, nombre, orden, descripcion)
        registrar_log("configuracion", "editar", "estacion", estacion_id,
                      datos={"nombre": nombre, "orden": orden, "descripcion": descripcion})

    def desactivar_estacion(self, estacion_id: int) -> None:
        self.estacion_model.desactivar(estacion_id)
        registrar_log("configuracion", "eliminar", "estacion", estacion_id)

    def eliminar_estacion(self, estacion_id: int) -> None:
        self.estacion_model.eliminar(estacion_id)
        registrar_log("configuracion", "eliminar", "estacion", estacion_id)

    def posicion_op(self, op_id: int) -> dict:
        return self.op_model.posicion_actual(op_id)

    def mover_en_kanban(self, op_id: int, target_estacion_id) -> bool:
        ok = self.op_model.mover_en_kanban(op_id, target_estacion_id)
        registrar_log("produccion", "mover", "orden_produccion", op_id,
                      datos={"estacion_destino": target_estacion_id})
        return ok

    # -- Modelos --
    def listar_modelos(self) -> list[dict]:
        return self.modelo_model.listar()

    def buscar_modelos(self, termino: str) -> list[dict]:
        return self.modelo_model.buscar(termino)

    def obtener_modelo(self, modelo_id: int) -> dict | None:
        return self.modelo_model.obtener(modelo_id)

    def obtener_imagen_modelo(self, modelo_id: int) -> bytes | None:
        return self.modelo_model.obtener_imagen(modelo_id)

    def crear_modelo(self, codigo: str, nombre: str, descripcion: str = "",
                     imagen: bytes | None = None) -> int:
        modelo_id = self.modelo_model.crear(codigo, nombre, descripcion, imagen)
        registrar_log("produccion", "crear", "modelo", modelo_id,
                      datos={"codigo": codigo, "nombre": nombre,
                             "descripcion": descripcion, "imagen": bool(imagen)})
        return modelo_id

    def actualizar_modelo(self, modelo_id: int, codigo: str, nombre: str, descripcion: str,
                          imagen: bytes | None = None) -> None:
        self.modelo_model.actualizar(modelo_id, codigo, nombre, descripcion, imagen)
        registrar_log("produccion", "editar", "modelo", modelo_id,
                      datos={"codigo": codigo, "nombre": nombre,
                             "descripcion": descripcion, "imagen": bool(imagen)})

    def desactivar_modelo(self, modelo_id: int) -> None:
        self.modelo_model.desactivar(modelo_id)
        registrar_log("produccion", "eliminar", "modelo", modelo_id)

    # -- Variantes --
    def listar_variantes(self, modelo_id: int | None = None) -> list[dict]:
        return self.variante_model.listar(modelo_id)

    def buscar_variantes(self, termino: str) -> list[dict]:
        return self.variante_model.buscar(termino)

    def obtener_variante(self, variante_id: int) -> dict | None:
        return self.variante_model.obtener(variante_id)

    def existe_codigo_variante(self, codigo_variante: str) -> bool:
        return self.variante_model.existe_codigo(codigo_variante)

    def crear_variante(self, modelo_id: int, color: str, piel: str, talla: str,
                       codigo_variante: str) -> int:
        variante_id = self.variante_model.crear(modelo_id, color, piel, talla, codigo_variante)
        registrar_log("produccion", "crear", "variante", variante_id,
                      datos={"modelo_id": modelo_id, "color": color, "piel": piel,
                             "talla": talla, "codigo_variante": codigo_variante})
        return variante_id

    def actualizar_variante(self, variante_id: int, modelo_id: int, color: str, piel: str,
                            talla: str, codigo_variante: str) -> None:
        self.variante_model.actualizar(variante_id, modelo_id, color, piel, talla, codigo_variante)
        registrar_log("produccion", "editar", "variante", variante_id,
                      datos={"modelo_id": modelo_id, "color": color, "piel": piel,
                             "talla": talla, "codigo_variante": codigo_variante})

    def desactivar_variante(self, variante_id: int) -> None:
        self.variante_model.desactivar(variante_id)
        registrar_log("produccion", "eliminar", "variante", variante_id)

    def listar_tallas(self) -> list[dict]:
        return self.op_model.listar_tallas_corrida()

    # -- BOM (Lista de Materiales) --
    def obtener_bom(self, modelo_id: int) -> list[dict]:
        return self.bom_model.obtener_por_modelo(modelo_id)

    def guardar_bom(self, modelo_id: int, insumos: list[dict]) -> None:
        self.bom_model.guardar(modelo_id, insumos)
        registrar_log("produccion", "editar", "bom", modelo_id, datos={"insumos": insumos})

    # -- Órdenes de Producción --
    def listar_ops(self) -> list[dict]:
        return self.op_model.listar()

    def buscar_ops(self, termino: str) -> list[dict]:
        return self.op_model.buscar(termino)

    def obtener_op(self, op_id: int) -> dict | None:
        return self.op_model.obtener(op_id)

    def obtener_tallas_op(self, op_id: int) -> list[dict]:
        return self.op_model.obtener_tallas(op_id)

    def crear_op(self, folio: str, variante_id: int, matriz_tallas: list[dict],
                 fecha_inicio: str = "", fecha_entrega: str = "",
                 prioridad: str = "normal", observaciones: str = "") -> int:
        total = sum(m["pares"] for m in matriz_tallas)
        op_id = self.op_model.crear(folio, variante_id, total, fecha_inicio,
                                     fecha_entrega, prioridad, observaciones)
        for m in matriz_tallas:
            if m["pares"] > 0:
                self.op_model.agregar_talla(op_id, m["talla_id"], m["pares"])
        registrar_log("produccion", "crear", "orden_produccion", op_id,
                      datos={"folio": folio, "variante_id": variante_id,
                             "total_pares": total, "fecha_inicio": fecha_inicio,
                             "fecha_entrega": fecha_entrega, "prioridad": prioridad,
                             "observaciones": observaciones, "matriz_tallas": matriz_tallas})
        return op_id

    def avanzar_estacion(self, op_id: int, estacion_id: int,
                          pares_procesados: int, pares_defectuosos: int = 0,
                          observaciones: str = "") -> None:
        self.op_model.avanzar_estacion(op_id, estacion_id, pares_procesados,
                                        pares_defectuosos, observaciones)
        registrar_log("produccion", "avanzar", "orden_produccion", op_id,
                      datos={"estacion_id": estacion_id, "pares_procesados": pares_procesados,
                             "pares_defectuosos": pares_defectuosos,
                             "observaciones": observaciones})

    def verificar_materiales(self, variante_id: int, total_pares: int) -> list[dict]:
        return self.op_model.verificar_materiales(variante_id, total_pares)

    def obtener_seguimiento(self, op_id: int) -> list[dict]:
        return self.op_model.obtener_seguimiento(op_id)

    # -- Producto Terminado --
    def listar_pt(self) -> list[dict]:
        return self.pt_model.listar()
