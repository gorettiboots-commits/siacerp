"""Stack de componentes propios del sistema (catálogo reutilizable).

Ciclo de vida:
- Un control se prototipa primero en el Sandbox (`src/views/sandbox_view.py`).
- Cuando el usuario aprueba el control, se desarrolla de forma reutilizable
  aquí (o se registra si ya vive en `src/utils/`) y se agrega al catálogo.
- El catálogo permite listar los componentes disponibles y usarlos en tareas.

Uso:
    from src.components import listar_componentes, obtener_componente

    listar_componentes()              # -> [{"nombre", "descripcion"}, ...]
    obtener_componente("odoo_list")   # -> clase registrada
"""

from __future__ import annotations

_COMPONENTES: dict[str, dict] = {}


def registrar_componente(nombre: str, clase: type, descripcion: str) -> None:
    """Registra un componente reutilizable en el catálogo."""
    _COMPONENTES[nombre] = {"clase": clase, "descripcion": descripcion}


def listar_componentes() -> list[dict]:
    """Devuelve la lista de componentes disponibles (nombre + descripción)."""
    return [
        {"nombre": nombre, "descripcion": datos["descripcion"]}
        for nombre, datos in sorted(_COMPONENTES.items())
    ]


def obtener_componente(nombre: str) -> type:
    """Devuelve la clase registrada o lanza `KeyError`."""
    if nombre not in _COMPONENTES:
        raise KeyError(f"Componente no registrado: {nombre}")
    return _COMPONENTES[nombre]["clase"]


# ---------------------------------------------------------------------------
# Registro de componentes propios ya aprobados.
# ---------------------------------------------------------------------------

from src.utils.odoo_list import OdooListView  # noqa: E402

registrar_componente(
    "odoo_list",
    OdooListView,
    "Vista de listado con alternador tabla/lista/iconos (tarjetas), columnas "
    "ordenables y selección/doble clic configurable.",
)

from src.components.tallas_matrix import MatrizTallasDialog, MatrizTallasWidget  # noqa: E402

registrar_componente(
    "matriz_tallas",
    MatrizTallasDialog,
    "Matriz de tallas por bloques: encabezado negro/texto blanco, filas de "
    "captura con navegación Enter/Tab y celdas sin flechas numéricas.",
)

registrar_componente(
    "matriz_tallas_widget",
    MatrizTallasWidget,
    "Control embebido de matriz de tallas por bloques (sin diálogo) con "
    "captura por celdas, navegación Enter/Tab y señales de cambio.",
)

from src.components.complex_grid import ComplexGrid  # noqa: E402

registrar_componente(
    "complexGrid",
    ComplexGrid,
    "Tabla de datos con búsqueda, filtros, agrupación, vistas "
    "lista/iconos/tabla, acciones por registro y exportación "
    "Excel/PDF/Imprimir.",
)

from src.components.preview_impresion import PreviewImpresion  # noqa: E402

registrar_componente(
    "preview_impresion",
    PreviewImpresion,
    "Vista previa de impresión WYSIWYG para reportes HTML: hoja simulada con "
    "proporción real de página, zoom, tamaño de página, orientación, "
    "impresión y exportación a PDF por la misma vía que los reportes.",
)

from src.components.editor_etiqueta import LabelCanvas, PanelPropiedadesCampo  # noqa: E402

registrar_componente(
    "label_canvas",
    LabelCanvas,
    "Lienzo interactivo de diseño de etiqueta: render en tiempo real y "
    "arrastre (drag & drop) de elementos con el mouse.",
)

registrar_componente(
    "label_campo_props",
    PanelPropiedadesCampo,
    "Panel de propiedades del elemento de etiqueta: coordenadas, dimensiones, "
    "borde, tipografía, alineación y visibilidad.",
)

from src.components.editor_etiqueta_widget import (  # noqa: E402
    DialogoEditorEtiqueta, EditorEtiquetaWidget,
)

registrar_componente(
    "editor_etiqueta",
    EditorEtiquetaWidget,
    "Creador/editor de etiquetas estilo Windows Forms: lienzo interactivo, "
    "tamaño de lienzo en mm, controles de campos (texto/dato/duplicar/quitar) "
    "y guardado de diseños con nombre en la base de datos (etiqueta_config).",
)

registrar_componente(
    "editor_etiqueta_dialog",
    DialogoEditorEtiqueta,
    "Diálogo a pantalla completa con el editor de etiquetas aprobado; botón "
    "Cerrar para salir. Ideal para abrir desde los módulos sin que los datos "
    "se vean pequeños.",
)

from src.components.date_picker import DatePicker  # noqa: E402

registrar_componente(
    "date_picker",
    DatePicker,
    "Selector de fecha con calendario emergente: formato dd/MM/yyyy, "
    "conversión ISO para base de datos (fecha_bd / establecer_fecha_bd).",
)

from src.components.campo_historico import CampoHistorico  # noqa: E402

registrar_componente(
    "campo_historico",
    CampoHistorico,
    "Campo de texto con histórico de capturas: al enfocar/hacer clic despliega "
    "el histórico del campo y autocompleta mientras se escribe; registra la "
    "captura al salir del campo. Incluye InstaladorHistorico para aplicarlo a "
    "todo el sistema.",
)

from src.components.notificacion_flotante import (  # noqa: E402
    NotificacionesFlotantes, notificar_flotante,
)

registrar_componente(
    "notificacion_flotante",
    NotificacionesFlotantes,
    "Notificaciones flotantes (toasts): tarjetas que se apilan en una esquina "
    "de la ventana activa u host fijo, con tipos info/success/warning/error, "
    "cierre automático o manual, animación y callback al hacer clic. Incluye "
    "la función singleton notificar_flotante para uso directo.",
)

from src.components.grid_hibrido import GridHibrido  # noqa: E402

registrar_componente(
    "grid_hibrido",
    GridHibrido,
    "Wrapper híbrido de ComplexGrid con toolbar de 2 filas: fila 1 (módulo) "
    "configurable con botones de acción del módulo y fila 2 (grid) con "
    "Buscar/Imprimir/Vista previa/Exportar; barra de estado inferior.",
)

from src.components.matriz_preview import MatrizPreviewWidget  # noqa: E402

registrar_componente(
    "matriz_preview",
    MatrizPreviewWidget,
    "Widget flotante de vista previa de la matriz de tallas al hacer hover "
    "sobre la columna de talla en ComplexGrid: soporte multi-bloque.",
)
