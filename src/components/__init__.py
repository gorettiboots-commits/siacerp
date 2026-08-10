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

from src.components.tallas_matrix import MatrizTallasDialog  # noqa: E402

registrar_componente(
    "matriz_tallas",
    MatrizTallasDialog,
    "Matriz de tallas por bloques: encabezado negro/texto blanco, filas de "
    "captura con navegación Enter/Tab y celdas sin flechas numéricas.",
)

from src.components.complex_grid import ComplexGrid  # noqa: E402

registrar_componente(
    "complexGrid",
    ComplexGrid,
    "Tabla de datos con búsqueda, filtros, agrupación, vistas "
    "lista/iconos/tabla, acciones por registro y exportación "
    "Excel/PDF/Imprimir.",
)
