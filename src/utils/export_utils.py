import os
from pathlib import Path
from typing import Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PySide6.QtCore import Qt
from PySide6.QtGui import QPageLayout, QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidget, QWidget


def export_table_to_excel(table: QTableWidget, titulo: str, parent: QWidget) -> Optional[str]:
    path, _ = QFileDialog.getSaveFileName(parent, f"Exportar {titulo}", f"{titulo}.xlsx",
                                           "Excel (*.xlsx)")
    if not path:
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = titulo[:31]

    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    visible_cols = [c for c in range(table.columnCount()) if not table.isColumnHidden(c)]
    headers = [table.horizontalHeaderItem(c).text() if table.horizontalHeaderItem(c) else ""
               for c in visible_cols]

    for ci, col_idx in enumerate(visible_cols):
        cell = ws.cell(row=1, column=ci + 1, value=headers[ci])
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    for row in range(table.rowCount()):
        for ci, col_idx in enumerate(visible_cols):
            item = table.item(row, col_idx)
            val = item.text() if item else ""
            cell = ws.cell(row=row + 2, column=ci + 1, value=val)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if ci > 0 else "left")

    for ci in range(len(visible_cols)):
        ws.column_dimensions[get_column_letter(ci + 1)].width = max(12, len(headers[ci]) + 4)

    wb.save(path)
    return path


def print_table(table: QTableWidget, titulo: str, parent: QWidget) -> None:
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPageSize.Letter)
    printer.setPageOrientation(QPageLayout.Landscape)

    dlg = QFileDialog()
    path, _ = QFileDialog.getSaveFileName(parent, f"Guardar PDF - {titulo}", f"{titulo}.pdf",
                                           "PDF (*.pdf)")
    if not path:
        return
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)

    html = _table_to_html(table, titulo)
    doc = QTextDocument()
    doc.setHtml(html)
    doc.print_(printer)


def _table_to_html(table: QTableWidget, titulo: str) -> str:
    logo_path = Path(__file__).resolve().parent.parent / "views" / "assets" / "logo.png"
    logo_b64 = ""
    if logo_path.exists():
        import base64
        with open(str(logo_path), "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()

    rows_html = ""
    visible_cols = [c for c in range(table.columnCount()) if not table.isColumnHidden(c)]
    headers = [table.horizontalHeaderItem(c).text() if table.horizontalHeaderItem(c) else ""
               for c in visible_cols]

    header_row = "".join(f"<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;"
                         f"font-size:11px'>{h}</th>" for h in headers)
    rows_html += f"<tr>{header_row}</tr>"

    for row in range(table.rowCount()):
        cells = ""
        for ci in visible_cols:
            item = table.item(row, ci)
            val = item.text() if item else ""
            cells += f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"

    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width:80px;max-height:80px;float:right"/>'

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/></head><body>
<div style='border-bottom:2px solid #4f46e5;padding-bottom:8px;margin-bottom:16px'>
{logo_html}
<h2 style='color:#1e293b;margin:0'>{titulo}</h2>
<p style='color:#64748b;font-size:11px;margin:4px 0'>SIAC ERP - Sistema Integral de Administración y Control</p>
</div>
<table style='width:100%;border-collapse:collapse;font-family:Segoe UI,sans-serif'>
{rows_html}
</table>
<p style='color:#94a3b8;font-size:9px;margin-top:16px;text-align:center'>
Generado por SIAC ERP - Desarrollado por Mario Felipe Luevano - Todos los derechos reservados</p>
</body></html>"""


def _logo_base64() -> str:
    """Logo del membrete en base64: prefiere `logonew.png` de la raíz del
    proyecto (membrete actual); si no existe, usa `views/assets/logo.png`."""
    raiz = Path(__file__).resolve().parent.parent.parent
    candidatos = [
        raiz / "logonew.png",
        Path(__file__).resolve().parent.parent / "views" / "assets" / "logo.png",
    ]
    import base64
    for ruta in candidatos:
        if ruta.exists():
            with open(str(ruta), "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def _fmt_fecha(fecha: str) -> str:
    s = (fecha or "").strip()
    if not s:
        return ""
    fecha_solo = s.split(" ")[0]
    partes = fecha_solo.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        anio, mes, dia = partes
        return f"{dia}/{mes}/{anio}"
    partes = fecha_solo.split("/")
    if len(partes) == 3:
        if len(partes[2]) == 4:
            dia, mes, anio = partes
        else:
            anio, mes, dia = partes[2], partes[1], partes[0]
        return f"{dia}/{mes}/{anio}"
    return fecha_solo


def _esc(texto: str) -> str:
    return (str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _clave_numerica_talla(texto: str) -> float:
    try:
        return float(texto)
    except (TypeError, ValueError):
        return 0.0


def _oc_columnas_tallas(detalle: list[dict]) -> list[dict]:
    cols: list[dict] = []
    vistos: set[int] = set()
    for d in detalle:
        for t in d.get("tallas", []):
            tid = t["talla_id"]
            if tid not in vistos:
                vistos.add(tid)
                cols.append({"talla_id": tid, "talla": t.get("talla", "")})
    cols.sort(key=lambda t: _clave_numerica_talla(t.get("talla", "")))
    return cols


def _oc_subtotal_detalle(d: dict) -> float:
    """Subtotal del renglón: Σ(pares × precio) por talla si hay precios por talla;
    si no, cantidad × precio_unitario."""
    tallas = d.get("tallas", []) or []
    con_precio = [t for t in tallas if float(t.get("precio", 0) or 0) > 0]
    if con_precio:
        return sum(float(t.get("pares", 0) or 0) * float(t.get("precio", 0) or 0)
                   for t in con_precio)
    return float(d.get("cantidad", 0) or 0) * float(d.get("precio_unitario", 0) or 0)


def _oc_totales(detalle: list[dict], solo_remision: bool) -> tuple[float, float, float]:
    subtotal = sum(_oc_subtotal_detalle(d) for d in detalle)
    if solo_remision:
        iva = 0.0
    else:
        iva = round(subtotal * 0.16, 2)
    total = round(subtotal + iva, 2)
    return round(subtotal, 2), iva, total


def _oc_receipt_html(datos: dict, detalle: list[dict]) -> str:
    """Recibo de OC con el diseño aprobado en el Sandbox (ondas menta/salvia).

    Cabecera y pie con ondas superpuestas (curvas S) a todo lo ancho: menta
    pálido #D4EDEA de fondo y salvia #A9C5C1 al frente, en hoja carta vertical.
    Fondo #f0f0f0, tipografía sans-serif; los insumos quedan justificados a la
    izquierda y los precios alineados a la derecha. El pie queda anclado al
    fondo de la hoja. Incluye el membrete `logonew.png` de la raíz del proyecto
    y el área de Observaciones cuando la orden las tiene.
    """
    from datetime import datetime

    solo_remision = bool(datos.get("solo_remision"))
    titulo = "REMI-SIÓN - ORDEN DE COMPRA" if solo_remision else "RECIBO DE COMPRA"
    subtotal, iva, total = _oc_totales(detalle, solo_remision)
    columnas = _oc_columnas_tallas(detalle)
    logo_b64 = _logo_base64()

    estatus = str(datos.get("estatus", "") or "").replace("_", " ").capitalize()
    proveedor = datos.get("proveedor_nombre") or "Compra a inventario"
    telefono = datos.get("proveedor_telefono") or ""
    email = datos.get("proveedor_email") or ""
    rfc = datos.get("proveedor_rfc") or ""
    direccion = datos.get("proveedor_direccion") or ""

    logo_html = ""
    if logo_b64:
        logo_html = (f'<img src="data:image/png;base64,{logo_b64}" '
                     f'style="max-width:110px;max-height:110px;vertical-align:middle;margin-right:10px"/>')

    th_tallas = "".join(
        f"<th>{_esc('#')}{_esc(c['talla'])}</th>" for c in columnas)

    rows = ""
    for d in detalle:
        por_talla = {int(t["talla_id"]): int(t.get("pares", 0) or 0)
                     for t in d.get("tallas", [])}
        celdas = "".join(
            f"<td>{por_talla.get(int(c['talla_id']), 0) or ''}</td>"
            for c in columnas)
        cant = int(d.get("cantidad", 0) or 0)
        precio = float(d.get("precio_unitario", 0) or 0)
        sub = _oc_subtotal_detalle(d)
        rows += f"""<tr>
            <td style='text-align:left'>{_esc(d.get('insumo_nombre', ''))}</td>
            {celdas}
            <td>{cant}</td>
            <td style='text-align:right'>${precio:,.2f}</td>
            <td style='text-align:right;font-weight:600'>${sub:,.2f}</td>
        </tr>"""

    filas_iva = ""
    if not solo_remision:
        filas_iva = (
            f"<tr><td>IVA (16%)</td><td class='val'>${iva:,.2f}</td></tr>")

    lineas_proveedor = [l for l in [
        _esc(proveedor),
        (f"Tel: {_esc(telefono)}" if telefono else ""),
        (f"Email: {_esc(email)}" if email else ""),
        (f"RFC: {_esc(rfc)}" if rfc else ""),
        (f"Dirección: {_esc(direccion)}" if direccion else ""),
    ] if l]
    vendido_html = "".join(
        f"<div style='{'font-size:15px;font-weight:700;color:#2f4f3a' if i == 0 else 'color:#5b6b60;font-size:12px'}'>"
        f"{l}</div>" for i, l in enumerate(lineas_proveedor))

    obs_html = ""
    observaciones = str(datos.get("observaciones") or "").strip()
    if observaciones:
        obs_html = f"""<div class='bloque obs'>
    <div class='lbl'>Observaciones</div>
    <div class='texto'>{_esc(observaciones).replace(chr(10), '<br/>')}</div>
  </div>"""

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ margin: 0; }}
html, body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #374151;
              margin: 0; padding: 0; background: #f0f0f0;
              height: 100%; }}
.hoja {{ width: 100%; max-width: 820px; margin: 0 auto;
        display: flex; flex-direction: column;
        min-height: 100%; box-sizing: border-box; }}
.cabecera {{ background: #D4EDEA; padding: 24px 30px 18px 30px; }}
.cabecera table {{ width: 100%; border-collapse: collapse; }}
.cabecera td {{ vertical-align: middle; }}
.marca {{ font-size: 26px; font-weight: 800; color: #2f4f3a; letter-spacing: 2px; }}
.titulo {{ font-size: 17px; font-weight: 700; color: #2f4f3a; }}
.folio {{ font-size: 15px; font-weight: 700; color: #2f4f3a; }}
.sec {{ font-size: 10px; color: #5b6b60; }}
.bloque {{ background: #ffffff; border-radius: 10px; padding: 12px 16px;
          margin: 12px 26px 0 26px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
          border-left: 4px solid #A9C5C1; }}
.obs .texto {{ color: #374151; }}
.lbl {{ font-weight: 700; color: #5b6b60; font-size: 11px; text-transform: uppercase;
       letter-spacing: 1px; margin-bottom: 4px; }}
table.items {{ width: calc(100% - 52px); margin: 16px 26px 0 26px;
              border-collapse: collapse; table-layout: fixed; }}
table.items th {{ background: linear-gradient(135deg, #A9C5C1 0%, #8FB5B1 100%);
                 color: #ffffff; padding: 8px 10px; font-size: 10px; text-align: center;
                 border: 1px solid #8FB5B1; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }}
table.items th:first-child {{ text-align: left; width: 34%; }}
table.items td {{ border: 1px solid #e4e7e2; padding: 7px 10px; font-size: 11px;
                 text-align: center; background: #ffffff; overflow: hidden; }}
table.items td:first-child {{ text-align: left; }}
table.items tr:nth-child(even) td {{ background: #f7faf6; }}
.resumen {{ margin: 16px 26px 0 26px; width: 260px; margin-left: auto;
           border-collapse: collapse; }}
.resumen td {{ padding: 5px 12px; font-size: 12px; border: 1px solid #e4e7e2;
              background: #ffffff; }}
.resumen .val {{ text-align: right; font-weight: 700; }}
.resumen .fila-total td {{ background: linear-gradient(135deg, #A9C5C1 0%, #8FB5B1 100%);
                          color: #ffffff; font-size: 15px; font-weight: 800; }}
.pie-ancla {{ margin-top: auto; padding-top: 30px; }}
</style></head><body>
<div class='hoja'>

  <!-- Cabecera: ondas superpuestas (menta de fondo, salvia al frente) -->
  <div class='cabecera'>
  <table><tr>
  <td style='width:32%'>
    <div>{logo_html}<span class='marca'>GORETTI</span></div>
    <div class='sec'>SIAC ERP · Sistema Integral de Administración y Control</div>
  </td>
  <td style='width:36%;text-align:center'><span class='titulo'>{titulo}</span></td>
  <td style='width:32%;text-align:right'>
    <div>NO. <span class='folio'>{_esc(datos.get('folio', ''))}</span></div>
    <div>FECHA: <b>{_fmt_fecha(datos.get('fecha_emision', ''))}</b></div>
    <div class='sec'>Estatus: {_esc(estatus)}</div>
  </td>
  </tr></table>
  </div>
  <svg viewBox='0 0 1200 110' preserveAspectRatio='none'
       style='display:block;width:100%;height:110px;margin-top:-44px;position:relative;z-index:1'>
    <!-- Capa de fondo: menta pálido (#D4EDEA) -->
    <path d='M0,40 C160,82 320,8 480,40 C640,82 800,8 960,40 C1120,82 1160,28 1200,50 L1200,110 L0,110 Z'
          fill='#D4EDEA'/>
    <!-- Capa de frente: salvia (#A9C5C1), curvas S superpuestas -->
    <path d='M0,64 C160,106 320,32 480,64 C640,106 800,32 960,64 C1120,106 1160,52 1200,74 L1200,110 L0,110 Z'
          fill='#A9C5C1'/>
  </svg>

  <div class='bloque'>
    <div class='lbl'>Vendido a:</div>
    {vendido_html}
  </div>

  <table class='items'>
  <tr>
    <th style='min-width:170px'>NOMBRE</th>
    {th_tallas}
    <th>TOTAL PARES</th>
    <th>VALOR UNITARIO</th>
    <th>TOTAL</th>
  </tr>
  {rows}
  </table>

  <table class='resumen'>
  <tr><td>Subtotal</td><td class='val'>${subtotal:,.2f}</td></tr>
  {filas_iva}
  <tr class='fila-total'><td>TOTAL</td><td>${total:,.2f}</td></tr>
  </table>

  {obs_html}

  <!-- Pie: ondas superpuestas, anclado al fondo de la hoja -->
  <div class='pie-ancla'>
  <svg viewBox='0 0 1200 90' preserveAspectRatio='none'
       style='display:block;width:100%;height:90px'>
    <!-- Capa de fondo: menta pálido (#D4EDEA) -->
    <path d='M0,28 C160,-10 320,56 480,28 C640,-10 800,56 960,28 C1120,-10 1160,16 1200,6 L1200,90 L0,90 Z'
          fill='#D4EDEA'/>
    <!-- Capa de frente: salvia (#A9C5C1), curvas S superpuestas -->
    <path d='M0,52 C160,14 320,80 480,52 C640,14 800,80 960,52 C1120,14 1160,40 1200,30 L1200,90 L0,90 Z'
          fill='#A9C5C1'/>
  </svg>
  <div style='background:linear-gradient(135deg, #A9C5C1 0%, #D4EDEA 100%);
              padding:6px 28px 22px 28px;'>
    <div style='font-size:14px;font-weight:700;color:#2f4f3a'>Gracias por su compra.</div>
    <div style='font-size:16px;font-weight:800;color:#2f4f3a;letter-spacing:2px;margin-top:2px'>GORETTI</div>
    <div style='font-size:9px;color:#4a6b52;margin-top:4px'>Generado por Goretti ERP el {ahora}</div>
  </div>
  </div>

</div>
</body></html>"""


def print_orden_compra(datos: dict, detalle: list[dict], parent: QWidget) -> None:
    """Abre la vista previa de impresión (componente aprobado `preview_impresion`)
    del reporte de Orden de Compra. Desde el diálogo se puede imprimir o
    exportar a PDF; el PDF se genera por la misma vía que la impresión
    (QTextDocument), así que lo que se ve es lo que sale."""
    from src.components.preview_impresion import previsualizar_html

    previsualizar_html(
        _oc_receipt_html(datos, detalle),
        titulo="Vista previa - Recibo de Orden de Compra",
        parent=parent,
    )


def export_orden_compra_excel(datos: dict, detalle: list[dict], parent: QWidget) -> Optional[str]:
    path, _ = QFileDialog.getSaveFileName(
        parent, "Exportar Excel - Orden de Compra",
        f"OC_{datos.get('folio', '')}.xlsx", "Excel (*.xlsx)")
    if not path:
        return None
    _write_oc_excel(path, datos, detalle)
    return path


def _write_oc_excel(path: str, datos: dict, detalle: list[dict]) -> None:
    from datetime import datetime

    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    solo_remision = bool(datos.get("solo_remision"))
    titulo = "REMI-SIÓN - ORDEN DE COMPRA" if solo_remision else \
        "RECIBO DE COMPRA - ORDEN DE COMPRA"
    columnas = _oc_columnas_tallas(detalle)
    subtotal, iva, total = _oc_totales(detalle, solo_remision)

    n_tallas = len(columnas)
    n_cols = 1 + n_tallas + 3

    navy = PatternFill(start_color="1D4ED8", end_color="1D4ED8", fill_type="solid")
    light = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    blanco = Font(color="FFFFFF")
    bold = Font(bold=True)
    thin = Side(style="thin", color="E2E8F0")
    borde = Border(left=thin, right=thin, top=thin, bottom=thin)
    centro = Alignment(horizontal="center", vertical="center")
    der = Alignment(horizontal="right", vertical="center")

    wb = Workbook()
    ws = wb.active
    ws.title = "OC"
    last = n_cols

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last)
    c = ws.cell(row=1, column=1, value=titulo)
    c.font = Font(bold=True, size=16, color="1D4ED8")
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last)
    c = ws.cell(row=2, column=1,
                value=f"NO. {datos.get('folio', '')}    FECHA: {_fmt_fecha(datos.get('fecha_emision', ''))}")
    c.font = Font(size=11)
    c.alignment = Alignment(horizontal="center", vertical="center")

    fila = 4
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1, value="Vendido a:")
    c.font = Font(bold=True, size=10, color="475569")
    fila += 1

    proveedor = datos.get("proveedor_nombre") or "Compra a inventario"
    lineas = [
        ("empresa", proveedor),
        ("sub", f"Tel: {datos.get('proveedor_telefono') or '—'}"),
        ("sub", f"Email: {datos.get('proveedor_email') or '—'}"),
        ("sub", f"RFC: {datos.get('proveedor_rfc') or '—'}"),
        ("sub", f"Dirección: {datos.get('proveedor_direccion') or '—'}"),
    ]
    for tipo, texto in lineas:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
        c = ws.cell(row=fila, column=1, value=texto)
        c.font = Font(bold=(tipo == "empresa"), size=13 if tipo == "empresa" else 11,
                      color="1F2937" if tipo == "empresa" else "64748B")
        fila += 1

    fila += 1
    header_fila = fila
    ws.cell(row=fila, column=1, value="NOMBRE")
    for i, col in enumerate(columnas):
        ws.cell(row=fila, column=2 + i, value=f"#{col['talla']}")
    ws.cell(row=fila, column=1 + n_tallas + 1, value="TOTAL PARES")
    ws.cell(row=fila, column=1 + n_tallas + 2, value="VALOR UNITARIO")
    ws.cell(row=fila, column=1 + n_tallas + 3, value="TOTAL")
    for col in range(1, last + 1):
        cc = ws.cell(row=fila, column=col)
        cc.font = Font(bold=True, color="FFFFFF", size=10)
        cc.fill = navy
        cc.alignment = centro
        cc.border = borde
    ws.row_dimensions[fila].height = 22
    fila += 1

    for d in detalle:
        por_talla = {int(t["talla_id"]): int(t.get("pares", 0) or 0)
                     for t in d.get("tallas", [])}
        ws.cell(row=fila, column=1, value=d.get("insumo_nombre", ""))
        for i, col in enumerate(columnas):
            ws.cell(row=fila, column=2 + i,
                    value=por_talla.get(int(col["talla_id"]), 0) or "")
        cant = int(d.get("cantidad", 0) or 0)
        precio = float(d.get("precio_unitario", 0) or 0)
        ws.cell(row=fila, column=1 + n_tallas + 1, value=cant)
        ws.cell(row=fila, column=1 + n_tallas + 2, value=precio)
        ws.cell(row=fila, column=1 + n_tallas + 3, value=round(_oc_subtotal_detalle(d), 2))
        for col in range(1, last + 1):
            cc = ws.cell(row=fila, column=col)
            cc.border = borde
            if col > 1:
                cc.alignment = centro if col <= 1 + n_tallas else der
            cc.font = Font(size=10)
        if fila % 2 == 0:
            for col in range(1, last + 1):
                ws.cell(row=fila, column=col).fill = light
        fila += 1

    fila += 1
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=max(1, last - 3))
    c = ws.cell(row=fila, column=1, value="Subtotal")
    c.font = Font(size=11)
    c.alignment = der
    c2 = ws.cell(row=fila, column=last - 2 if last - 2 > 1 else last, value=round(subtotal, 2))
    c2.font = Font(bold=True, size=11)
    c2.alignment = der
    fila += 1

    if not solo_remision:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=max(1, last - 3))
        c = ws.cell(row=fila, column=1, value="IVA (16%)")
        c.font = Font(size=11)
        c.alignment = der
        c2 = ws.cell(row=fila, column=last - 2 if last - 2 > 1 else last, value=iva)
        c2.font = Font(bold=True, size=11)
        c2.alignment = der
        fila += 1

    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=max(1, last - 3))
    c = ws.cell(row=fila, column=1, value="TOTAL")
    c.font = Font(bold=True, size=14, color="FFFFFF")
    c.fill = navy
    c.alignment = der
    c2 = ws.cell(row=fila, column=last - 2 if last - 2 > 1 else last, value=total)
    c2.font = Font(bold=True, size=14, color="FFFFFF")
    c2.fill = navy
    c2.alignment = der
    fila += 2

    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1,
                value=f"Método de pago: {datos.get('metodo_pago') or 'Transferencia bancaria'}")
    c.font = Font(bold=True, size=12, color="1D4ED8")
    fila += 2

    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1, value="Información de Pago")
    c.font = Font(bold=True, size=10, color="475569")
    fila += 1
    for texto in [
        proveedor,
        f"Tel: {datos.get('proveedor_telefono') or '—'}",
        f"Email: {datos.get('proveedor_email') or '—'}",
    ]:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
        c = ws.cell(row=fila, column=1, value=texto)
        c.font = Font(size=11)
        fila += 1

    fila += 2
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1, value="Gracias por su compra.")
    c.font = Font(bold=True, size=14)
    c.alignment = Alignment(horizontal="center")
    fila += 1
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1, value="GORETTI")
    c.font = Font(bold=True, size=16, color="1D4ED8")
    c.alignment = Alignment(horizontal="center")
    fila += 1
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=last)
    c = ws.cell(row=fila, column=1,
                value=f"Generado por Goretti ERP el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.font = Font(size=9, color="94A3B8")
    c.alignment = Alignment(horizontal="center")

    ws.column_dimensions["A"].width = 42
    for i in range(n_tallas):
        ws.column_dimensions[get_column_letter(2 + i)].width = 9
    ws.column_dimensions[get_column_letter(1 + n_tallas + 1)].width = 12
    ws.column_dimensions[get_column_letter(1 + n_tallas + 2)].width = 15
    ws.column_dimensions[get_column_letter(1 + n_tallas + 3)].width = 13

    wb.save(path)
