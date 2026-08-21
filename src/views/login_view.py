from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpacerItem, QVBoxLayout, QWidget,
)


class LoginView(QWidget):
    login_successful = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("loginWidget")
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # El fondo del widget y de la tarjeta los define styles.qss
        # (QWidget#loginWidget y QFrame#loginCard): aquí solo se
        # configura el tamaño fijo de la tarjeta.
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(Qt.GlobalColor.gray)
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 48, 40, 48)

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
                120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        title = QLabel("SIAC ERP")
        title.setObjectName("loginTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b;")
        layout.addWidget(title)

        subtitle = QLabel("Sistema Integral de Administración y Control")
        subtitle.setObjectName("loginSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 16px;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Ingrese su usuario")
        self.txt_user.setMinimumHeight(38)
        self.txt_user.setCompleter(None)

        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Ingrese su contraseña")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setMinimumHeight(38)
        self.txt_pass.setCompleter(None)

        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.setObjectName("btnLogin")
        self.btn_login.setMinimumHeight(40)

        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #dc2626; font-size: 12px;")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setVisible(False)

        layout.addWidget(lbl_user)
        layout.addWidget(self.txt_user)
        layout.addSpacing(4)
        layout.addWidget(lbl_pass)
        layout.addWidget(self.txt_pass)
        layout.addSpacing(8)
        layout.addWidget(self.lbl_error)
        layout.addWidget(self.btn_login)

        outer.addStretch()
        outer.addWidget(card, 0, Qt.AlignCenter)
        outer.addStretch()

        self.btn_login.clicked.connect(self._handle_login)
        self.txt_pass.returnPressed.connect(self._handle_login)

    def _handle_login(self) -> None:
        user = self.txt_user.text().strip()
        password = self.txt_pass.text().strip()

        if not user or not password:
            self.lbl_error.setText("Ingrese usuario y contraseña")
            self.lbl_error.setVisible(True)
            return

        self.btn_login.setEnabled(False)
        self.btn_login.setText("Conectando...")
        self.login_successful.emit({"username": user, "password": password})
