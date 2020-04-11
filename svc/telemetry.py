from PyQt5.QtCore import QThread, pyqtSignal
from irsdk import IRSDK
import time


class Telemetry(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.ir = IRSDK()
        self.ir_connected = False
        self.last_car_setup_tick = -1
        self.timeout = 0.1
        self.session_info = None

    def run(self):
        while True:
            if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
                self.ir_connected = False
                self.last_car_setup_tick = -1
                self.ir.shutdown()
                self.session_info = None
            elif not self.ir_connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
                self.ir_connected = True
                self.session_info = None
            
            if self.ir_connected:
                self.ir.freeze_var_buffer_latest()

                if self.session_info == None:
                    self.set_session_info()



                if self.ir['SessionTime']:
                    self.signal.emit('session time: ' + str(self.ir['SessionTime']))
            
            time.sleep(self.timeout)
    
    def set_session_info(self):
        session_info = {}
        session_info['Track'] = self.ir['WeekendInfo']['TrackDisplayName'] + " (" + self.ir['WeekendInfo']['TrackCountry'] + ")"
        session_info['SessionID'] = str(self.ir['WeekendInfo']['SessionID']) + " (SubSessionID: " + str(self.ir['WeekendInfo']['SubSessionID']) + ")"
        session_info['TrackInfo'] = "TrackCleanup: " + str(self.ir['WeekendInfo']['TrackCleanup']) + " | TrackDynamicTrack: " + str(self.ir['WeekendInfo']['TrackDynamicTrack'])
        session_info['Weather'] = self.ir['WeekendInfo']['WeekendOptions']['Date'] + " | " + self.ir['WeekendInfo']['WeekendOptions']['TimeOfDay'] + " | " + self.ir['WeekendInfo']['WeekendOptions']['WeatherType'] + " | " + self.ir['WeekendInfo']['WeekendOptions']['Skies']
        session_info['Drivers'] = self.get_drivers_list()

        self.session_info = session_info
        self.signal.emit(self.session_info)

    def get_drivers_list(self):
        drivers_list = "(" + str(len(self.ir['DriverInfo']['Drivers'])) + ") "
        for driver in self.ir['DriverInfo']['Drivers']:
            if driver['CarIsPaceCar'] == 1:
                continue
            drivers_list += "#" +  driver['CarNumber'] + " " + driver['UserName'] + " <" + driver['CarScreenName'] + ">\n"
        return drivers_list