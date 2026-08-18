"""Demo de Sandbox: Preview de Impresión (componente aprobado).

El componente reutilizable vive en `src/components/preview_impresion.py` y
está registrado en el catálogo como `preview_impresion`. Esta vista es solo
la demo que lo muestra con reportes de ejemplo (datos reales si existen).

Uso del componente desde cualquier vista del sistema:
    from src.components.preview_impresion import previsualizar_html

    previsualizar_html(html, titulo="Recibo de Orden de Compra", parent=self)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from src.components.preview_impresion import PreviewImpresion


def _nombre_empresa() -> str:
    try:
        from src.models.empresa_model import EmpresaModel
        return EmpresaModel().nombre_empresa()
    except Exception:
        return "SIAC ERP"


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


def _oc_receipt_mint_html(datos: dict, detalle: list[dict]) -> str:
    """Recibo de OC con diseño 'ondas menta/salvia' (plantilla de la demo).

    Cabecera y pie con ondas superpuestas (curvas S) a todo lo ancho: menta
    pálido #D4EDEA de fondo y salvia #A9C5C1 al frente, en hoja carta vertical.
    Fondo #f0f0f0, tipografía sans-serif; los insumos quedan justificados a la
    izquierda y los precios alineados a la derecha. El pie queda anclado al
    fondo de la hoja y la tabla de items ocupa todo el ancho útil.
    """
    from datetime import datetime

    from src.utils.export_utils import (
        _esc, _fmt_fecha, _oc_columnas_tallas, _oc_totales)

    solo_remision = bool(datos.get("solo_remision"))
    titulo = "REMI-SIÓN - ORDEN DE COMPRA" if solo_remision else "RECIBO DE COMPRA"
    subtotal, iva, total = _oc_totales(detalle, solo_remision)
    columnas = _oc_columnas_tallas(detalle)

    estatus = str(datos.get("estatus", "") or "").replace("_", " ").capitalize()
    proveedor = datos.get("proveedor_nombre") or "Compra a inventario"
    telefono = datos.get("proveedor_telefono") or ""
    email = datos.get("proveedor_email") or ""
    rfc = datos.get("proveedor_rfc") or ""
    direccion = datos.get("proveedor_direccion") or ""

    th_tallas = "".join(
        f"<th>{_esc('#')}{_esc(c['talla'])}</th>" for c in columnas)

    rows = ""
    for d in detalle:
        por_talla = {int(t["talla_id"]): int(t.get("pares", 0) or 0)
                     for t in d.get("tallas", [])}
        celdas = "".join(
            f"<td>{por_talla.get(int(c['talla_id']), 0) or ''}</td>"
            for c in columnas)
        cant = int(d.get("cantidad", 0) or 0)
        precio = float(d.get("precio_unitario", 0) or 0)
        sub = cant * precio
        rows += f"""<tr>
            <td style='text-align:left'>{_esc(d.get('insumo_nombre', ''))}</td>
            {celdas}
            <td>{cant}</td>
            <td style='text-align:right'>${precio:,.2f}</td>
            <td style='text-align:right;font-weight:600'>${sub:,.2f}</td>
        </tr>"""

    filas_iva = ""
    if not solo_remision:
        filas_iva = (
            f"<tr><td>IVA (16%)</td><td style='text-align:right'>${iva:,.2f}</td></tr>")

    lineas_proveedor = [l for l in [
        _esc(proveedor),
        (f"Tel: {_esc(telefono)}" if telefono else ""),
        (f"Email: {_esc(email)}" if email else ""),
        (f"RFC: {_esc(rfc)}" if rfc else ""),
        (f"Dirección: {_esc(direccion)}" if direccion else ""),
    ] if l]
    vendido_html = "".join(
        f"<div style='{'font-size:15px;font-weight:700;color:#2f4f3a' if i == 0 else 'color:#5b6b60;font-size:12px'}'>"
        f"{l}</div>" for i, l in enumerate(lineas_proveedor))

    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html><head><meta charset='utf-8'/><style>
@page {{ margin: 0; }}
html, body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #374151;
              margin: 0; padding: 0; background: #f0f0f0;
              height: 100%; }}
.hoja {{ width: 100%; max-width: 820px; margin: 0 auto;
        display: flex; flex-direction: column;
        min-height: 100%; box-sizing: border-box; }}
.cabecera {{ background: #D4EDEA; padding: 24px 30px 18px 30px; }}
.cabecera table {{ width: 100%; border-collapse: collapse; }}
.cabecera td {{ vertical-align: middle; }}
.marca {{ font-size: 26px; font-weight: 800; color: #2f4f3a; letter-spacing: 2px; }}
.titulo {{ font-size: 17px; font-weight: 700; color: #2f4f3a; }}
.folio {{ font-size: 15px; font-weight: 700; color: #2f4f3a; }}
.sec {{ font-size: 10px; color: #5b6b60; }}
.bloque {{ background: #ffffff; border-radius: 10px; padding: 12px 16px;
          margin: 12px 26px 0 26px; box-shadow: 0 1px 4px rgba(0,0,0,.06);
          border-left: 4px solid #A9C5C1; }}
.lbl {{ font-weight: 700; color: #5b6b60; font-size: 11px; text-transform: uppercase;
       letter-spacing: 1px; margin-bottom: 4px; }}
table.items {{ width: calc(100% - 52px); margin: 16px 26px 0 26px;
              border-collapse: collapse; table-layout: fixed; }}
table.items th {{ background: linear-gradient(135deg, #A9C5C1 0%, #8FB5B1 100%);
                 color: #ffffff; padding: 8px 10px; font-size: 10px; text-align: center;
                 border: 1px solid #8FB5B1; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }}
table.items th:first-child {{ text-align: left; width: 34%; }}
table.items td {{ border: 1px solid #e4e7e2; padding: 7px 10px; font-size: 11px;
                 text-align: center; background: #ffffff; overflow: hidden; }}
table.items td:first-child {{ text-align: left; }}
table.items tr:nth-child(even) td {{ background: #f7faf6; }}
.resumen {{ margin: 16px 26px 0 26px; width: 260px; margin-left: auto;
           border-collapse: collapse; }}
.resumen td {{ padding: 5px 12px; font-size: 12px; border: 1px solid #e4e7e2;
              background: #ffffff; }}
.resumen .val {{ text-align: right; font-weight: 700; }}
.resumen .fila-total td {{ background: linear-gradient(135deg, #A9C5C1 0%, #8FB5B1 100%);
                          color: #ffffff; font-size: 15px; font-weight: 800; }}
.pie-ancla {{ margin-top: auto; padding-top: 30px; }}
</style></head><body>
<div class='hoja'>

  <!-- Cabecera: ondas superpuestas (menta de fondo, salvia al frente) -->
  <div class='cabecera'>
  <table><tr>
  <td style='width:32%'>
    <div class='marca'>{_nombre_empresa().upper()}</div>
    <div class='sec'>SIAC ERP · Sistema Integral de Administración y Control</div>
  </td>
  <td style='width:36%;text-align:center'><span class='titulo'>{titulo}</span></td>
  <td style='width:32%;text-align:right'>
    <div>NO. <span class='folio'>{_esc(datos.get('folio', ''))}</span></div>
    <div>FECHA: <b>{_fmt_fecha(datos.get('fecha_emision', ''))}</b></div>
    <div class='sec'>Estatus: {_esc(estatus)}</div>
  </td>
  </tr></table>
  </div>
  <svg viewBox='0 0 1200 110' preserveAspectRatio='none'
       style='display:block;width:100%;height:110px;margin-top:-44px;position:relative;z-index:1'>
    <!-- Capa de fondo: menta pálido (#D4EDEA) -->
    <path d='M0,40 C160,82 320,8 480,40 C640,82 800,8 960,40 C1120,82 1160,28 1200,50 L1200,110 L0,110 Z'
          fill='#D4EDEA'/>
    <!-- Capa de frente: salvia (#A9C5C1), curvas S superpuestas -->
    <path d='M0,64 C160,106 320,32 480,64 C640,106 800,32 960,64 C1120,106 1160,52 1200,74 L1200,110 L0,110 Z'
          fill='#A9C5C1'/>
  </svg>

  <div class='bloque'>
    <div class='lbl'>Vendido a:</div>
    {vendido_html}
  </div>

  <table class='items'>
  <tr>
    <th style='min-width:170px'>NOMBRE</th>
    {th_tallas}
    <th>TOTAL PARES</th>
    <th>VALOR UNITARIO</th>
    <th>TOTAL</th>
  </tr>
  {rows}
  </table>

  <table class='resumen'>
  <tr><td>Subtotal</td><td class='val'>${subtotal:,.2f}</td></tr>
  {filas_iva}
  <tr class='fila-total'><td>TOTAL</td><td>${total:,.2f}</td></tr>
  </table>

  <!-- Pie: ondas superpuestas, anclado al fondo de la hoja -->
  <div class='pie-ancla'>
  <svg viewBox='0 0 1200 90' preserveAspectRatio='none'
       style='display:block;width:100%;height:90px'>
    <!-- Capa de fondo: menta pálido (#D4EDEA) -->
    <path d='M0,28 C160,-10 320,56 480,28 C640,-10 800,56 960,28 C1120,-10 1160,16 1200,6 L1200,90 L0,90 Z'
          fill='#D4EDEA'/>
    <!-- Capa de frente: salvia (#A9C5C1), curvas S superpuestas -->
    <path d='M0,52 C160,14 320,80 480,52 C640,14 800,80 960,52 C1120,14 1160,40 1200,30 L1200,90 L0,90 Z'
          fill='#A9C5C1'/>
  </svg>
  <div style='background:linear-gradient(135deg, #A9C5C1 0%, #D4EDEA 100%);
              padding:6px 28px 22px 28px;'>
    <div style='font-size:14px;font-weight:700;color:#2f4f3a'>Gracias por su compra.</div>
    <div style='font-size:16px;font-weight:800;color:#2f4f3a;letter-spacing:2px;margin-top:2px'>{_nombre_empresa().upper()}</div>
    <div style='font-size:9px;color:#4a6b52;margin-top:4px'>Generado por {_nombre_empresa()} el {ahora}</div>
  </div>
  </div>

</div>
</body></html>"""


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
