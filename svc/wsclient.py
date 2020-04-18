from PyQt5.QtCore import QObject, QUrl, QTimer, QFile, QIODevice
from PyQt5.QtNetwork import QSslConfiguration, QSslCertificate
from PyQt5.QtWebSockets import QWebSocket, QWebSocketProtocol
from json import dumps
import certs.server_res

class WSClient(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.client = QWebSocket("", QWebSocketProtocol.Version13, None)        
        self.client.error.connect(self.onError)
        self.client.connected.connect(self.onConnected)
        self.client.disconnected.connect(self.onDisconnected)
        self.ssl_config = QSslConfiguration()
        self.ssl_cert_file = QFile(":certs/server.pem")
        self.ssl_cert_file.open(QIODevice.ReadOnly)
        self.ssl_cert = QSslCertificate(self.ssl_cert_file)
        self.ssl_config.setCaCertificates([self.ssl_cert])
        self.client.setSslConfiguration(self.ssl_config)
        self.message_queue = []
        self.is_connected = False
        self.telemetry_connected = False
        self.websocket_url = "wss://localhost:8081"
        self.websocket_token = "aVerySecureToken"
        
        self.timer_connection_watchdog = QTimer(parent)
        self.timer_connection_watchdog.start(5000)
        self.timer_connection_watchdog.timeout.connect(self.connection_watchdog)

        self.timer_reconnect = QTimer(parent)
        self.timer_reconnect.start(500)
        self.timer_reconnect.timeout.connect(self.send_message)

    def onConnected(self):
        # print("WebSocket: connected")
        self.is_connected = True

    def onDisconnected(self):
        # print("WebSocket: disconnected -> " + self.client.errorString())
        self.is_connected = False
        self.client.abort()
    
    def onError(self):
        # print("WebSocket: error -> " + self.client.errorString())
        self.is_connected = False
        self.client.abort()
    

    def queue_message(self, message):
        self.message_queue.append(message)

    def send_message(self):
        if self.is_connected and len(self.message_queue) > 0:
            message = self.message_queue.pop(0)
            message['token'] = self.websocket_token
            if self.client.sendTextMessage(dumps(message)) <= 0:
                self.message_queue.append(message)  

    def connection_watchdog(self):
        if self.is_connected == False and self.telemetry_connected == True:
            # print("WebSocket: connecting to -> " + self.websocket_url)
            c = self.client.open(QUrl(self.websocket_url))
        if self.is_connected == True and self.telemetry_connected == False:
            # print("WebSocket: disconnecting from -> " + self.websocket_url)
            self.client.close()
            self.is_connected = False