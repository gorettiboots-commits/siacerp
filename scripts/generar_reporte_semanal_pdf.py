"""
Generador del Reporte Semanal de Trabajo (SIAC ERP) en PDF.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import os

# ── Colores del sistema ──────────────────────────────────────────────
INDIGO = HexColor("#4F46E5")
INDIGO_CLARO = HexColor("#EEF2FF")
AZUL_DARK = HexColor("#1E293B")
VIOLETA = HexColor("#7C3AED")
VERDE = HexColor("#16A34A")
VERDE_CLARO = HexColor("#DCFCE7")
GRIS_OSCURO = HexColor("#1F2937")
GRIS_MEDIO = HexColor("#4B5563")
GRIS_CLARO = HexColor("#F8FAFC")
BORDE_GRIS = HexColor("#E2E8F0")

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "Reporte_Semanal_SIAC_ERP_2026-08-22.pdf")

# ── Estilos ──────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

estilo_titulo = ParagraphStyle(
    "TituloDoc", parent=styles["Title"],
    fontSize=20, leading=24, textColor=INDIGO,
    spaceAfter=4, alignment=TA_LEFT, fontName="Helvetica-Bold"
)

estilo_subtitulo = ParagraphStyle(
    "SubtituloDoc", parent=styles["Normal"],
    fontSize=10.5, leading=14, textColor=GRIS_MEDIO,
    spaceAfter=10, alignment=TA_LEFT, fontName="Helvetica"
)

estilo_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontSize=13, leading=17, textColor=AZUL_DARK,
    spaceBefore=12, spaceAfter=8, fontName="Helvetica-Bold"
)

estilo_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"],
    fontSize=11, leading=15, textColor=INDIGO,
    spaceBefore=8, spaceAfter=4, fontName="Helvetica-Bold"
)

estilo_cuerpo = ParagraphStyle(
    "Cuerpo", parent=styles["Normal"],
    fontSize=9.5, leading=13.5, textColor=GRIS_OSCURO,
    spaceAfter=6, alignment=TA_JUSTIFY, fontName="Helvetica"
)

estilo_bullet = ParagraphStyle(
    "Bullet", parent=estilo_cuerpo,
    leftIndent=14, firstLineIndent=-10, spaceAfter=4
)

estilo_th = ParagraphStyle(
    "TH", parent=styles["Normal"],
    fontSize=9, leading=12, textColor=white,
    fontName="Helvetica-Bold", alignment=TA_CENTER
)

estilo_td = ParagraphStyle(
    "TD", parent=styles["Normal"],
    fontSize=8.5, leading=11.5, textColor=GRIS_OSCURO,
    fontName="Helvetica"
)

estilo_td_center = ParagraphStyle(
    "TDCenter", parent=estilo_td, alignment=TA_CENTER
)

estilo_td_bold = ParagraphStyle(
    "TDBold", parent=estilo_td, fontName="Helvetica-Bold", textColor=AZUL_DARK
)

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(GRIS_MEDIO)
        # Encabezado
        self.drawString(36, 11 * inch - 26, "SIAC ERP — Reporte Semanal Consolidado de Desarrollo")
        self.drawRightString(8.5 * inch - 36, 11 * inch - 26, "Semana: 16 al 22 de Agosto, 2026")
        self.setStrokeColor(BORDE_GRIS)
        self.setLineWidth(0.5)
        self.line(36, 11 * inch - 30, 8.5 * inch - 36, 11 * inch - 30)
        
        # Pie de página
        self.line(36, 36, 8.5 * inch - 36, 36)
        self.drawString(36, 24, "Documento Informativo y de Control Interno")
        self.drawRightString(8.5 * inch - 36, 24, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def generar_pdf():
    doc = SimpleDocTemplate(
        OUTPUT, pagesize=letter,
        leftMargin=36, rightMargin=36,
        topMargin=46, bottomMargin=46
    )
    
    story = []
    
    # ── Encabezado Principal ──
    story.append(Paragraph("REPORTE SEMANAL DE ACTIVIDADES Y AVANCES", estilo_titulo))
    story.append(Paragraph("<b>Proyecto:</b> SIAC ERP (Fábrica de Calzado) &nbsp;|&nbsp; <b>Periodo:</b> 16 al 22 de Agosto, 2026 &nbsp;|&nbsp; <b>Versión:</b> 1.0.0", estilo_subtitulo))
    story.append(HRFlowable(width="100%", thickness=1.5, color=INDIGO, spaceBefore=0, spaceAfter=10))
    
    # ── Resumen Ejecutivo ──
    story.append(Paragraph("1. Resumen Ejecutivo", estilo_h1))
    story.append(Paragraph(
        "Durante la presente semana se consolidaron trabajos críticos en todas las líneas de desarrollo "
        "(ramas <b>productivo1</b>, <b>Goretti_Prd</b> y <b>main</b>). La meta principal se centró en "
        "la <b>estabilización del sistema para piso de producción</b>, la <b>mejora visual y ergonomía de captura</b>, "
        "la emisión de <b>reportes de programación claros con subtotales por corrida</b> y la preparación del <b>instalador oficial (v1.0.0)</b>.",
        estilo_cuerpo
    ))
    
    # Tabla resumen métricas
    datos_resumen = [
        [Paragraph("Área de Enfoque", estilo_th), Paragraph("Impacto en Operación", estilo_th), Paragraph("Estado", estilo_th)],
        [Paragraph("<b>Reportes de Programación</b>", estilo_td), Paragraph("Impresión con carátula ejecutiva, separación de hojas por corrida y subtotales.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Experiencia de Usuario (UI)</b>", estilo_td), Paragraph("Buscador global rápido (Ctrl+K), atajos directos y tablas interactivas tipo Excel.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Fluidez de Captura</b>", estilo_td), Paragraph("Eliminación de sugerencias/bloqueos automáticos de Windows en cajas de texto.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Distribución (v1.0.0)</b>", estilo_td), Paragraph("Generación de ejecutable independiente y manual de usuario formal en PDF.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Herramientas Admin</b>", estilo_td), Paragraph("Visor de bitácora y auditoría de eventos del sistema (Logs con filtros y exportación).", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)]
    ]
    t_resumen = Table(datos_resumen, colWidths=[130, 310, 100])
    t_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDE_GRIS),
        ('BOX', (0, 0), (-1, -1), 1, AZUL_DARK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_resumen)
    story.append(Spacer(1, 10))
    
    # ── Detalle de Módulos y Cambios ──
    story.append(Paragraph("2. Detalle de Módulos y Cambios Realizados", estilo_h1))
    
    story.append(Paragraph("A. Módulo de Producción y Programación Semanal", estilo_h2))
    story.append(Paragraph("• <b>Carátula Resumen Obligatoria:</b> Al imprimir la programación de la semana se genera una primera hoja ejecutiva que condensa los totales generales de pares por modelo y cliente antes de entrar al detalle.", estilo_bullet))
    story.append(Paragraph("• <b>Saltos de Página por Corrida:</b> Se estructuró el reporte para que el desglose de tallas/puntos no se mezcle de forma desordenada en una sola hoja, facilitando la entrega de hojas individuales a las áreas de corte y ensamble.", estilo_bullet))
    story.append(Paragraph("• <b>Subtotales Claros:</b> Cálculo automático y visible de pares totales por grupo de tallas.", estilo_bullet))
    
    story.append(Paragraph("B. Ergonomía, Rapidez y Experiencia de Usuario", estilo_h2))
    story.append(Paragraph("• <b>Buscador Global (Ctrl + K):</b> Los usuarios ahora pueden presionar <i>Ctrl + K</i> desde cualquier pantalla para escribir y abrir inmediatamente cualquier módulo o función del sistema sin necesidad de usar el ratón.", estilo_bullet))
    story.append(Paragraph("• <b>Eliminación de Trabas en Captura:</b> Se implementó una protección global que desactiva el historial emergente del sistema operativo en cajas de texto, lo que previene que la aplicación se trabe o se desplieguen menús no deseados durante la captura continua de pedidos e inventario.", estilo_bullet))
    story.append(Paragraph("• <b>Tablas Modernas (Grid Híbrido):</b> Unificación visual de las tablas de datos combinando búsqueda rápida, agrupación visual y botones de acción unificados.", estilo_bullet))
    story.append(Paragraph("• <b>Barra de Menús y Barra de Herramientas:</b> Rediseño con estilo oscuro profesional, iconos ordenados por módulo a la izquierda y opciones de sistema a la derecha.", estilo_bullet))

    story.append(Paragraph("C. Administración, Seguridad y Auditoría", estilo_h2))
    story.append(Paragraph("• <b>Visor de Registro de Eventos (Logs):</b> Pantalla exclusiva para administradores en el menú de Ayuda que permite auditar errores, advertencias e historial de uso, con opciones de filtrado y exportación para diagnóstico técnico inmediato.", estilo_bullet))
    story.append(Paragraph("• <b>Optimización de Inicio de Sesión:</b> Se protegió el botón de acceso para evitar solicitudes dobles y se agilizó la validación de credenciales.", estilo_bullet))
    story.append(Paragraph("• <b>Configuración Centralizada:</b> Se optimizó la lectura de datos de la empresa desde la sección de Configuración del sistema.", estilo_bullet))

    story.append(Paragraph("D. Empaquetado y Documentación Oficial", estilo_h2))
    story.append(Paragraph("• <b>Etiquetado de Release v1.0.0:</b> Se estructuró el empaquetado mediante PyInstaller para generar el software listo para instalarse en las computadoras de planta y oficina.", estilo_bullet))
    story.append(Paragraph("• <b>Manual de Usuario Oficial:</b> Se elaboró e integró un manual completo en PDF con ilustraciones y explicaciones paso a paso de cada módulo para capacitación del personal.", estilo_bullet))

    story.append(PageBreak())

    # ── Cronología de Cambios (Ramas y Commits) ──
    story.append(Paragraph("3. Bitácora Cronológica de Trabajo (Todas las Ramas)", estilo_h1))
    story.append(Paragraph(
        "A continuación se presenta el registro cronológico consolidando las ramas <b>productivo1</b> y <b>Goretti_Prd</b>:",
        estilo_cuerpo
    ))
    
    bitacora_data = [
        [Paragraph("Fecha / Ref", estilo_th), Paragraph("Rama", estilo_th), Paragraph("Descripción del Cambio", estilo_th), Paragraph("Beneficio / Resultado", estilo_th)],
        
        [Paragraph("22/08 05:14<br/><code>70c87a1</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Asegurar carátula visible en impresión de programación.", estilo_td),
         Paragraph("Garantiza que la hoja resumen siempre aparezca en el PDF final sin importar la cantidad de registros.", estilo_td)],
        
        [Paragraph("22/08 04:57<br/><code>fa9f1d0</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Carátula resumen y saltos de página por corrida.", estilo_td),
         Paragraph("Separa limpiamente las hojas de trabajo por corrida de calzado para entrega en taller.", estilo_td)],

        [Paragraph("21/08 18:22<br/><code>19f3544</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Conexión de botón Imprimir en Programación.", estilo_td),
         Paragraph("El botón de impresión ahora invoca directamente el nuevo formato con subtotales.", estilo_td)],

        [Paragraph("21/08 16:56<br/><code>ddc13b6</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Buscador global rápido (Ctrl+K) y atajos.", estilo_td),
         Paragraph("Navegación veloz entre módulos usando únicamente el teclado.", estilo_td)],

        [Paragraph("21/08 13:01<br/><code>57d98ee</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Desactivación global de autocompletado nativo.", estilo_td),
         Paragraph("Elimina trabas y cierres involuntarios al teclear en campos de texto.", estilo_td)],

        [Paragraph("21/08 12:42<br/><code>c324b58</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Seguridad y fluidez en Login.", estilo_td),
         Paragraph("Previene doble clic accidental en acceso y limpia el autocompletado.", estilo_td)],

        [Paragraph("20/08 12:47<br/><code>c1697e6</code>", estilo_td), Paragraph("productivo1<br/>(tag v1.0.0)", estilo_td_bold),
         Paragraph("Release v1.0.0 y empaquetado.", estilo_td),
         Paragraph("Generación del instalador y binarios listos para producción.", estilo_td)],

        [Paragraph("20/08 10:49<br/><code>cb7efe9</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Implementación de Grid Híbrido unificado.", estilo_td),
         Paragraph("Homologa la apariencia de todas las tablas de datos del sistema.", estilo_td)],

        [Paragraph("19/08 10:48<br/><code>7cb559f</code>", estilo_td), Paragraph("Goretti_Prd", estilo_td_bold),
         Paragraph("Plantilla compartida de impresión y stock.", estilo_td),
         Paragraph("Formato consistente tipo vista previa exacta en todas las impresiones.", estilo_td)],

        [Paragraph("17/08 20:13<br/><code>4913f2e</code>", estilo_td), Paragraph("productivo1 / Goretti_Prd", estilo_td_bold),
         Paragraph("Módulo de Visor de Logs para Administrador.", estilo_td),
         Paragraph("Auditoría interna de operaciones y soporte técnico simplificado.", estilo_td)],

        [Paragraph("17/08 16:27<br/><code>edf2a11</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Manual de Usuario SIAC ERP en PDF.", estilo_td),
         Paragraph("Documento integral para entrenamiento de personal operativo.", estilo_td)],

        [Paragraph("17/08 16:04<br/><code>82cecf5</code>", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Movimientos multi-partida y levantamiento oficio.", estilo_td),
         Paragraph("Permite registrar varios insumos a la vez y genera formatos PDF de levantamiento.", estilo_td)],
    ]
    
    t_bitacora = Table(bitacora_data, colWidths=[80, 85, 175, 200])
    t_bitacora.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDE_GRIS),
        ('BOX', (0, 0), (-1, -1), 1, AZUL_DARK),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_bitacora)
    
    story.append(Spacer(1, 14))
    
    # ── Conclusiones y Próximos Pasos ──
    story.append(Paragraph("4. Conclusiones y Siguientes Pasos", estilo_h1))
    story.append(Paragraph(
        "El sistema ha alcanzado un estado de madurez sólido con la versión 1.0.0. "
        "Para los próximos días se contempla continuar con el seguimiento en piso del nuevo formato de programación semanal, "
        "validar la retroalimentación de los operadores respecto al buscador rápido y avanzar en la siguiente fase de pedidos y clientes.",
        estilo_cuerpo
    ))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Reporte generado exitosamente en: {OUTPUT}")

if __name__ == "__main__":
    generar_pdf()
