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
        self.weekend_info_update_rate = 60
        self.session_info_update_rate = 10
        self.weather_info_update_rate = 60
        self.driver_info_update_rate = 10
        self.pit_settings_info_update_rate = 10
        self.data = None

    def run(self):
        while True:
            if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
                self.ir_connected = False
                self.last_car_setup_tick = -1
                self.ir.shutdown()
                self.data = None
                self.signal.emit({"pyirsdk" : "shutdown"})
            elif not self.ir_connected and self.ir.startup() and self.ir.is_initialized and self.ir.is_connected:
                self.ir_connected = True
                self.data = None
                self.signal.emit({"pyirsdk" : "connected"})
            
            if self.ir_connected:
                self.ir.freeze_var_buffer_latest()
                self.update()
                self.ir.unfreeze_var_buffer_latest()
            
            time.sleep(self.timeout)
    
    def update(self):
        if self.data == None:
            self.data ={}
        
        self.update_weekend_info()
        self.update_session_info()
        self.update_weather_info()
        self.update_driver_info()
        self.update_pit_settings_info()

    def update_weekend_info(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'weekend_info' not in self.data:
            self.data['weekend_info'] = {}

        if 'weekend_info_timestamp' not in self.data:
            self.data['weekend_info_timestamp'] = 0

        if self.data['weekend_info_timestamp'] + self.weekend_info_update_rate < timestamp:
            if self.data['weekend_info'] != self.ir['WeekendInfo']:
                self.signal.emit({
                        "timestamp": timestamp,
                        "session_id": session_id,
                        "sub_session_id": sub_session_id,
                        "weekend_info": self.data['weekend_info'],
                        "message": "Weekend -> Track: " + self.ir['WeekendInfo']['TrackDisplayName'] + " (" + self.ir['WeekendInfo']['TrackDisplayShortName'] + "|ID:" + str(self.ir['WeekendInfo']['TrackID']) + ") | WeatherType: " + self.ir['WeekendInfo']['TrackWeatherType'] + " | TrackSkies: " + self.ir['WeekendInfo']['TrackSkies'] + " | TrackCleanup: " + ("Yes" if self.ir['WeekendInfo']['TrackCleanup'] == 1 else "No")
                    })
                self.data['weekend_info'] = self.ir['WeekendInfo']
                self.data['weekend_info_timestamp'] = timestamp

    def update_session_info(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'session_info' not in self.data:
            self.data['session_info'] = {}

        if 'session_info_timestamp' not in self.data:
            self.data['session_info_timestamp'] = 0

        if self.data['session_info_timestamp'] + self.session_info_update_rate < timestamp:
            if self.data['session_info'] != self.ir['SessionInfo']:
                message = "Session ->"
                for session in self.ir['SessionInfo']['Sessions']:
                    message += " Type: " + session['SessionType'] + " (" + str(session['SessionNum']) + ") |"
                    message += " TrackRubberState: " + session['SessionTrackRubberState'] + " |"
                    message += " FastestLap: " + str(session['ResultsFastestLap'])

                self.signal.emit({
                        "timestamp": timestamp,
                        "session_id": session_id,
                        "sub_session_id": sub_session_id,
                        "session_info": self.ir['SessionInfo'],
                        "message": message
                    })
                self.data['session_info'] = self.ir['SessionInfo']
                self.data['session_info_timestamp'] = timestamp

    def update_weather_info(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'weather_info' not in self.data:
            self.data['weather_info'] = {}

        if 'weather_info_timestamp' not in self.data:
            self.data['weather_info_timestamp'] = 0
        
        if self.data['weather_info_timestamp'] + self.weather_info_update_rate < timestamp:
            wi = dict()
            wi['AirTemp'] = round(self.ir['AirTemp'], 1)
            wi['TrackTemp'] = round(self.ir['TrackTemp'], 1)
            wi['TrackTempCrew'] = round(self.ir['TrackTempCrew'], 1)
            wi['Skies'] = self.ir['Skies']
            wi['WeatherType'] = self.ir['WeatherType']
            wi['FogLevel'] = round(self.ir['FogLevel'], 1)
            wi['RelativeHumidity'] = round(self.ir['RelativeHumidity'], 1)
            wi['WindDir'] = round(self.ir['WindDir'], 1)
            wi['WindVel'] = round(self.ir['WindVel'], 1)
            
            if self.data['weather_info'] != wi:
                self.data['weather_info'] = wi
                self.data['weather_info_timestamp'] = timestamp
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "weather_info": self.data['weather_info'],
                    "message": "Weather -> Air:" + str(wi['AirTemp']) + "C | Track:" + str(wi['TrackTemp']) + "C | TrackCrew:" +  str(wi['TrackTempCrew']) + "C | Wind:" + str(wi['WindVel']) + "m/sec | WindDir:" + str(wi['WindDir'])
                })
                
    def update_driver_info(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        driver_user_id = self.ir['DriverInfo']['DriverUserID']
        driver_car_idx = self.ir['DriverInfo']['DriverCarIdx']

        if 'drivers_info' not in self.data:
            self.data['drivers_info'] = []

        if 'drivers_info_timestamp' not in self.data:
            self.data['drivers_info_timestamp'] = 0

        if self.data['drivers_info_timestamp'] + self.driver_info_update_rate < timestamp:
            drivers = []
            for driver in self.ir['DriverInfo']['Drivers']:
                if driver['CarIsPaceCar'] == 0 and driver['CarIsAI'] == 0:
                    d = dict()
                    d['CarIdx'] = driver['CarIdx']
                    d['UserName'] = driver['UserName']
                    d['UserID'] = driver['UserID']
                    d['TeamID'] = driver['TeamID']
                    d['TeamName'] = driver['TeamName']
                    d['CarNumber'] = driver['CarNumber']
                    d['CarNumberRaw'] = driver['CarNumberRaw']
                    d['CarPath'] = driver['CarPath']
                    d['CarClassID'] = driver['CarClassID']
                    d['CarID'] = driver['CarID']
                    d['CarScreenName'] = driver['CarScreenName']
                    d['CarScreenNameShort'] = driver['CarScreenNameShort']
                    d['CarClassShortName'] = driver['CarClassShortName']
                    d['CarClassRelSpeed'] = driver['CarClassRelSpeed']
                    d['CarClassLicenseLevel'] = driver['CarClassLicenseLevel']
                    d['CarClassMaxFuelPct'] = driver['CarClassMaxFuelPct']
                    d['CarClassWeightPenalty'] = driver['CarClassWeightPenalty']
                    d['CarClassPowerAdjust'] = driver['CarClassPowerAdjust']
                    d['IRating'] = driver['IRating']
                    d['LicLevel'] = driver['LicLevel']
                    d['LicSubLevel'] = driver['LicSubLevel']
                    d['LicString'] = driver['LicString']
                    d['IsSpectator'] = driver['IsSpectator']
                    d['ClubName'] = driver['ClubName']
                    d['DivisionName'] = driver['DivisionName']
                    d['CurDriverIncidentCount'] = driver['CurDriverIncidentCount']
                    d['TeamIncidentCount'] = driver['TeamIncidentCount']
                    drivers.append(d)
            
            if self.data['drivers_info'] != drivers:
                for i in drivers:
                    found = False
                    for j in self.data['drivers_info']:
                        if i == j:
                            found = True
                            break
                    if found is False:
                        self.signal.emit({
                            "timestamp": timestamp,
                            "session_id": session_id,
                            "sub_session_id": sub_session_id,
                            "driver_user_id": driver_user_id,
                            "driver_car_idx": driver_car_idx,
                            "driver_info": i,
                            "message": "Driver -> CarIdx: " + str(i['CarIdx']) + " | UserName: " + i['UserName'] + " (ID:" + str(i['UserID']) +"|iRating:" + str(i['IRating']) + ") | Team: " + i['TeamName'] + " (ID:" + str(i['TeamID']) + ") | Car: " + i['CarScreenName']
                        })
                self.data['drivers_info'] = drivers
                self.data['drivers_info_timestamp'] = timestamp

    
    # def update_cars_on_track_info(self):
    #     timestamp = self.ir['SessionTime']
    #     session_id = self.ir['WeekendInfo']['SessionID']
    #     sub_session_id = self.ir['WeekendInfo']['SubSessionID']

    #     td['CarIdxPosition'] = self.ir['CarIdxPosition']
    #     td['CarIdxClassPosition'] = self.ir['CarIdxClassPosition']
    #     td['CarIdxLap'] = self.ir['CarIdxLap']
    #     td['CarIdxLapCompleted'] = self.ir['CarIdxLapCompleted']
    #     td['CarIdxOnPitRoad'] = self.ir['CarIdxOnPitRoad']

    def update_pit_settings_info(self):
        timestamp = int(self.ir['SessionTime'])
        session_id = self.ir['WeekendInfo']['SessionID']
        sub_session_id = self.ir['WeekendInfo']['SubSessionID']
        
        if 'pit_settings_info' not in self.data:
            self.data['pit_settings_info'] = {}

        if 'pit_settings_info_timestamp' not in self.data:
            self.data['pit_settings_info_timestamp'] = 0
        
        if self.data['pit_settings_info_timestamp'] + self.pit_settings_info_update_rate < timestamp:
            dp = dict()
            dp['dpFastRepair'] = int(self.ir['dpFastRepair'])
            dp['dpFuelAddKg'] = int(self.ir['dpFuelAddKg'])
            dp['dpFuelFill'] = int(self.ir['dpFuelFill'])
            dp['dpLFTireChange'] = int(self.ir['dpLFTireChange'])
            dp['dpLFTireColdPress'] = int(self.ir['dpLFTireColdPress'])
            dp['dpRFTireChange'] = int(self.ir['dpRFTireChange'])
            dp['dpRFTireColdPress'] = int(self.ir['dpRFTireColdPress'])
            dp['dpLRTireChange'] = int(self.ir['dpLRTireChange'])
            dp['dpLRTireColdPress'] = int(self.ir['dpLRTireColdPress'])
            dp['dpRRTireChange'] = int(self.ir['dpRRTireChange'])
            dp['dpRRTireColdPress'] = int(self.ir['dpRRTireColdPress'])
            dp['dpWindshieldTearoff'] = int(self.ir['dpWindshieldTearoff'])

            if self.data['pit_settings_info'] != dp:
                self.signal.emit({
                    "timestamp": timestamp,
                    "session_id": session_id,
                    "sub_session_id": sub_session_id,
                    "pit_settings_info": dp,
                    "message": "PitSettings -> FastRepair: " + str(dp['dpFastRepair']) + "|Fuel(kg): " + str(dp['dpFuelAddKg']) + "|FuelFill: " + str(dp['dpFuelFill']) + "|TireChange(LF/RF/LR/RR): " + str(dp['dpLFTireChange']) + "/" + str(dp['dpRFTireChange']) + "/" + str(dp['dpLRTireChange']) + "/" + str(dp['dpRRTireChange']) + "|TireChange(LF/RF/LR/RR): " + str(dp['dpLFTireColdPress']) + "/" + str(dp['dpRFTireColdPress']) + "/" + str(dp['dpLRTireColdPress']) + "/" + str(dp['dpRRTireColdPress'])
                    })
                self.data['pit_settings_info'] = dp
                self.data['pit_settings_info_timestamp'] = timestamp



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