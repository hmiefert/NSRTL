from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QWidget, QTextEdit, QSystemTrayIcon, QAction, QStyle, qApp, QMenu
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QPixmap, QIcon
from svc.database import JsonStorage
from svc.telemetry import Telemetry
from svc.wsclient import WSClient
import res.newman_res

class MainWindow(QMainWindow):
    tray_icon = None
 
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
 
        self.setMinimumSize(QSize(1200, 800))
        self.setMaximumSize(QSize(1200, 800))
        self.setWindowTitle("Newman-Simracing Telemetry-Logger")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.textEdit_session_info = QTextEdit(central_widget)
        self.textEdit_session_info.setGeometry(QRect(0, 0, 1200, 250))
        self.textEdit_session_info.setObjectName("textEdit_session_info")
        self.textEdit_session_info.setReadOnly(True)

        self.textEdit_debug = QTextEdit(central_widget)
        self.textEdit_debug.setGeometry(QRect(0, 250, 1200, 550))
        self.textEdit_debug.setObjectName("textEdit_debug")
        self.textEdit_debug.setReadOnly(True)

        self.setWindowIcon(QIcon(QPixmap(':icons/newman-icon.png')))

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(QPixmap(':icons/newman-icon.png')))

        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.ws = WSClient(self)
        self.db = JsonStorage()

        self.ir_thread = Telemetry()
        self.ir_thread.timeout = 0.25
        self.ir_thread.weekend_info_update_rate = 60
        self.ir_thread.session_info_update_rate = 10
        self.ir_thread.weather_info_update_rate = 60
        self.ir_thread.drivers_info_update_rate = 10
        self.ir_thread.pit_settings_info_update_rate = 10
        self.ir_thread.signal.connect(self.recieve_signal)
        self.ir_thread.start()

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def recieve_signal(self, signal):
        now = datetime.now()
        fnow = now.strftime("%Y-%m-%d %H:%M:%S")
        
        if 'pyirsdk' in signal:
            self.textEdit_debug.append(fnow + ": Telemetry Status -> " + signal['pyirsdk'])

        if 'weekend_info' in signal:
            self.textEdit_debug.append(fnow + ": " + signal['message'])
            self.db.insert_weekend_info(signal)
            
        if 'session_info' in signal:
            self.textEdit_debug.append(fnow + ": " + signal['message'])
            self.db.insert_session_info(signal)

        if 'weather_info' in signal:
            self.textEdit_debug.append(fnow + ": " + signal['message'])
            self.db.insert_weather_info(signal)

        if 'driver_info' in signal:
            self.textEdit_debug.append(fnow + ": " + signal['message'])
            self.db.insert_driver_info(signal)

        if 'pit_settings_info' in signal:
            self.textEdit_debug.append(fnow + ": " + signal['message'])
            self.db.insert_pit_settings_info(signal)

        self.textEdit_debug.verticalScrollBar().setValue(self.textEdit_debug.verticalScrollBar().maximum())

        # self.ws.send_message(signal)

    def closeEvent(self, event):
        event.ignore()
        self.hide()