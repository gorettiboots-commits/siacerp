#!/usr/bin/env python3
"""Poblar la base de datos con datos de prueba realistas (Ene - Sep 2026).

Crea registros en:
- Proveedores, Insumos, Modelos, Variantes, Fichas Técnicas
- Clientes (ya existentes, solo agrega si faltan)
- Pedidos de cliente con detalle y pares por talla
- Programación semanal con líneas
- Órdenes de producción con seguimiento por estación
- Órdenes de compra con detalle

Uso:
    .python_embed/python.exe scripts/poblar_base_datos.py
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "goretti_erp.db")
random.seed(42)  # Reproducible

# ── Catálogos base ─────────────────────────────────────────
MODELOS = [
    ("MOD-0002", "9209"),
    ("MOD-0003", "9210"),
    ("MOD-0004", "9213"),
    ("MOD-0005", "9215"),
    ("MOD-0006", "9218"),
    ("MOD-0007", "9228"),
    ("MOD-0008", "9231"),
    ("MOD-0009", "1001"),
    ("MOD-0010", "1002"),
    ("MOD-0011", "9203"),
    ("MOD-0012", "9128"),
    ("MOD-0013", "9211"),
    ("MOD-0014", "3000"),
]

COLORES = ["NEGRO", "CAMEL", "CAFÉ", "ROJO", "BLANCO", "AZUL", "GRIS"]
PIELES = ["CRAZY", "CINCELADO", "NUCA", "LIZARD", "PITÓN", "SHEDRON", "PIEL", "PATENTADO", "SUEDE"]
TIPOS_SUELA = ["RX", "FLEX", "Crepe", "Liso", "Tacos"]

INSUMOS_DATA = [
    # (codigo, nombre, categoria, unidad, stock_min)
    # Piel
    ("PIEL-001", "Piel CRAZY Negro", "Piel", "dm2", 500),
    ("PIEL-002", "Piel CRAZY Camel", "Piel", "dm2", 500),
    ("PIEL-003", "Piel CRAZY Café", "Piel", "dm2", 400),
    ("PIEL-004", "Piel CINCELADO Negro", "Piel", "dm2", 300),
    ("PIEL-005", "Piel CINCELADO Camel", "Piel", "dm2", 250),
    ("PIEL-006", "Piel NUCA Café", "Piel", "dm2", 200),
    ("PIEL-007", "Piel LIZARD Negro", "Piel", "dm2", 150),
    ("PIEL-008", "Piel PITÓN Café", "Piel", "dm2", 120),
    ("PIEL-009", "Piel SHEDRON Café", "Piel", "dm2", 180),
    ("PIEL-010", "Piel PATENTADO Negro", "Piel", "dm2", 100),
    # Forro
    ("FORR-001", "Forro Textil Negro", "Forro", "dm2", 600),
    ("FORR-002", "Forro Textil Camel", "Forro", "dm2", 400),
    ("FORR-003", "Forro Cuero Café", "Forro", "dm2", 200),
    ("FORR-004", "Forro Sintético Blanco", "Forro", "dm2", 300),
    # Suela
    ("SUEL-001", "Suela RX Hombre 23-27", "Suelas", "pieza", 2000),
    ("SUEL-002", "Suela RX Hombre 27-31", "Suelas", "pieza", 1500),
    ("SUEL-003", "Suela Flex Unisex 22-26", "Suelas", "pieza", 1800),
    ("SUEL-004", "Suela Crepe Hombre", "Suelas", "pieza", 1200),
    ("SUEL-005", "Suela Liso Negro 23-28", "Suelas", "pieza", 900),
    ("SUEL-006", "Suela Tacos Mujer", "Suelas", "pieza", 600),
    # Tacon
    ("TACN-001", "Tacón 3cm Hombre", "Tacon", "pieza", 800),
    ("TACN-002", "Tacón 5cm Mujer", "Tacon", "pieza", 400),
    ("TACN-003", "Tacón 7cm Mujer", "Tacon", "pieza", 300),
    # Plantilla
    ("PLAN-001", "Plantilla Eva 3mm", "Plantilla", "pieza", 3000),
    ("PLAN-002", "Plantilla Cuero 2mm", "Plantilla", "pieza", 1500),
    ("PLAN-003", "Plantilla Memory Foam", "Plantilla", "pieza", 1000),
    # Herrajes y accesorios
    ("HERR-001", "Hebilla cromada", "Herraje", "pieza", 2000),
    ("HERR-002", "Ojales metálicos", "Herraje", "pieza", 5000),
    ("HERR-003", "Cierre metálico", "Herraje", "pieza", 800),
    # Hilos
    ("HILO-001", "Hilo Nylon #40 Negro", "Hilo", "rollo", 100),
    ("HILO-002", "Hilo Nylon #40 Café", "Hilo", "rollo", 80),
    ("HILO-003", "Hilo Nylon #60 Blanco", "Hilo", "rollo", 60),
    # Tubo / Entretela
    ("TUBO-001", "Tubo Espuma 4mm", "Tubo", "metro", 200),
    ("TUBO-002", "Tubo Goma Eva 3mm", "Tubo", "metro", 150),
    ("TUBO-003", "Entretela Rígida", "Tubo", "metro", 100),
    # Caja y empaque
    ("CAJA-001", "Caja Calzado Estándar", "Empaque", "pieza", 5000),
    ("CAJA-002", "Bolsa Polipropileno", "Empaque", "pieza", 8000),
    ("CAJA-003", "Papel de Relleno", "Empaque", "pieza", 3000),
    ("CAJA-004", "Etiqueta Código Barras", "Empaque", "pieza", 10000),
]

PROVEEDORES_DATA = [
    ("PGR010101AAA", "CUEROS DEL NORTE", "Cueros del Norte SA", "8181234567", "ventas@cuerosnorte.com"),
    ("PSU020202BBB", "SUELAS DEL CENTRO", "Suelas del Centro SC", "3334567890", "pedidos@suelacentro.com"),
    ("PTE030303CCC", "TEXTILES GOYESCOS", "Textiles Goyescos SA de CV", "8189876543", "ventas@textilesgoy.com"),
    ("PHJ040404DDD", "HERRAJES PRECISION", "Herrajes Precisión SA", "5551234567", "ventas@herrajespre.com"),
    ("PEM050505EEE", "EMPAQUES Y MÁS", "Empaques y Más SC", "3339876543", "pedidos@empaquesymas.com"),
]

# Tallas comunes para calzado masculino/femenino (por talla_id)
TALLAS_M = [(18, "23.5"), (19, "24"), (20, "24.5"), (21, "25"), (22, "25.5"),
            (23, "26"), (24, "26.5"), (25, "27"), (26, "27.5"), (27, "28")]
TALLAS_F = [(36, "16"), (37, "16.5"), (38, "17"), (39, "18"), (40, "19"),
            (41, "20"), (42, "21"), (48, "17.5"), (50, "18.5"), (52, "19.5")]

# Los clientes ya existen, usamos sus IDs
CLIENTES_IDS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 285]


def crear_proveedores(cur):
    """Insertar proveedores adicionales."""
    print("→ Creando proveedores...")
    for rfc, nombre, comercial, tel, email in PROVEEDORES_DATA:
        cur.execute(
            "INSERT OR IGNORE INTO proveedores (rfc, nombre, nombre_comercial, telefono, email) "
            "VALUES (?, ?, ?, ?, ?)",
            (rfc, nombre, comercial, tel, email)
        )
    conn.commit()
    print(f"  {len(PROVEEDORES_DATA)} proveedores insertados/ignorados")


def crear_insumos(cur):
    """Insertar insumos de materia prima."""
    print("→ Creando insumos...")
    for codigo, nombre, cat, unidad, stock_min in INSUMOS_DATA:
        stock = random.randint(stock_min, stock_min * 3)
        cur.execute(
            "INSERT OR IGNORE INTO insumos (codigo, nombre, categoria, unidad_medida, stock_actual, stock_minimo) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (codigo, nombre, cat, unidad, stock, stock_min)
        )
    conn.commit()
    print(f"  {len(INSUMOS_DATA)} insumos insertados/ignorados")


def crear_modelos_variantes(cur):
    """Crear modelos y variantes (colores × piel)."""
    print("→ Creando modelos y variantes...")
    modelo_ids = {}

    for codigo, nombre in MODELOS:
        cur.execute(
            "INSERT OR IGNORE INTO modelos (codigo, nombre, descripcion) VALUES (?, ?, ?)",
            (codigo, nombre, f"Modelo de zapato {nombre}")
        )
        cur.execute("SELECT id FROM modelos WHERE codigo=?", (codigo,))
        row = cur.fetchone()
        if row:
            modelo_ids[codigo] = row[0]
            # Crear variantes: 3 colores × 2 pieles por modelo
            colores_sel = random.sample(COLORES, 3)
            pieles_sel = random.sample(PIELES, 2)
            for color in colores_sel:
                for piel in pieles_sel:
                    cod_var = f"{codigo}-{color[:4]}-{piel[:4]}"
                    cur.execute(
                        "INSERT OR IGNORE INTO variantes (modelo_id, color, piel, talla, codigo_variante) "
                        "VALUES (?, ?, '', ?, ?)",
                        (modelo_ids[codigo], color, piel, cod_var)
                    )

    conn.commit()
    print(f"  {len(modelo_ids)} modelos, variantes creadas")


def crear_fichas_tecnicas(cur):
    """Crear fichas técnicas para los modelos."""
    print("→ Creando fichas técnicas...")
    cur.execute("SELECT id, codigo, nombre FROM modelos")
    modelos = cur.fetchall()

    for mid, codigo, nombre in modelos:
        if codigo == "FT-TEST":
            continue
        colores = random.sample(COLORES, 2)
        cur.execute(
            "INSERT OR IGNORE INTO fichas_tecnicas "
            "(modelo_id, proyecto, etapa, id_diseno, color_nombre, "
            "piel_corte_1, forro, suela, plantilla, herraje, acabado, caja) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, f"Proyecto {nombre}", "PRODUCCIÓN", f"DIS-{codigo}",
             "/".join(colores),
             random.choice(PIELES), "Textil", random.choice(TIPOS_SUELA),
             "Eva 3mm", "Hebilla + Ojales", "Pintura + Cepillado",
             "Caja Estándar")
        )
    conn.commit()
    print("  Fichas técnicas creadas")


def crear_insumos_modelo(cur):
    """Asociar insumos a modelos (lista de materiales BOM)."""
    print("→ Creando lista de materiales...")
    cur.execute("SELECT id, codigo FROM modelos WHERE codigo != 'FT-TEST'")
    modelos = cur.fetchall()

    cur.execute("SELECT id, codigo, categoria FROM insumos")
    insumos = cur.fetchall()
    insumos_por_cat = {}
    for iid, icod, icat in insumos:
        insumos_por_cat.setdefault(icat, []).append(iid)

    for mid, mcodigo in modelos:
        # Piel: 2 insumos
        for iid in random.sample(insumos_por_cat.get("Piel", [1]), min(2, len(insumos_por_cat.get("Piel", [1])))):
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, iid, round(random.uniform(0.5, 2.0), 2), "dm2"))
        # Forro: 1
        forro_list = insumos_por_cat.get("Forro", [11])
        if forro_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(forro_list), round(random.uniform(0.3, 1.0), 2), "dm2"))
        # Suela: 1
        suela_list = insumos_por_cat.get("Suelas", [15])
        if suela_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(suela_list), 1.0, "pieza"))
        # Plantilla: 1
        plan_list = insumos_por_cat.get("Plantilla", [25])
        if plan_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(plan_list), 1.0, "pieza"))
        # Hilo: 1
        hilo_list = insumos_por_cat.get("Hilo", [31])
        if hilo_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(hilo_list), 0.1, "rollo"))
        # Tubo: 1
        tubo_list = insumos_por_cat.get("Tubo", [34])
        if tubo_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(tubo_list), 0.3, "metro"))
        # Caja: 1
        caja_list = insumos_por_cat.get("Empaque", [38])
        if caja_list:
            cur.execute("INSERT OR IGNORE INTO lista_materiales (modelo_id, insumo_id, cantidad_por_par, unidad) "
                        "VALUES (?, ?, ?, ?)", (mid, random.choice(caja_list), 1.0, "pieza"))

    conn.commit()
    print("  Lista de materiales creada")


def _next_folio(cur, tabla, prefijo):
    """Obtener el siguiente folio para una tabla."""
    cur.execute(f"SELECT MAX(folio) FROM {tabla}")
    row = cur.fetchone()
    if row and row[0]:
        num = int(row[0].split("-")[1]) + 1
    else:
        num = 1
    return f"{prefijo}-{num:04d}"


def _fecha_aleatoria(inicio, fin):
    """Fecha aleatoria entre dos fechas."""
    delta = (fin - inicio).days
    if delta <= 0:
        return inicio
    return inicio + timedelta(days=random.randint(0, delta))


def crear_pedidos(cur):
    """Crear pedidos de cliente de enero a septiembre 2026."""
    print("→ Creando pedidos de cliente (Ene-Sep 2026)...")

    modelos_nombres = ["9209", "9210", "9213", "9215", "9218", "9228", "9231",
                       "1001", "1002", "9203", "9128", "9211", "3000"]
    pieles = ["CRAZY", "CINCELADO", "NUCA", "LIZARD", "PITÓN", "SHEDRON", "PIEL"]
    colores = ["NEGRO/NEGRO", "CAMEL/CAMEL", "CAFÉ/CAFÉ", "CAFÉ/CAMEL",
               "NEGRO/CAFÉ", "CAMEL/CAFÉ", "COÑAC/CAMEL", "COÑAC/CAFÉ"]
    tallas_corrida = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27]  # 23.5 a 27
    estatus_pedidos = ["pendiente", "programado"]

    inicio = datetime(2026, 1, 1)
    fin = datetime(2026, 9, 3)

    # Crear ~150 pedidos distribuidos por mes
    pedidos_por_mes = {
        1: 15, 2: 15, 3: 18, 4: 20, 5: 25, 6: 20, 7: 18, 8: 15, 9: 10
    }

    total_pedidos = 0
    for mes, cantidad in pedidos_por_mes.items():
        for i in range(cantidad):
            fecha = datetime(2026, mes, random.randint(1, 28))
            cliente_id = random.choice(CLIENTES_IDS)
            folio = _next_folio(cur, "pedidos_cliente", "PED")

            # Para pedidos antes de agosto: programado; después: pendiente
            estatus = "programado" if mes < 8 else random.choice(["pendiente", "programado"])

            num_detalles = random.randint(1, 4)
            total_pares = 0

            cur.execute(
                "INSERT INTO pedidos_cliente (folio, folio_pedido, cliente_id, fecha_pedido, estatus, total_pares, suela, horma, observaciones) "
                "VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)",
                (folio, f"PEDCLI-{random.randint(1000,9999)}", cliente_id,
                 fecha.strftime("%Y-%m-%d"), estatus,
                 random.choice(["RX", "Flex", "Crepe"]),
                 f"Horma {random.randint(1,20)}",
                 "Pedido de prueba")
            )
            pedido_id = cur.lastrowid

            for _ in range(num_detalles):
                modelo = random.choice(modelos_nombres)
                piel = random.choice(pieles)
                color = random.choice(colores)

                cur.execute(
                    "INSERT INTO detalle_pedido_cliente (pedido_id, modelo, piel, color) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, modelo, piel, color)
                )
                detalle_id = cur.lastrowid

                # Pares por talla: corrida 23.5-27
                pares_total_linea = 0
                for talla_id in tallas_corrida:
                    pares = random.choice([0, 5, 10, 15, 20, 25, 30, 40])
                    if pares > 0:
                        cur.execute(
                            "INSERT OR IGNORE INTO detalle_pedido_cliente_puntos "
                            "(detalle_id, talla_id, pares) VALUES (?, ?, ?)",
                            (detalle_id, talla_id, pares)
                        )
                        pares_total_linea += pares

                total_pares += pares_total_linea

            cur.execute("UPDATE pedidos_cliente SET total_pares=? WHERE id=?",
                        (total_pares, pedido_id))
            total_pedidos += 1

    conn.commit()
    print(f"  {total_pedidos} pedidos creados")


def crear_programacion_semanal(cur):
    """Crear semanas y líneas de programación."""
    print("→ Creando programación semanal...")
    # Ya existen semanas (id hasta 99). Crear más para enero-sep 2026
    semanas_creadas = 0
    inicio = datetime(2025, 12, 29)  # Lunes antes del 1 de enero
    fin = datetime(2026, 9, 7)

    cur.execute("SELECT MAX(id) FROM programacion_semana")
    max_id = cur.fetchone()[0] or 0

    current = inicio
    semana_num = 0
    while current <= fin:
        semana_num += 1
        fin_semana = current + timedelta(days=5)
        nombre = f"{current.day} {current.strftime('%B')} - {fin_semana.day} {fin_semana.strftime('%B')}"
        cur.execute(
            "INSERT OR IGNORE INTO programacion_semana (nombre, fecha_inicio, orden) "
            "VALUES (?, ?, ?)",
            (nombre, current.strftime("%Y-%m-%d"), semana_num)
        )
        semanas_creadas += 1
        current += timedelta(days=7)

    conn.commit()
    print(f"  {semanas_creadas} semanas creadas")

    # Crear líneas de programación para pedidos programados
    print("→ Creando líneas de programación...")
    cur.execute(
        "SELECT p.id, p.folio, c.nombre, dpc.modelo, dpc.piel, dpc.color, "
        "p.fecha_pedido, p.total_pares "
        "FROM pedidos_cliente p "
        "JOIN clientes c ON c.id = p.cliente_id "
        "JOIN detalle_pedido_cliente dpc ON dpc.pedido_id = p.id "
        "WHERE p.estatus = 'programado'"
    )
    detalles = cur.fetchall()

    # Obtener todas las semanas
    cur.execute("SELECT id, fecha_inicio FROM programacion_semana ORDER BY fecha_inicio")
    semanas = cur.fetchall()
    semana_fechas = {s[0]: datetime.strptime(s[1], "%Y-%m-%d") for s in semanas}

    lineas_creadas = 0
    for pedido_id, folio, cliente, modelo, piel, color, fecha_pedido, total_pares in detalles:
        if not fecha_pedido:
            continue
        fp = datetime.strptime(fecha_pedido[:10], "%Y-%m-%d")

        # Encontrar la semana correspondiente
        semana_id = None
        for sid, sf in semana_fechas.items():
            if sf <= fp < sf + timedelta(days=7):
                semana_id = sid
                break
        if not semana_id:
            # Usar la semana más cercana después de la fecha
            for sid, sf in sorted(semana_fechas.items(), key=lambda x: x[1]):
                if sf >= fp - timedelta(days=7):
                    semana_id = sid
                    break
        if not semana_id:
            continue

        folio_prog = f"{random.randint(100, 999)}"
        cur.execute(
            "INSERT INTO programacion_lineas "
            "(semana_id, orden, folio_prog, folio_pedido, cliente, modelo, piel, color, "
            "fecha_prog, total_pares, estatus, pedido_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (semana_id, lineas_creadas + 1, folio_prog, folio, cliente,
             modelo, piel, color, fecha_pedido[:10],
             total_pares, "programado", pedido_id)
        )
        linea_id = cur.lastrowid
        lineas_creadas += 1

        # Agregar tallas
        for tid, tnum in TALLAS_M:
            pares = random.choice([0, 5, 10, 15, 20, 25])
            if pares > 0:
                cur.execute(
                    "INSERT OR IGNORE INTO programacion_linea_tallas (linea_id, talla, pares) "
                    "VALUES (?, ?, ?)",
                    (linea_id, tnum, pares)
                )

    conn.commit()
    print(f"  {lineas_creadas} líneas de programación creadas")


def crear_ordenes_compra(cur):
    """Crear órdenes de compra mensuales."""
    print("→ Creando órdenes de compra...")
    proveedores_ids = []
    cur.execute("SELECT id FROM proveedores")
    for row in cur.fetchall():
        proveedores_ids.append(row[0])

    insumos_ids = []
    cur.execute("SELECT id FROM insumos")
    for row in cur.fetchall():
        insumos_ids.append(row[0])

    oc_creadas = 0
    for mes in range(1, 10):  # Ene a Sep
        num_oc = random.randint(2, 4)
        for i in range(num_oc):
            fecha = datetime(2026, mes, random.randint(1, 25))
            folio = _next_folio(cur, "ordenes_compra", "OC")
            proveedor = random.choice(proveedores_ids)
            estatus = "recibida" if mes < 8 else random.choice(["pendiente", "recibida"])

            cur.execute(
                "INSERT INTO ordenes_compra "
                "(folio, proveedor_id, fecha_emision, estatus, total, observaciones, tipo) "
                "VALUES (?, ?, ?, ?, 0, ?, 'orden')",
                (folio, proveedor, fecha.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                 estatus, f"Compra mensual {fecha.strftime('%B %Y')}")
            )
            oc_id = cur.lastrowid
            total = 0

            num_detalle = random.randint(3, 8)
            for _ in range(num_detalle):
                insumo = random.choice(insumos_ids)
                cantidad = round(random.uniform(50, 500), 0)
                precio = round(random.uniform(15, 250), 2)

                cur.execute(
                    "INSERT INTO detalle_orden_compra "
                    "(orden_compra_id, insumo_id, cantidad, precio_unitario, proveedor_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (oc_id, insumo, cantidad, precio, proveedor)
                )
                detalle_id = cur.lastrowid
                total += cantidad * precio

                # Pares por punto/talla (solo suelas)
                cur.execute("SELECT categoria FROM insumos WHERE id=?", (insumo,))
                cat_row = cur.fetchone()
                if cat_row and cat_row[0] == "Suelas":
                    for tid, tnum in TALLAS_M[:random.randint(4, 8)]:
                        pares = random.randint(10, 100)
                        cur.execute(
                            "INSERT OR IGNORE INTO detalle_orden_compra_puntos "
                            "(detalle_id, talla_id, pares, precio_unitario) "
                            "VALUES (?, ?, ?, ?)",
                            (detalle_id, tid, pares, round(precio / 2, 2))
                        )

            cur.execute("UPDATE ordenes_compra SET total=? WHERE id=?", (round(total, 2), oc_id))
            oc_creadas += 1

    conn.commit()
    print(f"  {oc_creadas} órdenes de compra creadas")


def crear_ordenes_produccion(cur):
    """Crear órdenes de producción con seguimiento histórico."""
    print("→ Creando órdenes de producción...")

    # Obtener variantes existentes
    cur.execute("SELECT v.id, v.codigo_variante FROM variantes v WHERE v.activo=1")
    variantes = cur.fetchall()
    if not variantes:
        print("  ⚠ No hay variantes, saltando OPs")
        return

    # Obtener estaciones
    cur.execute("SELECT id, nombre, orden FROM estaciones_produccion ORDER BY orden")
    estaciones = cur.fetchall()

    op_creadas = 0
    for mes in range(1, 9):  # Ene a Ago (Sep queda planeada)
        num_op = random.randint(3, 6)
        for i in range(num_op):
            variante = random.choice(variantes)
            vid, vcod = variante

            fecha_inicio = datetime(2026, mes, random.randint(1, 20))
            fecha_entrega = fecha_inicio + timedelta(days=random.randint(7, 21))
            folio = _next_folio(cur, "ordenes_produccion", "OP")
            total_pares = random.choice([100, 150, 200, 250, 300, 400, 500])

            # Estatus basado en mes
            if mes <= 5:
                estatus = "terminada"
            elif mes <= 7:
                estatus = "en_produccion"
            else:
                estatus = "planeada"

            cur.execute(
                "INSERT INTO ordenes_produccion "
                "(folio, variante_id, total_pares, fecha_inicio, fecha_entrega, "
                "prioridad, estatus, observaciones) "
                "VALUES (?, ?, ?, ?, ?, 'normal', ?, ?)",
                (folio, vid, total_pares,
                 fecha_inicio.strftime("%Y-%m-%d"),
                 fecha_entrega.strftime("%Y-%m-%d"),
                 estatus,
                 f"OP generada automáticamente - {vcod}")
            )
            op_id = cur.lastrowid

            # Matriz de tallas
            pares_restantes = total_pares
            for tid, tnum in TALLAS_M:
                if pares_restantes <= 0:
                    break
                pares_talla = random.randint(1, min(50, max(1, pares_restantes)))
                cur.execute(
                    "INSERT INTO matriz_tallas_op (orden_produccion_id, talla_id, pares) "
                    "VALUES (?, ?, ?)",
                    (op_id, tid, pares_talla)
                )
                pares_restantes -= pares_talla

            # Seguimiento por estación
            for est_id, est_nombre, est_orden in estaciones:
                if estatus == "terminada":
                    # Completada
                    entrada = fecha_inicio + timedelta(days=est_orden - 1)
                    salida = entrada + timedelta(days=random.randint(1, 3))
                    seg_estatus = "completado"
                elif estatus == "en_produccion":
                    # Algunas completadas, otras en proceso
                    if est_orden <= 3:
                        entrada = fecha_inicio + timedelta(days=est_orden - 1)
                        salida = entrada + timedelta(days=random.randint(1, 2))
                        seg_estatus = "completado"
                    elif est_orden == 4:
                        entrada = fecha_inicio + timedelta(days=3)
                        seg_estatus = "en_proceso"
                        salida = None
                    else:
                        seg_estatus = "pendiente"
                        entrada = None
                        salida = None
                else:
                    # Planeada
                    seg_estatus = "pendiente"
                    entrada = None
                    salida = None

                cur.execute(
                    "INSERT INTO seguimiento_produccion "
                    "(orden_produccion_id, estacion_id, fecha_entrada, fecha_salida, "
                    "estatus, pares_procesados, pares_defectuosos) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (op_id, est_id,
                     entrada.strftime("%Y-%m-%d %H:%M:%S") if entrada else None,
                     salida.strftime("%Y-%m-%d %H:%M:%S") if salida else None,
                     seg_estatus,
                     total_pares if seg_estatus == "completado" else random.randint(0, total_pares),
                     random.randint(0, 5) if seg_estatus == "completado" else 0)
                )

            op_creadas += 1

    conn.commit()
    print(f"  {op_creadas} órdenes de producción creadas")


def crear_incidencias(cur):
    """Crear algunas incidencias de producción."""
    print("→ Creando incidencias de producción...")
    cur.execute(
        "SELECT s.id FROM seguimiento_produccion s "
        "WHERE s.estatus IN ('completado', 'en_proceso')"
    )
    segs = cur.fetchall()

    incidencias = 0
    for seg_id_tuple in random.sample(segs, min(15, len(segs))):
        seg_id = seg_id_tuple[0]
        tipos = ["Retraso material", "Defecto costura", "Diferencia pares",
                 "Cambio urgente", "Falla maquinaria"]
        cur.execute(
            "INSERT INTO incidencias_produccion (seguimiento_id, tipo, descripcion, pares_afectados) "
            "VALUES (?, ?, ?, ?)",
            (seg_id, random.choice(tipos),
             f"Incidencia generada automáticamente",
             random.randint(2, 20))
        )
        incidencias += 1

    conn.commit()
    print(f"  {incidencias} incidencias creadas")


def main():
    global conn
    print("=" * 60)
    print("  POBLAR BASE DE DATOS — SIAC ERP")
    print("  Datos de prueba: Enero - Septiembre 2026")
    print("=" * 60)
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    cur = conn.cursor()

    crear_proveedores(cur)
    crear_insumos(cur)
    crear_modelos_variantes(cur)
    crear_fichas_tecnicas(cur)
    crear_insumos_modelo(cur)
    crear_pedidos(cur)
    crear_programacion_semanal(cur)
    crear_ordenes_compra(cur)
    crear_ordenes_produccion(cur)
    crear_incidencias(cur)

    # Resumen
    print()
    print("=" * 60)
    print("  RESUMEN DE DATOS INSERTADOS")
    print("=" * 60)
    tablas = [
        "proveedores", "insumos", "modelos", "variantes",
        "fichas_tecnicas", "lista_materiales",
        "pedidos_cliente", "detalle_pedido_cliente",
        "detalle_pedido_cliente_puntos",
        "programacion_semana", "programacion_lineas",
        "ordenes_compra", "detalle_orden_compra",
        "ordenes_produccion", "seguimiento_produccion",
        "incidencias_produccion"
    ]
    for t in tablas:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(f"  {t}: {cur.fetchone()[0]} registros")
        except Exception:
            pass

    conn.close()
    print()
    print("✅ Base de datos poblada exitosamente.")


if __name__ == "__main__":
    main()
