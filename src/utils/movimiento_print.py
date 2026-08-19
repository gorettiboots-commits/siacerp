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
    """Construye el HTML del documento de movimiento con plantilla mint/salvia."""
    from src.utils.print_template import (
        esc as t_esc, fmt_fecha as t_fmt_fecha,
        html_cabecera, html_ondas_superiores, html_obs_bloque,
        html_pie, wrap_hoja,
    )

    tipo = datos.get('tipo_movimiento', '')
    tipo_label = ('Salida de Inventario' if tipo == 'salida'
                  else 'Cambio de Ubicacion')
    folio = t_esc(datos.get('folio', ''))
    obs = t_esc(datos.get('observaciones', '') or '')

    rows = ""
    for i, d in enumerate(detalle, 1):
        nombre = t_esc(d.get('insumo_nombre', ''))
        codigo = t_esc(d.get('insumo_codigo', ''))
        unidad = t_esc(d.get('unidad_medida', ''))
        cant = d.get('cantidad', 0)
        obs_item = t_esc(d.get('observaciones', '') or '')
        rows += f"""<tr>
            <td style='text-align:center'>{i}</td>
            <td style='text-align:left'>{codigo}</td>
            <td style='text-align:left'>{nombre}</td>
            <td style='text-align:center'>{cant}</td>
            <td style='text-align:center'>{unidad}</td>
            <td style='text-align:left'>{obs_item}</td>
        </tr>"""

    cabecera = html_cabecera(
        "DOCUMENTO DE MOVIMIENTO", folio=folio,
        fecha=datos.get('created_at', ''),
        extra_derecha=f"<b>{tipo_label}</b>")

    obs_html = html_obs_bloque(str(datos.get('observaciones', '') or '').strip())

    contenido = f"""
{cabecera}
{html_ondas_superiores()}

<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">
<tr><td style="padding:0 14mm;">

{obs_html}

<table class='items' width="100%" cellpadding="0" cellspacing="0">
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

<div style='margin:8px 0;font-size:11px;color:#5b6b60'>
  Total de partidas: <b>{len(detalle)}</b>
</div>

</td></tr></table>

{html_pie("Documento de Movimiento")}
"""
    return wrap_hoja(contenido)


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
