"""Genera el reporte de trabajo semanal de SIAC ERP en PDF (reportlab).

El reporte se construye a partir del historial de git de la semana (commits,
archivos modificados, líneas agregadas/eliminadas), se explica en lenguaje
sencillo para personas no técnicas y se guarda en
reportes/Reporte_Trabajo_Semanal_<inicio>_al_<fin>.pdf.

Uso:
    python scripts/reporte_semanal.py                       # semana actual (lunes a hoy)
    python scripts/reporte_semanal.py --desde 2026-08-10 --hasta 2026-08-15
"""

import argparse
import datetime
import re
import subprocess
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

RAIZ = Path(__file__).resolve().parent.parent
DIA_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado",
              "domingo"]
ANCHO = 184 * mm

PRIMARIO = colors.HexColor("#4f46e5")
OSCURO = colors.HexColor("#1e293b")
GRIS = colors.HexColor("#64748b")
CLARO = colors.HexColor("#f1f5f9")
BORDE = colors.HexColor("#e2e8f0")
VERDE = colors.HexColor("#16a34a")
ROJO = colors.HexColor("#dc2626")

PATRON_COMMIT = re.compile(r"^[0-9a-f]{40}\|")

FUENTE_NORMAL = "Helvetica"
FUENTE_BOLD = "Helvetica-Bold"
FUENTE_ITALICA = "Helvetica-Oblique"
FUENTES_UNICODE = False

# Temas del trabajo semanal: título + explicación en lenguaje sencillo.
# Cada commit se clasifica por las palabras clave de su descripción.
TEMAS: list[dict[str, Any]] = [
    {
        "titulo": "Pedidos y programación semanal",
        "explicacion": (
            "Los pedidos de los clientes ahora se incorporan a la programación "
            "semanal de producción. Cada línea de pedido se puede programar por "
            "fila, se captura su corrida de tallas (del punto X al punto Y) y esa "
            "corrida se muestra en la columna Corrida. Cuando una línea queda "
            "programada, su estatus se bloquea para evitar cambios accidentales."),
        "claves": ["programac", "pedido", "programar", "corrida", "linea de pedido"],
    },
    {
        "titulo": "Catálogos y base de datos",
        "explicacion": (
            "Se unificaron los puntos y las tallas en un solo catálogo (las tallas "
            "se manejan por corrida, de medio en medio punto). Los pedidos de "
            "clientes ahora usan el mismo catálogo que el resto del sistema, lo que "
            "elimina datos duplicados e inconsistencias. Las actualizaciones de la "
            "base de datos se aplican solas al abrir el programa, sin perder "
            "información."),
        "claves": ["talla", "punto", "catálogo", "catalogo", "migraci", "rd-1",
                   "esquema"],
    },
    {
        "titulo": "Impresión de etiquetas y reportes",
        "explicacion": (
            "Se rediseñó la impresión de etiquetas con dos modos: Flejes (cajas) y "
            "Partidas, ambos con matriz de tallas. Se agregó una impresora virtual "
            "que muestra en pantalla el resultado de una impresión sin gastar papel, "
            "y la programación semanal se puede exportar con formato de reporte "
            "listo para presentar."),
        "claves": ["etiqueta", "impres", "flejes", "partidas", "kardex", "ficha",
                   "reporte", "preview", "cola", "matriz"],
    },
    {
        "titulo": "Interfaz y experiencia de uso",
        "explicacion": (
            "El sistema adoptó un tema clásico estilo Windows, familiar para los "
            "usuarios de escritorio. Se agregaron notificaciones flotantes de éxito "
            "al guardar, un toolbar superior de navegación, iconos de fila "
            "circulares y se ajustaron los tamaños de ventana y de las matrices de "
            "tallas para mostrar todo el contenido."),
        "claves": ["tema", "notificacion", "toolbar", "navegacion", "icono",
                   "ventana", "estilo", "windows forms", "flotante"],
    },
    {
        "titulo": "Componentes y catálogo de controles",
        "explicacion": (
            "Se amplió el catálogo de componentes reutilizables del sistema: campo "
            "con histórico de capturas, selector de fecha con calendario, catálogo "
            "de componentes del Sandbox y botones extra en las tablas."),
        "claves": ["componente", "sandbox", "histórico", "historico", "date picker",
                   "grid", "editor"],
    },
    {
        "titulo": "Empaquetado y despliegue",
        "explicacion": (
            "El sistema se empaquetó como programa ejecutable (.exe): ya no se "
            "necesita Python instalado para usarlo. Los datos del usuario se "
            "guardan en su propia carpeta de AppData, separados del programa, para "
            "que una actualización no borre la información capturada."),
        "claves": ["empaqueta", "pyinstaller", "appdata", "despliegue",
                   "ejecutable"],
    },
    {
        "titulo": "Órdenes de compra e inventario",
        "explicacion": (
            "En las órdenes de compra se incorporó el precio por talla, se amplió "
            "el catálogo de puntos del 15 al 21 y los proveedores se eligen por "
            "razón social o nombre comercial. El detalle de la orden se muestra con "
            "filas más altas para una mejor lectura."),
        "claves": ["orden", "compra", "inventario", "proveedor", "precio", "stock",
                   "insumo"],
    },
    {
        "titulo": "Estabilidad, pruebas y calidad",
        "explicacion": (
            "Se corrigieron fallas al cerrar la aplicación y se automatizaron las "
            "pruebas de los componentes nuevos para que se ejecuten con cada "
            "cambio. Esto garantiza que las mejoras no rompan funciones ya "
            "existentes."),
        "claves": ["segfault", "pytest", "ci", "xvfb", "offscreen", "teardown",
                   "prueba", "test", "corrige", "limpieza", "workflow", "fixture"],
    },
    {
        "titulo": "Otros ajustes y mejoras",
        "explicacion": "Cambios menores y de soporte que no encajan en los temas anteriores.",
        "claves": [],
    },
]


def ejecutar_git(args: list[str]) -> str:
    """Ejecuta un comando git en la raíz del repositorio y devuelve la salida."""
    resultado = subprocess.run(
        ["git", *args],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return resultado.stdout


def obtener_commits(desde: datetime.date, hasta: datetime.date) -> list[dict]:
    """Devuelve los commits (sin merges) de la semana con sus archivos."""
    salida = ejecutar_git([
        "log",
        "--since", f"{desde} 00:00:00",
        "--until", f"{hasta} 23:59:59",
        "--no-merges",
        "--date=format:%Y-%m-%dT%H:%M",
        "--pretty=format:%H|%ad|%an|%s",
        "--numstat",
        "--",
    ])
    commits: list[dict] = []
    actual: dict[str, Any] | None = None
    for linea in salida.splitlines():
        if not linea.strip():
            continue
        if PATRON_COMMIT.match(linea):
            if actual is not None:
                commits.append(actual)
            hash_, fecha_hora, autor, *resto = linea.split("|", 3)
            asunto = resto[0] if resto else ""
            iso, hora = fecha_hora.split("T")
            fecha = datetime.date.fromisoformat(iso)
            actual = {"hash": hash_[:7], "hash_largo": hash_, "fecha": fecha,
                      "hora": hora, "autor": autor, "asunto": asunto,
                      "archivos": [], "insertadas": 0, "eliminadas": 0}
        elif actual is not None:
            partes = linea.split("\t")
            if len(partes) == 3 and partes[0].isdigit() and partes[1].isdigit():
                actual["archivos"].append(partes[2])
                actual["insertadas"] += int(partes[0])
                actual["eliminadas"] += int(partes[1])
    if actual is not None:
        commits.append(actual)
    return commits


def contar_merges(desde: datetime.date, hasta: datetime.date) -> int:
    """Cuenta los merges (fusiones de versiones) de la semana."""
    lineas = ejecutar_git([
        "log",
        "--since", f"{desde} 00:00:00",
        "--until", f"{hasta} 23:59:59",
        "--merges", "--pretty=format:%H",
    ]).splitlines()
    return len([l for l in lineas if l.strip()])


def cambios_pendientes() -> tuple[int, list[str]]:
    """Devuelve archivos con cambios sin confirmar (modificados o nuevos)."""
    lineas = [l for l in ejecutar_git(["status", "--short"]).splitlines()
              if l.strip()]
    archivos: list[str] = []
    for linea in lineas:
        nombre = linea[3:].strip()
        if nombre and nombre not in archivos:
            archivos.append(nombre)
    return len(lineas), archivos


def clasificar_commits(commits: list[dict]) -> list[dict[str, Any]]:
    """Agrupa los commits por tema usando las palabras clave de su descripción."""
    por_tema = [{"tema": dict(tema), "commits": []} for tema in TEMAS]
    for c in commits:
        asunto = c["asunto"].lower()
        mejor_idx, mejor_puntaje = len(por_tema) - 1, 0
        for i, grupo in enumerate(por_tema):
            puntaje = sum(1 for k in grupo["tema"]["claves"] if k in asunto)
            if puntaje > mejor_puntaje:
                mejor_puntaje, mejor_idx = puntaje, i
        por_tema[mejor_idx]["commits"].append(c)
    return [g for g in por_tema if g["commits"]]


def _registrar_fuentes() -> tuple[str, str, str]:
    """Registra Segoe UI si está disponible (fallback Helvetica)."""
    global FUENTE_NORMAL, FUENTE_BOLD, FUENTE_ITALICA, FUENTES_UNICODE
    if Path("C:/Windows/Fonts/segoeui.ttf").exists():
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        for nombre, ruta in (("SegoeUI", "C:/Windows/Fonts/segoeui.ttf"),
                             ("SegoeUI-Bold", "C:/Windows/Fonts/segoeuib.ttf"),
                             ("SegoeUI-Italic", "C:/Windows/Fonts/segoeuii.ttf")):
            if Path(ruta).exists():
                pdfmetrics.registerFont(TTFont(nombre, ruta))
        FUENTE_NORMAL, FUENTE_BOLD, FUENTE_ITALICA = (
            "SegoeUI", "SegoeUI-Bold", "SegoeUI-Italic")
        FUENTES_UNICODE = True
    return FUENTE_NORMAL, FUENTE_BOLD, FUENTE_ITALICA


def _texto(valor: str) -> str:
    """Normaliza texto dinámico a la codificación soportada por la fuente."""
    if FUENTES_UNICODE:
        return valor
    return valor.encode("latin-1", errors="replace").decode("latin-1")


def _estilos(normal: str, bold: str) -> dict[str, ParagraphStyle]:
    return {
        "titulo": ParagraphStyle("titulo", fontName=bold, fontSize=20,
                                 textColor=OSCURO, leading=24, alignment=TA_LEFT),
        "subtitulo": ParagraphStyle("subtitulo", fontName=normal, fontSize=10.5,
                                    textColor=GRIS, leading=14),
        "h2": ParagraphStyle("h2", fontName=bold, fontSize=13, textColor=PRIMARIO,
                             leading=16, spaceBefore=10, spaceAfter=6),
        "cuerpo": ParagraphStyle("cuerpo", fontName=normal, fontSize=9.5,
                                 textColor=OSCURO, leading=13.5),
        "lista": ParagraphStyle("lista", fontName=normal, fontSize=9.5,
                                textColor=OSCURO, leading=14, leftIndent=4),
        "archivo": ParagraphStyle("archivo", fontName=normal, fontSize=8.3,
                                  textColor=GRIS, leading=11, leftIndent=8),
        "celda": ParagraphStyle("celda", fontName=normal, fontSize=9,
                                textColor=OSCURO, leading=11),
        "celda_centro": ParagraphStyle("celda_centro", parent=None, fontName=normal,
                                       fontSize=9, textColor=OSCURO, leading=11,
                                       alignment=TA_CENTER),
        "celda_head": ParagraphStyle("celda_head", fontName=bold, fontSize=9,
                                     textColor=colors.white, leading=11,
                                     alignment=TA_CENTER),
    }


def _tabla_datos(datos: list[list[Any]], anchos: list[float]) -> Table:
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARIO),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for fila in range(1, len(datos)):
        if fila % 2 == 0:
            estilo.append(("BACKGROUND", (0, fila), (-1, fila), CLARO))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _link_commit(hash_largo: str, corto: str) -> str:
    url = f"https://github.com/gorettiboots-commits/siacerp/commit/{hash_largo}"
    return f'<link href="{url}" color="#4f46e5">{corto}</link>'


def _fecha_mes(fecha: datetime.date) -> str:
    return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"


def _nombre_dia(fecha: datetime.date) -> str:
    return DIA_SEMANA[fecha.weekday()]


def _cabecera(desde: datetime.date, hasta: datetime.date, normal: str,
              bold: str) -> list[Any]:
    est = _estilos(normal, bold)
    celdas = [
        Paragraph("Reporte de Trabajo Semanal", est["titulo"]),
        Paragraph("SIAC ERP — Sistema Integral de Administración y Control",
                  est["subtitulo"]),
        Paragraph(f"Periodo: {_fecha_mes(desde)} al {_fecha_mes(hasta)}",
                  est["subtitulo"]),
    ]
    return celdas


def _tabla_resumen(stats: dict[str, Any], normal: str, bold: str) -> Table:
    etiquetas = ["Cambios integrados", "Fusiones de versiones", "Archivos tocados",
                 "Líneas agregadas", "Líneas quitadas", "Colaboradores",
                 "En curso"]
    valores = [str(stats["commits"]), str(stats["merges"]), str(stats["archivos"]),
               str(stats["insertadas"]), str(stats["eliminadas"]),
               str(stats["autores"]), str(stats["pendientes"])]
    est = _estilos(normal, bold)
    filas = [
        [Paragraph(et, est["celda_head"]) for et in etiquetas],
        [Paragraph(v, est["celda_centro"]) for v in valores],
    ]
    return _tabla_datos(filas, [ANCHO / len(etiquetas)] * len(etiquetas))


def _tabla_por_dia(commits: list[dict], normal: str, bold: str) -> Table:
    por_dia: dict[datetime.date, dict[str, int]] = {}
    for c in commits:
        clave = c["fecha"]
        if clave not in por_dia:
            por_dia[clave] = {"commits": 0, "archivos": 0, "insertadas": 0,
                              "eliminadas": 0}
        por_dia[clave]["commits"] += 1
        por_dia[clave]["archivos"] += len(c["archivos"])
        por_dia[clave]["insertadas"] += c["insertadas"]
        por_dia[clave]["eliminadas"] += c["eliminadas"]

    est = _estilos(normal, bold)
    filas = [[Paragraph(h, est["celda_head"]) for h in
              ["Día", "Fecha", "Cambios", "Archivos", "Líneas +", "Líneas −"]]]
    for fecha in sorted(por_dia):
        d = por_dia[fecha]
        filas.append([
            Paragraph(_nombre_dia(fecha).capitalize(), est["celda"]),
            Paragraph(_fecha_mes(fecha), est["celda_centro"]),
            Paragraph(str(d["commits"]), est["celda_centro"]),
            Paragraph(str(d["archivos"]), est["celda_centro"]),
            Paragraph(f"<font color='#16a34a'>+{d['insertadas']}</font>",
                       est["celda_centro"]),
            Paragraph(f"<font color='#dc2626'>−{d['eliminadas']}</font>",
                       est["celda_centro"]),
        ])
    anchos = [30 * mm, 24 * mm, 20 * mm, 24 * mm, 20 * mm, 20 * mm]
    return _tabla_datos(filas, anchos)


def _resumen_ejecutivo(por_tema: list[dict[str, Any]], desde: datetime.date,
                       hasta: datetime.date, normal: str, bold: str) -> list[Any]:
    est = _estilos(normal, bold)
    flujos: list[Any] = []
    flujos.append(Paragraph(
        f"Este documento resume el trabajo realizado en el sistema SIAC ERP "
        f"durante la semana del {_fecha_mes(desde)} al {_fecha_mes(hasta)}. "
        f"A continuación se explican los avances en lenguaje sencillo; al "
        f"final se incluye el detalle técnico completo.",
        est["cuerpo"]))
    flujos.append(Spacer(1, 2 * mm))
    for grupo in por_tema:
        n = len(grupo["commits"])
        flujos.append(Paragraph(
            f"• <b>{_texto(grupo['tema']['titulo'])}</b> — {n} cambio"
            f"{'s' if n != 1 else ''}.", est["lista"]))
    flujos.append(Spacer(1, 2 * mm))
    flujos.append(Paragraph(
        "<i>Cómo leer este reporte:</i> un \"cambio\" es una mejora integrada al "
        "sistema y verificada con pruebas automáticas. Los \"archivos\" son las "
        "pantallas y reglas de negocio que se tocaron. Las \"líneas\" indican "
        "cuánto código se agregó (+) o se quitó (−) y son una medida del tamaño "
        "del trabajo.", est["cuerpo"]))
    return flujos


def _detalle_por_tema(por_tema: list[dict[str, Any]], normal: str,
                      bold: str) -> list[Any]:
    est = _estilos(normal, bold)
    flujos: list[Any] = []
    for grupo in por_tema:
        tema = grupo["tema"]
        flujos.append(Paragraph(tema["titulo"], est["h2"]))
        flujos.append(Paragraph(_texto(tema["explicacion"]), est["cuerpo"]))
        flujos.append(Spacer(1, 2 * mm))
        filas = [[Paragraph(h, est["celda_head"]) for h in
                  ["Fecha", "Cambio", "Descripción", "Archivos"]]]
        for c in grupo["commits"]:
            filas.append([
                Paragraph(_fecha_mes(c["fecha"]), est["celda_centro"]),
                Paragraph(_link_commit(c["hash_largo"], c["hash"]),
                          est["celda_centro"]),
                Paragraph(_texto(c["asunto"]), est["celda"]),
                Paragraph(str(len(c["archivos"])), est["celda_centro"]),
            ])
        flujos.append(_tabla_datos(filas, [22 * mm, 20 * mm, 122 * mm, 20 * mm]))
        flujos.append(Spacer(1, 3 * mm))
    return flujos


def _anexo_por_dia(commits: list[dict], normal: str, bold: str) -> list[Any]:
    est = _estilos(normal, bold)
    flujos: list[Any] = []
    por_dia: dict[datetime.date, list[dict]] = {}
    for c in commits:
        por_dia.setdefault(c["fecha"], []).append(c)

    for fecha in sorted(por_dia, reverse=True):
        flujos.append(Paragraph(
            f"{_nombre_dia(fecha).capitalize()} — {_fecha_mes(fecha)}",
            est["h2"]))
        for c in por_dia[fecha]:
            filas = [[
                Paragraph(_link_commit(c["hash_largo"], c["hash"]),
                          est["celda"]),
                Paragraph(c["hora"], est["celda_centro"]),
                Paragraph(_texto(c["autor"]), est["celda"]),
                Paragraph(_texto(c["asunto"]), est["celda"]),
            ]]
            flujos.append(_tabla_datos(
                filas, [20 * mm, 16 * mm, 36 * mm, 112 * mm]))
            for archivo in c["archivos"]:
                flujos.append(Paragraph(f"• {_texto(archivo)}", est["archivo"]))
            flujos.append(Spacer(1, 2 * mm))
    return flujos


def _proximos_pasos(normal: str, bold: str) -> list[Any]:
    est = _estilos(normal, bold)
    pasos = [
        "Módulo de clientes y pedidos con programación semanal integrada "
        "(en desarrollo).",
        "Migración de la base de datos a PostgreSQL para producción.",
        "Diseñador e impresor de etiquetas en terminal de trabajo.",
        "Sincronización de datos entre estaciones de trabajo (Supabase).",
    ]
    return [Paragraph(f"• {paso}", est["lista"]) for paso in pasos]


def _pie_pagina(canvas: Any, doc: Any) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDE)
    canvas.setLineWidth(0.5)
    canvas.line(15 * mm, 13 * mm, 15 * mm + ANCHO, 13 * mm)
    canvas.setFont(FUENTE_NORMAL, 8)
    canvas.setFillColor(GRIS)
    canvas.drawCentredString(
        letter[0] / 2, 9 * mm,
        "Generado por SIAC ERP — Desarrollado por Mario Felipe Luevano — "
        "© 2026. Todos los derechos reservados.")
    canvas.drawRightString(15 * mm + ANCHO, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def construir_pdf(commits: list[dict], desde: datetime.date,
                  hasta: datetime.date, stats: dict[str, Any],
                  pendientes: list[str]) -> Path:
    normal, bold, _ = _registrar_fuentes()
    ruta = RAIZ / "reportes" / (
        f"Reporte_Trabajo_Semanal_{desde.isoformat()}_al_{hasta.isoformat()}.pdf")
    ruta.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(ruta), pagesize=letter,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title=f"Reporte de trabajo semanal {_fecha_mes(desde)} - {_fecha_mes(hasta)}",
        author="SIAC ERP")

    est = _estilos(normal, bold)
    historia: list[Any] = []
    historia += _cabecera(desde, hasta, normal, bold)
    historia.append(Spacer(1, 4 * mm))

    if not commits:
        historia.append(Paragraph(
            "No se registraron cambios confirmados en el periodo.", est["cuerpo"]))
    else:
        por_tema = clasificar_commits(commits)

        historia.append(Paragraph("Resumen ejecutivo", est["h2"]))
        historia += _resumen_ejecutivo(por_tema, desde, hasta, normal, bold)
        historia.append(Spacer(1, 3 * mm))

        historia.append(Paragraph("Cifras de la semana", est["h2"]))
        historia.append(_tabla_resumen(stats, normal, bold))
        historia.append(Spacer(1, 3 * mm))

        historia.append(Paragraph("Actividad por día", est["h2"]))
        historia.append(_tabla_por_dia(commits, normal, bold))
        historia.append(Spacer(1, 3 * mm))

        historia.append(Paragraph("Cambios principales por tema", est["h2"]))
        historia += _detalle_por_tema(por_tema, normal, bold)

        if pendientes:
            historia.append(Paragraph("Trabajo en curso (sin confirmar)", est["h2"]))
            for nombre in pendientes[:30]:
                historia.append(Paragraph(f"• {_texto(nombre)}", est["archivo"]))
            if len(pendientes) > 30:
                historia.append(Paragraph(
                    f"… y {len(pendientes) - 30} archivos más.", est["archivo"]))
            historia.append(Spacer(1, 3 * mm))

        historia.append(Paragraph("Próximos pasos", est["h2"]))
        historia += _proximos_pasos(normal, bold)

        historia.append(Spacer(1, 4 * mm))
        historia.append(Paragraph("Anexo — Detalle técnico por día", est["h2"]))
        historia += _anexo_por_dia(commits, normal, bold)

    historia.append(Spacer(1, 6 * mm))
    doc.build(historia, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return ruta


def semana_actual() -> tuple[datetime.date, datetime.date]:
    hoy = datetime.date.today()
    inicio = hoy - datetime.timedelta(days=hoy.weekday())
    return inicio, hoy


def main() -> None:
    parser = argparse.ArgumentParser(description="Reporte de trabajo semanal PDF")
    parser.add_argument("--desde", type=datetime.date.fromisoformat, default=None,
                        help="Fecha de inicio (YYYY-MM-DD)")
    parser.add_argument("--hasta", type=datetime.date.fromisoformat, default=None,
                        help="Fecha de fin (YYYY-MM-DD)")
    args = parser.parse_args()

    desde, hasta = semana_actual()
    if args.desde:
        desde = args.desde
    if args.hasta:
        hasta = args.hasta

    commits = obtener_commits(desde, hasta)
    merges = contar_merges(desde, hasta)
    pendientes, archivos_pendientes = cambios_pendientes()

    archivos = sum(len(c["archivos"]) for c in commits)
    insertadas = sum(c["insertadas"] for c in commits)
    eliminadas = sum(c["eliminadas"] for c in commits)
    autores = sorted({c["autor"] for c in commits})

    stats = {
        "commits": len(commits),
        "merges": merges,
        "archivos": archivos,
        "insertadas": insertadas,
        "eliminadas": eliminadas,
        "autores": len(autores),
        "pendientes": pendientes,
    }

    ruta = construir_pdf(commits, desde, hasta, stats, archivos_pendientes)
    print(f"Reporte generado: {ruta}")
    print(f"Cambios: {len(commits)} | Merges: {merges} | "
          f"Archivos: {archivos} | +{insertadas} -{eliminadas}")
    if autores:
        print("Colaboradores: " + ", ".join(autores))


if __name__ == "__main__":
    main()
