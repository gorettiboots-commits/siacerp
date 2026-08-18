import configparser
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Optional


def directorio_datos() -> Path:
    """Directorio de datos de la aplicación (config.ini y BD SQLite).

    En desarrollo es la raíz del proyecto; en el empaquetado (PyInstaller)
    es %APPDATA%\\SIAC para que los datos no dependan de la carpeta del .exe.
    """
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "SIAC"
        base.mkdir(parents=True, exist_ok=True)
        return base
    return Path(__file__).resolve().parent.parent.parent


class DatabaseManager:
    _instance: Optional['DatabaseManager'] = None

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.config = self._load_config()
        self.engine: str = self.config.get('database', 'engine')
        self.connection: Any = None

    def _load_config(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        ruta = directorio_datos() / 'config.ini'
        if not ruta.exists():
            ejemplo = Path(__file__).resolve().parent.parent.parent / 'config.example.ini'
            if ejemplo.exists():
                base = configparser.ConfigParser()
                base.read(str(ejemplo), encoding='utf-8')
                with open(str(ruta), 'w', encoding='utf-8') as f:
                    base.write(f)
        config.read(str(ruta))
        return config

    @property
    def db_path(self) -> str:
        sqlite_path = self.config.get('database', 'sqlite_path')
        return str(directorio_datos() / sqlite_path)

    def connect(self) -> Any:
        if self.connection:
            return self.connection
        if self.engine == 'sqlite':
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
        elif self.engine == 'postgresql':
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.config.get('database', 'pg_host'),
                port=self.config.getint('database', 'pg_port'),
                user=self.config.get('database', 'pg_user'),
                password=self.config.get('database', 'pg_password'),
                dbname=self.config.get('database', 'pg_database'),
            )
        if self.connection:
            self.connection.row_factory = sqlite3.Row if self.engine == 'sqlite' else None
        return self.connection

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, query: str, params: tuple = ()) -> Any:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[dict]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row is None:
            return None
        if self.engine == 'sqlite':
            return dict(row)
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def fetch_all(self, query: str, params: tuple = ()) -> list[dict]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if self.engine == 'sqlite':
            return [dict(r) for r in rows]
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def initialize_schema(self) -> None:
        schema_path = Path(__file__).resolve().parent / 'schema.sql'
        with open(str(schema_path), 'r', encoding='utf-8') as f:
            sql = f.read()
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        conn = self.connect()
        cursor = conn.cursor()
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Advertencia al ejecutar: {stmt[:60]}... -> {e}")
        self._migrar()
        conn.commit()
        print("Esquema de base de datos inicializado correctamente.")

    def _migrar(self) -> None:
        self._migrar_passwords()
        self._migrar_logs()
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if self.engine == 'sqlite':
                cols = [r[1] for r in cursor.execute("PRAGMA table_info(variantes)").fetchall()]
                if 'talla' not in cols:
                    cursor.execute(
                        "ALTER TABLE variantes ADD COLUMN talla TEXT NOT NULL DEFAULT ''")
                    conn.commit()
                    print("Migración: columna talla agregada a variantes.")
            else:
                cursor.execute(
                    "ALTER TABLE variantes ADD COLUMN IF NOT EXISTS talla TEXT NOT NULL DEFAULT ''")
                conn.commit()
        except Exception as e:
            print(f"Migración talla omitida: {e}")
        try:
            conn = self.connect()
            cursor = conn.cursor()
            for tabla in ("insumos", "modelos"):
                if self.engine == 'sqlite':
                    cols = [r[1] for r in cursor.execute(f"PRAGMA table_info({tabla})").fetchall()]
                    if 'imagen' not in cols:
                        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN imagen BLOB")
                        conn.commit()
                        print(f"Migración: columna imagen agregada a {tabla}.")
                else:
                    cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS imagen BYTEA")
                    conn.commit()
        except Exception as e:
            print(f"Migración imagen omitida: {e}")
        if self.engine != 'sqlite':
            return
        conn = self.connect()
        cursor = conn.cursor()
        try:
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(estaciones_produccion)").fetchall()]
            if 'activo' not in cols:
                cursor.execute(
                    "ALTER TABLE estaciones_produccion ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
                conn.commit()
                print("Migración: columna activo agregada a estaciones_produccion.")
        except Exception as e:
            print(f"Migración omitida: {e}")

        try:
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(programacion_semana)").fetchall()]
            if 'fecha_inicio' not in cols:
                cursor.execute(
                    "ALTER TABLE programacion_semana ADD COLUMN fecha_inicio TEXT NOT NULL DEFAULT ''")
                conn.commit()
                print("Migración: columna fecha_inicio agregada a programacion_semana.")
        except Exception as e:
            print(f"Migración fecha_inicio omitida: {e}")

        try:
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(programacion_lineas)").fetchall()]
            if 'folio_pedido' not in cols:
                cursor.execute(
                    "ALTER TABLE programacion_lineas ADD COLUMN folio_pedido TEXT NOT NULL DEFAULT ''")
                conn.commit()
                print("Migración: columna folio_pedido agregada a programacion_lineas.")
        except Exception as e:
            print(f"Migración folio_pedido omitida: {e}")

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(programacion_lineas)").fetchall()]
            if 'pedido_id' not in cols:
                cursor.execute(
                    "ALTER TABLE programacion_lineas ADD COLUMN pedido_id INTEGER")
                print("Migración: columna pedido_id agregada a programacion_lineas.")
            if 'detalle_pedido_id' not in cols:
                cursor.execute(
                    "ALTER TABLE programacion_lineas ADD COLUMN detalle_pedido_id INTEGER")
                print("Migración: columna detalle_pedido_id agregada a programacion_lineas.")
            conn.commit()
        except Exception as e:
            print(f"Migración pedido_id omitida: {e}")

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cols = [r[1] for r in cursor.execute("PRAGMA table_info(pedidos_cliente)").fetchall()]
            if 'folio_pedido' not in cols:
                cursor.execute(
                    "ALTER TABLE pedidos_cliente ADD COLUMN folio_pedido TEXT NOT NULL DEFAULT ''")
                print("Migración: columna folio_pedido agregada a pedidos_cliente.")
            if 'suela' not in cols:
                cursor.execute(
                    "ALTER TABLE pedidos_cliente ADD COLUMN suela TEXT NOT NULL DEFAULT ''")
                print("Migración: columna suela agregada a pedidos_cliente.")
            if 'horma' not in cols:
                cursor.execute(
                    "ALTER TABLE pedidos_cliente ADD COLUMN horma TEXT NOT NULL DEFAULT ''")
                print("Migración: columna horma agregada a pedidos_cliente.")
            conn.commit()
        except Exception as e:
            print(f"Migración folio_pedido/suela/horma omitida: {e}")

        try:
            conn.commit()
            cursor.execute("PRAGMA foreign_keys=OFF")

            cursor.execute("DROP TABLE IF EXISTS ordenes_compra_old")

            info = cursor.execute("PRAGMA table_info(ordenes_compra)").fetchall()
            proveedor_col = next((c for c in info if c[1] == 'proveedor_id'), None)
            if proveedor_col and proveedor_col[3]:
                cursor.execute("ALTER TABLE ordenes_compra RENAME TO ordenes_compra_tmp")
                cursor.execute("""
                    CREATE TABLE ordenes_compra (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folio TEXT NOT NULL UNIQUE,
                        proveedor_id INTEGER REFERENCES proveedores(id),
                        fecha_emision TEXT NOT NULL DEFAULT (datetime('now')),
                        fecha_recibido TEXT,
                        estatus TEXT NOT NULL DEFAULT 'pendiente',
                        total REAL NOT NULL DEFAULT 0,
                        observaciones TEXT,
                        metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria',
                        solo_remision INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                cursor.execute(
                    "INSERT INTO ordenes_compra (id, folio, proveedor_id, fecha_emision, fecha_recibido, estatus, total, observaciones, metodo_pago, solo_remision, created_at) SELECT id, folio, proveedor_id, fecha_emision, fecha_recibido, estatus, total, observaciones, metodo_pago, solo_remision, created_at FROM ordenes_compra_tmp"
                )
                cursor.execute("DROP TABLE ordenes_compra_tmp")
                print("Migración: proveedor_id ahora es opcional en ordenes_compra.")

            cols = [r[1] for r in cursor.execute("PRAGMA table_info(detalle_orden_compra)").fetchall()]
            fks = cursor.execute("PRAGMA foreign_key_list(detalle_orden_compra)").fetchall()
            necesita_recrear = 'proveedor_id' not in cols or any(r[2] == 'ordenes_compra_old' for r in fks)
            if necesita_recrear:
                cursor.execute("ALTER TABLE detalle_orden_compra RENAME TO detalle_orden_compra_tmp")
                cursor.execute("""
                    CREATE TABLE detalle_orden_compra (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        orden_compra_id INTEGER NOT NULL REFERENCES ordenes_compra(id),
                        insumo_id INTEGER NOT NULL REFERENCES insumos(id),
                        cantidad REAL NOT NULL,
                        precio_unitario REAL NOT NULL,
                        proveedor_id INTEGER REFERENCES proveedores(id),
                        FOREIGN KEY (orden_compra_id) REFERENCES ordenes_compra(id),
                        FOREIGN KEY (insumo_id) REFERENCES insumos(id),
                        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
                    )
                """)
                cursor.execute(
                    "INSERT INTO detalle_orden_compra (id, orden_compra_id, insumo_id, cantidad, precio_unitario, proveedor_id) SELECT id, orden_compra_id, insumo_id, cantidad, precio_unitario, proveedor_id FROM detalle_orden_compra_tmp"
                )
                cursor.execute("DROP TABLE detalle_orden_compra_tmp")
                print("Migración: detalle_orden_compra con proveedor_id por renglón.")

            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()
        except Exception as e:
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            print(f"Migración OC omitida: {e}")

        try:
            conn.commit()
            cursor.execute("PRAGMA foreign_keys=OFF")

            cols = [r[1] for r in cursor.execute("PRAGMA table_info(ordenes_compra)").fetchall()]
            if 'metodo_pago' not in cols:
                cursor.execute(
                    "ALTER TABLE ordenes_compra ADD COLUMN metodo_pago TEXT NOT NULL DEFAULT 'Transferencia bancaria'")
                print("Migración: columna metodo_pago agregada a ordenes_compra.")
            if 'solo_remision' not in cols:
                cursor.execute(
                    "ALTER TABLE ordenes_compra ADD COLUMN solo_remision INTEGER NOT NULL DEFAULT 0")
                print("Migración: columna solo_remision agregada a ordenes_compra.")
            if 'tipo' not in cols:
                cursor.execute(
                    "ALTER TABLE ordenes_compra ADD COLUMN tipo TEXT NOT NULL DEFAULT 'orden'")
                print("Migración: columna tipo agregada a ordenes_compra.")

            cursor.execute("DROP TABLE IF EXISTS detalle_orden_compra_tallas")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_orden_compra_puntos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detalle_id INTEGER NOT NULL REFERENCES detalle_orden_compra(id) ON DELETE CASCADE,
                    talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
                    pares INTEGER NOT NULL DEFAULT 0,
                    precio_unitario REAL NOT NULL DEFAULT 0,
                    UNIQUE(detalle_id, talla_id),
                    FOREIGN KEY (detalle_id) REFERENCES detalle_orden_compra(id),
                    FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
                )
            """)

            puntos_cols = [r[1] for r in cursor.execute("PRAGMA table_info(detalle_orden_compra_puntos)").fetchall()]
            if 'precio_unitario' not in puntos_cols:
                cursor.execute(
                    "ALTER TABLE detalle_orden_compra_puntos ADD COLUMN precio_unitario REAL NOT NULL DEFAULT 0")
                print("Migración: columna precio_unitario agregada a detalle_orden_compra_puntos.")

            prov_cols = [r[1] for r in cursor.execute("PRAGMA table_info(proveedores)").fetchall()]
            if 'nombre_comercial' not in prov_cols:
                cursor.execute(
                    "ALTER TABLE proveedores ADD COLUMN nombre_comercial TEXT")
                print("Migración: columna nombre_comercial agregada a proveedores.")

            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()
        except Exception as e:
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            print(f"Migración tallas/pago omitida: {e}")

        self._migrar_tallas_unificadas()
        self._migrar_pedidos_tallas()
        self._migrar_impresiones_historico()
        self._migrar_fichas_tecnicas()
        self._migrar_movimientos_inventario()

    def _migrar_impresiones_historico(self) -> None:
        """Garantiza la tabla del histórico de la cola de impresión.

        Idempotente: si la tabla ya existe no hace nada (schema.sql la crea
        en instalaciones nuevas; esta migración cubre BD que ya existían).
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if self.engine == 'sqlite':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS impresiones_historico (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        supabase_id TEXT,
                        tipo TEXT NOT NULL DEFAULT 'partidas',
                        payload TEXT NOT NULL,
                        solicitado_en TEXT,
                        impreso_en TEXT NOT NULL DEFAULT (datetime('now')),
                        usuario TEXT,
                        reimpresiones INTEGER NOT NULL DEFAULT 0
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS impresiones_historico (
                        id SERIAL PRIMARY KEY,
                        supabase_id TEXT,
                        tipo TEXT NOT NULL DEFAULT 'partidas',
                        payload TEXT NOT NULL,
                        solicitado_en TEXT,
                        impreso_en TIMESTAMP NOT NULL DEFAULT NOW(),
                        usuario TEXT,
                        reimpresiones INTEGER NOT NULL DEFAULT 0
                    )
                """)
            conn.commit()
        except Exception as e:
            print(f"Migración impresiones_historico omitida: {e}")

    def _migrar_fichas_tecnicas(self) -> None:
        """Garantiza las tablas de la ficha técnica por modelo.

        Idempotente: si las tablas ya existen no hace nada (schema.sql las
        crea en instalaciones nuevas; esta migración cubre BD que ya existían).
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if self.engine == 'sqlite':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fichas_tecnicas (
                        modelo_id INTEGER PRIMARY KEY REFERENCES modelos(id),
                        proyecto TEXT NOT NULL DEFAULT '',
                        etapa TEXT NOT NULL DEFAULT 'MUESTRA',
                        id_diseno TEXT NOT NULL DEFAULT '',
                        ref_cliente TEXT NOT NULL DEFAULT '',
                        color_nombre TEXT NOT NULL DEFAULT '',
                        cintilla TEXT DEFAULT '',
                        carnuza_chinela TEXT DEFAULT '',
                        forro TEXT DEFAULT '',
                        piel_corte_1 TEXT DEFAULT '',
                        piel_corte_2 TEXT DEFAULT '',
                        piel_corte_3 TEXT DEFAULT '',
                        piel_corte_4 TEXT DEFAULT '',
                        entretela_tubo TEXT DEFAULT '',
                        entretela_chinela TEXT DEFAULT '',
                        entretela_talon TEXT DEFAULT '',
                        rebajado_tubo TEXT DEFAULT '',
                        rebajado_chinela TEXT DEFAULT '',
                        rebajado_talon TEXT DEFAULT '',
                        bordado_tubo TEXT DEFAULT '',
                        bordado_chinela TEXT DEFAULT '',
                        bordado_calzador TEXT DEFAULT '',
                        bordado_oreja TEXT DEFAULT '',
                        bordado_logo TEXT DEFAULT '',
                        hilo_bordado_tubo TEXT DEFAULT '',
                        hilo_bordado_chinela TEXT DEFAULT '',
                        hilo_bordado_calzador TEXT DEFAULT '',
                        hilo_bordado_oreja TEXT DEFAULT '',
                        hilo_logo TEXT DEFAULT '',
                        hilo_armado TEXT DEFAULT '',
                        hilo_sobrecostura TEXT DEFAULT '',
                        vivo TEXT DEFAULT '',
                        ribete TEXT DEFAULT '',
                        estoperol TEXT DEFAULT '',
                        herraje TEXT DEFAULT '',
                        acc_1 TEXT DEFAULT '',
                        acc_2 TEXT DEFAULT '',
                        acc_3 TEXT DEFAULT '',
                        acc_4 TEXT DEFAULT '',
                        puntera TEXT DEFAULT '',
                        planta TEXT DEFAULT '',
                        contrafuerte TEXT DEFAULT '',
                        casco TEXT DEFAULT '',
                        suela TEXT DEFAULT '',
                        cambrellon TEXT DEFAULT '',
                        cerco TEXT DEFAULT '',
                        herradura TEXT DEFAULT '',
                        landis TEXT DEFAULT '',
                        espinazo TEXT DEFAULT '',
                        firme TEXT DEFAULT '',
                        tacon TEXT DEFAULT '',
                        stein TEXT DEFAULT '',
                        acabado TEXT DEFAULT '',
                        cierre TEXT DEFAULT '',
                        cantos TEXT DEFAULT '',
                        plantilla TEXT DEFAULT '',
                        transfer TEXT DEFAULT '',
                        caja TEXT DEFAULT '',
                        serigrafia TEXT DEFAULT '',
                        bolsa TEXT DEFAULT '',
                        soporte TEXT DEFAULT '',
                        asadera TEXT DEFAULT '',
                        papel_relleno TEXT DEFAULT '',
                        colgante TEXT DEFAULT '',
                        grabado_suela TEXT DEFAULT '',
                        barranca TEXT DEFAULT '',
                        comentarios TEXT DEFAULT '',
                        realizo TEXT DEFAULT '',
                        recibio TEXT DEFAULT '',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ficha_tecnica_fotos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        modelo_id INTEGER NOT NULL REFERENCES modelos(id)
                            ON DELETE CASCADE,
                        tipo_foto TEXT NOT NULL CHECK(tipo_foto IN
                            ('producto','tubo','chinela','talon','suela')),
                        imagen BLOB,
                        UNIQUE(modelo_id, tipo_foto)
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fichas_tecnicas (
                        modelo_id BIGINT PRIMARY KEY REFERENCES modelos(id),
                        proyecto TEXT NOT NULL DEFAULT '',
                        etapa TEXT NOT NULL DEFAULT 'MUESTRA',
                        id_diseno TEXT NOT NULL DEFAULT '',
                        ref_cliente TEXT NOT NULL DEFAULT '',
                        color_nombre TEXT NOT NULL DEFAULT '',
                        cintilla TEXT DEFAULT '',
                        carnuza_chinela TEXT DEFAULT '',
                        forro TEXT DEFAULT '',
                        piel_corte_1 TEXT DEFAULT '',
                        piel_corte_2 TEXT DEFAULT '',
                        piel_corte_3 TEXT DEFAULT '',
                        piel_corte_4 TEXT DEFAULT '',
                        entretela_tubo TEXT DEFAULT '',
                        entretela_chinela TEXT DEFAULT '',
                        entretela_talon TEXT DEFAULT '',
                        rebajado_tubo TEXT DEFAULT '',
                        rebajado_chinela TEXT DEFAULT '',
                        rebajado_talon TEXT DEFAULT '',
                        bordado_tubo TEXT DEFAULT '',
                        bordado_chinela TEXT DEFAULT '',
                        bordado_calzador TEXT DEFAULT '',
                        bordado_oreja TEXT DEFAULT '',
                        bordado_logo TEXT DEFAULT '',
                        hilo_bordado_tubo TEXT DEFAULT '',
                        hilo_bordado_chinela TEXT DEFAULT '',
                        hilo_bordado_calzador TEXT DEFAULT '',
                        hilo_bordado_oreja TEXT DEFAULT '',
                        hilo_logo TEXT DEFAULT '',
                        hilo_armado TEXT DEFAULT '',
                        hilo_sobrecostura TEXT DEFAULT '',
                        vivo TEXT DEFAULT '',
                        ribete TEXT DEFAULT '',
                        estoperol TEXT DEFAULT '',
                        herraje TEXT DEFAULT '',
                        acc_1 TEXT DEFAULT '',
                        acc_2 TEXT DEFAULT '',
                        acc_3 TEXT DEFAULT '',
                        acc_4 TEXT DEFAULT '',
                        puntera TEXT DEFAULT '',
                        planta TEXT DEFAULT '',
                        contrafuerte TEXT DEFAULT '',
                        casco TEXT DEFAULT '',
                        suela TEXT DEFAULT '',
                        cambrellon TEXT DEFAULT '',
                        cerco TEXT DEFAULT '',
                        herradura TEXT DEFAULT '',
                        landis TEXT DEFAULT '',
                        espinazo TEXT DEFAULT '',
                        firme TEXT DEFAULT '',
                        tacon TEXT DEFAULT '',
                        stein TEXT DEFAULT '',
                        acabado TEXT DEFAULT '',
                        cierre TEXT DEFAULT '',
                        cantos TEXT DEFAULT '',
                        plantilla TEXT DEFAULT '',
                        transfer TEXT DEFAULT '',
                        caja TEXT DEFAULT '',
                        serigrafia TEXT DEFAULT '',
                        bolsa TEXT DEFAULT '',
                        soporte TEXT DEFAULT '',
                        asadera TEXT DEFAULT '',
                        papel_relleno TEXT DEFAULT '',
                        colgante TEXT DEFAULT '',
                        grabado_suela TEXT DEFAULT '',
                        barranca TEXT DEFAULT '',
                        comentarios TEXT DEFAULT '',
                        realizo TEXT DEFAULT '',
                        recibio TEXT DEFAULT '',
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ficha_tecnica_fotos (
                        id BIGSERIAL PRIMARY KEY,
                        modelo_id BIGINT NOT NULL REFERENCES modelos(id)
                            ON DELETE CASCADE,
                        tipo_foto TEXT NOT NULL CHECK(tipo_foto IN
                            ('producto','tubo','chinela','talon','suela')),
                        imagen BYTEA,
                        UNIQUE(modelo_id, tipo_foto)
                    )
                """)
            conn.commit()
        except Exception as e:
            print(f"Migración fichas_tecnicas omitida: {e}")

    def _migrar_movimientos_inventario(self) -> None:
        """Garantiza las tablas de movimientos de inventario multi-partida."""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if self.engine == 'sqlite':
                tablas = {r[0] for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            else:
                tablas = {r[0] for r in cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'").fetchall()}
            if 'movimientos_inventario' not in tablas:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movimientos_inventario (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folio TEXT NOT NULL UNIQUE,
                        tipo_movimiento TEXT NOT NULL
                            CHECK(tipo_movimiento IN ('salida','cambio_ubicacion')),
                        observaciones TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
            if 'detalle_movimiento_inventario' not in tablas:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detalle_movimiento_inventario (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        movimiento_id INTEGER NOT NULL
                            REFERENCES movimientos_inventario(id),
                        insumo_id INTEGER NOT NULL REFERENCES insumos(id),
                        cantidad REAL NOT NULL,
                        observaciones TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
            conn.commit()
        except Exception as e:
            print(f"Migración movimientos_inventario omitida: {e}")

    def _migrar_tallas_unificadas(self) -> None:
        """RD-1: fusiona `puntos_catalogo` + `tallas_corrida` en `tallas_catalogo`.

        Crea el catálogo unificado (sin campo `orden`), fusiona los valores de
        ambos catálogos históricos y remapea las tablas de detalle
        (`detalle_orden_compra_puntos`, `matriz_tallas_op`, `inventario_pt`)
        para que apunten a `tallas_catalogo`. Idempotente y no destructivo:
        si los catálogos históricos ya no existen, no hace nada.
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            def tabla_existe(nombre: str) -> bool:
                if self.engine == 'sqlite':
                    row = cursor.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nombre,),
                    ).fetchone()
                    return row is not None
                row = cursor.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name=%s",
                    (nombre,),
                ).fetchone()
                return row is not None

            existe_puntos = tabla_existe('puntos_catalogo')
            existe_corrida = tabla_existe('tallas_corrida')
            if not existe_puntos and not existe_corrida:
                return

            if self.engine == 'sqlite':
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS tallas_catalogo ("
                    " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    " talla TEXT NOT NULL UNIQUE,"
                    " activo INTEGER NOT NULL DEFAULT 1)")
            else:
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS tallas_catalogo ("
                    " id SERIAL PRIMARY KEY,"
                    " talla TEXT NOT NULL UNIQUE,"
                    " activo INTEGER NOT NULL DEFAULT 1)")

            if self.engine == 'sqlite':
                # SQLite no soporta ON CONFLICT con INSERT...SELECT:
                # se usa INSERT OR IGNORE y luego se propaga el estado `activo`.
                if existe_puntos:
                    cursor.execute(
                        "INSERT OR IGNORE INTO tallas_catalogo (talla, activo) "
                        "SELECT punto, activo FROM puntos_catalogo")
                    cursor.execute(
                        "UPDATE tallas_catalogo SET activo = "
                        "(SELECT p.activo FROM puntos_catalogo p "
                        " WHERE p.punto = tallas_catalogo.talla) "
                        "WHERE talla IN (SELECT punto FROM puntos_catalogo)")
                if existe_corrida:
                    cursor.execute(
                        "INSERT OR IGNORE INTO tallas_catalogo (talla, activo) "
                        "SELECT talla, 1 FROM tallas_corrida")
            else:
                # PostgreSQL: ON CONFLICT (talla) DO NOTHING es la sintaxis válida.
                if existe_puntos:
                    cursor.execute(
                        "INSERT INTO tallas_catalogo (talla, activo) "
                        "SELECT punto, activo FROM puntos_catalogo "
                        "ON CONFLICT (talla) DO NOTHING")
                    cursor.execute(
                        "UPDATE tallas_catalogo SET activo = "
                        "(SELECT p.activo FROM puntos_catalogo p "
                        " WHERE p.punto = tallas_catalogo.talla) "
                        "WHERE talla IN (SELECT punto FROM puntos_catalogo)")
                if existe_corrida:
                    cursor.execute(
                        "INSERT INTO tallas_catalogo (talla, activo) "
                        "SELECT talla, 1 FROM tallas_corrida "
                        "ON CONFLICT (talla) DO NOTHING")
            conn.commit()

            # Reintento seguro: si una corrida anterior falló a mitad del
            # remapeo, la tabla vieja quedó como *_old. En el siguiente
            # arranque schema.sql pudo recrear la tabla principal vacía;
            # se restaura la *_old (con sus datos) para volver a intentar.
            if self.engine == 'sqlite':
                for nombre, sufijo in (
                    ("detalle_orden_compra_puntos", "detalle_orden_compra_puntos_old"),
                    ("matriz_tallas_op", "matriz_tallas_op_old"),
                    ("inventario_pt", "inventario_pt_old"),
                ):
                    if not tabla_existe(sufijo):
                        continue
                    if not tabla_existe(nombre):
                        cursor.execute(
                            f"ALTER TABLE {sufijo} RENAME TO {nombre}")
                        print(f"Migración RD-1: restaurada {nombre} tras reintento.")
                        continue
                    filas = cursor.execute(
                        f"SELECT COUNT(*) FROM {nombre}").fetchone()[0]
                    if filas == 0:
                        # La principal fue recreada vacía por schema.sql:
                        # se reemplaza por la *_old para no perder datos.
                        cursor.execute(f"DROP TABLE {nombre}")
                        cursor.execute(
                            f"ALTER TABLE {sufijo} RENAME TO {nombre}")
                        print(f"Migración RD-1: restaurada {nombre} tras reintento.")
                    else:
                        # La principal ya tiene datos (migración completa
                        # previa): la *_old es residuo y se descarta.
                        cursor.execute(f"DROP TABLE {sufijo}")
                conn.commit()

            if self.engine == 'sqlite':
                cursor.execute("PRAGMA foreign_keys=OFF")
                if existe_puntos:
                    cursor.execute(
                        "ALTER TABLE detalle_orden_compra_puntos "
                        "RENAME TO detalle_orden_compra_puntos_old")
                    cursor.execute("""
                        CREATE TABLE detalle_orden_compra_puntos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            detalle_id INTEGER NOT NULL
                                REFERENCES detalle_orden_compra(id) ON DELETE CASCADE,
                            talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
                            pares INTEGER NOT NULL DEFAULT 0,
                            precio_unitario REAL NOT NULL DEFAULT 0,
                            UNIQUE(detalle_id, talla_id),
                            FOREIGN KEY (detalle_id) REFERENCES detalle_orden_compra(id),
                            FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO detalle_orden_compra_puntos
                            (id, detalle_id, talla_id, pares, precio_unitario)
                        SELECT d.id, d.detalle_id, t.id, d.pares, d.precio_unitario
                        FROM detalle_orden_compra_puntos_old d
                        JOIN puntos_catalogo p ON p.id = d.punto_id
                        JOIN tallas_catalogo t ON t.talla = p.punto
                    """)
                    cursor.execute("DROP TABLE detalle_orden_compra_puntos_old")
                    print("Migración RD-1: detalle_orden_compra_puntos -> talla_id.")

                if existe_corrida:
                    cursor.execute(
                        "ALTER TABLE matriz_tallas_op RENAME TO matriz_tallas_op_old")
                    cursor.execute("""
                        CREATE TABLE matriz_tallas_op (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            orden_produccion_id INTEGER NOT NULL
                                REFERENCES ordenes_produccion(id),
                            talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
                            pares INTEGER NOT NULL DEFAULT 0,
                            FOREIGN KEY (orden_produccion_id)
                                REFERENCES ordenes_produccion(id),
                            FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO matriz_tallas_op
                            (id, orden_produccion_id, talla_id, pares)
                        SELECT m.id, m.orden_produccion_id, t.id, m.pares
                        FROM matriz_tallas_op_old m
                        JOIN tallas_corrida tc ON tc.id = m.talla_id
                        JOIN tallas_catalogo t ON t.talla = tc.talla
                    """)
                    cursor.execute("DROP TABLE matriz_tallas_op_old")

                    cursor.execute(
                        "ALTER TABLE inventario_pt RENAME TO inventario_pt_old")
                    cursor.execute("""
                        CREATE TABLE inventario_pt (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            variante_id INTEGER NOT NULL REFERENCES variantes(id),
                            talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
                            pares INTEGER NOT NULL DEFAULT 0,
                            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                            FOREIGN KEY (variante_id) REFERENCES variantes(id),
                            FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
                        )
                    """)
                    cursor.execute("""
                        INSERT INTO inventario_pt
                            (id, variante_id, talla_id, pares, updated_at)
                        SELECT i.id, i.variante_id, t.id, i.pares, i.updated_at
                        FROM inventario_pt_old i
                        JOIN tallas_corrida tc ON tc.id = i.talla_id
                        JOIN tallas_catalogo t ON t.talla = tc.talla
                    """)
                    cursor.execute("DROP TABLE inventario_pt_old")
                    print("Migración RD-1: matriz_tallas_op/inventario_pt -> tallas_catalogo.")

                cursor.execute("DROP TABLE IF EXISTS puntos_catalogo")
                cursor.execute("DROP TABLE IF EXISTS tallas_corrida")
                cursor.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                print("Migración RD-1: catálogo unificado tallas_catalogo aplicado.")
            else:
                if existe_puntos:
                    cursor.execute(
                        "ALTER TABLE detalle_orden_compra_puntos "
                        "RENAME COLUMN punto_id TO talla_id")
                    cursor.execute("""
                        UPDATE detalle_orden_compra_puntos d
                        SET talla_id = t.id
                        FROM puntos_catalogo p, tallas_catalogo t
                        WHERE p.id = d.talla_id AND t.talla = p.punto
                    """)
                    cursor.execute(
                        "ALTER TABLE detalle_orden_compra_puntos "
                        "DROP CONSTRAINT IF EXISTS "
                        "detalle_orden_compra_puntos_punto_id_fkey")
                    cursor.execute(
                        "ALTER TABLE detalle_orden_compra_puntos "
                        "ADD CONSTRAINT detalle_orden_compra_puntos_talla_id_fkey "
                        "FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)")
                if existe_corrida:
                    cursor.execute("""
                        UPDATE matriz_tallas_op m
                        SET talla_id = t.id
                        FROM tallas_corrida tc, tallas_catalogo t
                        WHERE tc.id = m.talla_id AND t.talla = tc.talla
                    """)
                    cursor.execute(
                        "ALTER TABLE matriz_tallas_op "
                        "DROP CONSTRAINT IF EXISTS matriz_tallas_op_talla_id_fkey")
                    cursor.execute(
                        "ALTER TABLE matriz_tallas_op "
                        "ADD CONSTRAINT matriz_tallas_op_talla_id_fkey "
                        "FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)")
                    cursor.execute("""
                        UPDATE inventario_pt i
                        SET talla_id = t.id
                        FROM tallas_corrida tc, tallas_catalogo t
                        WHERE tc.id = i.talla_id AND t.talla = tc.talla
                    """)
                    cursor.execute(
                        "ALTER TABLE inventario_pt "
                        "DROP CONSTRAINT IF EXISTS inventario_pt_talla_id_fkey")
                    cursor.execute(
                        "ALTER TABLE inventario_pt "
                        "ADD CONSTRAINT inventario_pt_talla_id_fkey "
                        "FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)")
                cursor.execute("DROP TABLE IF EXISTS puntos_catalogo")
                cursor.execute("DROP TABLE IF EXISTS tallas_corrida")
                conn.commit()
                print("Migración RD-1: catálogo unificado tallas_catalogo aplicado (PG).")
        except Exception as e:
            try:
                if self.engine == 'sqlite':
                    cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            print(f"Migración RD-1 tallas_catalogo omitida: {e}")
    def _migrar_logs(self) -> None:
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL DEFAULT (datetime('now')),
                    usuario_id INTEGER,
                    usuario TEXT,
                    modulo TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    entidad TEXT,
                    entidad_id INTEGER,
                    nivel TEXT NOT NULL DEFAULT 'info',
                    detalle TEXT,
                    datos TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_fecha ON logs_sistema (fecha)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_modulo ON logs_sistema (modulo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_entidad ON logs_sistema (entidad, entidad_id)")
            conn.commit()
        except Exception as e:
            print(f"Migración logs omitida: {e}")
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO permisos (modulo, accion, descripcion) "
                "VALUES ('programacion', 'crear', 'Crear líneas de programación'), "
                "('programacion', 'eliminar', 'Eliminar líneas de la programación')")
            conn.commit()
        except Exception as e:
            print(f"Migración permisos programación omitida: {e}")

    def _migrar_pedidos_tallas(self) -> None:
        """RD-1b: remapea `detalle_pedido_cliente_puntos` a `tallas_catalogo`.

        El módulo de clientes (pedidos) quedó con el esquema antiguo
        (`punto_id` -> `puntos_catalogo`) después de la unificación RD-1.
        Reconstruye la tabla con `talla_id` -> `tallas_catalogo`, conservando
        las filas cuyo `punto_id` exista en `tallas_catalogo` (los id de
        catálogos regenerados que se descartaron no tienen talla recuperable).
        Idempotente: si la tabla ya usa `talla_id`, no hace nada.
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            def tabla_existe(nombre: str) -> bool:
                if self.engine == 'sqlite':
                    return cursor.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (nombre,),
                    ).fetchone() is not None
                return cursor.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name=%s",
                    (nombre,),
                ).fetchone() is not None

            if not tabla_existe('detalle_pedido_cliente_puntos'):
                return

            # Reintento seguro: si una corrida anterior falló a mitad, la tabla
            # vieja quedó como *_old y schema.sql pudo recrear la principal.
            if self.engine == 'sqlite' and tabla_existe(
                    'detalle_pedido_cliente_puntos_old'):
                cursor.execute("PRAGMA foreign_keys=OFF")
                if not tabla_existe('detalle_pedido_cliente_puntos'):
                    cursor.execute(
                        "ALTER TABLE detalle_pedido_cliente_puntos_old "
                        "RENAME TO detalle_pedido_cliente_puntos")
                    print("Migración RD-1b: restaurada tabla tras reintento.")
                else:
                    filas = cursor.execute(
                        "SELECT COUNT(*) FROM detalle_pedido_cliente_puntos"
                    ).fetchone()[0]
                    if filas == 0:
                        cursor.execute("DROP TABLE detalle_pedido_cliente_puntos")
                        cursor.execute(
                            "ALTER TABLE detalle_pedido_cliente_puntos_old "
                            "RENAME TO detalle_pedido_cliente_puntos")
                        print("Migración RD-1b: restaurada tabla tras reintento.")
                    else:
                        cursor.execute("DROP TABLE detalle_pedido_cliente_puntos_old")
                cursor.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                return

            if self.engine == 'sqlite':
                cols = [r[1] for r in cursor.execute(
                    "PRAGMA table_info(detalle_pedido_cliente_puntos)").fetchall()]
                if 'talla_id' in cols:
                    return
                cursor.execute("PRAGMA foreign_keys=OFF")
                cursor.execute(
                    "ALTER TABLE detalle_pedido_cliente_puntos "
                    "RENAME TO detalle_pedido_cliente_puntos_old")
                cursor.execute("""
                    CREATE TABLE detalle_pedido_cliente_puntos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        detalle_id INTEGER NOT NULL
                            REFERENCES detalle_pedido_cliente(id) ON DELETE CASCADE,
                        talla_id INTEGER NOT NULL REFERENCES tallas_catalogo(id),
                        pares INTEGER NOT NULL DEFAULT 0,
                        UNIQUE(detalle_id, talla_id),
                        FOREIGN KEY (detalle_id) REFERENCES detalle_pedido_cliente(id),
                        FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)
                    )
                """)
                cursor.execute("""
                    INSERT INTO detalle_pedido_cliente_puntos
                        (id, detalle_id, talla_id, pares)
                    SELECT d.id, d.detalle_id, t.id, d.pares
                    FROM detalle_pedido_cliente_puntos_old d
                    JOIN tallas_catalogo t ON t.id = d.punto_id
                """)
                total_antes = cursor.execute(
                    "SELECT COUNT(*) FROM detalle_pedido_cliente_puntos_old"
                ).fetchone()[0]
                conservadas = cursor.execute(
                    "SELECT COUNT(*) FROM detalle_pedido_cliente_puntos"
                ).fetchone()[0]
                cursor.execute("DROP TABLE detalle_pedido_cliente_puntos_old")
                cursor.execute("PRAGMA foreign_keys=ON")
                conn.commit()
                print(f"Migración RD-1b: detalle_pedido_cliente_puntos -> "
                      f"tallas_catalogo ({conservadas}/{total_antes} filas conservadas).")
            else:
                # PostgreSQL: renombrar columna, re-apuntar a tallas_catalogo.
                cols = [r[0] for r in cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='detalle_pedido_cliente_puntos'")]
                if 'talla_id' in cols:
                    return
                cursor.execute(
                    "ALTER TABLE detalle_pedido_cliente_puntos "
                    "RENAME COLUMN punto_id TO talla_id")
                cursor.execute("""
                    DELETE FROM detalle_pedido_cliente_puntos d
                    WHERE NOT EXISTS (SELECT 1 FROM tallas_catalogo t
                                      WHERE t.id = d.talla_id)
                """)
                cursor.execute(
                    "ALTER TABLE detalle_pedido_cliente_puntos "
                    "DROP CONSTRAINT IF EXISTS "
                    "detalle_pedido_cliente_puntos_punto_id_fkey")
                cursor.execute(
                    "ALTER TABLE detalle_pedido_cliente_puntos "
                    "ADD CONSTRAINT detalle_pedido_cliente_puntos_talla_id_fkey "
                    "FOREIGN KEY (talla_id) REFERENCES tallas_catalogo(id)")
                conn.commit()
                print("Migración RD-1b: detalle_pedido_cliente_puntos -> "
                      "tallas_catalogo aplicado (PG).")
        except Exception as e:
            try:
                if self.engine == 'sqlite':
                    cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            print(f"Migración pedidos->tallas_catalogo omitida: {e}")

    def _migrar_passwords(self) -> None:
        from src.utils.security import es_hash_bcrypt, hash_contrasena
        try:
            conn = self.connect()
            cursor = conn.cursor()
            ph = "%s" if self.engine == 'postgresql' else "?"
            filas = cursor.execute("SELECT id, password_hash FROM usuarios").fetchall()
            migradas = 0
            for usuario_id, almacenado in filas:
                if almacenado and not es_hash_bcrypt(almacenado):
                    cursor.execute(
                        f"UPDATE usuarios SET password_hash = {ph} WHERE id = {ph}",
                        (hash_contrasena(almacenado), usuario_id),
                    )
                    migradas += 1
            conn.commit()
            if migradas:
                print(f"Migración: {migradas} contraseña(s) migradas a bcrypt.")
        except Exception as e:
            print(f"Migración de contraseñas omitida: {e}")
        self._migrar_configuracion_empresa()

    def _migrar_configuracion_empresa(self) -> None:
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if self.engine == 'sqlite':
                tablas = {r[0] for r in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()}
            else:
                tablas = {r[0] for r in cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public'"
                ).fetchall()}
            if 'configuracion_empresa' not in tablas:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS configuracion_empresa (
                        clave TEXT PRIMARY KEY,
                        valor TEXT NOT NULL DEFAULT '',
                        tipo TEXT NOT NULL DEFAULT 'texto',
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)
                for clave, valor, tipo in (
                    ('nombre_empresa', '', 'texto'),
                    ('razon_social', '', 'texto'),
                    ('logo', '', 'imagen'),
                    ('video_splash', '', 'archivo'),
                ):
                    cursor.execute(
                        "INSERT OR IGNORE INTO configuracion_empresa "
                        "(clave, valor, tipo) VALUES (?, ?, ?)",
                        (clave, valor, tipo),
                    )
                conn.commit()
                print("Migración: tabla configuracion_empresa creada.")
        except Exception as e:
            print(f"Migración configuracion_empresa omitida: {e}")
