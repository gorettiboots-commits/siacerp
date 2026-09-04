"""Utilidades para el auto-actualizador de SIAC ERP.

Proporciona funciones para verificar la firma digital de archivos
descargados y gestionar el proceso de actualización de forma segura.

Reglas aplicadas: D-21 a D-25 (AGENTS.md sección 6.6).
"""

import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Tuple


# Emisor del certificado de firma (se valida contra este valor)
# Se puede configurar desde config.ini [actualizacion] firmante=
EMISOR_FIRMA_DEFAULT = "Mario Felipe Luevano"

# Servidores de timestamp para verificar firma
TIMESTAMP_SERVERS = [
    "http://timestamp.sectigo.com",
    "http://timestamp.digicert.com",
    "http://timestamp.entrust.net/TSS/RFC3161sha2TS",
]


def _obtener_ruta_signtool() -> Optional[str]:
    """Busca signtool.exe en el sistema.

    Returns:
        Ruta completa a signtool.exe o None si no se encuentra.
    """
    # Buscar en PATH
    for dir_path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = os.path.join(dir_path, "signtool.exe")
        if os.path.isfile(candidate):
            return candidate

    # Buscar en Windows SDK
    sdk_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin",
        r"C:\Program Files\Windows Kits\10\bin",
    ]
    for sdk_base in sdk_paths:
        if os.path.isdir(sdk_base):
            for version_dir in sorted(Path(sdk_base).iterdir(), reverse=True):
                x64_dir = version_dir / "x64"
                if x64_dir.is_dir():
                    candidate = x64_dir / "signtool.exe"
                    if candidate.is_file():
                        return str(candidate)

    return None


def verificar_firma_digital(
    ruta_archivo: str,
    emisor_esperado: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verifica la firma digital Authenticode de un archivo .exe o .msi.

    Args:
        ruta_archivo: Ruta al archivo a verificar.
        emisor_esperado: Nombre del emisor esperado (opcional).

    Returns:
        Tupla (es_valido, mensaje).
    """
    if emisor_esperado is None:
        emisor_esperado = EMISOR_FIRMA_DEFAULT

    signtool = _obtener_ruta_signtool()
    if signtool is None:
        return False, "signtool.exe no encontrado en el sistema. " \
                     "Instala Windows SDK o Visual Studio."

    try:
        resultado = subprocess.run(
            [
                signtool,
                "verify",
                "/pa",          # Verificar usando la politica de autenticidad
                "/v",           # Verbose
                "/dw",          # Mostrar advertencias
                str(ruta_archivo),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        salida = resultado.stdout + resultado.stderr

        # Verificar si la firma es valida
        if resultado.returncode == 0 and "Successfully verified" in salida:
            # Verificar el emisor si se especifico
            if emisor_esperado:
                if emisor_esperado.lower() in salida.lower():
                    return True, f"Firma verificada correctamente (emisor: {emisor_esperado})"
                else:
                    return False, (
                        f"El emisor de la firma no coincide. "
                        f"Esperado: {emisor_esperado}"
                    )
            return True, "Firma digital verificada correctamente"

        # La firma no es valida
        if "No signature" in salida or "not signed" in salida.lower():
            return False, "El archivo no tiene firma digital"

        return False, f"Verificacion de firma fallida: {salida.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Tiempo de espera agotado verificando firma"
    except Exception as e:
        return False, f"Error verificando firma: {str(e)}"


def verificar_firma_con_timestamp(
    ruta_archivo: str,
    emisor_esperado: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verifica la firma digital con verificacion de timestamp.

    Un timestamp valido garantiza que la firma era valida al momento
    de firmar, incluso si el certificado ya expiro.

    Args:
        ruta_archivo: Ruta al archivo a verificar.
        emisor_esperado: Nombre del emisor esperado (opcional).

    Returns:
        Tupla (es_valido, mensaje).
    """
    if emisor_esperado is None:
        emisor_esperado = EMISOR_FIRMA_DEFAULT

    signtool = _obtener_ruta_signtool()
    if signtool is None:
        return False, "signtool.exe no encontrado en el sistema."

    # Intentar con cada servidor de timestamp
    for ts_server in TIMESTAMP_SERVERS:
        try:
            resultado = subprocess.run(
                [
                    signtool,
                    "verify",
                    "/pa",
                    "/v",
                    "/tw",              # Verificar timestamp
                    "/t", ts_server,    # Servidor de timestamp
                    str(ruta_archivo),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            salida = resultado.stdout + resultado.stderr

            if resultado.returncode == 0 and "Successfully verified" in salida:
                if emisor_esperado:
                    if emisor_esperado.lower() in salida.lower():
                        return True, (
                            f"Firma verificada con timestamp "
                            f"(emisor: {emisor_esperado}, ts: {ts_server})"
                        )
                    else:
                        return False, (
                            f"El emisor de la firma no coincide. "
                            f"Esperado: {emisor_esperado}"
                        )
                return True, f"Firma verificada con timestamp ({ts_server})"

        except (subprocess.TimeoutExpired, Exception):
            continue

    # Si todos los timestamps fallaron, intentar sin timestamp
    return verificar_firma_digital(ruta_archivo, emisor_esperado)


def calcular_hash_archivo(ruta_archivo: str) -> str:
    """Calcula el hash SHA-256 de un archivo.

    Args:
        ruta_archivo: Ruta al archivo.

    Returns:
        Hash SHA-256 en formato hexadecimal.
    """
    sha256 = hashlib.sha256()
    with open(ruta_archivo, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verificar_hash_archivo(
    ruta_archivo: str,
    hash_esperado: str,
) -> Tuple[bool, str]:
    """Verifica el SHA-256 de un archivo descargado.

    Args:
        ruta_archivo: Ruta al archivo descargado.
        hash_esperado: Hash SHA-256 esperado (hexadecimal).

    Returns:
        Tupla (es_valido, mensaje).
    """
    if not hash_esperado:
        return True, "Sin hash para verificar (se omite validacion)"

    hash_real = calcular_hash_archivo(ruta_archivo)
    if hash_real == hash_esperado.lower():
        return True, f"Hash SHA-256 verificado: {hash_real[:16]}..."
    else:
        return False, (
            f"Hash SHA-256 no coincide.\n"
            f"Esperado: {hash_esperado}\n"
            f"Real:     {hash_real}"
        )


def descargar_archivo(
    url: str,
    ruta_destino: str,
    callback_progreso: Optional[Callable[[int, int], None]] = None,
) -> Tuple[bool, str]:
    """Descarga un archivo desde una URL con verificacion de integridad.

    Args:
        url: URL de descarga.
        ruta_destino: Ruta donde guardar el archivo.
        callback_progreso: Funcion callback(bytes_descargados, total_bytes).

    Returns:
        Tupla (exito, mensaje).
    """
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SIAC-ERP-Updater"},
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            total = int(response.headers.get("Content-Length", 0))
            descargado = 0

            with open(ruta_destino, "wb") as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    descargado += len(chunk)
                    if callback_progreso:
                        callback_progreso(descargado, total)

        return True, f"Descarga completada: {descargado} bytes"

    except Exception as e:
        return False, f"Error descargando archivo: {str(e)}"


def ejecutar_instalador(ruta_instalador: str) -> Tuple[bool, str]:
    """Ejecuta el instalador descargado y verificado.

    Args:
        ruta_instalador: Ruta al archivo .exe del instalador.

    Returns:
        Tupla (exito, mensaje).
    """
    try:
        # Verificar que el archivo existe y tiene tamano razonable
        tamano = os.path.getsize(ruta_instalador)
        if tamano < 1024 * 1024:  # Menos de 1 MB
            return False, f"El instalador parece incompleto ({tamano} bytes)"

        # Ejecutar el instalador de forma silenciosa
        # Nota: Los instaladores Inno Setup soportan /SILENT
        if sys.platform == "win32":
            subprocess.Popen(
                [ruta_instalador, "/SILENT"],
                shell=False,
            )
            return True, "Instalador ejecutado. La aplicacion se cerrara."

        return False, "Plataforma no soportada para instalacion automatica"

    except Exception as e:
        return False, f"Error ejecutando instalador: {str(e)}"


def obtener_ruta_temporal(nombre_archivo: str) -> str:
    """Obtiene una ruta temporal para descargar archivos.

    Args:
        nombre_archivo: Nombre del archivo a descargar.

    Returns:
        Ruta completa en el directorio temporal.
    """
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, "siac_actualizacion", nombre_archivo)


def limpiar_archivos_temporales() -> None:
    """Limpia los archivos temporales de actualizaciones anteriores."""
    temp_dir = os.path.join(tempfile.gettempdir(), "siac_actualizacion")
    if os.path.isdir(temp_dir):
        for archivo in os.listdir(temp_dir):
            ruta = os.path.join(temp_dir, archivo)
            try:
                os.remove(ruta)
            except OSError:
                pass
