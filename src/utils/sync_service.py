import json
import threading
import time
from datetime import datetime
from typing import Optional

from src.database.db_manager import DatabaseManager
from src.utils.supabase_service import SupabaseService


class SyncService:
    """Servicio de sincronizacion bidireccional entre BD local y Supabase.

    Permite que multiples terminales de la misma empresa compartan datos.
    Cada terminal sincroniza periodicamente con Supabase.

    Flujo:
    1. Local -> Supabase: sube datos modificados localmente
    2. Supabase -> Local: baja datos modificados en otras terminales
    3. Resolucion de conflictos: ultima modificacion gana (timestamp)
    """

    _instance: Optional['SyncService'] = None

    def __new__(cls) -> 'SyncService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.db = DatabaseManager()
        self.supabase = SupabaseService()
        self._activo = False
        self._timer: Optional[threading.Timer] = None
        self._intervalo_segundos = 300  # 5 minutos
        self._ultima_sincronizacion: Optional[datetime] = None
        self._errores: list[str] = []

    @property
    def conectado(self) -> bool:
        return self.supabase.configurado and self.supabase.autenticado

    @property
    def estado(self) -> dict:
        return {
            'activo': self._activo,
            'conectado': self.conectado,
            'ultima_sync': self._ultima_sincronizacion.isoformat() if self._ultima_sincronizacion else None,
            'errores_recientes': self._errores[-5:],
            'empresa_id': self.supabase.empresa_id[:8] + '...' if self.supabase.empresa_id else None,
        }

    def iniciar(self, intervalo_segundos: int = 300) -> None:
        """Inicia la sincronizacion automatica."""
        if not self.conectado:
            print('[Sync] No conectado a Supabase')
            return

        self._activo = True
        self._intervalo_segundos = intervalo_segundos
        print(f'[Sync] Iniciada cada {intervalo_segundos}s')

        # Primera sincronizacion inmediata
        self._sincronizar()

        # Programar siguientes sincronizaciones
        self._programar_siguiente()

    def detener(self) -> None:
        """Detiene la sincronizacion automatica."""
        self._activo = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        print('[Sync] Detenida')

    def _programar_siguiente(self) -> None:
        """Programa la siguiente sincronizacion."""
        if not self._activo:
            return
        self._timer = threading.Timer(
            self._intervalo_segundos,
            self._sincronizar_y_reprogramar
        )
        self._timer.daemon = True
        self._timer.start()

    def _sincronizar_y_reprogramar(self) -> None:
        """Sincroniza y reprograma la siguiente."""
        self._sincronizar()
        self._programar_siguiente()

    def sincronizar_ahora(self) -> dict:
        """Ejecuta una sincronizacion inmediata.

        Returns:
            {'ok': True, 'subidos': N, 'bajados': M} o {'ok': False, 'error': '...'}
        """
        if not self.conectado:
            return {'ok': False, 'error': 'No conectado a Supabase'}
        return self._sincronizar()

    def _sincronizar(self) -> dict:
        """Ejecuta la sincronizacion completa."""
        resultado = {'ok': True, 'subidos': 0, 'bajados': 0, 'errores': []}

        try:
            # 1. Subir datos locales a Supabase
            subidos = self._subir_datos_locales()
            resultado['subidos'] = subidos

            # 2. Bajar datos de Supabase a local
            bajados = self._bajar_datos_supabase()
            resultado['bajados'] = bajados

            self._ultima_sincronizacion = datetime.now()
            print(f'[Sync] OK: {subidos} subidos, {bajados} bajados')

        except Exception as e:
            resultado['ok'] = False
            resultado['errores'].append(str(e))
            self._errores.append(f'{datetime.now()}: {e}')
            print(f'[Sync] ERROR: {e}')

        return resultado

    def _subir_datos_locales(self) -> int:
        """Sube datos modificados localmente a Supabase."""
        total = 0

        # Tablas para sincronizar (local -> Supabase)
        tablas = {
            'insumos': 'insumos_movil',
            'ordenes_compra': 'ordenes_compra_movil',
            'detalle_orden_compra': 'detalle_orden_compra_movil',
            'ordenes_produccion': 'ordenes_produccion_movil',
            'seguimiento_produccion': 'seguimiento_produccion_movil',
        }

        for local_table, remote_table in tablas.items():
            try:
                # Obtener registros con empresa_id
                datos = self.db.fetch_all(
                    f'SELECT * FROM {local_table} WHERE empresa_id = ?',
                    (self.supabase.empresa_id,)
                )
                if datos:
                    # Mapear columnas locales a Supabase
                    mapped = self._mapear_a_supabase(local_table, datos)
                    if mapped:
                        result = self.supabase.sincronizar_tabla(remote_table, mapped)
                        if result.get('ok'):
                            total += len(mapped)
                            print(f'  {local_table}: {len(mapped)} registros subidos')
            except Exception as e:
                print(f'  {local_table}: error subiendo - {e}')

        return total

    def _bajar_datos_supabase(self) -> int:
        """Baja datos de Supabase a la BD local."""
        total = 0

        # Tablas para sincronizar (Supabase -> local)
        tablas = {
            'insumos_movil': 'insumos',
            'ordenes_compra_movil': 'ordenes_compra',
            'detalle_orden_compra_movil': 'detalle_orden_compra',
            'ordenes_produccion_movil': 'ordenes_produccion',
            'seguimiento_produccion_movil': 'seguimiento_produccion',
            'tallas_catalogo_movil': 'tallas_catalogo',
        }

        for remote_table, local_table in tablas.items():
            try:
                datos = self.supabase.obtener_tabla(remote_table)
                if datos:
                    mapped = self._mapear_a_local(remote_table, datos)
                    if mapped:
                        for registro in mapped:
                            self._upsert_local(local_table, registro)
                        total += len(mapped)
                        print(f'  {remote_table}: {len(mapped)} registros bajados')
            except Exception as e:
                print(f'  {remote_table}: error bajando - {e}')

        return total

    def _mapear_a_supabase(self, tabla_local: str, datos: list[dict]) -> list[dict]:
        """Mapea registros de la BD local al formato de Supabase."""
        result = []
        for d in datos:
            registro = dict(d)
            registro['empresa_id'] = self.supabase.empresa_id
            # Eliminar campos que no existen en Supabase
            registro.pop('created_at', None)
            registro.pop('updated_at', None)
            result.append(registro)
        return result

    def _mapear_a_local(self, tabla_remota: str, datos: list[dict]) -> list[dict]:
        """Mapea registros de Supabase al formato de la BD local."""
        result = []
        for d in datos:
            registro = dict(d)
            registro['empresa_id'] = self.supabase.empresa_id
            result.append(registro)
        return result

    def _upsert_local(self, tabla: str, registro: dict) -> None:
        """Inserta o actualiza un registro en la BD local."""
        try:
            if 'id' not in registro or registro['id'] is None:
                return

            # Verificar si existe
            existente = self.db.fetch_one(
                f'SELECT id FROM {tabla} WHERE id = ?',
                (registro['id'],)
            )

            if existente:
                # Actualizar
                cols = [k for k in registro.keys() if k != 'id' and k in self._obtener_columnas(tabla)]
                if cols:
                    set_clause = ', '.join(f'{c} = ?' for c in cols)
                    valores = tuple(registro[c] for c in cols) + (registro['id'],)
                    self.db.execute(
                        f'UPDATE {tabla} SET {set_clause} WHERE id = ?',
                        valores
                    )
            else:
                # Insertar
                cols = [k for k in registro.keys() if k in self._obtener_columnas(tabla)]
                placeholders = ', '.join('?' * len(cols))
                col_names = ', '.join(cols)
                valores = tuple(registro[c] for c in cols)
                self.db.execute(
                    f'INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})',
                    valores
                )
        except Exception as e:
            print(f'    upsert {tabla} id={registro.get("id")}: {e}')

    def _obtener_columnas(self, tabla: str) -> list[str]:
        """Obtiene las columnas de una tabla."""
        try:
            if self.db.engine == 'sqlite':
                conn = self.db.connect()
                cursor = conn.cursor()
                return [r[1] for r in cursor.execute(
                    f'PRAGMA table_info({tabla})').fetchall()]
            else:
                conn = self.db.connect()
                cursor = conn.cursor()
                cursor.execute(
                    f'SELECT column_name FROM information_schema.columns '
                    f'WHERE table_name = %s', (tabla,))
                return [r[0] for r in cursor.fetchall()]
        except Exception:
            return []
