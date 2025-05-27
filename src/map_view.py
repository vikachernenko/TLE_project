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
        
        # Флаг для отслеживания состояния приближения
        self.zoomed = False
        self.original_extent = None
        
        # Подключаем обработчик событий мыши
        self.canvas.mpl_connect('button_press_event', self.on_click)
    
    def on_click(self, event):
        """Обработчик клика для приближения/отдаления"""
        if event.button == 1:  # Левая кнопка мыши
            if not self.zoomed and hasattr(self, 'current_lon') and hasattr(self, 'current_lat'):
                # Запоминаем исходные границы
                if self.original_extent is None:
                    ax = self.figure.axes[0]
                    self.original_extent = ax.get_extent()
                
                # Приближаем к текущей позиции спутника
                ax = self.figure.axes[0]
                lon, lat = self.current_lon, self.current_lat
                ax.set_extent([lon-30, lon+30, lat-15, lat+15], 
                             crs=ccrs.PlateCarree())
                self.zoomed = True
            else:
                # Возвращаем исходные границы
                if self.original_extent is not None:
                    ax = self.figure.axes[0]
                    ax.set_extent(self.original_extent, crs=ccrs.PlateCarree())
                    self.zoomed = False
            self.canvas.draw()
    
    def update_plot(self, lons, lats, name, station_lon=None, station_lat=None):
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree(), facecolor='#f0f0f0')
        
        # Сохраняем текущие координаты для приближения
        if len(lons) > 0:
            self.current_lon, self.current_lat = lons[0], lats[0]
        
        # Упрощенная карта земли
        ax.add_feature(cfeature.LAND, facecolor='#e0e0c0')
        ax.add_feature(cfeature.OCEAN, facecolor='#c0e0ff')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        # Траектория спутника
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
        
        # Добавляем линии для лучшей видимости
        ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        
        ax.legend(loc='upper right')
        ax.set_title(f'Траектория спутника {name} (кликните для приближения)', fontsize=10)

        if not self.zoomed:
            # Запоминаем исходные границы
            if self.original_extent is None:
                ax = self.figure.axes[0]
                self.original_extent = ax.get_extent()
            
            # Приближаем к текущей позиции спутника
            ax = self.figure.axes[0]
            lon, lat = self.current_lon, self.current_lat
            ax.set_extent([lon-30, lon+30, lat-15, lat+15], 
                            crs=ccrs.PlateCarree())
        else:
            # Возвращаем исходные границы
            if self.original_extent is not None:
                ax = self.figure.axes[0]
                ax.set_extent(self.original_extent, crs=ccrs.PlateCarree())

        self.canvas.draw()