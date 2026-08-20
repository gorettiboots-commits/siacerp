"""Wizard de onboarding: captura de datos de empresa al primer arranque.

Muestra un wizard paso a paso (QWizard) para configurar los datos
generales de la empresa usuaria: nombre, razón social, RFC, domicilio,
teléfono, email, logotipo y video de bienvenida. Se ejecuta una sola
vez (la primera vez que el sistema detecta que no hay datos configurados).
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
    QWizard, QWizardPage,
)

from src.utils.icons import mono_icon


class PaginaEmpresa(QWizardPage):
    """Paso 1: Datos generales de la empresa."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Datos de la Empresa")
        self.setSubTitle(
            "Ingrese el nombre comercial y la razón social de la empresa "
            "que utilizará el sistema.")
        self._setup_ui()

    def _setup_ui(self) -> None:
        form = QFormLayout()
        form.setSpacing(12)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Goretti Calzado")
        form.addRow("Nombre de empresa:", self.txt_nombre)

        self.txt_razon = QLineEdit()
        self.txt_razon.setPlaceholderText("Ej: Goretti Calzado S.A. de C.V.")
        form.addRow("Razón social:", self.txt_razon)

        self.txt_rfc = QLineEdit()
        self.txt_rfc.setPlaceholderText("Ej: GCA123456XX0")
        form.addRow("RFC:", self.txt_rfc)

        self.setLayout(form)

    def validatePage(self) -> bool:
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(
                self, "Campo obligatorio",
                "Debe ingresar el nombre de la empresa.")
            return False
        return True


class PaginaContacto(QWizardPage):
    """Paso 2: Datos de contacto de la empresa."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Datos de Contacto")
        self.setSubTitle(
            "Información de contacto y domicilio fiscal de la empresa.")
        self._setup_ui()

    def _setup_ui(self) -> None:
        form = QFormLayout()
        form.setSpacing(12)

        self.txt_domicilio = QTextEdit()
        self.txt_domicilio.setPlaceholderText(
            "Ej: Av. Industrial #123, Col. Progreso, CDMX, C.P. 02870")
        self.txt_domicilio.setMaximumHeight(70)
        form.addRow("Domicilio:", self.txt_domicilio)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Ej: 55 1234 5678")
        form.addRow("Teléfono:", self.txt_telefono)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Ej: contacto@goretti.com")
        form.addRow("Email:", self.txt_email)

        self.setLayout(form)


class PaginaLogo(QWizardPage):
    """Paso 3: Logotipo de la empresa."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Logotipo de la Empresa")
        self.setSubTitle(
            "Seleccione el logotipo que se mostrará en el sistema. "
            "Puede omitirlo y configurarlo después.")
        self._logo_bytes: bytes | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout()
        layout.setSpacing(20)

        izq = QVBoxLayout()
        self.lbl_preview = QLabel("Sin logotipo")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setMinimumSize(200, 200)
        self.lbl_preview.setMaximumSize(300, 300)
        self.lbl_preview.setStyleSheet(
            "border: 2px dashed #cbd5e1; border-radius: 8px; "
            "color: #94a3b8; font-size: 13px; background: #f8fafc;")
        izq.addWidget(self.lbl_preview)

        btn_seleccionar = QPushButton("Seleccionar imagen...")
        btn_seleccionar.setIcon(mono_icon("editar", 18, "#1892D4"))
        btn_seleccionar.clicked.connect(self._seleccionar_logo)
        izq.addWidget(btn_seleccionar)

        btn_quitar = QPushButton("Quitar logo")
        btn_quitar.clicked.connect(self._quitar_logo)
        izq.addWidget(btn_quitar)
        izq.addStretch()

        layout.addLayout(izq)

        info = QVBoxLayout()
        hint = QLabel(
            "Recomendaciones:\n\n"
            "- Formato: PNG o JPG\n"
            "- Tamaño recomendado: 300x300 px\n"
            "- Fondo transparente (PNG)\n"
            "- Se usará en el splash y encabezados")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        info.addWidget(hint)
        info.addStretch()

        layout.addLayout(info)
        self.setLayout(layout)

    def _seleccionar_logo(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar logotipo", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp);;Todos (*)")
        if not ruta:
            return
        try:
            self._logo_bytes = Path(ruta).read_bytes()
            pixmap = QPixmap()
            pixmap.loadFromData(self._logo_bytes)
            if not pixmap.isNull():
                self.lbl_preview.setPixmap(pixmap.scaled(
                    200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo leer la imagen:\n{e}")
            self._logo_bytes = None

    def _quitar_logo(self) -> None:
        self._logo_bytes = None
        self.lbl_preview.clear()
        self.lbl_preview.setText("Sin logotipo")

    @property
    def logo_bytes(self) -> bytes | None:
        return self._logo_bytes


class PaginaVideo(QWizardPage):
    """Paso 4: Video de bienvenida."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle("Video de Bienvenida")
        self.setSubTitle(
            "Seleccione un video corto que se reproducirá como splash "
            "al iniciar sesión. Puede omitirlo.")
        self._ruta_video: str = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(16)

        form = QFormLayout()
        self.txt_ruta_video = QLineEdit()
        self.txt_ruta_video.setReadOnly(True)
        self.txt_ruta_video.setPlaceholderText("No se ha seleccionado video")
        form.addRow("Archivo:", self.txt_ruta_video)
        layout.addLayout(form)

        fila_btns = QHBoxLayout()
        btn_seleccionar = QPushButton("Seleccionar video...")
        btn_seleccionar.setIcon(mono_icon("editar", 18, "#1892D4"))
        btn_seleccionar.clicked.connect(self._seleccionar_video)
        fila_btns.addWidget(btn_seleccionar)

        btn_quitar = QPushButton("Quitar video")
        btn_quitar.clicked.connect(self._quitar_video)
        fila_btns.addWidget(btn_quitar)
        fila_btns.addStretch()
        layout.addLayout(fila_btns)

        hint = QLabel(
            "Recomendaciones:\n\n"
            "- Formato: MP4 (H.264)\n"
            "- Duración: 10-30 segundos\n"
            "- Tamaño máximo recomendado: 50 MB\n"
            "- Se reproducirá al cada vez que un usuario inicie sesión")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(hint)
        layout.addStretch()

        self.setLayout(layout)

    def _seleccionar_video(self) -> None:
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar video", "",
            "Videos (*.mp4 *.avi *.mov);;Todos (*)")
        if ruta:
            self._ruta_video = ruta
            self.txt_ruta_video.setText(ruta)

    def _quitar_video(self) -> None:
        self._ruta_video = ""
        self.txt_ruta_video.clear()

    @property
    def ruta_video(self) -> str:
        return self._ruta_video


class DialogOnboarding(QWizard):
    """Wizard de configuración inicial de empresa.

    Se muestra en la primera ejecución cuando la tabla
    ``configuracion_empresa`` está vacía. Al finalizar, guarda los datos
    en la BD y se cierra.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configuración Inicial — SIAC ERP")
        self.setFixedSize(720, 540)
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoDefaultButton, True)

        icono_logo = mono_icon("empresa", 32, "#07756A")
        self.setWindowIcon(icono_logo)

        self.setButtonText(QWizard.NextButton, "Siguiente")
        self.setButtonText(QWizard.BackButton, "Atrás")
        self.setButtonText(QWizard.FinishButton, "Finalizar")
        self.setButtonText(QWizard.CancelButton, "Cancelar")
        self.setButtonText(
            QWizard.CommitButton,
            "Guardar y continuar")

        self._page_empresa = PaginaEmpresa()
        self._page_contacto = PaginaContacto()
        self._page_logo = PaginaLogo()
        self._page_video = PaginaVideo()

        self.addPage(self._page_empresa)
        self.addPage(self._page_contacto)
        self.addPage(self._page_logo)
        self.addPage(self._page_video)

        self.currentIdChanged.connect(self._on_page_changed)

    def _on_page_changed(self, page_id: int) -> None:
        if page_id == 3:
            self.setButtonText(
                self.NextButton,
                "Finalizar")

    def accept(self) -> None:
        datos = {
            'nombre_empresa': self._page_empresa.txt_nombre.text().strip(),
            'razon_social': self._page_empresa.txt_razon.text().strip(),
            'rfc': self._page_empresa.txt_rfc.text().strip(),
            'domicilio': self._page_contacto.txt_domicilio.toPlainText().strip(),
            'telefono': self._page_contacto.txt_telefono.text().strip(),
            'email': self._page_contacto.txt_email.text().strip(),
        }
        logo = self._page_logo.logo_bytes
        video = self._page_video.ruta_video

        try:
            from src.models.empresa_model import EmpresaModel
            model = EmpresaModel()
            model.guardar_varias(datos)
            if logo:
                model.guardar_logo(logo)
            if video:
                model.guardar('video_splash', video)
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"No se pudieron guardar los datos:\n{e}")
            return

        QMessageBox.information(
            self, "Configuración completada",
            "Los datos de la empresa se han guardado correctamente.\n\n"
            "Puede modificarlos más tarde desde Configuración > Empresa.")

        super().accept()
