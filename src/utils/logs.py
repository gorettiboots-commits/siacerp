"""Registro técnico de acciones del sistema (auditoría de datos modificados)."""

import json
import platform
import socket
from datetime import datetime
from typing import Any, Optional

from src.database.db_manager import DatabaseManager


_usuario_actual: Optional[dict] = None


def set_usuario_actual(usuario: Optional[dict]) -> None:
    global _usuario_actual
    _usuario_actual = usuario


def get_usuario_actual() -> Optional[dict]:
    return _usuario_actual


def _sanitizar(valor: Any, _depth: int = 0) -> Any:
    """Convierte valores no serializables a representaciones seguras."""
    if _depth > 6:
        return "..."
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if isinstance(valor, (bytes, bytearray)):
        return f"<bytes {len(valor)}B>"
    if isinstance(valor, dict):
        return {str(k): _sanitizar(v, _depth + 1) for k, v in valor.items()}
    if isinstance(valor, (list, tuple, set)):
        return [_sanitizar(v, _depth + 1) for v in valor]
    return str(valor)


def _metadata() -> dict:
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "0.0.0.0"
    return {
        "hostname": hostname,
        "ip": ip,
        "plataforma": platform.platform(),
        "python": platform.python_version(),
        "usuario_os": getattr(platform, "uname", lambda: ("?",))().node,
    }


def registrar_log(
    modulo: str,
    accion: str,
    entidad: str = "",
    entidad_id: Any = None,
    nivel: str = "info",
    detalle: str = "",
    datos: Optional[dict] = None,
) -> int:
    """Registra una acción que modifica datos, con su data y metadata."""
    usuario = get_usuario_actual()
    payload = {
        "usuario_id": (usuario or {}).get("id"),
        "usuario": (usuario or {}).get("username", ""),
        "modulo": modulo,
        "accion": accion,
        "entidad": entidad,
        "entidad_id": entidad_id if entidad_id is not None else None,
        "nivel": nivel,
        "detalle": detalle,
        "datos": json.dumps(_sanitizar(datos or {}), ensure_ascii=False),
        "metadata": json.dumps(_metadata(), ensure_ascii=False),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        db = DatabaseManager()
        cursor = db.execute(
            """INSERT INTO logs_sistema
               (fecha, usuario_id, usuario, modulo, accion, entidad, entidad_id,
                nivel, detalle, datos, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                payload["fecha"],
                payload["usuario_id"],
                payload["usuario"],
                payload["modulo"],
                payload["accion"],
                payload["entidad"],
                payload["entidad_id"],
                payload["nivel"],
                payload["detalle"],
                payload["datos"],
                payload["metadata"],
            ),
        )
        return int(cursor.lastrowid)
    except Exception as e:
        print(f"Error al registrar log: {e}")
        return 0


def limpiar_logs() -> int:
    db = DatabaseManager()
    cursor = db.execute("DELETE FROM logs_sistema")
    return cursor.rowcount or 0
