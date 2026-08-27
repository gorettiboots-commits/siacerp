"""Registrar nueva empresa en Supabase (multi-tenant).

Uso:
    python scripts/registrar_empresa.py \
        --nombre "Mi Empresa" \
        --rfc "XAXX010101000" \
        --email-admin "admin@miempresa.com" \
        --password-admin "admin123"

Este script:
1. Crea la empresa en la tabla 'empresas'
2. Crea el usuario admin en Supabase Auth
3. Crea el perfil vinculado a la empresa
4. Muestra el empresa_id para configurar en config.ini

Requiere service_role_key en config.ini [supabase].
"""
import argparse
import configparser
import json
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def obtener_supabase():
    """Lee configuracion de Supabase desde config.ini."""
    config = configparser.ConfigParser()
    config.read(str(RAIZ / "config.ini"))
    if not config.has_section("supabase"):
        print("[ERROR] Seccion [supabase] no encontrada en config.ini")
        sys.exit(1)
    url = config.get("supabase", "url", fallback="").strip()
    anon_key = config.get("supabase", "anon_key", fallback="").strip()
    service_key = config.get("supabase", "service_role_key", fallback="").strip()
    if not url or not anon_key:
        print("[ERROR] url o anon_key vacios en config.ini")
        sys.exit(1)
    if not service_key:
        print("[WARN] service_role_key no configurada, usando anon_key")
        service_key = anon_key
    return url, anon_key, service_key


def api_call(url, key, method="GET", data=None):
    """Realiza una llamada a la API de Supabase con service_role."""
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "return=representation"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            if not raw.strip():
                return {"ok": True}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "already registered" in body or "duplicate key" in body or e.code == 409:
            return "DUPLICATE"
        print(f"[ERROR] HTTP {e.code}: {body[:300]}")
        return None


def crear_empresa(url, service_key, nombre, rfc=None):
    """Crea una empresa en Supabase."""
    empresa_id = str(uuid.uuid4())
    data = {"id": empresa_id, "nombre": nombre, "rfc": rfc, "activo": True}
    result = api_call(f"{url}/rest/v1/empresas", service_key, "POST", data)
    if result is not None and result != "DUPLICATE":
        print(f"  [OK] Empresa creada: {empresa_id}")
        return empresa_id
    elif result == "DUPLICATE":
        print(f"  [WARN] Empresa ya existe, buscando...")
        empresas = api_call(f"{url}/rest/v1/empresas?nombre=eq.{nombre}&select=id", service_key)
        if empresas and len(empresas) > 0:
            return empresas[0]["id"]
    return None


def crear_usuario_auth(url, service_key, email, password):
    """Crea un usuario en Supabase Auth."""
    data = {"email": email, "password": password, "email_confirm": True}
    result = api_call(f"{url}/auth/v1/admin/users", service_key, "POST", data)
    if result and isinstance(result, dict) and "id" in result:
        print(f"  [OK] Usuario Auth: {result['id']}")
        return result["id"]
    elif result == "DUPLICATE" or (isinstance(result, dict) and "msg" in result and "already" in str(result.get("msg", ""))):
        print(f"  [WARN] Usuario ya existe, buscando...")
        users = api_call(f"{url}/auth/v1/admin/users?page=1&per_page=50", service_key)
        if users and "users" in users:
            for u in users["users"]:
                if u.get("email") == email:
                    print(f"  [OK] Usuario encontrado: {u['id']}")
                    return u["id"]
    return None


def crear_perfil(url, service_key, user_id, empresa_id, username, nombre, rol):
    """Crea el perfil del usuario en perfiles_usuario."""
    data = {
        "id": user_id,
        "empresa_id": empresa_id,
        "username": username,
        "nombre_completo": nombre,
        "rol": rol,
        "activo": True,
    }
    result = api_call(f"{url}/rest/v1/perfiles_usuario", service_key, "POST", data)
    if result is not None and result != "DUPLICATE":
        print(f"  [OK] Perfil: {username} ({rol})")
        return True
    elif result == "DUPLICATE":
        print(f"  [OK] Perfil ya existe")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Registrar nueva empresa en SIAC ERP")
    parser.add_argument("--nombre", required=True, help="Nombre de la empresa")
    parser.add_argument("--rfc", default=None, help="RFC de la empresa")
    parser.add_argument("--email-admin", required=True, help="Email del admin de la empresa")
    parser.add_argument("--password-admin", required=True, help="Password del admin")
    parser.add_argument("--username", default=None, help="Username del admin (default: email sin @)")
    args = parser.parse_args()

    print("=" * 60)
    print("SIAC ERP - Registro de Nueva Empresa")
    print("=" * 60)
    print()

    # 1. Cargar configuracion
    url, anon_key, service_key = obtener_supabase()
    print(f"Supabase: {url[:40]}...")
    print(f"Service key: {'Configurada' if service_key != anon_key else 'Usando anon_key'}")
    print()

    # 2. Crear empresa
    print(f"[1/4] Creando empresa '{args.nombre}'...")
    empresa_id = crear_empresa(url, service_key, args.nombre, args.rfc)
    if not empresa_id:
        print("[ERROR] No se pudo crear la empresa")
        sys.exit(1)
    print()

    # 3. Crear usuario admin
    print(f"[2/4] Creando usuario admin: {args.email_admin}...")
    user_id = crear_usuario_auth(url, service_key, args.email_admin, args.password_admin)
    if not user_id:
        print("[ERROR] No se pudo crear el usuario")
        sys.exit(1)
    print()

    # 4. Crear perfil
    print("[3/4] Creando perfil de admin...")
    username = args.username or args.email_admin.split("@")[0]
    nombre = f"Admin de {args.nombre}"
    crear_perfil(url, service_key, user_id, empresa_id, username, nombre, "admin")
    print()

    # 5. Resumen
    print("[4/4] Configuracion para la nueva instancia...")
    print()
    print("=" * 60)
    print("EMPRESA REGISTRADA EXITOSAMENTE")
    print("=" * 60)
    print(f"  Empresa:      {args.nombre}")
    print(f"  Empresa ID:   {empresa_id}")
    print(f"  Admin email:  {args.email_admin}")
    print(f"  Admin pass:   {args.password_admin}")
    print(f"  Username:     {username}")
    print()
    print("  Agregar en config.ini de la nueva instancia:")
    print(f"    [supabase]")
    print(f"    url = {url}")
    print(f"    anon_key = {anon_key[:20]}...")
    print(f"    empresa_id = {empresa_id}")
    print()
    print("  O ejecutar en la nueva terminal:")
    print(f"    python scripts/configurar_instancia.py --empresa-id {empresa_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
