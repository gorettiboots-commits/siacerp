"""Genera y abre en el navegador la impresión HTML de la programación semanal.

Uso:
    python scripts/imprimir_programacion.py                # imprime la última semana
    python scripts/imprimir_programacion.py 12             # imprime la semana con id 12
    python scripts/imprimir_programacion.py "03-08-2026"   # semana por nombre/rango

Genera un HTML Carta horizontal (@page letter landscape) con encabezado rosa
(#ffccff), una columna por talla y la fila final de totales en negrita; abre el
archivo en el navegador con window.print() activado.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.controllers.programacion_controller import ProgramacionController  # noqa: E402
from src.utils.programacion_print import abrir_programacion_html  # noqa: E402


def _seleccionar_semana(arg: str | None):
    prog = ProgramacionController()
    semanas = prog.listar_semanas()
    if not semanas:
        print("No hay semanas registradas.")
        sys.exit(1)
    if arg is None:
        return semanas[-1]
    if arg.isdigit():
        sem = next((s for s in semanas if s["id"] == int(arg)), None)
        if sem:
            return sem
    sem = next((s for s in semanas
                if arg.lower() in (s.get("nombre") or "").lower()), None)
    if sem:
        return sem
    print(f"No se encontró una semana con: {arg}")
    print("Semanas disponibles:")
    for s in semanas:
        print(f"  {s['id']}  {s.get('nombre', '')}")
    sys.exit(1)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    semana = _seleccionar_semana(arg)
    prog = ProgramacionController()
    lineas = prog.lineas_con_tallas(semana["id"])
    titulo = f"PROGRAMACIÓN SEMANAL — {semana.get('nombre', '')}"
    ruta = abrir_programacion_html(lineas, titulo=titulo)
    print(f"Líneas: {len(lineas)}")
    print(f"HTML guardado y abierto en el navegador:\n{ruta}")


if __name__ == "__main__":
    main()
