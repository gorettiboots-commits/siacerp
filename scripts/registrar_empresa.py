"""
Registrar nueva empresa en Supabase.

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
    config = configparser.ConfigParser()
    config.read(str(RAIZ / "config.ini"))
    if not config.has_section("supabase"):
        print("[ERROR] Seccion [supabase] no encontrada en config.ini")
        sys.exit(1)
    url = config.get("supabase", "url", fallback="").strip()
    key = config.get("supabase", "anon_key", fallback="").strip()
    if not url or not key:
        print("[ERROR] url o anon_key vacios en config.ini")
        sys.exit(1)
    return url, key


def api_request(url, api_key, method="GET", data=None, token=None):
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[ERROR] HTTP {e.code}: {body[:300]}")
        return None


def crear_empresa(url, api_key, token, nombre, rfc=None):
    empresa_id = str(uuid.uuid4())
    data = {
        "id": empresa_id,
        "nombre": nombre,
        "rfc": rfc,
        "activo": True,
    }
    result = api_request(
        f"{url}/rest/v1/empresas", api_key, "POST", data, token
    )
    if result is not None:
        print(f"[OK] Empresa creada: {empresa_id}")
        return empresa_id
    return None


def crear_usuario_auth(url, api_key, email, password):
    data = {"email": email, "password": password, "email_confirm": True}
    result = api_request(
        f"{url}/auth/v1/admin/users", api_key, "POST", data
    )
    if result and "id" in result:
        print(f"[OK] Usuario Auth creado: {result['id']}")
        return result["id"]
    return None


def login(url, api_key, email, password):
    data = {"email": email, "password": password}
    result = api_request(
        f"{url}/auth/v1/token?grant_type=password", api_key, "POST", data
    )
    if result and "access_token" in result:
        return result["access_token"], result["user"]["id"]
    return None, None


def crear_perfil(url, api_key, token, user_id, empresa_id, username, rol):
    data = {
        "id": user_id,
        "empresa_id": empresa_id,
        "username": username,
        "nombre_completo": f"Admin de {username}",
        "rol": rol,
        "activo": True,
    }
    result = api_request(
        f"{url}/rest/v1/perfiles_usuario", api_key, "POST", data, token
    )
    if result is not None:
        print(f"[OK] Perfil creado: {username} ({rol})")
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Registrar nueva empresa en SIAC ERP"
    )
    parser.add_argument("--nombre", required=True, help="Nombre de la empresa")
    parser.add_argument("--rfc", default=None, help="RFC de la empresa")
    parser.add_argument(
        "--email-admin", required=True, help="Email del admin"
    )
    parser.add_argument(
        "--password-admin", required=True, help="Password del admin"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SIAC ERP - Registro de Nueva Empresa")
    print("=" * 60)

    url, api_key = obtener_supabase()
    print(f"[OK] Supabase: {url[:40]}...")

    # Login como admin existente para tener permisos
    print("\nAutenticando como admin existente...")
    token, _ = login(url, api_key, "admin@siac.com", "admin123")
    if not token:
        print("[ERROR] No se pudo autenticar como admin existente")
        print("  Asegurate de que existe admin@siac.com en Supabase")
        sys.exit(1)
    print("[OK] Autenticado")

    # Crear empresa
    print(f"\nCreando empresa '{args.nombre}'...")
    empresa_id = crear_empresa(url, api_key, token, args.nombre, args.rfc)
    if not empresa_id:
        sys.exit(1)

    # Crear usuario admin de la nueva empresa
    print(f"\nCreando usuario admin: {args.email_admin}...")
    user_id = crear_usuario_auth(url, api_key, args.email_admin, args.password_admin)
    if not user_id:
        sys.exit(1)

    # Crear perfil
    print("\nCreando perfil de admin...")
    username = args.email_admin.split("@")[0]
    crear_perfil(url, api_key, token, user_id, empresa_id, username, "admin")

    print(f"\n{'=' * 60}")
    print("[OK] Empresa registrada exitosamente")
    print(f"  Empresa: {args.nombre}")
    print(f"  Empresa ID: {empresa_id}")
    print(f"  Admin: {args.email_admin} / {args.password_admin}")
    print(f"  Username: {username}")
    print()
    print("  Agregar en config.ini de la nueva instancia:")
    print(f"    empresa_id = {empresa_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
