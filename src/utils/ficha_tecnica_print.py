"""Impresión en PDF de la ficha técnica de un modelo.

Reutiliza el patrón QTextDocument + QPrinter de `export_utils.print_table`
para generar el documento con las fotos de las piezas y los campos de
característica agrupados por sección, como en la plantilla Ficha tecnica.xlsx.
"""
import base64
from pathlib import Path

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


def imprimir_ficha_tecnica(modelo: dict, ficha: dict,
                           fotos: dict[str, bytes | None],
                           parent: QWidget | None = None) -> None:
    """Muestra la vista previa de la ficha técnica."""
    from src.components.preview_impresion import previsualizar_html
    titulo = f"Ficha técnica - {modelo.get('codigo', '')} {modelo.get('nombre', '')}".strip()
    previsualizar_html(_html(modelo, ficha, fotos), titulo=titulo, parent=parent)


def _documento(modelo: dict, ficha: dict, fotos: dict[str, bytes | None]):
    from PySide6.QtGui import QTextDocument
    doc = QTextDocument()
    doc.setHtml(_html(modelo, ficha, fotos))
    return doc


def _html(modelo: dict, ficha: dict, fotos: dict[str, bytes | None]) -> str:
    """Ficha tecnica con plantilla mint/salvia."""
    from src.utils.print_template import (
        esc as t_esc, nombre_empresa as t_empresa, logo_base64,
        html_cabecera, html_ondas_superiores, html_pie, wrap_hoja,
    )

    logo_b64 = logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (f'<img src="data:image/png;base64,{logo_b64}" '
                     'style="max-width:70px;max-height:70px;float:right"/>')

    datos = ficha or {}
    header_cells = "".join(
        f"<td style='padding:4px 8px;border:1px solid #e4e7e2;font-size:10px'>"
        f"<b>{etiqueta}:</b> {t_esc(_valor(datos, col))}</td>"
        for etiqueta, col in CAMPOS_ENCABEZADO
    )
    header_html = (f"<div style='border-bottom:2px solid #A9C5C1;padding-bottom:8px;"
                   f"margin-bottom:12px'>{logo_html}"
                   f"<h2 style='color:#2f4f3a;margin:0'>Ficha Tecnica</h2>"
                   f"<p style='color:#5b6b60;font-size:11px;margin:4px 0'>"
                   f"{modelo.get('codigo', '')} - {modelo.get('nombre', '')}</p></div>")

    tabla_encabezado = (f"<table style='width:100%;border-collapse:collapse;"
                        f"margin-bottom:12px;font-family:Segoe UI,sans-serif'>"
                        f"<tr>{header_cells}</tr></table>")

    secciones_html = ""
    for etiqueta, columnas in SECCIONES:
        celdas = []
        for _, col in CAMPOS_FICHA:
            if col not in columnas:
                continue
            etiqueta_campo = dict(CAMPOS_FICHA)[col]
            celdas.append(
                f"<td style='padding:4px 8px;border:1px solid #e4e7e2;"
                f"font-size:10px'><b>{t_esc(etiqueta_campo)}:</b> "
                f"{t_esc(_valor(datos, col))}</td>")
        filas_html = ""
        for i in range(0, len(celdas), 2):
            filas_html += f"<tr>{''.join(celdas[i:i + 2])}</tr>"
        secciones_html += (f"<div style='margin-bottom:12px'>"
                           f"<h3 style='color:#A9C5C1;font-size:12px;margin:8px 0'>"
                           f"{etiqueta}</h3>"
                           f"<table style='width:100%;border-collapse:collapse;"
                           f"font-family:Segoe UI,sans-serif'>{filas_html}</table></div>")

    fotos_html = ""
    for etiqueta, tipo in (("Producto terminado", "producto"),
                           ("Tubo", "tubo"), ("Chinela", "chinela"),
                           ("Talon", "talon"), ("Suela", "suela")):
        img = fotos.get(tipo)
        if not img:
            continue
        import base64 as b64
        img_b64 = b64.b64encode(img).decode()
        fotos_html += (f"<div style='text-align:center;margin:6px;display:inline-block'>"
                       f"<img src='data:image/png;base64,{img_b64}' "
                       f"style='max-width:160px;max-height:160px;border:1px solid #e4e7e2'/>"
                       f"<p style='font-size:10px;color:#5b6b60;margin:2px 0 0 0'>{etiqueta}</p></div>")
    if fotos_html:
        fotos_html = (f"<div style='margin-bottom:12px'>"
                      f"<h3 style='color:#A9C5C1;font-size:12px;margin:8px 0'>Fotos</h3>"
                      f"{fotos_html}</div>")

    cabecera = html_cabecera(
        "FICHA TECNICA",
        subtitulo=f"{modelo.get('codigo', '')} - {modelo.get('nombre', '')}")

    contenido = f"""
{cabecera}
{html_ondas_superiores()}

<table width="100%" cellpadding="0" cellspacing="0" style="margin:0;">
<tr><td style="padding:0 14mm;">

{header_html}
{tabla_encabezado}
{secciones_html}
{fotos_html}

</td></tr></table>

{html_pie("Ficha Tecnica")}
"""
    return wrap_hoja(contenido)


def _valor(datos: dict, columna: str) -> str:
    valor = datos.get(columna, "")
    return "" if valor is None else str(valor)


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
