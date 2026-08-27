"""Controller del dashboard de Super Admin.

Orquesta las consultas del SuperAdminModel y expone los datos
formateados para la vista.
"""
from src.models.super_admin_model import SuperAdminModel


class SuperAdminController:
    """Controller para el dashboard de super_admin."""

    def __init__(self) -> None:
        self.model = SuperAdminModel()

    def obtener_empresas_con_estadisticas(self) -> list[dict]:
        """Retorna la lista de empresas con sus estadisticas."""
        empresas = self.model.listar_empresas()
        resultado = []

        for emp in empresas:
            eid = emp['id']
            resultado.append({
                'id': eid,
                'nombre': emp.get('nombre', ''),
                'rfc': emp.get('rfc', ''),
                'activo': emp.get('activo', True),
                'usuarios': self.model.contar_usuarios_por_empresa(eid),
                'insumos': self.model.contar_insumos_por_empresa(eid),
                'ocs': self.model.contar_ocs_por_empresa(eid),
                'ops': self.model.contar_ops_por_empresa(eid),
            })

        return resultado

    def obtener_estadisticas_globales(self) -> dict:
        """Retorna estadisticas globales del sistema."""
        return self.model.estadisticas_globales()

    def obtener_usuarios_empresa(self, empresa_id: str) -> list[dict]:
        """Retorna los usuarios de una empresa."""
        return self.model.listar_usuarios_empresa(empresa_id)

    def obtener_todos_usuarios(self) -> list[dict]:
        """Retorna todos los usuarios del sistema."""
        return self.model.obtener_todos_los_usuarios()
