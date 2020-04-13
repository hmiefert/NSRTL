from PyQt5.QtWidgets import QApplication
from gui.window import MainWindow
import os
import sys
import winreg as reg


if __name__ == "__main__":
    # AutoStart
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
    reg.SetValueEx(key, 'NSRTL', 0, reg.REG_SZ, os.getcwd() + '\\NSRTL.exe')

    # APP
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.close()
    sys.exit(app.exec())