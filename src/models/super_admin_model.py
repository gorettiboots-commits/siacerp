"""Modelo del dashboard de Super Admin.

Consulta datos de Supabase para mostrar estadisticas multi-empresa:
- Lista de empresas con estadisticas
- Usuarios por empresa
- Actividad reciente
"""
from typing import Any

from src.utils.supabase_service import SupabaseService


class SuperAdminModel:
    """Modelo para el dashboard de super_admin (multi-empresa)."""

    def __init__(self) -> None:
        self.sb = SupabaseService()

    def listar_empresas(self) -> list[dict]:
        """Lista todas las empresas con estadisticas basicas."""
        if not self.sb.configurado:
            return []
        try:
            empresas = self.sb.service_call('/rest/v1/empresas?select=*&order=nombre')
            return empresas or []
        except Exception:
            return []

    def contar_usuarios_por_empresa(self, empresa_id: str) -> int:
        """Cuenta los usuarios activos de una empresa."""
        if not self.sb.configurado:
            return 0
        try:
            perfiles = self.sb.service_call(
                f'/rest/v1/perfiles_usuario?select=id&empresa_id=eq.{empresa_id}&activo=eq.true'
            )
            return len(perfiles) if perfiles else 0
        except Exception:
            return 0

    def contar_insumos_por_empresa(self, empresa_id: str) -> int:
        """Cuenta los insumos de una empresa."""
        if not self.sb.configurado:
            return 0
        try:
            insumos = self.sb.service_call(
                f'/rest/v1/insumos_movil?select=id&empresa_id=eq.{empresa_id}'
            )
            return len(insumos) if insumos else 0
        except Exception:
            return 0

    def contar_ocs_por_empresa(self, empresa_id: str) -> int:
        """Cuenta las OCs de una empresa."""
        if not self.sb.configurado:
            return 0
        try:
            ocs = self.sb.service_call(
                f'/rest/v1/ordenes_compra_movil?select=id&empresa_id=eq.{empresa_id}'
            )
            return len(ocs) if ocs else 0
        except Exception:
            return 0

    def contar_ops_por_empresa(self, empresa_id: str) -> int:
        """Cuenta las OPs de una empresa."""
        if not self.sb.configurado:
            return 0
        try:
            ops = self.sb.service_call(
                f'/rest/v1/ordenes_produccion_movil?select=id&empresa_id=eq.{empresa_id}'
            )
            return len(ops) if ops else 0
        except Exception:
            return 0

    def listar_usuarios_empresa(self, empresa_id: str) -> list[dict]:
        """Lista los usuarios de una empresa."""
        if not self.sb.configurado:
            return []
        try:
            perfiles = self.sb.service_call(
                f'/rest/v1/perfiles_usuario?select=id,username,nombre_completo,rol,activo'
                f'&empresa_id=eq.{empresa_id}&order=username'
            )
            return perfiles or []
        except Exception:
            return []

    def obtener_todos_los_usuarios(self) -> list[dict]:
        """Lista todos los usuarios de todas las empresas."""
        if not self.sb.configurado:
            return []
        try:
            perfiles = self.sb.service_call(
                '/rest/v1/perfiles_usuario?select=id,username,nombre_completo,rol,activo,empresa_id&order=username'
            )
            return perfiles or []
        except Exception:
            return []

    def cambiar_estado_empresa(self, empresa_id: str, activo: bool) -> dict:
        """Activa o desactiva una empresa."""
        if not self.sb.configurado:
            return {'ok': False, 'error': 'Supabase no configurado'}
        try:
            self.sb.service_call(
                f'/rest/v1/empresas?id=eq.{empresa_id}',
                method='PATCH',
                data={'activo': activo}
            )
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def estadisticas_globales(self) -> dict:
        """Obtiene estadisticas globales de todas las empresas."""
        empresas = self.listar_empresas()
        total_usuarios = 0
        total_insumos = 0
        total_ocs = 0
        total_ops = 0

        for emp in empresas:
            eid = emp['id']
            total_usuarios += self.contar_usuarios_por_empresa(eid)
            total_insumos += self.contar_insumos_por_empresa(eid)
            total_ocs += self.contar_ocs_por_empresa(eid)
            total_ops += self.contar_ops_por_empresa(eid)

        return {
            'total_empresas': len(empresas),
            'empresas_activas': sum(1 for e in empresas if e.get('activo', True)),
            'total_usuarios': total_usuarios,
            'total_insumos': total_insumos,
            'total_ocs': total_ocs,
            'total_ops': total_ops,
        }
