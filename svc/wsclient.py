from PyQt5.QtCore import QObject, QUrl, QTimer
from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol
from json import dumps


class WSClient(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.client = QWebSocket("", QWebSocketProtocol.Version13, None)        
        self.client.error.connect(self.onError)
        self.client.connected.connect(self.onConnected)
        self.message_queue = []
        self.is_connected = False
        
        self.timer_reconnect = QTimer(parent)
        self.timer_reconnect.start(30000)
        self.timer_reconnect.timeout.connect(self.reconnect)

        self.timer_reconnect = QTimer(parent)
        self.timer_reconnect.start(500)
        self.timer_reconnect.timeout.connect(self.send_message)

    def onConnected(self):
        self.is_connected = True

    def onError(self):
        self.is_connected = False
        self.client.abort()

    def queue_message(self, message):
        self.message_queue.append(message)

    def send_message(self):
        if self.is_connected and len(self.message_queue) > 0:
            message = self.message_queue.pop(0)
            if self.client.sendTextMessage(dumps(message)) <= 0:
                self.message_queue.append(message)  

    def reconnect(self):
        if self.is_connected == False:
            self.client.open(QUrl("ws://localhost:8080"))
