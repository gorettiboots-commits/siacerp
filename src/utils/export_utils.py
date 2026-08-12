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
    logo_path = Path(__file__).resolve().parent.parent / "views" / "assets" / "logo.png"
    if not logo_path.exists():
        return ""
    import base64
    with open(str(logo_path), "rb") as f:
        return base64.b64encode(f.read()).decode()


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


def _oc_totales(detalle: list[dict], solo_remision: bool) -> tuple[float, float, float]:
    subtotal = sum(float(d.get("cantidad", 0) or 0) * float(d.get("precio_unitario", 0) or 0)
                   for d in detalle)
    if solo_remision:
        iva = 0.0
    else:
        iva = round(subtotal * 0.16, 2)
    total = round(subtotal + iva, 2)
    return round(subtotal, 2), iva, total


def _oc_receipt_html(datos: dict, detalle: list[dict]) -> str:
    from datetime import datetime

    solo_remision = bool(datos.get("solo_remision"))
    titulo = "REMI-SIÓN - ORDEN DE COMPRA" if solo_remision else \
        "RECIBO DE COMPRA - ORDEN DE COMPRA"
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
                     f'style="max-width:56px;max-height:56px;vertical-align:middle;margin-right:8px"/>')

    th_tallas = "".join(
        f"<th>{_esc('#')}{_esc(c['talla'])}</th>" for c in columnas)

    rows = ""
    for d in detalle:
        por_talla = {int(t["talla_id"]): int(t.get("pares", 0) or 0)
                     for t in d.get("tallas", [])}
        celdas = "".join(
            f"<td class='td-num'>{por_talla.get(int(c['talla_id']), 0) or ''}</td>"
            for c in columnas)
        cant = int(d.get("cantidad", 0) or 0)
        precio = float(d.get("precio_unitario", 0) or 0)
        sub = cant * precio
        rows += f"""<tr>
            <td style='text-align:left'>{_esc(d.get('insumo_nombre', ''))}</td>
            {celdas}
            <td class='td-num'>{cant}</td>
            <td class='td-der'>${precio:,.2f}</td>
            <td class='td-der'>${sub:,.2f}</td>
        </tr>"""

    filas_iva = ""
    if not solo_remision:
        filas_iva = f"""<tr>
            <td class='lbl'>IVA (16%)</td>
            <td class='val'>${iva:,.2f}</td>
        </tr>"""

    datos_proveedor = [l for l in [
        _esc(proveedor),
        (f"Tel: {_esc(telefono)}" if telefono else ""),
        (f"Email: {_esc(email)}" if email else ""),
        (f"RFC: {_esc(rfc)}" if rfc else ""),
        (f"Dirección: {_esc(direccion)}" if direccion else ""),
    ] if l]

    vendido_html = "".join(
        f"<div class='{'empresa' if i == 0 else 'sub'}'>"
        f"{l}</div>" for i, l in enumerate(datos_proveedor))

    info_pago = [l for l in [
        _esc(proveedor),
        (f"Tel: {_esc(telefono)}" if telefono else ""),
        (f"Email: {_esc(email)}" if email else ""),
    ] if l]
    info_pago_html = "".join(f"<div>{l}</div>" for l in info_pago)

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ margin: 14mm; }}
body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 12px; color: #1f2937; margin: 0; }}
.encabezado {{ border-bottom: 3px solid #1d4ed8; padding-bottom: 10px; }}
.encabezado table {{ width: 100%; border-collapse: collapse; }}
.encabezado td {{ vertical-align: middle; }}
.marca {{ font-size: 26px; font-weight: bold; color: #1d4ed8; letter-spacing: 2px; }}
.titulo {{ font-size: 17px; font-weight: bold; color: #1f2937; }}
.titulo2 {{ font-size: 11px; color: #64748b; margin-top: 3px; }}
.no-fecha {{ text-align: right; font-size: 12px; color: #1f2937; }}
.no-fecha .num {{ font-size: 15px; font-weight: bold; color: #1d4ed8; }}
.vendido {{ border: 1px solid #cbd5e1; border-left: 4px solid #1d4ed8; padding: 10px 14px; margin-top: 14px; }}
.vendido .lbl {{ font-weight: bold; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.vendido .empresa {{ font-size: 15px; font-weight: bold; color: #1f2937; }}
.vendido .sub {{ font-size: 12px; color: #64748b; }}
table.items {{ width: 100%; border-collapse: collapse; margin-top: 14px; }}
table.items th {{ background: #1d4ed8; color: #ffffff; padding: 7px 6px; font-size: 10px; text-align: center; border: 1px solid #1d4ed8; }}
table.items td {{ border: 1px solid #e2e8f0; padding: 6px; font-size: 11px; }}
table.items tr:nth-child(even) td {{ background: #f8fafc; }}
.td-num {{ text-align: center; }}
.td-der {{ text-align: right; }}
.resumen {{ margin-top: 14px; margin-left: auto; width: 250px; border-collapse: collapse; }}
.resumen td {{ padding: 5px 10px; font-size: 12px; border: 1px solid #e2e8f0; }}
.resumen .lbl {{ color: #475569; }}
.resumen .val {{ text-align: right; font-weight: bold; }}
.resumen .fila-total td {{ background: #1d4ed8; color: #ffffff; font-size: 15px; font-weight: bold; }}
.metodo {{ margin-top: 16px; font-size: 13px; }}
.metodo b {{ color: #1d4ed8; }}
.pago {{ border: 1px solid #cbd5e1; border-left: 4px solid #16a34a; padding: 10px 14px; margin-top: 10px; font-size: 12px; }}
.pago .lbl {{ font-weight: bold; color: #475569; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
.pie {{ margin-top: 26px; padding-top: 10px; border-top: 2px solid #1d4ed8; text-align: center; }}
.pie .gracias {{ font-size: 14px; font-weight: bold; color: #1f2937; }}
.pie .marca {{ font-size: 16px; font-weight: bold; color: #1d4ed8; letter-spacing: 2px; margin-top: 4px; }}
.pie .leyenda {{ font-size: 9px; color: #94a3b8; margin-top: 4px; }}
</style></head><body>
<div class='encabezado'>
<table><tr>
<td style='width:30%'>
  <div>{logo_html}<span class='marca'>GORETTI</span></div>
  <div class='titulo2'>Sistema Integral de Administración y Control</div>
</td>
<td style='width:40%;text-align:center'>
  <div class='titulo'>{titulo}</div>
</td>
<td class='no-fecha' style='width:30%'>
  <div>NO. <span class='num'>{_esc(datos.get('folio', ''))}</span></div>
  <div>FECHA: <b>{_fmt_fecha(datos.get('fecha_emision', ''))}</b></div>
  <div style='font-size:10px;color:#64748b'>Estatus: {_esc(estatus)}</div>
</td>
</tr></table>
</div>

<div class='vendido'>
  <div class='lbl'>Vendido a:</div>
  {vendido_html}
</div>

<table class='items'>
<tr>
  <th style='text-align:left;min-width:170px'>NOMBRE</th>
  {th_tallas}
  <th>TOTAL PARES</th>
  <th>VALOR UNITARIO</th>
  <th>TOTAL</th>
</tr>
{rows}
</table>

<table class='resumen'>
<tr><td class='lbl'>Subtotal</td><td class='val'>${subtotal:,.2f}</td></tr>
{filas_iva}
<tr class='fila-total'><td>TOTAL</td><td>${total:,.2f}</td></tr>
</table>

<div class='metodo'>Método de pago: <b>{_esc(datos.get('metodo_pago') or 'Transferencia bancaria')}</b></div>

<div class='pago'>
  <div class='lbl'>Información de Pago</div>
  {info_pago_html}
</div>

<div class='pie'>
  <div class='gracias'>Gracias por su compra.</div>
  <div class='marca'>GORETTI</div>
  <div class='leyenda'>Generado por Goretti ERP el {ahora}</div>
</div>
</body></html>"""


def print_orden_compra(datos: dict, detalle: list[dict], parent: QWidget) -> None:
    path, _ = QFileDialog.getSaveFileName(
        parent, "Guardar PDF - Orden de Compra",
        f"OC_{datos.get('folio', '')}.pdf", "PDF (*.pdf)")
    if not path:
        return

    doc = QTextDocument()
    doc.setHtml(_oc_receipt_html(datos, detalle))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPageSize.Letter)
    printer.setPageOrientation(QPageLayout.Landscape
                               if len(_oc_columnas_tallas(detalle)) > 6
                               else QPageLayout.Portrait)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    doc.print_(printer)


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
        ws.cell(row=fila, column=1 + n_tallas + 3, value=round(cant * precio, 2))
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
