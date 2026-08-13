import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.components.campo_historico import InstaladorHistorico
from src.database.db_manager import DatabaseManager
from src.utils.ui_helpers import load_styles
from src.views.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SIAC ERP")
    app.setApplicationVersion("1.0.0")

    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    stylesheet = load_styles()
    if stylesheet:
        app.setStyleSheet(stylesheet)

    db = DatabaseManager()
    db.initialize_schema()

    InstaladorHistorico.instalar()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
