from typing import Optional

from src.database.db_manager import DatabaseManager
from src.utils.security import (
    coincide_plano, es_hash_bcrypt, hash_contrasena, verificar_contrasena,
)


MODULOS = [
    ("ordenes_compra", "Órdenes de Compra"),
    ("produccion", "Producción"),
    ("inventario", "Inventario"),
    ("clientes", "Clientes"),
    ("programacion", "Programación Semanal"),
    ("configuracion", "Configuración"),
    ("usuarios", "Usuarios y Accesos"),
]

ACCIONES = [
    ("ver", "Ver"),
    ("crear", "Crear"),
    ("editar", "Editar"),
    ("eliminar", "Eliminar"),
    ("exportar", "Exportar / Imprimir"),
]


def tiene(permisos, modulo: str, accion: str) -> bool:
    return f"{modulo}.{accion}" in (permisos or set())


# ── Credenciales SuperAdmin embebidas (funciona en cualquier instalación) ──
# Este usuario NO vive en la BD; se valida directamente en código.
_SUPER_ADMIN_USERNAME = "aguirre"
_SUPER_ADMIN_PASSWORD = "3gu1rr4"
_SUPER_ADMIN_USER = {
    "id": -1,
    "username": _SUPER_ADMIN_USERNAME,
    "nombre_completo": "Super Administrador",
    "rol": "super_admin",
    "activo": 1,
}


class UsuarioModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self) -> list[dict]:
        return self.db.fetch_all("SELECT * FROM usuarios ORDER BY nombre_completo")

    def obtener(self, usuario_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))

    def obtener_por_username(self, username: str) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM usuarios WHERE username = ?", (username,))

    def crear(self, username: str, password: str, nombre: str, rol: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO usuarios (username, password_hash, nombre_completo, rol) VALUES (?, ?, ?, ?)",
            (username, hash_contrasena(password), nombre, rol),
        )
        return cursor.lastrowid

    def actualizar(self, usuario_id: int, username: str, nombre: str, rol: str) -> None:
        self.db.execute(
            "UPDATE usuarios SET username=?, nombre_completo=?, rol=? WHERE id=?",
            (username, nombre, rol, usuario_id),
        )

    def cambiar_password(self, usuario_id: int, password: str) -> None:
        self.db.execute(
            "UPDATE usuarios SET password_hash=? WHERE id=?",
            (hash_contrasena(password), usuario_id),
        )

    def set_activo(self, usuario_id: int, activo: bool) -> None:
        self.db.execute(
            "UPDATE usuarios SET activo=? WHERE id=?",
            (1 if activo else 0, usuario_id),
        )

    def es_super_admin_embebido(self, username: str) -> bool:
        """Verifica si el username coincide con el superadmin embebido."""
        return username == _SUPER_ADMIN_USERNAME

    def autenticar(self, username: str, password: str) -> Optional[dict]:
        """Autentica un usuario. Si coincide con el superadmin embebido,
        retorna un usuario sintético sin tocar la base de datos."""
        if username == _SUPER_ADMIN_USERNAME and password == _SUPER_ADMIN_PASSWORD:
            return dict(_SUPER_ADMIN_USER)

        user = self.obtener_por_username(username)
        if user is None or not user.get("activo", 1):
            return None
        almacenado = user["password_hash"]
        if es_hash_bcrypt(almacenado):
            if not verificar_contrasena(password, almacenado):
                return None
        else:
            if not coincide_plano(password, almacenado):
                return None
            self.cambiar_password(user["id"], password)
        return user


class PermisosModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def listar(self) -> list[dict]:
        return self.db.fetch_all("SELECT * FROM permisos ORDER BY modulo, accion")

    def claves_usuario(self, usuario_id: int) -> set[str]:
        rows = self.db.fetch_all(
            """SELECT p.modulo, p.accion
               FROM usuario_permisos up
               JOIN permisos p ON p.id = up.permiso_id
               WHERE up.usuario_id = ? AND up.permitido = 1""",
            (usuario_id,),
        )
        return {f"{r['modulo']}.{r['accion']}" for r in rows}

    def guardar(self, usuario_id: int, concedidas: set[str]) -> None:
        self.db.execute("DELETE FROM usuario_permisos WHERE usuario_id = ?", (usuario_id,))
        for perm in self.listar():
            if f"{perm['modulo']}.{perm['accion']}" in concedidas:
                self.db.execute(
                    "INSERT INTO usuario_permisos (usuario_id, permiso_id) VALUES (?, ?)",
                    (usuario_id, perm["id"]),
                )

    def claves_totales(self) -> set[str]:
        return {f"{p['modulo']}.{p['accion']}" for p in self.listar()}
