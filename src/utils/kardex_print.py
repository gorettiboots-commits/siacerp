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
    """Kardex del insumo con plantilla mint/salvia."""
    from src.utils.print_template import (
        esc as t_esc, fmt_fecha as t_fmt_fecha, fmt_numero as t_fmt_numero,
        html_cabecera, html_ondas_superiores, html_pie, wrap_hoja,
    )

    filas = ""
    for m in movimientos:
        tipo = m.get("tipo_movimiento", "")
        etiqueta_tipo = {"entrada": "Entrada", "salida": "Salida",
                         "ajuste": "Ajuste"}.get(tipo, tipo)
        filas += (
            f"<tr>"
            f"<td>{t_fmt_fecha(m.get('created_at', ''))}</td>"
            f"<td>{etiqueta_tipo}</td>"
            f"<td>{t_fmt_numero(m.get('entrada', 0))}</td>"
            f"<td>{t_fmt_numero(m.get('salida', 0))}</td>"
            f"<td style='font-weight:700'>{t_fmt_numero(m.get('saldo', 0))}</td>"
            f"<td>{t_esc(m.get('referencia_folio', '') or '')}</td>"
            f"<td>{t_esc(m.get('observaciones', '') or '')}</td>"
            f"</tr>"
        )

    cabecera = html_cabecera(
        "KARDEX DE INSUMO",
        subtitulo=f"{t_esc(insumo.get('codigo', ''))} - {t_esc(insumo.get('nombre', ''))} | "
                  f"Unidad: {t_esc(insumo.get('unidad_medida', ''))} | "
                  f"Stock minimo: {t_fmt_numero(insumo.get('stock_minimo', 0))}")

    contenido = f"""
{cabecera}
{html_ondas_superiores()}

<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">
<tr><td style="padding:0 14mm;">

<table class='items' width="100%" cellpadding="0" cellspacing="0">
<tr>
  <th>Fecha</th>
  <th>Tipo</th>
  <th>Entrada</th>
  <th>Salida</th>
  <th>Saldo</th>
  <th>Referencia</th>
  <th>Observaciones</th>
</tr>
{filas}
</table>

</td></tr></table>

{html_pie("Kardex de Insumo")}
"""
    return wrap_hoja(contenido)


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
