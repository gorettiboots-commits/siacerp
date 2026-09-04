"""
Generador del Manual de Usuario SIAC ERP en PDF.
Ejecutar: python scripts/generar_manual_usuario.py
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Colores del sistema ──────────────────────────────────────────────
INDIGO = HexColor("#4F46E5")
INDIGO_CLARO = HexColor("#E0E7FF")
VIOLETA = HexColor("#7C3AED")
VERDE = HexColor("#16A34A")
VERDE_CLARO = HexColor("#DCFCE7")
AMARILLO = HexColor("#EAB308")
AMARILLO_CLARO = HexColor("#FEF9C3")
CYAN = HexColor("#06B6D4")
ROJO = HexColor("#DC2626")
ROJO_CLARO = HexColor("#FEE2E2")
GRIS_OSCURO = HexColor("#1F2937")
GRIS_MEDIO = HexColor("#6B7280")
GRIS_CLARO = HexColor("#F3F4F6")
BLANCO = white
NEGRO = black
AZUL_CLARO = HexColor("#DBEAFE")

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "Manual_Usuario_SIAC_ERP.pdf")

# ── Estilos ──────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

estilo_titulo_portada = ParagraphStyle(
    "TituloPortada", parent=styles["Title"],
    fontSize=32, leading=40, textColor=INDIGO,
    spaceAfter=12, alignment=TA_CENTER, fontName="Helvetica-Bold"
)
estilo_subtitulo_portada = ParagraphStyle(
    "SubtituloPortada", parent=styles["Normal"],
    fontSize=14, leading=18, textColor=GRIS_MEDIO,
    spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica"
)
estilo_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=22, leading=28, textColor=INDIGO,
    spaceBefore=24, spaceAfter=12, fontName="Helvetica-Bold",
    borderWidth=0, borderPadding=0
)
estilo_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=16, leading=22, textColor=GRIS_OSCURO,
    spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold"
)
estilo_h3 = ParagraphStyle(
    "H3", parent=styles["Heading3"],
    fontSize=13, leading=17, textColor=HexColor("#374151"),
    spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold"
)
estilo_h4 = ParagraphStyle(
    "H4", parent=styles["Heading4"],
    fontSize=11, leading=15, textColor=HexColor("#4B5563"),
    spaceBefore=8, spaceAfter=4, fontName="Helvetica-BoldOblique"
)
estilo_cuerpo = ParagraphStyle(
    "Cuerpo", parent=styles["Normal"],
    fontSize=10, leading=14, textColor=GRIS_OSCURO,
    spaceAfter=6, alignment=TA_JUSTIFY, fontName="Helvetica"
)
estilo_cuerpo_negrita = ParagraphStyle(
    "CuerpoNegrita", parent=estilo_cuerpo,
    fontName="Helvetica-Bold"
)
estilo_lista = ParagraphStyle(
    "Lista", parent=estilo_cuerpo,
    leftIndent=20, bulletIndent=8, spaceAfter=3
)
estilo_nota = ParagraphStyle(
    "Nota", parent=estilo_cuerpo,
    fontSize=9, leading=12, textColor=HexColor("#6B7280"),
    leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=8,
    backColor=GRIS_CLARO, borderPadding=6, fontName="Helvetica-Oblique"
)
estilo_codigo = ParagraphStyle(
    "Codigo", parent=estilo_cuerpo,
    fontName="Courier", fontSize=9, leading=12,
    backColor=GRIS_CLARO, borderPadding=6,
    leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=8
)
estilo_pie = ParagraphStyle(
    "Pie", parent=styles["Normal"],
    fontSize=8, textColor=GRIS_MEDIO, alignment=TA_CENTER
)
estilo_tip = ParagraphStyle(
    "Tip", parent=estilo_cuerpo,
    fontSize=9, leading=13, leftIndent=12, rightIndent=12,
    spaceBefore=4, spaceAfter=8, borderPadding=6,
    backColor=VERDE_CLARO, textColor=HexColor("#166534"),
    fontName="Helvetica"
)
estilo_advertencia = ParagraphStyle(
    "Advertencia", parent=estilo_cuerpo,
    fontSize=9, leading=13, leftIndent=12, rightIndent=12,
    spaceBefore=4, spaceAfter=8, borderPadding=6,
    backColor=ROJO_CLARO, textColor=ROJO,
    fontName="Helvetica-Bold"
)
estilo_atajo = ParagraphStyle(
    "Atajo", parent=estilo_cuerpo,
    fontSize=9, fontName="Courier-Bold", textColor=INDIGO
)

# ── Utilidades ───────────────────────────────────────────────────────
def _separador():
    return HRFlowable(width="100%", thickness=1, color=INDIGO_CLARO,
                       spaceBefore=8, spaceAfter=8)

def _tabla(headers, filas, ancho_cols=None):
    """Tabla estilizada con encabezado indigo."""
    data = [headers] + filas
    t = Table(data, colWidths=ancho_cols, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
        ("TEXTCOLOR", (0, 0), (-1, 0), BLANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(estilo))
    return t

def _tabla_simple(headers, filas, ancho_cols=None):
    """Tabla sin fondo de encabezado."""
    data = [headers] + filas
    t = Table(data, colWidths=ancho_cols, repeatRows=1)
    estilo = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, HexColor("#E5E7EB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    t.setStyle(TableStyle(estilo))
    return t

def _tip(texto):
    return Paragraph(f"<b>Tip:</b> {texto}", estilo_tip)

def _nota(texto):
    return Paragraph(f"<i>{texto}</i>", estilo_nota)

def _adv(texto):
    return Paragraph(f"! {texto}", estilo_advertencia)

def _p(texto, estilo=None):
    return Paragraph(texto, estilo or estilo_cuerpo)

def _h1(t):
    return Paragraph(t, estilo_h1)

def _h2(t):
    return Paragraph(t, estilo_h2)

def _h3(t):
    return Paragraph(t, estilo_h3)

def _h4(t):
    return Paragraph(t, estilo_h4)

def _lista(items):
    return [Paragraph(f"  {i}", estilo_lista) for i in items]

def _bullet_list(items):
    result = []
    for i in items:
        result.append(Paragraph(f"\u2022  {i}", estilo_lista))
    return result

def _numero_list(items):
    result = []
    for idx, i in enumerate(items, 1):
        result.append(Paragraph(f"{idx}.  {i}", estilo_lista))
    return result

# ── Pie de pagina ────────────────────────────────────────────────────
def _pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS_MEDIO)
    canvas.drawString(inch, 0.5 * inch, "SIAC ERP - Manual de Usuario v1.0")
    canvas.drawRightString(letter[0] - inch, 0.5 * inch,
                           f"Pagina {doc.page}")
    canvas.setStrokeColor(INDIGO_CLARO)
    canvas.setLineWidth(0.5)
    canvas.line(inch, 0.6 * inch, letter[0] - inch, 0.6 * inch)
    canvas.restoreState()

def _cabecera(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(INDIGO)
    canvas.setLineWidth(2)
    canvas.line(inch, letter[1] - 0.5 * inch,
                letter[0] - inch, letter[1] - 0.5 * inch)
    canvas.restoreState()

# ══════════════════════════════════════════════════════════════════════
# CONTENIDO DEL MANUAL
# ══════════════════════════════════════════════════════════════════════

def construir_manual():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=inch, rightMargin=inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
        title="Manual de Usuario - SIAC ERP",
        author="SIAC - Sistema Integral de Administracion y Control",
        subject="Manual de Usuario detallado del sistema SIAC ERP"
    )
    story = []

    # ══════════════════════════════════════════════════════════════════
    # PORTADA
    # ══════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 1.5 * inch))
    story.append(_separador())
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("SIAC ERP", estilo_titulo_portada))
    story.append(Paragraph("Sistema Integral de Administracion y Control", estilo_subtitulo_portada))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("Manual de Usuario", ParagraphStyle(
        "TituloManual", parent=estilo_titulo_portada,
        fontSize=24, textColor=VIOLETA
    )))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Version 1.0  |  Agosto 2026", estilo_subtitulo_portada))
    story.append(Spacer(1, 0.6 * inch))
    story.append(_separador())
    story.append(Spacer(1, 0.3 * inch))

    # Info de portada
    portada_data = [
        ["Empresa:", "Fabrica de Calzado Goretti"],
        ["Sistema:", "SIAC ERP v1.0"],
        ["Fecha:", "Agosto 2026"],
        ["Elaborado por:", "Departamento de Sistemas"],
    ]
    portada_t = Table(portada_data, colWidths=[2 * inch, 4 * inch])
    portada_t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), INDIGO),
        ("TEXTCOLOR", (1, 0), (1, -1), GRIS_OSCURO),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(portada_t)
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(
        "Documento confidencial. Uso exclusivo del personal autorizado.",
        ParagraphStyle("Confidencial", parent=estilo_cuerpo,
                       fontSize=9, textColor=ROJO, alignment=TA_CENTER,
                       fontName="Helvetica-Bold")
    ))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════
    # TABLA DE CONTENIDOS
    # ══════════════════════════════════════════════════════════════════
    story.append(_h1("Tabla de Contenidos"))
    story.append(_separador())
    story.append(Spacer(1, 0.2 * inch))

    toc_items = [
        ("1.", "Introduccion", "Descripcion general del sistema"),
        ("2.", "Requisitos del Sistema", "Componentes minimos requeridos"),
        ("3.", "Inicio de Sesion", "Acceso y autenticacion"),
        ("4.", "Ventana Principal", "Navegacion y elementos de la interfaz"),
        ("5.", "Modulo de Inventario", "Gestion de insumos y movimientos"),
        ("6.", "Modulo de Compras", "Ordenes de compra, facturas y proveedores"),
        ("7.", "Modulo de Produccion", "Ordenes de produccion, modelos y variantes"),
        ("8.", "Programacion Semanal", "Planeacion y asignacion de produccion"),
        ("9.", "Modulo de Clientes y Pedidos", "Gestion de clientes y pedidos"),
        ("10.", "Tablero Kanban", "Vista visual del flujo de produccion"),
        ("11.", "Sistema de Etiquetas", "Diseno e impresion de etiquetas"),
        ("12.", "Cola de Impresion", "Gestion de impresiones desde piso"),
        ("13.", "Configuracion del Sistema", "Empresa, catalogos, usuarios y permisos"),
        ("14.", "Exportacion e Impresion", "Reportes en Excel e impresion"),
        ("15.", "Atajos de Teclado", "Referencia rapida de atajos"),
        ("16.", "Glosario", "Definiciones del dominio"),
    ]

    toc_data = []
    for num, titulo, desc in toc_items:
        toc_data.append([
            Paragraph(f"<b>{num}</b>", ParagraphStyle("TocNum", parent=estilo_cuerpo, fontSize=10, textColor=INDIGO)),
            Paragraph(f"<b>{titulo}</b><br/><font size=8 color='#6B7280'>{desc}</font>", ParagraphStyle("TocItem", parent=estilo_cuerpo, fontSize=10))
        ])

    toc_t = Table(toc_data, colWidths=[0.5 * inch, 5.5 * inch])
    toc_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, GRIS_CLARO),
        ("LINEBELOW", (0, -1), (-1, -1), 0.3, GRIS_CLARO),
    ]))
    story.append(toc_t)
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════
    # 1. INTRODUCCION
    # ══════════════════════════════════════════════════════════════════
    story.append(_h1("1. Introduccion"))
    story.append(_separador())
    story.append(_p(
        "SIAC ERP (Sistema Integral de Administracion y Control) es una "
        "aplicacion de escritorio disenada para la gestion integral de una "
        "fabrica de calzado. El sistema abarca los procesos criticos del "
        "negocio:"
    ))
    story.extend(_bullet_list([
        "<b>Compras:</b> Ordenes de compra a proveedores, recepcion de mercancia y control de facturas.",
        "<b>Inventario:</b> Catalogo de insumos (materia prima), movimientos de entrada, salida y ajuste.",
        "<b>Produccion:</b> Ordenes de produccion, modelos de calzado, variantes (modelo x color x piel), "
        "fichas tecnicas y listas de materiales (BOM).",
        "<b>Programacion:</b> Planeacion semanal de produccion con asignacion de pares por talla.",
        "<b>Clientes y Pedidos:</b> Gestion de pedidos de clientes y programacion de entrega.",
        "<b>Etiquetas:</b> Diseno e impresion de etiquetas termicas para cajas y partidas.",
        "<b>Reportes:</b> Exportacion a Excel e impresion de documentos en todos los modulos.",
    ]))
    story.append(Spacer(1, 6))
    story.append(_p(
        "Este manual describe paso a paso cada modulo, sus funciones, "
        "formularios y operaciones disponibles, para que el usuario pueda "
        "aprovechar al maximo las capacidades del sistema."
    ))
    story.append(_nota(
        "El sistema utiliza base de datos SQLite para desarrollo y PostgreSQL "
        "para produccion. Todos los datos se almacenan localmente de forma segura."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 2. REQUISITOS
    # ══════════════════════════════════════════════════════════════════
    story.append(_h1("2. Requisitos del Sistema"))
    story.append(_separador())
    story.append(_h3("2.1 Requisitos minimos de hardware"))
    story.append(_tabla(
        ["Componente", "Minimo", "Recomendado"],
        [
            ["Procesador", "Dual-Core 1.5 GHz", "Quad-Core 2.5 GHz"],
            ["Memoria RAM", "4 GB", "8 GB o mas"],
            ["Disco duro", "500 MB libres", "1 GB libres"],
            ["Monitor", "1024 x 768", "1920 x 1080 o superior"],
            ["Impresora termica", "Opcional (para etiquetas)", "Zebra/Datec compatible"],
        ],
        [2 * inch, 2 * inch, 2.5 * inch]
    ))
    story.append(Spacer(1, 8))
    story.append(_h3("2.2 Requisitos de software"))
    story.extend(_bullet_list([
        "<b>Sistema operativo:</b> Windows 10/11 (64 bits)",
        "<b>Python:</b> 3.12 o superior",
        "<b>PySide6:</b> 6.5 o superior (Qt for Python)",
        "<b>Base de datos:</b> SQLite (incluido) o PostgreSQL 14+ (produccion)",
        "<b>Navegador:</b> Chrome o Edge (para vista previa de impresion con WebEngine)",
    ]))

    # ══════════════════════════════════════════════════════════════════
    # 3. INICIO DE SESION
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("3. Inicio de Sesion"))
    story.append(_separador())
    story.append(_p(
        "Al iniciar la aplicacion, se presenta la pantalla de acceso. "
        "Es obligatorio autenticarse para acceder a cualquier modulo del sistema."
    ))
    story.append(_h3("3.1 Pantalla de login"))
    story.append(_p("La pantalla de login contiene:"))
    story.extend(_bullet_list([
        "<b>Logo de la empresa:</b> Se muestra el logo registrado en la configuracion.",
        "<b>Campo Usuario:</b> Ingrese su nombre de usuario asignado.",
        "<b>Campo Contrasena:</b> Ingrese su contrasena (se oculta con asteriscos).",
        "<b>Boton 'Iniciar Sesion':</b> Presione o Use Enter para autenticar.",
    ]))
    story.append(_h3("3.2 Credenciales iniciales"))
    story.append(_adv(
        "Credenciales por defecto: Usuario = admin | Contrasena = admin123. "
        "Cambie la contrasena inmediatamente despues del primer ingreso."
    ))
    story.append(_h3("3.3 Errores de acceso"))
    story.append(_tabla(
        ["Mensaje", "Causa", "Solucion"],
        [
            ["Usuario no encontrado", "Nombre de usuario incorrecto", "Verifique el nombre o consulte al administrador"],
            ["Contrasena incorrecta", "Clave erronea", "Use 'Olvide mi contrasena' o contacte al admin"],
            ["Usuario desactivado", "Cuenta deshabilitada", "Contacte al administrador para reactivar"],
        ],
        [1.8 * inch, 2 * inch, 2.7 * inch]
    ))
    story.append(_tip(
        "Si olvido su contrasena, contacte al administrador del sistema para "
        "restablecerla desde el modulo de Configuracion > Usuarios."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 4. VENTANA PRINCIPAL
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("4. Ventana Principal"))
    story.append(_separador())
    story.append(_p(
        "Despues del login exitoso, se muestra la ventana principal del sistema, "
        "compuesta por cuatro areas:"
    ))

    story.append(_h3("4.1 Barra de menus (superior)"))
    story.append(_tabla(
        ["Menu", "Opcion", "Funcion", "Atajo"],
        [
            ["Archivo", "Inventario", "Abre el modulo de inventario", "Ctrl+I"],
            ["Archivo", "Compras", "Abre el modulo de compras", "Ctrl+L"],
            ["Archivo", "Produccion", "Abre el modulo de produccion", "Ctrl+P"],
            ["Archivo", "Programacion", "Abre la programacion semanal", "-"],
            ["Archivo", "Clientes", "Abre el modulo de clientes", "-"],
            ["Archivo", "Salir", "Cierra la aplicacion", "Ctrl+Q"],
            ["Herramientas", "Configuracion", "Solo admin: config del sistema", "-"],
            ["Herramientas", "Sandbox", "Solo admin: controles y pruebas", "-"],
            ["Herramientas", "Cambiar usuario", "Vuelve al login", "Ctrl+U"],
            ["Ayuda", "Acerca de", "Informacion del sistema", "-"],
        ],
        [1.2 * inch, 1.3 * inch, 2.5 * inch, 1 * inch]
    ))

    story.append(_h3("4.2 Barra lateral de navegacion (izquierda)"))
    story.append(_p(
        "La barra lateral muestra accesos directos a los modulos principales. "
        "Los modulos Configuracion y Sandbox solo aparecen para usuarios con "
        "rol de administrador."
    ))
    story.extend(_bullet_list([
        "<b>Inventario</b> - Gestion de insumos y movimientos",
        "<b>Compras</b> - Ordenes de compra y proveedores",
        "<b>Produccion</b> - Ordenes de produccion y modelos",
        "<b>Programacion</b> - Planeacion semanal",
        "<b>Clientes</b> - Pedidos y catalogo de clientes",
        "<b>Kanban</b> - Tablero visual de produccion",
    ]))

    story.append(_h3("4.3 Barra de estado (inferior)"))
    story.extend(_bullet_list([
        "<b>Izquierda:</b> Usuario conectado y su rol (ej. 'admin - Administrador')",
        "<b>Centro:</b> Fecha actual (ej. 'Hoy: 17 de agosto de 2026')",
        "<b>Derecha:</b> Nombre de la empresa (configurable)",
    ]))

    story.append(_h3("4.4 Area central"))
    story.append(_p(
        "El area central muestra el contenido del modulo seleccionado. "
        "Cada modulo se carga como una vista con pestanas, tablas de datos, "
        "botones de accion y formularios."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 5. MODULO DE INVENTARIO
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("5. Modulo de Inventario"))
    story.append(_separador())
    story.append(_p(
        "El modulo de Inventario permite gestionar los insumos (materia prima) "
        "y los movimientos de entrada, salida y ajuste de stock."
    ))

    story.append(_h2("5.1 Pestana Insumos"))
    story.append(_h3("5.1.1 Buscar insumos"))
    story.append(_p(
        "Use la barra de busqueda en la parte superior para filtrar insumos "
        "por nombre, codigo o proveedor. La busqueda es en tiempo real."
    ))

    story.append(_h3("5.1.2 Acciones disponibles"))
    story.append(_tabla(
        ["Boton", "Atajo", "Permiso", "Descripcion"],
        [
            ["Nuevo", "Ctrl+N", "inventario/crear", "Registra un nuevo insumo"],
            ["Movimiento", "Ctrl+M", "inventario/editar", "Registra movimiento de stock multi-partida"],
            ["Editar", "Ctrl+E", "inventario/editar", "Modifica los datos del insumo seleccionado"],
            ["Desactivar", "Ctrl+D", "inventario/eliminar", "Desactiva el insumo (borrado logico)"],
            ["Exportar", "Ctrl+X", "inventario/exportar", "Exporta la tabla a Excel"],
            ["Imprimir", "Ctrl+P", "inventario/exportar", "Vista previa de impresion"],
        ],
        [1 * inch, 0.7 * inch, 1.3 * inch, 3.5 * inch]
    ))

    story.append(_h3("5.1.3 Columnas de la tabla"))
    story.extend(_bullet_list([
        "<b>Codigo:</b> Identificador unico del insumo (formato INS-XXXX)",
        "<b>Nombre:</b> Nombre descriptivo del insumo",
        "<b>Unidad de Medida:</b> Par, Kg, Litro, etc.",
        "<b>Stock Actual:</b> Cantidad disponible en almacen",
        "<b>Stock Minimo:</b> Nivel minimo de alerta",
        "<b>Precio Unitario:</b> Costo por unidad",
        "<b>Estado:</b> Activo o Desactivado",
        "<b>Proveedor:</b> Proveedor principal del insumo",
        "<b>Descripcion:</b> Detalles adicionales",
    ]))
    story.append(_nota(
        "Los insumos desactivados se muestran en texto gris italica y fondo gris "
        "para distinguirlos visualmente de los activos."
    ))

    story.append(_h3("5.1.4 Dialogo Nuevo/Editar Insumo"))
    story.append(_p("Al presionar 'Nuevo' o 'Editar', se abre un formulario con:"))
    story.extend(_bullet_list([
        "<b>Codigo:</b> Auto-generado (INS-XXXX) o editable",
        "<b>Nombre:</b> Nombre del insumo (obligatorio)",
        "<b>Unidad de medida:</b> Selector del catalogo de unidades",
        "<b>Stock minimo:</b> Cantidad minima para alerta",
        "<b>Precio unitario:</b> Costo por unidad de medida",
        "<b>Proveedor:</b> Buscador desplegable de proveedores",
        "<b>Descripcion:</b> Campo libre de texto",
    ]))

    story.append(_h2("5.2 Pestana Movimientos"))
    story.append(_p(
        "Esta pestana muestra el historial de todos los movimientos de inventario "
        "(entradas, salidas y ajustes)."
    ))

    story.append(_h3("5.2.1 Nuevo Movimiento"))
    story.append(_p(
        "El dialogo de movimiento multi-partida permite registrar multiples "
        "insumos en un solo movimiento:"
    ))
    story.extend(_numero_list([
        "Seleccione el <b>tipo de movimiento</b>: Entrada, Salida o Ajuste",
        "Ingrese una <b>referencia</b> (numero de factura, orden de compra, etc.)",
        "Agregue partidas con el boton '+': cada partida incluye insumo, cantidad y observaciones",
        "Revise el total de partidas y presione <b>Guardar</b>",
        "El sistema genera un folio automatico (MOV-XXXX)",
    ]))
    story.append(_adv(
        "Las salidas de inventario no pueden exceder el stock actual del insumo. "
        "El sistema valida esta restriccion antes de guardar."
    ))

    story.append(_h3("5.2.2 Imprimir movimiento"))
    story.append(_p(
        "Seleccione un movimiento y presione 'Imprimir' para generar un documento "
        "formal con el encabezado de la empresa, el folio, fecha, tabla de "
        "insumos afectados y pie de pagina."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 6. MODULO DE COMPRAS
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("6. Modulo de Compras"))
    story.append(_separador())
    story.append(_p(
        "El modulo de Compras gestiona las ordenes de compra (OC) a proveedores, "
        "el registro de facturas y el catalogo de proveedores."
    ))

    story.append(_h2("6.1 Pestana Ordenes de Compra"))
    story.append(_h3("6.1.1 Acciones disponibles"))
    story.append(_tabla(
        ["Boton", "Atajo", "Descripcion"],
        [
            ["Nueva OC", "Ctrl+N", "Crea una nueva orden de compra"],
            ["Factura", "Ctrl+F", "Registra una factura (tipo documento)"],
            ["Recibir", "Ctrl+R", "Abre el dialogo de recepcion para la OC seleccionada"],
            ["Cancelar", "-", "Cancela la OC seleccionada (estatus = cancelada)"],
            ["Nueva OC e Inmediata", "Ctrl+Shift+N", "Crea OC y abre recepcion de inmediato"],
            ["Ver Detalle", "Ctrl+Shift+V", "Muestra vista de solo lectura de la OC"],
            ["Exportar", "Ctrl+X", "Exporta la tabla a Excel"],
            ["Imprimir", "Ctrl+P", "Vista previa de impresion de la OC"],
        ],
        [1.5 * inch, 1.3 * inch, 3.7 * inch]
    ))

    story.append(_h3("6.1.2 Dialogo Nueva Orden de Compra"))
    story.append(_p("Complete los siguientes campos:"))
    story.extend(_bullet_list([
        "<b>Proveedor:</b> Seleccione el proveedor con el buscador desplegable",
        "<b>Fecha:</b> Fecha de la orden (seleccionar del calendario)",
        "<b>Tipo:</b> 'orden' (recibe inventario) o 'factura' (solo registro contable)",
        "<b>Notas:</b> Observaciones adicionales (opcional)",
        "<b>Detalle:</b> Agregue insumos con cantidades por punto/talla",
        "<b>Subtotal, IVA, Total:</b> Se calculan automaticamente",
    ]))

    story.append(_h3("6.1.3 Colores de fila"))
    story.append(_tabla(
        ["Color", "Significado"],
        [
            ["Verde claro (#daf2d0)", "OC recibida o tipo factura"],
            ["Texto rojo tachado", "OC cancelada"],
            ["Fila normal (blanco/gris)", "OC pendiente"],
        ],
        [2.5 * inch, 4 * inch]
    ))

    story.append(_h3("6.1.4 Recepcion de Orden de Compra"))
    story.append(_p(
        "Al presionar 'Recibir', se abre un dialogo donde captura las cantidades "
        "efectivamente recibidas por cada linea y por cada talla/punto:"
    ))
    story.extend(_numero_list([
        "Revise cada linea de la orden de compra",
        "Capture la cantidad recibida en cada celda de la matriz de tallas",
        "El sistema valida si las cantidades coinciden con lo ordenado",
        "Si coinciden: OC se marca como 'recibida'",
        "Si difieren: OC se marca como 'recibida_con_diferencias'",
        "El inventario se actualiza automaticamente (entrada de stock)",
    ]))
    story.append(_tip(
        "Use el boton 'Nueva OC e Inmediata' (Ctrl+Shift+N) cuando vaya a recibir "
        "la mercancia en el mismo momento de crear la orden."
    ))

    story.append(_h3("6.1.5 Menu contextual (clic derecho)"))
    story.append(_p("Al hacer clic derecho sobre una OC:"))
    story.extend(_bullet_list([
        "<b>Copiar importe total al clipboard</b> (Ctrl+Shift+C): Copia el total de la OC seleccionada"
    ]))

    story.append(_h2("6.2 Pestana Proveedores"))
    story.append(_p("Catalogo de proveedores con las acciones:"))
    story.extend(_bullet_list([
        "<b>Nuevo Prov:</b> Registra un nuevo proveedor (nombre, direccion, telefono, email, contacto, cuenta bancaria)",
        "<b>Editar Prov:</b> Modifica los datos del proveedor seleccionado",
        "<b>Desactivar Prov:</b> Desactiva el proveedor (borrado logico)",
        "<b>Exportar:</b> Exporta la tabla de proveedores a Excel",
        "<b>Imprimir:</b> Vista previa de impresion",
    ]))

    story.append(_h3("6.2.1 Dialogo Nuevo/Editar Proveedor"))
    story.extend(_bullet_list([
        "<b>Nombre:</b> Nombre o razon social (obligatorio)",
        "<b>Direccion:</b> Direccion completa",
        "<b>Telefono:</b> Numero de contacto",
        "<b>Email:</b> Correo electronico",
        "<b>Contacto:</b> Nombre de la persona de contacto",
        "<b>Cuenta bancaria:</b> Informacion bancaria para pagos",
        "<b>Notas:</b> Observaciones adicionales",
    ]))

    # ══════════════════════════════════════════════════════════════════
    # 7. MODULO DE PRODUCCION
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("7. Modulo de Produccion"))
    story.append(_separador())
    story.append(_p(
        "El modulo de Produccion es el corazon del sistema. Gestiona las "
        "ordenes de produccion (OP), los modelos de calzado, variantes, "
        "fichas tecnicas y listas de materiales."
    ))

    story.append(_h2("7.1 Pestana Ordenes de Produccion"))
    story.append(_h3("7.1.1 Acciones disponibles"))
    story.append(_tabla(
        ["Boton", "Atajo", "Descripcion"],
        [
            ["Nueva OP", "Ctrl+N", "Crea una nueva orden de produccion"],
            ["Seguimiento", "Ctrl+S", "Abre el dialogo de seguimiento por estacion"],
            ["Avanzar", "Ctrl+A", "Avanza la OP al siguiente estatus"],
            ["Exportar", "Ctrl+X", "Exporta la tabla a Excel"],
            ["Imprimir", "Ctrl+P", "Vista previa con matriz de tallas"],
        ],
        [1.3 * inch, 0.9 * inch, 4.3 * inch]
    ))

    story.append(_h3("7.1.2 Dialogo Nueva Orden de Produccion"))
    story.extend(_bullet_list([
        "<b>Modelo:</b> Seleccione el modelo de calzado a producir",
        "<b>Fecha planeada:</b> Fecha objetivo de produccion",
        "<b>Prioridad:</b> Nivel de prioridad (normal por defecto)",
        "<b>Pares por talla:</b> Use la matriz de tallas para asignar la cantidad de pares por cada talla",
    ]))
    story.append(_p(
        "La <b>Matriz de Tallas</b> es un componente especial que muestra las "
        "tallas configuradas en columnas. Use Tab o Enter para navegar entre "
        "celdas. El total de pares se calcula automaticamente."
    ))

    story.append(_h3("7.1.3 Estatus de las OP"))
    story.append(_tabla(
        ["Estatus", "Color", "Significado"],
        [
            ["planeada", "Gris", "OP creada, aun no iniciada"],
            ["en_produccion", "Cyan", "En proceso de fabricacion"],
            ["terminada", "Verde", "Produccion completada"],
        ],
        [1.5 * inch, 1 * inch, 4 * inch]
    ))

    story.append(_h3("7.1.4 Seguimiento por estacion"))
    story.append(_p(
        "El dialogo de seguimiento muestra las estaciones de produccion "
        "(Corte, Pespunte, Montado, Ensuelado, Acabado, Empaque) y permite "
        "actualizar el estatus de cada una individualmente:"
    ))
    story.append(_tabla(
        ["Estatus", "Significado"],
        [
            ["pendiente", "La estacion no ha comenzado"],
            ["en_proceso", "Trabajo en curso en esta estacion"],
            ["completado", "La estacion ha finalizado"],
        ],
        [1.5 * inch, 5 * inch]
    ))

    story.append(_h2("7.2 Pestana Modelos"))
    story.append(_p("Catalogo de modelos de calzado:"))
    story.extend(_bullet_list([
        "<b>Codigo:</b> Identificador unico del modelo",
        "<b>Nombre:</b> Nombre del modelo",
        "<b>Descripcion:</b> Detalle del modelo",
        "<b>Estado:</b> Activo o desactivado",
    ]))

    story.append(_h2("7.3 Pestana Variantes"))
    story.append(_p(
        "Una variante es la combinacion unica de modelo x color x piel. "
        "Cada variante puede tener imagen propia."
    ))
    story.extend(_bullet_list([
        "<b>Modelo:</b> Modelo asociado",
        "<b>Color:</b> Color de la variante",
        "<b>Piel:</b> Tipo de material/piel",
        "<b>Imagen:</b> Fotografia de referencia",
    ]))

    story.append(_h2("7.4 Pestana Ficha Tecnica / BOM"))
    story.append(_h3("7.4.1 Ficha Tecnica"))
    story.append(_p(
        "La ficha tecnica documenta las especificaciones del modelo con hasta "
        "5 fotografias de referencia:"
    ))
    story.extend(_bullet_list([
        "<b>Producto:</b> Foto del zapato terminado",
        "<b>Tubo:</b> Foto de la parte superior",
        "<b>Chinela:</b> Foto de la plantilla",
        "<b>Talon:</b> Foto del talon",
        "<b>Suela:</b> Foto de la suela",
    ]))
    story.append(_p(
        "Las secciones de la ficha incluyen: Corte, Bordados, Accesorios, "
        "Suela y Estructura, Empaque y Otros. Cada campo se imprime en "
        "documento formal."
    ))

    story.append(_h3("7.4.2 Lista de Materiales (BOM)"))
    story.append(_p(
        "La BOM (Bill of Materials) define que insumos y cantidades se "
        "necesitan para producir un modelo. Cada linea especifica:"
    ))
    story.extend(_bullet_list([
        "<b>Insumo:</b> Seleccion con busqueda",
        "<b>Cantidad:</b> Cantidad necesaria por par",
        "<b>Unidad:</b> Unidad de medida del insumo",
    ]))

    # ══════════════════════════════════════════════════════════════════
    # 8. PROGRAMACION SEMANAL
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("8. Programacion Semanal"))
    story.append(_separador())
    story.append(_p(
        "La Programacion Semanal es la herramienta de planeacion que conecta "
        "los pedidos de clientes con la produccion. Permite asignar pares "
        "por talla, organizar por cliente/modelo/color y generar las "
        "ordenes de produccion."
    ))

    story.append(_h2("8.1 Controles superiores"))
    story.extend(_bullet_list([
        "<b>Ver Todas (Ctrl+T):</b> Alterna entre ver toda la programacion o solo la semana actual",
        "<b>Exportar a Excel:</b> Abre dialogo de agrupacion para exportar",
        "<b>Imprimir Programacion:</b> Genera vista previa del reporte semanal",
        "<b>Cola de Impresion:</b> Abre la cola de impresion de etiquetas",
    ]))

    story.append(_h2("8.2 Tabla de programacion"))
    story.append(_p(
        "La tabla es editable directamente. Cada fila representa una linea "
        "de programacion con las columnas:"
    ))
    story.extend(_bullet_list([
        "Cliente, Modelo, Piel, Color, Fecha de programacion",
        "Una columna por cada talla de la corrida activa",
        "Columna de Total de Pares",
    ]))
    story.append(_tip(
        "Use la tecla Tab o Enter para navegar rapidamente entre celdas. "
        "Las celdas sin pares asignados estan deshabilitadas."
    ))

    story.append(_h3("8.2.1 Agrupacion"))
    story.append(_p(
        "Puede agrupar las lineas por: Cliente, Modelo, Piel o Color. "
        "Los grupos se expanden/colapsan con clic en la fila de grupo."
    ))

    story.append(_h3("8.2.2 Estatus de programacion"))
    story.append(_tabla(
        ["Estatus", "Color", "Significado"],
        [
            ["programado", "Violeta", "Todas las cantidades asignadas correctamente"],
            ["programacion_incompleta", "Amarillo", "Faltan cantidades por asignar"],
            ["en_proceso", "Cyan", "Ya esta en produccion"],
            ["producido", "Verde", "Terminado y producido"],
        ],
        [1.8 * inch, 1 * inch, 3.7 * inch]
    ))

    story.append(_h2("8.3 Dialogo de linea de detalle"))
    story.append(_p(
        "Al hacer doble clic en una linea, se abre el detalle con: "
        "datos de la linea, campos editables para impresion (Modelo, Corte, Color), "
        "matriz de tallas para captura de pares, y el editor de etiquetas."
    ))

    story.append(_h2("8.4 Exportacion agrupada"))
    story.append(_p(
        "El dialogo de exportacion permite elegir criterios de agrupacion "
        "para el Excel:"
    ))
    story.extend(_bullet_list([
        "<b>Cliente:</b> Agrupa por cliente",
        "<b>Modelo:</b> Agrupa por modelo",
        "<b>Piel:</b> Agrupa por tipo de piel",
        "<b>Color:</b> Agrupa por color",
    ]))
    story.append(_p(
        "El Excel generado tiene encabezado violeta (#7C3AED), filas alternas "
        "coloreadas y fila de totales."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 9. CLIENTES Y PEDIDOS
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("9. Modulo de Clientes y Pedidos"))
    story.append(_separador())

    story.append(_h2("9.1 Pestana Pedidos"))
    story.append(_h3("9.1.1 Acciones disponibles"))
    story.append(_tabla(
        ["Boton", "Descripcion"],
        [
            ["Nuevo Pedido", "Crea un nuevo pedido de cliente"],
            ["Programar Pedido", "Abre dialogo para programar el pedido seleccionado"],
            ["Editar Pedido", "Modifica el pedido seleccionado"],
            ["Imprimir Pedido", "Vista previa de impresion del pedido"],
            ["Exportar", "Exporta la tabla de pedidos a Excel"],
        ],
        [1.5 * inch, 5 * inch]
    ))

    story.append(_h3("9.1.2 Dialogo Nuevo Pedido"))
    story.extend(_bullet_list([
        "<b>Cliente:</b> Seleccione el cliente",
        "<b>Fecha:</b> Fecha del pedido",
        "<b>Observaciones:</b> Notas adicionales",
        "<b>Detalle:</b> Agregar lineas con modelo, cantidades por talla",
    ]))

    story.append(_h2("9.2 Pestana Clientes"))
    story.append(_p("Catalogo de clientes con acciones:"))
    story.extend(_bullet_list([
        "<b>Nuevo Cliente:</b> Registra un nuevo cliente",
        "<b>Editar Cliente:</b> Modifica los datos del cliente seleccionado",
        "<b>Desactivar Cliente:</b> Desactiva el cliente (borrado logico)",
        "<b>Exportar:</b> Exporta a Excel",
        "<b>Imprimir:</b> Vista previa de impresion",
    ]))
    story.append(_p("Campos del formulario de cliente:"))
    story.extend(_bullet_list([
        "Codigo, Nombre, Direccion, Telefono, Email, Contacto, Estado"
    ]))

    # ══════════════════════════════════════════════════════════════════
    # 10. KANBAN
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("10. Tablero Kanban"))
    story.append(_separador())
    story.append(_p(
        "El tablero Kanban ofrece una vista visual del flujo de produccion. "
        "Las ordenes de produccion se muestran como tarjetas organizadas "
        "en columnas por estacion."
    ))
    story.append(_h3("10.1 Funcionalidades"))
    story.extend(_bullet_list([
        "<b>Arrastrar y soltar:</b> Mueva tarjetas entre columnas para cambiar el estatus",
        "<b>Tarjetas:</b> Muestran Folio, Modelo, Pares y badge de estatus",
        "<b>Barras de color:</b> Cada tarjeta tiene una barra lateral del color del estatus",
        "<b>Refrescar:</b> Boton para actualizar el tablero",
        "<b>Ver Detalle:</b> Abre los detalles de la OP seleccionada",
    ]))

    story.append(_nota(
        "El tablero Kanban es ideal para visualizar el avance general de "
        "produccion en una reunion de piso o en una pantalla grande."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 11. SISTEMA DE ETIQUETAS
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("11. Sistema de Etiquetas"))
    story.append(_separador())
    story.append(_p(
        "El sistema de etiquetas permite disenar, previsualizar e imprimir "
        "etiquetas termicas para las cajas de calzado."
    ))

    story.append(_h2("11.1 Tipos de etiqueta"))
    story.append(_tabla(
        ["Tipo", "Descripcion", "Uso"],
        [
            ["Flejes (Cajas)", "Etiqueta de texto simple con cantidad", "Cajas de pares"],
            ["Partidas", "Etiqueta con modelo/corte/color y cantidades por talla", "Detalle de partidas"],
        ],
        [1.5 * inch, 2.5 * inch, 2.5 * inch]
    ))

    story.append(_h2("11.2 Editor de Etiquetas"))
    story.append(_p(
        "El editor es un diseno WYSIWYG (lo que ve es lo que imprime) con:"
    ))
    story.extend(_bullet_list([
        "<b>Lienzo interactivo:</b> Arrastre y suelte campos de texto y datos",
        "<b>Panel de herramientas:</b> Agregar texto, dato dinamico, duplicar, quitar",
        "<b>Panel de campos:</b> Lista de todos los campos con posicion y tamano",
        "<b>Propiedades:</b> Editor del campo seleccionado (tipo, contenido, fuente, "
        "alineacion, borde, rotacion, colores, visibilidad)",
        "<b>Tamano del lienzo:</b> Configurable en milimetros (ancho x alto)",
        "<b>Guardar/Cargar:</b> Guarda disenos con nombre en la base de datos",
    ]))

    story.append(_h3("11.2.1 Tipos de campo"))
    story.append(_tabla(
        ["Tipo", "Descripcion"],
        [
            ["Texto estatico", "Texto fijo que se imprime tal cual"],
            ["Dato dinamico", "Campo vinculado a datos (modelo, color, talla, etc.)"],
        ],
        [2 * inch, 4.5 * inch]
    ))

    story.append(_h2("11.3 Impresion de etiquetas"))
    story.extend(_numero_list([
        "Desde la programacion, abra el detalle de una linea",
        "Seleccione 'Imprimir Etiquetas' o 'Imprimir Muestra'",
        "Revise la vista previa en la etiqueta termica (75x45mm)",
        "Seleccione la impresora y confirme la impresion",
    ]))
    story.append(_tip(
        "Use 'Imprimir Muestra' para probar una sola etiqueta antes de "
        "imprimir toda la tirada."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 12. COLA DE IMPRESION
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("12. Cola de Impresion"))
    story.append(_separador())
    story.append(_p(
        "La Cola de Impresion gestiona las solicitudes de etiquetas que "
        "provienen del piso de produccion (mediante la aplicacion movil "
        "sincronizada con Supabase)."
    ))

    story.append(_h2("12.1 Pestana Cola (pendientes)"))
    story.extend(_bullet_list([
        "<b>Actualizar:</b> Refresca la lista de solicitudes pendientes",
        "<b>Vista previa:</b> Muestra la etiqueta antes de imprimir",
        "<b>Imprimir:</b> Envia la etiqueta a la impresora termica",
    ]))

    story.append(_h2("12.2 Pestana Historico"))
    story.extend(_bullet_list([
        "<b>Actualizar:</b> Refresca el historial",
        "<b>Vista previa:</b> Muestra la etiqueta impresa anteriormente",
        "<b>Reimprimir:</b> Vuelve a imprimir una etiqueta del historial",
    ]))

    story.append(_nota(
        "La cola de impresion soporta dos tipos de etiquetas: Partidas "
        "(modelo/corte/color/talla) y Flejes/Cajas (texto simple con cantidad)."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 13. CONFIGURACION
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("13. Configuracion del Sistema"))
    story.append(_separador())
    story.append(_adv(
        "Este modulo es visible y editable SOLO para usuarios con rol de "
        "Administrador."
    ))

    story.append(_h2("13.1 Datos de la Empresa"))
    story.append(_p("Configure los datos de su empresa que aparecen en reportes y documentos:"))
    story.extend(_bullet_list([
        "<b>Nombre:</b> Nombre comercial de la empresa",
        "<b>Direccion:</b> Direccion fiscal",
        "<b>Telefono:</b> Numero de contacto",
        "<b>RFC:</b> Registro Federal de Contribuyentes",
        "<b>Logo:</b> Imagen de logotipo (seleccionar archivo desde disco)",
    ]))
    story.append(_nota(
        "El logo se muestra en la pantalla de login, en los reportes impresos "
        "y en los documentos de movimiento."
    ))

    story.append(_h2("13.2 Unidades de Medida"))
    story.append(_p("Catalogo de unidades utilizadas en los insumos:"))
    story.extend(_bullet_list([
        "Par, Kg, Litro, Metro, Pieza, Caja, etc.",
        "Acciones: Nuevo, Editar, Desactivar"
    ]))

    story.append(_h2("13.3 Areas de Produccion"))
    story.append(_p("Estaciones o etapas del proceso productivo:"))
    story.extend(_bullet_list([
        "Corte, Pespunte, Montado, Ensuelado, Acabado, Empaque, etc.",
        "Cada area tiene un orden de secuencia",
        "Acciones: Nuevo, Editar, Desactivar"
    ]))

    story.append(_h2("13.4 Tallas de Variante"))
    story.append(_p("Catalogo de tallas/puntos disponibles:"))
    story.extend(_bullet_list([
        "Valores numericos (00, 00.5, 01, 01.5, ..., 13, etc.)",
        "Se usan en las matrices de tallas de OC y OP",
        "Acciones: Nuevo, Editar, Desactivar"
    ]))

    story.append(_h2("13.5 Colores de Variante"))
    story.append(_p("Catalogo de colores para variantes de calzado:"))
    story.extend(_bullet_list([
        "Nombre, Codigo y color hexadecimal",
        "Acciones: Nuevo, Editar, Desactivar"
    ]))

    story.append(_h2("13.6 Usuarios y Accesos"))
    story.append(_h3("13.6.1 Gestion de usuarios"))
    story.extend(_bullet_list([
        "<b>Usuario:</b> Nombre de usuario para login",
        "<b>Contrasena:</b> Indicador de fortaleza (debil/media/fuerte)",
        "<b>Rol:</b> admin, operador o consulta",
    ]))

    story.append(_h3("13.6.2 Matriz de permisos"))
    story.append(_p(
        "Cada usuario tiene una matriz de permisos por modulo x accion:"
    ))
    story.append(_tabla(
        ["Accion", "Descripcion"],
        [
            ["ver", "Puede visualizar el modulo"],
            ["crear", "Puede crear nuevos registros"],
            ["editar", "Puede modificar registros existentes"],
            ["eliminar", "Puede desactivar registros"],
            ["exportar", "Puede exportar a Excel e imprimir"],
        ],
        [1.2 * inch, 5.3 * inch]
    ))
    story.append(_p("Modulos disponibles: inventario, ordenes_compra, produccion, configuracion, usuarios"))

    story.append(_h3("13.6.3 Roles predefinidos"))
    story.append(_tabla(
        ["Rol", "Permisos"],
        [
            ["admin", "Todos los permisos (ver, crear, editar, eliminar, exportar) en todos los modulos"],
            ["operador", "Ver, crear y editar en modulos principales"],
            ["consulta", "Solo ver en todos los modulos"],
        ],
        [1.2 * inch, 5.3 * inch]
    ))

    story.append(_h2("13.7 Impresion"))
    story.append(_p(
        "Toggle para habilitar la 'Impresora virtual SIAC'. Cuando esta "
        "activada, todas las impresiones abren vista previa en pantalla "
        "en lugar de enviar a una impresora fisica. Util para pruebas y "
        "configuracion inicial."
    ))

    # ══════════════════════════════════════════════════════════════════
    # 14. EXPORTACION E IMPRESION
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("14. Exportacion e Impresion"))
    story.append(_separador())
    story.append(_p(
        "Todos los modulos del sistema cuentan con opciones de exportacion "
        "e impresion."
    ))

    story.append(_h2("14.1 Exportar a Excel"))
    story.append(_p(
        "El boton Exportar genera un archivo Excel (.xlsx) con formato "
        "profesional:"
    ))
    story.extend(_bullet_list([
        "<b>Encabezado:</b> Fondo indigo (#4F46E5) con texto blanco",
        "<b>Bordes:</b> Todos los celdas con bordes finos",
        "<b>Filas alternas:</b> Colores alternos para mejor lectura",
        "<b>Fila de totales:</b> Negrita al final de la tabla",
        "<b>Titulo y subtitulo:</b> Informe del contenido del reporte",
    ]))

    story.append(_h2("14.2 Vista previa de impresion"))
    story.append(_p(
        "El boton Imprimir abre una vista previa WYSIWYG donde puede:"
    ))
    story.extend(_bullet_list([
        "Seleccionar tamano de papel: Carta, Oficio o A4",
        "Orientacion: Vertical u Horizontal",
        "Zoom: Ampliar o reducir la vista",
        "Imprimir: Enviar a la impresora seleccionada",
        "Exportar PDF: Guardar como archivo PDF",
    ]))

    story.append(_h2("14.3 Documentos especiales"))
    story.append(_tabla(
        ["Documento", "Modulo", "Formato"],
        [
            ["Orden de Compra", "Compras", "Recibo con encabezado de empresa y detalle de items"],
            ["Movimiento de Inventario", "Inventario", "Documento formal con tabla de insumos"],
            ["Kardex", "Inventario", "Historial de movimientos con saldo corrido"],
            ["Ficha Tecnica", "Produccion", "Documento con fotos y especificaciones"],
            ["Programacion", "Programacion", "Reporte paisaje con columnas por talla"],
            ["Etiquetas", "Programacion", "Etiqueta termica 75x45mm"],
        ],
        [1.8 * inch, 1.3 * inch, 3.4 * inch]
    ))

    # ══════════════════════════════════════════════════════════════════
    # 15. ATAJOS DE TECLADO
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("15. Atajos de Teclado"))
    story.append(_separador())

    story.append(_h2("15.1 Navegacion general"))
    story.append(_tabla(
        ["Atajo", "Accion"],
        [
            ["Ctrl+I", "Ir a Inventario"],
            ["Ctrl+L", "Ir a Compras"],
            ["Ctrl+P", "Ir a Produccion"],
            ["Ctrl+Q", "Cerrar aplicacion"],
            ["Ctrl+U", "Cambiar usuario (volver al login)"],
            ["Ctrl+T", "Ver todas las programaciones"],
        ],
        [1.5 * inch, 5 * inch]
    ))

    story.append(_h2("15.2 Acciones en registros"))
    story.append(_tabla(
        ["Atajo", "Accion"],
        [
            ["Ctrl+N", "Crear nuevo registro"],
            ["Ctrl+E", "Editar registro seleccionado"],
            ["Ctrl+D", "Desactivar registro seleccionado"],
            ["Ctrl+R", "Recibir orden de compra"],
            ["Ctrl+S", "Abrir seguimiento de OP"],
            ["Ctrl+A", "Avanzar OP al siguiente estatus"],
            ["Ctrl+F", "Nueva factura"],
            ["Ctrl+Shift+N", "Nueva OC e Inmediata (crear + recibir)"],
            ["Ctrl+Shift+V", "Ver detalle (solo lectura)"],
            ["Ctrl+Shift+C", "Copiar importe total al clipboard"],
            ["Ctrl+X", "Exportar tabla a Excel"],
        ],
        [1.8 * inch, 4.7 * inch]
    ))

    story.append(_h2("15.3 Navegacion en formularios"))
    story.append(_tabla(
        ["Tecla", "Accion"],
        [
            ["Tab", "Siguiente campo"],
            ["Shift+Tab", "Campo anterior"],
            ["Enter", "Siguiente celda (en matrices) / Confirmar"],
            ["Escape", "Cerrar dialogo / Cancelar"],
            ["Flechas", "Navegar en listas y tablas"],
        ],
        [1.5 * inch, 5 * inch]
    ))

    # ══════════════════════════════════════════════════════════════════
    # 16. GLOSARIO
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(_h1("16. Glosario"))
    story.append(_separador())

    glosario = [
        ["BOM", "Bill of Materials / Lista de Materiales. Documento que lista los insumos y cantidades para fabricar un modelo."],
        ["Corrida", "Rango de tallas (de X a Y) usado en una orden de compra o produccion."],
        ["Folio", "Numero secuencial unico asignado a cada registro (OC-0001, OP-0001, MOV-0001, INS-0001)."],
        ["Insumo", "Materia prima: piel, suela, forro, hilo, pegamento, etc."],
        ["Kardex", "Historial de movimientos de un insumo con saldo corrido."],
        ["Modelo", "Diseno de zapato con sus especificaciones y lista de materiales."],
        ["OC", "Orden de Compra. Folio OC-XXXX. Tipos: orden (recibe inventario) o factura (solo registro)."],
        ["OP", "Orden de Produccion. Folio OP-XXXX. Define que modelo, cuantos pares y en que tallas producir."],
        ["Pares por talla", "Cantidad de pares asignada a cada talla/punto en una OC u OP."],
        ["PT", "Producto Terminado. Inventario de zapatos fabricados por variante y talla."],
        ["Sandbox", "Area de pruebas para el administrador. Controles y prototipos."],
        ["Talla / Punto", "Son la misma medida. El sistema las maneja como 'tallas' de forma unificada."],
        ["Variante", "Combinacion unica de modelo x color x piel."],
    ]

    glosario_data = []
    for termino, definicion in glosario:
        glosario_data.append([
            Paragraph(f"<b>{termino}</b>", ParagraphStyle("GlosTerm", parent=estilo_cuerpo, fontSize=9, textColor=INDIGO)),
            Paragraph(definicion, ParagraphStyle("GlosDef", parent=estilo_cuerpo, fontSize=9))
        ])

    g_t = Table(glosario_data, colWidths=[1.3 * inch, 5.2 * inch])
    g_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, GRIS_CLARO),
        ("LINEBELOW", (0, -1), (-1, -1), 0.3, GRIS_CLARO),
    ]))
    story.append(g_t)

    # ══════════════════════════════════════════════════════════════════
    # CIERRE
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.append(Spacer(1, 2 * inch))
    story.append(_separador())
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("SIAC ERP", ParagraphStyle(
        "FinTitulo", parent=estilo_titulo_portada, fontSize=28, textColor=INDIGO
    )))
    story.append(Paragraph("Manual de Usuario v1.0", ParagraphStyle(
        "FinSub", parent=estilo_subtitulo_portada, fontSize=14, textColor=VIOLETA
    )))
    story.append(Spacer(1, 0.4 * inch))
    story.append(_separador())
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "Fabrica de Calzado Goretti<br/>"
        "Sistema Integral de Administracion y Control<br/>"
        "Septiembre 2026",
        ParagraphStyle("FinInfo", parent=estilo_subtitulo_portada, fontSize=11, textColor=GRIS_MEDIO)
    ))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "Soporte Tecnico: mluevanov@gmail.com | +52 477 452 1438",
        ParagraphStyle("FinSoporte", parent=estilo_cuerpo, fontSize=10, textColor=GRIS_OSCURO, alignment=TA_CENTER)
    ))

    # ── Generar PDF ──────────────────────────────────────────────────
    doc.build(story, onFirstPage=_cabecera, onLaterPages=_pie_pagina)
    return os.path.abspath(OUTPUT)


if __name__ == "__main__":
    ruta = construir_manual()
    print(f"Manual generado exitosamente: {ruta}")
