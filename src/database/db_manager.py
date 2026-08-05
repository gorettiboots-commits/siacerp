import configparser
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional


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
        config_path = Path(__file__).resolve().parent.parent.parent / 'config.ini'
        config.read(str(config_path))
        return config

    @property
    def db_path(self) -> str:
        base = Path(__file__).resolve().parent.parent.parent
        sqlite_path = self.config.get('database', 'sqlite_path')
        return str(base / sqlite_path)

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

            cursor.execute("DROP TABLE IF EXISTS detalle_orden_compra_tallas")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_orden_compra_puntos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detalle_id INTEGER NOT NULL REFERENCES detalle_orden_compra(id) ON DELETE CASCADE,
                    punto_id INTEGER NOT NULL REFERENCES puntos_catalogo(id),
                    pares INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(detalle_id, punto_id),
                    FOREIGN KEY (detalle_id) REFERENCES detalle_orden_compra(id),
                    FOREIGN KEY (punto_id) REFERENCES puntos_catalogo(id)
                )
            """)

            cursor.execute("PRAGMA foreign_keys=ON")
            conn.commit()
        except Exception as e:
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass
            print(f"Migración tallas/pago omitida: {e}")
