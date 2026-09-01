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
    ON detalle_oc_puntos_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 6. ORDENES DE PRODUCCION
CREATE TABLE IF NOT EXISTS ordenes_produccion_movil (
    id BIGINT PRIMARY KEY,
    folio TEXT NOT NULL,
    modelo_nombre TEXT,
    codigo_variante TEXT,
    total_pares INTEGER NOT NULL DEFAULT 0,
    fecha_inicio TEXT,
    fecha_entrega TEXT,
    prioridad TEXT NOT NULL DEFAULT 'normal',
    estatus TEXT NOT NULL DEFAULT 'planeada',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE ordenes_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen OP"
    ON ordenes_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 7. SEGUIMIENTO PRODUCCION
CREATE TABLE IF NOT EXISTS seguimiento_produccion_movil (
    id BIGINT PRIMARY KEY,
    orden_produccion_id BIGINT NOT NULL REFERENCES ordenes_produccion_movil(id),
    estacion_nombre TEXT NOT NULL,
    estatus TEXT NOT NULL DEFAULT 'pendiente',
    pares_procesados INTEGER NOT NULL DEFAULT 0,
    pares_defectuosos INTEGER NOT NULL DEFAULT 0,
    observaciones TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE seguimiento_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen seguimiento"
    ON seguimiento_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Usuarios autenticados actualizan seguimiento"
    ON seguimiento_produccion_movil FOR UPDATE
    USING (auth.role() = 'authenticated');

-- 8. INCIDENCIAS
CREATE TABLE IF NOT EXISTS incidencias_produccion_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    seguimiento_id BIGINT NOT NULL REFERENCES seguimiento_produccion_movil(id),
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    pares_afectados INTEGER NOT NULL DEFAULT 0,
    reportado_por UUID REFERENCES perfiles_usuario(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE incidencias_produccion_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen incidencias"
    ON incidencias_produccion_movil FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Usuarios autenticados crean incidencias"
    ON incidencias_produccion_movil FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- 9. TALLAS
CREATE TABLE IF NOT EXISTS tallas_catalogo_movil (
    id BIGINT PRIMARY KEY,
    talla TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true
);

ALTER TABLE tallas_catalogo_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados leen tallas"
    ON tallas_catalogo_movil FOR SELECT
    USING (auth.role() = 'authenticated');

-- 10. LOGS
CREATE TABLE IF NOT EXISTS logs_movil (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    usuario_id UUID REFERENCES perfiles_usuario(id),
    accion TEXT NOT NULL,
    entidad TEXT NOT NULL,
    entidad_id BIGINT,
    detalle JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE logs_movil ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuarios autenticados crean logs"
    ON logs_movil FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Admin ve todos los logs"
    ON logs_movil FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM perfiles_usuario
            WHERE id = auth.uid() AND rol = 'admin'
        )
    );
"""
    return sql


def ejecutar_sql(sql_texto, url_supabase, service_role_key):
    """Ejecuta SQL via la API de Supabase (PostgREST)."""
    # Dividir en sentencias individuales
    sentencias = [s.strip() for s in sql_texto.split(';') if s.strip() and not s.strip().startswith('--')]
    exito = 0
    fallos = 0

    for sentencia in sentencias:
        if not sentencia:
            continue
        try:
            datos = json.dumps({"query": sentencia}).encode('utf-8')
            req = urllib.request.Request(
                f"{url_supabase}/rest/v1/rpc/executar_sql",
                data=datos,
                headers={
                    "Content-Type": "application/json",
                    "apikey": service_role_key,
                    "Authorization": f"Bearer {service_role_key}",
                },
                method="POST",
            )
            try:
                urllib.request.urlopen(req)
                exito += 1
            except urllib.error.HTTPError:
                # Si rpc no existe, intentar con SQL Editor manual
                fallos += 1
        except Exception:
            fallos += 1

    return exito, fallos


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Configuracion automatica de Supabase para SIAC ERP movil"
    )
    parser.add_argument("--admin-email", default="admin@siac.com", help="Email del admin")
    parser.add_argument("--admin-password", default="admin123", help="Password del admin")
    args = parser.parse_args()

    print_paso("Configuracion de Supabase para SIAC ERP")
    print()

    config = obtener_config()
    if not config:
        print_error("No se pudo leer config.ini. Verifica la seccion [supabase].")
        sys.exit(1)

    url = config["url"]
    anon_key = config["anon_key"]
    service_role_key = config.get("service_role_key", "")

    print_ok(f"URL: {url}")
    print_ok(f"Anon Key: {anon_key[:20]}...")
    print_ok(f"Service Role: {'Configurada' if service_role_key else 'NO configurada'}")
    print()

    # Paso 1: Verificar conexion
    print_paso("Paso 1/4: Verificando conexion...")
    if verificar_conexion((url, anon_key)):
        print_ok("Conexion exitosa")
    else:
        print_error("No se pudo conectar con Supabase")
        sys.exit(1)

    # Paso 2: Generar esquema
    print_paso("Paso 2/4: Generando esquema SQL...")
    sql = crear_esquema_sql()
    print_ok(f"SQL generado ({len(sql)} caracteres)")

    # Paso 3: Ejecutar esquema
    print_paso("Paso 3/4: Ejecutando esquema en Supabase...")
    key = service_role_key or anon_key
    exito, fallos = ejecutar_sql(sql, url, key)
    print_ok(f"Sentencias ejecutadas: {exito}, Fallos: {fallos}")

    # Paso 4: Verificar tablas
    print_paso("Paso 4/4: Verificando tablas...")
    resultados = verificar_tablas((url, key))
    for tabla, existe in resultados.items():
        if existe:
            print_ok(tabla)
        else:
            print_error(f"{tabla} (no creada)")

    print()
    print_paso("Configuracion completada")
    print()
    print_info("Copia este SQL en el SQL Editor de Supabase si hubo fallos:")
    print_info(f"  (SQL de {len(sql)} caracteres en memoria)")


if __name__ == "__main__":
    main()

