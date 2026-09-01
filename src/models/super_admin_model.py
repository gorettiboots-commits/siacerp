"""Modelo del dashboard de Super Admin (local + Supabase).

Consulta la BD local (SQLite/PostgreSQL) como fuente principal.
Cuando Supabase esta configurado, tambien consulta y sincroniza
los datos de empresas y usuarios en Supabase.
"""
import configparser
from pathlib import Path
from typing import Any

from src.database.db_manager import DatabaseManager


class SuperAdminModel:
    """Modelo para el dashboard de super_admin (local + Supabase)."""

    def __init__(self) -> None:
        self.db = DatabaseManager()
        self._sb_configurado: bool | None = None
        self._service_key: str = ''

    # ----------------------------------------------------------------
    # Supabase helpers
    # ----------------------------------------------------------------

    def _cargar_supabase(self) -> bool:
        """Carga configuracion de Supabase y retorna True si esta disponible."""
        if self._sb_configurado is not None:
            return self._sb_configurado
        try:
            config = configparser.ConfigParser()
            ruta = Path(__file__).resolve().parent.parent.parent / 'config.ini'
            config.read(str(ruta))
            url = config.get('supabase', 'url', fallback='')
            self._service_key = config.get(
                'supabase', 'service_role_key', fallback='')
            self._sb_configurado = bool(url and self._service_key)
            if self._sb_configurado:
                self._sb_url = url.rstrip('/')
            return self._sb_configurado
        except Exception:
            self._sb_configurado = False
            return False

    def _sb_llamada(self, endpoint: str, method: str = 'GET',
                    data: dict | None = None) -> Any:
        """Realiza una llamada REST a Supabase usando service_role key."""
        import json
        import urllib.request

        url = f'{self._sb_url}/rest/v1{endpoint}'
        headers = {
            'apikey': self._service_key,
            'Authorization': f'Bearer {self._service_key}',
            'Content-Type': 'application/json',
        }
        if method in ('PATCH', 'POST'):
            headers['Prefer'] = 'return=representation'
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode()
        return json.loads(raw) if raw.strip() else []

    def _obtener_empresa_id(self) -> str:
        """Obtiene el empresa_id de config.ini."""
        try:
            config = configparser.ConfigParser()
            ruta = Path(__file__).resolve().parent.parent.parent / 'config.ini'
            config.read(str(ruta))
            return config.get('supabase', 'empresa_id', fallback='')
        except Exception:
            return ''

    # ----------------------------------------------------------------
    # EMPRESA (local + Supabase)
    # ----------------------------------------------------------------

    def obtener_empresa_local(self) -> dict:
        """Obtiene la info de la empresa desde configuracion_empresa."""
        try:
            config = self.db.fetch_all(
                "SELECT clave, valor FROM configuracion_empresa")
            empresa = {}
            for row in config:
                empresa[row['clave']] = row['valor']
            empresa['id'] = self._obtener_empresa_id()
            # Parsear activo (puede ser '1'/'0' o 'True'/'False')
            activo_raw = empresa.get('activo', '1')
            empresa['activo'] = activo_raw in ('1', 'True', 'true', 'on')
            return empresa
        except Exception:
            return {}

    def cambiar_estado_empresa_local(self, activo: bool) -> dict:
        """Activa o desactiva la empresa local."""
        try:
            self.db.execute(
                "UPDATE configuracion_empresa SET valor = ? WHERE clave = 'activo'",
                ('1' if activo else '0',))
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def listar_empresas_supabase(self) -> list[dict]:
        """Lista empresas desde Supabase (si esta configurado)."""
        if not self._cargar_supabase():
            return []
        try:
            return self._sb_llamada('/empresas?select=*&order=nombre')
        except Exception:
            return []

    def cambiar_estado_empresa_supabase(
            self, empresa_id: str, activo: bool) -> dict:
        """Activa/desactiva una empresa en Supabase."""
        if not self._cargar_supabase():
            return {'ok': False, 'error': 'Supabase no configurado'}
        try:
            resultado = self._sb_llamada(
                f'/empresas?id=eq.{empresa_id}',
                method='PATCH',
                data={'activo': activo}
            )
            if isinstance(resultado, list) and len(resultado) == 0:
                return {'ok': False,
                        'error': 'Empresa no encontrada en Supabase'}
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # ----------------------------------------------------------------
    # ESTADISTICAS
    # ----------------------------------------------------------------

    def estadisticas_globales(self) -> dict:
        """Estadisticas de la BD local + Supabase si disponible."""
        try:
            total_usuarios = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM usuarios")['n']
            total_insumos = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM insumos WHERE activo = 1")['n']
            total_ocs = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM ordenes_compra")['n']
            total_ops = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM ordenes_produccion")['n']
            total_modelos = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM modelos WHERE activo = 1")['n']
            usuarios_activos = self.db.fetch_one(
                "SELECT COUNT(*) as n FROM usuarios WHERE activo = 1")['n']
        except Exception:
            total_usuarios = total_insumos = total_ocs = 0
            total_ops = total_modelos = usuarios_activos = 0

        # Agregar datos de Supabase si esta disponible
        empresas_sb = self.listar_empresas_supabase()
        return {
            'total_empresas': max(1, len(empresas_sb)) if empresas_sb else 1,
            'empresas_activas': sum(
                1 for e in empresas_sb if e.get('activo', True)
            ) if empresas_sb else 1,
            'total_usuarios': total_usuarios,
            'usuarios_activos': usuarios_activos,
            'total_insumos': total_insumos,
            'total_ocs': total_ocs,
            'total_ops': total_ops,
            'total_modelos': total_modelos,
            'supabase_configurado': self._cargar_supabase(),
        }

    # ----------------------------------------------------------------
    # USUARIOS (local)
    # ----------------------------------------------------------------

    def listar_usuarios(self) -> list[dict]:
        """Lista todos los usuarios de la BD local."""
        try:
            return self.db.fetch_all(
                "SELECT id, username, nombre_completo, rol, activo "
                "FROM usuarios ORDER BY username")
        except Exception:
            return []

    def cambiar_estado_usuario(self, usuario_id: int, activo: bool) -> dict:
        """Activa o desactiva un usuario local."""
        try:
            self.db.execute(
                "UPDATE usuarios SET activo = ? WHERE id = ?",
                (1 if activo else 0, usuario_id))
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}
