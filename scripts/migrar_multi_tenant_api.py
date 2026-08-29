"""
Migracion multi-tenant via API REST de Supabase.
Ejecuta cada paso de la migracion de forma segura.
"""
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Configuracion
URL = "https://makeccmgamhumiktuhxh.supabase.co"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ha2VjY21nYW1odW1pa3R1aHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODY2NzE5NDQsImV4cCI6MjEwMjI0Nzk0NH0.1FNnNidBK_WGzqcFd95p_XgxYj26z-E2fY59bs4JXT8"


def api(method, endpoint, data=None, token=None):
    headers = {"apikey": API_KEY, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    url = f"{URL}/rest/v1/{endpoint}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return e.code, body


def login(email, password):
    data = json.dumps({"email": email, "password": password}).encode()
    req = urllib.request.Request(
        f"{URL}/auth/v1/token?grant_type=password",
        data=data,
        headers={"apikey": API_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())
        return result["access_token"], result["user"]["id"]


def main():
    print("=" * 60)
    print("SIAC ERP - Migracion Multi-Tenant via API")
    print("=" * 60)

    # Login
    print("\n[1] Autenticando...")
    token, user_id = login("admin@siac.com", "admin123")
    print(f"    Token: {token[:20]}...")
    print(f"    User ID: {user_id}")

    # Verificar si la tabla empresas ya existe
    print("\n[2] Verificando tabla 'empresas'...")
    status, data = api("GET", "empresas?select=id&limit=1", token=token)
    print(f"    Status: {status}")

    empresa_id = None

    if status == 200:
        # La tabla ya existe
        if isinstance(data, list) and len(data) > 0:
            empresa_id = data[0]["id"]
            print(f"    Empresa existente: {empresa_id}")
        else:
            # Tabla existe pero esta vacia, crear empresa
            empresa_id = str(uuid.uuid4())
            status, _ = api("POST", "empresas", {
                "id": empresa_id,
                "nombre": "SIAC ERP",
                "activo": True,
            }, token=token)
            print(f"    Empresa creada: {empresa_id} (status: {status})")
    elif status == 404 or "does not exist" in str(data):
        print("    Tabla no existe - necesita ejecutar schema.sql primero")
        print("    Ejecuta 'mobile/supabase/schema.sql' en SQL Editor")
        print("    y luego vuelve a ejecutar este script")
        sys.exit(1)
    else:
        print(f"    Error: {data}")
        sys.exit(1)

    if not empresa_id:
        print("[ERROR] No se pudo obtener/crear empresa_id")
        sys.exit(1)

    # Verificar si empresa_id ya esta en perfiles_usuario
    print("\n[3] Verificando empresa_id en perfiles_usuario...")
    status, data = api(
        "GET",
        "perfiles_usuario?select=id,empresa_id,username&limit=10",
        token=token,
    )
    print(f"    Status: {status}")
    if isinstance(data, list):
        for p in data:
            tiene_empresa = "empresa_id" in p and p["empresa_id"] is not None
            print(f"    - {p.get('username', '?')}: empresa_id={'SI' if tiene_empresa else 'NO'}")

    # Verificar si empresa_id ya esta en insumos_movil
    print("\n[4] Verificando empresa_id en insumos_movil...")
    status, data = api(
        "GET",
        "insumos_movil?select=id,empresa_id&limit=3",
        token=token,
    )
    print(f"    Status: {status}")
    if isinstance(data, list) and len(data) > 0:
        tiene_empresa = "empresa_id" in data[0] and data[0]["empresa_id"] is not None
        print(f"    empresa_id en insumos: {'SI' if tiene_empresa else 'NO'}")
    else:
        print("    (sin datos o tabla no existe)")

    print(f"\n{'=' * 60}")
    print("DIAGNOSTICO COMPLETADO")
    print(f"{'=' * 60}")
    print()
    print("Si empresa_id NO esta en las tablas, necesitas ejecutar")
    print("el script de migracion en Supabase SQL Editor:")
    print()
    print("  1. Ve a https://supabase.com/dashboard")
    print("  2. Selecciona tu proyecto")
    print("  3. Ve a SQL Editor")
    print("  4. Copia el contenido de:")
    print("     mobile/supabase/migrar_multi_tenant.sql")
    print("  5. Haz clic en 'Run'")
    print()
    print("Despues de ejecutar, vuelve a correr este script para verificar.")
    print("=" * 60)


if __name__ == "__main__":
    main()
