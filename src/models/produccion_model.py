from typing import Optional
from src.database.db_manager import DatabaseManager


class ModeloModel:
    _COLUMNAS = ("id", "codigo", "nombre", "descripcion", "activo",
                 "created_at", "updated_at")

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = f"SELECT {', '.join(self._COLUMNAS)} FROM modelos"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY nombre"
        return self.db.fetch_all(query)

    def buscar(self, termino: str) -> list[dict]:
        q = "%" + termino + "%"
        return self.db.fetch_all(
            f"SELECT {', '.join(self._COLUMNAS)} FROM modelos WHERE activo=1 AND (codigo LIKE ? OR nombre LIKE ?) ORDER BY nombre", (q, q)
        )

    def obtener(self, modelo_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM modelos WHERE id = ?", (modelo_id,))

    def obtener_imagen(self, modelo_id: int) -> Optional[bytes]:
        row = self.db.fetch_one("SELECT imagen FROM modelos WHERE id = ?", (modelo_id,))
        return row["imagen"] if row else None

    def crear(self, codigo: str, nombre: str, descripcion: str = "",
              imagen: Optional[bytes] = None) -> int:
        cursor = self.db.execute(
            "INSERT INTO modelos (codigo, nombre, descripcion, imagen) VALUES (?, ?, ?, ?)",
            (codigo, nombre, descripcion, imagen),
        )
        return cursor.lastrowid

    def actualizar(self, modelo_id: int, codigo: str, nombre: str, descripcion: str,
                   imagen: Optional[bytes] = None) -> None:
        self.db.execute(
            "UPDATE modelos SET codigo=?, nombre=?, descripcion=?, imagen=?, updated_at=datetime('now') WHERE id=?",
            (codigo, nombre, descripcion, imagen, modelo_id),
        )

    def desactivar(self, modelo_id: int) -> None:
        self.db.execute("UPDATE modelos SET activo=0 WHERE id=?", (modelo_id,))


class VarianteModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, modelo_id: Optional[int] = None) -> list[dict]:
        if modelo_id:
            return self.db.fetch_all(
                "SELECT * FROM variantes WHERE modelo_id = ? AND activo = 1 ORDER BY codigo_variante", (modelo_id,)
            )
        return self.db.fetch_all(
            """SELECT v.*, m.nombre as modelo_nombre
               FROM variantes v JOIN modelos m ON m.id = v.modelo_id
               WHERE v.activo = 1 ORDER BY v.codigo_variante"""
        )

    def buscar(self, termino: str) -> list[dict]:
        q = "%" + termino + "%"
        return self.db.fetch_all(
            """SELECT v.*, m.nombre as modelo_nombre
               FROM variantes v JOIN modelos m ON m.id = v.modelo_id
               WHERE v.activo=1 AND (v.codigo_variante LIKE ? OR v.color LIKE ? OR v.piel LIKE ? OR v.talla LIKE ?)
               ORDER BY v.codigo_variante""", (q, q, q, q)
        )

    def obtener(self, variante_id: int) -> Optional[dict]:
        return self.db.fetch_one(
            "SELECT v.*, m.nombre as modelo_nombre FROM variantes v JOIN modelos m ON m.id=v.modelo_id WHERE v.id=?",
            (variante_id,),
        )

    def existe_codigo(self, codigo_variante: str) -> bool:
        row = self.db.fetch_one(
            "SELECT id FROM variantes WHERE codigo_variante = ?", (codigo_variante,))
        return row is not None

    def crear(self, modelo_id: int, color: str, piel: str, talla: str,
              codigo_variante: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO variantes (modelo_id, color, piel, talla, codigo_variante) VALUES (?, ?, ?, ?, ?)",
            (modelo_id, color, piel, talla, codigo_variante),
        )
        return cursor.lastrowid

    def actualizar(self, variante_id: int, modelo_id: int, color: str, piel: str,
                   talla: str, codigo_variante: str) -> None:
        self.db.execute(
            "UPDATE variantes SET modelo_id=?, color=?, piel=?, talla=?, codigo_variante=? WHERE id=?",
            (modelo_id, color, piel, talla, codigo_variante, variante_id),
        )

    def desactivar(self, variante_id: int) -> None:
        self.db.execute("UPDATE variantes SET activo=0 WHERE id=?", (variante_id,))


class ListaMaterialesModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def obtener_por_modelo(self, modelo_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT lm.*, i.nombre as insumo_nombre, i.codigo as insumo_codigo,
                      i.unidad_medida, i.stock_actual
               FROM lista_materiales lm
               JOIN insumos i ON i.id = lm.insumo_id
               WHERE lm.modelo_id = ?""",
            (modelo_id,),
        )

    def guardar(self, modelo_id: int, insumos: list[dict]) -> None:
        self.db.execute("DELETE FROM lista_materiales WHERE modelo_id = ?", (modelo_id,))
        for ins in insumos:
            self.db.execute(
                "INSERT INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) VALUES (?, ?, ?, ?)",
                (modelo_id, ins["insumo_id"], ins["cantidad"], ins.get("unidad", "pieza")),
            )


class EstacionModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        query = "SELECT * FROM estaciones_produccion"
        if solo_activos:
            query += " WHERE activo = 1"
        query += " ORDER BY orden, id"
        return self.db.fetch_all(query)

    def crear(self, nombre: str, orden: int, descripcion: str = "") -> int:
        cursor = self.db.execute(
            "INSERT INTO estaciones_produccion (nombre, orden, descripcion) VALUES (?, ?, ?)",
            (nombre, orden, descripcion),
        )
        return cursor.lastrowid

    def actualizar(self, estacion_id: int, nombre: str, orden: int, descripcion: str) -> None:
        self.db.execute(
            "UPDATE estaciones_produccion SET nombre=?, orden=?, descripcion=? WHERE id=?",
            (nombre, orden, descripcion, estacion_id),
        )

    def desactivar(self, estacion_id: int) -> None:
        self.db.execute("UPDATE estaciones_produccion SET activo=0 WHERE id=?", (estacion_id,))

    def eliminar(self, estacion_id: int) -> None:
        self.db.execute("DELETE FROM estaciones_produccion WHERE id=?", (estacion_id,))


class OrdenProduccionModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self) -> list[dict]:
        return self.db.fetch_all(
            """SELECT op.*, v.codigo_variante, m.nombre as modelo_nombre,
                      v.color, v.piel, v.talla
               FROM ordenes_produccion op
               JOIN variantes v ON v.id = op.variante_id
               JOIN modelos m ON m.id = v.modelo_id
               ORDER BY op.created_at DESC"""
        )

    def listar_tallas_corrida(self) -> list[dict]:
        return self.db.fetch_all(
            "SELECT * FROM tallas_corrida ORDER BY orden, id")

    def buscar(self, termino: str) -> list[dict]:
        q = "%" + termino + "%"
        return self.db.fetch_all(
            """SELECT op.*, v.codigo_variante, m.nombre as modelo_nombre, v.color, v.piel
               FROM ordenes_produccion op
               JOIN variantes v ON v.id = op.variante_id
               JOIN modelos m ON m.id = v.modelo_id
               WHERE op.folio LIKE ? OR m.nombre LIKE ? OR v.codigo_variante LIKE ?
               ORDER BY op.created_at DESC""", (q, q, q)
        )

    def obtener(self, op_id: int) -> Optional[dict]:
        return self.db.fetch_one(
            """SELECT op.*, v.codigo_variante, m.nombre as modelo_nombre,
                      v.modelo_id, v.color, v.piel
               FROM ordenes_produccion op
               JOIN variantes v ON v.id = op.variante_id
               JOIN modelos m ON m.id = v.modelo_id
               WHERE op.id = ?""",
            (op_id,),
        )

    def obtener_tallas(self, op_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT mto.*, tc.talla
               FROM matriz_tallas_op mto
               JOIN tallas_corrida tc ON tc.id = mto.talla_id
               WHERE mto.orden_produccion_id = ?
               ORDER BY tc.orden""",
            (op_id,),
        )

    def crear(self, folio: str, variante_id: int, total_pares: int,
              fecha_inicio: str = "", fecha_entrega: str = "",
              prioridad: str = "normal", observaciones: str = "") -> int:
        cursor = self.db.execute(
            "INSERT INTO ordenes_produccion (folio, variante_id, total_pares, fecha_inicio, fecha_entrega, prioridad, observaciones) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (folio, variante_id, total_pares, fecha_inicio, fecha_entrega, prioridad, observaciones),
        )
        op_id = cursor.lastrowid
        estaciones = self.db.fetch_all(
            "SELECT * FROM estaciones_produccion WHERE activo = 1 ORDER BY orden")
        for est in estaciones:
            self.db.execute(
                "INSERT INTO seguimiento_produccion (orden_produccion_id, estacion_id) VALUES (?, ?)",
                (op_id, est["id"]),
            )
        return op_id

    def agregar_talla(self, op_id: int, talla_id: int, pares: int) -> int:
        cursor = self.db.execute(
            "INSERT INTO matriz_tallas_op (orden_produccion_id, talla_id, pares) VALUES (?, ?, ?)",
            (op_id, talla_id, pares),
        )
        return cursor.lastrowid

    def verificar_materiales(self, variante_id: int, total_pares: int) -> list[dict]:
        variante = self.db.fetch_one("SELECT modelo_id FROM variantes WHERE id = ?", (variante_id,))
        if not variante:
            return []
        bom = self.db.fetch_all(
            """SELECT lm.*, i.nombre as insumo_nombre, i.unidad_medida, i.stock_actual
               FROM lista_materiales lm
               JOIN insumos i ON i.id = lm.insumo_id
               WHERE lm.modelo_id = ?""",
            (variante["modelo_id"],),
        )
        resultado = []
        for b in bom:
            requerido = b["cantidad_por_par"] * total_pares
            disponible = b["stock_actual"] or 0
            resultado.append({
                "insumo_id": b["insumo_id"],
                "insumo_nombre": b["insumo_nombre"],
                "unidad": b["unidad_medida"],
                "cantidad_por_par": b["cantidad_por_par"],
                "requerido": round(requerido, 2),
                "disponible": round(disponible, 2),
                "faltante": round(max(0.0, requerido - disponible), 2),
            })
        return resultado

    def consumir_insumos(self, op_id: int) -> list[dict]:
        op = self.obtener(op_id)
        if not op:
            return []
        bom = self.db.fetch_all(
            """SELECT lm.*, i.nombre as insumo_nombre, i.unidad_medida, i.stock_actual
               FROM lista_materiales lm
               JOIN insumos i ON i.id = lm.insumo_id
               WHERE lm.modelo_id = ?""",
            (op["modelo_id"],),
        )
        total = op.get("total_pares", 0)
        resultados = []
        for b in bom:
            requerido = b["cantidad_por_par"] * total
            disponible = b["stock_actual"] or 0
            faltante = max(0.0, requerido - disponible)
            nuevo_stock = max(0.0, disponible - requerido)
            self.db.execute(
                "UPDATE insumos SET stock_actual = ?, updated_at = datetime('now') WHERE id = ?",
                (nuevo_stock, b["insumo_id"]),
            )
            obs = f"Consumo OP {op['folio']}"
            if faltante > 0.005:
                obs += f" - FALTANTE {faltante:.2f}"
            self.db.execute(
                "INSERT INTO movimiento_inventario (insumo_id, tipo_movimiento, cantidad, referencia_tipo, referencia_id, observaciones) VALUES (?, 'salida', ?, 'orden_produccion', ?, ?)",
                (b["insumo_id"], round(requerido, 2), op_id, obs),
            )
            resultados.append({
                "insumo_nombre": b["insumo_nombre"],
                "unidad": b["unidad_medida"],
                "requerido": round(requerido, 2),
                "faltante": round(faltante, 2),
            })
        return resultados

    def avanzar_estacion(self, op_id: int, estacion_id: int, pares_procesados: int,
                          pares_defectuosos: int = 0, observaciones: str = "") -> None:
        estaciones = self.db.fetch_all(
            "SELECT * FROM estaciones_produccion WHERE activo = 1 ORDER BY orden, id")
        if not estaciones:
            return
        primera = estaciones[0]["id"]
        ultima = estaciones[-1]["id"]
        prev = self.db.fetch_one(
            "SELECT estatus FROM seguimiento_produccion WHERE orden_produccion_id = ? AND estacion_id = ?",
            (op_id, estacion_id),
        )
        if prev and prev["estatus"] == "pendiente" and estacion_id == primera:
            self.consumir_insumos(op_id)
        self.db.execute(
            """UPDATE seguimiento_produccion
               SET estatus = 'completado', fecha_salida = datetime('now'),
                   pares_procesados = ?, pares_defectuosos = ?, observaciones = ?
               WHERE orden_produccion_id = ? AND estacion_id = ?""",
            (pares_procesados, pares_defectuosos, observaciones, op_id, estacion_id),
        )
        siguiente = None
        for i, est in enumerate(estaciones):
            if est["id"] == estacion_id and i + 1 < len(estaciones):
                siguiente = estaciones[i + 1]
                break
        if siguiente:
            self.db.execute(
                "UPDATE seguimiento_produccion SET estatus = 'en_proceso', fecha_entrada = datetime('now') WHERE orden_produccion_id = ? AND estacion_id = ?",
                (op_id, siguiente["id"]),
            )
        if estacion_id == ultima:
            self.db.execute(
                "UPDATE ordenes_produccion SET estatus = 'terminada', updated_at = datetime('now') WHERE id = ?",
                (op_id,),
            )
            self._ingresar_pt(op_id)
        else:
            self.db.execute(
                "UPDATE ordenes_produccion SET estatus = 'en_produccion', updated_at = datetime('now') WHERE id = ?",
                (op_id,),
            )

    def posicion_actual(self, op_id: int) -> dict:
        op = self.obtener(op_id)
        if not op:
            return {"columna": None, "estacion": None}
        if op["estatus"] == "planeada":
            return {"columna": "planeada", "estacion": None}
        if op["estatus"] == "terminada":
            return {"columna": "terminada", "estacion": None}
        seguimiento = self.obtener_seguimiento(op_id)
        actual = None
        for s in seguimiento:
            if s["estatus"] != "completado":
                actual = s
                break
        if actual is None:
            return {"columna": "terminada", "estacion": None}
        return {"columna": actual["estacion_id"], "estacion": actual}

    def mover_en_kanban(self, op_id: int, target_estacion_id: int) -> bool:
        estaciones = self.db.fetch_all(
            "SELECT * FROM estaciones_produccion WHERE activo = 1 ORDER BY orden, id")
        if not estaciones:
            return False
        op = self.obtener(op_id)
        if not op:
            return False
        pos = self.posicion_actual(op_id)
        if pos["columna"] == "terminada":
            return False
        if pos["columna"] == "planeada":
            current_index = -1
        else:
            current_index = next(
                (i for i, e in enumerate(estaciones) if e["id"] == pos["columna"]), None
            )
            if current_index is None:
                return False
        if target_estacion_id == "terminada":
            target_index = len(estaciones)
        else:
            target_index = next(
                (i for i, e in enumerate(estaciones) if e["id"] == target_estacion_id), None
            )
            if target_index is None:
                return False
        if target_index <= current_index:
            return False
        inicio = current_index + 1
        fin = min(target_index, len(estaciones) - 1)
        for i in range(inicio, fin + 1):
            self.avanzar_estacion(op_id, estaciones[i]["id"], op["total_pares"])
        return True

    def _ingresar_pt(self, op_id: int) -> None:
        op = self.obtener(op_id)
        if not op:
            return
        tallas = self.db.fetch_all(
            "SELECT * FROM matriz_tallas_op WHERE orden_produccion_id = ?", (op_id,)
        )
        for t in tallas:
            if t["pares"] > 0:
                existente = self.db.fetch_one(
                    "SELECT * FROM inventario_pt WHERE variante_id = ? AND talla_id = ?",
                    (op["variante_id"], t["talla_id"]),
                )
                if existente:
                    self.db.execute(
                        "UPDATE inventario_pt SET pares = pares + ?, updated_at = datetime('now') WHERE id = ?",
                        (t["pares"], existente["id"]),
                    )
                else:
                    self.db.execute(
                        "INSERT INTO inventario_pt (variante_id, talla_id, pares) VALUES (?, ?, ?)",
                        (op["variante_id"], t["talla_id"], t["pares"]),
                    )

    def obtener_seguimiento(self, op_id: int) -> list[dict]:
        return self.db.fetch_all(
            """SELECT sp.*, e.nombre as estacion_nombre, e.orden
               FROM seguimiento_produccion sp
               JOIN estaciones_produccion e ON e.id = sp.estacion_id
               WHERE sp.orden_produccion_id = ?
               ORDER BY e.orden""",
            (op_id,),
        )


class InventarioPTModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self) -> list[dict]:
        return self.db.fetch_all(
            """SELECT ipt.*, v.codigo_variante, m.nombre as modelo_nombre,
                      v.color, v.piel, tc.talla
               FROM inventario_pt ipt
               JOIN variantes v ON v.id = ipt.variante_id
               JOIN modelos m ON m.id = v.modelo_id
               JOIN tallas_corrida tc ON tc.id = ipt.talla_id
               ORDER BY m.nombre, v.codigo_variante, tc.orden"""
        )
