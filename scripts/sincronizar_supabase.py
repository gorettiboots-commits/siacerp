"""
Sincronización de datos del escritorio SIAC ERP a Supabase.

Este script lee los datos de la base de datos local (SQLite o PostgreSQL)
y los envía a las tablas Supabase correspondientes para que la app móvil
pueda acceder a ellos.

Uso:
    python scripts/sincronizar_supabase.py

Configuración:
    Las credenciales de Supabase se leen de config.ini (sección [supabase])
    o de las variables de entorno SUPABASE_URL y SUPABASE_ANON_KEY.

Sincronización:
    - Insumos → insumos_movil
    - Órdenes de compra → ordenes_compra_movil
    - Detalle OC → detalle_orden_compra_movil
    - Puntos OC → detalle_oc_puntos_movil
    - Órdenes de producción → ordenes_produccion_movil
    - Seguimiento → seguimiento_produccion_movil
"""

import json
import os
from typing import Any
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# Agregar raíz del proyecto al path
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.database.db_manager import DatabaseManager


# ─── Configuración de Supabase ──────────────────────────────

def obtener_config_supabase() -> tuple[str, str] | None:
    """Obtiene (url, anon_key) de config.ini o variables de entorno."""
    # 1. Variables de entorno
    url = os.environ.get("SUPABASE_URL", "").strip()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if url and anon_key:
        return url, anon_key

    # 2. config.ini
    try:
        db = DatabaseManager()
        cfg = db.config
        url = cfg.get("supabase", "url", fallback="").strip()
        anon_key = cfg.get("supabase", "anon_key", fallback="").strip()
    except Exception:
        pass

    if url and anon_key:
        return url, anon_key

    return None


def supabase_request(method: str, ruta: str, body: dict | None = None,
                     config: tuple[str, str] | None = None) -> Any:
    """Ejecuta una petición REST a Supabase."""
    if config is None:
        config = obtener_config_supabase()
    if config is None:
        raise RuntimeError("Supabase no configurado. Define SUPABASE_URL y SUPABASE_ANON_KEY")

    base_url, anon_key = config
    base = base_url.rstrip("/") + "/rest/v1"
    url = f"{base}/{ruta}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8") if resp.read() else None
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase HTTP {e.code}: {detalle}") from e


# ─── Funciones de sincronización ────────────────────────────

def sincronizar_insumos(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza insumos activos a insumos_movil."""
    print("  Sincronizando insumos...")
    filas = db.fetch_all(
        "SELECT id, codigo, nombre, categoria, unidad_medida, "
        "stock_actual, stock_minimo, activo "
        "FROM insumos WHERE activo = 1 ORDER BY codigo"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "codigo": f["codigo"],
            "nombre": f["nombre"],
            "categoria": f["categoria"],
            "unidad_medida": f["unidad_medida"],
            "stock_actual": f["stock_actual"],
            "stock_minimo": f["stock_minimo"],
            "activo": True,
        })

    # Upsert: insertar o actualizar
    if registros:
        supabase_request("POST", "insumos_movil", registros, config)
    print(f"    → {len(registros)} insumos sincronizados")
    return len(registros)


def sincronizar_ordenes_compra(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza órdenes de compra a ordenes_compra_movil."""
    print("  Sincronizando órdenes de compra...")
    filas = db.fetch_all(
        "SELECT oc.id, oc.folio, oc.fecha_emision, oc.estatus, oc.total, "
        "oc.metodo_pago, oc.solo_remision, oc.tipo, oc.observaciones, "
        "p.nombre AS proveedor_nombre "
        "FROM ordenes_compra oc "
        "LEFT JOIN proveedores p ON p.id = oc.proveedor_id "
        "ORDER BY oc.id DESC LIMIT 100"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "folio": f["folio"],
            "proveedor_nombre": f.get("proveedor_nombre") or "Sin proveedor",
            "fecha_emision": f.get("fecha_emision"),
            "estatus": f["estatus"],
            "total": f["total"],
            "metodo_pago": f["metodo_pago"],
            "solo_remision": bool(f["solo_remision"]),
            "tipo": f["tipo"],
            "observaciones": f.get("observaciones"),
        })

    if registros:
        supabase_request("POST", "ordenes_compra_movil", registros, config)
    print(f"    → {len(registros)} órdenes sincronizadas")
    return len(registros)


def sincronizar_detalle_oc(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza detalle de OC y puntos/tallas."""
    print("  Sincronizando detalle de OC...")
    filas = db.fetch_all(
        "SELECT doc.id, doc.orden_compra_id, doc.insumo_id, "
        "doc.cantidad, doc.precio_unitario, "
        "i.nombre AS insumo_nombre "
        "FROM detalle_orden_compra doc "
        "JOIN insumos i ON i.id = doc.insumo_id "
        "ORDER BY doc.id"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "orden_compra_id": f["orden_compra_id"],
            "insumo_id": f["insumo_id"],
            "insumo_nombre": f["insumo_nombre"],
            "cantidad": f["cantidad"],
            "precio_unitario": f["precio_unitario"],
        })

    if registros:
        supabase_request("POST", "detalle_orden_compra_movil", registros, config)

    # Sincronizar puntos/tallas
    puntos = db.fetch_all(
        "SELECT dop.id, dop.detalle_id, dop.talla_id, dop.pares, "
        "tc.talla "
        "FROM detalle_orden_compra_puntos dop "
        "JOIN tallas_catalogo tc ON tc.id = dop.talla_id "
        "ORDER BY dop.id"
    )

    registros_puntos = []
    for p in puntos:
        registros_puntos.append({
            "id": p["id"],
            "detalle_id": p["detalle_id"],
            "talla_id": p["talla_id"],
            "talla": p["talla"],
            "pares": p["pares"],
        })

    if registros_puntos:
        supabase_request("POST", "detalle_oc_puntos_movil", registros_puntos, config)

    print(f"    → {len(registros)} detalles, {len(registros_puntos)} puntos")
    return len(registros) + len(registros_puntos)


def sincronizar_ordenes_produccion(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza órdenes de producción a ordenes_produccion_movil."""
    print("  Sincronizando órdenes de producción...")
    filas = db.fetch_all(
        "SELECT op.id, op.folio, op.total_pares, op.fecha_inicio, "
        "op.fecha_entrega, op.prioridad, op.estatus, "
        "m.nombre AS modelo_nombre, v.codigo_variante "
        "FROM ordenes_produccion op "
        "LEFT JOIN variantes v ON v.id = op.variante_id "
        "LEFT JOIN modelos m ON m.id = v.modelo_id "
        "WHERE op.estatus != 'terminada' "
        "ORDER BY op.fecha_entrega ASC LIMIT 50"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "folio": f["folio"],
            "modelo_nombre": f.get("modelo_nombre") or "",
            "codigo_variante": f.get("codigo_variante") or "",
            "total_pares": f["total_pares"],
            "fecha_inicio": f.get("fecha_inicio"),
            "fecha_entrega": f.get("fecha_entrega"),
            "prioridad": f["prioridad"],
            "estatus": f["estatus"],
        })

    if registros:
        supabase_request("POST", "ordenes_produccion_movil", registros, config)
    print(f"    → {len(registros)} OPs sincronizadas")
    return len(registros)


def sincronizar_seguimiento(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza seguimiento de producción a seguimiento_produccion_movil."""
    print("  Sincronizando seguimiento de producción...")
    filas = db.fetch_all(
        "SELECT sp.id, sp.orden_produccion_id, sp.estatus, "
        "sp.pares_procesados, sp.pares_defectuosos, sp.observaciones, "
        "ep.nombre AS estacion_nombre "
        "FROM seguimiento_produccion sp "
        "JOIN estaciones_produccion ep ON ep.id = sp.estacion_id "
        "JOIN ordenes_produccion op ON op.id = sp.orden_produccion_id "
        "WHERE op.estatus != 'terminada' "
        "ORDER BY sp.orden_produccion_id, ep.orden"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "orden_produccion_id": f["orden_produccion_id"],
            "estacion_nombre": f["estacion_nombre"],
            "estatus": f["estatus"],
            "pares_procesados": f["pares_procesados"] or 0,
            "pares_defectuosos": f["pares_defectuosos"] or 0,
            "observaciones": f.get("observaciones"),
        })

    if registros:
        supabase_request("POST", "seguimiento_produccion_movil", registros, config)
    print(f"    → {len(registros)} seguimientos sincronizados")
    return len(registros)


def sincronizar_tallas(db: DatabaseManager, config: tuple[str, str]) -> int:
    """Sincroniza catálogo de tallas."""
    print("  Sincronizando tallas...")
    filas = db.fetch_all(
        "SELECT id, talla, activo FROM tallas_catalogo ORDER BY CAST(talla AS REAL)"
    )

    registros = []
    for f in filas:
        registros.append({
            "id": f["id"],
            "talla": f["talla"],
            "activo": bool(f["activo"]),
        })

    if registros:
        supabase_request("POST", "tallas_catalogo_movil", registros, config)
    print(f"    → {len(registros)} tallas sincronizadas")
    return len(registros)


# ─── Función principal ──────────────────────────────────────

def sincronizar_todo():
    """Ejecuta la sincronización completa."""
    print("=" * 60)
    print("SIAC ERP — Sincronización a Supabase")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Verificar configuración
    config = obtener_config_supabase()
    if config is None:
        print("\n❌ Error: Supabase no está configurado.")
        print("   Define SUPABASE_URL y SUPABASE_ANON_KEY,")
        print("   o configura la sección [supabase] en config.ini")
        sys.exit(1)

    print(f"\n✅ Supabase configurado: {config[0][:30]}...")

    # Conectar a BD local
    db = DatabaseManager()
    print("✅ Conexión a BD local establecida\n")

    # Sincronizar cada tabla
    total = 0
    inicio = datetime.now()

    try:
        total += sincronizar_tallas(db, config)
        total += sincronizar_insumos(db, config)
        total += sincronizar_ordenes_compra(db, config)
        total += sincronizar_detalle_oc(db, config)
        total += sincronizar_ordenes_produccion(db, config)
        total += sincronizar_seguimiento(db, config)
    except Exception as e:
        print(f"\n❌ Error durante la sincronización: {e}")
        sys.exit(1)

    duracion = (datetime.now() - inicio).total_seconds()

    print("\n" + "=" * 60)
    print(f"✅ Sincronización completada")
    print(f"   Registros sincronizados: {total}")
    print(f"   Duración: {duracion:.1f} segundos")
    print("=" * 60)


if __name__ == "__main__":
    sincronizar_todo()
