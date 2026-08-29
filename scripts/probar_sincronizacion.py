"""
Prueba de sincronización - Versión offline.

Este script verifica que la configuración esté correcta y prepara
los datos para sincronizar cuando haya conectividad.

Uso:
    python scripts/probar_sincronizacion.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.database.db_manager import DatabaseManager


def verificar_configuracion():
    """Verifica que la configuración de Supabase esté completa."""
    print("1. Verificando configuracion...")
    
    config_path = RAIZ / "config.ini"
    if not config_path.exists():
        print("  [ERROR] config.ini no encontrado")
        return False
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(str(config_path))
        
        if not config.has_section("supabase"):
            print("  [ERROR] Seccion [supabase] no encontrada")
            return False
        
        url = config.get("supabase", "url", fallback="").strip()
        key = config.get("supabase", "anon_key", fallback="").strip()
        
        if not url:
            print("  [ERROR] URL de Supabase vacia")
            return False
        
        if not key or len(key) < 20:
            print("  [ERROR] API Key invalida")
            return False
        
        print(f"  [OK] URL: {url[:40]}...")
        print(f"  [OK] API Key: {key[:20]}...")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error al leer config: {e}")
        return False


def verificar_datos_locales():
    """Verifica que haya datos en la BD local para sincronizar."""
    print("\n2. Verificando datos locales...")
    
    try:
        db = DatabaseManager()
        
        # Contar insumos
        insumos = db.fetch_one("SELECT COUNT(*) as total FROM insumos WHERE activo = 1")
        total_insumos = insumos["total"] if insumos else 0
        print(f"  [OK] Insumos activos: {total_insumos}")
        
        # Contar órdenes de compra
        ocs = db.fetch_one("SELECT COUNT(*) as total FROM ordenes_compra")
        total_ocs = ocs["total"] if ocs else 0
        print(f"  [OK] Ordenes de compra: {total_ocs}")
        
        # Contar órdenes de producción
        ops = db.fetch_one("SELECT COUNT(*) as total FROM ordenes_produccion WHERE estatus != 'terminada'")
        total_ops = ops["total"] if ops else 0
        print(f"  [OK] Ordenes de produccion activas: {total_ops}")
        
        # Contar seguimiento
        seguimientos = db.fetch_one(
            "SELECT COUNT(*) as total FROM seguimiento_produccion sp "
            "JOIN ordenes_produccion op ON op.id = sp.orden_produccion_id "
            "WHERE op.estatus != 'terminada'"
        )
        total_seg = seguimientos["total"] if seguimientos else 0
        print(f"  [OK] Seguimientos de produccion: {total_seg}")
        
        # Contar tallas
        tallas = db.fetch_one("SELECT COUNT(*) as total FROM tallas_catalogo")
        total_tallas = tallas["total"] if tallas else 0
        print(f"  [OK] Tallas en catalogo: {total_tallas}")
        
        total = total_insumos + total_ocs + total_ops + total_seg + total_tallas
        print(f"\n  Total de registros para sincronizar: {total}")
        
        return total > 0
        
    except Exception as e:
        print(f"  [ERROR] Error al verificar datos: {e}")
        return False


def preparar_datos_sincronizacion():
    """Prepara los datos en formato JSON para sincronización posterior."""
    print("\n3. Preparando datos para sincronizacion...")
    
    try:
        db = DatabaseManager()
        datos = {
            "fecha": datetime.now().isoformat(),
            "tablas": {}
        }
        
        # Insumos
        insumos = db.fetch_all(
            "SELECT id, codigo, nombre, categoria, unidad_medida, "
            "stock_actual, stock_minimo, activo "
            "FROM insumos WHERE activo = 1 ORDER BY codigo LIMIT 100"
        )
        datos["tablas"]["insumos_movil"] = [
            {
                "id": f["id"],
                "codigo": f["codigo"],
                "nombre": f["nombre"],
                "categoria": f["categoria"],
                "unidad_medida": f["unidad_medida"],
                "stock_actual": f["stock_actual"],
                "stock_minimo": f["stock_minimo"],
                "activo": True,
            }
            for f in insumos
        ]
        print(f"  [OK] Insumos: {len(datos['tablas']['insumos_movil'])} registros")
        
        # Órdenes de compra
        ocs = db.fetch_all(
            "SELECT oc.id, oc.folio, oc.fecha_emision, oc.estatus, oc.total, "
            "oc.metodo_pago, oc.solo_remision, oc.tipo, oc.observaciones, "
            "p.nombre AS proveedor_nombre "
            "FROM ordenes_compra oc "
            "LEFT JOIN proveedores p ON p.id = oc.proveedor_id "
            "ORDER BY oc.id DESC LIMIT 50"
        )
        datos["tablas"]["ordenes_compra_movil"] = [
            {
                "id": f["id"],
                "folio": f["folio"],
                "proveedor_nombre": f.get("proveedor_nombre") or "Sin proveedor",
                "fecha_emision": f.get("fecha_emision"),
                "estatus": f["estatus"],
                "total": f["total"],
                "metodo_pago": f["metodo_pago"],
                "solo_remision": bool(f["solo_remision"]),
                "tipo": f["tipo"],
                "observaciones": f.get("observaciones"),
            }
            for f in ocs
        ]
        print(f"  [OK] Ordenes de compra: {len(datos['tablas']['ordenes_compra_movil'])} registros")
        
        # Órdenes de producción
        ops = db.fetch_all(
            "SELECT op.id, op.folio, op.total_pares, op.fecha_inicio, "
            "op.fecha_entrega, op.prioridad, op.estatus, "
            "m.nombre AS modelo_nombre, v.codigo_variante "
            "FROM ordenes_produccion op "
            "LEFT JOIN variantes v ON v.id = op.variante_id "
            "LEFT JOIN modelos m ON m.id = v.modelo_id "
            "WHERE op.estatus != 'terminada' "
            "ORDER BY op.fecha_entrega ASC LIMIT 50"
        )
        datos["tablas"]["ordenes_produccion_movil"] = [
            {
                "id": f["id"],
                "folio": f["folio"],
                "modelo_nombre": f.get("modelo_nombre") or "",
                "codigo_variante": f.get("codigo_variante") or "",
                "total_pares": f["total_pares"],
                "fecha_inicio": f.get("fecha_inicio"),
                "fecha_entrega": f.get("fecha_entrega"),
                "prioridad": f["prioridad"],
                "estatus": f["estatus"],
            }
            for f in ops
        ]
        print(f"  [OK] Ordenes de produccion: {len(datos['tablas']['ordenes_produccion_movil'])} registros")
        
        # Guardar en archivo
        output_path = RAIZ / "mobile" / "supabase" / "datos_sincronizacion.json"
        with open(str(output_path), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        
        print(f"\n  [OK] Datos guardados en: {output_path}")
        print(f"  [OK] Tamano del archivo: {output_path.stat().st_size / 1024:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Error al preparar datos: {e}")
        return False


def main():
    print("=" * 60)
    print("SIAC ERP - Prueba de Sincronizacion (Offline)")
    print("=" * 60)
    
    # 1. Verificar configuración
    if not verificar_configuracion():
        print("\n[FIN] Configuracion incompleta")
        sys.exit(1)
    
    # 2. Verificar datos locales
    if not verificar_datos_locales():
        print("\n[FIN] No hay datos para sincronizar")
        sys.exit(1)
    
    # 3. Preparar datos
    if not preparar_datos_sincronizacion():
        print("\n[FIN] Error al preparar datos")
        sys.exit(1)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("\n[OK] Configuracion verificada")
    print("[OK] Datos locales verificados")
    print("[OK] Datos preparados para sincronizacion")
    print("\nArchivos generados:")
    print("  - mobile/supabase/datos_sincronizacion.json")
    print("\nPara sincronizar cuando haya conexion:")
    print("  1. Verificar que las tablas existan en Supabase")
    print("  2. Ejecutar: python scripts/sincronizar_supabase.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
