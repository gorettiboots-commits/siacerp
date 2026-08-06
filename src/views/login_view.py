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

        self.setStyleSheet("""
            QWidget#loginWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e293b, stop:1 #0f172a);
            }
        """)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame#loginCard {
                background-color: #ffffff;
                border-radius: 16px;
                padding: 40px;
            }
        """)

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
        logo_path = Path(__file__).resolve().parent / "assets" / "logo.jpeg"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
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
        self.txt_user.setStyleSheet("""
            QLineEdit {
                padding: 12px 16px;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                font-size: 14px;
                background-color: #f9fafb;
            }
            QLineEdit:focus {
                border: 2px solid #4f46e5;
                background-color: #ffffff;
            }
        """)

        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("font-size: 13px; font-weight: 600; color: #374151;")
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Ingrese su contraseña")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setStyleSheet(self.txt_user.styleSheet())

        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.setObjectName("btnLogin")
        self.btn_login.setMinimumHeight(48)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """)

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

        self.login_successful.emit({"username": user, "password": password})
