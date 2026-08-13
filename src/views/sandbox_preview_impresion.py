"""Demo de Sandbox: Preview de Impresión (componente aprobado).

El componente reutilizable vive en `src/components/preview_impresion.py` y
está registrado en el catálogo como `preview_impresion`. Esta vista es solo
la demo que lo muestra con reportes de ejemplo (datos reales si existen).

El formato aprobado del "Recibo de Orden de Compra" (ondas menta/salvia) vive
en `src/utils/export_utils.py` (`_oc_receipt_html`); aquí solo se referencia.

Uso del componente desde cualquier vista del sistema:
    from src.components.preview_impresion import previsualizar_html

    previsualizar_html(html, titulo="Recibo de Orden de Compra", parent=self)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from src.components.preview_impresion import PreviewImpresion
from src.utils.export_utils import _oc_receipt_html as _oc_receipt_mint_html


def _reporte_oc_html() -> str:
    """Recibo de OC de ejemplo: usa datos reales de la BD si existen."""
    from src.controllers.ordenes_compra_controller import OrdenesCompraController

    ctrl = OrdenesCompraController()
    ordenes = ctrl.listar_ordenes() if hasattr(ctrl, "listar_ordenes") else []
    if not ordenes:
        return _reporte_oc_ejemplo_html()

    oc_id = ordenes[0]["id"]
    datos = ctrl.obtener_orden(oc_id)
    detalle = ctrl.obtener_detalle_orden(oc_id)
    if not datos:
        return _reporte_oc_ejemplo_html()
    return _oc_receipt_mint_html(datos, detalle)


def _reporte_oc_ejemplo_html() -> str:
    """Recibo de compra de ejemplo (sin depender de datos en BD)."""
    datos = {
        "folio": "OC-0001",
        "fecha_emision": "2026-08-12",
        "estatus": "en_proceso",
        "solo_remision": False,
        "proveedor_nombre": "Proveedor Ejemplo S.A. de C.V.",
        "proveedor_telefono": "55 1234 5678",
        "proveedor_email": "ventas@ejemplo.mx",
        "proveedor_rfc": "PEJ000101XYZ",
        "proveedor_direccion": "Av. Industrial 123, León, Gto.",
        "observaciones": "Entregar antes del viernes en la bodega principal.",
    }
    detalle = [
        {"insumo_nombre": "Suela de hule natural", "cantidad": 40,
         "precio_unitario": 58.50,
         "tallas": [{"talla_id": 23, "talla": "23", "pares": 10},
                     {"talla_id": 24, "talla": "24", "pares": 10},
                     {"talla_id": 25, "talla": "25", "pares": 10},
                     {"talla_id": 26, "talla": "26", "pares": 10}]},
        {"insumo_nombre": "Piel vaquera café", "cantidad": 20,
         "precio_unitario": 120.00,
         "tallas": [{"talla_id": 23, "talla": "23", "pares": 5},
                     {"talla_id": 24, "talla": "24", "pares": 5},
                     {"talla_id": 25, "talla": "25", "pares": 5},
                     {"talla_id": 26, "talla": "26", "pares": 5}]},
        {"insumo_nombre": "Hilo encerado", "cantidad": 12,
         "precio_unitario": 15.00, "tallas": []},
    ]
    return _oc_receipt_mint_html(datos, detalle)


def _reporte_inventario_html() -> str:
    """Reporte de inventario de ejemplo con datos reales."""
    from src.controllers.inventario_controller import InventarioController

    ctrl = InventarioController()
    try:
        insumos = ctrl.listar_insumos()[:20]
    except Exception:
        insumos = []

    filas = ""
    for i, ins in enumerate(insumos, start=1):
        stock = ins.get("stock_actual", 0)
        minimo = ins.get("stock_minimo", 0)
        color = "#dc2626" if stock < minimo else "#059669"
        filas += (f"<tr><td>{i}</td><td>{ins.get('codigo', '')}</td>"
                  f"<td>{ins.get('nombre', '')}</td>"
                  f"<td>{ins.get('categoria', '')}</td>"
                  f"<td style='text-align:right'>{stock}</td>"
                  f"<td style='text-align:right;color:{color}'>{minimo}</td></tr>")

    if not filas:
        filas = ("<tr><td colspan='6' style='text-align:center;color:#94a3b8'>"
                 "Sin datos de inventario en la base de datos.</td></tr>")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ margin: 14mm; }}
body {{ font-family: Segoe UI, Arial, sans-serif; font-size: 12px; color: #1f2937; margin: 0; }}
h2 {{ color: #1e293b; margin: 0 0 4px 0; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
th {{ background: #4f46e5; color: #fff; padding: 8px; font-size: 11px; }}
td {{ border: 1px solid #e2e8f0; padding: 6px 8px; font-size: 11px; }}
tr:nth-child(even) td {{ background: #f8fafc; }}
</style></head><body>
<div style='border-bottom:2px solid #4f46e5;padding-bottom:8px'>
<h2>Reporte de Inventario</h2>
<span style='color:#64748b;font-size:11px'>SIAC ERP · {len(insumos)} insumos mostrados</span>
</div>
<table>
<tr><th>#</th><th>Código</th><th>Nombre</th><th>Categoría</th><th>Stock</th><th>Stock mín.</th></tr>
{filas}
</table>
</body></html>"""


class PreviewImpresionDemo(QDialog):
    """Demo del componente aprobado 'preview_impresion' (Sandbox)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preview de impresión — componente aprobado")
        self.resize(760, 420)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        titulo = QLabel("Preview de impresión (componente aprobado)")
        titulo.setObjectName("sectionTitle")
        titulo.setWordWrap(True)
        lay.addWidget(titulo)

        subtitulo = QLabel(
            "Muestra cómo se verá un reporte ANTES de imprimirlo o exportarlo "
            "a PDF: misma fidelidad que el documento final (WYSIWYG). Vive en "
            "src/components/preview_impresion.py y se usa vía "
            "previsualizar_html(html, titulo, parent).")
        subtitulo.setObjectName("sectionSubtitle")
        subtitulo.setWordWrap(True)
        lay.addWidget(subtitulo)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Reporte de ejemplo:"))
        self.cmb_reporte = QComboBox()
        self.cmb_reporte.addItems([
            "Recibo de Orden de Compra",
            "Reporte de Inventario",
        ])
        fila.addWidget(self.cmb_reporte, 1)

        btn_ver = QPushButton("Ver preview")
        btn_ver.setObjectName("btnPrimary")
        btn_ver.setCursor(Qt.PointingHandCursor)
        btn_ver.clicked.connect(self._ver_preview)
        fila.addWidget(btn_ver)
        lay.addLayout(fila)

        nota = QLabel(
            "En producción, este preview se abriría antes de imprimir o "
            "exportar cualquier reporte del sistema (OC, inventario, "
            "producción, etiquetas...).")
        nota.setStyleSheet("color: #64748b; font-size: 11px;")
        nota.setWordWrap(True)
        lay.addWidget(nota)

        lay.addStretch()

        bar = QHBoxLayout()
        bar.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecondary")
        btn_cerrar.clicked.connect(self.accept)
        bar.addWidget(btn_cerrar)
        lay.addLayout(bar)

    def _ver_preview(self) -> None:
        if self.cmb_reporte.currentIndex() == 0:
            html = _reporte_oc_html()
            titulo = "Preview — Recibo de Orden de Compra"
        else:
            html = _reporte_inventario_html()
            titulo = "Preview — Reporte de Inventario"
        dlg = PreviewImpresion(html, titulo=titulo, parent=self)
        dlg.exec()
