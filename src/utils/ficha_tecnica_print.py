"""Impresión profesional de la ficha técnica de un modelo.

Genera el HTML del formato de "Hoja de especificación de diseño" con la
identidad visual del sistema (tema menta/salvia de `print_template`) y lo
muestra en el componente aprobado de vista previa de impresión
(`src.components.preview_impresion`), desde donde se puede imprimir o
exportar a PDF.

Secciones del formato:
  • Encabezado institucional (logo, empresa, folio del modelo y fecha).
  • Datos generales (proyecto, etapa, ID de diseño, ref. cliente, color).
  • Fotos de las piezas.
  • Especificaciones agrupadas por sección (corte, bordados, accesorios…).
  • Materiales con cantidad por par, costo unitario, importe y total (opcional).
  • Comentarios y firmas (realizó / recibió).
"""
from datetime import datetime

from PySide6.QtWidgets import QWidget

from src.models.ficha_tecnica_model import CAMPOS_FICHA, CAMPOS_ENCABEZADO

# Etiqueta de sección -> columnas de característica que le pertenecen.
SECCIONES: list[tuple[str, list[str]]] = [
    ("Corte", ["cintilla", "carnuza_chinela", "forro", "piel_corte_1",
               "piel_corte_2", "piel_corte_3", "piel_corte_4",
               "entretela_tubo", "entretela_chinela", "entretela_talon",
               "rebajado_tubo", "rebajado_chinela", "rebajado_talon"]),
    ("Bordados", ["bordado_tubo", "bordado_chinela", "bordado_calzador",
                  "bordado_oreja", "bordado_logo", "hilo_bordado_tubo",
                  "hilo_bordado_chinela", "hilo_bordado_calzador",
                  "hilo_bordado_oreja", "hilo_logo", "hilo_armado",
                  "hilo_sobrecostura"]),
    ("Accesorios", ["vivo", "ribete", "estoperol", "herraje", "acc_1",
                    "acc_2", "acc_3", "acc_4"]),
    ("Suela y estructura", ["puntera", "planta", "contrafuerte", "casco",
                            "suela", "cambrellon", "cerco", "herradura",
                            "landis", "espinazo", "firme", "tacon", "stein",
                            "acabado", "cierre", "cantos"]),
    ("Empaque", ["plantilla", "transfer", "caja", "serigrafia", "bolsa",
                 "soporte", "asadera", "papel_relleno", "colgante"]),
    ("Otros", ["grabado_suela", "barranca", "comentarios", "realizo",
               "recibio"]),
]

# Paleta del tema (misma identidad que src/utils/print_template.py)
_MENTA = "#D4EDEA"
_SALVIA = "#A9C5C1"
_SALVIA_OSCURA = "#8FB5B1"
_VERDE_OSCURO = "#2f4f3a"
_VERDE_MEDIO = "#5b6b60"
_FILA_PAR = "#f7faf6"

# Campos que se muestran fuera de las secciones (comentarios y firmas).
_CAMPOS_FUERA = {"comentarios", "realizo", "recibio"}


def imprimir_ficha_tecnica(modelo: dict, ficha: dict,
                           fotos: dict[str, bytes | None],
                           parent: QWidget | None = None,
                           materiales: list[dict] | None = None) -> None:
    """Abre la vista previa de impresión con la ficha técnica formateada.

    `materiales` es opcional: lista de dicts con llaves `nombre`, `cantidad`,
    `unidad` y `costo`; si se proporciona, el formato incluye la tabla de
    "Materiales y Costos" con su total por par.
    """
    from src.components.preview_impresion import previsualizar_html
    titulo = f"Ficha técnica - {modelo.get('codigo', '')} {modelo.get('nombre', '')}".strip()
    previsualizar_html(_html(modelo, ficha, fotos, materiales),
                       titulo=titulo, parent=parent)


def _html(modelo: dict, ficha: dict, fotos: dict[str, bytes | None],
          materiales: list[dict] | None = None) -> str:
    """Formato profesional de la ficha técnica (tema menta/salvia)."""
    from src.utils.print_template import (
        esc as t_esc, html_cabecera, html_obs_bloque, html_pie,
        html_ondas_superiores, wrap_hoja,
    )

    datos = ficha or {}
    etiquetas = {col: etiqueta for etiqueta, col in CAMPOS_FICHA}

    # ── Encabezado institucional ──────────────────────────────────────
    cabecera = html_cabecera(
        "FICHA TÉCNICA",
        folio=modelo.get("codigo", ""),
        fecha=datetime.now().strftime("%Y-%m-%d"),
        subtitulo=f"Hoja de especificación de diseño — "
                  f"{modelo.get('nombre', '')}".strip(" —"))

    # ── Datos generales (rejilla etiqueta/valor en 2 pares por fila) ──
    celdas_gen: list[str] = []
    for etiqueta, col in CAMPOS_ENCABEZADO:
        celdas_gen.append(
            f"<td width='16%' bgcolor='{_SALVIA}' style='padding:5px 8px;"
            f"font-size:9px;font-weight:bold;color:#ffffff;border:1px solid {_SALVIA_OSCURA};'>"
            f"{t_esc(etiqueta).upper()}</td>"
            f"<td width='34%' style='padding:5px 8px;font-size:10px;"
            f"border:1px solid #e4e7e2;'>{t_esc(_valor(datos, col)) or '&nbsp;'}</td>")
    filas_gen = "".join(
        f"<tr>{''.join(celdas_gen[i:i + 2])}</tr>"
        for i in range(0, len(celdas_gen), 2))
    tabla_generales = (
        f"<div class='lbl' style='margin:14px 0 4px 0;'>Datos generales</div>"
        f"<table width='100%' cellpadding='0' cellspacing='0' "
        f"style='border-collapse:collapse;margin-bottom:6px;'>{filas_gen}</table>")

    # ── Fotos de las piezas ────────────────────────────────────────────
    fotos_html = _html_fotos(fotos)

    # ── Especificaciones por sección ───────────────────────────────────
    filas_specs = ""
    hay_secciones = False
    for titulo_sec, columnas in SECCIONES:
        pares = [(etiquetas.get(col, col), _valor(datos, col))
                 for _, col in CAMPOS_FICHA
                 if col in columnas and col not in _CAMPOS_FUERA]
        if not pares:
            continue
        hay_secciones = True
        filas_specs += (
            f"<tr><td colspan='4' bgcolor='{_MENTA}' style='padding:5px 8px;"
            f"font-size:10px;font-weight:bold;color:{_VERDE_OSCURO};"
            f"border:1px solid {_SALVIA_OSCURA};letter-spacing:1px;'>"
            f"{t_esc(titulo_sec).upper()}</td></tr>")
        for i in range(0, len(pares), 2):
            bloque_par = pares[i:i + 2]
            celdas = ""
            for j, (lbl_campo, valor) in enumerate(bloque_par):
                es_par = (i // 2) % 2 == 1
                bg = f" bgcolor='{_FILA_PAR}'" if es_par else ""
                celdas += (
                    f"<td width='18%'{bg} style='padding:4px 8px;font-size:9px;"
                    f"font-weight:bold;color:{_VERDE_MEDIO};"
                    f"border:1px solid #e4e7e2;text-transform:uppercase;'>"
                    f"{t_esc(lbl_campo)}</td>"
                    f"<td width='32%'{bg} style='padding:4px 8px;font-size:10px;"
                    f"border:1px solid #e4e7e2;'>{t_esc(valor) or '&nbsp;'}</td>")
            filas_specs += f"<tr>{celdas}</tr>"
    specs_html = ""
    if hay_secciones:
        specs_html = (
            f"<div class='lbl' style='margin:14px 0 4px 0;'>Especificaciones</div>"
            f"<table width='100%' cellpadding='0' cellspacing='0' "
            f"style='border-collapse:collapse;margin-bottom:6px;'>{filas_specs}</table>")

    # ── Materiales y costos ────────────────────────────────────────────
    mats_html = _html_materiales(materiales)

    # ── Comentarios y firmas ───────────────────────────────────────────
    comentarios = _valor(datos, "comentarios")
    obs_html = html_obs_bloque(comentarios) if comentarios else ""
    firmas_html = f"""
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:22px;">
<tr>
<td width="50%" align="center" style="padding:0 20px;">
  <div style="border-top:1px solid #374151;margin-top:26px;">&nbsp;</div>
  <div style="font-size:9px;color:{_VERDE_MEDIO};">REALIZÓ&nbsp;&nbsp;&nbsp;
  {t_esc(_valor(datos, 'realizo'))}</div>
</td>
<td width="50%" align="center" style="padding:0 20px;">
  <div style="border-top:1px solid #374151;margin-top:26px;">&nbsp;</div>
  <div style="font-size:9px;color:{_VERDE_MEDIO};">RECIBIÓ&nbsp;&nbsp;&nbsp;
  {t_esc(_valor(datos, 'recibio'))}</div>
</td>
</tr>
</table>"""

    contenido = f"""
{cabecera}
{html_ondas_superiores()}

<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">
<tr><td style="padding:10px 14mm 0 14mm;">
{tabla_generales}
{fotos_html}
{specs_html}
{mats_html}
{obs_html}
{firmas_html}
</td></tr></table>

{html_pie("Ficha Técnica")}
"""
    return wrap_hoja(contenido)


def _optimizar_imagen(datos: bytes, max_px: int) -> tuple[str, str] | None:
    """Redimensiona/comprime una foto para incrustarla en el HTML.

    Devuelve (mime, base64) o None si los bytes no son una imagen válida.
    Las fotos se guardan a resolución de cámara; incrustarlas tal cual
    supera el límite de ~2 MB de QWebEngineView.setHtml y la vista previa
    sale en blanco. Para impresión basta con ~3x su tamaño de despliegue.
    """
    import base64 as b64

    from PySide6.QtCore import QBuffer, Qt
    from PySide6.QtGui import QImage

    img = QImage.fromData(datos)
    if img.isNull():
        return None
    if max(img.width(), img.height()) > max_px:
        img = img.scaled(max_px, max_px, Qt.KeepAspectRatio,
                         Qt.SmoothTransformation)
    buf = QBuffer()
    buf.open(QBuffer.WriteOnly)
    if img.hasAlphaChannel():
        mime = "image/png"
        img.save(buf, "PNG")
    else:
        mime = "image/jpeg"
        img.save(buf, "JPEG", 85)
    return mime, b64.b64encode(bytes(buf.data())).decode()


def _html_fotos(fotos: dict[str, bytes | None]) -> str:
    """Rejilla de fotos: producto terminado grande y piezas alrededor."""

    def _img(tipo: str, ancho_max: int) -> str:
        raw = fotos.get(tipo)
        if not raw:
            return ""
        opt = _optimizar_imagen(raw, ancho_max * 3)
        if opt is None:
            return ""
        mime, img_b64 = opt
        return (f"<img src='data:{mime};base64,{img_b64}' "
                f"style='max-width:{ancho_max}px;max-height:{ancho_max}px;"
                f"border:1px solid #e4e7e2;'/>")

    principal = _img("producto", 220)
    secundarias = ""
    for etiqueta, tipo in (("Tubo", "tubo"), ("Chinela", "chinela"),
                           ("Talón", "talon"), ("Suela", "suela")):
        mini = _img(tipo, 110)
        if not mini:
            continue
        secundarias += (
            f"<td width='25%' align='center'>{mini}"
            f"<div style='font-size:9px;color:{_VERDE_MEDIO};margin-top:2px;'>&nbsp;"
            f"{etiqueta}&nbsp;</div></td>")
    if not principal and not secundarias:
        return ""
    fila_principal = ""
    if principal:
        fila_principal = (
            "<tr><td align='center'>"
            f"{principal}"
            f"<div style='font-size:9px;color:{_VERDE_MEDIO};margin-top:2px;'>&nbsp;"
            f"Producto terminado&nbsp;</div></td></tr>")
    return (
        f"<div class='lbl' style='margin:14px 0 4px 0;'>Fotos de las piezas</div>"
        f"<table width='100%' cellpadding='4' cellspacing='0' "
        f"bgcolor='{_FILA_PAR}' style='border-collapse:collapse;"
        f"border:1px solid #e4e7e2;'>{fila_principal}"
        f"{f'<tr>{secundarias}</tr>' if secundarias else ''}</table>")


def _html_materiales(materiales: list[dict] | None) -> str:
    """Tabla de materiales con cantidad, costo unitario, importe y total."""
    if not materiales:
        return ""

    def td_c(texto: str, alineado: str = "left", es_par: bool = False,
             negrita: bool = False) -> str:
        bg = f" bgcolor='{_FILA_PAR}'" if es_par else ""
        fw = "font-weight:bold;" if negrita else ""
        return (f"<td{bg} style='padding:4px 8px;font-size:10px;"
                f"text-align:{alineado};border:1px solid #e4e7e2;{fw}'>{texto}</td>")

    filas = ""
    total = 0.0
    for i, m in enumerate(materiales):
        es_par = i % 2 == 1
        cantidad = float(m.get("cantidad", 0) or 0)
        costo = float(m.get("costo", 0) or 0)
        importe = cantidad * costo
        total += importe
        filas += (
            "<tr>"
            + td_c(str(m.get("nombre") or ""), "left", es_par)
            + td_c(f"{cantidad:,.2f}", "right", es_par)
            + td_c(str(m.get("unidad") or ""), "center", es_par)
            + td_c(f"${costo:,.2f}", "right", es_par)
            + td_c(f"${importe:,.2f}", "right", es_par)
            + "</tr>")
    filas += (
        f"<tr><td colspan='4' align='right' bgcolor='{_MENTA}' "
        f"style='padding:5px 8px;font-size:10px;font-weight:bold;"
        f"color:{_VERDE_OSCURO};border:1px solid {_SALVIA_OSCURA};'>"
        f"COSTO TOTAL DE MATERIALES POR PAR:</td>"
        f"<td align='right' bgcolor='{_MENTA}' style='padding:5px 8px;"
        f"font-size:11px;font-weight:bold;color:{_VERDE_OSCURO};"
        f"border:1px solid {_SALVIA_OSCURA};'>${total:,.2f}</td></tr>")
    return (
        "<div class='lbl' style='margin:14px 0 4px 0;'>"
        "Materiales · Cantidades y Costos</div>"
        "<table width='100%' cellpadding='0' cellspacing='0' "
        "style='border-collapse:collapse;margin-bottom:6px;'>"
        "<tr>"
        + "".join(
            f"<td bgcolor='{_SALVIA}' style='padding:5px 8px;font-size:9px;"
            f"font-weight:bold;text-align:{al};color:#ffffff;"
            f"border:1px solid {_SALVIA_OSCURA};'>{txt}</td>"
            for txt, al in [("Material", "left"), ("Cant. por par", "right"),
                            ("Unidad", "center"), ("Costo unitario", "right"),
                            ("Importe", "right")])
        + "</tr>"
        + filas
        + "</table>")


def _valor(datos: dict, columna: str) -> str:
    valor = datos.get(columna, "")
    return "" if valor is None else str(valor)
