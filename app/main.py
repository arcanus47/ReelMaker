import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from app.config import APP_NAME, ASSETS_DIR
from app.ui.main_window import MainWindow
from app.ui.theme import apply_palette


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # Fusion + paleta oscura fría: apariencia idéntica en Windows y Linux.
    app.setStyle("Fusion")
    apply_palette(app)
    logo_path = ASSETS_DIR / "reelmaker.png"
    if logo_path.is_file():
        app.setWindowIcon(QIcon(str(logo_path)))
    font = QFont()
    font.setFamilies(["Inter", "Segoe UI", "Noto Sans", "Ubuntu", "DejaVu Sans"])
    font.setPointSize(10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
