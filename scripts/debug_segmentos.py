"""Script de debug: verifica qué datos llegan a _detectar_segmentos."""
import sys
sys.path.insert(0, ".")

from src.database.db_manager import DatabaseManager
from src.models.programacion_model import ProgramacionModel
from src.utils.programacion_print import _detectar_segmentos, _tallas_linea, _normalizar_talla


def main():
    db = DatabaseManager()
    model = ProgramacionModel()

    # Obtener semanas disponibles
    semanas = model.listar_semanas()
    if not semanas:
        print("No hay semanas")
        return

    for s in semanas:
        print(f"\n{'='*60}")
        print(f"SEMANA: {s['nombre']} (id={s['id']})")
        print(f"{'='*60}")

        lineas = model.lineas_con_tallas(s["id"])
        if not lineas:
            print("  Sin líneas")
            continue

        print(f"  Total líneas: {len(lineas)}")

        # Mostrar tallas de cada línea
        for l in lineas:
            tl = _tallas_linea(l)
            vals = sorted(float(t) for t in tl) if tl else []
            rango = f"[{vals[0]} - {vals[-1]}]" if vals else "[sin tallas]"
            print(f"  Línea {l.get('folio_prog', '?'):>6s} "
                  f"{l.get('cliente', '')[:20]:20s} "
                  f"tallas={rango} "
                  f"lista={sorted(tl)}")

        # Ejecutar detección de segmentos
        segmentos = _detectar_segmentos(lineas)
        print(f"\n  SEGMENTOS DETECTADOS: {len(segmentos)}")
        for idx, seg in enumerate(segmentos):
            tallas_all = set()
            for l in seg:
                tallas_all |= _tallas_linea(l)
            tallas_ord = sorted(tallas_all, key=lambda x: float(x))
            total = sum(int(l.get("total_pares", 0) or 0) for l in seg)
            print(f"    Segmento {idx+1}: {len(seg)} líneas, "
                  f"{total} pares, "
                  f"tallas=[{tallas_ord[0] if tallas_ord else '?'} "
                  f"- {tallas_ord[-1] if tallas_ord else '?'}]")


if __name__ == "__main__":
    main()
