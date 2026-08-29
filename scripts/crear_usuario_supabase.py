"""
Script para crear usuarios de prueba en Supabase Auth.

Uso:
    python scripts/crear_usuario_supabase.py
    python scripts/crear_usuario_supabase.py --email operador@siac.com --password operador123
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.database.db_manager import DatabaseManager


def obtener_config_supabase():
    url = os.environ.get("SUPABASE_URL", "").strip()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if url and anon_key:
        return url, anon_key
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


def crear_usuario_supabase(email, password, nombre, username, rol, config):
    base_url, anon_key = config
    
    print(f"  Creando usuario: {email}")
    try:
        auth_url = f"{base_url.rstrip('/')}/auth/v1/signup"
        auth_body = json.dumps({
            "email": email,
            "password": password,
            "data": {
                "nombre_completo": nombre,
                "username": username,
                "rol": rol,
            },
        }).encode("utf-8")
        auth_headers = {
            "apikey": anon_key,
            "Content-Type": "application/json",
        }
        auth_req = urllib.request.Request(
            auth_url, data=auth_body, headers=auth_headers, method="POST"
        )
        with urllib.request.urlopen(auth_req, timeout=30) as resp:
            auth_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")
        if "already been registered" in detalle:
            return {"ok": False, "mensaje": f"El correo {email} ya esta registrado"}
        return {"ok": False, "mensaje": f"Error: {detalle}"}
    except Exception as e:
        return {"ok": False, "mensaje": f"Error de conexion: {e}"}

    usuario_id = auth_data.get("id")
    if not usuario_id:
        return {"ok": False, "mensaje": "No se obtuvo el ID del usuario"}

    print(f"  [OK] Usuario creado en Auth: {usuario_id}")

    # Crear perfil
    print(f"  Creando perfil...")
    try:
        perfil_body = {
            "id": usuario_id,
            "username": username,
            "nombre_completo": nombre,
            "rol": rol,
            "activo": True,
        }
        data = json.dumps(perfil_body).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/rest/v1/perfiles_usuario",
            data=data,
            headers={
                "apikey": anon_key,
                "Authorization": f"Bearer {anon_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            pass
        print(f"  [OK] Perfil creado")
    except Exception as e:
        print(f"  [WARN] Error al crear perfil: {e}")

    return {"ok": True, "usuario_id": usuario_id}


def main():
    parser = argparse.ArgumentParser(description="Crear usuarios en Supabase Auth")
    parser.add_argument("--email", default="operador@siac.com")
    parser.add_argument("--password", default="operador123")
    parser.add_argument("--nombre", default="Operador de Prueba")
    parser.add_argument("--username", default="operador")
    parser.add_argument("--rol", default="operador", choices=["admin", "operador"])
    args = parser.parse_args()

    print("=" * 60)
    print("SIAC ERP - Crear Usuario Supabase")
    print("=" * 60)

    config = obtener_config_supabase()
    if config is None:
        print("\n[ERROR] Supabase no configurado en config.ini")
        sys.exit(1)

    print(f"[OK] Supabase configurado\n")

    resultado = crear_usuario_supabase(
        email=args.email,
        password=args.password,
        nombre=args.nombre,
        username=args.username,
        rol=args.rol,
        config=config,
    )

    if resultado["ok"]:
        print(f"\n[OK] {resultado['mensaje']}")
        print(f"\n  Credenciales para la app movil:")
        print(f"  --------------------------------")
        print(f"  Email:    {args.email}")
        print(f"  Password: {args.password}")
        print(f"  Rol:      {args.rol}")
        print(f"  --------------------------------")
        print(f"\n  NOTA: En Supabase -> Authentication -> Settings")
        print(f"  Desactiva 'Confirm email' para desarrollo")
    else:
        print(f"\n[ERROR] {resultado['mensaje']}")


if __name__ == "__main__":
    main()
