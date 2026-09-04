"""Servicio de sincronización bidireccional (outbox pattern).

Flujo:
  1. Los models encolan cambios en `sync_queue` al modificar datos locales.
  2. Este servicio periodically:
     a) Envía los registros pendientes de sync_queue a Supabase.
     b) Descarga cambios de otras terminales desde Supabase.
     c) Limpia registros ya enviados antiguos.

Compatibilidad: SQLite (desarrollo) y PostgreSQL (estación principal).
"""
import json
import socket
import threading
import time
import urllib.request
from datetime import datetime
from typing import Optional

from src.database.db_manager import DatabaseManager
from src.models.sync_queue_model import SyncQueueModel
from src.utils.supabase_service import SupabaseService


class SyncService:
    """Sincronización bidireccional usando outbox (sync_queue)."""

    _instance: Optional['SyncService'] = None

    # Mapeo local_table -> remote_table (Supabase)
    TABLAS_SUBIR = {
        'insumos': 'insumos_movil',
        'modelos': 'modelos_movil',
        'variantes': 'variantes_movil',
        'proveedores': 'proveedores_movil',
        'clientes': 'clientes_movil',
        'ordenes_compra': 'ordenes_compra_movil',
        'detalle_orden_compra': 'detalle_orden_compra_movil',
        'ordenes_produccion': 'ordenes_produccion_movil',
        'seguimiento_produccion': 'seguimiento_produccion_movil',
        'pedidos_cliente': 'pedidos_cliente_movil',
        'programacion_semana': 'programacion_semana_movil',
        'programacion_lineas': 'programacion_lineas_movil',
        'programacion_linea_tallas': 'programacion_linea_tallas_movil',
    }

    # Mapeo remote_table -> local_table (para descarga)
    TABLAS_BAJAR = {
        'insumos_movil': 'insumos',
        'ordenes_compra_movil': 'ordenes_compra',
        'detalle_orden_compra_movil': 'detalle_orden_compra',
        'ordenes_produccion_movil': 'ordenes_produccion',
        'seguimiento_produccion_movil': 'seguimiento_produccion',
        'tallas_catalogo_movil': 'tallas_catalogo',
    }

    def __new__(cls) -> 'SyncService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.db = DatabaseManager()
        self.queue = SyncQueueModel()
        self.supabase = SupabaseService()
        self._activo = False
        self._timer: Optional[threading.Timer] = None
        self._intervalo_segundos = 300  # 5 minutos
        self._ultima_sincronizacion: Optional[datetime] = None
        self._errores: list[str] = []

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    @staticmethod
    def hay_red() -> bool:
        """Verifica si hay conexion a Internet rapida (timeout 3s)."""
        try:
            socket.create_connection(('1.1.1.1', 53), timeout=3)
            return True
        except (OSError, socket.timeout):
            return False

    @property
    def conectado(self) -> bool:
        return self.supabase.configurado and self.supabase.autenticado

    @property
    def estado(self) -> dict:
        return {
            'activo': self._activo,
            'conectado': self.conectado,
            'cola_pendientes': self.queue.contar_pendientes(),
            'ultima_sync': (
                self._ultima_sincronizacion.isoformat()
                if self._ultima_sincronizacion else None
            ),
            'errores_recientes': self._errores[-5:],
            'empresa_id': (
                self.supabase.empresa_id[:8] + '...'
                if self.supabase.empresa_id else None
            ),
        }

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def iniciar(self, intervalo_segundos: int = 300) -> None:
        """Inicia la sincronización automática."""
        if not self.conectado:
            print('[Sync] No conectado a Supabase')
            return
        self._activo = True
        self._intervalo_segundos = intervalo_segundos
        print(f'[Sync] Iniciada cada {intervalo_segundos}s '
              f'(cola: {self.queue.contar_pendientes()} pendientes)')
        self._sincronizar()
        self._programar_siguiente()

    def detener(self) -> None:
        """Detiene la sincronización automática."""
        self._activo = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        print('[Sync] Detenida')

    def sincronizar_ahora(self) -> dict:
        """Ejecuta una sincronización inmediata si hay red."""
        if not self.conectado:
            return {'ok': False, 'error': 'No conectado a Supabase'}
        if not self.hay_red():
            return {'ok': False, 'error': 'Sin conexión a Internet'}
        return self._sincronizar()

    def sincronizar_si_hay_red(self) -> dict:
        """Sincroniza solo si hay red. No bloquea la UI."""
        if not self.conectado or not self.hay_red():
            return {'ok': False, 'error': 'No disponible'}
        try:
            return self._sincronizar()
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Core de sincronización
    # ------------------------------------------------------------------

    def _programar_siguiente(self) -> None:
        if not self._activo:
            return
        self._timer = threading.Timer(
            self._intervalo_segundos,
            self._sincronizar_y_reprogramar,
        )
        self._timer.daemon = True
        self._timer.start()

    def _sincronizar_y_reprogramar(self) -> None:
        self._sincronizar()
        self._programar_siguiente()

    def _sincronizar(self) -> dict:
        resultado = {
            'ok': True, 'subidos': 0, 'bajados': 0,
            'eliminados': 0, 'errores': [],
        }
        try:
            # 0. Verificar conexion
            if not self.hay_red():
                return resultado

            # 1. Subir cambios pendientes de la cola
            subidos, eliminados = self._subir_cola()
            resultado['subidos'] = subidos
            resultado['eliminados'] = eliminados

            # 2. Reintentar errores
            reintentados = self._reintentar_errores()
            resultado['subidos'] += reintentados

            # 3. Bajar cambios de otras terminales
            bajados = self._bajar_datos_supabase()
            resultado['bajados'] = bajados

            # 4. Limpiar registros antiguos
            self.queue.limpiar_enviados(dias=7)

            self._ultima_sincronizacion = datetime.now()
            print(f'[Sync] OK: {subidos} subidos, {eliminados} eliminados, '
                  f'{bajados} bajados')

        except Exception as e:
            resultado['ok'] = False
            resultado['errores'].append(str(e))
            self._errores.append(f'{datetime.now()}: {e}')
            print(f'[Sync] ERROR: {e}')

        return resultado

    # ------------------------------------------------------------------
    # Subir: cola -> Supabase
    # ------------------------------------------------------------------

    def _subir_cola(self) -> tuple[int, int]:
        """Envía registros pendientes de sync_queue a Supabase."""
        pendientes = self.queue.pendientes(limite=200)
        subidos = 0
        eliminados = 0

        for registro in pendientes:
            try:
                tabla = registro['tabla']
                operacion = registro['operacion']
                registro_id = registro['registro_id']
                remote_table = self.TABLAS_SUBIR.get(tabla)

                if not remote_table:
                    # Tabla no sincronizable, marcar como enviado
                    self.queue.marcar_enviado(registro['id'])
                    continue

                if operacion == 'DELETE':
                    # Soft delete: enviar el registro con is_deleted=1
                    snapshot = self.queue.snapshot_registro(tabla, registro_id)
                    if snapshot:
                        datos = self._preparar_para_supabase(
                            tabla, snapshot, is_deleted=True)
                        self.supabase.sincronizar_tabla(remote_table, [datos])
                    eliminados += 1

                elif operacion in ('INSERT', 'UPDATE'):
                    datos_json = json.loads(registro['datos']) if registro['datos'] else None
                    if datos_json is None:
                        # Fallback: obtener snapshot actual
                        snapshot = self.queue.snapshot_registro(tabla, registro_id)
                        if snapshot:
                            datos_json = self._preparar_para_supabase(
                                tabla, snapshot)
                        else:
                            self.queue.marcar_enviado(registro['id'])
                            continue

                    self.supabase.sincronizar_tabla(remote_table, [datos_json])
                    subidos += 1

                self.queue.marcar_enviado(registro['id'])

            except Exception as e:
                self.queue.marcar_error(registro['id'], str(e))
                print(f'  [Sync] Error subiendo {registro["tabla"]}'
                      f'#{registro["registro_id"]}: {e}')

        return subidos, eliminados

    def _reintentar_errores(self) -> int:
        """Reintenta registros que fallaron previamente."""
        errores = self.queue.reintento_pendientes(max_intentos=3)
        reintentados = 0

        for registro in errores:
            try:
                tabla = registro['tabla']
                remote_table = self.TABLAS_SUBIR.get(tabla)
                if not remote_table:
                    self.queue.marcar_enviado(registro['id'])
                    continue

                datos_json = json.loads(registro['datos']) if registro['datos'] else None
                if datos_json is None:
                    snapshot = self.queue.snapshot_registro(
                        tabla, registro['registro_id'])
                    if snapshot:
                        datos_json = self._preparar_para_supabase(tabla, snapshot)
                    else:
                        self.queue.marcar_enviado(registro['id'])
                        continue

                self.supabase.sincronizar_tabla(remote_table, [datos_json])
                self.queue.marcar_enviado(registro['id'])
                reintentados += 1

            except Exception as e:
                self.queue.marcar_error(registro['id'], str(e))

        return reintentados

    # ------------------------------------------------------------------
    # Bajar: Supabase -> local
    # ------------------------------------------------------------------

    def _bajar_datos_supabase(self) -> int:
        """Descarga cambios de Supabase a la BD local."""
        total = 0

        for remote_table, local_table in self.TABLAS_BAJAR.items():
            try:
                datos = self.supabase.obtener_tabla(remote_table)
                if datos:
                    for registro in datos:
                        self._upsert_local(local_table, registro)
                    total += len(datos)
                    print(f'  [Sync] {remote_table}: {len(datos)} bajados')
            except Exception as e:
                print(f'  [Sync] Error bajando {remote_table}: {e}')

        return total

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _preparar_para_supabase(self, tabla: str, datos: dict,
                                 is_deleted: bool = False) -> dict:
        """Prepara un registro local para envío a Supabase."""
        registro = dict(datos)
        registro['empresa_id'] = self.supabase.empresa_id
        if is_deleted:
            registro['is_deleted'] = True
        # Eliminar campos que no existen en Supabase
        for campo in ('created_at', 'updated_at'):
            registro.pop(campo, None)
        return registro

    def _upsert_local(self, tabla: str, registro: dict) -> None:
        """Inserta o actualiza un registro en la BD local."""
        try:
            if 'id' not in registro or registro['id'] is None:
                return

            registro_id = registro['id']
            existente = self.db.fetch_one(
                f'SELECT id FROM {tabla} WHERE id = ?', (registro_id,)
            )

            cols_disponibles = self._obtener_columnas(tabla)
            cols = [k for k in registro.keys()
                    if k != 'id' and k in cols_disponibles]

            if existente:
                if cols:
                    set_clause = ', '.join(f'{c} = ?' for c in cols)
                    valores = tuple(registro[c] for c in cols) + (registro_id,)
                    self.db.execute(
                        f'UPDATE {tabla} SET {set_clause} WHERE id = ?',
                        valores,
                    )
            else:
                if cols:
                    placeholders = ', '.join('?' * (len(cols) + 1))
                    col_names = 'id, ' + ', '.join(cols)
                    valores = (registro_id,) + tuple(registro[c] for c in cols)
                    self.db.execute(
                        f'INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})',
                        valores,
                    )
        except Exception as e:
            print(f'  [Sync] upsert {tabla}#{registro.get("id")}: {e}')

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
                    'SELECT column_name FROM information_schema.columns '
                    'WHERE table_name = %s', (tabla,))
                return [r[0] for r in cursor.fetchall()]
        except Exception:
            return []
