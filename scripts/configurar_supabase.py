"""
Configuracion automatica de Supabase para SIAC ERP movil.

Este script ejecuta todo el proceso de configuracion:
1. Verifica conexion
2. Crea el esquema de tablas
3. Crea los usuarios de prueba
4. Crea los perfiles
5. Sincroniza datos iniciales

Uso:
    python scripts/configurar_supabase.py
    python scripts/configurar_supabase.py --admin-email admin@miempresa.com --admin-password admin123
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def print_ok(msg):
    print(f"  [OK] {msg}")

def print_error(msg):
    print(f"  [ERROR] {msg}")

def print_info(msg):
    print(f"  [INFO] {msg}")

def print_paso(msg):
    print(f"\n>> {msg}")


def obtener_config():
    """Lee la configuracion de Supabase de config.ini."""
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(str(RAIZ / "config.ini"))
        
        if config.has_section("supabase"):
            url = config.get("supabase", "url", fallback="").strip()
            key = config.get("supabase", "anon_key", fallback="").strip()
            if url and key:
                return url, key
    except Exception:
        pass
    return None, None


def supabase_request(method: str, ruta: str, body: Any = None,
                     config: tuple = None, extra_headers: dict = None) -> Any:
    """Ejecuta una peticion REST a Supabase."""
    if config is None:
        raise RuntimeError("Supabase no configurado")
    
    base_url, anon_key = config
    base = base_url.rstrip("/") + "/rest/v1"
    url = f"{base}/{ruta}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else None


def auth_request(method: str, path: str, body: dict = None, config: tuple = None) -> Any:
    """Ejecuta una peticion al endpoint de Auth."""
    if config is None:
        raise RuntimeError("Supabase no configurado")
    
    base_url, anon_key = config
    url = f"{base_url.rstrip('/')}/auth/v1{path}"
    headers = {
        "apikey": anon_key,
        "Content-Type": "application/json",
    }
    
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else None


def sql_request(sql: str, config: tuple) -> Any:
    """Ejecuta SQL directo via PostgREST (usando una funcion RPC)."""
    # Nota: Esto requiere que exista una funcion RPC para ejecutar SQL
    # Alternativamente, el usuario debe ejecutar el SQL manualmente
    return None


def verificar_conexion(config: tuple) -> bool:
    """Verifica que Supabase este accesible."""
    try:
        base_url, anon_key = config
        url = f"{base_url.rstrip('/')}/auth/v1/settings"
        req = urllib.request.Request(url)
        req.add_header("apikey", anon_key)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def verificar_tablas(config: tuple) -> dict:
    """Verifica que las tablas existan."""
    tablas_requeridas = [
        "perfiles_usuario",
        "insumos_movil",
        "ordenes_compra_movil",
        "detalle_orden_compra_movil",
        "detalle_oc_puntos_movil",
        "ordenes_produccion_movil",
        "seguimiento_produccion_movil",
        "incidencias_produccion_movil",
        "tallas_catalogo_movil",
        "logs_movil",
    ]
    
    resultados = {}
    base_url, anon_key = config
    
    for tabla in tablas_requeridas:
        try:
            url = f"{base_url.rstrip('/')}/rest/v1/{tabla}?select=id&limit=1"
            req = urllib.request.Request(url)
            req.add_header("apikey", anon_key)
            req.add_header("Authorization", f"Bearer {anon_key}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                resultados[tabla] = True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                resultados[tabla] = False
            else:
                resultados[tabla] = True  # Existe pero hay error de permisos
        except Exception:
            resultados[tabla] = False
    
    return resultados


def crear_esquema_sql():
    """Genera el SQL para crear las tablas."""
    sql = """
-- ============================================================
-- SIAC ERP - Esquema Supabase para sincronizacion movil
-- ============================================================

-- 1. PERFILES DE USUARIO
CREATE TABLE IF NOT EXISTS perfiles_usuario (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'operador',
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE perfiles_usuario ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios ven su propio perfil"
    ON perfiles_usuario FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Usuarios actualizan su propio perfil"
    ON perfiles_usuario FOR UPDATE
    USING (auth.uid() = id);

-- 2. INSUMOS
CREATE TABLE IF NOT EXISTS insumos_movil (
    id BIGINT PRIMARY KEY,
    codigo TEXT NOT NULL,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    unidad_medida TEXT NOT NULL DEFAULT 'pieza',
    stock_actual NUMERIC NOT NULL DEFAULT 0,
    stock_minimo NUMERIC NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE insumos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen insumos"
    ON insumos_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 3. ORDENES DE COMPRA
CREATE TABLE IF NOT EXISTS ordenes_compra_movil (
    id BIGINT PRIMARY KEY,
    folio TEXT NOT NULL,
    proveedor_nombre TEXT,
    fecha_emision TIMESTAMPTZ,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    total NUMERIC NOT NULL DEFAULT 0,
    metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria',
    solo_remision BOOLEAN NOT NULL DEFAULT false,
    tipo TEXT NOT NULL DEFAULT 'orden',
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE ordenes_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen OC"
    ON ordenes_compra_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 4. DETALLE OC
CREATE TABLE IF NOT EXISTS detalle_orden_compra_movil (
    id BIGINT PRIMARY KEY,
    orden_compra_id BIGINT NOT NULL REFERENCES ordenes_compra_movil(id),
    insumo_id BIGINT NOT NULL,
    insumo_nombre TEXT,
    cantidad NUMERIC NOT NULL,
    precio_unitario NUMERIC NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE detalle_orden_compra_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen detalle OC"
    ON detalle_orden_compra_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 5. PUNTOS OC
CREATE TABLE IF NOT EXISTS detalle_oc_puntos_movil (
    id BIGINT PRIMARY KEY,
    detalle_id BIGINT NOT NULL REFERENCES detalle_orden_compra_movil(id),
    talla_id BIGINT NOT NULL,
    talla TEXT NOT NULL,
    pares INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE detalle_oc_puntos_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen puntos OC"
    ON detalle_oc_puntos_movil F
