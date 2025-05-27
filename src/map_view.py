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
        if event.button == 1:  # Левая кнопка мыши
            self.zoomed = not self.zoomed
            self.update_plot([], [], "")  # Перерисовываем с текущими настройками
    
    def update_plot(self, lons, lats, name, station_lon=None, station_lat=None):
        """Обновляет карту с автоматической обработкой границ"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Сохраняем текущие координаты для приближения
        if len(lons) > 0:
            self.current_lon, self.current_lat = lons[0], lats[0]
        
        # Устанавливаем границы в зависимости от режима
        if self.zoomed and hasattr(self, 'current_lon'):
            # Режим увеличения - центрируем на текущей позиции
            lon_padding = 30  # градусов по долготе
            lat_padding = 20  # градусов по широте
            
            extent = [
                max(-180, self.current_lon - lon_padding),
                min(180, self.current_lon + lon_padding),
                max(-90, self.current_lat - lat_padding),
                min(90, self.current_lat + lat_padding)
            ]
        else:
            # Полный вид
            extent = self.original_extent
        
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        
        # Добавляем особенности карты
        ax.add_feature(cfeature.LAND, facecolor='#e0e0c0')
        ax.add_feature(cfeature.OCEAN, facecolor='#c0e0ff')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        # Отображаем траекторию
        if len(lons) > 1:
            ax.plot(lons, lats, 'r-', transform=ccrs.Geodetic(),
                    linewidth=1.5, alpha=0.7, label='Траектория')
        
        # Текущая позиция спутника
        if len(lons) > 0:
            ax.scatter(lons[0], lats[0], color='red', s=40,
                     transform=ccrs.Geodetic(), label='Спутник')
        
        # Наземная станция
        if station_lon and station_lat:
            ax.scatter(station_lon, station_lat, color='blue', s=60, marker='^',
                     transform=ccrs.Geodetic(), label='Станция')
        
        # Настройка сетки
        ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        ax.legend(loc='upper right')
        
        title = f'Траектория {name}'
        if self.zoomed:
            title += ' (увеличенный вид)'
        ax.set_title(title, fontsize=10)
        
        self.canvas.draw()