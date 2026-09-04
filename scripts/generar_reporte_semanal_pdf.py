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

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "Reporte_Semanal_SIAC_ERP_2026-08-29.pdf")

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
        self.drawRightString(8.5 * inch - 36, 11 * inch - 26, "Semana: 23 al 29 de Agosto, 2026")
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
    story.append(Paragraph("<b>Proyecto:</b> SIAC ERP (Fábrica de Calzado) &nbsp;|&nbsp; <b>Periodo:</b> 23 al 29 de Agosto, 2026 &nbsp;|&nbsp; <b>Versión:</b> 1.1.0", estilo_subtitulo))
    story.append(HRFlowable(width="100%", thickness=1.5, color=INDIGO, spaceBefore=0, spaceAfter=10))
    
    # ── Resumen Ejecutivo ──
    story.append(Paragraph("1. Resumen Ejecutivo", estilo_h1))
    story.append(Paragraph(
        "Durante la presente semana se completaron tareas clave de <b>empaquetado, distribución y configuración</b> del sistema. "
        "Se implementó el <b>icono oficial de la aplicación</b> en escritorio y móvil, se creó la <b>página de configuración de usuario administrador</b> en el instalador, "
        "se preparó el <b>build del APK móvil</b> con Expo EAS y se compiló el <b>instalador v1.1.0</b> con todas las mejoras.",
        estilo_cuerpo
    ))
    
    # Tabla resumen métricas
    datos_resumen = [
        [Paragraph("Área de Enfoque", estilo_th), Paragraph("Impacto en Operación", estilo_th), Paragraph("Estado", estilo_th)],
        [Paragraph("<b>Icono Oficial de la Aplicación</b>", estilo_td), Paragraph("Icono personalizado aplicado a ventana principal, toolbar, instalador (.ico) y app móvil (Android adaptive icon).", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Instalador con Usuario Admin</b>", estilo_td), Paragraph("Nueva página en el instalador para configurar usuario y contraseña del administrador durante la instalación.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Build de APK Móvil</b>", estilo_td), Paragraph("Script build_apk.bat para generar el APK con EAS Build. Iconos adaptativos Android generados.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Instalador v1.1.0</b>", estilo_td), Paragraph("Compilación exitosa del instalador con icono nuevo, página de admin y configuración de empresa/contacto.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)],
        [Paragraph("<b>Documentación Interna</b>", estilo_td), Paragraph("Limpieza de referencias sensibles en README y CHANGELOG. Credenciales internas removidas de documentación pública.", estilo_td), Paragraph("<font color='#16A34A'><b>Completado</b></font>", estilo_td_center)]
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
    
    story.append(Paragraph("A. Icono Oficial y Identidad Visual", estilo_h2))
    story.append(Paragraph("• <b>Conversión de Icono:</b> Se convirtió el archivo <i>icon.png</i> (1024×1024) a formato <b>.ico</b> con múltiples tamaños (16–256px) para PyInstaller y Windows.", estilo_bullet))
    story.append(Paragraph("• <b>Icono en Escritorio:</b> Se aplicó el icono a la ventana principal de la app (<i>MainWindow</i>) y al ejecutable compilado.", estilo_bullet))
    story.append(Paragraph("• <b>Iconos Android Adaptativos:</b> Se generaron las 3 capas del icono adaptativo Android: foreground (zona segura 66%), background sólido y monocromático.", estilo_bullet))

    story.append(Paragraph("B. Instalador con Configuración de Usuario Admin", estilo_h2))
    story.append(Paragraph('• <b>Nueva Página en Inno Setup:</b> Se agregó una página "Usuario Administrador" al instalador con campos de usuario, contraseña (enmascarada), confirmación y nombre completo.', estilo_bullet))
    story.append(Paragraph("• <b>Validación en Instalador:</b> El instalador valida que el usuario no esté vacío, que la contraseña coincida y que ambas contraseñas sean iguales antes de continuar.", estilo_bullet))
    story.append(Paragraph("• <b>Pre-configuración Automática:</b> Al finalizar la instalación se ejecuta el modo <i>--pre-configurar</i> que crea el usuario admin con los datos capturados y le asigna todos los permisos.", estilo_bullet))
    story.append(Paragraph("• <b>Script de Pre-configuración:</b> Se actualizó <i>pre_configurar.py</i> para aceptar los argumentos <i>--admin-user</i>, <i>--admin-password</i> y <i>--admin-nombre</i>.", estilo_bullet))

    story.append(Paragraph("C. App Móvil — Build de APK", estilo_h2))
    story.append(Paragraph("• <b>Script build_apk.bat:</b> Se creó el script automatizado que verifica Node.js, instala EAS CLI, valida la sesión de Expo y ejecuta el build en la nube.", estilo_bullet))
    story.append(Paragraph("• <b>Iconos Móviles Actualizados:</b> Se copió el icono oficial a <i>mobile/assets/</i> y se regeneraron los Android adaptive icons.", estilo_bullet))
    story.append(Paragraph("• <b>EAS Build Ejecutado:</b> Se inició el build del APK en la nube de Expo (perfil production, buildType apk).", estilo_bullet))

    story.append(Paragraph("D. Seguridad y Documentación", estilo_h2))
    story.append(Paragraph("• <b>Limpieza de Credenciales en Docs:</b> Se removieron las credenciales de super_admin del README y CHANGELOG. El usuario interno funciona pero no se documenta.", estilo_bullet))
    story.append(Paragraph("• <b>Compilación del Instalador v1.1.0:</b> Se compiló el ejecutable con PyInstaller y se generó el instalador final con Inno Setup (30.6 MB).", estilo_bullet))

    story.append(PageBreak())

    # ── Cronología de Cambios (Ramas y Commits) ──
    story.append(Paragraph("3. Bitácora Cronológica de Trabajo (Todas las Ramas)", estilo_h1))
    story.append(Paragraph(
        "A continuación se presenta el registro cronológico consolidando las ramas <b>productivo1</b> y <b>Goretti_Prd</b>:",
        estilo_cuerpo
    ))
    
    bitacora_data = [
        [Paragraph("Fecha / Ref", estilo_th), Paragraph("Rama", estilo_th), Paragraph("Descripción del Cambio", estilo_th), Paragraph("Beneficio / Resultado", estilo_th)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Compilación del instalador v1.1.0 (PyInstaller + Inno Setup).", estilo_td),
         Paragraph("Ejecutable y instalador de 30.6 MB con todas las mejoras incluidas.", estilo_td)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Build del APK móvil con EAS Build.", estilo_td),
         Paragraph("Script build_apk.bat automatiza el build en la nube de Expo.", estilo_td)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Iconos adaptativos Android (foreground, background, monochrome).", estilo_td),
         Paragraph("App móvil muestra el icono oficial en todos los dispositivos Android.", estilo_td)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Página de usuario admin en el instalador Inno Setup.", estilo_td),
         Paragraph("El instalador permite configurar usuario y contraseña del admin durante la instalación.", estilo_td)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Icono oficial (.ico + .png) aplicado a la app de escritorio.", estilo_td),
         Paragraph("Ventana principal y ejecutable muestran el icono de SIAC ERP.", estilo_td)],

        [Paragraph("29/08<br/>Sesión IA", estilo_td), Paragraph("productivo1", estilo_td_bold),
         Paragraph("Limpieza de credenciales sensibles en documentación.", estilo_td),
         Paragraph("Credenciales de usuario interno removidas del README y CHANGELOG.", estilo_td)],
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
        "La semana se cerró con el <b>empaquetado completo</b> del sistema: instalador de escritorio v1.1.0 con configuración de admin, "
        "app móvil lista para build de APK e icono oficial aplicado en todas las plataformas. "
        "El sistema está listo para su <b>distribución y despliegue</b> en la fábrica. "
        "Para los próximos días se contempla validar el instalador en equipo de planta, "
        "completar el build del APK y avanzar en la fase de pedidos y clientes (RD-2).",
        estilo_cuerpo
    ))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Reporte generado exitosamente en: {OUTPUT}")

if __name__ == "__main__":
    generar_pdf()
