# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 26.04.26.0

Coordinate systems:
1. TEME (True Equator, Mean Equinox), km
2. ECEF (Earth-Centered, Earth-Fixed), km
3. AER (Azimuth, Elevation, Range)
'''

import numpy as np
from numpy import sin, cos, sqrt, arctan2, radians, degrees
from datetime import datetime
from zoneinfo import ZoneInfo
from sgp4.api import Satrec, jday
import pymap3d as pm


# Константы Земли (WGS-84)
WGS84_A = 6378.137
WGS84_F = 1 / 298.257223563


class Satellite:
    def __init__(self, sat: str, TLE_parsed: list):
        self.name = sat
        self.TLE = TLE_parsed
        self.satrec = Satrec.twoline2rv(TLE_parsed[0], TLE_parsed[1])
        self.teme = [0, 0]
    
    # Возвращает r (км) и v (км/с) в ИСО Земли (TEME)
    def get_state_vector(self, now: datetime):
        # Юлианская дата
        jd_base, jd_frac = jday(now.year, now.month, now.day, now.hour, now.minute, now.second + now.microsecond/1e6)

        # Модель SGP4
        error, r, v = self.satrec.sgp4(jd_base, jd_frac)

        self.teme = np.array([r, v])
            
        return np.array([r, v])

    # TEME -> географические координаты подспутниковой точки
    def get_subsatellite_point(self, state, now: datetime): 
        r_ecef = teme_to_ecef(state, now)
        x, y, z = r_ecef
    
        # Долгота (вычисляется напрямую из ECEF)
        lon = arctan2(y, x)
    
        # Широта (итеративный метод Bowring)
        rho = sqrt(x**2 + y**2)
        lat = arctan2(z, rho)
        e2 = WGS84_F * (2 - WGS84_F)
    
        for i in range(3):
            n = WGS84_A / sqrt(1 - e2 * sin(lat)**2)
            lat = arctan2(z + n * e2 * sin(lat), rho)
        
        return degrees(lat), degrees(lon)

    def __repr__(self):
        return f"Satellite('{self.name}', TEME_r={self.teme[0]},\nTEME_v={self.teme[1]})"


class GroundStation:
    def __init__(self, name: str, lat: float, lon: float, alt: float = 0.0):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.alt = alt

        # Константы WGS-84
        self._a = 6378.137
        self._f = 1 / 298.257223563
        self._e2 = self._f * (2 - self._f)

    # Геодезические координаты (lat, lon, alt) -> ECEF
    def get_ecef_coordinates(self):
        # pymap3d работает в метрах
        x, y, z = pm.geodetic2ecef(self.lat, self.lon, self.alt * 1000)
    
        return np.array([x, y, z]) / 1000.0

    def __repr__(self):
        return f"GroundStation('{self.name}', lat={self.lat}, lon={self.lon}, alt={self.alt})"


# Звездное время в Гринвиче (GMST)
def get_gmst(now: datetime):
    # Юлианская дата
    jd_base, jd_frac = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
    jd = jd_base + jd_frac

    # Эпоха J2000.0. Время в юлианских столетиях
    t = (jd - 2451545.0) / 36525.0

    # GMST = A + B t + C t^2 + D t^3
    # Учитываем прецессию и нутацию оси вращения Земли (члены C, D)
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * t**2 - t**3 / 38710000.0
    
    return radians(gmst % 360)


# TEME -> ECEF
def teme_to_ecef(state, now: datetime):
    r_teme = state[0]
    
    gmst = get_gmst(now)
    
    # Поворот вокруг оси Z на угол звездного времени
    cos_g = cos(gmst)
    sin_g = sin(gmst)
    
    Rz = np.array([[cos_g, sin_g, 0],
                   [-sin_g, cos_g, 0],
                   [0, 0, 1]])
    
    r_ecef = Rz @ r_teme
    
    return r_ecef


# TEME -> топоцентрическая СК (для наведения антенны), азимут Az и высота над горизонтом El
def get_az_el(coord, pos, ground_station, dt: datetime):
    if coord: r_ecef_sat = teme_to_ecef(pos, dt) # coord = 1 - TEME
    else: r_ecef_sat = pos # coord = 0 - ECEF
    
    # pymap3d работает в метрах
    az, el, rng = pm.ecef2aer(r_ecef_sat[0] * 1000, 
                              r_ecef_sat[1] * 1000, 
                              r_ecef_sat[2] * 1000, 
                              ground_station.lat, 
                              ground_station.lon, 
                              ground_station.alt * 1000)
    
    return az, el, rng / 1000


def get_dt(location):
    dt = datetime.now(ZoneInfo(location))
    
    if not dt:
        return "ERROR: Не удалось получить точное время. Проверьте локацию."
    
    return dt
