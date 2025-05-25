"""Основной модуль для запуска GUI приложения трекинга спутников."""
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt
from visualization import plot_2d_trajectory, plot_3d_orbit, get_dummy_trajectory
from datetime import datetime, timedelta
import configparser
import sys

from satellite_position import Satellite
'''MERIDIAN-4
1 37398U 11018A   25078.69307982 -.00000464  00000-0  00000+0 0  9991
2 37398  62.1504 146.3299 7311923 260.0888  18.0830  2.00652128101651'''


tle1 = '1 40296U 14069A   25143.36398969  .00000184  00000-0  00000-0 0  9992'
tle2 = '2 40296  63.4869 255.6893 6837698 272.5525  17.3585  2.00611251 77418'

class SatelliteTrackerApp(QMainWindow):
    """Главное окно приложения трекинга спутников."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Спутниковый трекер")
        self.setGeometry(100, 100, 400, 400)

        # Чтение конфигурации
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        if not self.config.sections():
            self.config["Style"] = {"background": "white", "font_size": "12"}
            with open("config.ini", "w") as f:
                self.config.write(f)

        # Центральный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Выбор спутника
        self.satellite_label = QLabel("Выберите спутник:")
        self.satellite_combo = QComboBox()
        self.satellite_combo.addItems(["ISS (ZARYA)", "NOAA 15", "METEOR-M 2"])
        self.layout.addWidget(self.satellite_label)
        self.layout.addWidget(self.satellite_combo)

        # Ввод координат станции
        self.station_label = QLabel("Координаты станции (широта, долгота):")
        self.lat_input = QLineEdit("55.7558")  # Пример: Москва
        self.lon_input = QLineEdit("37.6173")
        self.layout.addWidget(self.station_label)
        self.layout.addWidget(self.lat_input)
        self.layout.addWidget(self.lon_input)

        # Информация о местоположении спутника
        self.position_label = QLabel("Текущие координаты спутника: Неизвестно")
        self.layout.addWidget(self.position_label)

        # Кнопки для визуализации
        self.plot_2d_button = QPushButton("Показать 2D-траекторию")
        self.plot_2d_button.clicked.connect(self.show_2d_plot)
        self.layout.addWidget(self.plot_2d_button)

        self.plot_3d_button = QPushButton("Показать 3D-орбит")
        self.plot_3d_button.clicked.connect(self.show_3d_plot)
        self.layout.addWidget(self.plot_3d_button)

        self.plot_2d_button.setStyleSheet("background-color: lightblue; color: black;")
        self.plot_3d_button.setStyleSheet("background-color: lightgreen; color: black;")

        self.satellite_label.setStyleSheet("background-color: lightgreen; color: black;")
        self.satellite_label.setStyleSheet("background-color: lightgreen; color: black;")

        # Применение стилей из config.ini
        font_size = self.config["Style"]["font_size"]
        background = self.config["Style"]["background"]
        self.central_widget.setStyleSheet(
            f"background-color: {background}; font-size: {font_size}px; color: black;"
        )

        # Поддержка управления мышью
        self.setWindowFlags(
           Qt.WindowType.Window)
        self.setMinimumSize(300, 300)

    def show_2d_plot(self):
        """Отображает 2D-траекторию спутника."""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())

            satellite = Satellite(
                    sat_name=self.satellite_combo.currentText(),
                    tle1=tle1,
                    tle2=tle2
            )

            timestamp = datetime.utcnow()
            delt=timedelta(minutes=1)
            lons = []
            lats = []
            for i in range(6*24):
                cords = satellite.calculate_satellite_position(timestamp)
                lons.append(cords['longitude'])
                lats.append(cords['latitude'])
                timestamp+=delt

            plot_2d_trajectory(lons, lats, satellite.name, lon, lat)
            # Обновление информации о местоположении
            self.position_label.setText(
                f"Текущие координаты: ({lons[-1]:.2f}, {lats[-1]:.2f})")
        except ValueError as e:
            self.position_label.setText(f"Ошибка: Неверные координаты ({e})")

    def show_3d_plot(self):
        """Отображает 3D-орбит спутника."""
        satellite = Satellite(
                    sat_name=self.satellite_combo.currentText(),
                    tle1=tle1,
                    tle2=tle2
        )
        # Тестовые данные (заменить на реальные из satellite_position.py
        timestamp = datetime.utcnow()
        delt=timedelta(minutes=1)
        pos = []
        for i in range(6*24):
            cords = satellite.calculate_satellite_position(timestamp)
            pos.append(cords['earth_mj2000'])
            timestamp+=delt

        plot_3d_orbit(pos, satellite.name)

def main():
    """Запускает приложение."""
    app = QApplication(sys.argv)
    window = SatelliteTrackerApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
