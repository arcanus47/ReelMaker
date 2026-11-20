import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.ui.main_window import MainWindow
from app.config import APP_NAME

def main():
    app=QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("DejaVu Sans",10))
    window=MainWindow(); window.show()
    sys.exit(app.exec())

if __name__=="__main__": main()
