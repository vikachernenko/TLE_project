from pyorbital.orbital import Orbital
from vpython import vector
import math
#from datetime import datetime, timedelta

class Satellite:
    def __init__(self, sat_name, tle1, tle2 ):
        """
        Инициализация спутника

        :param sat_name: Название спутника
        :param tle1: Первая строка TLE
        :param tle2: Вторая строка TLE
        """
        self.name = sat_name
        self.tle1 = tle1
        self.tle2 = tle2
        self.orb = Orbital(sat_name, line1=tle1, line2=tle2)

    def calculate_satellite_position(self, timestamp):
        """
        Рассчитывает позицию спутника в системе EarthMJ2000 и географические координаты.
        
        :param timestamp: Временная метка (datetime в UTC)
        :return: Словарь с координатами спутника
        """

        position = self.orb.get_position(timestamp, normalize=False)[0]
        lon, lat, alt = self.orb.get_lonlatalt(timestamp)

        x, y, z = self.lla_to_ecef(lat, lon, alt)
        
        return {
            'latitude': lat,
            'longitude': lon,
            'ecef': (x, y, z),
            'earth_mj2000': position,
            'altitude': alt
        }
    
    def get_observer_look(self, ground_station, timestamp):
        """
        Рассчитывает позицию спутника в сферической системе координат относительно наблюдателя
        
        :param ground_station: Словарь с 'lat', 'lon', 'alt' станции
        :param timestamp: Временная метка (datetime в UTC)
        :return: Словарь с азимутом и возвышением
        """

        az,elev=self.orb.get_observer_look(timestamp, ground_station['lon'], ground_station['lat'], ground_station['alt'])
        return{
            'azimuth': az,
            'elevation': elev 
        }

    def get_contacts_times(self, ground_station, timestamp, duration, horizon = 0.0):
        """
        Находит ближайшее время контакта спутника с наземной станцией.

        :param ground_station: Словарь с 'lat', 'lon', 'alt' станции
        :param timestamp: Начало периода поиска (datetime в UTC)
        :param duration: В течении скольки часов искать контакт
        :param horizon: Минимальный угол возвыщения (по умочанию 0.0)
        :return: Массив кортежей (время начала контакта, время конца контакта, время максимального возвышения) (datetime в UTC)
        """
        return self.orb.get_next_passes(timestamp, duration, ground_station['lon'], ground_station['lat'], ground_station['alt'], horizon)
    
    def lla_to_ecef(self, lat, lon, alt):
        """Конвертация широты, долготы, высоты в ECEF"""
        # WGS84 параметры
        a = 6378137.0  # большая полуось (м)
        e = 0.0818191908426  # эксцентриситет
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Вычисление N - радиус кривизны
        N = a / math.sqrt(1 - (e * math.sin(lat_rad))**2)
        
        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = ((1 - e**2) * N + alt) * math.sin(lat_rad)
        
        return x/1000, y/1000, z/1000  # Конвертируем в км