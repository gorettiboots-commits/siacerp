#!/usr/bin/env python3
"""Sincroniza datos existentes del escritorio a Supabase.

Ejecutar UNA VEZ para cargar los datos iniciales que el movil necesita:
  python scripts/sincronizar_datos_movil.py

Requiere:
  - config.ini con [supabase] url, service_role_key, empresa_id
  - Tablas locales con datos (clientes, pedidos, programacion)
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_manager import DatabaseManager
from src.utils.supabase_service import SupabaseService


# Mapeo: tabla_local -> tabla_supabase
TABLAS = {
    'clientes': {
        'remota': 'clientes_movil',
        'columnas': ['id', 'nombre', 'rfc', 'nombre_comercial', 'telefono',
                     'email', 'direccion', 'activo'],
        'where': 'activo = 1',
    },
    'pedidos_cliente': {
        'remota': 'pedidos_cliente_movil',
        'columnas': ['id', 'folio', 'folio_pedido', 'cliente_id', 'fecha_pedido',
                     'fecha_programado', 'total_pares', 'estatus', 'suela', 'horma',
                     'observaciones'],
        'where': '1=1',
        'join': 'LEFT JOIN clientes ON clientes.id = pedidos_cliente.cliente_id',
        'join_cols': {
            'cliente_nombre': 'clientes.nombre',
        },
    },
    'detalle_pedido_cliente': {
        'remota': 'detalle_pedido_cliente_movil',
        'columnas': ['id', 'pedido_id', 'modelo', 'piel', 'color'],
        'where': '1=1',
    },
    'detalle_pedido_cliente_puntos': {
        'remota': 'detalle_pedido_puntos_movil',
        'columnas': ['id', 'detalle_id', 'talla_id', 'pares'],
        'where': '1=1',
        'join': 'LEFT JOIN tallas_catalogo ON tallas_catalogo.id = detalle_pedido_cliente_puntos.talla_id',
        'join_cols': {
            'talla': 'tallas_catalogo.talla',
        },
    },
    'programacion_semana': {
        'remota': 'programacion_semana_movil',
        'columnas': ['id', 'nombre', 'fecha_inicio', 'orden', 'activo'],
        'where': 'activo = 1',
    },
    'programacion_lineas': {
        'remota': 'programacion_lineas_movil',
        'columnas': ['id', 'semana_id', 'orden', 'folio_prog', 'folio_pedido',
                     'cliente', 'modelo', 'piel', 'color', 'fecha_prog',
                     'total_pares', 'estatus', 'pedido_id', 'detalle_pedido_id'],
        'where': '1=1',
    },
    'programacion_linea_tallas': {
        'remota': 'programacion_linea_tallas_movil',
        'columnas': ['id', 'linea_id', 'talla', 'orden', 'pares'],
        'where': '1=1',
    },
}


def sincronizar_tabla(db, supabase, tabla_local, config, empresa_id):
    """Sincroniza una tabla local a Supabase."""
    columnas = config['columnas']
    remota = config['remota']
    where = config.get('where', '1=1')
    join = config.get('join', '')

    # Construir query
    join_cols = config.get('join_cols', {})
    if join:
        cols_select = []
        for c in columnas:
            cols_select.append(f"{tabla_local}.{c}")
        for alias, expr in join_cols.items():
            cols_select.append(f"{expr} AS {alias}")
        cols_sql = ', '.join(cols_select)
        query = f"SELECT {cols_sql} FROM {tabla_local} {join} WHERE {where}"
    else:
        cols_sql = ', '.join(columnas)
        query = f"SELECT {cols_sql} FROM {tabla_local} WHERE {where}"

    filas = db.fetch_all(query)

    if not filas:
        print(f"  {tabla_local}: 0 registros (saltando)")
        return 0

    # Preparar datos para Supabase
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc).isoformat()
    datos_enviar = []
    for fila in filas:
        registro = dict(fila)
        registro['empresa_id'] = empresa_id
        # Agregar timestamps si la tabla remota los requiere
        if 'updated_at' not in registro:
            registro['updated_at'] = ahora
        if 'created_at' not in registro:
            registro['created_at'] = ahora
        # Convertir tipos que Supabase no acepta directamente
        for k, v in registro.items():
            if isinstance(v, (bytes, bytearray)):
                registro[k] = str(v)
            elif isinstance(v, set):
                registro[k] = list(v)
        datos_enviar.append(registro)

    # Enviar en lotes de 50
    lote_size = 50
    total_enviados = 0
    for i in range(0, len(datos_enviar), lote_size):
        lote = datos_enviar[i:i + lote_size]
        resultado = supabase.sincronizar_tabla(remota, lote)
        if resultado.get('ok'):
            total_enviados += len(lote)
            print(f"  {remota}: {len(lote)} registros enviados")
        else:
            print(f"  {remota}: ERROR - {resultado.get('error', 'desconocido')}")
            # Intentar uno por uno
            for registro in lote:
                r2 = supabase.sincronizar_tabla(remota, [registro])
                if r2.get('ok'):
                    total_enviados += 1
                else:
                    print(f"    ERROR registro {registro.get('id')}: {r2.get('error')}")

    return total_enviados


def main():
    print("=" * 60)
    print("  SIAC ERP - Sincronizacion de datos al movil")
    print("=" * 60)
    print()

    # Verificar Supabase
    supabase = SupabaseService()
    if not supabase.configurado:
        print("ERROR: Supabase no esta configurado.")
        print("Verifica [supabase] en config.ini")
        sys.exit(1)

    print(f"Supabase: {supabase.url}")
    print(f"Empresa ID: {supabase.empresa_id}")
    print()

    db = DatabaseManager()
    empresa_id = supabase.empresa_id

    total = 0
    for tabla_local, config in TABLAS.items():
        print(f"Sincronizando {tabla_local}...")
        n = sincronizar_tabla(db, supabase, tabla_local, config, empresa_id)
        total += n
        print()

    print("=" * 60)
    print(f"  COMPLETADO: {total} registros sincronizados")
    print("=" * 60)
    print()
    print("Ahora abre la app movil y haz pull-to-refresh.")


if __name__ == '__main__':
    main()
