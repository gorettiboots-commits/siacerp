"""Impresión en PDF del kardex de un insumo.

Genera el historial de movimientos (entradas/salidas) con saldo acumulado,
reutilizando el patrón QTextDocument + QPrinter de `export_utils.print_table`.
"""
import base64
from pathlib import Path

from PySide6.QtWidgets import QWidget


def imprimir_kardex(insumo: dict, movimientos: list[dict],
                    parent: QWidget | None = None) -> None:
    """Muestra la vista previa del kardex del insumo."""
    from src.components.preview_impresion import previsualizar_html
    titulo = f"Kardex - {insumo.get('codigo', '')} {insumo.get('nombre', '')}".strip()
    previsualizar_html(_html(insumo, movimientos), titulo=titulo, parent=parent)


def _html(insumo: dict, movimientos: list[dict]) -> str:
    logo_b64 = _logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (f'<img src="data:image/jpeg;base64,{logo_b64}" '
                     'style="max-width:70px;max-height:70px;float:right"/>')

    filas = ""
    for m in movimientos:
        tipo = m.get("tipo_movimiento", "")
        etiqueta_tipo = {"entrada": "Entrada", "salida": "Salida",
                         "ajuste": "Ajuste"}.get(tipo, tipo)
        filas += (
            f"<tr><td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_esc(_fmt_fecha(m.get('created_at', '')))}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{etiqueta_tipo}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_fmt_numero(m.get('entrada', 0))}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_fmt_numero(m.get('salida', 0))}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_fmt_numero(m.get('saldo', 0))}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_esc(m.get('referencia_folio', '') or '')}</td>"
            f"<td style='padding:6px;border:1px solid #ddd;font-size:10px'>{_esc(m.get('observaciones', '') or '')}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/></head><body>
<div style='border-bottom:2px solid #4f46e5;padding-bottom:8px;margin-bottom:12px'>
{logo_html}
<h2 style='color:#1e293b;margin:0'>Kardex de insumo</h2>
<p style='color:#64748b;font-size:11px;margin:4px 0'>
{_esc(insumo.get('codigo', ''))} - {_esc(insumo.get('nombre', ''))} &nbsp;|&nbsp;
Unidad: {_esc(insumo.get('unidad_medida', ''))} &nbsp;|&nbsp;
Stock mínimo: {_fmt_numero(insumo.get('stock_minimo', 0))}</p>
</div>
<table style='width:100%;border-collapse:collapse;font-family:Segoe UI,sans-serif'>
<tr><th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Fecha</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Tipo</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Entrada</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Salida</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Saldo</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Referencia</th>
<th style='background:#4f46e5;color:#fff;padding:8px;text-align:center;font-size:11px'>Observaciones</th></tr>
{filas}
</table>
<p style='color:#94a3b8;font-size:9px;margin-top:16px;text-align:center'>
Generado por SIAC ERP - Desarrollado por Mario Felipe Luevano - Todos los derechos reservados</p>
</body></html>"""


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
        return f"{partes[0]}/{partes[1]}/{partes[2]}"
    return s


def _fmt_numero(valor) -> str:
    try:
        num = float(valor)
        if num.is_integer():
            return f"{int(num)}"
        return f"{num:.2f}"
    except (TypeError, ValueError):
        return str(valor or "")


def _esc(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _logo_base64() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        logo = EmpresaModel().obtener('logo')
        if logo:
            return logo
    except Exception:
        pass
    logo_path = Path(__file__).resolve().parent.parent / "views" / "assets" / "logo.jpeg"
    if not logo_path.exists():
        return ""
    with open(str(logo_path), "rb") as f:
        return base64.b64encode(f.read()).decode()
