from window import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
