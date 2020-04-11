from PyQt5.QtWidgets import QMainWindow, QWidget, QTextEdit, QSystemTrayIcon, QAction, QStyle, qApp, QMenu
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QPixmap, QIcon
from svc.telemetry import Telemetry
from svc.wsclient import WSClient
import res.newman_res

class MainWindow(QMainWindow):
    tray_icon = None
 
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
 
        self.setMinimumSize(QSize(800, 600))
        self.setMaximumSize(QSize(800, 600))
        self.setWindowTitle("Newman-Simracing Telemetry-Logger")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.textEdit_session_info = QTextEdit(central_widget)
        self.textEdit_session_info.setGeometry(QRect(0, 0, 800, 200))
        self.textEdit_session_info.setObjectName("textEdit_session_info")
        self.textEdit_session_info.setReadOnly(True)

        self.textEdit_debug = QTextEdit(central_widget)
        self.textEdit_debug.setGeometry(QRect(0, 200, 800, 600))
        self.textEdit_debug.setObjectName("textEdit_debug")
        self.textEdit_debug.setReadOnly(True)

        self.setWindowIcon(QIcon(QPixmap(':icons/newman-icon.png')))

        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(QPixmap(':icons/newman-icon.png')))
        # self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        show_action = QAction("Show", self)
        quit_action = QAction("Quit", self)
        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(qApp.quit)

        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.ws = WSClient(self)

        self.ir_thread = Telemetry()
        self.ir_thread.timeout = 0.5
        self.ir_thread.signal.connect(self.recieve_signal)
        self.ir_thread.start()

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def recieve_signal(self, signal):
        if type(signal) == str:
            self.ws.send_message(signal)
            self.textEdit_debug.append(signal)
            self.textEdit_debug.verticalScrollBar().setValue(self.textEdit_debug.verticalScrollBar().maximum())

        if type(signal) == dict:
            output = ""
            for key, val in signal.items():
                item = key + ": " + val + "\n"
                output += item
                self.ws.send_message(item)
            self.textEdit_session_info.setText(output)

    def closeEvent(self, event):
        event.ignore()
        self.hide()