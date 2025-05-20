"""Модуль для 2D- и 3D-визуализации траектории спутника."""
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from vpython import sphere, vector, color, scene, canvas
import numpy as np


def plot_2d_trajectory(lons, lats, satellite_name, station_lon=None, station_lat=None):
    """Отображает 2D-траекторию спутника на карте с использованием Cartopy.

    Args:
        lons (list): Список долгот (в градусах).
        lats (list): Список широт (в градусах).
        satellite_name (str): Название спутника.
        station_lon (float, optional): Долгота наземной станции.
        station_lat (float, optional): Широта наземной станции.
    """
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mercator())
    ax.add_feature(cfeature.LAND, facecolor="lightgray")
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS)

    ax.plot(lons, lats, "b-", transform=ccrs.Geodetic(),
            label=f"Траектория {satellite_name}")
    ax.scatter(lons[-1], lats[-1], color="red", s=50,
               transform=ccrs.Geodetic(), label="Текущая позиция")

    if station_lon is not None and station_lat is not None:
        ax.scatter(station_lon, station_lat, color="green", s=100, marker="^",
                   transform=ccrs.Geodetic(), label="Наземная станция")

    ax.legend()
    ax.set_title(f"Траектория спутника {satellite_name}")
    plt.show()


def plot_3d_orbit(positions, satellite_name):
    """Отображает 3D-орбитальную траекторию спутника с использованием VPython.

    Args:
        positions (list): Список векторов позиции (x, y, z в км).
        satellite_name (str): Название спутника.
    """
    canvas()  # Создаём новое окно VPython
    scene.title = f"3D-орбита спутника {satellite_name}"
    scene.background = color.black
    scene.width = 800
    scene.height = 600

    # Земля
    earth = sphere(pos=vector(0, 0, 0), radius=6371, color=color.blue)

    # Спутник
    satellite = sphere(pos=vector(
        *positions[0]), radius=100, color=color.red, make_trail=True)

    # Анимация
    for pos in positions[1:]:
        satellite.pos = vector(*pos)
        scene.waitfor("redraw")


def get_dummy_trajectory():
    """Возвращает тестовую траекторию для отладки.

    Returns:
        tuple: (lons, lats, positions) для 2D и 3D визуализации.
    """
    t = np.linspace(0, 2 * np.pi, 100)
    lons = 360 * np.sin(t)
    lats = 180 * np.cos(t)
    # Позиции в км (для 3D: орбита на высоте 400 км)
    positions = [(6371 * np.cos(theta) + 400, 6371 * np.sin(theta), 400)
                 for theta in t]
    return lons, lats, positions
