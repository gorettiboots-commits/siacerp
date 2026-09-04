"""Hooks de sincronización para encolar cambios en sync_queue.

Uso en models:
    from src.utils.sync_hooks import sync_insert, sync_update, sync_delete

    # Después de un INSERT exitoso:
    sync_insert('insumos', nuevo_id, datos_dict)

    # Después de un UPDATE:
    sync_update('insumos', registro_id, datos_dict)

    # Después de un DELETE / soft delete:
    sync_delete('insumos', registro_id)

Si sync_queue no está disponible (BD antigua o sync deshabilitado),
los hooks fallan silenciosamente para no bloquear la operación local.
"""
from typing import Optional

_queue_instance = None


def _get_queue():
    """Obtiene la instancia de SyncQueueModel (lazy)."""
    global _queue_instance
    if _queue_instance is None:
        try:
            from src.models.sync_queue_model import SyncQueueModel
            _queue_instance = SyncQueueModel()
        except Exception:
            return None
    return _queue_instance


def sync_insert(tabla: str, registro_id: int, datos: dict) -> None:
    """Encola un INSERT para sincronización."""
    q = _get_queue()
    if q is None:
        return
    try:
        q.encolar_insert(tabla, registro_id, datos)
    except Exception:
        pass  # No bloquear la operación local
    sync_trigger()


def sync_update(tabla: str, registro_id: int, datos: dict) -> None:
    """Encola un UPDATE para sincronización."""
    q = _get_queue()
    if q is None:
        return
    try:
        q.encolar_update(tabla, registro_id, datos)
    except Exception:
        pass
    sync_trigger()


def sync_delete(tabla: str, registro_id: int) -> None:
    """Encola un DELETE (soft delete) para sincronización."""
    q = _get_queue()
    if q is None:
        return
    try:
        q.encolar_delete(tabla, registro_id)
    except Exception:
        pass
    sync_trigger()


def sync_trigger():
    """Trigger sincronización inmediata si hay red (fire-and-forget)."""
    try:
        from src.utils.sync_service import SyncService
        svc = SyncService()
        if svc.conectado and svc.hay_red():
            import threading
            threading.Thread(
                target=svc.sincronizar_si_hay_red,
                daemon=True
            ).start()
    except Exception:
        pass
