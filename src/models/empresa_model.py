"""Modelo de configuración de empresa.

Gestiona los datos de la empresa que usa el sistema: nombre, razón social,
logo (membrete) y ruta del video de splash. Todo se almacena como pares
clave-valor en la tabla ``configuracion_empresa``.
"""
from src.database.db_manager import DatabaseManager


class EmpresaModel:
    """Acceso a la configuración de empresa (key-value store)."""

    CLAVES = (
        'nombre_empresa', 'razon_social', 'logo', 'video_splash',
        'rfc', 'domicilio', 'telefono', 'email',
    )

    def __init__(self) -> None:
        self.db = DatabaseManager()

    # ------------------------------------------------------------------
    def obtener(self, clave: str) -> str:
        """Devuelve el valor de una clave de configuración."""
        fila = self.db.fetch_one(
            "SELECT valor FROM configuracion_empresa WHERE clave = ?",
            (clave,),
        )
        return fila["valor"] if fila else ""

    def obtener_todas(self) -> dict[str, str]:
        """Devuelve todas las claves como diccionario {clave: valor}."""
        filas = self.db.fetch_all(
            "SELECT clave, valor FROM configuracion_empresa"
        )
        return {f["clave"]: f["valor"] for f in filas}

    # ------------------------------------------------------------------
    def guardar(self, clave: str, valor: str) -> None:
        """Actualiza o inserta una clave de configuración."""
        self.db.execute(
            "INSERT INTO configuracion_empresa (clave, valor, updated_at) "
            "VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, "
            "updated_at = excluded.updated_at",
            (clave, valor),
        )

    def guardar_varias(self, datos: dict[str, str]) -> None:
        """Guarda múltiples claves de una vez."""
        for clave, valor in datos.items():
            self.guardar(clave, valor)

    # ------------------------------------------------------------------
    def obtener_logo_bytes(self) -> bytes | None:
        """Devuelve los bytes del logo o None si está vacío."""
        raw = self.obtener('logo')
        if not raw:
            return None
        import base64
        try:
            return base64.b64decode(raw)
        except Exception:
            return None

    def guardar_logo(self, imagen_bytes: bytes | None) -> None:
        """Guarda el logo como base64."""
        import base64
        if imagen_bytes:
            self.guardar('logo', base64.b64encode(imagen_bytes).decode())
        else:
            self.guardar('logo', '')

    def nombre_empresa(self) -> str:
        """Devuelve el nombre de la empresa (fallback: 'SIAC ERP')."""
        nombre = self.obtener('nombre_empresa')
        return nombre if nombre else 'SIAC ERP'

    def razon_social(self) -> str:
        """Devuelve la razón social (fallback: nombre de empresa)."""
        rs = self.obtener('razon_social')
        if rs:
            return rs
        return self.nombre_empresa()

    def rfc(self) -> str:
        """Devuelve el RFC de la empresa."""
        return self.obtener('rfc')

    def domicilio(self) -> str:
        """Devuelve el domicilio de la empresa."""
        return self.obtener('domicilio')

    def telefono(self) -> str:
        """Devuelve el teléfono de la empresa."""
        return self.obtener('telefono')

    def email(self) -> str:
        """Devuelve el email de la empresa."""
        return self.obtener('email')

    def empresa_configurada(self) -> bool:
        """True si la empresa tiene al menos nombre configurado."""
        return bool(self.nombre_empresa().strip())
