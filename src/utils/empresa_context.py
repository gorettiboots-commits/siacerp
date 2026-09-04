"""Contexto de empresa actual para filtrado multi-tenant en el escritorio.

Permite que los modelos obtengan el empresa_id del usuario logueado
sin importar vistas ni controladores.
"""
from typing import Optional

_empresa_id_actual: Optional[str] = None


def establecer_empresa_id(empresa_id: Optional[str]) -> None:
    """Establece el empresa_id del usuario logueado."""
    global _empresa_id_actual
    _empresa_id_actual = empresa_id


def obtener_empresa_id() -> Optional[str]:
    """Obtiene el empresa_id del usuario actual.

    Returns:
        UUID de la empresa o None (super_admin ve todo).
    """
    return _empresa_id_actual


def donde_empresa(tabla_alias: str = '') -> str:
    """Genera fragmento WHERE para filtrar por empresa_id.

    Args:
        tabla_alias: prefijo de tabla (ej: 'oc' para 'oc.empresa_id').
                     Vacio si la tabla no tiene alias.

    Returns:
        Fragmento SQL como ' AND X.empresa_id = ?' o '' si no hay empresa.
    """
    emp = _empresa_id_actual
    if not emp:
        return ''
    col = f'{tabla_alias}.empresa_id' if tabla_alias else 'empresa_id'
    return f' AND {col} = ?'


def parametros_empresa() -> list[str]:
    """Retorna los parametros del empresa_id actual para queries parameterizadas."""
    emp = _empresa_id_actual
    if not emp:
        return []
    return [emp]
