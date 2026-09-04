"""Genera el HTML del reporte con datos reales de la BD."""
import sys
sys.path.insert(0, ".")

from src.controllers.programacion_controller import ProgramacionController
from src.utils.programacion_print import generar_html_programacion


def main():
    ctrl = ProgramacionController()

    # Buscar semana 03-07 agosto
    semanas = ctrl.listar_semanas()
    semana_obj = None
    for s in semanas:
        if "03-07 agosto" in s.get("nombre", "").lower() or "ago" in s.get("nombre", "").lower():
            semana_obj = s
            break

    if not semana_obj:
        print("No se encontró la semana 03-07 agosto")
        return

    print(f"Semana: {semana_obj['nombre']} (id={semana_obj['id']})")

    lineas = ctrl.lineas_con_tallas(semana_obj["id"])
    print(f"Líneas: {len(lineas)}")

    for l in lineas:
        tallas = l.get("tallas", [])
        talla_vals = [t["talla"] for t in tallas]
        print(f"  {l.get('folio_prog', '?'):>6s} {l.get('cliente', '')[:25]:25s} "
              f"tallas={talla_vals[:5]}... total={l.get('total_pares', 0)}")

    titulo = f"PROGRAMACIÓN SEMANAL — {semana_obj['nombre']}"
    html = generar_html_programacion(lineas, titulo=titulo, incluir_semana=False,
                                     auto_imprimir=False)

    from pathlib import Path
    ruta = Path("reporte_real_03_07_agosto.html")
    ruta.write_text(html, encoding="utf-8")
    print(f"\nHTML guardado en: {ruta.resolve()}")


if __name__ == "__main__":
    main()
