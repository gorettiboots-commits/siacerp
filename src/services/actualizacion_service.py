"""Servicio de auto-actualización de SIAC ERP.

Consulta un manifiesto remoto (version.json) para detectar nuevas
versiones y notificar al usuario. Incluye verificacion de firma
digital antes de ejecutar cualquier instalador descargado.

Reglas aplicadas: D-21 a D-25 (AGENTS.md sección 6.6).
"""

import hashlib
import json
import os
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from src.utils.updater_utils import (
    calcular_hash_archivo,
    descargar_archivo,
    ejecutar_instalador,
    limpiar_archivos_temporales,
    obtener_ruta_temporal,
    verificar_firma_con_timestamp,
    verificar_hash_archivo,
)


# URL del manifiesto de versiones (configurable)
MANIFIESTO_URL = (
    "https://raw.githubusercontent.com/gorettiboots-commits/siacerp/"
    "main/version.json"
)


class ActualizacionService:
    """Servicio de detección y descarga de actualizaciones."""

    def __init__(self, version_actual: str) -> None:
        self.version_actual = version_actual
        self._ultima_verificacion: Optional[dict] = None
        self._emisor_firma: Optional[str] = None

    def set_emisor_firma(self, emisor: str) -> None:
        """Configura el emisor esperado del certificado de firma.

        Args:
            emisor: Nombre del emisor del certificado.
        """
        self._emisor_firma = emisor

    def verificar(self) -> dict:
        """Verifica si hay una nueva versión disponible.

        Returns:
            dict con keys: hay_actualizacion, version_remota,
            url_descarga, mensaje, obligatorio, hash_sha256,
            url_instalador, firma_requerida
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
                "url_instalador": data.get("url_instalador", ""),
                "url_changelog": data.get("url_changelog", ""),
                "mensaje": data.get("mensaje", ""),
                "obligatorio": data.get("obligatorio", False),
                "hash_sha256": data.get("hash_sha256", ""),
                "firma_requerida": data.get("firma_requerida", True),
                "fecha": data.get("fecha", ""),
            }

            return self._ultima_verificacion

        except Exception:
            # Sin red o error → silenciosamente continuar
            return {
                "hay_actualizacion": False,
                "version_remota": self.version_actual,
                "url_descarga": "",
                "url_instalador": "",
                "mensaje": "",
                "obligatorio": False,
                "hash_sha256": "",
                "firma_requerida": True,
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

    def descargar_e_instalar(
        self,
        url_instalador: str,
        hash_esperado: Optional[str] = None,
        verificar_firma: bool = True,
        callback_progreso: Optional[Callable[[int, int], None]] = None,
        callback_completo: Optional[Callable[[bool, str], None]] = None,
    ) -> None:
        """Descarga y verifica un instalador en un hilo separado.

        El proceso es:
        1. Descargar el archivo .exe
        2. Verificar SHA-256 (si se proporciona hash)
        3. Verificar firma digital Authenticode
        4. Ejecutar el instalador

        Args:
            url_instalador: URL del archivo .exe a descargar.
            hash_esperado: Hash SHA-256 esperado (opcional).
            verificar_firma: Si True, verifica firma digital antes de ejecutar.
            callback_progreso: Callback(bytes_descargados, total_bytes).
            callback_completo: Callback(exito, mensaje) al finalizar.
        """
        def _descargar():
            # Crear directorio temporal
            nombre_archivo = url_instalador.split("/")[-1]
            if not nombre_archivo.endswith(".exe"):
                nombre_archivo = f"SIAC_ERP_{self.version_actual}.exe"
            ruta_temp = obtener_ruta_temporal(nombre_archivo)
            os.makedirs(os.path.dirname(ruta_temp), exist_ok=True)

            try:
                # 1) Descargar
                if callback_progreso:
                    callback_progreso(0, -1)  # Indicar inicio
                ok, msg = descargar_archivo(
                    url_instalador, ruta_temp, callback_progreso
                )
                if not ok:
                    if callback_completo:
                        callback_completo(False, f"Error de descarga: {msg}")
                    return

                # 2) Verificar hash SHA-256
                if hash_esperado:
                    ok, msg = verificar_hash_archivo(ruta_temp, hash_esperado)
                    if not ok:
                        limpiar_archivos_temporales()
                        if callback_completo:
                            callback_completo(False, f"Hash incorrecto: {msg}")
                        return

                # 3) Verificar firma digital
                if verificar_firma:
                    ok, msg = verificar_firma_con_timestamp(
                        ruta_temp, self._emisor_firma
                    )
                    if not ok:
                        limpiar_archivos_temporales()
                        if callback_completo:
                            callback_completo(
                                False,
                                f"Firma digital invalida: {msg}\n"
                                "El instalador podria estar manipulado."
                            )
                        return

                # 4) Ejecutar instalador
                ok, msg = ejecutar_instalador(ruta_temp)
                if callback_completo:
                    callback_completo(ok, msg)

            except Exception as e:
                limpiar_archivos_temporales()
                if callback_completo:
                    callback_completo(False, f"Error inesperado: {str(e)}")

        hilo = threading.Thread(target=_descargar, daemon=True)
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
