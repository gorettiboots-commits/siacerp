import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLineEdit

_orig_le_init = QLineEdit.__init__


def _patched_le_init(self, *args, **kwargs):
    _orig_le_init(self, *args, **kwargs)
    self.setCompleter(None)
    self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, False)


QLineEdit.__init__ = _patched_le_init

from src.components.campo_historico import InstaladorHistorico
from src.database.db_manager import DatabaseManager
from src.utils.ui_helpers import instalar_adaptador_resolucion_global, load_styles
from src.views.main_window import MainWindow


def _pre_configurar() -> bool:
    """Modo pre-configuración para el instalador.

    Si se ejecuta con --pre-configurar, inicializa la BD y guarda los
    datos de empresa sin abrir la interfaz gráfica. Devuelve True si
    se procesó este modo (para que main() salga).
    """
    args = sys.argv
    if "--pre-configurar" not in args:
        return False

    import argparse
    parser = argparse.ArgumentParser(
        description="Pre-configuración de SIAC ERP")
    parser.add_argument("--pre-configurar", action="store_true",
                        help="Modo pre-configuración (instalador)")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--razon", default="")
    parser.add_argument("--rfc", default="")
    parser.add_argument("--domicilio", default="")
    parser.add_argument("--telefono", default="")
    parser.add_argument("--email", default="")
    parser.add_argument("--admin-user", default="admin",
                        help="Nombre de usuario admin")
    parser.add_argument("--admin-password", default="admin123",
                        help="Contrasena del usuario admin")
    parser.add_argument("--admin-nombre", default="Administrador del Sistema",
                        help="Nombre completo del admin")
    pa = parser.parse_args()

    print("=" * 50)
    print("  SIAC ERP — Pre-configuración")
    print("=" * 50)

    db = DatabaseManager()
    db.initialize_schema()

    from src.models.empresa_model import EmpresaModel
    model = EmpresaModel()
    model.guardar_varias({
        "nombre_empresa": pa.nombre,
        "razon_social": pa.razon or pa.nombre,
        "rfc": pa.rfc,
        "domicilio": pa.domicilio,
        "telefono": pa.telefono,
        "email": pa.email,
    })
    print(f"Datos de empresa guardados: {pa.nombre}")

    # Crear usuario admin con credenciales personalizadas
    from src.models.accesos_model import UsuarioModel, PermisosModel
    user_model = UsuarioModel()
    perm_model = PermisosModel()
    existing = user_model.obtener_por_username(pa.admin_user)
    if not existing:
        admin_id = user_model.crear(
            pa.admin_user, pa.admin_password, pa.admin_nombre, "admin")
        # Asignar todos los permisos al admin
        perm_model.guardar(admin_id, perm_model.claves_totales())
        print(f"Usuario admin creado: {pa.admin_user}")
    else:
        # Actualizar password del admin existente
        user_model.cambiar_password(existing["id"], pa.admin_password)
        user_model.actualizar(
            existing["id"], pa.admin_user, pa.admin_nombre, "admin")
        print(f"Usuario admin actualizado: {pa.admin_user}")

    print("Pre-configuración completada.")
    return True


def _verificar_onboarding() -> None:
    """Muestra el wizard de onboarding si la empresa no está configurada.

    Se ejecuta después de initialize_schema() para que la BD ya exista.
    Si el instalador pre-configuró los datos, este wizard no se muestra.
    """
    try:
        from src.models.empresa_model import EmpresaModel
        if not EmpresaModel().empresa_configurada():
            from src.views.dialog_onboarding import DialogOnboarding
            dlg = DialogOnboarding()
            dlg.exec()
    except Exception as e:
        print(f"Onboarding omitido: {e}")


def main() -> None:
    # Modo pre-configuración: inicializar BD y salir sin GUI
    if _pre_configurar():
        sys.exit(0)
    app = QApplication(sys.argv)
    app.setApplicationName("SIAC ERP")
    app.setApplicationVersion("1.0.0")

    instalar_adaptador_resolucion_global()

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    stylesheet = load_styles()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    db = DatabaseManager()
    db.initialize_schema()

    # Onboarding: solo se muestra si el instalador no pre-configuró la empresa
    _verificar_onboarding()

    InstaladorHistorico.instalar()

    # Icono de la ventana principal
    from pathlib import Path as _Path
    _icono_ruta = _Path(__file__).resolve().parent / "src" / "views" / "assets" / "icono_siac.png"
    if _icono_ruta.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(_icono_ruta)))

    window = MainWindow()
    window.setWindowIcon(QIcon(str(_icono_ruta))) if _icono_ruta.exists() else None
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
