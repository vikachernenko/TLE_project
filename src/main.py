import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QComboBox, QLineEdit, QLabel, QGroupBox,
                               QFormLayout, QTextEdit, QPushButton,
                               QListWidget, QMessageBox)
from PySide6.QtCore import QTimer
from datetime import datetime, timedelta
from satellite_position import Satellite
from map_view import Map2DWidget
from d3_view import Earth3DViewer
from sky_view import SkyViewWidget
from tle_parcer import (fetch_tle, search_satellites,
                       get_satellite_categories, get_all_satellites)


class SatelliteTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Трекер спутников")
        self.setGeometry(100, 100, 1400, 900)

        # Центральный виджет
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Левая панель - управление и информация
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Группа выбора спутника
        sat_group = QGroupBox("Параметры спутника")
        sat_layout = QFormLayout(sat_group)

        # Добавляем выпадающий список категорий
        self.category_combo = QComboBox()
        self.category_combo.addItem("Все спутники")
        self.category_combo.addItems(get_satellite_categories())
        sat_layout.addRow("Категория:", self.category_combo)

        # Поле поиска и список результатов
        search_widget = QWidget()
        search_layout = QVBoxLayout(search_widget)
        
        search_input_layout = QHBoxLayout()
        self.sat_search = QLineEdit()
        self.sat_search.setPlaceholderText("Введите название спутника")
        self.search_button = QPushButton("Поиск")
        search_input_layout.addWidget(self.sat_search)
        search_input_layout.addWidget(self.search_button)
        
        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(150)
        
        search_layout.addLayout(search_input_layout)
        search_layout.addWidget(self.search_results)
        
        sat_layout.addRow("Поиск:", search_widget)

        # Подключаем сигналы
        self.search_button.clicked.connect(self.search_satellite)
        self.sat_search.returnPressed.connect(self.search_satellite)
        self.search_results.itemDoubleClicked.connect(self.select_satellite)
        self.category_combo.currentTextChanged.connect(self.on_category_changed)

        prog_group = QGroupBox("Глубина прогноза")
        prog_layout = QFormLayout(prog_group)
        self.prog_input = QLineEdit("120")
        prog_layout.addRow("Интервал (мин):", self.prog_input)

        # Группа станции
        station_group = QGroupBox("Наземная станция")
        station_layout = QFormLayout(station_group)

        self.lat_input = QLineEdit("55.7558")
        self.lon_input = QLineEdit("37.6173")
        self.alt_input = QLineEdit("0.1")
        station_layout.addRow("Широта (°):", self.lat_input)
        station_layout.addRow("Долгота (°):", self.lon_input)
        station_layout.addRow("Высота (км):", self.alt_input)

        # Информация о спутнике
        info_group = QGroupBox("Информация о положении")
        info_layout = QVBoxLayout(info_group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)

        # Добавляем группы на левую панель
        left_layout.addWidget(sat_group)
        left_layout.addWidget(prog_group)
        left_layout.addWidget(station_group)
        left_layout.addWidget(info_group, stretch=2)
        left_layout.addStretch()

        # Правая панель - визуализация
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Верхняя часть - 2D карта
        self.map_2d = Map2DWidget()
        right_layout.addWidget(self.map_2d, stretch=2)

        # Нижняя часть - 3D и SkyView
        bottom_panel = QWidget()
        bottom_layout = QHBoxLayout(bottom_panel)

        self.earth_3d = Earth3DViewer()
        self.sky_view = SkyViewWidget()

        bottom_layout.addWidget(self.earth_3d, stretch=2)
        bottom_layout.addWidget(self.sky_view, stretch=1)

        right_layout.addWidget(bottom_panel, stretch=1)

        # Добавляем панели в главный layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=4)

        # Таймер для автообновления
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_views)
        self.update_timer.start(1000)  # Обновление каждую секунду

        # Инициализация TLE
        self.current_tle1 = ""
        self.current_tle2 = ""
        self.current_satellite_name = ""

    def search_satellite(self):
        """Поиск спутника по имени и отображение результатов"""
        search_term = self.sat_search.text().strip()
        if not search_term:
            QMessageBox.warning(self, "Предупреждение", "Введите название спутника")
            return

        self.search_results.clear()
        try:
            results = search_satellites(search_term)
            if results:
                self.search_results.addItems(results[:20])  # Показываем первые 20 результатов
                if len(results) > 20:
                    self.search_results.addItem(f"... и еще {len(results) - 20} результатов")
            else:
                self.search_results.addItem("Спутники не найдены")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка поиска: {str(e)}")

    def select_satellite(self, item):
        """Обработка выбора спутника из списка"""
        satellite_name = item.text()
        if "... и еще" in satellite_name:
            return

        try:
            self.current_tle1, self.current_tle2 = fetch_tle(satellite_name)
            self.current_satellite_name = satellite_name
            self.update_views()
            QMessageBox.information(self, "Успех", f"Спутник {satellite_name} выбран")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def on_category_changed(self, category):
        """Обработка изменения категории спутников"""
        if category == "Все спутники":
            return
        
        try:
            # Здесь можно добавить фильтрацию по категории
            # Пока просто показываем сообщение
            QMessageBox.information(self, "Категория", f"Выбрана категория: {category}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при смене категории: {str(e)}")

    def update_views(self):
        if not self.current_tle1 or not self.current_tle2:
            return

        try:
            sat = Satellite(self.current_satellite_name,
                            self.current_tle1, self.current_tle2)

            # Рассчитываем траекторию
            now = datetime.utcnow()
            lons, lats, alts = [], [], []
            try:
                depth = int(self.prog_input.text())
            except:
                depth = 0
            for i in range(depth+1):
                time = now + timedelta(minutes=i)  # Исправлено: добавлен множитель *10
                try:
                    pos = sat.calculate_satellite_position(time)
                    lons.append(pos['longitude'])
                    lats.append(pos['latitude'])
                    alts.append(pos['altitude'])
                except Exception as e:
                    print(f"Ошибка расчета позиции для времени {time}: {e}")
                    continue

            if not lons:  # Если не удалось рассчитать ни одной позиции
                QMessageBox.warning(self, "Предупреждение", 
                    "Не удалось рассчитать траекторию спутника")
                return

            # Получаем координаты станции
            try:
                station_lon = float(self.lon_input.text())
                station_lat = float(self.lat_input.text())
                station_alt = float(self.alt_input.text())
            except ValueError:
                station_lon, station_lat, station_alt = None, None, None

            # Рассчитываем положение спутника относительно станции
            azimuth = None
            elevation = None
            passes = []

            if station_lon is not None and station_lat is not None:
                try:
                    look = sat.get_observer_look({
                        'lat': station_lat,
                        'lon': station_lon,
                        'alt': station_alt
                    }, now)
                    azimuth = look['azimuth']
                    elevation = look['elevation']
                    self.update_satellite_info(sat, now, azimuth, elevation)
                except Exception as e:
                    print(f"Ошибка расчета положения относительно станции: {e}")
                    QMessageBox.warning(self, "Предупреждение", 
                        f"Ошибка расчета положения относительно станции: {str(e)}")
                    azimuth, elevation = None, None

                try:
                    passes = self.calculate_passes(
                        sat, station_lat, station_lon, station_alt, now)
                except Exception as e:
                    print(f"Ошибка расчета пролетов: {e}")
                    passes = []

            # Обновляем все представления
            try:
                self.map_2d.update_plot(
                    lons, lats, sat.name, station_lon, station_lat)
            except Exception as e:
                print(f"Ошибка обновления 2D карты: {e}")
                QMessageBox.warning(self, "Предупреждение", 
                    f"Ошибка обновления 2D карты: {str(e)}")

            try:
                self.earth_3d.update_view(
                    lons, lats, alts, sat.name, station_lon, station_lat)
            except Exception as e:
                print(f"Ошибка обновления 3D вида: {e}")
                QMessageBox.warning(self, "Предупреждение", 
                    f"Ошибка обновления 3D вида: {str(e)}")

            try:
                self.sky_view.update_plot(azimuth, elevation, passes)
            except Exception as e:
                print(f"Ошибка обновления вида неба: {e}")
                QMessageBox.warning(self, "Предупреждение", 
                    f"Ошибка обновления вида неба: {str(e)}")

        except Exception as e:
            error_msg = f"Ошибка при обновлении представлений: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Ошибка", error_msg)

    def calculate_passes(self, sat, station_lat, station_lon, station_alt, now):
        """Рассчитывает пролеты спутника над станцией"""
        passes = []
        try:
            contacts = sat.get_contacts_times({
                'lat': station_lat,
                'lon': station_lon,
                'alt': station_alt
            }, now, 5)  # Рассматриваем 5 ч

            for contact in contacts:
                pass_data = {'azimuths': [], 'elevations': []}
                duration = (contact[1] - contact[0]).total_seconds()
                time_step = timedelta(seconds=duration/100)
                current_time = contact[0]

                while current_time <= contact[1]:
                    try:
                        pos = sat.get_observer_look({
                            'lat': station_lat,
                            'lon': station_lon,
                            'alt': station_alt
                        }, current_time)
                        # Добавляем только если спутник над горизонтом
                        if pos['elevation'] > 0:
                            pass_data['azimuths'].append(pos['azimuth'])
                            pass_data['elevations'].append(pos['elevation'])
                    except:
                        pass
                    current_time += time_step

                # Добавляем точки до и после пролета для плавного отображения
                if pass_data['azimuths']:
                    # Точка входа (понижаемся до 0°)
                    pass_data['azimuths'].insert(0, pass_data['azimuths'][0])
                    pass_data['elevations'].insert(0, 0)

                    # Точка выхода (понижаемся до 0°)
                    pass_data['azimuths'].append(pass_data['azimuths'][-1])
                    pass_data['elevations'].append(0)

                    passes.append(pass_data)
        except Exception as e:
            print(f"Ошибка расчета пролетов: {e}")

        return passes

    def update_satellite_info(self, sat, time, azimuth, elevation):
        """Обновляет информацию о спутнике"""
        info = f"=== Спутник: {sat.name} ===\n"
        info += f"Время: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

        try:
            TLE2 = self.current_tle2
            info += "Параметры орбиты:\n"
            info += (f"Наклонение: {float(TLE2[8:16]):.2f}°\n")
            info += (f"RAAN: {float(TLE2[17:25]):.2f}°\n")
            info += (f"Аргумент перицентра: {float(TLE2[34:42]):.2f}°\n")
            info += (f"Эксцентриситет: {float(f'0.{TLE2[26:33]}'):.6f}\n")
            info += (f"Средняя аномалия: {float(TLE2[43:51]):.2f}°\n")
            info += (f"Период: {(1440 / float(TLE2[52:63])):.2f} мин\n\n")
        except Exception as e:
            info += str(e) + '\n'
            info += "Не удалось получить параметры орбиты\n\n"

        # Текущее положение в MJ2000
        try:
            pos = sat.calculate_satellite_position(time)
            info += "Положение в MJ2000 (км):\n"
            info += f"X: {pos['earth_mj2000'][0]:.2f}\n"
            info += f"Y: {pos['earth_mj2000'][1]:.2f}\n"
            info += f"Z: {pos['earth_mj2000'][2]:.2f}\n\n"
        except Exception as e:
            info += "Не удалось получить положение в MJ2000\n\n"

        # Информация о видимости
        if azimuth is not None and elevation is not None:
            info += "Относительно станции:\n"
            info += f"Азимут: {azimuth:.1f}°\n"
            info += f"Угол места: {elevation:.1f}°\n"

            if elevation > 0:
                info += "Статус: Над горизонтом\n"
            else:
                info += "Статус: За горизонтом\n"

            # Рассчитываем следующее время контакта
            try:
                station_lat = float(self.lat_input.text())
                station_lon = float(self.lon_input.text())
                station_alt = float(self.alt_input.text())

                contacts = sat.get_contacts_times({
                    'lat': station_lat,
                    'lon': station_lon,
                    'alt': station_alt
                }, time, 5)

                if contacts and len(contacts) > 0:
                    next_contact = contacts[0]
                    info += f"\nСледующий контакт:\n"
                    info += f"Начало: {next_contact[0].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    info += f"Макс. угол в {next_contact[2].strftime('%H:%M:%S')}\n"
                    info += f"Конец: {next_contact[1].strftime('%H:%M:%S')}\n"
                    info += f"Длительность: {(next_contact[1]-next_contact[0]).total_seconds()/60:.1f} мин\n"
                else:
                    info += "\nНет предстоящих контактов в ближайшие 5 часов\n"
            except Exception as e:
                info += "\nНе удалось рассчитать время контакта\n"

        self.info_text.setPlainText(info)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SatelliteTracker()
    window.show()
    sys.exit(app.exec())
