from PyQt5.QtWidgets import QApplication
from gui.window import MainWindow
import sys


if __name__ == "__main__": 
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    mw.close()
    sys.exit(app.exec())