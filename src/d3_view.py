from pyvistaqt import BackgroundPlotter
import pyvista as pv
from pyvista import examples
from PySide6 import QtWidgets
import numpy as np
import math
from typing import Dict, List, Optional, Tuple


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
        self.orbit_width = 3       # ширина линии орбиты

        # Создаем Землю
        self._init_earth()
        self._init_stars()
        self._init_station()
        self.reset_camera()

        # Хранилище объектов спутников
        self.satellites: Dict[str, dict] = {}

    def _init_earth(self):
        """Инициализация модели Земли"""
        self.earth = examples.planets.load_earth(radius=6378.1)
        try:
            texture = examples.load_globe_texture()
            self.plotter.add_mesh(self.earth, texture=texture, 
                                 smooth_shading=True, name='earth')
        except:
            self.plotter.add_mesh(self.earth, color='blue', 
                                 opacity=0.8, name='earth')
        self.earth.rotate_z(-180, inplace=True)

    def _init_stars(self):
        """Инициализация фона со звездами"""
        np.random.seed(42)
        for size in [1, 2, 3]:
            stars = np.random.uniform(-50000, 50000, size=(300, 3))
            self.plotter.add_mesh(
                pv.PolyData(stars),
                render_points_as_spheres=True,
                point_size=size,
                color='white',
                opacity=0.7,
                name=f'stars_{size}'
            )

    def _init_station(self):
        """Инициализация наземной станции"""
        self.station = None
        self.station_actor = None

    def reset_camera(self):
        """Сброс положения камеры"""
        self.plotter.reset_camera()
        self.plotter.camera.position = (0, -15000, 15000)
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.up = (0, 0, 1)
        self.plotter.camera.view_angle = 45

    def update_view(self, satellites_data: List[dict], 
                   station_lon: Optional[float] = None, 
                   station_lat: Optional[float] = None):
        """Обновление 3D сцены"""
        try:
            # Обновляем наземную станцию
            self._update_station(station_lon, station_lat)

            # Удаляем спутники, которых больше нет
            self._remove_old_satellites(satellites_data)

            # Добавляем/обновляем спутники
            for sat_data in satellites_data:
                self._update_satellite(sat_data)

            self.plotter.update()
        except Exception as e:
            print(f"Ошибка обновления 3D вида: {str(e)}")

    def _update_station(self, lon: Optional[float], lat: Optional[float]):
        """Обновление позиции наземной станции"""
        if lon is None or lat is None:
            return

        x, y, z = self.geodetic_to_ecef(lat, lon, 0)
        
        if self.station is None:
            # Создаем новую станцию
            self.station = pv.Cone(center=(x, y, z), direction=(0, 0, 1),
                                 height=500, radius=200)
            self.station_actor = self.plotter.add_mesh(
                self.station, color='red', name='station')
        else:
            # Обновляем существующую станцию
            self.station = pv.Cone(center=(x, y, z), direction=(0, 0, 1),
                                    height=500, radius=200, resolution=10)
            self.station_actor = self.plotter.add_mesh(
                    self.station, color='red')

    def _remove_old_satellites(self, satellites_data: List[dict]):
        """Удаление спутников, которых больше нет в данных"""
        current_names = {sat['name'] for sat in satellites_data}
        for name in list(self.satellites.keys()):
            if name not in current_names:
                self._remove_satellite(name)

    def _update_satellite(self, sat_data: dict):
        """Обновление данных одного спутника"""
        name = sat_data['name']
        lons = sat_data['lons']
        lats = sat_data['lats']
        alts = sat_data['alts']
        color = sat_data['color']

        # Конвертируем цвет
        color_rgb = (color.red()/255, color.green()/255, color.blue()/255)

        # Конвертируем координаты
        ecef_positions = [self.geodetic_to_ecef(lat, lon, alt) 
                         for lon, lat, alt in zip(lons, lats, alts)]

        if name not in self.satellites:
            # Создаем новый спутник
            self._create_satellite(name, ecef_positions, color_rgb)
        else:
            # Обновляем существующий спутник
            self._update_existing_satellite(name, ecef_positions, color_rgb)

    def _create_satellite(self, name: str, 
                         positions: List[Tuple[float, float, float]], 
                         color: Tuple[float, float, float]):
        """Создание нового спутника"""
        if not positions:
            return

        # Создаем орбиту
        orbit = pv.Spline(positions) if len(positions) > 1 else None
        
        # Создаем спутник
        satellite = pv.Sphere(radius=self.satellite_size, 
                             center=positions[0])

        # Добавляем на сцену
        orbit_actor = self.plotter.add_mesh(
            orbit, color=color, line_width=self.orbit_width, 
            name=f'orbit_{name}') if orbit else None
        
        sat_actor = self.plotter.add_mesh(
            satellite, color=color, name=f'sat_{name}')
        
        label = self.plotter.add_point_labels(
            [positions[0]], [name],
            font_size=10, text_color=color,
            shadow=True, name=f'label_{name}'
        )

        # Сохраняем в хранилище
        self.satellites[name] = {
            'orbit': orbit,
            'satellite': satellite,
            'orbit_actor': orbit_actor,
            'satellite_actor': sat_actor,
            'label': label,
            'color': color
        }

    def _update_existing_satellite(self, name: str, 
                                  positions: List[Tuple[float, float, float]], 
                                  color: Tuple[float, float, float]):
        """Обновление существующего спутника"""
        if not positions or name not in self.satellites:
            return

        sat = self.satellites[name]
        current_pos = positions[0]

        # Обновляем орбиту
        if len(positions) > 1 and sat['orbit'] is not None:
            new_orbit = pv.Spline(positions)
            sat['orbit'].copy_from(new_orbit)

        # Обновляем позицию спутника
        satellite = pv.Sphere(radius=self.satellite_size, 
                             center=current_pos)
        sat['satellite'].copy_from (satellite)

        # Обновляем метку (удаляем старую и создаем новую)
        self.plotter.remove_actor(f'label_{name}')
        sat['label'] = self.plotter.add_point_labels(
            [current_pos], [name],
            font_size=10, text_color=color,
            shadow=True, name=f'label_{name}'
        )

    def _remove_satellite(self, name: str):
        """Удаление спутника со сцены"""
        if name not in self.satellites:
            return

        sat = self.satellites[name]
        
        # Удаляем все компоненты
        if sat['orbit_actor']:
            self.plotter.remove_actor(f'orbit_{name}')
        if sat['satellite_actor']:
            self.plotter.remove_actor(f'sat_{name}')
        if sat['label']:
            self.plotter.remove_actor(f'label_{name}')
        
        del self.satellites[name]

    def clear_view(self):
        """Очистка сцены от всех спутников"""
        for name in list(self.satellites.keys()):
            self._remove_satellite(name)
        self.plotter.update()

    @staticmethod
    def geodetic_to_ecef(lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """Конвертация геодезических координат в ECEF (в км)"""
        a = 6378.137  # Большая полуось (км)
        e = 0.0818191908426  # Эксцентриситет

        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        N = a / math.sqrt(1 - (e * math.sin(lat_rad))**2)

        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = ((1 - e**2) * N + alt) * math.sin(lat_rad)

        return (x, y, z)