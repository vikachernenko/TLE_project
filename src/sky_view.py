import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets
from matplotlib.patches import Circle
import math
from scipy.interpolate import make_smoothing_spline

class SkyViewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure(figsize=(8, 8), facecolor='black')
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)
        
    def update_plot(self, azimuth, elevation, passes=None):
        """Обновляет вид небесной сферы с плавными траекториями"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, polar=True, facecolor='black')
        
        # Настройка полярного графика
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_xticks(np.radians(range(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], color='white')
        
        # Устанавливаем метки для оси Y
        yticks = range(0, 91, 30)
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{90-x}°' for x in yticks], color='white')
        
        # Сетка и оформление
        ax.grid(True, linestyle='--', alpha=0.3, color='white')
        
        # Рисуем зенит и горизонт
        ax.add_patch(Circle((0, 0), 90, transform=ax.transData._b, 
                    facecolor='#000033', alpha=0.5, edgecolor='none'))
        
        # Отображаем пролеты с плавными кривыми
        if passes:
            for pass_data in passes:
                if len(pass_data['azimuths']) > 3:  # Минимум 4 точки для интерполяции
                    az = np.array(pass_data['azimuths'])
                    el = np.array(pass_data['elevations'])
                    
                    # Нормализуем азимуты и сортируем точки
                    az = np.where(az < 0, az + 360, az)  # Убираем отрицательные значения
                    sort_idx = np.argsort(az)
                    az = np.radians(az[sort_idx])
                    el = np.clip(90 - el[sort_idx], 0, 90)  # Инвертируем и ограничиваем
                    
                    # Разбиваем на сегменты, если есть разрыв > 180°
                    diffs = np.diff(az)
                    split_indices = np.where(diffs > np.pi)[0] + 1
                    
                    if len(split_indices) > 0:
                        # Разделяем на непрерывные сегменты
                        segments = np.split(np.column_stack((az, el)), split_indices)
                    else:
                        segments = [np.column_stack((az, el))]
                    
                    # Рисуем каждый сегмент отдельно
                    for segment in segments:
                        if len(segment) > 3:
                            az_seg = segment[:, 0]
                            el_seg = segment[:, 1]
                            
                            try:
                                # Создаем плавную кривую для сегмента
                                spline = make_smoothing_spline(az_seg, el_seg)
                                az_new = np.linspace(az_seg.min(), az_seg.max(), 100)
                                el_new = spline(az_new)
                                
                                ax.plot(az_new, el_new, 'lime', linewidth=2, alpha=0.7)
                            except:
                                ax.plot(az_seg, el_seg, 'lime', linewidth=2, alpha=0.7)
        
        # Текущее положение спутника
        if azimuth is not None and elevation is not None:
            rad_az = math.radians(azimuth % 360)  # Нормализуем азимут
            clipped_elevation = max(0, min(90, 90 - elevation))
            ax.plot(rad_az, clipped_elevation, 'ro', markersize=8,
                markeredgecolor='white', markeredgewidth=1)
            
            # Информация о положении
            ax.text(1.3, 1.1, 
                f'Аз: {azimuth:.1f}°\nВз: {elevation:.1f}°', 
                transform=ax.transAxes, ha='right', va='top', 
                color='white', fontsize=9,
                bbox=dict(facecolor='black', alpha=1, edgecolor='none'))
        
        ax.set_title('Положение спутника на небесной сфере', 
                    color='white', pad=15, fontsize=10)
        self.canvas.draw()