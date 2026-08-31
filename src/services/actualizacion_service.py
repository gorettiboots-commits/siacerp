"""Servicio de auto-actualización de SIAC ERP.

Consulta un manifiesto remoto (version.json) para detectar nuevas
versiones y notificar al usuario. No descarga ni instala automáticamente
sin confirmación del usuario.

Reglas aplicadas: D-21 a D-25 (AGENTS.md sección 6.6).
"""

import hashlib
import json
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional


# URL del manifiesto de versiones (configurable)
MANIFIESTO_URL = (
    "https://raw.githubusercontent.com/gorettiboots-commits/siacerp/"
    "main/version.json"
)


class ActualizacionService:
    """Servicio de detección de actualizaciones."""

    def __init__(self, version_actual: str) -> None:
        self.version_actual = version_actual
        self._ultima_verificacion: Optional[dict] = None

    def verificar(self) -> dict:
        """Verifica si hay una nueva versión disponible.

        Returns:
            dict con keys: hay_actualizacion, version_remota,
            url_descarga, mensaje, obligatorio, hash_sha256
        """
        try:
            req = urllib.request.Request(
                MANIFIESTO_URL,
                headers={"User-Agent": f"SIAC-ERP/{self.version_actual}"}
            )
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode())

            version_remota = data.get("version", "0.0.0")
            hay_actualizacion = self._comparar_versiones(
                self.version_actual, version_remota
            )

            self._ultima_verificacion = {
                "hay_actualizacion": hay_actualizacion,
                "version_remota": version_remota,
                "url_descarga": data.get("url_descarga", ""),
                "url_changelog": data.get("url_changelog", ""),
                "mensaje": data.get("mensaje", ""),
                "obligatorio": data.get("obligatorio", False),
                "hash_sha256": data.get("hash_sha256", ""),
                "fecha": data.get("fecha", ""),
            }

            return self._ultima_verificacion

        except Exception:
            # Sin red o error → silenciosamente continuar
            return {
                "hay_actualizacion": False,
                "version_remota": self.version_actual,
                "url_descarga": "",
                "mensaje": "",
                "obligatorio": False,
                "hash_sha256": "",
            }

    def verificar_en_background(
        self,
        callback: Optional[Callable[[dict], None]] = None,
    ) -> None:
        """Verifica actualizaciones en un hilo separado (no bloquea UI)."""
        def _verificar():
            resultado = self.verificar()
            if callback and resultado.get("hay_actualizacion"):
                callback(resultado)

        hilo = threading.Thread(target=_verificar, daemon=True)
        hilo.start()

    @staticmethod
    def _comparar_versiones(actual: str, remota: str) -> bool:
        """Compara versiones CalVersioning (YYYY.M.DD).

        Returns True si remota es mayor que actual.
        """
        try:
            partes_actual = [int(x) for x in actual.split(".")]
            partes_remota = [int(x) for x in remota.split(".")]
            return partes_remota > partes_actual
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def verificar_hash_archivo(
        ruta_archivo: str, hash_esperado: str
    ) -> bool:
        """Verifica el SHA-256 de un archivo descargado."""
        sha256 = hashlib.sha256()
        with open(ruta_archivo, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == hash_esperado

    def obtener_mensaje_actualizacion(self) -> str:
        """Genera el mensaje para el usuario."""
        if not self._ultima_verificacion:
            return ""

        v = self._ultima_verificacion
        if not v.get("hay_actualizacion"):
            return ""

        mensaje = (
            f"Nueva versión disponible: {v['version_remota']}\\n\\n"
            f"Versión actual: {self.version_actual}\\n"
        )

        if v.get("mensaje"):
            mensaje += f"\\nCambios: {v['mensaje']}\\n"

        if v.get("obligatorio"):
            mensaje += (
                "\\n⚠️ Esta actualización es obligatoria. "
                "La aplicación se cerrará después de 5 minutos."
            )
        else:
            mensaje += "\\n¿Desea descargar e instalar la actualización?"

        return mensaje
