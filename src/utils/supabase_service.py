import configparser
import json
import urllib.request
from pathlib import Path
from typing import Any, Optional


class SupabaseService:
    """Servicio de conexion a Supabase para el escritorio SIAC ERP.

    Permite:
    - Autenticar usuarios via Supabase Auth
    - Leer/escribir datos en Supabase
    - Sincronizar datos locales con Supabase
    - Validar licenciamiento por empresa
    """

    _instance: Optional['SupabaseService'] = None

    def __new__(cls) -> 'SupabaseService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.url: str = ''
        self.anon_key: str = ''
        self.empresa_id: str = ''
        self._token: str = ''
        self._usuario_id: str = ''
        self._conectado = False
        self._cargar_config()

    def _cargar_config(self) -> None:
        """Carga configuracion de Supabase desde config.ini."""
        config = configparser.ConfigParser()
        ruta = Path(__file__).resolve().parent.parent.parent / 'config.ini'
        if not ruta.exists():
            return
        config.read(str(ruta))
        if config.has_section('supabase'):
            self.url = config.get('supabase', 'url', fallback='')
            self.anon_key = config.get('supabase', 'anon_key', fallback='')
            self.empresa_id = config.get('supabase', 'empresa_id', fallback='')

    @property
    def configurado(self) -> bool:
        return bool(self.url and self.anon_key and self.empresa_id)

    @property
    def autenticado(self) -> bool:
        return bool(self._token and self._usuario_id)

    def login(self, email: str, password: str) -> dict:
        """Inicia sesion con email/password via Supabase Auth.

        Returns:
            {'ok': True, 'usuario': {...}} o {'ok': False, 'error': '...'}
        """
        if not self.configurado:
            return {'ok': False, 'error': 'Supabase no configurado'}

        try:
            req = urllib.request.Request(
                f'{self.url}/auth/v1/token?grant_type=password',
                data=json.dumps({
                    'email': email,
                    'password': password
                }).encode(),
                headers={
                    'apikey': self.anon_key,
                    'Content-Type': 'application/json'
                }
            )
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode())

            self._token = data['access_token']
            self._usuario_id = data['user']['id']

            # Obtener perfil con empresa_id
            perfil = self._api_call(
                f'/rest/v1/perfiles_usuario?select=*&id=eq.{self._usuario_id}'
            )
            if perfil and len(perfil) > 0:
                p = perfil[0]
                if not p.get('activo', True):
                    return {'ok': False, 'error': 'Usuario desactivado'}

                # Verificar que la empresa del usuario coincida con la configurada
                # Super_admin puede no tener empresa_id (acceso total)
                if p.get('rol') != 'super_admin':
                    if p.get('empresa_id') and p['empresa_id'] != self.empresa_id:
                        return {
                            'ok': False,
                            'error': 'Este usuario no pertenece a esta empresa'
                        }

                self._conectado = True
                return {
                    'ok': True,
                    'usuario': {
                        'id': p['id'],
                        'username': p['username'],
                        'nombre_completo': p['nombre_completo'],
                        'rol': p['rol'],
                        'empresa_id': p['empresa_id']
                    }
                }
            else:
                return {'ok': False, 'error': 'Perfil no encontrado'}

        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if 'Invalid login' in body or 'invalid_grant' in body:
                return {'ok': False, 'error': 'Credenciales incorrectas'}
            return {'ok': False, 'error': f'Error de conexion: {e.code}'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def logout(self) -> None:
        """Cierra sesion."""
        self._token = ''
        self._usuario_id = ''
        self._conectado = False

    def _api_call(self, endpoint: str, method: str = 'GET',
                  data: dict = None) -> Any:
        """Realiza una llamada a la API de Supabase."""
        url = f'{self.url}{endpoint}'
        headers = {
            'apikey': self.anon_key,
            'Content-Type': 'application/json'
        }
        if self._token:
            headers['Authorization'] = f'Bearer {self._token}'

        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())

    def service_call(self, endpoint: str, method: str = 'GET',
                     data: dict = None) -> Any:
        """Realiza una llamada usando la service_role key (bypass RLS)."""
        config = configparser.ConfigParser()
        ruta = Path(__file__).resolve().parent.parent.parent / 'config.ini'
        config.read(str(ruta))
        service_key = config.get('supabase', 'service_role_key', fallback='')

        if not service_key:
            # Fallback a anon key
            return self._api_call(endpoint, method, data)

        url = f'{self.url}{endpoint}'
        headers = {
            'apikey': self.anon_key,
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        }
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())

    def verificar_licencia(self) -> dict:
        """Verifica que la empresa tenga licencia activa en Supabase.

        Returns:
            {'ok': True, 'empresa': {...}} o {'ok': False, 'error': '...'}
        """
        if not self.configurado:
            return {'ok': False, 'error': 'Supabase no configurado'}

        try:
            empresas = self.service_call(
                f'/rest/v1/empresas?select=*&id=eq.{self.empresa_id}'
            )
            if empresas and len(empresas) > 0:
                emp = empresas[0]
                if emp.get('activo', True):
                    return {'ok': True, 'empresa': emp}
                else:
                    return {'ok': False, 'error': 'Empresa desactivada'}
            else:
                return {'ok': False, 'error': 'Empresa no encontrada'}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def listar_usuarios_empresa(self) -> list[dict]:
        """Lista los usuarios de la empresa actual."""
        if not self.configurado:
            return []
        try:
            return self.service_call(
                f'/rest/v1/perfiles_usuario?select=id,username,nombre_completo,rol,activo&empresa_id=eq.{self.empresa_id}'
            )
        except Exception:
            return []

    def sincronizar_tabla(self, tabla: str, datos: list[dict]) -> dict:
        """Sincroniza datos de una tabla local a Supabase.

        Args:
            tabla: Nombre de la tabla en Supabase (con sufijo _movil si aplica)
            datos: Lista de registros a sincronizar

        Returns:
            {'ok': True, 'registros': N} o {'ok': False, 'error': '...'}
        """
        if not self.configurado or not self.autenticado:
            return {'ok': False, 'error': 'No autenticado'}

        try:
            # Agregar empresa_id a cada registro
            for registro in datos:
                registro['empresa_id'] = self.empresa_id

            # Upsert en Supabase
            req = urllib.request.Request(
                f'{self.url}/rest/v1/{tabla}',
                data=json.dumps(datos).encode(),
                headers={
                    'apikey': self.anon_key,
                    'Authorization': f'Bearer {self._token}',
                    'Content-Type': 'application/json',
                    'Prefer': 'resolution=merge-duplicates'
                },
                method='POST'
            )
            urllib.request.urlopen(req, timeout=30)
            return {'ok': True, 'registros': len(datos)}

        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def obtener_tabla(self, tabla: str, filtros: str = '') -> list[dict]:
        """Obtiene datos de una tabla en Supabase.

        Args:
            tabla: Nombre de la tabla en Supabase
            filtros: Filtros adicionales (ej: '&estatus=eq.pendiente')

        Returns:
            Lista de registros
        """
        if not self.configurado or not self.autenticado:
            return []

        try:
            endpoint = f'/rest/v1/{tabla}?empresa_id=eq.{self.empresa_id}{filtros}'
            return self._api_call(endpoint)
        except Exception:
            return []
