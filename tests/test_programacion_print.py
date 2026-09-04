"""Pruebas de la Orden de Pedido sobre hoja pre-impresa 13.5x21.5cm.

La impresión debe posicionar SOLO los datos en coordenadas absolutas
(mm) para llenar los espacios vacíos de la hoja ya impresa.
"""

import re

from src.utils.programacion_print import (
    ALTO_HOJA_PEDIDO_MM,
    ANCHO_HOJA_PEDIDO_MM,
    generar_html_orden_pedido,
)

LINEA = {
    "id": 1,
    "folio_prog": "PR-0001",
    "folio_pedido": "PED-0051",
    "cliente": "Goretti Boutique",
    "modelo": "GO-1200",
    "piel": "Napa vacuno",
    "color": "Vino",
    "suela": "PVC crema",
    "fecha_prog": "2026-08-24",
    "total_pares": 144,
    "tallas": [
        {"talla": "12", "pares": 8},
        {"talla": "22", "pares": 10},
        {"talla": "22.5", "pares": 12},
        {"talla": "26", "pares": 14},
    ],
}


def _spans(html: str) -> list[tuple[float, float, str]]:
    """Extrae (left_mm, top_mm, texto) de los spans posicionados."""
    resultado = []
    for estilo, texto in re.findall(
            r'<span class="v" style="([^"]+)">([^<]*)</span>', html):
        left = float(re.search(r"left:([\d.]+)mm", estilo).group(1))
        top = float(re.search(r"top:([\d.]+)mm", estilo).group(1))
        resultado.append((left, top, texto))
    return resultado


def test_impresion_usa_pagina_135x215_sin_margenes():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    assert f"@page{{size:{ANCHO_HOJA_PEDIDO_MM:.0f}mm " \
           f"{ALTO_HOJA_PEDIDO_MM:.0f}mm;margin:0;}}" in html


def test_impresion_solo_datos_sin_plantilla():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    assert "ORDEN DE PEDIDO" not in html
    assert "MONTADO" not in html
    assert "Goretti Boutique" in html
    assert "24/08/2026" in html
    assert "PVC crema" in html


def test_impresion_duplica_los_datos_en_las_dos_ordenes():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    assert html.count("Goretti Boutique") == 2
    assert html.count("PVC crema") == 2


def test_impresion_todos_los_spans_dentro_de_la_hoja():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    for left, top, _ in _spans(html):
        assert 0 <= left <= ANCHO_HOJA_PEDIDO_MM, f"left {left} fuera"
        assert 0 <= top <= ALTO_HOJA_PEDIDO_MM, f"top {top} fuera"


def test_impresion_cantidad_en_columna_correcta_del_bloque():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    # Columnas del bloque 2: 20->0, 20.5->1, 21->2, 21.5->3, 22->4...
    # talla 12 -> bloque 1 col 0 (y ~38.2); talla 22 -> bloque 2 col 4
    # (x = 2.2 + 8.16*4 = 34.8); talla 22.5 -> col 5; talla 26 -> col 12
    # La segunda orden repite todo con +71.3mm de desplazamiento vertical.
    celdas = [(l, t, txt) for l, t, txt in _spans(html) if txt == "8"]
    assert celdas and all(
        36 <= t <= 44 or 107 <= t <= 115 for _, t, _ in celdas), \
        "talla 12 en bloque 1 (ambas ordenes)"
    por_texto = {}
    for l, t, txt in _spans(html):
        if txt in ("10", "12", "14"):
            por_texto.setdefault(txt, []).append((l, t))
    for tops in por_texto.values():
        assert all(49 <= t <= 56 or 120 <= t <= 127 for _, t in tops), \
            "fila del bloque 2 (ambas ordenes)"
    assert all(33 <= l <= 37 for l, _ in por_texto["10"]), \
        "talla 22 col 4 bloque 2"
    assert all(41 <= l <= 45 for l, _ in por_texto["12"]), \
        "talla 22.5 col 5 bloque 2"
    assert all(98 <= l <= 102 for l, _ in por_texto["14"]), \
        "talla 26 col 12 bloque 2"


def test_impresion_tarjetas_estaciones_con_datos():
    html = generar_html_orden_pedido(LINEA, solo_contenido=True)
    # 6 tarjetas x 3 valores = 18 spans; pares/estilo/color aparecen 6 veces
    assert html.count(">144<") == 8  # 2 ordenes + 6 tarjetas
    assert html.count(">GO-1200<") == 8
    assert html.count(">Vino<") == 8


def test_visor_muestra_la_replica_de_la_hoja():
    html = generar_html_orden_pedido(LINEA)
    assert html.count("ORDEN DE PEDIDO") == 2
    for estacion in ("MONTADO", "PEGAR", "ADORNO", "CORTADA", "BORDADO",
                     "PESPUNTAR"):
        assert estacion in html
    assert "Goretti Boutique" in html


def test_linea_sin_pedido_no_rompe():
    linea = dict(LINEA)
    linea["suela"] = ""
    linea["tallas"] = [{"talla": "99", "pares": 5}]
    html = generar_html_orden_pedido(linea, solo_contenido=True)
    assert "Goretti Boutique" in html
