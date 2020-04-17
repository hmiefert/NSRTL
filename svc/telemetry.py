from PyQt5.QtCore import QThread, pyqtSignal
from irsdk import IRSDK
import json
import time


class Telemetry(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.ir = IRSDK()
        self.ir_connected = False
        self.last_car_setup_tick = -1
        self.timeout = 0.25
        self.weekend_update_rate = 60
        self.session_update_rate = 30
        self.weather_update_rate = 30
        self.driver_update_rate = 10
        self.drivers_update_rate = 20
        self.carsetup_update_rate = 5
        self.pitstop_update_rate = 5
        self.data = None

    def run(self):
        while True:
            if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
                self.ir_connected = False
                self.last_car_setup_tick = -1
                self.ir.shutdown()
                self.data = None
                self.signal.emit({"type": "pyirsdk", "status" : "disconnected"})
            elif not self.ir_connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
                self.ir_connected = True
                self.data = None
                self.signal.emit({"type": "pyirsdk", "status" : "connected"})
            
            if self.ir_connected:
                self.ir.freeze_var_buffer_latest()
                self.update()
                self.ir.unfreeze_var_buffer_latest()
            
            time.sleep(self.timeout)
    
    def update(self):
        if self.data == None:
            self.data ={}
        
        self.update_weekend()
        self.update_session()
        self.update_weather()
        self.update_carsetup()
        self.update_pitstop()
        self.update_driver()
        self.update_drivers()

    def update_weekend(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'weekend' not in self.data:
            self.data['weekend'] = {}

        if 'weekend_timestamp' not in self.data:
            self.data['weekend_timestamp'] = 0

        if self.data['weekend_timestamp'] + self.weekend_update_rate < timestamp:
            if self.data['weekend'] != self.ir['WeekendInfo']:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "weekend",
                    "data": {
                        "weekend": self.ir['WeekendInfo']
                    }
                })
                self.data['weekend'] = self.ir['WeekendInfo']
                self.data['weekend_timestamp'] = timestamp

    def update_session(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'session' not in self.data:
            self.data['session'] = {}

        if 'session_timestamp' not in self.data:
            self.data['session_timestamp'] = 0

        if self.data['session_timestamp'] + self.session_update_rate < timestamp:
            if self.data['session'] != self.ir['SessionInfo']:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "session",
                    "data": {
                        "session": self.ir['SessionInfo']
                    }
                })
                self.data['session'] = self.ir['SessionInfo']
                self.data['session_timestamp'] = timestamp

    def update_weather(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'weather' not in self.data:
            self.data['weather'] = {}

        if 'weather_timestamp' not in self.data:
            self.data['weather_timestamp'] = 0
        
        if self.data['weather_timestamp'] + self.weather_update_rate < timestamp:
            wi = dict()
            wi_keys = ['AirTemp', 'TrackTemp', 'TrackTempCrew', 'WeatherType', 'Skies', 'FogLevel', 'RelativeHumidity', 'WindDir', 'WindVel']

            for key in wi_keys:
                try:
                    val = self.ir[key]
                except KeyError:
                    wi[key] = None
                    continue
                
                if type(val) == str:
                    wi[key] = val
                elif type(val) == int:
                    wi[key] = val
                elif type(val) == float:
                    wi[key] = round(val, 1)
                else:
                    wi[key] = None
            
            if self.data['weather'] != wi:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "weather",
                    "data": {
                        "weather": wi
                    }
                })
                self.data['weather'] = wi
                self.data['weather_timestamp'] = timestamp
    
    def update_driver(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']

        if 'driver' not in self.data:
            self.data['driver'] = []

        if 'driver_timestamp' not in self.data:
            self.data['driver_timestamp'] = 0

        if self.data['driver_timestamp'] + self.driver_update_rate < timestamp:
            driver = dict()
            driver_keys = ['DriverUserID', 'DriverCarIdx', 'DriverCarIdx', 'DriverUserID', 'PaceCarIdx', 'DriverCarIdleRPM',
            'DriverCarRedLine', 'DriverCarEngCylinderCount', 'DriverCarFuelKgPerLtr', 'DriverCarFuelMaxLtr', 'DriverCarMaxFuelPct',
            'DriverCarSLFirstRPM', 'DriverCarSLShiftRPM', 'DriverCarSLLastRPM', 'DriverCarSLBlinkRPM', 'DriverCarVersion', 'DriverPitTrkPct',
            'DriverCarEstLapTime', 'DriverSetupName', 'DriverSetupIsModified', 'DriverSetupLoadTypeName', 'DriverSetupPassedTech', 'DriverIncidentCount']

            for key in driver_keys:
                try:
                    driver[key] = self.ir['DriverInfo'][key]
                except KeyError:
                    driver[key] = None
            if self.data['driver'] != driver:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "driver",
                    "data": {
                        "driver": driver
                    }
                })
                self.data['driver'] = driver
                self.data['driver_timestamp'] = timestamp

    def update_drivers(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']

        if 'drivers' not in self.data:
            self.data['drivers'] = []

        if 'drivers_timestamp' not in self.data:
            self.data['drivers_timestamp'] = 0

        if self.data['drivers_timestamp'] + self.drivers_update_rate < timestamp:
            drivers = []

            for driver in self.ir['DriverInfo']['Drivers']:
                if driver['CarIsPaceCar'] == 0 and driver['CarIsAI'] == 0:
                    dr = dict()
                    for key, val in driver.items():
                        dr[key] = val
                    drivers.append(dr)
            
            if self.data['drivers'] != drivers:
                for i in drivers:
                    found = False
                    for j in self.data['drivers']:
                        if i == j:
                            found = True
                            break
                    if found is False:
                        self.signal.emit({
                            "timestamp": timestamp,
                            "session_id": session_id,
                            "sub_session_id": sub_session_id,
                            "type": "drivers",
                            "data": {
                                "drivers": i
                            }
                        })
                self.data['drivers'] = drivers
                self.data['drivers_timestamp'] = timestamp

    def update_carsetup(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'carsetup' not in self.data:
            self.data['carsetup'] = {}

        if 'carsetup_timestamp' not in self.data:
            self.data['carsetup_timestamp'] = 0

        if self.data['carsetup_timestamp'] + self.carsetup_update_rate < timestamp:
            if self.data['carsetup'] != self.ir['CarSetup']:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "carsetup",
                    "data": {
                        "carsetup": self.ir['CarSetup']
                    }
                })
                self.data['carsetup'] = self.ir['CarSetup']
                self.data['carsetup_timestamp'] = timestamp

    def update_pitstop(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'pitstop' not in self.data:
            self.data['pitstop'] = {}

        if 'pitstop_timestamp' not in self.data:
            self.data['pitstop_timestamp'] = 0
        
        if self.data['pitstop_timestamp'] + self.pitstop_update_rate < timestamp:
            ps = dict()
            ps_keys = ['dpFastRepair', 'dpFuelAddKg', 'dpFuelFill', 'dpLFTireChange', 'dpLFTireColdPress', 'dpRFTireChange',
            'dpRFTireColdPress', 'dpLRTireChange', 'dpLRTireColdPress', 'dpRRTireChange', 'dpRRTireColdPress', 'dpWindshieldTearoff']
            
            for key in ps_keys:
                try:
                    val = self.ir[key]
                except KeyError:
                    ps[key] = None
                    continue
                ps[key] = int(val)            

            if self.data['pitstop'] != ps:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "type": "pitstop",
                    "data": {
                        "pitstop": ps
                    }
                })
                self.data['pitstop'] = ps
                self.data['pitstop_timestamp'] = timestamp


    
    # def update_cars_on_track_(self):
    #     timestamp = self.ir['SessionTime']
    #     session_id = self.ir['WeekendInfo']['SessionID']
    #     sub_session_id = self.ir['WeekendInfo']['SubSessionID']

    #     td['CarIdxPosition'] = self.ir['CarIdxPosition']
    #     td['CarIdxClassPosition'] = self.ir['CarIdxClassPosition']
    #     td['CarIdxLap'] = self.ir['CarIdxLap']
    #     td['CarIdxLapCompleted'] = self.ir['CarIdxLapCompleted']
    #     td['CarIdxOnPitRoad'] = self.ir['CarIdxOnPitRoad']



        # td['DriverMarker'] = self.ir['DriverMarker']
        # td['EngineWarnings'] = self.ir['EngineWarnings']
        # td['EnterExitReset'] = self.ir['EnterExitReset']
        # td['FastRepairAvailable'] = self.ir['FastRepairAvailable']
        # td['FastRepairUsed'] = self.ir['FastRepairUsed']

        # td['FrameRate'] = self.ir['FrameRate']
        # td['FuelLevel'] = self.ir['FuelLevel']
        # td['FuelLevelPct'] = self.ir['FuelLevelPct']
        # td['FuelPress'] = self.ir['FuelPress']
        # td['FuelUsePerHour'] = self.ir['FuelUsePerHour']

        # td['OnPitRoad'] = self.ir['OnPitRoad']
        # td['IsInGarage'] = self.ir['IsInGarage']
        # td['IsOnTrack'] = self.ir['IsOnTrack']
        # td['IsOnTrackCar'] = self.ir['IsOnTrackCar']

        # td['Lap'] = self.ir['Lap']
        # td['LapBestLap'] = self.ir['LapBestLap']
        # td['LapBestLapTime'] = self.ir['LapBestLapTime']
        # td['LapBestNLapLap'] = self.ir['LapBestNLapLap']
        # td['LapBestNLapTime'] = self.ir['LapBestNLapTime']
        # td['LapCompleted'] = self.ir['LapCompleted']
        # td['LapLasNLapSeq'] = self.ir['LapLasNLapSeq']
        # td['LapLastLapTime'] = self.ir['LapLastLapTime']
        # td['LapLastNLapTime'] = self.ir['LapLastNLapTime']

        # td['ManifoldPress'] = self.ir['ManifoldPress']
        # td['OilLevel'] = self.ir['OilLevel']
        # td['OilPress'] = self.ir['OilPress']
        # td['OilTemp'] = self.ir['OilTemp']
        # td['Voltage'] = self.ir['Voltage']
        # td['WaterLevel'] = self.ir['WaterLevel']
        # td['WaterTemp'] = self.ir['WaterTemp']

        # td['PitOptRepairLeft'] = self.ir['PitOptRepairLeft']
        # td['PitRepairLeft'] = self.ir['PitRepairLeft']
        # td['PitsOpen'] = self.ir['PitsOpen']
        # td['PitstopActive'] = self.ir['PitstopActive']
        # td['PitSvFlags'] = self.ir['PitSvFlags']
        # td['PitSvFuel'] = self.ir['PitSvFuel']
        # td['PitSvLFP'] = self.ir['PitSvLFP']
        # td['PitSvLRP'] = self.ir['PitSvLRP']
        # td['PitSvRFP'] = self.ir['PitSvRFP']
        # td['PitSvRRP'] = self.ir['PitSvRRP']

        # td['LFcoldPressure'] = self.ir['LFcoldPressure']
        # td['LFtempCL'] = self.ir['LFtempCL']
        # td['LFtempCM'] = self.ir['LFtempCM']
        # td['LFtempCR'] = self.ir['LFtempCR']
        # td['LFwearL'] = self.ir['LFwearL']
        # td['LFwearM'] = self.ir['LFwearM']
        # td['LFwearR'] = self.ir['LFwearR']

        # td['RFcoldPressure'] = self.ir['RFcoldPressure']
        # td['RFtempCL'] = self.ir['RFtempCL']
        # td['RFtempCM'] = self.ir['RFtempCM']
        # td['RFtempCR'] = self.ir['RFtempCR']
        # td['RFwearL'] = self.ir['RFwearL']
        # td['RFwearM'] = self.ir['RFwearM']
        # td['RFwearR'] = self.ir['RFwearR']

        # td['LRcoldPressure'] = self.ir['LRcoldPressure']
        # td['LRtempCL'] = self.ir['LRtempCL']
        # td['LRtempCM'] = self.ir['LRtempCM']
        # td['LRtempCR'] = self.ir['LRtempCR']
        # td['LRwearL'] = self.ir['LRwearL']
        # td['LRwearM'] = self.ir['LRwearM']
        # td['LRwearR'] = self.ir['LRwearR']

        # td['RRcoldPressure'] = self.ir['RRcoldPressure']
        # td['RRtempCL'] = self.ir['RRtempCL']
        # td['RRtempCM'] = self.ir['RRtempCM']
        # td['RRtempCR'] = self.ir['RRtempCR']
        # td['RRtempCL'] = self.ir['RRtempCL']
        # td['RRwearL'] = self.ir['RRwearL']
        # td['RRwearM'] = self.ir['RRwearM']
        # td['RRwearR'] = self.ir['RRwearR']

        # td['PlayerCarClassPosition'] = self.ir['PlayerCarClassPosition']
        # td['PlayerCarDriverIncidentCount'] = self.ir['PlayerCarDriverIncidentCount']
        # td['PlayerCarIdx'] = self.ir['PlayerCarIdx']
        # td['PlayerCarInPitStall'] = self.ir['PlayerCarInPitStall']
        # td['PlayerCarMyIncidentCount'] = self.ir['PlayerCarMyIncidentCount']
        # td['PlayerCarPitSvStatus'] = self.ir['PlayerCarPitSvStatus']
        # td['PlayerCarPosition'] = self.ir['PlayerCarPosition']
        # td['PlayerCarPowerAdjust'] = self.ir['PlayerCarPowerAdjust']
        # td['PlayerCarTeamIncidentCount'] = self.ir['PlayerCarTeamIncidentCount']
        # td['PlayerCarTowTime'] = self.ir['PlayerCarTowTime']
        # td['PlayerCarWeightPenalty'] = self.ir['PlayerCarWeightPenalty']

        # td['RaceLaps'] = self.ir['RaceLaps']

        # td['SessionFlags'] = self.ir['SessionFlags']
        # td['SessionLapsRemain'] = self.ir['SessionLapsRemain']
        # td['SessionLapsRemainEx'] = self.ir['SessionLapsRemainEx']
        # td['SessionNum'] = self.ir['SessionNum']
        # td['SessionState'] = self.ir['SessionState']

        # td['DCDriversSoFar'] = self.ir['DCDriversSoFar']
        # td['dcHeadlightFlash'] = self.ir['dcHeadlightFlash']
        # td['DCLapStatus'] = self.ir['DCLapStatus']
        # td['dcPitSpeedLimiterToggle'] = self.ir['dcPitSpeedLimiterToggle']
        # td['dcStarter'] = self.ir['dcStarter']