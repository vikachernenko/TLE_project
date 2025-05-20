"""Основной модуль для запуска GUI приложения трекинга спутников."""
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QComboBox, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
from src.visualization import plot_2d_trajectory, plot_3d_orbit, get_dummy_trajectory
import configparser
import sys


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

        # Применение стилей из config.ini
        font_size = self.config["Style"]["font_size"]
        background = self.config["Style"]["background"]
        self.central_widget.setStyleSheet(
            f"background-color: {background}; font-size: {font_size}px;"
        )

        # Поддержка управления мышью
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setMinimumSize(300, 300)

    def show_2d_plot(self):
        """Отображает 2D-траекторию спутника."""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            satellite = self.satellite_combo.currentText()
            # Тестовые данные (заменить на реальные из satellite_position.py)
            lons, lats, _ = get_dummy_trajectory()
            plot_2d_trajectory(lons, lats, satellite, lon, lat)
            # Обновление информации о местоположении
            self.position_label.setText(
                f"Текущие координаты: ({lons[-1]:.2f}, {lats[-1]:.2f})")
        except ValueError as e:
            self.position_label.setText(f"Ошибка: Неверные координаты ({e})")

    def show_3d_plot(self):
        """Отображает 3D-орбит спутника."""
        satellite = self.satellite_combo.currentText()
        # Тестовые данные (заменить на реальные из satellite_position.py)
        _, _, positions = get_dummy_trajectory()
        plot_3d_orbit(positions, satellite)


def main():
    """Запускает приложение."""
    app = QApplication(sys.argv)
    window = SatelliteTrackerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
