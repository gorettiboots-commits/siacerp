from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QFont, QKeySequence, QPixmap, QShortcut
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMenuBar, QMessageBox, QPushButton,
    QStackedWidget, QStatusBar, QToolButton, QVBoxLayout, QWidget,
)

from src.controllers.accesos_controller import AccesosController
from src.models.accesos_model import tiene
from src.utils.icons import mono_icon
from src.utils.logs import registrar_log, set_usuario_actual
from src.views.login_view import LoginView
from src.views.clientes_view import ClientesView
from src.views.dashboard_view import DashboardView
from src.views.ordenes_compra_view import OrdenesCompraView
from src.views.produccion_view import ProduccionView
from src.views.programacion_view import ProgramacionView
from src.views.sandbox_view import SandboxView
from src.views.stock_view import StockView


class AcercaDeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Acerca de SIAC ERP")
        self.setFixedSize(480, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 24, 32, 24)

        from pathlib import Path
        logo_path = Path(__file__).resolve().parent / "assets" / "logo.jpeg"
        if logo_path.exists():
            lbl_logo = QLabel()
            pixmap = QPixmap(str(logo_path)).scaled(
                100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pixmap)
            lbl_logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl_logo)

        title = QLabel("SIAC ERP")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b;")
        layout.addWidget(title)

        subtitle = QLabel("Sistema Integral de Administración y Control")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(subtitle)

        info = QFormLayout()
        info.setSpacing(8)
        info.addRow("Versión:", QLabel("1.0.0"))
        info.addRow("Plataforma:", QLabel("Python 3.11+ / PySide6"))
        info.addRow("Base de Datos:", QLabel("SQLite / PostgreSQL"))
        info.addRow("Desarrollado por:", QLabel("Mario Felipe Luevano"))
        layout.addLayout(info)

        layout.addStretch()

        rights = QLabel(
            "Todos los derechos reservados\n"
            "Derechos de uso y modificación: Francisco Aguirre\n"
            "© 2026 Mario Felipe Luevano")
        rights.setAlignment(Qt.AlignCenter)
        rights.setStyleSheet("font-size: 11px; color: #94a3b8; padding: 8px; "
                             "border-top: 1px solid #e2e8f0;")
        layout.addWidget(rights)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnPrimary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignCenter)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SIAC ERP")
        disp = QApplication.primaryScreen().availableGeometry()
        min_w = min(1100, int(disp.width() * 0.95))
        min_h = min(700, int(disp.height() * 0.90))
        self.setMinimumSize(min_w, min_h)
        self.resize(min(1400, int(disp.width() * 0.98)), min(900, int(disp.height() * 0.95)))

        self._central = QWidget()
        self._central.setObjectName("centralContainer")
        self.setCentralWidget(self._central)

        self._current_user = None
        self._permisos: set = set()

        self._stack = QStackedWidget()
        self._login_view = LoginView()
        self._main_container = QWidget()

        self._setup_menu()
        self._setup_login()
        self._setup_main_container()
        self._setup_status_bar()
        self._setup_shortcuts()

        self._stack.addWidget(self._login_view)
        self._stack.addWidget(self._main_container)
        self._stack.setCurrentWidget(self._login_view)

        main_layout = QVBoxLayout(self._central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._stack)

        self._login_view.login_successful.connect(self._on_login)

    def _setup_menu(self) -> None:
        # El estilo de la barra de menú lo define styles.qss (QMenuBar/QMenu).
        menubar = self.menuBar()

        archivo_menu = menubar.addMenu("Archivo")
        self._config_action = QAction("Configuración", self)
        self._config_action.triggered.connect(self._mostrar_configuracion)
        archivo_menu.addAction(self._config_action)
        archivo_menu.addSeparator()
        self._crear_etiqueta_action = QAction("Crear Etiqueta", self)
        self._crear_etiqueta_action.triggered.connect(self._crear_etiqueta)
        archivo_menu.addAction(self._crear_etiqueta_action)
        self._imprimir_etiquetas_action = QAction("Imprimir Etiquetas", self)
        self._imprimir_etiquetas_action.triggered.connect(self._imprimir_etiquetas)
        archivo_menu.addAction(self._imprimir_etiquetas_action)
        archivo_menu.addSeparator()
        self._cola_impresion_action = QAction("Cola de Impresión", self)
        self._cola_impresion_action.triggered.connect(self._mostrar_cola_impresion)
        archivo_menu.addAction(self._cola_impresion_action)
        archivo_menu.addSeparator()
        salir_action = QAction("Salir", self)
        salir_action.triggered.connect(self.close)
        archivo_menu.addAction(salir_action)

        ayuda_menu = menubar.addMenu("Ayuda")
        self._atajos_action = QAction("Atajos de Teclado", self)
        self._atajos_action.triggered.connect(self._mostrar_atajos)
        ayuda_menu.addAction(self._atajos_action)
        ayuda_menu.addSeparator()
        self._logs_action = QAction("Logs del Sistema", self)
        self._logs_action.triggered.connect(self._mostrar_logs)
        ayuda_menu.addAction(self._logs_action)
        ayuda_menu.addSeparator()
        acerca_action = QAction("Acerca de SIAC ERP", self)
        acerca_action.triggered.connect(self._mostrar_acerca)
        ayuda_menu.addAction(acerca_action)

    def _mostrar_configuracion(self) -> None:
        if self._stack.currentWidget() != self._main_container:
            return
        if not (tiene(self._permisos, "configuracion", "ver")
                or tiene(self._permisos, "usuarios", "ver")):
            QMessageBox.information(
                self, "Acceso denegado",
                "No tiene permisos para ver la configuración del sistema.")
            return
        from src.views.configuracion_view import DialogConfiguracion
        dlg = DialogConfiguracion(self, self._permisos)
        dlg.exec()

    def _mostrar_logs(self) -> None:
        if self._stack.currentWidget() != self._main_container:
            return
        from src.views.logs_view import DialogLogs
        dlg = DialogLogs(self)
        dlg.exec()

    def _mostrar_acerca(self) -> None:
        if self._stack.currentWidget() == self._main_container:
            dlg = AcercaDeDialog(self)
            dlg.exec()

    def _mostrar_atajos(self) -> None:
        texto = (
            "<b>Atajos de Teclado — SIAC ERP</b><br><br>"
            "<table cellspacing='8'>"
            "<tr><td><b>Ctrl+1</b></td><td>Órdenes de Compra</td></tr>"
            "<tr><td><b>Ctrl+2</b></td><td>Producción</td></tr>"
            "<tr><td><b>Ctrl+3</b></td><td>Inventario</td></tr>"
            "<tr><td><b>Ctrl+4</b></td><td>Clientes</td></tr>"
            "<tr><td><b>Ctrl+5</b></td><td>Programación</td></tr>"
            "<tr><td><b>Ctrl+6</b></td><td>Dashboard</td></tr>"
            "<tr><td><b>Ctrl+K</b></td><td>Buscador Global</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>Configuración</td></tr>"
            "<tr><td><b>Enter</b></td><td>Aceptar / Confirmar</td></tr>"
            "<tr><td><b>Escape</b></td><td>Cancelar / Cerrar</td></tr>"
            "</table>"
        )
        QMessageBox.information(self, "Atajos de Teclado", texto)

    def _mostrar_cola_impresion(self) -> None:
        if self._stack.currentWidget() != self._main_container:
            return
        from src.controllers.impresiones_controller import ImpresionesController
        from src.views.cola_impresion_view import DialogColaImpresion
        dlg = DialogColaImpresion(ImpresionesController(), self)
        dlg.exec()

    def _crear_etiqueta(self) -> None:
        from src.components.editor_etiqueta_widget import DialogoEditorEtiqueta
        dlg = DialogoEditorEtiqueta(self)
        dlg.abrir_fullscreen()

    def _imprimir_etiquetas(self) -> None:
        from src.views.etiquetas_dialog import EtiquetasDialog
        from src.controllers.programacion_controller import ProgramacionController
        dlg = EtiquetasDialog(ProgramacionController(), self)
        dlg.exec()

    def _setup_login(self) -> None:
        pass

    def _setup_main_container(self) -> None:
        self._main_container.setObjectName("mainContainer")
        layout = QVBoxLayout(self._main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tool_bar = self._create_tool_bar()
        self._content_area = QStackedWidget()
        self._content_area.setObjectName("contentArea")

        self._view_ordenes = OrdenesCompraView()
        self._view_produccion = ProduccionView()
        self._view_stock = StockView()
        self._view_clientes = ClientesView()
        self._view_programacion = ProgramacionView()
        self._view_sandbox = SandboxView()
        self._view_dashboard = DashboardView()
        self._view_super_admin = None  # Se carga bajo demanda

        self._video_splash = self._create_video_splash()
        self._content_area.addWidget(self._video_splash)
        self._content_area.addWidget(self._view_ordenes)
        self._content_area.addWidget(self._view_produccion)
        self._content_area.addWidget(self._view_stock)
        self._content_area.addWidget(self._view_clientes)
        self._content_area.addWidget(self._view_programacion)
        self._content_area.addWidget(self._view_sandbox)
        self._content_area.addWidget(self._view_dashboard)

        # Clic en tarjetas KPI del Dashboard → navegar al módulo correspondiente
        self._view_dashboard.navegar_modulo.connect(self._ir_a_modulo_desde_dashboard)

        # Super Admin (carga lazy)
        self._idx_super_admin = self._content_area.count()  # Índice futuro
        self._nav_super_admin = None  # Se crea bajo demanda

        layout.addWidget(self._tool_bar)
        layout.addWidget(self._content_area, 1)

    def _create_video_splash(self) -> QWidget:
        stack = QStackedWidget()
        stack.setObjectName("videoSplash")

        video_page = QWidget()
        lay = QVBoxLayout(video_page)
        lay.setContentsMargins(0, 0, 0, 0)
        video = QVideoWidget(video_page)
        video.setAspectRatioMode(Qt.KeepAspectRatio)
        lay.addWidget(video)
        stack.addWidget(video_page)

        logo_page = QWidget()
        logo_page.setStyleSheet("background-color: #0f172a;")
        l = QVBoxLayout(logo_page)
        l.addStretch()
        logo_label = QLabel()
        logo_pixmap = None
        try:
            from src.models.empresa_model import EmpresaModel
            logo_bytes = EmpresaModel().obtener_logo_bytes()
            if logo_bytes:
                logo_pixmap = QPixmap()
                logo_pixmap.loadFromData(logo_bytes)
        except Exception:
            pass
        if logo_pixmap is None or logo_pixmap.isNull():
            logo_path = Path(__file__).resolve().parent / "assets" / "logo.jpeg"
            if logo_path.exists():
                logo_pixmap = QPixmap(str(logo_path))
        if logo_pixmap is not None and not logo_pixmap.isNull():
            logo_label.setPixmap(logo_pixmap.scaled(
                160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        l.addWidget(logo_label)
        brand = QLabel("SIAC ERP")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet("font-size: 30px; font-weight: bold; color: #ffffff;")
        l.addWidget(brand)
        sub = QLabel("Sistema Integral de Administración y Control")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("font-size: 14px; color: #94a3b8;")
        l.addWidget(sub)
        hint = QLabel("Seleccione un módulo en la barra superior")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #64748b; padding-top: 24px;")
        l.addWidget(hint)
        l.addStretch()
        stack.addWidget(logo_page)

        player = QMediaPlayer(stack)
        audio = QAudioOutput(stack)
        player.setAudioOutput(audio)
        player.setVideoOutput(video)
        ruta_video = None
        try:
            from src.models.empresa_model import EmpresaModel
            ruta_cfg = EmpresaModel().obtener('video_splash')
            if ruta_cfg and Path(ruta_cfg).exists():
                ruta_video = Path(ruta_cfg)
        except Exception:
            pass
        if ruta_video is None:
            ruta_default = (
                Path(__file__).resolve().parents[2] / "video.mp4")
            if ruta_default.exists():
                ruta_video = ruta_default
        if ruta_video is not None:
            player.setSource(QUrl.fromLocalFile(str(ruta_video)))
            player.mediaStatusChanged.connect(self._on_video_status)
        self._splash_player = player
        self._splash_stack = stack
        return stack

    _TB_ALTO = 64

    def _create_tool_bar(self) -> QFrame:
        """Barra de herramientas superior (estilo del Sandbox) que reemplaza
        la sidebar colapsable. Botón por módulo con ícono arriba y texto debajo;
        el activo se resalta en teal oscuro."""
        bar = QFrame()
        bar.setObjectName("navToolbar")
        bar.setFixedHeight(self._TB_ALTO)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(6)

        logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
        if not logo_path.exists():
            logo_path = Path(__file__).resolve().parent.parent.parent / "logonew.png"
        if logo_path.exists():
            logo_btn = QLabel()
            logo_btn.setPixmap(QPixmap(str(logo_path)).scaled(
                36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_btn.setAlignment(Qt.AlignCenter)
            logo_btn.setFixedSize(44, 52)
            lay.addWidget(logo_btn)

        # --- Botón Dashboard (primer elemento del toolbar) ---
        _color_dashboard = "#0D9488"
        self.nav_dashboard = QToolButton()
        self.nav_dashboard.setObjectName("navToolDashboard")
        self.nav_dashboard.setText("Dashboard")
        self.nav_dashboard.setToolTip("Dashboard del sistema (Ctrl+6)")
        self.nav_dashboard.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.nav_dashboard.setCheckable(True)
        self.nav_dashboard.setAutoExclusive(True)
        self.nav_dashboard.setFixedSize(78, 58)
        self.nav_dashboard.setCursor(Qt.PointingHandCursor)
        self.nav_dashboard.setIcon(mono_icon("dashboard", 26, _color_dashboard))
        self.nav_dashboard.setIconSize(QSize(26, 26))
        self.nav_dashboard.toggled.connect(
            lambda checked: self.nav_dashboard.setIcon(mono_icon(
                "dashboard", 26, "#ffffff" if checked else _color_dashboard)))
        self.nav_dashboard.clicked.connect(lambda checked=False: self._mostrar_dashboard())
        lay.addWidget(self.nav_dashboard)

        self.nav_ordenes = self._modulo_btn(
            "oc", "OC", mono_icon("oc", 26, "#1892D4"), 0)
        self.nav_ordenes.setToolTip("Órdenes de Compra (Ctrl+1)")
        self.nav_produccion = self._modulo_btn(
            "produccion", "Producción", mono_icon("produccion", 26, "#16A34A"), 1)
        self.nav_produccion.setToolTip("Producción (Ctrl+2)")
        self.nav_stock = self._modulo_btn(
            "inventario", "Inventario", mono_icon("inventario", 26, "#E3C14D"), 2)
        self.nav_stock.setToolTip("Inventario (Ctrl+3)")
        self.nav_clientes = self._modulo_btn(
            "clientes", "Clientes", mono_icon("clientes", 26, "#77307E"), 3)
        self.nav_clientes.setToolTip("Clientes (Ctrl+4)")
        self.nav_programacion = self._modulo_btn(
            "programacion", "Programación", mono_icon("programacion", 26, "#22A8C6"), 4)
        self.nav_programacion.setToolTip("Programación (Ctrl+5)")

        # --- Estilos/colores de botones módulo (izquierda) ---
        _iconos_nav = {
            "oc": ("navToolOC", "#1892D4"),
            "produccion": ("navToolProduccion", "#16A34A"),
            "inventario": ("navToolInventario", "#E3C14D"),
            "clientes": ("navToolClientes", "#77307E"),
            "programacion": ("navToolProgramacion", "#22A8C6"),
        }
        for clave, btn in [
            ("oc", self.nav_ordenes),
            ("produccion", self.nav_produccion),
            ("inventario", self.nav_stock),
            ("clientes", self.nav_clientes),
            ("programacion", self.nav_programacion),
        ]:
            obj_name, color = _iconos_nav[clave]
            btn.setObjectName(obj_name)
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setFixedSize(78, 58)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(mono_icon(clave, 26, color))
            btn.setIconSize(QSize(26, 26))
            btn.toggled.connect(
                lambda checked, b=btn, k=clave, c=color:
                b.setIcon(mono_icon(k, 26, "#ffffff" if checked else c)))
            lay.addWidget(btn)

        # --- Spacer: módulos a la izquierda, Sandbox/Salir a la derecha ---
        lay.addStretch()

        # Botón Sandbox (solo admin)
        self.nav_sandbox = QToolButton()
        self.nav_sandbox.setObjectName("navToolSandbox")
        self.nav_sandbox.setText("Sandbox")
        self.nav_sandbox.setToolTip("Sandbox (solo admin)")
        self.nav_sandbox.setIcon(mono_icon("sandbox", 26, "#ca8a04"))
        self.nav_sandbox.setIconSize(QSize(26, 26))
        self.nav_sandbox.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.nav_sandbox.setCheckable(True)
        self.nav_sandbox.setAutoExclusive(True)
        self.nav_sandbox.setFixedSize(78, 58)
        self.nav_sandbox.setCursor(Qt.PointingHandCursor)
        self.nav_sandbox.setVisible(False)
        self.nav_sandbox.clicked.connect(self._mostrar_sandbox)
        lay.addWidget(self.nav_sandbox)

        # Botón Super Admin (solo super_admin)
        self._nav_super_admin = QToolButton()
        self._nav_super_admin.setObjectName("navToolSuperAdmin")
        self._nav_super_admin.setText("Admin")
        self._nav_super_admin.setToolTip("Panel de Administración (Super Admin)")
        self._nav_super_admin.setIcon(mono_icon("dashboard", 26, "#7C3AED"))
        self._nav_super_admin.setIconSize(QSize(26, 26))
        self._nav_super_admin.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._nav_super_admin.setCheckable(True)
        self._nav_super_admin.setAutoExclusive(True)
        self._nav_super_admin.setFixedSize(78, 58)
        self._nav_super_admin.setCursor(Qt.PointingHandCursor)
        self._nav_super_admin.setVisible(False)
        self._nav_super_admin.clicked.connect(self._mostrar_super_admin)
        lay.addWidget(self._nav_super_admin)

        # Cierre de sesión
        self.nav_salir = QToolButton()
        self.nav_salir.setText("Cerrar Sesión")
        self.nav_salir.setObjectName("navToolSalir")
        self.nav_salir.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.nav_salir.setFixedSize(78, 58)
        self.nav_salir.setCursor(Qt.PointingHandCursor)
        self.nav_salir.setToolTip("Cerrar Sesión")
        self.nav_salir.setIcon(mono_icon("logout", 26, "#dc2626"))
        self.nav_salir.setIconSize(QSize(26, 26))
        self.nav_salir.clicked.connect(self._logout)
        lay.addWidget(self.nav_salir)

        return bar

    def _modulo_btn(self, clave: str, texto: str, icono, idx: int) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("navTool")
        btn.setText(texto)
        btn.setIcon(icono)
        btn.setIconSize(QSize(26, 26))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        btn.setFixedSize(88, 52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked=False, i=idx: self._switch_view(i))
        return btn

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistema listo")

    def _setup_shortcuts(self) -> None:
        sc = QShortcut(QKeySequence("Ctrl+1"), self)
        sc.activated.connect(lambda: self._switch_view(0))
        sc = QShortcut(QKeySequence("Ctrl+2"), self)
        sc.activated.connect(lambda: self._switch_view(1))
        sc = QShortcut(QKeySequence("Ctrl+3"), self)
        sc.activated.connect(lambda: self._switch_view(2))
        sc = QShortcut(QKeySequence("Ctrl+4"), self)
        sc.activated.connect(lambda: self._switch_view(3))
        sc = QShortcut(QKeySequence("Ctrl+5"), self)
        sc.activated.connect(lambda: self._switch_view(4))
        sc = QShortcut(QKeySequence("Ctrl+6"), self)
        sc.activated.connect(self._mostrar_dashboard)
        sc = QShortcut(QKeySequence("Ctrl+K"), self)
        sc.activated.connect(self._abrir_buscador)
        sc = QShortcut(QKeySequence("Ctrl+,"), self)
        sc.activated.connect(self._mostrar_configuracion)

    def _abrir_buscador(self) -> None:
        if self._stack.currentWidget() != self._main_container:
            return
        from src.views.search_dialog import DialogBuscadorGlobal
        dlg = DialogBuscadorGlobal(self)
        dlg.navegar.connect(self._navegar_desde_buscador)
        dlg.exec()

    def _navegar_desde_buscador(self, modulo: str, registro: dict) -> None:
        mod_indices = {
            "ordenes_compra": 0,
            "produccion": 1,
            "inventario": 2,
            "clientes": 3,
        }
        if modulo in mod_indices:
            self._switch_view(mod_indices[modulo])

    def _on_video_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._splash_stack.setCurrentIndex(1)

    def _switch_view(self, index: int) -> None:
        mods = ["ordenes_compra", "produccion", "inventario", "clientes", "programacion"]
        if not tiene(self._permisos, mods[index], "ver"):
            return
        self._content_area.setCurrentIndex(index + 1)
        for i, nav in enumerate([self.nav_ordenes, self.nav_produccion,
                                 self.nav_stock, self.nav_clientes,
                                 self.nav_programacion]):
            nav.setChecked(i == index)
        names = ["Órdenes de Compra", "Producción", "Inventario", "Clientes",
                 "Programación"]
        if index < len(names):
            self.status_bar.showMessage(f"Módulo: {names[index]}")

    def _aplicar_permisos(self) -> None:
        self.nav_ordenes.setVisible(tiene(self._permisos, "ordenes_compra", "ver"))
        self.nav_produccion.setVisible(tiene(self._permisos, "produccion", "ver"))
        self.nav_stock.setVisible(tiene(self._permisos, "inventario", "ver"))
        self.nav_clientes.setVisible(tiene(self._permisos, "clientes", "ver"))
        self.nav_programacion.setVisible(tiene(self._permisos, "programacion", "ver"))
        self.nav_sandbox.setVisible(
            bool(self._current_user) and self._current_user.get("rol") == "admin")
        # Super Admin: visible solo para rol super_admin
        es_super = bool(self._current_user) and self._current_user.get("rol") == "super_admin"
        if self._nav_super_admin:
            self._nav_super_admin.setVisible(es_super)
        self._config_action.setEnabled(
            tiene(self._permisos, "configuracion", "ver")
            or tiene(self._permisos, "usuarios", "ver"))
        self._cola_impresion_action.setEnabled(
            bool(self._current_user)
            and (tiene(self._permisos, "produccion", "ver")
                 or tiene(self._permisos, "programacion", "ver")))
        self._logs_action.setVisible(
            bool(self._current_user)
            and self._current_user.get("rol") == "admin")
        self._view_ordenes.set_permisos(self._permisos)
        self._view_produccion.set_permisos(self._permisos)
        self._view_stock.set_permisos(self._permisos)
        self._view_clientes.set_permisos(self._permisos)
        self._view_programacion.set_permisos(self._permisos)
        tiene_prog_export = tiene(self._permisos, "programacion", "exportar")
        self._crear_etiqueta_action.setEnabled(tiene_prog_export)
        self._imprimir_etiquetas_action.setEnabled(tiene_prog_export)

    def _on_login(self, credentials: dict) -> None:
        user = AccesosController().autenticar(
            credentials["username"], credentials["password"])
        if user:
            self._current_user = user
            set_usuario_actual(user)
            self._permisos = AccesosController().permisos_login(user)
            self._stack.setCurrentWidget(self._main_container)
            self._aplicar_permisos()
            self._content_area.setCurrentWidget(self._video_splash)
            self._splash_player.stop()
            self._splash_player.setPosition(0)
            self._splash_stack.setCurrentIndex(0)
            self._splash_player.play()
            self.status_bar.showMessage(
                f"Conectado como: {user['nombre_completo']} ({user['rol']})")
            self.setWindowTitle(f"SIAC ERP - {user['nombre_completo']}")
        else:
            from src.views.login_view import LoginView
            for w in self._stack.findChildren(LoginView):
                w.lbl_error.setText("Usuario o contraseña incorrectos")
                w.lbl_error.setVisible(True)
                w.btn_login.setEnabled(True)
                w.btn_login.setText("Iniciar Sesión")

    def _mostrar_sandbox(self) -> None:
        self._content_area.setCurrentWidget(self._view_sandbox)
        self.status_bar.showMessage("Módulo: Sandbox")

    def _mostrar_super_admin(self) -> None:
        """Muestra el dashboard de super_admin (multi-empresa)."""
        if self._stack.currentWidget() != self._main_container:
            return
        if not self._view_super_admin:
            from src.views.super_admin_view import SuperAdminView
            self._view_super_admin = SuperAdminView()
            self._content_area.addWidget(self._view_super_admin)
            self._idx_super_admin = self._content_area.count() - 1
        self._view_super_admin.recargar()
        self._content_area.setCurrentWidget(self._view_super_admin)
        self.status_bar.showMessage("Módulo: Panel de Administración (Super Admin)")

    def _mostrar_dashboard(self) -> None:
        if self._stack.currentWidget() != self._main_container:
            return
        self._view_dashboard.recargar()
        self._content_area.setCurrentWidget(self._view_dashboard)
        self.status_bar.showMessage("Módulo: Dashboard")

    def _ir_a_modulo_desde_dashboard(self, modulo: str) -> None:
        """Navega al módulo solicitado por una tarjeta KPI del Dashboard.
        `_switch_view` valida los permisos del usuario."""
        indices = {"ordenes_compra": 0, "produccion": 1, "inventario": 2,
                   "clientes": 3, "programacion": 4}
        if modulo in indices:
            self._switch_view(indices[modulo])

    def _logout(self) -> None:
        if self._current_user:
            registrar_log("seguridad", "logout", "usuario", self._current_user.get("id"),
                          datos={"username": self._current_user.get("username")})
        self._current_user = None
        set_usuario_actual(None)
        self._permisos = set()
        self._config_action.setEnabled(False)
        self._crear_etiqueta_action.setEnabled(False)
        self._imprimir_etiquetas_action.setEnabled(False)
        self._cola_impresion_action.setEnabled(False)
        self._logs_action.setVisible(False)
        if self._nav_super_admin:
            self._nav_super_admin.setVisible(False)
        self._stack.setCurrentWidget(self._login_view)
        for w in self._stack.findChildren(LoginView):
            w.txt_user.clear()
            w.txt_pass.clear()
            w.lbl_error.setVisible(False)
        self._splash_player.stop()
        self._splash_stack.setCurrentIndex(0)
        self._content_area.setCurrentWidget(self._video_splash)
        self.setWindowTitle("SIAC ERP")
        self.status_bar.showMessage("Sesión cerrada")
