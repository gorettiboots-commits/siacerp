"""Impresión de programación semanal en HTML (Carta horizontal).

Toma una lista de diccionarios con la programación de calzado y genera un
documento HTML listo para imprimir: @page letter landscape, encabezado con
fondo rosa (#ffccff), una columna por talla y una fila final de totales en
negrita.

Cuando hay varias corridas (segmentos) con tallas disjuntas, se genera
una tabla por cada segmento, cada una con sus propias columnas de talla.

Dos vías de salida:
    - `generar_html_programacion`: solo genera el HTML (para la vista previa
      de impresión del sistema, sin autoprint).
    - `abrir_programacion_html`: guarda el HTML en un temporal y lo abre en
      el navegador con window.print() (autoprint por defecto).
"""
import html
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path


def _esc(texto: str) -> str:
    return (str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))


_FIJAS = [
    ("cliente", "CLIENTE"),
    ("folio_prog", "FOLIO PROG."),
    ("folio_pedido", "FOLIO PEDIDO"),
    ("modelo", "MODELO"),
    ("piel", "PIEL"),
    ("color", "COLOR"),
    ("fecha_prog", "FECHA PROG."),
]


def _datos_empresa() -> dict[str, str]:
    """Devuelve datos de la empresa desde configuración."""
    try:
        from src.models.empresa_model import EmpresaModel
        em = EmpresaModel()
        return {
            "nombre": em.nombre_empresa(),
            "razon_social": em.razon_social(),
            "rfc": em.rfc(),
            "domicilio": em.domicilio(),
            "telefono": em.telefono(),
            "email": em.email(),
        }
    except Exception:
        return {"nombre": "SIAC ERP", "razon_social": "",
                "rfc": "", "domicilio": "",
                "telefono": "", "email": ""}


def _normalizar_talla(talla: str) -> str:
    """Normaliza una talla para dedup: '22.0' → '22', '15.5' → '15.5'."""
    try:
        v = float(talla)
        return str(int(v)) if v == int(v) else str(v)
    except (TypeError, ValueError):
        return talla.strip()


def _rango_tallas_linea(linea: dict) -> tuple[float, float] | None:
    """Obtiene el punto mínimo y máximo que tienen pares > 0 en el registro.

    Devuelve (min_punto, max_punto) como floats, o None si no tiene pares asignados.
    """
    puntos_con_pares: list[float] = []
    for t in linea.get("tallas") or []:
        pares = int(t.get("pares", 0) or 0)
        if pares > 0:
            try:
                puntos_con_pares.append(float(t.get("talla", 0)))
            except (TypeError, ValueError):
                continue
    if not puntos_con_pares:
        return None
    return (min(puntos_con_pares), max(puntos_con_pares))


def _generar_serie_tallas(min_punto: float, max_punto: float) -> list[str]:
    """Genera la lista continua de tallas de medio en medio punto desde min_punto hasta max_punto."""
    if min_punto > max_punto:
        min_punto, max_punto = max_punto, min_punto
    tallas: list[str] = []
    for i in range(int(round(min_punto * 2)), int(round(max_punto * 2)) + 1):
        valor = i / 2.0
        tallas.append(_normalizar_talla(str(valor)))
    return tallas


def _detectar_segmentos(lineas: list[dict]) -> list[dict]:
    """Agrupa las líneas de programación en conjuntos (corridas) por [min_punto, max_punto].

    Itera sobre los datos y para cada línea:
    1. Toma el mínimo y el máximo punto que tienen pares (> 0) en ese registro.
    2. Pregunta si ya existe este conjunto (ejemplo: 22 - 26).
    3. Si no existe, lo agrega al arreglo de conjuntos.
    4. Asigna la línea a su conjunto correspondiente.

    Devuelve una lista de diccionarios con la estructura:
    [
        {
            "min_punto": float,
            "max_punto": float,
            "clave": (min_punto, max_punto),
            "rango_texto": "Del X al Y",
            "tallas_columnas": ["15", "15.5", ..., "21.5"],
            "lineas": [linea1, linea2, ...]
        },
        ...
    ]
    """
    if not lineas:
        return []

    conjuntos: list[dict] = []
    conjuntos_map: dict[tuple[float, float] | None, dict] = {}

    for linea in lineas:
        rango = _rango_tallas_linea(linea)
        if rango not in conjuntos_map:
            if rango is not None:
                min_p, max_p = rango
                tallas_cols = _generar_serie_tallas(min_p, max_p)
                rango_txt = f"Del {_fmt_talla_encabezado(tallas_cols[0])} al {_fmt_talla_encabezado(tallas_cols[-1])}"
            else:
                min_p, max_p = (0.0, 0.0)
                tallas_cols = []
                rango_txt = "Sin tallas asignadas"

            item_conjunto = {
                "min_punto": min_p,
                "max_punto": max_p,
                "clave": rango,
                "rango_texto": rango_txt,
                "tallas_columnas": tallas_cols,
                "lineas": [],
            }
            conjuntos_map[rango] = item_conjunto
            conjuntos.append(item_conjunto)

        conjuntos_map[rango]["lineas"].append(linea)

    # Ordenar los conjuntos por punto mínimo y luego máximo
    conjuntos.sort(
        key=lambda c: (
            1 if c["clave"] is None else 0,
            c["min_punto"],
            c["max_punto"]
        )
    )

    return conjuntos


def _caratula_resumen(
    segmentos: list[dict],
    incluir_semana: bool,
) -> str:
    """Genera la carátula resumen con la cantidad de tablas/corridas detectadas.

    Muestra una tabla con: #, Rango de corrida, Líneas, Total pares,
    y una fila de gran total al final.
    """
    filas = []
    gran_lineas = 0
    gran_pares = 0
    for idx, seg in enumerate(segmentos, 1):
        lineas_seg = seg["lineas"]
        total = sum(int(l.get("total_pares", 0) or 0) for l in lineas_seg)
        rango = seg["rango_texto"]
        n_lineas = len(lineas_seg)
        gran_lineas += n_lineas
        gran_pares += total
        filas.append(
            f"<tr>"
            f"<td class='num'>{idx}</td>"
            f"<td>{_esc(rango)}</td>"
            f"<td class='num'>{n_lineas}</td>"
            f"<td class='num'>{total}</td>"
            f"</tr>")

    filas_total = (
        f"<tr class='total'>"
        f"<td></td>"
        f"<td>TOTAL GENERAL</td>"
        f"<td class='num'>{gran_lineas}</td>"
        f"<td class='num'>{gran_pares}</td>"
        f"</tr>")

    titulo_caratula = "RESUMEN POR CORRIDA" if len(segmentos) > 1 else "RESUMEN DE CORRIDA"

    return f"""
<div class="caratula">
  <div class="caratula-titulo">{titulo_caratula}</div>
  <table class="prog caratula-tabla">
  <thead><tr>
    <th style="width:40px">#</th>
    <th>RANGO DE TALLAS</th>
    <th style="width:80px">LÍNEAS</th>
    <th style="width:100px">TOTAL PARES</th>
  </tr></thead>
  <tbody>
  {''.join(filas)}
  {filas_total}
  </tbody>
  </table>
</div>
"""


def _fmt_talla_encabezado(talla: str) -> str:
    """Formatea la talla para el encabezado de columna."""
    try:
        v = float(talla)
        return str(int(v)) if v == int(v) else str(v)
    except (TypeError, ValueError):
        return talla


def _fila_html(valores: list[str], n_texto: int) -> str:
    celdas = []
    for i, valor in enumerate(valores):
        if i < n_texto:
            celdas.append(f"<td>{_esc(valor)}</td>")
        else:
            celdas.append(f"<td class='num'>{_esc(valor)}</td>")
    return "<tr>" + "".join(celdas) + "</tr>"


def _renderizar_tabla_segmento(
    seg: dict,
    incluir_semana: bool,
    mostrar_subtotal_segmento: bool,
    pagina_nueva: bool = False,
) -> str:
    """Renderiza una sola tabla HTML para un conjunto/segmento de líneas.

    Si *pagina_nueva* es True, agrega page-break-before para que la tabla
    empiece en una hoja nueva (útil cuando hay múltiples corridas).
    """
    lineas = seg["lineas"]
    tallas = seg["tallas_columnas"]
    total_por_talla: dict[str, int] = {talla: 0 for talla in tallas}
    gran_total = 0

    filas_html = []
    for linea in lineas:
        texto = []
        if incluir_semana:
            texto.append(linea.get("semana", ""))
        base = {
            "cliente": linea.get("cliente", ""),
            "folio_prog": linea.get("folio_prog", ""),
            "folio_pedido": linea.get("folio_pedido", ""),
            "modelo": linea.get("modelo", ""),
            "piel": linea.get("piel", ""),
            "color": linea.get("color", ""),
            "fecha_prog": linea.get("fecha_prog", "") or "",
        }
        texto += [base.get(key, "") for key, _ in _FIJAS]
        numeros = []
        por_talla = {_normalizar_talla(str(t.get("talla", ""))):
                     int(t.get("pares", 0) or 0)
                     for t in linea.get("tallas") or []}
        for talla in tallas:
            pares = por_talla.get(talla, 0)
            total_por_talla[talla] += pares
            numeros.append(str(pares or ""))
        total = int(linea.get("total_pares", 0) or 0)
        gran_total += total
        numeros.append(str(total))
        filas_html.append(_fila_html(texto + numeros, len(texto)))

    encabezados = []
    if incluir_semana:
        encabezados.append("SEMANA")
    encabezados += [t for _, t in _FIJAS]
    encabezados += [_fmt_talla_encabezado(t) for t in tallas]
    encabezados.append("TOTAL PARES")

    fila_total = []
    if incluir_semana:
        fila_total.append("")
    fila_total.append("TOTAL")
    fila_total += [""] * (len(_FIJAS) - 1)
    fila_total += [str(total_por_talla.get(talla, 0)) for talla in tallas]
    fila_total.append(str(gran_total))

    cuerpo = "\n".join(filas_html) if filas_html else (
        "<tr><td colspan='%d' style='text-align:center;padding:16px;"
        "color:#64748b'>Sin líneas para esta selección.</td></tr>"
        % len(encabezados))

    # Etiqueta de corrida: siempre se muestra el rango y los totales
    etiqueta_corrida = ""
    if mostrar_subtotal_segmento and tallas:
        etiqueta_corrida = (
            f'<div class="corrida">'
            f'Corrida del {_fmt_talla_encabezado(tallas[0])} al '
            f'{_fmt_talla_encabezado(tallas[-1])} — '
            f'{len(lineas)} líneas · {gran_total} pares'
            f'</div>')

    estilo_extra = " style='page-break-before:always'" if pagina_nueva else ""

    return f"""<div class="segmento"{estilo_extra}>
{etiqueta_corrida}
<table class="prog">
<thead><tr>
{''.join(f'<th>{_esc(h)}</th>' for h in encabezados)}
</tr></thead>
<tbody>
{cuerpo}
<tr class="total">{''.join(f'<td>{_esc(c)}</td>' for c in fila_total)}</tr>
</tbody>
</table>
</div>"""


def generar_html_programacion(lineas: list[dict], titulo: str = "PROGRAMACION SEMANAL",
                              incluir_semana: bool = False,
                              auto_imprimir: bool = True) -> str:
    """Genera el HTML de la programacion con plantilla mint/salvia.

    Carta horizontal. Separa por conjuntos de corridas [min, max] y genera
    las tablas correspondientes con su carátula.
    """
    from src.utils.print_template import (
        esc as t_esc, nombre_empresa as t_empresa, logo_base64,
        _MENTA, _SALVIA, _SALVIA_OSCURA, _VERDE_OSCURO, _VERDE_MEDIO, _BLANCO,
    )

    segmentos = _detectar_segmentos(lineas)
    hay_multiples = len(segmentos) > 1

    tablas = []
    gran_total_todos = 0
    for idx, seg in enumerate(segmentos):
        # La primera tabla va en la misma hoja; las demás en hoja nueva
        pagina_nueva = hay_multiples and idx > 0
        tablas.append(
            _renderizar_tabla_segmento(
                seg, incluir_semana, hay_multiples,
                pagina_nueva=pagina_nueva))
        gran_total_todos += sum(
            int(l.get("total_pares", 0) or 0) for l in seg["lineas"])

    # Carátula resumen siempre (muestra resumen de corridas)
    caratula_html = ""
    if segmentos:
        caratula_html = _caratula_resumen(segmentos, incluir_semana)

    cuerpo_completo = caratula_html + "\n".join(tablas) if tablas else (
        caratula_html + "<div style='text-align:center;padding:40px;"
        "color:#64748b'>Sin lineas para esta seleccion.</div>")

    if not lineas:
        gran_total_todos = 0

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    logo_b64 = logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (f'<img src="data:image/png;base64,{logo_b64}" '
                     f'style="max-width:50px;max-height:50px;vertical-align:middle;margin-right:8px"/>')

    empresa = _datos_empresa()
    empresa_nombre = t_esc(empresa["nombre"].upper())
    empresa_sub = t_esc(empresa["razon_social"])
    empresa_rfc = t_esc(empresa["rfc"])
    empresa_domicilio = t_esc(empresa["domicilio"])
    empresa_tel = t_esc(empresa["telefono"])
    empresa_email = t_esc(empresa["email"])

    # Línea de datos de empresa (solo los que tengan valor)
    datos_empresa = []
    if empresa_rfc:
        datos_empresa.append(f"RFC: {empresa_rfc}")
    if empresa_domicilio:
        datos_empresa.append(empresa_domicilio)
    if empresa_tel:
        datos_empresa.append(f"Tel: {empresa_tel}")
    if empresa_email:
        datos_empresa.append(f"Email: {empresa_email}")
    linea_datos = " &nbsp;·&nbsp; ".join(datos_empresa)

    script_autoprint = "" if not auto_imprimir else (
        "<script>\n"
        "window.addEventListener('load', function () {\n"
        "  setTimeout(function () { window.print(); }, 400);\n"
        "});\n"
        "</script>")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>{t_esc(titulo)}</title>
<style>
@page {{ size: letter landscape; margin: 10mm; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; color: #374151; }}
.header {{
    background: linear-gradient(135deg, {_MENTA} 0%, {_SALVIA} 100%);
    padding: 12px 20px; border-bottom: 3px solid {_SALVIA_OSCURA};
}}
.header table {{ width: 100%; border-collapse: collapse; }}
.header td {{ vertical-align: middle; }}
.header .marca {{ font-size: 20px; font-weight: 800; color: {_VERDE_OSCURO}; letter-spacing: 2px; }}
.header .razon {{ font-size: 11px; color: {_VERDE_MEDIO}; margin-top: 2px; }}
.header .datos {{ font-size: 10px; color: {_VERDE_MEDIO}; margin-top: 2px; }}
.header .titulo {{ font-size: 18px; font-weight: 700; color: {_VERDE_OSCURO}; text-align: center; }}
.header .fecha {{ font-size: 11px; color: {_VERDE_MEDIO}; text-align: right; }}
.caratula {{ margin: 16px 0; padding: 16px 20px;
    background: {_BLANCO}; border: 2px solid {_SALVIA_OSCURA};
    border-radius: 6px; }}
.caratula-titulo {{ font-size: 14px; font-weight: 800;
    color: {_VERDE_OSCURO}; text-align: center; margin-bottom: 12px;
    letter-spacing: 2px; text-transform: uppercase; }}
.caratula-tabla {{ width: 60%; margin: 0 auto; }}
.caratula-tabla th {{ background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
    color: #ffffff; border: 1px solid {_SALVIA_OSCURA};
    padding: 8px 10px; font-size: 11px; text-align: center; }}
.caratula-tabla td {{ border: 1px solid #e4e7e2; padding: 6px 10px;
    font-size: 12px; text-align: center; background: {_BLANCO}; }}
.caratula-tabla tr.total td {{ font-weight: bold;
    background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
    color: #ffffff; border-color: {_SALVIA_OSCURA}; }}
table.prog {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
table.prog th {{ background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
                color: #ffffff; border: 1px solid {_SALVIA_OSCURA};
                padding: 6px 4px; font-size: 10px; white-space: nowrap; }}
table.prog td {{ border: 1px solid #e4e7e2; padding: 4px; font-size: 11px;
                text-align: center; background: {_BLANCO}; }}
table.prog td.num {{ text-align: center; }}
table.prog tr.total td {{ font-weight: bold;
    background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
    color: #ffffff; border-color: {_SALVIA_OSCURA}; }}
table.prog tr:nth-child(even) td {{ background: #f7faf6; }}
.segmento {{ margin-top: 20px; padding: 12px 16px;
    border: 2px solid {_SALVIA_OSCURA}; border-radius: 6px;
    background: #ffffff; page-break-inside: avoid; }}
.segmento:first-child {{ margin-top: 0; }}
.corrida {{ margin-bottom: 6px; padding: 6px 14px;
    background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
    color: #ffffff; font-size: 12px; font-weight: bold;
    letter-spacing: 0.5px; border-radius: 4px; }}
.gran-total {{ margin-top: 14px; padding: 8px 16px;
    background: linear-gradient(135deg, {_SALVIA} 0%, {_MENTA} 100%);
    border: 2px solid {_SALVIA_OSCURA}; border-radius: 6px;
    font-size: 13px; font-weight: bold; color: {_VERDE_OSCURO};
    text-align: right; }}
.footer {{ margin-top: 14px; font-size: 10px; color: {_VERDE_MEDIO}; text-align: right; }}
</style>
</head>
<body>
<div class="header">
<table><tr>
<td style="width:35%">
  {logo_html}<span class="marca">{empresa_nombre}</span>
  {'<div class="razon">' + empresa_sub + '</div>' if empresa_sub and empresa_sub != empresa_nombre else ''}
  {'<div class="datos">' + linea_datos + '</div>' if linea_datos else ''}
</td>
<td style="width:30%">
  <div class="titulo">{t_esc(titulo)}</div>
</td>
<td style="width:35%">
  <div class="fecha">Generado el {ahora}</div>
</td>
</tr></table>
</div>
{cuerpo_completo}
{"" if not hay_multiples or not lineas else
 f'<div class="gran-total">TOTAL GENERAL: {gran_total_todos} pares</div>'}
<div class="footer">{t_empresa()} - Programacion Semanal</div>
{script_autoprint}
</body>
</html>"""


def abrir_programacion_html(lineas: list[dict], titulo: str = "PROGRAMACIÓN SEMANAL",
                            incluir_semana: bool = False) -> str:
    """Guarda el HTML en un archivo temporal y lo abre en el navegador."""
    html_texto = generar_html_programacion(lineas, titulo=titulo,
                                           incluir_semana=incluir_semana)
    nombre = f"programacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    ruta = Path(tempfile.gettempdir()) / nombre
    ruta.write_text(html_texto, encoding="utf-8")
    webbrowser.open(ruta.as_uri())
    return str(ruta)


# ================================================================
# Orden de Pedido sobre hoja pre-impresa (13.5 x 21.5 cm)
#
# La hoja física ya viene impresa: dos órdenes de pedido arriba y seis
# tarjetas de estaciones (MONTADO, PEGAR...) abajo. Al imprimir NO se
# dibuja la plantilla: solo se posicionan los datos en los espacios
# vacíos con coordenadas absolutas en milímetros.
#
# CALIBRACIÓN: si la impresora desvía la salida, ajustar _AJUSTE_X /
# _AJUSTE_Y (desplazan todo el contenido) o las coordenadas de
# _CAMPOS_ORDEN, _MATRIZ_PEDIDO y _TARJETAS_PEDIDO.
# ================================================================

ANCHO_HOJA_PEDIDO_MM = 135.0
ALTO_HOJA_PEDIDO_MM = 215.0

_AJUSTE_X = 0.0   # desplazamiento global de calibración (mm)
_AJUSTE_Y = 0.0

# Tallas impresas en la hoja (bloque superior e inferior de la matriz)
_TALLAS_BLOQUE_1 = [12.0 + 0.5 * i for i in range(16)]    # 12 a 19.5
_TALLAS_BLOQUE_2 = [20.0 + 0.5 * i for i in range(14)]    # 20 a 26.5

# Campos de cada orden: nombre -> (x, y_linea, ancho) en mm.
# y_linea es la posición de la línea pre-impresa; el valor se dibuja
# apoyado justo encima.
_CAMPOS_ORDEN = {
    "cliente": (20.0, 14.8, 65.5),
    "fecha": (99.5, 14.8, 30.0),
    "pares": (13.5, 22.3, 19.0),
    "estilo": (45.5, 22.3, 19.5),
    "color": (77.5, 22.3, 13.5),
    "suela": (104.0, 22.3, 23.0),
    "piel": (11.5, 28.7, 41.0),
}

# Matriz de tallas: cuadrícula fija de 16 columnas para ambos bloques
_MATRIZ_PEDIDO = {
    "x": 2.2,             # borde izquierdo de la matriz
    "ancho_col": 8.16,    # 16 columnas de 2.2 a 132.8 mm
    "y_bloque_1": 38.2,   # fila de cantidades del bloque 1 (12 a 19.5)
    "y_bloque_2": 51.8,   # fila de cantidades del bloque 2 (20 a 26.5)
    "alto_fila": 4.3,
}

# Tarjetas de estaciones: PARES / ESTILO / COLOR en las 6
_TARJETAS_PEDIDO = {
    "ancho": 56.5,
    "alto": 22.2,
    "x_columnas": (5.5, 68.7),
    "y_filas": (140.8, 166.8, 192.8),
    "linea_x": 12.5,                   # inicio de la línea (relativo)
    "linea_ancho": 18.5,
    "lineas_y": (11.4, 15.1, 18.6),    # PARES, ESTILO, COLOR (relativo)
}

_ESTACIONES_PEDIDO = [
    "MONTADO", "PEGAR", "ADORNO", "CORTADA", "BORDADO", "PESPUNTAR",
]

_DESPLAZ_ORDEN_2 = 71.3   # segunda copia de la orden (mm hacia abajo)

# Geometría de la réplica (solo visor)
_REPLICA_ORDEN = {"titulo": (38.0, 3.0, 59.0)}
_RENGLONES_REPLICA = [
    (14.8, [("CLIENTE", 3.0, 15.0, 20.0, 65.5),
            ("FECHA", 88.5, 9.5, 99.5, 30.0)]),
    (22.3, [("PARES", 3.0, 9.0, 13.5, 19.0),
            ("ESTILO", 35.5, 8.5, 45.5, 19.5),
            ("COLOR", 67.5, 8.5, 77.5, 13.5),
            ("SUELA", 93.5, 9.0, 104.0, 23.0)]),
    (28.7, [("PIEL", 3.0, 7.0, 11.5, 41.0)]),
]
_OBS_REPLICA = (55.0, 25.3, 30.0)   # etiqueta OBSERVACIONES centrada
_MATRIZ_REPLICA = {"y_inicio": 33.2, "alto_encabezado": 5.0}


def _fmt_fecha_pedido(valor) -> str:
    """Convierte la fecha ISO de la programación a dd/mm/yyyy."""
    valor = str(valor or "").strip()
    if not valor:
        return ""
    try:
        return datetime.fromisoformat(valor[:19]).strftime("%d/%m/%Y")
    except ValueError:
        return valor


def _datos_linea_pedido(linea: dict) -> dict:
    """Extrae y normaliza los datos de una línea para la Orden de Pedido."""
    total = int(linea.get("total_pares", 0) or 0)
    return {
        "cliente": _esc(linea.get("cliente", "")),
        "fecha": _fmt_fecha_pedido(linea.get("fecha_prog", "")),
        "pares": str(total) if total else "",
        "estilo": _esc(linea.get("modelo", "") or ""),
        "color": _esc(linea.get("color", "") or ""),
        "suela": _esc(linea.get("suela", "") or ""),
        "piel": _esc(linea.get("piel", "") or ""),
    }


def _pares_por_columna(linea: dict) -> dict[int, int]:
    """Mapa columna de la hoja (0..29) -> pares de la línea en esa talla."""
    mapa: dict[int, int] = {}
    columnas = _TALLAS_BLOQUE_1 + _TALLAS_BLOQUE_2
    for t in linea.get("tallas") or []:
        try:
            valor = float(str(t.get("talla", "")).replace(",", "."))
        except (TypeError, ValueError):
            continue
        pares = int(t.get("pares", 0) or 0)
        if pares <= 0:
            continue
        for i, col in enumerate(columnas):
            if abs(col - valor) < 0.01:
                mapa[i] = mapa.get(i, 0) + pares
                break
    return mapa


def _span_valor(x: float, y_linea: float, ancho: float, texto: str,
                fs: float = 3.0) -> str:
    """Span posicionado apoyado sobre una línea pre-impresa."""
    if not texto:
        return ""
    alto = 3.8
    top = y_linea - alto + 0.4 + _AJUSTE_Y
    return (f'<span class="v" style="left:{x + _AJUSTE_X:.2f}mm;'
            f'top:{top:.2f}mm;width:{ancho:.2f}mm;height:{alto:.2f}mm;'
            f'font-size:{fs}mm;line-height:{alto:.2f}mm;'
            f'text-align:center;">{texto}</span>')


def _span_celda(x: float, y: float, ancho: float, alto: float, texto: str,
                fs: float = 3.2) -> str:
    """Span centrado dentro de una celda de la matriz."""
    if not texto:
        return ""
    return (f'<span class="v" style="left:{x + _AJUSTE_X:.2f}mm;'
            f'top:{y + _AJUSTE_Y:.2f}mm;width:{ancho:.2f}mm;'
            f'height:{alto:.2f}mm;font-size:{fs}mm;'
            f'line-height:{alto:.2f}mm;text-align:center;'
            f'font-weight:bold;">{texto}</span>')


def _spans_orden(d: dict, por_columna: dict[int, int], dy: float) -> str:
    """Datos posicionados de UNA orden de pedido (con desplazamiento dy)."""
    valores = {
        "cliente": d["cliente"],
        "fecha": d["fecha"],
        "pares": d["pares"],
        "estilo": d["estilo"],
        "color": d["color"],
        "suela": d["suela"],
        "piel": d["piel"],
    }
    partes = []
    for campo, (x, y, ancho) in _CAMPOS_ORDEN.items():
        partes.append(_span_valor(x, y + dy, ancho, valores[campo]))
    m = _MATRIZ_PEDIDO
    for col, pares in por_columna.items():
        if col < len(_TALLAS_BLOQUE_1):
            idx, y = col, m["y_bloque_1"]
        else:
            idx, y = col - len(_TALLAS_BLOQUE_1), m["y_bloque_2"]
        x = m["x"] + m["ancho_col"] * idx
        partes.append(_span_celda(x, y + dy, m["ancho_col"], m["alto_fila"],
                                  str(pares)))
    return "".join(partes)


def _spans_tarjetas(d: dict) -> str:
    """PARES / ESTILO / COLOR posicionados en las 6 tarjetas de estaciones."""
    t = _TARJETAS_PEDIDO
    valores = (("pares", d["pares"]), ("estilo", d["estilo"]),
               ("color", d["color"]))
    partes = []
    for y_fila in t["y_filas"]:
        for x_col in t["x_columnas"]:
            for (campo, texto), dy in zip(valores, t["lineas_y"]):
                partes.append(_span_valor(
                    x_col + t["linea_x"], y_fila + dy,
                    t["linea_ancho"], texto, fs=2.6))
    return "".join(partes)


def _estilos_hoja() -> str:
    return (f'@page{{size:{ANCHO_HOJA_PEDIDO_MM:.0f}mm '
            f'{ALTO_HOJA_PEDIDO_MM:.0f}mm;margin:0;}}'
            'html,body{margin:0;padding:0;background:#ffffff;}'
            f'.hoja{{position:relative;width:{ANCHO_HOJA_PEDIDO_MM:.0f}mm;'
            f'height:{ALTO_HOJA_PEDIDO_MM:.0f}mm;overflow:hidden;'
            "font-family:'Segoe UI',Arial,sans-serif;}"
            '.v{position:absolute;color:#000;white-space:nowrap;'
            'overflow:hidden;box-sizing:border-box;}')


def _pagina_datos(contenido: str) -> str:
    """Página 13.5x21.5 con SOLO los datos (imprime sobre la hoja impresa)."""
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"/>'
            f'<style>{_estilos_hoja()}</style></head><body>'
            f'<div class="hoja">{contenido}</div></body></html>')


def _pagina_visor(contenido: str) -> str:
    """Página con réplica de la hoja + datos, escalada al ancho del visor."""
    px_hoja = ANCHO_HOJA_PEDIDO_MM * 96 / 25.4
    return ('<!DOCTYPE html><html><head><meta charset="utf-8"/>'
            f'<style>{_estilos_hoja()}'
            '.r{position:absolute;box-sizing:border-box;color:#000;}'
            '</style></head><body>'
            f'<div class="hoja">{contenido}</div>'
            '<script>'
            'function _escalar(){document.body.style.zoom='
            'document.documentElement.clientWidth/'
            f'{px_hoja:.2f}' + ';}'
            "window.addEventListener('load',_escalar);"
            "window.addEventListener('resize',_escalar);"
            '</script></body></html>')


def _div_replica(x: float, y: float, w: float, h: float, extra: str = "",
                 contenido: str = "") -> str:
    return (f'<div class="r" style="left:{x:.2f}mm;top:{y:.2f}mm;'
            f'width:{w:.2f}mm;height:{h:.2f}mm;{extra}">{contenido}</div>')


def _etiqueta_talla(talla: float) -> str:
    """Etiqueta de talla como en la hoja: '12' o '12½' con ½ pequeño."""
    if talla == int(talla):
        return str(int(talla))
    return (f'{int(talla)}<span style="font-size:65%;'
            f'vertical-align:super;">&frac12;</span>')


def _replica_orden(dy: float) -> str:
    """Dibuja la parte pre-impresa de UNA orden de pedido (solo visor)."""
    p = []
    x, y, w = _REPLICA_ORDEN["titulo"]
    p.append(_div_replica(
        x + _AJUSTE_X, y + dy + _AJUSTE_Y, w, 6.0,
        'font-size:4.2mm;font-weight:800;letter-spacing:0.4mm;'
        'text-align:center;', 'ORDEN DE PEDIDO'))
    for y_linea, campos in _RENGLONES_REPLICA:
        for etiqueta, x_lab, w_lab, x_lin, w_lin in campos:
            p.append(_div_replica(
                x_lab + _AJUSTE_X, y_linea + dy - 3.4 + _AJUSTE_Y,
                w_lab, 3.4, 'font-size:2.6mm;font-weight:700;', etiqueta))
            p.append(_div_replica(
                x_lin + _AJUSTE_X, y_linea + dy + _AJUSTE_Y, w_lin, 0.5,
                'border-bottom:0.35mm solid #000;'))
    x, y, w = _OBS_REPLICA
    p.append(_div_replica(
        x + _AJUSTE_X, y + dy + _AJUSTE_Y, w, 3.4,
        'font-size:2.6mm;font-weight:700;text-align:center;',
        'OBSERVACIONES'))
    return "".join(p)


def _replica_matriz(dy: float) -> str:
    """Dibuja la cuadrícula de tallas pre-impresa (solo visor)."""
    m = _MATRIZ_PEDIDO
    r = _MATRIZ_REPLICA
    x0 = m["x"] + _AJUSTE_X
    y0 = r["y_inicio"] + dy + _AJUSTE_Y
    alto_enc = r["alto_encabezado"]
    alto_fila = m["alto_fila"]
    ancho = m["ancho_col"] * 16
    alto = (alto_enc + 2 * alto_fila) * 2
    p = [_div_replica(x0, y0, ancho, alto, 'border:0.35mm solid #000;')]
    # Líneas horizontales internas (fin encabezado 1, fin filas, encabezado 2)
    for offset in (alto_enc, alto_enc + alto_fila,
                   alto_enc + 2 * alto_fila,
                   alto_enc + 2 * alto_fila + alto_enc,
                   alto_enc + 2 * alto_fila + alto_enc + alto_fila):
        p.append(_div_replica(x0, y0 + offset, ancho, 0.5,
                              'border-bottom:0.3mm solid #000;'))
    # Líneas verticales de las 16 columnas
    for i in range(1, 16):
        p.append(_div_replica(x0 + m["ancho_col"] * i, y0, 0.5, alto,
                              'border-left:0.3mm solid #000;'))
    # Encabezados de talla (bloque 1 y bloque 2)
    for i, talla in enumerate(_TALLAS_BLOQUE_1):
        p.append(_div_replica(
            x0 + m["ancho_col"] * i, y0, m["ancho_col"], alto_enc,
            'font-size:2.6mm;font-weight:700;text-align:center;'
            'padding-top:0.8mm;', _etiqueta_talla(talla)))
    y_enc2 = y0 + alto_enc + 2 * alto_fila
    for i, talla in enumerate(_TALLAS_BLOQUE_2):
        p.append(_div_replica(
            x0 + m["ancho_col"] * i, y_enc2, m["ancho_col"], alto_enc,
            'font-size:2.6mm;font-weight:700;text-align:center;'
            'padding-top:0.8mm;', _etiqueta_talla(talla)))
    return "".join(p)


def _replica_tarjetas() -> str:
    """Dibuja las 6 tarjetas de estaciones pre-impresas (solo visor)."""
    t = _TARJETAS_PEDIDO
    p = []
    for i, y_fila in enumerate(t["y_filas"]):
        for j, x_col in enumerate(t["x_columnas"]):
            x = x_col + _AJUSTE_X
            y = y_fila + _AJUSTE_Y
            p.append(_div_replica(x, y, t["ancho"], t["alto"],
                                  'border:0.4mm solid #000;'))
            nombre = _ESTACIONES_PEDIDO[i * 2 + j]
            p.append(_div_replica(
                x + 2.5, y + 1.5, t["ancho"] - 5.0, 4.5,
                'font-size:3.4mm;font-weight:800;', nombre))
            for etiqueta, dy in zip(("PARES", "ESTILO", "COLOR"),
                                    t["lineas_y"]):
                p.append(_div_replica(
                    x + 2.5, y + dy - 3.0, 9.5, 3.0,
                    'font-size:2.3mm;font-weight:700;', etiqueta))
                p.append(_div_replica(
                    x + t["linea_x"], y + dy, t["linea_ancho"], 0.5,
                    'border-bottom:0.3mm solid #000;'))
    return "".join(p)


def generar_html_orden_pedido(linea: dict, solo_contenido: bool = False) -> str:
    """Genera el HTML de la Orden de Pedido (hoja pre-impresa 13.5x21.5cm).

    Args:
        linea: línea con tallas (obtener_linea_con_tallas).
        solo_contenido: True = solo los datos posicionados en milímetros,
            para imprimir en los espacios vacíos de la hoja ya impresa.
            False = réplica de la hoja pre-impresa con los datos encima
            (vista previa WYSIWYG de cómo queda la hoja llenada).
    """
    d = _datos_linea_pedido(linea)
    por_columna = _pares_por_columna(linea)
    datos = (_spans_orden(d, por_columna, 0.0)
             + _spans_orden(d, por_columna, _DESPLAZ_ORDEN_2)
             + _spans_tarjetas(d))
    if solo_contenido:
        return _pagina_datos(datos)
    visor = (_replica_orden(0.0) + _replica_orden(_DESPLAZ_ORDEN_2)
             + _replica_matriz(0.0) + _replica_matriz(_DESPLAZ_ORDEN_2)
             + _replica_tarjetas())
    return _pagina_visor(visor + datos)


