from PyQt5.QtWidgets import QMainWindow, QWidget, QTextEdit, QSystemTrayIcon, QAction, QStyle, qApp, QMenu
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QPixmap, QIcon
from svc.telemetry import Telemetry
import res.newman_res

class MainWindow(QMainWindow):
    tray_icon = None
 
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
 
        self.setMinimumSize(QSize(480, 160))
        self.setMaximumSize(QSize(480, 160))
        self.setWindowTitle("Newman-Simracing Telemetry-Logger")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.textEdit_debug = QTextEdit(central_widget)
        self.textEdit_debug.setGeometry(QRect(0, 0, 480, 160))
        self.textEdit_debug.setObjectName("textEdit_debug")

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

        self.ir_thread = Telemetry()
        self.ir_thread.timeout = 0.5
        self.ir_thread.signal.connect(self.debug_message)
        self.ir_thread.start()

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def debug_message(self, message):
        self.textEdit_debug.append(message)
        self.textEdit_debug.verticalScrollBar().setValue(self.textEdit_debug.verticalScrollBar().maximum())

    def closeEvent(self, event):
        event.ignore()
        self.hide()