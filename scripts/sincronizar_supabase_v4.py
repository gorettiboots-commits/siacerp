"""Sincronizacion SIAC ERP a Supabase - v4 corregida"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.database.db_manager import DatabaseManager


def print_ok(msg): print(f"  [OK] {msg}")
def print_error(msg): print(f"  [ERROR] {msg}")


def obtener_config():
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(str(RAIZ / "config.ini"))
        if config.has_section("supabase"):
            url = config.get("supabase", "url", fallback="").strip()
            key = config.get("supabase", "anon_key", fallback="").strip()
            if url and key: return url, key
    except: pass
    return None, None


def login(url, key, email, password):
    auth_url = f"{url.rstrip('/')}/auth/v1/token?grant_type=password"
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(auth_url, data=body, headers={
        "apikey": key, "Content-Type": "application/json"
    }, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())["access_token"]


def upsert(tabla, registros, url, api_key, token):
    """Upsert: apikey=anon_key, Authorization=Bearer token"""
    api_url = f"{url.rstrip('/')}/rest/v1/{tabla}"
    data = json.dumps(registros).encode()
    req = urllib.request.Request(api_url, data=data, method="POST", headers={
        "apikey": api_key,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status


def sync_tallas(db, url, ak, tk):
    print("  Tallas...")
    filas = db.fetch_all("SELECT id, talla, activo FROM tallas_catalogo ORDER BY CAST(talla AS REAL)")
    reg = [{"id": f["id"], "talla": f["talla"], "activo": bool(f["activo"])} for f in filas]
    if reg: upsert("tallas_catalogo_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_insumos(db, url, ak, tk):
    print("  Insumos...")
    filas = db.fetch_all("SELECT id, codigo, nombre, categoria, unidad_medida, stock_actual, stock_minimo FROM insumos WHERE activo = 1")
    reg = [{"id": f["id"], "codigo": f["codigo"], "nombre": f["nombre"], "categoria": f["categoria"],
            "unidad_medida": f["unidad_medida"], "stock_actual": f["stock_actual"],
            "stock_minimo": f["stock_minimo"], "activo": True} for f in filas]
    if reg: upsert("insumos_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_ocs(db, url, ak, tk):
    print("  Ordenes de compra...")
    filas = db.fetch_all(
        "SELECT oc.id, oc.folio, oc.fecha_emision, oc.estatus, oc.total, oc.metodo_pago, "
        "oc.solo_remision, oc.tipo, oc.observaciones, p.nombre AS proveedor_nombre "
        "FROM ordenes_compra oc LEFT JOIN proveedores p ON p.id = oc.proveedor_id ORDER BY oc.id DESC LIMIT 100")
    reg = [{"id": f["id"], "folio": f["folio"], "proveedor_nombre": f.get("proveedor_nombre") or "",
            "fecha_emision": f.get("fecha_emision"), "estatus": f["estatus"], "total": f["total"],
            "metodo_pago": f["metodo_pago"], "solo_remision": bool(f["solo_remision"]),
            "tipo": f["tipo"], "observaciones": f.get("observaciones")} for f in filas]
    if reg: upsert("ordenes_compra_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_ops(db, url, ak, tk):
    print("  Ordenes de produccion...")
    filas = db.fetch_all(
        "SELECT op.id, op.folio, op.total_pares, op.fecha_inicio, op.fecha_entrega, "
        "op.prioridad, op.estatus, m.nombre AS modelo_nombre, v.codigo_variante "
        "FROM ordenes_produccion op LEFT JOIN variantes v ON v.id = op.variante_id "
        "LEFT JOIN modelos m ON m.id = v.modelo_id WHERE op.estatus != 'terminada' ORDER BY op.fecha_entrega")
    reg = [{"id": f["id"], "folio": f["folio"], "modelo_nombre": f.get("modelo_nombre") or "",
            "codigo_variante": f.get("codigo_variante") or "", "total_pares": f["total_pares"],
            "fecha_inicio": f.get("fecha_inicio"), "fecha_entrega": f.get("fecha_entrega"),
            "prioridad": f["prioridad"], "estatus": f["estatus"]} for f in filas]
    if reg: upsert("ordenes_produccion_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_seguimiento(db, url, ak, tk):
    print("  Seguimiento...")
    filas = db.fetch_all(
        "SELECT sp.id, sp.orden_produccion_id, sp.estatus, sp.pares_procesados, "
        "sp.pares_defectuosos, sp.observaciones, ep.nombre AS estacion_nombre "
        "FROM seguimiento_produccion sp JOIN estaciones_produccion ep ON ep.id = sp.estacion_id "
        "JOIN ordenes_produccion op ON op.id = sp.orden_produccion_id WHERE op.estatus != 'terminada'")
    reg = [{"id": f["id"], "orden_produccion_id": f["orden_produccion_id"],
            "estacion_nombre": f["estacion_nombre"], "estatus": f["estatus"],
            "pares_procesados": f["pares_procesados"] or 0,
            "pares_defectuosos": f["pares_defectuosos"] or 0,
            "observaciones": f.get("observaciones")} for f in filas]
    if reg: upsert("seguimiento_produccion_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def main():
    print("=" * 60)
    print("SIAC ERP - Sincronizacion a Supabase v4")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    config = obtener_config()
    if not config: print_error("Supabase no configurado"); sys.exit(1)
    url, anon_key = config
    print(f"\n[OK] Supabase: {url[:40]}...")

    print("Autenticando...")
    token = login(url, anon_key, "admin@siac.com", "admin123")
    print("[OK] Token obtenido\n")

    db = DatabaseManager()
    print("[OK] BD local conectada\n")

    total = 0
    ini = datetime.now()
    try:
        total += sync_tallas(db, url, anon_key, token)
        total += sync_insumos(db, url, anon_key, token)
        total += sync_ocs(db, url, anon_key, token)
        total += sync_ops(db, url, anon_key, token)
        total += sync_seguimiento(db, url, anon_key, token)
    except Exception as e:
        print_error(f"{e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

    dur = (datetime.now() - ini).total_seconds()
    print(f"\n{'='*60}")
    print(f"[OK] Sincronizacion completada: {total} registros en {dur:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
