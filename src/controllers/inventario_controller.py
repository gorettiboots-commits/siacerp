from src.models.catalogos_model import ColoresModel, TallasModel
from src.models.ficha_tecnica_model import FichaTecnicaModel
from src.models.inventario_model import (
    InsumoModel, ListaMaterialesModel, MovimientoInventarioModel,
)
from src.models.movimiento_inventario_model import MovimientoInventarioGrupoModel
from src.models.orden_compra_model import UnidadesMedidaModel
from src.utils.folios import siguiente_folio
from src.utils.logs import registrar_log


class InventarioController:
    def __init__(self) -> None:
        self.insumo_model = InsumoModel()
        self.bom_model = ListaMaterialesModel()
        self.mov_model = MovimientoInventarioModel()
        self.mov_grupo_model = MovimientoInventarioGrupoModel()
        self.unidades_model = UnidadesMedidaModel()
        self.tallas_model = TallasModel()
        self.colores_model = ColoresModel()
        self.ficha_model = FichaTecnicaModel()

    def existe_codigo_insumo(self, codigo: str) -> bool:
        return self.insumo_model.existe_codigo(codigo)

    def listar_tallas(self, solo_activos: bool = True) -> list[dict]:
        return self.tallas_model.listar(solo_activos)

    def crear_talla(self, talla: str) -> int:
        talla_id = self.tallas_model.crear(talla)
        registrar_log("configuracion", "crear", "talla", talla_id,
                      datos={"talla": talla})
        return talla_id

    def actualizar_talla(self, talla_id: int, talla: str) -> None:
        self.tallas_model.actualizar(talla_id, talla)
        registrar_log("configuracion", "editar", "talla", talla_id,
                      datos={"talla": talla})

    def desactivar_talla(self, talla_id: int) -> None:
        self.tallas_model.desactivar(talla_id)
        registrar_log("configuracion", "eliminar", "talla", talla_id)

    def activar_talla(self, talla_id: int) -> None:
        self.tallas_model.activar(talla_id)
        registrar_log("configuracion", "activar", "talla", talla_id)

    def vaciar_tallas(self) -> int:
        eliminados = self.tallas_model.vaciar()
        registrar_log("configuracion", "eliminar", "tallas", None,
                      datos={"eliminados": eliminados})
        return eliminados

    def generar_tallas(self, desde: float, hasta: float) -> int:
        creadas = self.tallas_model.generar(desde, hasta)
        registrar_log("configuracion", "crear", "tallas", None,
                      datos={"desde": desde, "hasta": hasta, "creadas": creadas})
        return creadas


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

    def listar_kardex(self, insumo_id: int) -> list[dict]:
        """Movimientos del insumo con saldo acumulado para el kardex."""
        movimientos = self.mov_model.listar_kardex(insumo_id)
        saldo = 0.0
        for m in movimientos:
            signo = m.get("cantidad", 0) if m.get("tipo_movimiento") == "entrada" else -m.get("cantidad", 0)
            saldo += signo
            m["entrada"] = m.get("cantidad", 0) if m.get("tipo_movimiento") == "entrada" else 0
            m["salida"] = m.get("cantidad", 0) if m.get("tipo_movimiento") != "entrada" else 0
            m["saldo"] = round(saldo, 4)
        return movimientos

    def obtener_ficha(self, modelo_id: int) -> dict | None:
        return self.ficha_model.obtener(modelo_id)

    def guardar_ficha(self, modelo_id: int, datos: dict) -> None:
        self.ficha_model.guardar(modelo_id, datos)
        registrar_log("inventario", "editar", "ficha_tecnica", modelo_id,
                      datos={"modelo_id": modelo_id})

    def obtener_foto_ficha(self, modelo_id: int, tipo_foto: str) -> bytes | None:
        return self.ficha_model.obtener_foto(modelo_id, tipo_foto)

    def guardar_foto_ficha(self, modelo_id: int, tipo_foto: str,
                           imagen: bytes | None) -> None:
        self.ficha_model.guardar_foto(modelo_id, tipo_foto, imagen)
        registrar_log("inventario", "editar", "foto_ficha", modelo_id,
                       datos={"modelo_id": modelo_id, "tipo_foto": tipo_foto,
                              "imagen": bool(imagen)})

    def valores_historicos_ficha(self, columna: str) -> list[str]:
        """Valores ya capturados en *columna* por otros modelos."""
        return self.ficha_model.valores_historicos(columna)

    def insumos_activos(self) -> list[dict]:
        """Catálogo de insumos activos."""
        return self.ficha_model.insumos_activos()

    def agregar_insumo_a_lista(self, modelo_id: int, insumo_id: int) -> bool:
        """Agrega insumo a la lista de materiales del modelo si no existía.

        Registra con cantidad_por_par = 0 (se ajusta después desde BOM).
        Devuelve True si insertó, False si ya existía la relación.
        """
        resultado = self.bom_model.agregar(modelo_id, insumo_id)
        if resultado:
            registrar_log("inventario", "crear", "lista_materiales", insumo_id,
                           datos={"modelo_id": modelo_id, "insumo_id": insumo_id})
        return resultado

    # ------------------------------------------------------------------
    # Movimientos de inventario multi-partida
    # ------------------------------------------------------------------

    def registrar_movimiento_grupo(self, tipo: str, observaciones: str,
                                   partidas: list[dict]) -> int:
        """Registra un grupo de movimientos multi-partida.

        Valida stock, genera folio, guarda header + detail, inserta filas
        en ``movimiento_inventario`` (kardex) y actualiza stock de cada
        insumo.

        Parameters
        ----------
        tipo : str
            'salida' o 'cambio_ubicacion'.
        observaciones : str
            Observaciones generales del movimiento.
        partidas : list[dict]
            Cada dict: ``{insumo_id, cantidad, observaciones?}``.

        Returns
        -------
        int
            ID del grupo creado.
        """
        if not partidas:
            raise ValueError("Debe agregar al menos una partida.")
        for p in partidas:
            cant = float(p.get('cantidad', 0) or 0)
            if cant <= 0:
                raise ValueError("Cada partida debe tener cantidad mayor a 0.")
            if tipo == 'salida':
                ins = self.insumo_model.obtener(p['insumo_id'])
                if ins and ins.get('stock_actual', 0) < cant:
                    raise ValueError(
                        f"Stock insuficiente para '{ins.get('nombre', '')}': "
                        f"disponible {ins['stock_actual']}, solicitado {cant}.")

        folio = siguiente_folio('movimientos_inventario', 'folio', 'MVI')
        mov_id = self.mov_grupo_model.registrar_grupo(
            folio, tipo, observaciones, partidas)

        for p in partidas:
            cant = float(p.get('cantidad', 0) or 0)
            self.mov_model.registrar(
                p['insumo_id'], tipo, cant,
                ref_tipo='movimiento', ref_id=mov_id,
                obs=folio,
            )
            self.insumo_model.actualizar_stock(p['insumo_id'], -cant)

        registrar_log("inventario", "movimiento_grupo", "movimiento",
                      mov_id, datos={
                          "folio": folio, "tipo": tipo,
                          "partidas": len(partidas),
                          "observaciones": observaciones})
        return mov_id

    def obtener_grupo_movimiento(self, movimiento_id: int) -> dict | None:
        """Obtiene un grupo de movimientos con su detalle."""
        return self.mov_grupo_model.obtener_grupo(movimiento_id)

    def listar_grupos_movimientos(self, limite: int = 200) -> list[dict]:
        """Lista grupos de movimientos (más recientes primero)."""
        return self.mov_grupo_model.listar_grupos(limite)
