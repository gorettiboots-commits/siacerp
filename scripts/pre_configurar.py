#!/usr/bin/env python3
"""Pre-configuración de SIAC ERP para el instalador.

Inicializa la base de datos y configura los datos de la empresa
desde la línea de comandos. Diseñado para ser ejecutado por Inno Setup
durante la instalación.

Uso:
    python pre_configurar.py \
        --nombre "Goretti Calzado" \
        --razon "Goretti Calzado S.A. de C.V." \
        --rfc "GCA123456XX0" \
        --domicilio "Av. Industrial #123" \
        --telefono "55 1234 5678" \
        --email "contacto@goretti.com"

También acepta PostgreSQL:
    python pre_configurar.py --db-engine postgresql --pg-host localhost ...
"""

import argparse
import configparser
import os
import sys
from pathlib import Path


def _directorio_datos() -> Path:
    """Directorio de datos: %APPDATA%\\SIAC en Windows."""
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "SIAC"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _crear_config(args: argparse.Namespace) -> Path:
    """Crea config.ini con los parámetros del instalador."""
    datos = _directorio_datos()
    config = configparser.ConfigParser()

    config["database"] = {
        "engine": args.db_engine,
        "sqlite_path": args.sqlite_path,
    }
    if args.db_engine == "postgresql":
        config["database"]["pg_host"] = args.pg_host
        config["database"]["pg_port"] = str(args.pg_port)
        config["database"]["pg_user"] = args.pg_user
        config["database"]["pg_password"] = args.pg_password
        config["database"]["pg_database"] = args.pg_database

    config["app"] = {
        "company_name": args.nombre,
        "app_title": "SIAC ERP",
        "version": "1.0.0",
    }

    ruta = datos / "config.ini"
    with open(str(ruta), "w", encoding="utf-8") as f:
        config.write(f)
    print(f"config.ini creado en: {ruta}")
    return ruta


def _inicializar_bd(args: argparse.Namespace) -> None:
    """Ejecuta el esquema SQL para crear las tablas."""
    # Importar DatabaseManager (funciona tanto en .py como en .exe empaquetado)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.initialize_schema()
        print("Base de datos inicializada correctamente.")
    except ImportError:
        # Si estamos empaquetados, intentar desde el directorio del .exe
        exe_dir = Path(sys.executable).parent
        schema = exe_dir / "src" / "database" / "schema.sql"
        if schema.exists():
            print(f"Ejecutando esquema desde: {schema}")
            _ejecutar_schema_directo(schema, args.db_engine)
        else:
            print("ADVERTENCIA: No se pudo inicializar la BD desde pre-config.")
            print("El esquema se creará al abrir la app por primera vez.")


def _ejecutar_schema_directo(schema_path: Path, engine: str) -> None:
    """Ejecuta schema.sql directamente sin DatabaseManager."""
    sql_text = schema_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    if engine == "sqlite":
        import sqlite3
        datos = _directorio_datos()
        conn = sqlite3.connect(str(datos / "goretti_erp.db"))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
    else:
        print("ADVERTENCIA: Para PostgreSQL, ejecute la app para crear el esquema.")
        return

    cursor = conn.cursor()
    for stmt in statements:
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"  Aviso: {stmt[:60]}... -> {e}")
    conn.commit()
    conn.close()


def _guardar_empresa(args: argparse.Namespace) -> None:
    """Inserta los datos de empresa en la tabla configuracion_empresa."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from src.database.db_manager import DatabaseManager
        from src.models.empresa_model import EmpresaModel
    except ImportError:
        print("ADVERTENCIA: No se pudo importar EmpresaModel.")
        print("Los datos de empresa se configurarán al abrir la app.")
        return

    db = DatabaseManager()
    model = EmpresaModel()

    datos = {
        "nombre_empresa": args.nombre,
        "razon_social": args.razon or args.nombre,
        "rfc": args.rfc or "",
        "domicilio": args.domicilio or "",
        "telefono": args.telefono or "",
        "email": args.email or "",
    }

    model.guardar_varias(datos)
    print(f"Datos de empresa guardados: {args.nombre}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-configuración de SIAC ERP para instalador")
    # Datos de empresa
    parser.add_argument("--nombre", required=True,
                        help="Nombre de la empresa")
    parser.add_argument("--razon", default="",
                        help="Razón social")
    parser.add_argument("--rfc", default="",
                        help="RFC")
    parser.add_argument("--domicilio", default="",
                        help="Domicilio")
    parser.add_argument("--telefono", default="",
                        help="Teléfono")
    parser.add_argument("--email", default="",
                        help="Email")

    # Usuario admin
    parser.add_argument("--admin-user", default="admin",
                        help="Nombre de usuario admin")
    parser.add_argument("--admin-password", default="admin123",
                        help="Contrasena del usuario admin")
    parser.add_argument("--admin-nombre", default="Administrador del Sistema",
                        help="Nombre completo del admin")

    # Configuración de BD
    parser.add_argument("--db-engine", default="sqlite",
                        choices=["sqlite", "postgresql"],
                        help="Motor de base de datos")
    parser.add_argument("--sqlite-path", default="goretti_erp.db",
                        help="Ruta del archivo SQLite")
    parser.add_argument("--pg-host", default="localhost")
    parser.add_argument("--pg-port", type=int, default=5432)
    parser.add_argument("--pg-user", default="postgres")
    parser.add_argument("--pg-password", default="")
    parser.add_argument("--pg-database", default="goretti_erp")

    args = parser.parse_args()

    print("=" * 50)
    print("  SIAC ERP — Pre-configuración")
    print("=" * 50)
    print()

    # 1. Crear config.ini
    _crear_config(args)

    # 2. Inicializar BD
    _inicializar_bd(args)

    # 3. Guardar datos de empresa
    _guardar_empresa(args)

    print()
    # 4. Crear usuario admin
    _crear_admin(args)

    print()
    print("Pre-configuración completada exitosamente.")
    print(f"Datos en: {_directorio_datos()}")


def _crear_admin(args: argparse.Namespace) -> None:
    """Crea o actualiza el usuario admin con permisos completos."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from src.models.accesos_model import UsuarioModel, PermisosModel
    except ImportError:
        print("ADVERTENCIA: No se pudo importar UsuarioModel.")
        print("El usuario admin se creará al abrir la app.")
        return

    user_model = UsuarioModel()
    perm_model = PermisosModel()

    # --- Usuario admin (general) ---
    existing = user_model.obtener_por_username(args.admin_user)
    if not existing:
        admin_id = user_model.crear(
            args.admin_user, args.admin_password,
            args.admin_nombre, "admin")
        perm_model.guardar(admin_id, perm_model.claves_totales())
        print(f"Usuario admin creado: {args.admin_user}")
    else:
        user_model.cambiar_password(existing["id"], args.admin_password)
        user_model.actualizar(
            existing["id"], args.admin_user, args.admin_nombre, "admin")
        print(f"Usuario admin actualizado: {args.admin_user}")


if __name__ == "__main__":
    main()
