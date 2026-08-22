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


def _nombre_empresa() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        return EmpresaModel().nombre_empresa()
    except Exception:
        return "SIAC ERP"


def _normalizar_talla(talla: str) -> str:
    """Normaliza una talla para dedup: '22.0' → '22', '15.5' → '15.5'."""
    try:
        v = float(talla)
        return str(int(v)) if v == int(v) else str(v)
    except (TypeError, ValueError):
        return talla.strip()


def _tallas_ordenadas(lineas: list[dict]) -> list[str]:
    tallas: list[str] = []
    vistos: set[str] = set()
    for linea in lineas:
        for t in linea.get("tallas") or []:
            talla = str(t.get("talla", "") or "").strip()
            norm = _normalizar_talla(talla)
            if norm and norm not in vistos:
                vistos.add(norm)
                tallas.append(norm)
    tallas.sort(key=lambda x: float(x))
    return tallas


def _tallas_linea(linea: dict) -> set[str]:
    """Devuelve el conjunto de tallas normalizadas de una línea."""
    return {
        _normalizar_talla(str(t.get("talla", "") or ""))
        for t in linea.get("tallas") or []
        if _normalizar_talla(str(t.get("talla", "") or ""))
    }


def _detectar_segmentos(lineas: list[dict]) -> list[list[dict]]:
    """Separa las líneas en segmentos (corridas) según gaps en las tallas.

    Recopila todas las tallas únicas de todas las líneas, las ordena y
    detecta saltos mayores a 1.0 (p. ej. 21.5 → 22.5). Cada línea se
    asigna al segmento donde cae la mayoría de sus tallas.

    Si no hay gaps o solo hay un segmento, devuelve todas las líneas
    juntas en una sola lista.
    """
    n = len(lineas)
    if n <= 1:
        return [lineas[:]] if lineas else []

    # 1. Recopilar todas las tallas únicas
    todas_tallas: set[str] = set()
    for linea in lineas:
        todas_tallas |= _tallas_linea(linea)

    if not todas_tallas:
        return [lineas[:]]

    tallas_ord = sorted(todas_tallas, key=lambda x: float(x))

    # 2. Detectar gaps (salto > 1.0 entre tallas consecutivas)
    cortes: list[float] = []
    for i in range(1, len(tallas_ord)):
        diff = float(tallas_ord[i]) - float(tallas_ord[i - 1])
        if diff > 1.0:
            midpoint = (float(tallas_ord[i - 1]) + float(tallas_ord[i])) / 2
            cortes.append(midpoint)

    if not cortes:
        return [lineas[:]]

    # 3. Asignar cada línea al segmento según dónde caen sus tallas
    #    Un segmento se define por los rangos: (-inf, corte1), (corte1, corte2), ...
    segmentos: list[list[dict]] = [[] for _ in range(len(cortes) + 1)]

    for linea in lineas:
        tallas_linea = _tallas_linea(linea)
        if not tallas_linea:
            segmentos[0].append(linea)
            continue

        # Contar cuántas tallas caen en cada segmento
        conteo = [0] * len(segmentos)
        for talla in tallas_linea:
            vt = float(talla)
            idx = 0
            for c in cortes:
                if vt > c:
                    idx += 1
                else:
                    break
            conteo[idx] += 1

        mejor = conteo.index(max(conteo))
        segmentos[mejor].append(linea)

    # Eliminar segmentos vacíos
    return [s for s in segmentos if s]


def _caratula_resumen(
    segmentos: list[list[dict]],
    incluir_semana: bool,
) -> str:
    """Genera una carátula resumen cuando hay múltiples segmentos.

    Muestra una tabla con: #, Rango de corrida, Líneas, Total pares,
    y una fila de gran total al final.
    """
    filas = []
    gran_lineas = 0
    gran_pares = 0
    for idx, seg in enumerate(segmentos, 1):
        tallas = _tallas_ordenadas(seg)
        total = sum(int(l.get("total_pares", 0) or 0) for l in seg)
        rango = (
            f"Del {_fmt_talla_encabezado(tallas[0])} al "
            f"{_fmt_talla_encabezado(tallas[-1])}"
            if tallas else "Sin tallas")
        n_lineas = len(seg)
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
    lineas: list[dict],
    incluir_semana: bool,
    mostrar_subtotal_segmento: bool,
    pagina_nueva: bool = False,
) -> str:
    """Renderiza una sola tabla HTML para un segmento de líneas.

    Si *pagina_nueva* es True, agrega page-break-before para que la tabla
    empiece en una hoja nueva (útil cuando hay múltiples corridas).
    """
    tallas = _tallas_ordenadas(lineas)
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
            f'<div class="corrida">Corrida: '
            f'del {_fmt_talla_encabezado(tallas[0])} al '
            f'{_fmt_talla_encabezado(tallas[-1])} '
            f'({len(lineas)} líneas · {gran_total} pares)</div>')

    estilo_extra = " style='page-break-before:always'" if pagina_nueva else ""

    return f"""<div{estilo_extra}>
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

    Carta horizontal. Si las lineas pertenecen a varias corridas
    (segmentos con tallas sin superposicion), genera una tabla por segmento.
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
            int(l.get("total_pares", 0) or 0) for l in seg)

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
.header .titulo {{ font-size: 18px; font-weight: 700; color: {_VERDE_OSCURO}; text-align: center; }}
.header .sub {{ font-size: 11px; color: {_VERDE_MEDIO}; }}
header .fecha {{ font-size: 11px; color: {_VERDE_MEDIO}; text-align: right; }}
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
.corrida {{ margin-top: 16px; padding: 5px 12px;
    background: linear-gradient(135deg, {_SALVIA} 0%, {_SALVIA_OSCURA} 100%);
    color: #ffffff; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; }}
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
<td style="width:30%">
  {logo_html}<span class="marca">{t_empresa().upper()}</span>
</td>
<td style="width:40%">
  <div class="titulo">{t_esc(titulo)}</div>
</td>
<td style="width:30%">
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
