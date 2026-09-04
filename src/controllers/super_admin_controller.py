"""Controller del dashboard de Super Admin.

Orquesta las consultas del SuperAdminModel y expone los datos
formateados para la vista. Opera sobre la BD local y Supabase
cuando esta configurado.
"""
from src.models.super_admin_model import SuperAdminModel


class SuperAdminController:
    """Controller para el dashboard de super_admin."""

    def __init__(self) -> None:
        self.model = SuperAdminModel()

    def obtener_empresa(self) -> dict:
        """Retorna la info de la empresa local."""
        return self.model.obtener_empresa_local()

    def obtener_estadisticas_globales(self) -> dict:
        """Retorna estadisticas globales del sistema."""
        return self.model.estadisticas_globales()

    def listar_usuarios(self) -> list[dict]:
        """Retorna todos los usuarios del sistema."""
        return self.model.listar_usuarios()

    def cambiar_estado_usuario(self, usuario_id: int, activo: bool) -> dict:
        """Activa o desactiva un usuario."""
        return self.model.cambiar_estado_usuario(usuario_id, activo)

    def cambiar_estado_empresa_local(self, activo: bool) -> dict:
        """Activa o desactiva la empresa local."""
        return self.model.cambiar_estado_empresa_local(activo)

    def listar_empresas_supabase(self) -> list[dict]:
        """Lista empresas desde Supabase (si configurado)."""
        return self.model.listar_empresas_supabase()

    def cambiar_estado_empresa(
            self, empresa_id: str, activo: bool) -> dict:
        """Activa o desactiva una empresa en Supabase."""
        return self.model.cambiar_estado_empresa_supabase(
            empresa_id, activo)
