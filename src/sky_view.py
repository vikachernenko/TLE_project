import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6 import QtWidgets
from matplotlib.patches import Circle
import math

class SkyViewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure(figsize=(8, 8), facecolor='#f0f0f0')
        self.canvas = FigureCanvas(self.figure)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.canvas)
        
    def update_plot(self, azimuth, elevation, passes=None):
        """Обновляет вид небесной сферы"""
        self.figure.clear()
        ax = self.figure.add_subplot(111, polar=True, facecolor='#f0f0f0')
        
        # Настройка полярного графика
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 90)
        ax.set_xticks(np.radians(range(0, 360, 45)))
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        
        # Устанавливаем метки для оси Y (угол места)
        yticks = range(0, 91, 30)
        ax.set_yticks(yticks)
        ax.set_yticklabels([f'{90-x}°' for x in yticks])  # 90° в центре, 0° на краю
        
        # Сетка и оформление
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Рисуем зенит (центр) и горизонт (край)
        ax.add_patch(Circle((0, 0), 90, transform=ax.transData._b, 
                    facecolor='lightblue', alpha=0.2, edgecolor='gray'))
        
        # Отображаем пролеты
        if passes:
            for pass_data in passes:
                if len(pass_data['azimuths']) > 1:
                    az = np.radians(pass_data['azimuths'])
                    el = [max(0, min(90, 90-e)) for e in pass_data['elevations']]  # Инвертируем и ограничиваем
                    
                    # Плавная интерполяция
                    from scipy.interpolate import make_interp_spline
                    try:
                        t = np.linspace(0, 1, len(az))
                        t_new = np.linspace(0, 1, 100)
                        az_smooth = make_interp_spline(t, az)(t_new)
                        el_smooth = make_interp_spline(t, el)(t_new)
                        ax.plot(az_smooth, el_smooth, 'g-', linewidth=2, alpha=0.7)
                    except:
                        ax.plot(az, el, 'g-', linewidth=2, alpha=0.7)
        
        # Текущее положение спутника
        if azimuth is not None and elevation is not None:
            rad_az = math.radians(azimuth)
            clipped_elevation = max(0, min(90, elevation))
            ax.plot(rad_az, 90 - clipped_elevation, 'ro', markersize=8, 
                   markeredgecolor='black', markeredgewidth=0.5)
            
            # Подпись с данными
            ax.text(rad_az, 90 - clipped_elevation + 5, 
                   f'Азимут: {azimuth:.1f}°\nУгол места: {elevation:.1f}°', 
                   ha='center', va='bottom', fontsize=8,
                   bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
        
        ax.set_title('Положение спутника на небесной сфере', pad=15, fontsize=10)
        self.canvas.draw()
