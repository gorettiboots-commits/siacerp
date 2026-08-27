"""Sincronizacion SIAC ERP a Supabase - v5 Multi-Tenant"""
import json
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.database.db_manager import DatabaseManager


def print_ok(msg):
    print(f"  [OK] {msg}")


def print_error(msg):
    print(f"  [ERROR] {msg}")


def obtener_config():
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(str(RAIZ / "config.ini"))
        if config.has_section("supabase"):
            url = config.get("supabase", "url", fallback="").strip()
            key = config.get("supabase", "anon_key", fallback="").strip()
            empresa = config.get("supabase", "empresa_id", fallback="").strip()
            if url and key and empresa:
                return url, key, uuid.UUID(empresa)
            elif url and key:
                print_error(
                    "empresa_id no configurado en config.ini [supabase]"
                )
                return None, None, None
    except Exception:
        pass
    return None, None, None


def login(url, key, email, password):
    auth_url = f"{url.rstrip('/')}/auth/v1/token?grant_type=password"
    body = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        auth_url,
        data=body,
        headers={"apikey": key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())["access_token"]


def upsert(tabla, registros, url, api_key, token):
    """Upsert: apikey=anon_key, Authorization=Bearer token"""
    api_url = f"{url.rstrip('/')}/rest/v1/{tabla}"
    data = json.dumps(registros).encode()
    req = urllib.request.Request(
        api_url,
        data=data,
        method="POST",
        headers={
            "apikey": api_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status


def sync_empresas(db, empresa_id, url, ak, tk):
    """Sincronizar la empresa actual (si no existe, crearla)"""
    print("  Empresa...")
    # Verificar si la empresa ya existe
    api_url = (
        f"{url.rstrip('/')}/rest/v1/empresas"
        f"?id=eq.{empresa_id}&select=id"
    )
    req = urllib.request.Request(
        api_url,
        headers={
            "apikey": ak,
            "Authorization": f"Bearer {tk}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data:
                print_ok("Empresa ya existe")
                return
    except Exception:
        pass

    # Crear empresa
    import configparser
    config = configparser.ConfigParser()
    config.read(str(RAIZ / "config.ini"))
    company = config.get("app", "company_name", fallback="SIAC")

    reg = {
        "id": str(empresa_id),
        "nombre": company,
        "activo": True,
    }
    upsert("empresas", [reg], url, ak, tk)
    print_ok(f"Empresa '{company}' creada")


def sync_perfil_admin(db, empresa_id, url, ak, tk):
    """Sincronizar perfil del admin"""
    print("  Perfil admin...")
    login_data = json.dumps({
        "email": "admin@siac.com",
        "password": "admin123"
    }).encode()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/auth/v1/token?grant_type=password",
        data=login_data,
        headers={"apikey": ak, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        user = json.loads(resp.read().decode())
        user_id = user["user"]["id"]

    reg = {
        "id": user_id,
        "empresa_id": str(empresa_id),
        "username": "admin",
        "nombre_completo": "Administrador del Sistema",
        "rol": "admin",
        "activo": True,
    }
    upsert("perfiles_usuario", [reg], url, ak, tk)
    print_ok(f"Perfil admin: {user_id}")


def sync_tallas(db, empresa_id, url, ak, tk):
    print("  Tallas...")
    filas = db.fetch_all(
        "SELECT id, talla, activo FROM tallas_catalogo "
        "ORDER BY CAST(talla AS REAL)"
    )
    eid = str(empresa_id)
    reg = [
        {"id": f["id"], "empresa_id": eid, "talla": f["talla"],
         "activo": bool(f["activo"])}
        for f in filas
    ]
    if reg:
        upsert("tallas_catalogo_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_insumos(db, empresa_id, url, ak, tk):
    print("  Insumos...")
    filas = db.fetch_all(
        "SELECT id, codigo, nombre, categoria, unidad_medida, "
        "stock_actual, stock_minimo FROM insumos WHERE activo = 1"
    )
    eid = str(empresa_id)
    reg = [
        {"id": f["id"], "empresa_id": eid, "codigo": f["codigo"],
         "nombre": f["nombre"], "categoria": f["categoria"],
         "unidad_medida": f["unidad_medida"],
         "stock_actual": f["stock_actual"],
         "stock_minimo": f["stock_minimo"], "activo": True}
        for f in filas
    ]
    if reg:
        upsert("insumos_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_ocs(db, empresa_id, url, ak, tk):
    print("  Ordenes de compra...")
    filas = db.fetch_all(
        "SELECT oc.id, oc.folio, oc.fecha_emision, oc.estatus, "
        "oc.total, oc.metodo_pago, oc.solo_remision, oc.tipo, "
        "oc.observaciones, p.nombre AS proveedor_nombre "
        "FROM ordenes_compra oc "
        "LEFT JOIN proveedores p ON p.id = oc.proveedor_id "
        "ORDER BY oc.id DESC LIMIT 100"
    )
    eid = str(empresa_id)
    reg = [
        {"id": f["id"], "empresa_id": eid, "folio": f["folio"],
         "proveedor_nombre": f.get("proveedor_nombre") or "",
         "fecha_emision": f.get("fecha_emision"),
         "estatus": f["estatus"], "total": f["total"],
         "metodo_pago": f["metodo_pago"],
         "solo_remision": bool(f["solo_remision"]),
         "tipo": f["tipo"],
         "observaciones": f.get("observaciones")}
        for f in filas
    ]
    if reg:
        upsert("ordenes_compra_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_ops(db, empresa_id, url, ak, tk):
    print("  Ordenes de produccion...")
    filas = db.fetch_all(
        "SELECT op.id, op.folio, op.total_pares, op.fecha_inicio, "
        "op.fecha_entrega, op.prioridad, op.estatus, "
        "m.nombre AS modelo_nombre, v.codigo_variante "
        "FROM ordenes_produccion op "
        "LEFT JOIN variantes v ON v.id = op.variante_id "
        "LEFT JOIN modelos m ON m.id = v.modelo_id "
        "WHERE op.estatus != 'terminada' ORDER BY op.fecha_entrega"
    )
    eid = str(empresa_id)
    reg = [
        {"id": f["id"], "empresa_id": eid, "folio": f["folio"],
         "modelo_nombre": f.get("modelo_nombre") or "",
         "codigo_variante": f.get("codigo_variante") or "",
         "total_pares": f["total_pares"],
         "fecha_inicio": f.get("fecha_inicio"),
         "fecha_entrega": f.get("fecha_entrega"),
         "prioridad": f["prioridad"], "estatus": f["estatus"]}
        for f in filas
    ]
    if reg:
        upsert("ordenes_produccion_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def sync_seguimiento(db, empresa_id, url, ak, tk):
    print("  Seguimiento...")
    filas = db.fetch_all(
        "SELECT sp.id, sp.orden_produccion_id, sp.estatus, "
        "sp.pares_procesados, sp.pares_defectuosos, "
        "sp.observaciones, ep.nombre AS estacion_nombre "
        "FROM seguimiento_produccion sp "
        "JOIN estaciones_produccion ep ON ep.id = sp.estacion_id "
        "JOIN ordenes_produccion op ON op.id = sp.orden_produccion_id "
        "WHERE op.estatus != 'terminada'"
    )
    eid = str(empresa_id)
    reg = [
        {"id": f["id"], "empresa_id": eid,
         "orden_produccion_id": f["orden_produccion_id"],
         "estacion_nombre": f["estacion_nombre"],
         "estatus": f["estatus"],
         "pares_procesados": f["pares_procesados"] or 0,
         "pares_defectuosos": f["pares_defectuosos"] or 0,
         "observaciones": f.get("observaciones")}
        for f in filas
    ]
    if reg:
        upsert("seguimiento_produccion_movil", reg, url, ak, tk)
    print_ok(f"{len(reg)} registros")
    return len(reg)


def main():
    print("=" * 60)
    print("SIAC ERP - Sincronizacion a Supabase v5 (Multi-Tenant)")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    url, anon_key, empresa_id = obtener_config()
    if not url or not empresa_id:
        print_error("Supabase o empresa_id no configurado en config.ini")
        print("  Agregar en [supabase]:")
        print("    url = https://tu-proyecto.supabase.co")
        print("    anon_key = tu-anon-key")
        print("    empresa_id = uuid-de-tu-empresa")
        sys.exit(1)

    print(f"\n[OK] Supabase: {url[:40]}...")
    print(f"[OK] Empresa: {empresa_id}")

    print("Autenticando...")
    token = login(url, anon_key, "admin@siac.com", "admin123")
    print("[OK] Token obtenido\n")

    db = DatabaseManager()
    print("[OK] BD local conectada\n")

    total = 0
    ini = datetime.now()
    try:
        # Sincronizar empresa y perfil admin primero
        sync_empresas(db, empresa_id, url, anon_key, token)
        sync_perfil_admin(db, empresa_id, url, anon_key, token)
        print()

        # Sincronizar datos
        total += sync_tallas(db, empresa_id, url, anon_key, token)
        total += sync_insumos(db, empresa_id, url, anon_key, token)
        total += sync_ocs(db, empresa_id, url, anon_key, token)
        total += sync_ops(db, empresa_id, url, anon_key, token)
        total += sync_seguimiento(
            db, empresa_id, url, anon_key, token
        )
    except Exception as e:
        print_error(f"{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    dur = (datetime.now() - ini).total_seconds()
    print(f"\n{'=' * 60}")
    print(
        f"[OK] Sincronizacion completada: {total} registros "
        f"en {dur:.1f}s"
    )
    print(f"  Empresa: {empresa_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
