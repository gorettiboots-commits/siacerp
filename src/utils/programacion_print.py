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
) -> str:
    """Renderiza una sola tabla HTML para un segmento de líneas."""
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

    etiqueta_corrida = ""
    if mostrar_subtotal_segmento and tallas:
        etiqueta_corrida = (
            f'<div class="corrida">Corrida: '
            f'del {_fmt_talla_encabezado(tallas[0])} al '
            f'{_fmt_talla_encabezado(tallas[-1])} '
            f'({len(lineas)} líneas · {gran_total} pares)</div>')

    return f"""{etiqueta_corrida}
<table class="prog">
<thead><tr>
{''.join(f'<th>{_esc(h)}</th>' for h in encabezados)}
</tr></thead>
<tbody>
{cuerpo}
<tr class="total">{''.join(f'<td>{_esc(c)}</td>' for c in fila_total)}</tr>
</tbody>
</table>"""


def generar_html_programacion(lineas: list[dict], titulo: str = "PROGRAMACIÓN SEMANAL",
                              incluir_semana: bool = False,
                              auto_imprimir: bool = True) -> str:
    """Genera el HTML de la programación con fila final de totales en negrita.

    Si las líneas pertenecen a varias corridas (segmentos con tallas sin
    superposición), genera una tabla independiente por cada segmento, cada
    una con sus propias columnas de talla y subtotal.

    `auto_imprimir=False` omite el script de window.print(): útil para
    mostrar el documento en la vista previa de impresión del sistema en
    lugar de abrirlo en el navegador.
    """
    segmentos = _detectar_segmentos(lineas)
    hay_multiples = len(segmentos) > 1

    tablas = []
    gran_total_todos = 0
    for seg in segmentos:
        tablas.append(
            _renderizar_tabla_segmento(seg, incluir_semana, hay_multiples))
        gran_total_todos += sum(
            int(l.get("total_pares", 0) or 0) for l in seg)

    cuerpo_completo = "\n".join(tablas) if tablas else (
        "<div style='text-align:center;padding:40px;color:#64748b'>"
        "Sin líneas para esta selección.</div>")

    if not lineas:
        gran_total_todos = 0

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

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
<title>{_esc(titulo)}</title>
<style>
@page {{ size: letter landscape; margin: 10mm; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; color: #111827; }}
.header {{ background: #ffccff; padding: 12px 16px; border-bottom: 3px solid #d946ef; }}
.header h1 {{ margin: 0; font-size: 18px; color: #7c3aed; }}
.header .sub {{ font-size: 11px; color: #4a4a4a; margin-top: 3px; }}
table.prog {{ width: 100%; border-collapse: collapse; margin-top: 6px; }}
table.prog th {{ background: #7c3aed; color: #ffffff; border: 1px solid #6b21a8;
                padding: 6px 4px; font-size: 10px; white-space: nowrap; }}
table.prog td {{ border: 1px solid #e5e7eb; padding: 4px; font-size: 11px;
                text-align: center; }}
table.prog td.num {{ text-align: center; }}
table.prog tr.total td {{ font-weight: bold; background: #ffe6ff; border-color: #d946ef; }}
table.prog tr:nth-child(even) td {{ background: #fdf2ff; }}
.corrida {{ margin-top: 16px; padding: 5px 12px; background: #7c3aed; color: #ffffff;
            font-size: 11px; font-weight: bold; letter-spacing: 0.5px; }}
.gran-total {{ margin-top: 14px; padding: 8px 16px; background: #ede9fe;
               border: 2px solid #7c3aed; border-radius: 6px;
               font-size: 13px; font-weight: bold; color: #4c1d95;
               text-align: right; }}
.footer {{ margin-top: 14px; font-size: 10px; color: #6b7280; text-align: right; }}
</style>
</head>
<body>
<div class="header">
  <h1>{_esc(titulo)}</h1>
  <div class="sub">Generado el {ahora}</div>
</div>
{cuerpo_completo}
{"" if not hay_multiples or not lineas else
 f'<div class="gran-total">TOTAL GENERAL: {gran_total_todos} pares</div>'}
<div class="footer">{_nombre_empresa()} — Impresión Carta horizontal</div>
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
