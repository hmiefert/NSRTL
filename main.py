# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication
from gui.window import MainWindow
import os
import sys
import winreg as reg


if __name__ == "__main__":
    # AutoStart
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 0, reg.KEY_SET_VALUE)
    cwd = os.getcwd()
    nsrtl_exe = cwd + '\\NSRTL.exe'
    if os.path.exists(nsrtl_exe):
        reg.SetValueEx(key, 'NSRTL', 0, reg.REG_SZ, nsrtl_exe)

    # APP
    app = QApplication(sys.argv)
    mw = MainWindow()

    # get URL and Token from registry
    try:
        nsrtl = reg.OpenKey(reg.HKEY_CURRENT_USER, 'Software\\NSRTL', 0, reg.KEY_READ)
        nsrtl_url = reg.QueryValueEx(nsrtl, 'URL')
        nsrtl_token = reg.QueryValueEx(nsrtl, 'TOKEN')
    except FileNotFoundError:
        nsrtl_url = 'wss://localhost:8081'
        nsrtl_token = 'aVerySecureToken'
    else:
        mw.ws.websocket_url = nsrtl_url[0]
        mw.ws.websocket_token = nsrtl_token[0]

    mw.close()
    sys.exit(app.exec())