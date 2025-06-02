import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets


class Map2DWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Настройка темного стиля matplotlib
        plt.style.use('dark_background')

        self.figure = plt.figure(figsize=(10, 6), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)

        # Инициализируем границы
        self.original_extent = [-180, 180, -90, 90]  # Весь мир
        self.zoomed = False

        # Подключаем обработчик событий мыши
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        """Обработчик клика для приближения/отдаления"""
        # if event.button == 1:  # Левая кнопка мыши
        #    self.zoomed = not self.zoomed
        #    self.update_plot([], [], None, None)

    def setup_dark_map(self, ax):
        """Настраивает темный стиль для карты"""
        # Цвета фона и элементов
        ax.set_facecolor('#1e1e1e')

        # Особенности карты в темных тонах
        ax.add_feature(cfeature.LAND, facecolor='#2d2d2d')
        ax.add_feature(cfeature.OCEAN, facecolor='#1a1a2e')
        ax.add_feature(cfeature.COASTLINE, edgecolor='#4d4d4d', linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=':',
                       edgecolor='#4d4d4d', linewidth=0.5)

        # Сетка
        gl = ax.gridlines(
            crs=ccrs.PlateCarree(),
            color='#4d4d4d',
            alpha=0.5,
            linestyle='--',
            draw_labels=True
        )
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'color': '#aaaaaa'}
        gl.ylabel_style = {'color': '#aaaaaa'}

    def update_plot(self, satellites_data, station_lon=None, station_lat=None):
        """Обновляет карту с темной темой"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())

        # Применяем темный стиль
        self.setup_dark_map(ax)

        # Устанавливаем границы
        if self.zoomed and satellites_data:
            all_lons = [lon for sat in satellites_data for lon in sat['lons']]
            all_lats = [lat for sat in satellites_data for lat in sat['lats']]

            if all_lons and all_lats:
                extent = [
                    max(-180, min(all_lons) - 30),
                    min(180, max(all_lons) + 30),
                    max(-90, min(all_lats) - 20),
                    min(90, max(all_lats) + 20)
                ]
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent(self.original_extent, crs=ccrs.PlateCarree())
        else:
            ax.set_extent(self.original_extent, crs=ccrs.PlateCarree())

        # Отображаем траектории спутников
        for sat_data in satellites_data:
            lons = sat_data['lons']
            lats = sat_data['lats']
            name = sat_data['name']
            color = sat_data['color']

            color_hex = "#{:02x}{:02x}{:02x}".format(
                color.red(), color.green(), color.blue())

            if len(lons) > 1:
                ax.plot(lons, lats, '-', transform=ccrs.Geodetic(),
                        color=color_hex, linewidth=1.8, alpha=1)

            if len(lons) > 0:
                ax.scatter(lons[0], lats[0], color=color_hex, s=50,
                           transform=ccrs.Geodetic(), edgecolors='white',
                           label=f'{name}')

        # Наземная станция
        if station_lon is not None and station_lat is not None:
            ax.scatter(station_lon, station_lat, color='#42a5f5', s=80,
                       marker='^', transform=ccrs.Geodetic(),
                       edgecolor='white', label='Станция')

        # Легенда
        if satellites_data or (station_lon and station_lat):
            ax.legend(loc='upper right', facecolor='#2d2d2d',
                      edgecolor='none', fontsize=9)

        # Заголовок
        title = 'Траектории спутников'
        if self.zoomed:
            title += ' (увеличенный вид)'
        ax.set_title(title, color='white', pad=15, fontsize=11)

        self.canvas.draw()

    def clear_plot(self):
        """Очищает карту"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection=ccrs.PlateCarree())
        self.setup_dark_map(ax)
        self.canvas.draw()
