import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                              QVBoxLayout, QHBoxLayout, QComboBox, 
                              QLineEdit, QLabel)
from PySide6.QtCore import QTimer
from datetime import datetime, timedelta
from satellite_position import Satellite
from vis_2d import Map2DWidget
from vis_3d import Earth3DViewer

# Пример TLE (замените на актуальные)
TLE1 = '1 06235U 72082A   25078.96535962 -.00000020  00000-0  16590-3 0  9999'
TLE2 = '2 06235 102.0253  87.2007 0003765 319.2629  55.2466 12.53197307398059'

class SatelliteTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер спутников")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Элементы управления
        control_layout.addWidget(QLabel("Спутник:"))
        self.sat_select = QComboBox()
        self.sat_select.addItems(["ISS", "Hubble", "GPS IIR-11"])
        control_layout.addWidget(self.sat_select)
        
        control_layout.addWidget(QLabel("Широта:"))
        self.lat_input = QLineEdit("55.7558")
        control_layout.addWidget(self.lat_input)
        
        control_layout.addWidget(QLabel("Долгота:"))
        self.lon_input = QLineEdit("37.6173")
        control_layout.addWidget(self.lon_input)
        
        main_layout.addWidget(control_panel)
        
        # Графическая область
        self.plot_area = QWidget()
        plot_layout = QHBoxLayout(self.plot_area)
        
        # 2D карта
        self.map_2d = Map2DWidget()
        plot_layout.addWidget(self.map_2d, stretch=1)
        
        # 3D вид
        self.earth_3d = Earth3DViewer()
        plot_layout.addWidget(self.earth_3d, stretch=1)
        
        main_layout.addWidget(self.plot_area, stretch=1)
        
        # Таймер для автообновления
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_views)
        self.update_timer.start(1000)  # Обновление каждые 5 секунд
        
        # Первоначальное обновление
        self.update_views()
    
    def update_views(self):
        sat = Satellite(
            self.sat_select.currentText(),
            TLE1, TLE2
        )
        
        # Рассчитываем траекторию
        now = datetime.utcnow()
        lons, lats, alts = [], [], []
        
        for i in range(24*6):  # 24 часа с шагом 10 минут
            time = now + timedelta(minutes=i)
            pos = sat.calculate_satellite_position(time)
            lons.append(pos['longitude'])
            lats.append(pos['latitude'])
            alts.append(pos['altitude'])
        
        # Получаем координаты станции
        try:
            station_lon = float(self.lon_input.text())
            station_lat = float(self.lat_input.text())
        except ValueError:
            station_lon, station_lat = None, None
        
        # Обновляем 2D вид
        self.map_2d.update_plot(
            lons, lats, sat.name,
            station_lon,
            station_lat
        )
        
        # Обновляем 3D вид (передаем lon, lat, alt)
        self.earth_3d.update_view(lons, lats, alts, sat.name, 
                                station_lon, station_lat)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SatelliteTracker()
    window.show()
    sys.exit(app.exec())