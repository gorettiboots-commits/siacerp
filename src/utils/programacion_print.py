"""Impresión de programación semanal en HTML (Carta horizontal).

Toma una lista de diccionarios con la programación de calzado y genera un
documento HTML listo para imprimir: @page letter landscape, encabezado con
fondo rosa (#ffccff), una columna por talla y una fila final de totales en
negrita. Guarda el HTML y lo abre en el navegador con window.print().
"""
import html
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path

_FIJAS = [
    ("cliente", "CLIENTE"),
    ("folio_prog", "FOLIO PROG."),
    ("folio_pedido", "FOLIO PEDIDO"),
    ("modelo", "MODELO"),
    ("piel", "PIEL"),
    ("color", "COLOR"),
    ("fecha_prog", "FECHA PROG."),
]


def _tallas_ordenadas(lineas: list[dict]) -> list[str]:
    tallas: list[str] = []
    vistos: set[str] = set()
    for linea in lineas:
        for t in linea.get("tallas") or []:
            talla = str(t.get("talla", "") or "").strip()
            if talla and talla not in vistos:
                vistos.add(talla)
                tallas.append(talla)
    tallas.sort(key=lambda x: (float(x), x))
    return tallas


def _esc(texto) -> str:
    return html.escape(str(texto or ""), quote=True)


def _fila_html(valores: list[str], n_texto: int) -> str:
    celdas = []
    for i, valor in enumerate(valores):
        if i < n_texto:
            celdas.append(f"<td>{_esc(valor)}</td>")
        else:
            celdas.append(f"<td class='num'>{_esc(valor)}</td>")
    return "<tr>" + "".join(celdas) + "</tr>"


def generar_html_programacion(lineas: list[dict], titulo: str = "PROGRAMACIÓN SEMANAL",
                              incluir_semana: bool = False) -> str:
    """Genera el HTML de la programación con fila final de totales en negrita."""
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
        por_talla = {str(t.get("talla", "")): int(t.get("pares", 0) or 0)
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
    encabezados += tallas
    encabezados.append("TOTAL PARES")

    fila_total = []
    if incluir_semana:
        fila_total.append("")
    fila_total.append("TOTAL")
    fila_total += [""] * (len(_FIJAS) - 1)
    fila_total += [str(total_por_talla.get(talla, 0)) for talla in tallas]
    fila_total.append(str(gran_total))

    cuerpo = "\n".join(filas_html) if filas_html else (
        "<tr><td colspan='%d' style='text-align:center;padding:16px;color:#64748b'>"
        "Sin líneas para esta selección.</td></tr>" % len(encabezados))

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

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
table.prog {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
table.prog th {{ background: #7c3aed; color: #ffffff; border: 1px solid #6b21a8;
                padding: 6px 4px; font-size: 10px; white-space: nowrap; }}
table.prog td {{ border: 1px solid #e5e7eb; padding: 4px; font-size: 11px;
                text-align: center; }}
table.prog td.num {{ text-align: center; }}
table.prog tr.total td {{ font-weight: bold; background: #ffe6ff; border-color: #d946ef; }}
table.prog tr:nth-child(even) td {{ background: #fdf2ff; }}
.footer {{ margin-top: 14px; font-size: 10px; color: #6b7280; text-align: right; }}
</style>
</head>
<body>
<div class="header">
  <h1>{_esc(titulo)}</h1>
  <div class="sub">Generado el {ahora}</div>
</div>
<table class="prog">
<thead><tr>
{''.join(f'<th>{_esc(h)}</th>' for h in encabezados)}
</tr></thead>
<tbody>
{cuerpo}
<tr class="total">{''.join(f'<td>{_esc(c)}</td>' for c in fila_total)}</tr>
</tbody>
</table>
<div class="footer">Goretti ERP — Impresión Carta horizontal</div>
<script>
window.addEventListener('load', function () {{
  setTimeout(function () {{ window.print(); }}, 400);
}});
</script>
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
