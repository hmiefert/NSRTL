from tinydb import TinyDB, Query
from os.path import exists, join
from os import mkdir


class JsonStorage:
    def __init__(self):
        self.data_dir = "data"
        self.dir_check()
        self.weekend = TinyDB(join(self.data_dir, "weekend.json"))
        self.weather = TinyDB(join(self.data_dir, "weather.json"))
        self.driver = TinyDB(join(self.data_dir, "driver.json"))
        self.session = TinyDB(join(self.data_dir, "session.json"))
        self.pit_settings = TinyDB(join(self.data_dir, "pit_settings.json"))

    def dir_check(self):
        if not exists(self.data_dir):
            mkdir(self.data_dir)

    def insert_weekend_info(self, wk):
        self.weekend.insert(wk)

    def insert_session_info(self, s):
        self.session.insert(s)

    def insert_weather_info(self, w):
        self.weather.insert(w)

    def insert_driver_info(self, d):
        self.driver.insert(d)

    def insert_pit_settings_info(self, b):
        self.pit_settings.insert(b)
