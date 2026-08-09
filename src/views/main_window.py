from pathlib import Path

from PySide6.QtCore import QEasingCurve, QSize, Qt, QUrl, QVariantAnimation
from PySide6.QtGui import QAction, QFont, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QApplication, QDialog, QFormLayout, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMenuBar, QMessageBox, QPushButton, QSizePolicy,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)

from src.controllers.accesos_controller import AccesosController
from src.models.accesos_model import tiene
from src.utils.icons import mono_icon
from src.views.login_view import LoginView
from src.views.ordenes_compra_view import OrdenesCompraView
from src.views.produccion_view import ProduccionView
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
        logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
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
        info.addRow("Desarrollado por:", QLabel("Francisco Aguirre"))
        layout.addLayout(info)

        layout.addStretch()

        rights = QLabel(
            "Todos los derechos reservados\n"
            "© 2026 Francisco Aguirre")
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
        self.setMinimumSize(1280, 800)
        self.resize(1400, 900)

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

        self._stack.addWidget(self._login_view)
        self._stack.addWidget(self._main_container)
        self._stack.setCurrentWidget(self._login_view)

        main_layout = QVBoxLayout(self._central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._stack)

        self._login_view.login_successful.connect(self._on_login)

    def _setup_menu(self) -> None:
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar { background-color: #1e293b; color: #94a3b8; padding: 2px; }
            QMenuBar::item:selected { background-color: #334155; color: #e2e8f0; }
            QMenu { background-color: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; }
            QMenu::item:selected { background-color: #eef2ff; color: #4f46e5; }
        """)

        archivo_menu = menubar.addMenu("Archivo")
        self._config_action = QAction("Configuración", self)
        self._config_action.triggered.connect(self._mostrar_configuracion)
        archivo_menu.addAction(self._config_action)
        salir_action = QAction("Salir", self)
        salir_action.triggered.connect(self.close)
        archivo_menu.addAction(salir_action)

        ayuda_menu = menubar.addMenu("Ayuda")
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

    def _mostrar_acerca(self) -> None:
        if self._stack.currentWidget() == self._main_container:
            dlg = AcercaDeDialog(self)
            dlg.exec()

    def _setup_login(self) -> None:
        pass

    def _setup_main_container(self) -> None:
        self._main_container.setObjectName("mainContainer")
        layout = QHBoxLayout(self._main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._nav_panel = self._create_nav_panel()
        self._content_area = QStackedWidget()
        self._content_area.setObjectName("contentArea")

        self._view_ordenes = OrdenesCompraView()
        self._view_produccion = ProduccionView()
        self._view_stock = StockView()
        self._view_sandbox = SandboxView()

        self._video_splash = self._create_video_splash()
        self._content_area.addWidget(self._video_splash)
        self._content_area.addWidget(self._view_ordenes)
        self._content_area.addWidget(self._view_produccion)
        self._content_area.addWidget(self._view_stock)
        self._content_area.addWidget(self._view_sandbox)

        layout.addWidget(self._nav_panel)
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
        logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
        if logo_path.exists():
            logo_label.setPixmap(QPixmap(str(logo_path)).scaled(
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
        hint = QLabel("Seleccione un módulo en el menú lateral")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("font-size: 12px; color: #64748b; padding-top: 24px;")
        l.addWidget(hint)
        l.addStretch()
        stack.addWidget(logo_page)

        player = QMediaPlayer(stack)
        audio = QAudioOutput(stack)
        player.setAudioOutput(audio)
        player.setVideoOutput(video)
        ruta_video = Path(__file__).resolve().parents[2] / "video.mp4"
        if ruta_video.exists():
            player.setSource(QUrl.fromLocalFile(str(ruta_video)))
            player.mediaStatusChanged.connect(self._on_video_status)
        self._splash_player = player
        self._splash_stack = stack
        return stack

    _NAV_W_ABIERTO = 240
    _NAV_W_CERRADO = 62

    def _create_nav_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("navPanel")
        panel.setFixedWidth(self._NAV_W_ABIERTO)
        panel.setStyleSheet("QFrame#navPanel { background-color: #1e293b; border: none; }")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 14, 12, 16)
        layout.setSpacing(2)

        self.nav_toggle = QPushButton()
        self.nav_toggle.setObjectName("navToggle")
        self.nav_toggle.setIcon(mono_icon("toggle", 22, "#cbd5e1"))
        self.nav_toggle.setIconSize(QSize(22, 22))
        self.nav_toggle.setCursor(Qt.PointingHandCursor)
        self.nav_toggle.setToolTip("Colapsar menú")
        self.nav_toggle.clicked.connect(self._toggle_sidebar)
        layout.addWidget(self.nav_toggle)

        from pathlib import Path
        logo_path = Path(__file__).resolve().parent / "assets" / "logo.png"
        self._logo_original = None
        self._nav_logo_label = QLabel()
        if logo_path.exists():
            self._logo_original = QPixmap(str(logo_path)).scaled(
                48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._nav_logo_label.setPixmap(self._logo_original)
        self._nav_logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._nav_logo_label)

        self._nav_logo_text = QLabel("SIAC ERP")
        self._nav_logo_text.setObjectName("navBrand")
        self._nav_logo_text.setStyleSheet("""
            font-size: 17px; font-weight: bold; color: #ffffff;
            padding: 4px 8px 12px 8px;
        """)
        self._nav_logo_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._nav_logo_text)

        self._nav_section = QLabel("MÓDULOS")
        self._nav_section.setObjectName("navSectionLabel")
        layout.addWidget(self._nav_section)

        self.nav_ordenes = QPushButton("Órdenes de Compra")
        self.nav_produccion = QPushButton("Producción")
        self.nav_stock = QPushButton("Inventario")
        self.nav_sandbox = QPushButton("Sandbox")

        self.nav_salir = QPushButton("Cerrar Sesión")
        self.nav_salir.setObjectName("navButton")

        _iconos_nav = {
            "oc": self.nav_ordenes,
            "produccion": self.nav_produccion,
            "inventario": self.nav_stock,
            "sandbox": self.nav_sandbox,
        }
        for clave, btn in _iconos_nav.items():
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setMinimumHeight(42)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(mono_icon(clave, 22))
            btn.setIconSize(QSize(22, 22))
            btn.toggled.connect(
                lambda checked, b=btn, k=clave:
                b.setIcon(mono_icon(k, 22, "#ffffff" if checked else "#cbd5e1")))
            layout.addWidget(btn)

        self.nav_salir.setIcon(mono_icon("logout", 22))
        self.nav_salir.setIconSize(QSize(22, 22))
        self.nav_salir.setMinimumHeight(42)
        self.nav_salir.setCursor(Qt.PointingHandCursor)

        divider = QFrame()
        divider.setObjectName("navDivider")
        layout.addWidget(divider)

        layout.addWidget(self.nav_salir)

        self.nav_sandbox.setVisible(False)
        self.nav_sandbox.clicked.connect(self._mostrar_sandbox)

        for btn, idx in [
            (self.nav_ordenes, 0), (self.nav_produccion, 1), (self.nav_stock, 2),
        ]:
            btn.clicked.connect(lambda checked, i=idx: self._switch_view(i))

        self.nav_salir.clicked.connect(self._logout)
        layout.addStretch()

        self._nav_user_card = QFrame()
        self._nav_user_card.setObjectName("userCard")
        user_layout = QVBoxLayout(self._nav_user_card)
        user_layout.setContentsMargins(10, 8, 10, 8)
        user_layout.setSpacing(2)
        self._lbl_user_name = QLabel("Sesión no iniciada")
        self._lbl_user_name.setObjectName("userName")
        self._lbl_user_role = QLabel("")
        self._lbl_user_role.setObjectName("userRole")
        user_layout.addWidget(self._lbl_user_name)
        user_layout.addWidget(self._lbl_user_role)
        layout.addWidget(self._nav_user_card)

        self._nav_version = QLabel("v1.0.0")
        self._nav_version.setObjectName("navVersion")
        self._nav_version.setStyleSheet("color: #475569; font-size: 11px; padding: 6px 0 0 0;")
        self._nav_version.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._nav_version)

        self._nav_abierto = True
        self._nav_anim = QVariantAnimation(self)
        self._nav_anim.setDuration(220)
        self._nav_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._nav_anim.valueChanged.connect(self._nav_redimensionar)

        return panel

    def _toggle_sidebar(self) -> None:
        self._nav_abierto = not self._nav_abierto
        destino = self._NAV_W_ABIERTO if self._nav_abierto else self._NAV_W_CERRADO
        self._nav_anim.stop()
        self._nav_anim.setStartValue(float(self._nav_panel.width()))
        self._nav_anim.setEndValue(float(destino))
        self._nav_anim.start()
        self._aplicar_estado_nav()

    def _nav_redimensionar(self, ancho: float) -> None:
        self._nav_panel.setFixedWidth(int(ancho))

    def _aplicar_estado_nav(self) -> None:
        abierto = self._nav_abierto
        self._nav_logo_text.setVisible(abierto)
        self._nav_section.setVisible(abierto)
        self._nav_user_card.setVisible(abierto)
        self._nav_version.setVisible(abierto)
        if self._logo_original:
            tam = 48 if abierto else 36
            self._nav_logo_label.setPixmap(self._logo_original.scaled(
                tam, tam, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        for btn, texto in [
            (self.nav_ordenes, "Órdenes de Compra"),
            (self.nav_produccion, "Producción"),
            (self.nav_stock, "Inventario"),
            (self.nav_sandbox, "Sandbox"),
        ]:
            btn.setText(texto if abierto else "")
            btn.setToolTip("" if abierto else texto)
        self.nav_salir.setText("Cerrar Sesión" if abierto else "")
        self.nav_salir.setToolTip("" if abierto else "Cerrar Sesión")
        self.nav_toggle.setToolTip("Colapsar menú" if abierto else "Expandir menú")

    def _setup_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Sistema listo")

    def _on_video_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._splash_stack.setCurrentIndex(1)

    def _switch_view(self, index: int) -> None:
        mods = ["ordenes_compra", "produccion", "inventario"]
        if not tiene(self._permisos, mods[index], "ver"):
            return
        self._content_area.setCurrentIndex(index + 1)
        for i, nav in enumerate([self.nav_ordenes, self.nav_produccion, self.nav_stock]):
            nav.setChecked(i == index)
        names = ["Órdenes de Compra", "Producción", "Inventario"]
        if index < len(names):
            self.status_bar.showMessage(f"Módulo: {names[index]}")

    def _aplicar_permisos(self) -> None:
        self.nav_ordenes.setVisible(tiene(self._permisos, "ordenes_compra", "ver"))
        self.nav_produccion.setVisible(tiene(self._permisos, "produccion", "ver"))
        self.nav_stock.setVisible(tiene(self._permisos, "inventario", "ver"))
        self.nav_sandbox.setVisible(
            bool(self._current_user) and self._current_user.get("rol") == "admin")
        self._config_action.setEnabled(
            tiene(self._permisos, "configuracion", "ver")
            or tiene(self._permisos, "usuarios", "ver"))
        self._view_ordenes.set_permisos(self._permisos)
        self._view_produccion.set_permisos(self._permisos)
        self._view_stock.set_permisos(self._permisos)

    def _on_login(self, credentials: dict) -> None:
        user = AccesosController().autenticar(
            credentials["username"], credentials["password"])
        if user:
            self._current_user = user
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
            self._lbl_user_name.setText(user["nombre_completo"])
            self._lbl_user_role.setText(f"Rol: {user['rol']}")
        else:
            from src.views.login_view import LoginView
            for w in self._stack.findChildren(LoginView):
                w.lbl_error.setText("Usuario o contraseña incorrectos")
                w.lbl_error.setVisible(True)

    def _mostrar_sandbox(self) -> None:
        self._content_area.setCurrentWidget(self._view_sandbox)
        self.status_bar.showMessage("Módulo: Sandbox")

    def _logout(self) -> None:
        self._current_user = None
        self._permisos = set()
        self._config_action.setEnabled(False)
        self._stack.setCurrentWidget(self._login_view)
        for w in self._stack.findChildren(LoginView):
            w.txt_user.clear()
            w.txt_pass.clear()
            w.lbl_error.setVisible(False)
        self._lbl_user_name.setText("Sesión no iniciada")
        self._lbl_user_role.setText("")
        self._splash_player.stop()
        self._splash_stack.setCurrentIndex(0)
        self._content_area.setCurrentWidget(self._video_splash)
        self.setWindowTitle("SIAC ERP")
        self.status_bar.showMessage("Sesión cerrada")
