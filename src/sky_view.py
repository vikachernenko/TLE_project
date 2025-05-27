import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets, QtCore
from matplotlib.patches import Circle
import math
from scipy.interpolate import make_smoothing_spline


class SkyViewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Основной layout
        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # График небесной сферы
        self.figure = plt.figure(figsize=(6, 6), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        
        # Панель информации о спутниках
        self.info_panel = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(self.info_panel)
        info_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок панели
        title = QtWidgets.QLabel("Текущие положения:")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        info_layout.addWidget(title)
        
        # Прокручиваемый список спутников
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.sat_container = QtWidgets.QWidget()
        self.sat_layout = QtWidgets.QVBoxLayout(self.sat_container)
        self.sat_layout.setAlignment(QtCore.Qt.AlignTop)
        self.scroll_area.setWidget(self.sat_container)
        
        # Стилизация
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #1e1e1e;
                border-radius: 5px;
            }
        """)
        
        info_layout.addWidget(self.scroll_area)
        
        # Добавляем виджеты в основной layout
        main_layout.addWidget(self.canvas, 70)  # 70% ширины
        main_layout.addWidget(self.info_panel, 30)  # 30% ширины
        
        # Стилизация панели
        self.info_panel.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                border-radius: 5px;
            }
        """)

    def _create_satellite_info_widget(self, name, azimuth, elevation, color):
        """Создает виджет с информацией о спутнике"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Цветной индикатор
        color_indicator = QtWidgets.QFrame()
        color_indicator.setFixedSize(15, 15)
        color_indicator.setStyleSheet(f"""
            background: rgb({color.red()}, {color.green()}, {color.blue()});
            border-radius: 7px;
        """)
        
        # Название спутника
        name_label = QtWidgets.QLabel(name)
        name_label.setStyleSheet("font-weight: bold; color: white;")
        
        # Положение
        pos_label = QtWidgets.QLabel(f"Азимут: {azimuth:.1f}°\nВысота: {elevation:.1f}°")
        pos_label.setStyleSheet("color: #CCCCCC;")
        
        # Горизонтальный layout для цветного индикатора и названия
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(color_indicator)
        top_layout.addWidget(name_label)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        layout.addWidget(pos_label)
        
        # Разделитель
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("color: #333333;")
        layout.addWidget(separator)
        
        return widget

    def update_plot(self, satellites_data, passes_data=None):
        """Обновляет вид небесной сферы и панель информации"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, polar=True, facecolor='#1e1e1e')
        self.setup_view(ax)
        # Очищаем список спутников
        for i in reversed(range(self.sat_layout.count())): 
            self.sat_layout.itemAt(i).widget().setParent(None)

        # Отображаем пролеты спутников (без легенды)
        if passes_data:
            for pass_item in passes_data:
                pass_data, color, sat_name = pass_item
                if len(pass_data['azimuths']) > 3:
                    az = np.array(pass_data['azimuths'])
                    el = np.array(pass_data['elevations'])

                    # Нормализуем азимуты
                    az = np.where(az < 0, az + 360, az)
                    sort_idx = np.argsort(az)
                    az = np.radians(az[sort_idx])
                    el = np.clip(90 - el[sort_idx], 0, 90)

                    # Разбиваем на сегменты при разрывах
                    diffs = np.diff(az)
                    split_indices = np.where(diffs > np.pi)[0] + 1
                    segments = np.split(np.column_stack((az, el)), split_indices) if len(split_indices) > 0 else [np.column_stack((az, el))]

                    # Конвертируем цвет
                    mpl_color = (color.red()/255, color.green()/255, color.blue()/255)

                    # Рисуем сегменты
                    for segment in segments:
                        if len(segment) > 3:
                            try:
                                spline = make_smoothing_spline(segment[:,0], segment[:,1])
                                az_new = np.linspace(segment[:,0].min(), segment[:,0].max(), 100)
                                ax.plot(az_new, spline(az_new), color=mpl_color, linewidth=2, alpha=0.7)
                            except:
                                ax.plot(segment[:,0], segment[:,1], color=mpl_color, linewidth=2, alpha=0.7)

        # Обрабатываем текущие положения спутников
        for sat_data in satellites_data:
            azimuth = sat_data['azimuth']
            elevation = sat_data['elevation']
            name = sat_data['name']
            color = sat_data['color']

            if azimuth is not None and elevation is not None:
                # Отображение на графике
                rad_az = math.radians(azimuth % 360)
                clipped_elev = max(0, min(90, 90 - elevation))
                mpl_color = (color.red()/255, color.green()/255, color.blue()/255)
                
                ax.plot(rad_az, clipped_elev, 'o', 
                       color=mpl_color, 
                       markersize=8, 
                       markeredgecolor='white', 
                       markeredgewidth=1)

                # Добавляем информацию в панель
                sat_widget = self._create_satellite_info_widget(name, azimuth, elevation, color)
                self.sat_layout.addWidget(sat_widget)

        # Настройка заголовка
        ax.set_title('Небесная сфера', color='white', pad=15, fontsize=10)
        self.canvas.draw()

    def setup_view(self, ax):
        # Настройка полярного графика
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_xticks(np.radians(range(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], 
                          color='white', fontsize=8)

        # Устанавливаем метки для оси Y
        yticks = range(0, 91, 30)
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{90-x}°' for x in yticks], color='white', fontsize=8)

        # Сетка и оформление
        ax.grid(True, linestyle='--', alpha=0.3, color='white')

        # Рисуем зенит и горизонт
        ax.add_patch(Circle((0, 0), 90, transform=ax.transData._b,
                     facecolor='#000033', alpha=0.5, edgecolor='none'))


    def clear_plot(self):
        """Очищает график и панель информации"""
        self.figure.clear()
        for i in reversed(range(self.sat_layout.count())): 
            self.sat_layout.itemAt(i).widget().setParent(None)
        ax = self.figure.add_subplot(111, polar=True, facecolor='#1e1e1e')
        self.setup_view(ax)
        self.canvas.draw()