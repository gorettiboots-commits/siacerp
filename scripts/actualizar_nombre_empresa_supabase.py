"""Actualiza el nombre de la empresa en Supabase para que coincida con el escritorio.

Ejecutar con: python scripts/actualizar_nombre_empresa_supabase.py
"""
import configparser
import json
import urllib.request
from pathlib import Path


def main():
    config = configparser.ConfigParser()
    ruta = Path(__file__).resolve().parent.parent / 'config.ini'
    if not ruta.exists():
        print("No se encontro config.ini")
        return
    config.read(str(ruta))

    url = config.get('supabase', 'url', fallback='')
    service_key = config.get('supabase', 'service_role_key', fallback='')
    empresa_id = config.get('supabase', 'empresa_id', fallback='')

    if not url or not service_key or not empresa_id:
        print("Falta configuracion de Supabase en config.ini")
        return

    # Leer nombre de empresa de la BD local
    from src.database.db_manager import DatabaseManager
    db = DatabaseManager()
    fila = db.fetch_one(
        "SELECT valor FROM configuracion_empresa WHERE clave = 'nombre_empresa'")
    nombre_local = fila['valor'] if fila else ''

    if not nombre_local:
        print("No hay nombre_empresa en configuracion_empresa")
        return

    print(f"Empresa local: {nombre_local}")
    print(f"Empresa ID: {empresa_id}")

    # Actualizar en Supabase
    datos = json.dumps({'nombre': nombre_local}).encode()
    req = urllib.request.Request(
        f'{url}/rest/v1/empresas?id=eq.{empresa_id}',
        data=datos,
        headers={
            'apikey': service_key,
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation',
        },
        method='PATCH'
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        resultado = json.loads(resp.read().decode())
        if resultado:
            print(f"OK: Empresa actualizada a '{resultado[0].get('nombre', '')}'")
        else:
            print("OK: Empresa actualizada")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == '__main__':
    main()
