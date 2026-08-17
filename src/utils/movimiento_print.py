"""Generador de PDF para documentos de movimiento de inventario.

Genera un documento estilo orden de compra con encabezado (logo, marca,
folio, fecha, tipo), tabla de partidas y pie de página.
"""
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QWidget


def _logo_base64() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        logo = EmpresaModel().obtener('logo')
        if logo:
            return logo
    except Exception:
        pass
    logo_path = (Path(__file__).resolve().parent.parent
                 / "views" / "assets" / "logo.jpeg")
    if not logo_path.exists():
        return ""
    import base64
    with open(str(logo_path), "rb") as f:
        return base64.b64encode(f.read()).decode()


def _nombre_empresa() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        return EmpresaModel().nombre_empresa()
    except Exception:
        return "SIAC ERP"


def _esc(texto: str) -> str:
    return (str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _fmt_fecha(fecha: str) -> str:
    s = (fecha or "").strip()
    if not s:
        return ""
    fecha_solo = s.split(" ")[0]
    partes = fecha_solo.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        anio, mes, dia = partes
        return f"{dia}/{mes}/{anio}"
    return fecha_solo


def _movimiento_html(datos: dict, detalle: list[dict]) -> str:
    """Construye el HTML del documento de movimiento."""
    logo_b64 = _logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (
            f'<img src="data:image/jpeg;base64,{logo_b64}" '
            f'style="max-width:56px;max-height:56px;vertical-align:middle;'
            f'margin-right:8px"/>')

    tipo = datos.get('tipo_movimiento', '')
    tipo_label = ('Salida de Inventario' if tipo == 'salida'
                  else 'Cambio de Ubicacion')
    folio = _esc(datos.get('folio', ''))
    fecha_raw = datos.get('created_at', '')
    fecha = _esc(_fmt_fecha(fecha_raw))
    obs = _esc(datos.get('observaciones', '') or '')
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    rows = ""
    for i, d in enumerate(detalle, 1):
        nombre = _esc(d.get('insumo_nombre', ''))
        codigo = _esc(d.get('insumo_codigo', ''))
        unidad = _esc(d.get('unidad_medida', ''))
        cant = d.get('cantidad', 0)
        obs_item = _esc(d.get('observaciones', '') or '')
        rows += f"""<tr>
            <td style='text-align:center'>{i}</td>
            <td style='text-align:left'>{codigo}</td>
            <td style='text-align:left'>{nombre}</td>
            <td style='text-align:center'>{cant}</td>
            <td style='text-align:center'>{unidad}</td>
            <td style='text-align:left'>{obs_item}</td>
        </tr>"""

    obs_block = ""
    if obs:
        obs_block = (
            f"<div style='margin:8px 0;padding:8px 12px;background:#f8fafc;"
            f"border-left:3px solid #1d4ed8;font-size:11px'>"
            f"<b>Observaciones:</b> {obs}</div>")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ margin: 14mm; }}
body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 12px;
        color: #1f2937; margin: 0; }}
.encabezado {{ border-bottom: 3px solid #1d4ed8; padding-bottom: 10px; }}
.encabezado table {{ width: 100%; border-collapse: collapse; }}
.encabezado td {{ vertical-align: middle; }}
.marca {{ font-size: 26px; font-weight: bold; color: #1d4ed8;
          letter-spacing: 2px; }}
.titulo {{ font-size: 17px; font-weight: bold; color: #1f2937; }}
.titulo2 {{ font-size: 11px; color: #64748b; margin-top: 3px; }}
.no-fecha {{ text-align: right; font-size: 12px; color: #1f2937; }}
.num {{ font-size: 18px; font-weight: bold; color: #1d4ed8; }}
table.items {{ width: 100%; border-collapse: collapse; margin-top: 12px;
               font-size: 11px; }}
table.items th {{ background: #111827; color: #fff; text-align: left;
                  padding: 7px 6px; font-size: 11px; }}
table.items td {{ border: 1px solid #e5e7eb; padding: 6px; }}
.pie {{ border-top: 2px solid #1d4ed8; padding-top: 10px;
        margin-top: 20px; text-align: center; font-size: 11px;
        color: #64748b; }}
.pie .marca {{ font-size: 13px; color: #1d4ed8; }}
</style></head><body>

<div class='encabezado'>
<table><tr>
<td style='width:30%'>
  {logo_html}<span class='marca'>{_nombre_empresa().upper()}</span>
  <div class='titulo2'>Sistema Integral de Administracion y Control</div>
</td>
<td style='width:40%;text-align:center'>
  <div class='titulo'>DOCUMENTO DE MOVIMIENTO</div>
  <div style='font-size:12px;color:#1f2937;margin-top:4px'>
    <b>{tipo_label}</b></div>
</td>
<td class='no-fecha' style='width:30%'>
  <div>NO. <span class='num'>{folio}</span></div>
  <div>FECHA: <b>{fecha}</b></div>
</td>
</tr></table>
</div>

{obs_block}

<table class='items'>
<tr>
  <th style='text-align:center;width:40px'>#</th>
  <th style='text-align:left;width:100px'>CODIGO</th>
  <th style='text-align:left'>NOMBRE</th>
  <th style='text-align:center;width:80px'>CANTIDAD</th>
  <th style='text-align:center;width:80px'>UNIDAD</th>
  <th style='text-align:left;width:200px'>OBSERVACIONES</th>
</tr>
{rows}
</table>

<div style='margin-top:8px;font-size:11px;color:#64748b'>
  Total de partidas: <b>{len(detalle)}</b>
</div>

<div class='pie'>
  <div class='marca'>{_nombre_empresa().upper()}</div>
  <div>Generado por {_nombre_empresa()} el {ahora}</div>
</div>

</body></html>"""


def imprimir_movimiento_documento(movimiento_id: int,
                                  parent: QWidget | None = None) -> None:
    """Muestra la vista previa de un documento de movimiento multi-partida.

    Parameters
    ----------
    movimiento_id : int
        ID del grupo de movimientos (``movimientos_inventario.id``).
    parent : QWidget | None
        Widget padre para el diálogo de vista previa.
    """
    from src.components.preview_impresion import previsualizar_html
    from src.models.movimiento_inventario_model import (
        MovimientoInventarioGrupoModel,
    )
    model = MovimientoInventarioGrupoModel()
    datos = model.obtener_grupo(movimiento_id)
    if not datos:
        return

    folio = datos.get('folio', 'MVI')
    detalle = datos.get('detalle', [])
    previsualizar_html(
        _movimiento_html(datos, detalle),
        titulo=f"Documento de Movimiento {folio}",
        parent=parent,
    )
