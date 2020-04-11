from PyQt5.QtCore import QObject, QUrl
from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol


class WSClient(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.client = QWebSocket("", QWebSocketProtocol.Version13, None)        
        self.client.error.connect(self.onError)
        self.client.connected.connect(self.onConnected)
        self.client.open(QUrl("ws://localhost:8080"))

    def onConnected(self):
        print("WS: Connected")

    def onError(self):
        print("WS: Error")

    def send_message(self, message):
        self.client.sendTextMessage(message)
