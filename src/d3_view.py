
#self.earth = examples.planets.load_earth(radius=6378.1)
from pyvistaqt import BackgroundPlotter
import pyvista as pv
from pyvista import examples
from PySide6 import QtWidgets
import numpy as np
from datetime import datetime
from pyorbital.astronomy import gmst
import math

class Earth3DViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Инициализация 3D сцены
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background('black')
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.plotter)
        self.setLayout(layout)
        
        # Параметры
        self.earth_radius = 6371  # км
        self.satellite_size = 500  # радиус спутника
        
        # Создаем Землю
        self.earth = examples.planets.load_earth(radius=6378.1)
        
        # Загружаем текстуру
        try:
            texture = examples.load_globe_texture()
            self.plotter.add_mesh(self.earth, texture=texture, smooth_shading=True)
        except:
            self.plotter.add_mesh(self.earth, color='blue', opacity=0.8)

        self.earth.rotate_z(-180, inplace=True)

        # Создаем объекты для орбиты и спутника
        self.orbit = pv.Spline([(0, 0, 0)])
        self.orbit_actor = self.plotter.add_mesh(self.orbit, color='red', line_width=3)
        
        self.satellite = pv.Sphere(radius=self.satellite_size)
        self.satellite_actor = self.plotter.add_mesh(self.satellite, color='yellow')
        
        # Начальная позиция камеры
        self.reset_camera()
    
    def reset_camera(self):
        """Устанавливаем камеру в стандартное положение"""
        self.plotter.camera.position = (0, -20000, 20000)
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.reset_camera()
    
    def update_view(self, lons, lats, alts, name, station_lon=None, station_lat=None):
        """Обновляем 3D сцену с координатами в ECEF"""
        if len(lons) == 0:
            return
        
        # Удаляем старые акторы
        if hasattr(self, 'orbit_actor'):
            self.plotter.remove_actor(self.orbit_actor)
        if hasattr(self, 'satellite_actor'):
            self.plotter.remove_actor(self.satellite_actor)
        if hasattr(self, 'station_actor'):
            self.plotter.remove_actor(self.station_actor)

        # Конвертируем геодезические координаты в ECEF
        ecef_positions = []
        for lon, lat, alt in zip(lons, lats, alts):
            x, y, z = self.geodetic_to_ecef(lat, lon, alt)
            ecef_positions.append((x, y, z))
        
        # Обновляем орбиту
        if len(ecef_positions) > 1:
            self.orbit = pv.Spline(ecef_positions)
            self.orbit_actor = self.plotter.add_mesh(
                self.orbit, 
                color='red', 
                line_width=3
            )
        
        # Обновляем спутник
        if len(ecef_positions) > 0:
            self.satellite = pv.Sphere(radius=500, center=ecef_positions[0])
            self.satellite_actor = self.plotter.add_mesh(
                self.satellite, color='yellow')
        
        # Добавляем наземную станцию
        if station_lon is not None and station_lat is not None:
            x, y, z = self.geodetic_to_ecef(station_lat, station_lon, 0)
            self.station = pv.Cone(center=(x, y, z), direction=(0, 0, 1), 
                                  height=1000, radius=500, resolution=10)
            self.station_actor = self.plotter.add_mesh(
                self.station, color='green')
        
        # Обновляем заголовок
        if hasattr(self, 'title_actor'):
            self.plotter.remove_actor(self.title_actor)
        self.title_actor = self.plotter.add_text(
            f"Орбита {name} (ECEF)",
            font_size=18
        )
        
        # Принудительное обновление сцены
        self.plotter.update()

    
    def geodetic_to_ecef(self, lat, lon, alt):
        """Конвертация геодезических координат в ECEF (в км)"""
        # Параметры WGS84
        a = 6378.137  # Большая полуось (км)
        e = 0.0818191908426  # Эксцентриситет
        
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Радиус кривизны
        N = a / math.sqrt(1 - (e * math.sin(lat_rad))**2)
        
        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = ((1 - e**2) * N + alt) * math.sin(lat_rad)
        
        return x, y, z