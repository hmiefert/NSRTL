from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QWidget, QTextEdit, QSystemTrayIcon, QAction, QStyle, qApp, QMenu
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QPixmap, QIcon
from svc.telemetry import Telemetry
from svc.wsclient import WSClient
from time import sleep
import res.newman_res

class MainWindow(QMainWindow):
    tray_icon = None
 
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
 
        self.setMinimumSize(QSize(400, 800))
        self.setMaximumSize(QSize(400, 800))
        self.setWindowTitle("NSRTL")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.textEdit_debug = QTextEdit(central_widget)
        self.textEdit_debug.setGeometry(QRect(0, 0, 400, 800))
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
        self.ws.websocket_url = "wss://api.hmiefert.de:42443"
        self.ws.websocket_token = "aVerySecureToken"

        self.ir_thread = Telemetry()
        self.ir_thread.timeout = 0.25
        self.ir_thread.weekend_update_rate = 60
        self.ir_thread.session_update_rate = 30
        self.ir_thread.weather_update_rate = 30
        self.ir_thread.driver_update_rate = 10
        self.ir_thread.drivers_update_rate = 20
        self.ir_thread.carsetup_update_rate = 5
        self.ir_thread.pitstop_update_rate = 5
        self.ir_thread.signal.connect(self.recieve_signal)
        self.ir_thread.start()

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def recieve_signal(self, signal):
        now = datetime.now()
        fnow = now.strftime("%Y-%m-%d %H:%M:%S")
        if signal['type'] == 'pyirsdk':
            self.textEdit_debug.append(fnow + ": Telemetry status -> " + signal['status'])
            if signal['status'] == "connected":
                self.ws.telemetry_connected = True
            else:
                self.ws.telemetry_connected = False

        if signal['type'] == 'weekend':
            self.textEdit_debug.append(fnow + ": Weekend data updated")
            self.ws.queue_message(signal)
            
        if signal['type'] == 'session':
            self.textEdit_debug.append(fnow + ": Session data updated")
            self.ws.queue_message(signal)

        if signal['type'] == 'weather':
            self.textEdit_debug.append(fnow + ": Weather data updated")
            self.ws.queue_message(signal)

        if signal['type'] == 'driver':
            self.textEdit_debug.append(fnow + ": Driver data updated")
            self.ws.queue_message(signal)

        if signal['type'] == 'drivers':
            self.textEdit_debug.append(fnow + ": Drivers data updated")
            self.ws.queue_message(signal)

        if signal['type'] == 'carsetup':
            self.textEdit_debug.append(fnow + ": CarSetup data updated")
            self.ws.queue_message(signal)

        if signal['type'] == 'pitstop':
            self.textEdit_debug.append(fnow + ": PitStop data updated")
            self.ws.queue_message(signal)

        self.textEdit_debug.verticalScrollBar().setValue(self.textEdit_debug.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.ws.is_connected == False
        self.ws.client.close()

        self.ir_thread.ir.shutdown()
        
        event.ignore()
        self.hide()