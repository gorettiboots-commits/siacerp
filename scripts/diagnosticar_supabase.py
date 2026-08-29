"""
Diagnóstico de conexión con Supabase.

Este script verifica:
1. La configuración de Supabase en config.ini
2. La resolución DNS del dominio
3. La conectividad HTTPS
4. La validez de la API key
5. La existencia de las tablas requeridas

Uso:
    python scripts/diagnosticar_supabase.py
"""

import json
import os
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def print_ok(msg):
    print(f"  [OK] {msg}")


def print_error(msg):
    print(f"  [ERROR] {msg}")


def print_warn(msg):
    print(f"  [WARN] {msg}")


def print_info(msg):
    print(f"  [INFO] {msg}")


def verificar_configuracion():
    """Verifica la configuración de Supabase."""
    print("\n1. Verificando configuracion...")
    
    # Buscar en config.ini
    config_path = RAIZ / "config.ini"
    if config_path.exists():
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read(str(config_path))
            
            if config.has_section("supabase"):
                url = config.get("supabase", "url", fallback="").strip()
                key = config.get("supabase", "anon_key", fallback="").strip()
                
                if url:
                    print_ok(f"URL encontrada: {url[:40]}...")
                else:
                    print_error("URL de Supabase vacia en config.ini")
                    return None, None
                    
                if key and len(key) > 20:
                    print_ok(f"API Key encontrada: {key[:20]}...")
                else:
                    print_error("API Key invalida o vacia")
                    return None, None
                    
                return url, key
            else:
                print_error("Seccion [supabase] no encontrada en config.ini")
                return None, None
        except Exception as e:
            print_error(f"Error al leer config.ini: {e}")
            return None, None
    else:
        print_error("config.ini no encontrado")
        return None, None


def verificar_dns(url):
    """Verifica la resolución DNS del dominio."""
    print("\n2. Verificando DNS...")
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.hostname
        
        print_info(f"Host a resolver: {host}")
        
        ip = socket.gethostbyname(host)
        print_ok(f"DNS resuelto: {host} -> {ip}")
        return True
    except socket.gaierror as e:
        print_error(f"No se pudo resolver el dominio: {e}")
        print_info("Posibles causas:")
        print_info("  - Sin conexion a internet")
        print_info("  - El dominio no existe")
        print_info("  - Problema temporal de DNS")
        return False
    except Exception as e:
        print_error(f"Error al verificar DNS: {e}")
        return False


def verificar_conexion(url):
    """Verifica la conectividad HTTPS."""
    print("\n3. Verificando conexion HTTPS...")
    
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "SIAC-ERP-Diagnostico/1.0")
        
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            print_ok(f"Conexion exitosa: HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        # HTTP error still means the server is reachable
        print_ok(f"Servidor accesible: HTTP {e.code}")
        return True
    except urllib.error.URLError as e:
        print_error(f"No se pudo conectar: {e.reason}")
        return False
    except Exception as e:
        print_error(f"Error de conexion: {e}")
        return False


def verificar_api_key(url, key):
    """Verifica que la API key sea valida."""
    print("\n4. Verificando API Key...")
    
    try:
        # Intentar una consulta simple
        api_url = f"{url.rstrip('/')}/rest/v1/?apikey={key}"
        req = urllib.request.Request(api_url)
        req.add_header("apikey", key)
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print_ok("API Key valida")
            print_info(f"Tablas encontradas: {len(data)}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print_error("API Key invalida o expirada")
        elif e.code == 403:
            print_warn("API Key sin permisos (puede que las tablas no existan)")
        else:
            print_error(f"Error HTTP: {e.code}")
        return False
    except Exception as e:
        print_error(f"Error al verificar API Key: {e}")
        return False


def verificar_tablas(url, key):
    """Verifica que las tablas requeridas existan."""
    print("\n5. Verificando tablas...")
    
    tablas_requeridas = [
        "perfiles_usuario",
        "insumos_movil",
        "ordenes_compra_movil",
        "ordenes_produccion_movil",
        "seguimiento_produccion_movil",
    ]
    
    tablas_encontradas = []
    
    for tabla in tablas_requeridas:
        try:
            api_url = f"{url.rstrip('/')}/rest/v1/{tabla}?select=id&limit=1"
            req = urllib.request.Request(api_url)
            req.add_header("apikey", key)
            req.add_header("Authorization", f"Bearer {key}")
            
            with urllib.request.urlopen(req, timeout=5) as resp:
                tablas_encontradas.append(tabla)
                print_ok(f"Tabla '{tabla}' existe")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print_error(f"Tabla '{tabla}' NO existe")
            elif e.code == 401:
                print_error(f"Tabla '{tabla}' - Sin permisos")
            else:
                print_warn(f"Tabla '{tabla}' - Error HTTP {e.code}")
        except Exception as e:
            print_warn(f"Tabla '{tabla}' - Error: {e}")
    
    print(f"\n  Resultado: {len(tablas_encontradas)}/{len(tablas_requeridas)} tablas encontradas")
    return len(tablas_encontradas) == len(tablas_requeridas)


def main():
    print("=" * 60)
    print("SIAC ERP - Diagnostico de Supabase")
    print("=" * 60)
    
    # 1. Verificar configuracion
    url, key = verificar_configuracion()
    if not url or not key:
        print("\n[FIN] Configuracion incompleta")
        sys.exit(1)
    
    # 2. Verificar DNS
    if not verificar_dns(url):
        print("\n[FIN] No se puede resolver el dominio")
        print("Soluciones:")
        print("  1. Verificar conexion a internet")
        print("  2. Cambiar DNS (8.8.8.8 o 1.1.1.1)")
        print("  3. Esperar y reintentar (puede ser temporal)")
        sys.exit(1)
    
    # 3. Verificar conexion
    if not verificar_conexion(url):
        print("\n[FIN] No se puede conectar a Supabase")
        sys.exit(1)
    
    # 4. Verificar API Key
    if not verificar_api_key(url, key):
        print("\n[FIN] API Key invalida")
        sys.exit(1)
    
    # 5. Verificar tablas
    tablas_ok = verificar_tablas(url, key)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL DIAGNOSTICO")
    print("=" * 60)
    
    if tablas_ok:
        print("\n[OK] Supabase esta configurado correctamente")
        print("\nPuedes ejecutar la sincronizacion:")
        print("  python scripts/sincronizar_supabase.py")
    else:
        print("\n[WARN] Algunas tablas no existen")
        print("\nEjecuta el esquema en Supabase SQL Editor:")
        print("  1. Ve a SQL Editor")
        print("  2. Copia el contenido de mobile/supabase/schema.sql")
        print("  3. Ejecuta el script")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
