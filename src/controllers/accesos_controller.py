from src.models.accesos_model import PermisosModel, UsuarioModel, tiene


class AccesosController:
    def __init__(self) -> None:
        self.usuario_model = UsuarioModel()
        self.permisos_model = PermisosModel()

    @staticmethod
    def tiene(permisos, modulo: str, accion: str) -> bool:
        return tiene(permisos, modulo, accion)

    def listar_usuarios(self) -> list[dict]:
        return self.usuario_model.listar()

    def obtener_usuario(self, usuario_id: int) -> dict | None:
        return self.usuario_model.obtener(usuario_id)

    def crear_usuario(self, username: str, password: str, nombre: str,
                      rol: str = "operador") -> int:
        return self.usuario_model.crear(username, password, nombre, rol)

    def actualizar_usuario(self, usuario_id: int, username: str, nombre: str,
                           rol: str) -> None:
        self.usuario_model.actualizar(usuario_id, username, nombre, rol)

    def cambiar_password(self, usuario_id: int, password: str) -> None:
        self.usuario_model.cambiar_password(usuario_id, password)

    def set_activo(self, usuario_id: int, activo: bool) -> None:
        self.usuario_model.set_activo(usuario_id, activo)

    def autenticar(self, username: str, password: str) -> dict | None:
        return self.usuario_model.autenticar(username, password)

    def listar_permisos(self) -> list[dict]:
        return self.permisos_model.listar()

    def permisos_usuario(self, usuario_id: int) -> set[str]:
        return self.permisos_model.claves_usuario(usuario_id)

    def guardar_permisos(self, usuario_id: int, concedidas: set[str]) -> None:
        self.permisos_model.guardar(usuario_id, concedidas)

    def claves_totales(self) -> set[str]:
        return self.permisos_model.claves_totales()

    def permisos_login(self, user: dict) -> set[str]:
        if user.get("rol") == "admin":
            return self.claves_totales()
        return self.permisos_usuario(user["id"])
