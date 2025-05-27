import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets
import numpy as np


class Map2DWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure(figsize=(10, 6), facecolor='#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Инициализируем границы сразу
        self.original_extent = [-180, 180, -90, 90]  # Весь мир
        self.zoomed = False

        # Подключаем обработчик событий мыши
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Обработчик клика для приближения/отдаления"""
        #if event.button == 1:  # Левая кнопка мыши
            #self.zoomed = not self.zoomed
            # Перерисовываем с текущими настройками
           # self.update_plot([], [], "")

    def update_plot(self, satellites_data, station_lon=None, station_lat=None):
        """Обновляет карту с автоматической обработкой границ"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())

        # Устанавливаем границы в зависимости от режима
        if self.zoomed and satellites_data:
            # Режим увеличения - центрируем на текущих позициях
            all_lons = [lon for sat in satellites_data for lon in sat['lons']]
            all_lats = [lat for sat in satellites_data for lat in sat['lats']]
            
            if all_lons and all_lats:
                lon_padding = 30  # градусов по долготе
                lat_padding = 20  # градусов по широте
                
                min_lon, max_lon = min(all_lons), max(all_lons)
                min_lat, max_lat = min(all_lats), max(all_lats)
                
                extent = [
                    max(-180, min_lon - lon_padding),
                    min(180, max_lon + lon_padding),
                    max(-90, min_lat - lat_padding),
                    min(90, max_lat + lat_padding)
                ]
            else:
                extent = self.original_extent
        else:
            # Полный вид
            extent = self.original_extent

        ax.set_extent(extent, crs=ccrs.PlateCarree())

        # Добавляем особенности карты
        ax.add_feature(cfeature.LAND, facecolor='#e0e0c0')
        ax.add_feature(cfeature.OCEAN, facecolor='#c0e0ff')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)

        # Отображаем траектории всех спутников
        for sat_data in satellites_data:
            lons = sat_data['lons']
            lats = sat_data['lats']
            name = sat_data['name']
            color = sat_data['color']
            
            # Преобразуем QColor в hex для matplotlib
            color_hex = "#{:02x}{:02x}{:02x}".format(
                color.red(), color.green(), color.blue())
            
            if len(lons) > 1:
                ax.plot(lons, lats, '-', transform=ccrs.Geodetic(),
                        color=color_hex, linewidth=1.5, alpha=0.7)

            # Текущая позиция спутника
            if len(lons) > 0:
                ax.scatter(lons[0], lats[0], color=color_hex, s=40,
                           transform=ccrs.Geodetic(), label=f'{name}')

        # Наземная станция
        if station_lon and station_lat:
            ax.scatter(station_lon, station_lat, color='blue', s=60, marker='^',
                       transform=ccrs.Geodetic(), label='Станция')

        # Настройка сетки
        ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        
        # Легенда только если есть что отображать
        if satellites_data or (station_lon and station_lat):
            ax.legend(loc='upper right')

        title = 'Траектории спутников'
        if self.zoomed:
            title += ' (увеличенный вид)'
        ax.set_title(title, fontsize=10)

        self.canvas.draw()
        
    def clear_plot(self):
        """Очищает карту"""
        self.figure.clear()
        self.canvas.draw()