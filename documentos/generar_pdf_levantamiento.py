"""Generador de PDF del documento de levantamiento SIAC ERP.

Convierte el archivo markdown a un PDF profesional con estilo corporativo.
"""
import re
from functools import partial
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import legal
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

# ── Colores corporativos ───────────────────────────────────────────
NAVY = colors.HexColor("#1e3a5f")
BLUE = colors.HexColor("#2563eb")
LIGHT_BLUE = colors.HexColor("#dbeafe")
GRAY_BG = colors.HexColor("#f1f5f9")
WHITE = colors.white
BLACK = colors.HexColor("#1f2937")
DARK_GRAY = colors.HexColor("#374151")
MID_GRAY = colors.HexColor("#6b7280")
LIGHT_GRAY = colors.HexColor("#e5e7eb")
BORDER = colors.HexColor("#cbd5e1")


def _crear_estilos():
    """Estilos de párrafo reutilizables."""
    base = getSampleStyleSheet()
    estilos = {}

    estilos["portada_titulo"] = ParagraphStyle(
        "portada_titulo", parent=base["Title"],
        fontSize=28, leading=34, textColor=NAVY,
        alignment=TA_CENTER, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    estilos["portada_sub"] = ParagraphStyle(
        "portada_sub", parent=base["Normal"],
        fontSize=14, leading=18, textColor=BLUE,
        alignment=TA_CENTER, spaceAfter=4,
        fontName="Helvetica",
    )
    estilos["portada_info"] = ParagraphStyle(
        "portada_info", parent=base["Normal"],
        fontSize=11, leading=16, textColor=DARK_GRAY,
        alignment=TA_CENTER, spaceAfter=3,
        fontName="Helvetica",
    )
    estilos["proceso_titulo"] = ParagraphStyle(
        "proceso_titulo", parent=base["Heading1"],
        fontSize=18, leading=22, textColor=NAVY,
        spaceBefore=16, spaceAfter=8,
        fontName="Helvetica-Bold",
        borderWidth=0, borderColor=BLUE, borderPadding=4,
    )
    estilos["seccion"] = ParagraphStyle(
        "seccion", parent=base["Heading2"],
        fontSize=13, leading=16, textColor=BLUE,
        spaceBefore=12, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    estilos["subseccion"] = ParagraphStyle(
        "subseccion", parent=base["Heading3"],
        fontSize=11, leading=14, textColor=DARK_GRAY,
        spaceBefore=8, spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    estilos["texto"] = ParagraphStyle(
        "texto", parent=base["Normal"],
        fontSize=9.5, leading=13, textColor=BLACK,
        spaceAfter=4, fontName="Helvetica",
    )
    estilos["texto_bold"] = ParagraphStyle(
        "texto_bold", parent=base["Normal"],
        fontSize=9.5, leading=13, textColor=BLACK,
        spaceAfter=4, fontName="Helvetica-Bold",
    )
    estilos["regla"] = ParagraphStyle(
        "regla", parent=base["Normal"],
        fontSize=9, leading=12, textColor=DARK_GRAY,
        spaceAfter=2, fontName="Helvetica",
        leftIndent=8,
    )
    estilos["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"],
        fontSize=7.5, leading=10, textColor=MID_GRAY,
        alignment=TA_CENTER, fontName="Helvetica",
    )
    estilos["firma"] = ParagraphStyle(
        "firma", parent=base["Normal"],
        fontSize=10, leading=14, textColor=BLACK,
        fontName="Helvetica",
    )
    return estilos


def _fmt(texto: str) -> str:
    """Limpia markdown inline: bold, italic, code."""
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"`(.+?)`", r'<font face="Courier" size="8" color="#7c3aed">\1</font>', texto)
    return texto


def _parsear_tabla(lineas: list[str]) -> list[list[str]]:
    """Convierte líneas markdown de tabla a lista de listas."""
    resultado = []
    for linea in lineas:
        linea = linea.strip()
        if not linea.startswith("|"):
            continue
        celdas = [c.strip() for c in linea.split("|")[1:-1]]
        # Saltar separador (---|---|---)
        if all(re.match(r"^-+$", c) for c in celdas):
            continue
        resultado.append(celdas)
    return resultado


def _construir_tabla(data: list[list[str]], estilos: dict) -> Table:
    """Construye un Table de reportlab con estilo corporativo."""
    # Convertir celdas a Paragraphs para wrapping
    celda_style = ParagraphStyle(
        "celda", parent=estilos["texto"],
        fontSize=8.5, leading=11, spaceAfter=0,
    )
    celda_bold = ParagraphStyle(
        "celda_bold", parent=celda_style,
        fontName="Helvetica-Bold", textColor=WHITE,
    )

    tabla_data = []
    for i, fila in enumerate(data):
        fila_paras = []
        for celda in fila:
            celda_texto = _fmt(celda)
            if i == 0:
                fila_paras.append(Paragraph(celda_texto, celda_bold))
            else:
                fila_paras.append(Paragraph(celda_texto, celda_style))
        tabla_data.append(fila_paras)

    n_cols = max(len(f) for f in tabla_data) if tabla_data else 1
    col_width = (17 * cm) / n_cols

    t = Table(tabla_data, colWidths=[col_width] * n_cols, repeatRows=1)

    estilo_base = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]
    # Filas alternas
    for i in range(1, len(tabla_data)):
        if i % 2 == 0:
            estilo_base.append(("BACKGROUND", (0, i), (-1, i), GRAY_BG))

    t.setStyle(TableStyle(estilo_base))
    return t


def _footer(canvas, doc, empresa: str = "GORETTI"):
    """Pie de página en todas las hojas."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MID_GRAY)
    canvas.drawCentredString(
        legal[0] / 2, 1.2 * cm,
        f"Documento de Levantamiento — SIAC ERP v1.0 — {empresa} — Página {doc.page}"
    )
    canvas.setStrokeColor(LIGHT_GRAY)
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, 1.6 * cm, legal[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def _portada(canvas, doc, empresa: str = "GORETTI"):
    """Portada del documento."""
    canvas.saveState()
    # Fondo azul oscuro superior
    canvas.setFillColor(NAVY)
    canvas.rect(0, legal[1] - 6 * cm, legal[0], 6 * cm, fill=1, stroke=0)
    # Línea decorativa
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(3)
    canvas.line(2 * cm, legal[1] - 6.5 * cm, legal[0] - 2 * cm, legal[1] - 6.5 * cm)
    canvas.restoreState()


def generar_pdf(ruta_md: str | None = None, ruta_pdf: str | None = None,
                empresa: str = "GORETTI") -> str:
    """Genera el PDF del documento de levantamiento en tamaño oficio.

    Parameters
    ----------
    ruta_md : str | None
        Ruta al archivo markdown. Si es None, usa la ruta por defecto.
    ruta_pdf : str | None
        Ruta de salida del PDF. Si es None, genera junto al markdown.
    empresa : str
        Nombre de la empresa (aparece en portada, footer y contenido).

    Returns
    -------
    str
        Ruta del PDF generado.
    """
    base = Path(__file__).resolve().parent
    if ruta_md is None:
        ruta_md = str(base / "Levantamiento_Sistema_SIAC_ERP.md")
    if ruta_pdf is None:
        ruta_pdf = str(base / f"Levantamiento_Sistema_{empresa.upper().replace(' ', '_')}.pdf")

    with open(ruta_md, "r", encoding="utf-8") as f:
        lineas_md = f.readlines()

    # Reemplazar "GORETTI" por la empresa indicada en el contenido
    lineas_md = [
        l.replace("GORETTI", empresa) for l in lineas_md
    ]

    estilos = _crear_estilos()

    doc = BaseDocTemplate(
        ruta_pdf, pagesize=legal,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title=f"Documento de Levantamiento — {empresa}",
        author="Mario Felipe Luevano",
        subject=f"Levantamiento de requerimientos del sistema SIAC ERP — {empresa}",
    )

    frame_contenido = Frame(
        2 * cm, 2.5 * cm,
        legal[0] - 4 * cm, legal[1] - 5 * cm,
        id="contenido",
    )
    frame_portada = Frame(
        2 * cm, 2.5 * cm,
        legal[0] - 4 * cm, legal[1] - 7 * cm,
        id="portada",
    )

    doc.addPageTemplates([
        PageTemplate(id="Portada", frames=[frame_portada],
                     onPage=partial(_portada, empresa=empresa)),
        PageTemplate(id="Contenido", frames=[frame_contenido],
                     onPage=partial(_footer, empresa=empresa)),
    ])

    # ── Construir elementos ──────────────────────────────────────────
    elementos: list = []
    i = 0
    en_portada = True
    tabla_buffer: list[str] = []
    buffer_texto: list[str] = []

    def _flush_texto():
        nonlocal buffer_texto
        if buffer_texto:
            txt = " ".join(buffer_texto)
            txt = _fmt(txt)
            if txt.strip():
                elementos.append(Paragraph(txt, estilos["texto"]))
            buffer_texto = []

    def _flush_tabla():
        nonlocal tabla_buffer
        if tabla_buffer:
            data = _parsear_tabla(tabla_buffer)
            if data:
                elementos.append(Spacer(1, 4 * mm))
                elementos.append(_construir_tabla(data, estilos))
                elementos.append(Spacer(1, 4 * mm))
            tabla_buffer = []

    while i < len(lineas_md):
        linea = lineas_md[i].rstrip("\n")

        # ── Separador horizontal ──
        if linea.strip() == "---":
            _flush_texto()
            _flush_tabla()
            i += 1
            continue

        # ── Tabla markdown ──
        if linea.strip().startswith("|"):
            _flush_texto()
            tabla_buffer.append(linea)
            i += 1
            continue
        else:
            _flush_tabla()

        # ── Portada ──
        if en_portada:
            if linea.startswith("# ") and "LEVANTAMIENTO" in linea:
                titulo = linea.lstrip("# ").strip()
                elementos.append(Spacer(1, 2 * cm))
                elementos.append(Paragraph(titulo, estilos["portada_titulo"]))
                i += 1
                continue
            if linea.startswith("## ") and "Integral" in linea:
                sub = linea.lstrip("# ").strip()
                elementos.append(Paragraph(sub, estilos["portada_sub"]))
                i += 1
                continue
            if linea.startswith("**"):
                txt = re.sub(r"\*\*(.+?)\*\*", r"\1", linea).strip()
                elementos.append(Paragraph(txt, estilos["portada_info"]))
                i += 1
                continue
            if linea.strip() == "" and len(elementos) > 3:
                en_portada = False
                elementos.append(NextPageTemplate("Contenido"))
                elementos.append(PageBreak())
                i += 1
                continue
            if linea.strip() == "":
                i += 1
                continue
            # Otro texto de portada
            txt = _fmt(linea.strip())
            if txt:
                elementos.append(Paragraph(txt, estilos["portada_info"]))
            i += 1
            continue

        # ── Títulos ──
        if linea.startswith("# ") and not en_portada:
            _flush_texto()
            titulo = linea.lstrip("# ").strip()
            elementos.append(Spacer(1, 6 * mm))
            # Línea decorativa
            elementos.append(Paragraph(
                '<font color="#2563eb">━</font>' * 60,
                ParagraphStyle("linea", fontSize=6, leading=8,
                               textColor=BLUE, spaceAfter=2)
            ))
            elementos.append(Paragraph(titulo, estilos["proceso_titulo"]))
            i += 1
            continue

        if linea.startswith("## "):
            _flush_texto()
            titulo = linea.lstrip("# ").strip()
            elementos.append(Paragraph(_fmt(titulo), estilos["seccion"]))
            i += 1
            continue

        if linea.startswith("### "):
            _flush_texto()
            titulo = linea.lstrip("# ").strip()
            elementos.append(Paragraph(_fmt(titulo), estilos["subseccion"]))
            i += 1
            continue

        # ── Línea vacía ──
        if linea.strip() == "":
            _flush_texto()
            i += 1
            continue

        # ── Texto normal ──
        buffer_texto.append(linea.strip())
        i += 1

    _flush_texto()
    _flush_tabla()

    # ── Página de firmas ──
    elementos.append(PageBreak())
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph("FIRMAS DE APROBACIÓN", estilos["proceso_titulo"]))
    elementos.append(Spacer(1, 1 * cm))

    firmas = [
        ("Gerente General", ""),
        ("Gerente de Producción", ""),
        ("Gerente de Compras", ""),
        ("Encargado de Inventario", ""),
        ("Area de Sistemas", ""),
    ]

    for rol, nombre in firmas:
        elementos.append(Spacer(1, 1.5 * cm))
        elementos.append(Paragraph(
            f"<b>{rol}</b>", estilos["firma"]
        ))
        elementos.append(Spacer(1, 0.8 * cm))
        # Línea de firma
        datos_firma = [
            ["_" * 40, "_" * 20],
            ["Firma", "Fecha"],
        ]
        t_firma = Table(datos_firma, colWidths=[10 * cm, 5 * cm])
        t_firma.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), MID_GRAY),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elementos.append(t_firma)

    doc.build(elementos)
    print(f"PDF generado: {ruta_pdf}")
    return ruta_pdf


if __name__ == "__main__":
    generar_pdf(empresa="GORETTI")
    generar_pdf(empresa="ESKINBOOTS")
