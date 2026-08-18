"""API de Supabase para la cola de impresión (escritorio).

Consulta las solicitudes de impresión que envía la app móvil a la tabla
`impresiones_etiqueta` de Supabase. El móvil inserta filas con estatus
'pendiente'; el escritorio las lee, las imprime y las marca como 'impresa'
(con lo que salen de la cola pero quedan en el histórico local).

Credenciales (sin tocar config.ini):
- Variables de entorno SUPABASE_URL y SUPABASE_ANON_KEY, o
- Sección [supabase] de config.ini (url / anon_key).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from src.database.db_manager import DatabaseManager

TABLA = "impresiones_etiqueta"
ESTATUS_PENDIENTE = "pendiente"
ESTATUS_IMPRESA = "impresa"


def _configuracion() -> tuple[str, str] | None:
    """Devuelve (url, anon_key) desde entorno o config.ini, o None."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if url and anon_key:
        return url, anon_key

    try:
        cfg = DatabaseManager().config
        url = cfg.get("supabase", "url", fallback="").strip()
        anon_key = cfg.get("supabase", "anon_key", fallback="").strip()
    except Exception:
        return None
    if url and anon_key:
        return url, anon_key
    return None


def configurado() -> bool:
    return _configuracion() is not None


def _request(method: str, ruta: str, body: dict | None = None) -> Any:
    """Ejecuta una petición REST a Supabase y devuelve la respuesta JSON."""
    config = _configuracion()
    if config is None:
        raise RuntimeError(
            "Supabase no configurado. Define SUPABASE_URL y SUPABASE_ANON_KEY "
            "(variables de entorno) o la sección [supabase] en config.ini.")
    base_url, anon_key = config
    base = base_url.rstrip("/") + "/rest/v1"
    url = f"{base}/{ruta}"
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase HTTP {e.code}: {detalle}") from e


def listar_pendientes() -> list[dict]:
    """Solicitudes de la cola: estatus = pendiente, ordenadas por creación."""
    filtro = f"{TABLA}?select=*&estatus=eq.{ESTATUS_PENDIENTE}&order=creada_en.asc"
    resultado = _request("GET", filtro)
    return resultado if isinstance(resultado, list) else []


def marcar_impresa(supabase_id: Any) -> None:
    """Marca la solicitud como impresa para que salga de la cola."""
    if supabase_id is None:
        return
    ident = urllib.parse.quote(str(supabase_id))
    _request("PATCH", f"{TABLA}?id=eq.{ident}", {"estatus": ESTATUS_IMPRESA})
