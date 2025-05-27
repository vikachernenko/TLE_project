
# self.earth = examples.planets.load_earth(radius=6378.1)
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
            self.plotter.add_mesh(
                self.earth, texture=texture, smooth_shading=True)
        except:
            self.plotter.add_mesh(self.earth, color='blue', opacity=0.8)

        self.earth.rotate_z(-180, inplace=True)

        # Создаем объекты для орбиты и спутника
        self.orbit = pv.Spline([(0, 0, 0)])
        self.orbit_actor = self.plotter.add_mesh(
            self.orbit, color='red', line_width=3)

        self.satellite = pv.Sphere(radius=self.satellite_size)
        self.satellite_actor = self.plotter.add_mesh(
            self.satellite, color='yellow')
        self.add_star_background()

        # Начальная позиция камеры
        self.reset_camera()

    def add_star_background(self):
        """Добавляет звезды на фон (исправленная версия)"""
        np.random.seed(42)

        # Создаем несколько групп звезд с разными размерами
        for size in [1, 2, 3]:
            # Создаем массив случайных точек для звезд
            stars = np.random.uniform(-50000, 50000, size=(300, 3))

            # Добавляем звезды на сцену с фиксированным размером
            self.plotter.add_mesh(
                pv.PolyData(stars),
                render_points_as_spheres=True,
                point_size=size,  # Теперь передаем число, а не массив
                color='white',
                opacity=0.7,
                name=f'stars_{size}'
            )

    def reset_camera(self):
        """Устанавливаем камеру в стандартное положение"""
        self.plotter.reset_camera()
        self.plotter.camera.position = (0, -15000, 15000)  # Ближе к Земле
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.camera.view_angle = 45  # Умеренное поле зрения

    def update_view(self, lons, lats, alts, name, station_lon=None, station_lat=None):
        """Обновляем 3D сцену с координатами в ECEF"""
        if len(lons) == 0:
            return

        # Удаляем старые акторы
        
        if hasattr(self, 'station_actor'):
            self.plotter.remove_actor(self.station_actor)

        # Конвертируем геодезические координаты в ECEF
        ecef_positions = []
        for lon, lat, alt in zip(lons, lats, alts):
            x, y, z = self.geodetic_to_ecef(lat, lon, alt)
            ecef_positions.append((x, y, z))

        if len(ecef_positions) > 1:
            new_orbit = pv.Spline(ecef_positions)
            if hasattr(self, 'orbit'):
                # Обновляем данные существующего меша вместо удаления/создания
                self.orbit.copy_from(new_orbit)
                self.plotter.update()
            else:
                self.orbit = new_orbit
                self.orbit_actor = self.plotter.add_mesh(
                    self.orbit,
                    color='red',
                    line_width=3
                )

    # Обновляем спутник
        if len(ecef_positions) > 0:
            new_satellite = pv.Sphere(radius=500, center=ecef_positions[0])
            if hasattr(self, 'satellite'):
                self.satellite.copy_from(new_satellite)
                self.plotter.update()
            else:
                self.satellite = new_satellite
                self.satellite_actor = self.plotter.add_mesh(
                    self.satellite, color='yellow')
            
            # Обновляем метку
            if hasattr(self.plotter, 'satellite_label'):
                self.plotter.remove_actor('satellite_label')
            self.plotter.add_point_labels(
                ecef_positions[0],
                [name],
                font_size=12,
                text_color='yellow',
                shadow=True,
                font_family='arial',
                name='satellite_label'
            )

        # Обновляем наземную станцию
        if station_lon is not None and station_lat is not None:
            x, y, z = self.geodetic_to_ecef(station_lat, station_lon, 0)
            if hasattr(self, 'station'):
                new_station = pv.Cone(center=(x, y, z), direction=(0, 0, 1),
                                height=500, radius=200, resolution=10)
                self.station.copy_from(new_station)
                self.plotter.update()
            else:
                self.station = pv.Cone(center=(x, y, z), direction=(0, 0, 1),
                                    height=500, radius=200, resolution=10)
                self.station_actor = self.plotter.add_mesh(
                    self.station, color='red')

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
