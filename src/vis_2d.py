import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets
import numpy as np

class Map2DWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure(figsize=(10, 6))
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
            if not self.zoomed:
                # Запоминаем исходные границы
                if self.original_extent is None:
                    ax = self.figure.axes[0]
                    self.original_extent = ax.get_extent()
                
                # Приближаем к текущей позиции спутника
                if hasattr(self, 'current_lon') and hasattr(self, 'current_lat'):
                    ax = self.figure.axes[0]
                    lon, lat = self.current_lon, self.current_lat
                    ax.set_extent([lon-30, lon+30, lat-20, lat+20], 
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
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Сохраняем текущие координаты для приближения
        if len(lons) > 0:
            self.current_lon, self.current_lat = lons[0], lats[0]
        
        ax.add_feature(cfeature.LAND, facecolor='lightgray')
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        ax.plot(lons, lats, 'b-', transform=ccrs.Geodetic(),
                label=f'Траектория {name}')
        ax.scatter(lons[0], lats[0], color='red', s=50,
                   transform=ccrs.Geodetic(), label='Текущая позиция')
        
        if station_lon and station_lat:
            ax.scatter(station_lon, station_lat, color='green', s=100, marker='^',
                       transform=ccrs.Geodetic(), label='Станция')
        
        # Добавляем линии для лучшей видимости
        ax.gridlines(draw_labels=True)
        
        ax.legend()
        ax.set_title(f'Траектория {name} (кликните для приближения)')

        if not self.zoomed:
            # Запоминаем исходные границы
            if self.original_extent is None:
                ax = self.figure.axes[0]
                self.original_extent = ax.get_extent()
            
            # Приближаем к текущей позиции спутника
            if hasattr(self, 'current_lon') and hasattr(self, 'current_lat'):
                ax = self.figure.axes[0]
                lon, lat = self.current_lon, self.current_lat
                ax.set_extent([lon-30, lon+30, lat-20, lat+20], 
                                crs=ccrs.PlateCarree())
        else:
            # Возвращаем исходные границы
            if self.original_extent is not None:
                ax = self.figure.axes[0]
                ax.set_extent(self.original_extent, crs=ccrs.PlateCarree())
                
        self.canvas.draw()