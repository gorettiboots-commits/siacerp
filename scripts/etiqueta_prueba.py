"""Genera/imprime la etiqueta térmica de prueba (75 x 45 mm).

Uso:
    python scripts/etiqueta_prueba.py                     # genera etiqueta_prueba.png
    python scripts/etiqueta_prueba.py --pdf salida.pdf    # genera PDF vectorial
    python scripts/etiqueta_prueba.py --imprimir          # abre diálogo e imprime

Los datos se pueden cambiar con --modelo/--corte/--color/--talla o editando
datos_prueba() en src/utils/etiqueta_termica.py.
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication  # noqa: E402

from src.utils.etiqueta_termica import (  # noqa: E402
    datos_prueba, etiqueta_termica_pdf, render_etiqueta_termica_pixmap,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Etiqueta térmica de prueba")
    ap.add_argument("--modelo", default=None)
    ap.add_argument("--corte", default=None)
    ap.add_argument("--color", default=None)
    ap.add_argument("--talla", default=None)
    ap.add_argument("--pdf", default=None, help="Ruta del PDF a generar")
    ap.add_argument("--png", default=None, help="Ruta del PNG a generar")
    ap.add_argument("--imprimir", action="store_true",
                    help="Enviar directo a la impresora")
    args = ap.parse_args()

    datos = datos_prueba()
    for k in ("modelo", "corte", "color", "talla"):
        v = getattr(args, k)
        if v is not None:
            datos[k] = v

    app = QApplication.instance() or QApplication([])

    if args.png or not (args.pdf or args.imprimir):
        out = args.png or str(ROOT / "etiqueta_prueba.png")
        pix = render_etiqueta_termica_pixmap(datos)
        if not pix.save(out):
            print(f"ERROR: no se pudo escribir {out}")
            return 1
        print(f"Imagen generada: {out} ({pix.width()}x{pix.height()} px)")

    if args.pdf:
        etiqueta_termica_pdf(args.pdf, datos)
        print(f"PDF generado: {args.pdf}")

    if args.imprimir:
        from PySide6.QtPrintSupport import QPrintDialog, QPrinter  # noqa: E402
        from src.utils.etiqueta_termica import (  # noqa: E402
            configurar_printer, imprimir_etiqueta)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        configurar_printer(printer)
        dlg = QPrintDialog(printer)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            err = imprimir_etiqueta(printer, datos)
            if err:
                print(f"ERROR: {err}")
                return 2
            print("Etiqueta enviada a la impresora.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
