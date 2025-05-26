from src.visualization import plot_2d_trajectory, plot_3d_orbit, get_dummy_trajectory
import numpy as np


class SatelliteTrackerApp:
    """Класс для работы с траекторией спутника."""

    def __init__(self, satellite_name="Спутник-1"):
        self.satellite_name = satellite_name
        self.lons = None
        self.lats = None
        self.positions = None

    def load_real_data(self, lons, lats, positions):
        """Загрузка реальных данных."""
        self.lons = lons
        self.lats = lats
        self.positions = positions

    def show_2d_trajectory(self, station_pos=None):
        """Показать 2D траекторию."""
        if self.lons is None:
            raise ValueError(
                "Данные не загружены. Сначала вызовите load_real_data()")
        station_lon, station_lat = station_pos if station_pos else (None, None)
        plot_2d_trajectory(self.lons, self.lats,
                           self.satellite_name, station_lon, station_lat)

    def show_3d_orbit(self):
        """Показать 3D орбиту."""
        if self.positions is None:
            raise ValueError(
                "Данные не загружены. Сначала вызовите или load_real_data()")
        total = 0
        plot_3d_orbit(self.positions, self.satellite_name)

    def calculate_distance(self):
        """Расчет длины орбиты (пример дополнительного метода)."""
        if self.positions is None:
            raise ValueError("Данные не загружены")

        for i in range(len(self.positions)-1):
            p1 = np.array(self.positions[i])
            p2 = np.array(self.positions[i+1])
            total += np.linalg.norm(p2 - p1)
