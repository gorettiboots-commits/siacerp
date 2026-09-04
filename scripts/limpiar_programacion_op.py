#!/usr/bin/env python3
"""Limpia todas las programaciones y órdenes de producción de la base de datos.

Elimina:
  - programacion_linea_tallas
  - programacion_lineas
  - incidencias_produccion
  - seguimiento_produccion
  - matriz_tallas_op
  - ordenes_produccion

Esto permite que todas las líneas de todos los pedidos vuelvan a estar
disponibles para programar.
"""

import sqlite3
import sys
from pathlib import Path


def limpiar(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=OFF")
    cursor = conn.cursor()

    tablas = [
        ("programacion_linea_tallas", "Tallas de programación"),
        ("programacion_lineas", "Líneas de programación"),
        ("incidencias_produccion", "Incidencias de producción"),
        ("seguimiento_produccion", "Seguimiento de producción"),
        ("matriz_tallas_op", "Matriz de tallas OP"),
        ("ordenes_produccion", "Órdenes de producción"),
    ]

    for tabla, descripcion in tablas:
        try:
            antes = cursor.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
            cursor.execute(f"DELETE FROM {tabla}")
            print(f"  [OK] {descripcion}: {antes} registros eliminados")
        except Exception as e:
            print(f"  [ERR] {descripcion}: error - {e}")

    conn.commit()
    conn.execute("PRAGMA foreign_keys=ON")
    conn.close()
    print("\n[LIMPIO] Todas las lineas de pedidos estan disponibles para programar.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
    else:
        ruta = str(Path(__file__).resolve().parent.parent / "goretti_erp.db")

    if not Path(ruta).exists():
        print(f"❌ No se encontró la base de datos: {ruta}")
        sys.exit(1)

    print(f"Base de datos: {ruta}")
    print("Eliminando programaciones y ordenes de produccion...\n")
    limpiar(ruta)
