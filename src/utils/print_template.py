"""Plantilla base comun para todas las impresiones del sistema.

WYSIWYG: atributos HTML inline (bgcolor, border) para QTextDocument.
Pie anclado al fondo de la hoja con spacer calculado.
"""
import base64
from datetime import datetime
from pathlib import Path


# ── Colores del tema ──────────────────────────────────────────────
_MENTA = "#D4EDEA"
_SALVIA = "#A9C5C1"
_SALVIA_OSCURA = "#8FB5B1"
_VERDE_OSCURO = "#2f4f3a"
_VERDE_MEDIO = "#5b6b60"
_BLANCO = "#ffffff"
_FILA_PAR = "#f7faf6"

# ── Dimensiones de hoja Carta en CSS px (1px = 1/96 pulgada) ─────
# Carta: 215.9 x 279.4 mm = 816 x 1056 CSS px
# @page margin: 0 => contenido va de 0 a 1056
# Pie ocupa ~60 px (linea + texto + padding)
# Cabecera + ondas ~85 px
# Contenido tipico ~350 px
# Spacer = 1056 - 85 - 350 - 60 = 561 px
_ALTURA_HOJA_PX = 1056
_ALTURA_PIE_PX = 60
_ALTURA_CABECERA_PX = 85
_ALTURA_CONTENIDO_TIPICO = 350


# ── Utilidades ────────────────────────────────────────────────────

def esc(texto: str) -> str:
    return (str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def fmt_fecha(fecha: str) -> str:
    s = (fecha or "").strip()
    if not s:
        return ""
    fecha_solo = s.split(" ")[0]
    partes = fecha_solo.split("-")
    if len(partes) == 3 and len(partes[0]) == 4:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return s


def fmt_numero(valor) -> str:
    try:
        num = float(valor)
        return f"{int(num)}" if num.is_integer() else f"{num:,.2f}"
    except (TypeError, ValueError):
        return str(valor or "")


def nombre_empresa() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        return EmpresaModel().nombre_empresa()
    except Exception:
        return "SIAC ERP"


def logo_base64() -> str:
    logo_path = Path(__file__).resolve().parent.parent / "logonew.png"
    if logo_path.exists():
        import base64 as b64
        with open(str(logo_path), "rb") as f:
            return b64.b64encode(f.read()).decode()
    try:
        from src.models.empresa_model import EmpresaModel
        logo = EmpresaModel().obtener("logo")
        if logo:
            return logo
    except Exception:
        pass
    for name in ("logo.png", "logo.jpeg"):
        p = Path(__file__).resolve().parent.parent / "views" / "assets" / name
        if p.exists():
            import base64 as b64
            with open(str(p), "rb") as f:
                return b64.b64encode(f.read()).decode()
    return ""


def ahora_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


# ── CSS Base ──────────────────────────────────────────────────────
CSS_BASE = f"""@page {{ margin: 0; }}
body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11px; color: #374151;
    margin: 0; padding: 0;
}}
.marca {{ font-size: 20px; font-weight: bold; color: {_VERDE_OSCURO}; }}
.titulo {{ font-size: 15px; font-weight: bold; color: {_VERDE_OSCURO}; }}
.folio {{ font-size: 13px; font-weight: bold; color: {_VERDE_OSCURO}; }}
.sec {{ font-size: 9px; color: {_VERDE_MEDIO}; }}
.lbl {{ font-weight: bold; color: {_VERDE_MEDIO}; font-size: 10px;
       text-transform: uppercase; letter-spacing: 1px; }}
"""


# ── Bloques HTML reutilizables ────────────────────────────────────

def html_logo(tam: int = 90) -> str:
    b64 = logo_base64()
    if not b64:
        return ""
    return (f'<img src="data:image/png;base64,{b64}" '
            f'width="{tam}" '
            f'style="vertical-align:middle;margin-right:6px"/>')


def html_cabecera(titulo: str, folio: str = "", fecha: str = "",
                  subtitulo: str = "", extra_derecha: str = "") -> str:
    empresa = nombre_empresa().upper()
    sub = subtitulo or "SIAC ERP - Sistema Integral de Administracion y Control"
    folio_html = ""
    if folio:
        folio_html = f'<div>NO. <span class="folio">{esc(folio)}</span></div>'
    fecha_html = ""
    if fecha:
        fecha_html = f'<div>FECHA: <b>{fmt_fecha(fecha)}</b></div>'
    extra = f"<div class='sec'>{extra_derecha}</div>" if extra_derecha else ""
    logo = html_logo(90)

    return f"""<table width="100%" cellpadding="0" cellspacing="0"
       bgcolor="{_MENTA}" style="border-bottom:3px solid {_SALVIA_OSCURA};margin:0;">
<tr>
<td width="35%" style="padding:14px 16px;">
  {logo}<span class="marca">{empresa}</span>
  <div class="sec">{sub}</div>
</td>
<td width="30%" align="center" style="padding:14px 8px;">
  <span class="titulo">{titulo}</span>
</td>
<td width="35%" align="right" style="padding:14px 16px;">
  {folio_html}{fecha_html}{extra}
</td>
</tr>
</table>"""


def html_ondas_superiores() -> str:
    return (f'<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">'
            f'<tr><td bgcolor="{_MENTA}" style="height:6px;font-size:1px;">&nbsp;</td></tr>'
            f'<tr><td bgcolor="{_SALVIA}" style="height:4px;font-size:1px;">&nbsp;</td></tr>'
            f'</table>')


def html_pie(mensaje: str = "Gracias por su compra.") -> str:
    """Pie con spacer line-height que lo empuja al fondo de la hoja Carta."""
    empresa = nombre_empresa().upper()
    ahora = ahora_str()
    spacer_h = _ALTURA_HOJA_PX - _ALTURA_CABECERA_PX - _ALTURA_CONTENIDO_TIPICO - _ALTURA_PIE_PX
    return f"""<p style="line-height:{spacer_h}px;font-size:1px;margin:0;">&nbsp;</p>
<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">
<tr><td bgcolor="{_SALVIA}" style="height:3px;font-size:1px;">&nbsp;</td></tr>
<tr><td align="center" style="padding:8px 14px;">
  <div style="font-size:12px;color:{_VERDE_OSCURO};font-weight:bold;">{mensaje}</div>
  <div style="font-size:13px;font-weight:bold;color:{_VERDE_OSCURO};letter-spacing:2px;margin-top:2px;">{empresa}</div>
  <div style="font-size:8px;color:{_VERDE_MEDIO};margin-top:3px;">Generado por {nombre_empresa()} el {ahora}</div>
</td></tr>
</table>"""


def html_obs_bloque(observaciones: str) -> str:
    if not observaciones or not observaciones.strip():
        return ""
    return f"""<table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0;">
<tr><td bgcolor="{_BLANCO}" style="padding:8px 12px;border-left:4px solid {_SALVIA};">
  <div class="lbl">Observaciones</div>
  <div style="color:#1f2937;font-size:10px;">
    {esc(observaciones).replace(chr(10), '<br/>')}
  </div>
</td></tr>
</table>"""


def html_tabla_items(th_html: str, rows_html: str) -> str:
    """Tabla de items con estilo inline: fondo salvia en headers,
    filas alternas, bordes en todas las celdas."""
    return f"""<table width="100%" cellpadding="0" cellspacing="0"
       border="0" style="border-collapse:collapse;margin:10px 0;">
<tr bgcolor="{_SALVIA}">
  {th_html}
</tr>
{rows_html}
</table>"""


def th(texto: str, ancho: str = "", alineado: str = "center") -> str:
    """Header de tabla con estilo inline (bgcolor salvia, texto blanco)."""
    w = f' width="{ancho}"' if ancho else ""
    return (f'<td{w} bgcolor="{_SALVIA}" '
            f'style="padding:6px 8px;font-size:9px;font-weight:bold;'
            f'text-align:{alineado};color:#ffffff;'
            f'border:1px solid {_SALVIA_OSCURA};">'
            f'{texto}</td>')


def td(texto: str, alineado: str = "center", es_par: bool = False,
       negrita: bool = False, color: str = "") -> str:
    """Celda de tabla con estilo inline, bordes y fondo alternado."""
    bg = f' bgcolor="{_FILA_PAR}"' if es_par else ""
    fw = "font-weight:bold;" if negrita else ""
    clr = f"color:{color};" if color else ""
    return (f'<td{bg} style="padding:5px 8px;font-size:10px;'
            f'text-align:{alineado};border:1px solid #e4e7e2;{fw}{clr}">'
            f'{texto}</td>')


def td_izq(texto: str, es_par: bool = False) -> str:
    return td(texto, alineado="left", es_par=es_par)


def td_der(texto: str, es_par: bool = False, negrita: bool = False) -> str:
    return td(texto, alineado="right", es_par=es_par, negrita=negrita)


def td_num(texto: str, es_par: bool = False) -> str:
    return td(texto, alineado="center", es_par=es_par)


def wrap_hoja(contenido: str, css_extra: str = "") -> str:
    css = CSS_BASE
    if css_extra:
        css += f"\n{css_extra}"
    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>{css}</style></head>
<body>
{contenido}
</body></html>"""
