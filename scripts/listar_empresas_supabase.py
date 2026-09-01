"""Script temporal: listar empresas en Supabase.

Ejecutar con: python scripts/listar_empresas_supabase.py
"""
import configparser
import json
import urllib.request
from pathlib import Path


def main():
    config = configparser.ConfigParser()
    ruta = Path(__file__).resolve().parent.parent / 'config.ini'
    if not ruta.exists():
        print("❌ No se encontró config.ini")
        return
    config.read(str(ruta))

    url = config.get('supabase', 'url', fallback='')
    service_key = config.get('supabase', 'service_role_key', fallback='')
    anon_key = config.get('supabase', 'anon_key', fallback='')

    if not url:
        print("❌ No hay URL de Supabase en config.ini")
        return

    # Usar service_role key si existe, sino anon
    key = service_key or anon_key
    if not key:
        print("❌ No hay service_role_key ni anon_key en config.ini")
        return

    print(f"📡 Conectando a: {url}")
    print(f"🔑 Usando: {'service_role_key' if service_key else 'anon_key'}\n")

    # Listar empresas
    try:
        req = urllib.request.Request(
            f'{url}/rest/v1/empresas?select=*&order=nombre',
            headers={
                'apikey': key,
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
        )
        resp = urllib.request.urlopen(req, timeout=15)
        empresas = json.loads(resp.read().decode())

        if not empresas:
            print("⚠️  No hay empresas registradas en Supabase.")
            print("   Ejecuta: mobile/supabase/migrar_multi_tenant.sql")
            return

        print(f"📋 Empresas encontradas: {len(empresas)}\n")
        print(f"{'ID':<38} {'Nombre':<30} {'RFC':<15} {'Activo':<8}")
        print("-" * 95)
        for emp in empresas:
            activo = "✅ Sí" if emp.get('activo', True) else "❌ No"
            print(f"{emp['id']}  {emp.get('nombre', ''):<30} {(emp.get('rfc') or '—'):<15} {activo}")

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Error HTTP {e.code}: {body}")
        if e.code == 401:
            print("\n💡 La API key no tiene permisos. Verifica:")
            print("   1. Que service_role_key sea correcta")
            print("   2. Que la tabla 'empresas' exista en Supabase")
            print("   3. Que las migraciones hayan sido ejecutadas")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Listar perfiles
    print("\n\n📋 Perfiles de usuario en Supabase:\n")
    try:
        req = urllib.request.Request(
            f'{url}/rest/v1/perfiles_usuario?select=id,username,nombre_completo,rol,activo,empresa_id&order=rol,username',
            headers={
                'apikey': key,
                'Authorization': f'Bearer {key}',
                'Content-Type': 'application/json'
            }
        )
        resp = urllib.request.urlopen(req, timeout=15)
        perfiles = json.loads(resp.read().decode())

        if not perfiles:
            print("⚠️  No hay perfiles de usuario.")
            return

        print(f"{'Username':<20} {'Nombre':<25} {'Rol':<15} {'Activo':<8} {'Empresa ID'}")
        print("-" * 110)
        for p in perfiles:
            activo = "✅" if p.get('activo', True) else "❌"
            eid = (p.get('empresa_id') or 'NULL')[:8] + '...' if p.get('empresa_id') else 'NULL'
            print(f"{p.get('username', ''):<20} {p.get('nombre_completo', ''):<25} {p.get('rol', ''):<15} {activo:<8} {eid}")

    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Error HTTP {e.code}: {body}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
