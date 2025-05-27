import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QComboBox, QLineEdit, QLabel, QGroupBox,
                               QFormLayout, QTextEdit, QPushButton,
                               QListWidget, QMessageBox, QColorDialog)
from PySide6.QtCore import QTimer, Qt
from PySide6 import QtGui
from PySide6.QtGui import QColor, QPalette
from datetime import datetime, timedelta
import random
from satellite_position import Satellite
from map_view import Map2DWidget
from d3_view import Earth3DViewer
from sky_view import SkyViewWidget
from tle_parcer import (fetch_tle, search_satellites,
                       get_satellite_categories, get_all_satellites)

def load_styles():
    with open('styles/styles.css', 'r') as f:
        return f.read()

class SatelliteTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.set_dark_theme()
        #self.setStyleSheet(load_styles())
        self.setWindowTitle("Трекер спутников")
        self.setGeometry(100, 100, 1400, 920)

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

        # Список выбранных спутников
        self.selected_sats_list = QListWidget()
        self.selected_sats_list.setMaximumHeight(150)
        self.selected_sats_list.itemDoubleClicked.connect(self.remove_satellite)
        self.selected_sats_list.itemClicked.connect(self.on_satellite_selected)
        sat_layout.addRow("Выбранные\nспутники:", self.selected_sats_list)

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
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #202020;
                color: #CCCCCC;
                border: 1px solid #333333;
                border-radius: 4px;
                font-family: Arial;
                font-size: 10pt;
                padding: 5px;
            }
            QScrollBar:vertical {
                background: #303030;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                min-height: 20px;
            }
        """)
        self.info_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
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
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.earth_3d = Earth3DViewer()
        self.sky_view = SkyViewWidget()

        bottom_layout.addWidget(self.earth_3d, stretch=1)
        bottom_layout.addWidget(self.sky_view, stretch=1)

        right_layout.addWidget(bottom_panel, stretch=1)

        # Добавляем панели в главный layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=4)

        # Таймер для автообновления
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_views)
        self.update_timer.start(1000)  # Обновление каждую секунду

        # Хранилище данных о спутниках
        self.satellites = {}  # {name: {'tle1': ..., 'tle2': ..., 'color': ...}}
        self.current_satellite = None  # Имя текущего выбранного спутника для детальной информации

    def generate_color(self):
        """Генерирует случайный цвет для нового спутника"""
        return QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

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

    def on_satellite_selected(self, item):
        """Обработчик выбора спутника из списка для отображения детальной информации"""
        satellite_name = item.text()
        self.current_satellite = satellite_name
        self.update_views()

    def select_satellite(self, item):
        """Обработка выбора спутника из списка"""
        satellite_name = item.text()
        if "... и еще" in satellite_name:
            return

        try:
            if satellite_name in self.satellites:
                QMessageBox.information(self, "Информация", "Этот спутник уже добавлен")
                return

            tle1, tle2 = fetch_tle(satellite_name)
            color = self.generate_color()
            
            # Добавляем спутник в хранилище
            self.satellites[satellite_name] = {
                'tle1': tle1,
                'tle2': tle2,
                'color': color
            }
            
            # Добавляем в список выбранных спутников
            self.selected_sats_list.addItem(satellite_name)
            
            # Устанавливаем как текущий для отображения информации
            self.current_satellite = satellite_name
            
            self.update_views()
            QMessageBox.information(self, "Успех", f"Спутник {satellite_name} добавлен")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def remove_satellite(self, item):
        """Удаление спутника из списка отслеживаемых"""
        satellite_name = item.text()
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Удалить спутник {satellite_name} из списка?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Удаляем из хранилища
            if satellite_name in self.satellites:
                del self.satellites[satellite_name]
            
            # Удаляем из списка
            self.selected_sats_list.takeItem(self.selected_sats_list.row(item))
            
            # Если удалили текущий спутник, сбрасываем текущий
            if self.current_satellite == satellite_name:
                self.current_satellite = None
                self.info_text.clear()
            
            self.update_views()

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
        if not self.satellites:
            # Очищаем все представления, если нет спутников
            self.map_2d.clear_plot()
            self.earth_3d.clear_view()
            self.sky_view.clear_plot()
            return

        try:
            # Получаем координаты станции
            try:
                station_lon = float(self.lon_input.text())
                station_lat = float(self.lat_input.text())
                station_alt = float(self.alt_input.text())
            except ValueError:
                station_lon, station_lat, station_alt = None, None, None

            now = datetime.utcnow()
            all_passes = []
            
            # Собираем данные для всех спутников
            map_data = []
            earth_3d_data = []
            sky_view_data = []
            
            for sat_name, sat_data in self.satellites.items():
                try:
                    sat = Satellite(sat_name, sat_data['tle1'], sat_data['tle2'])
                    color = sat_data['color']
                    
                    # Рассчитываем траекторию
                    lons, lats, alts = [], [], []
                    try:
                        depth = int(self.prog_input.text())
                    except:
                        depth = 0
                        
                    for i in range(depth+1):
                        time = now + timedelta(minutes=i)
                        try:
                            pos = sat.calculate_satellite_position(time)
                            lons.append(pos['longitude'])
                            lats.append(pos['latitude'])
                            alts.append(pos['altitude'])
                        except Exception as e:
                            print(f"Ошибка расчета позиции для времени {time}: {e}")
                            continue

                    if not lons:  # Если не удалось рассчитать ни одной позиции
                        continue

                    # Добавляем данные для 2D карты
                    map_data.append({
                        'lons': lons,
                        'lats': lats,
                        'name': sat_name,
                        'color': color
                    })

                    # Добавляем данные для 3D вида
                    earth_3d_data.append({
                        'lons': lons,
                        'lats': lats,
                        'alts': alts,
                        'name': sat_name,
                        'color': color
                    })

                    # Рассчитываем положение спутника относительно станции
                    if station_lon is not None and station_lat is not None:
                        try:
                            look = sat.get_observer_look({
                                'lat': station_lat,
                                'lon': station_lon,
                                'alt': station_alt
                            }, now)
                            
                            # Добавляем данные для SkyView
                            sky_view_data.append({
                                'azimuth': look['azimuth'],
                                'elevation': look['elevation'],
                                'name': sat_name,
                                'color': color
                            })
                            
                            # Если это текущий спутник, обновляем информацию
                            if sat_name == self.current_satellite:
                                self.update_satellite_info(sat, now, look['azimuth'], look['elevation'])
                            
                            # Рассчитываем пролеты для SkyView
                            passes = self.calculate_passes(
                                sat, station_lat, station_lon, station_alt, now)
                            if len (passes) >0:
                                all_passes.extend([(passes[0], color, sat_name)])
                            
                        except Exception as e:
                            print(f"Ошибка расчета положения относительно станции: {e}")
                            if sat_name == self.current_satellite:
                                self.update_satellite_info(sat, now, None, None)
                    
                    elif sat_name == self.current_satellite:
                        self.update_satellite_info(sat, now, None, None)

                except Exception as e:
                    print(f"Ошибка обработки спутника {sat_name}: {e}")
                    continue

            # Обновляем все представления
            try:
                self.map_2d.update_plot(map_data, station_lon, station_lat)
            except Exception as e:
                print(f"Ошибка обновления 2D карты: {e}")
                QMessageBox.warning(self, "Предупреждение", 
                    f"Ошибка обновления 2D карты: {str(e)}")

            try:
                self.earth_3d.update_view(earth_3d_data, station_lon, station_lat)
            except Exception as e:
                print(f"Ошибка обновления 3D вида: {e}")
                QMessageBox.warning(self, "Предупреждение", 
                    f"Ошибка обновления 3D вида: {str(e)}")

            try:
                self.sky_view.update_plot(sky_view_data, all_passes)
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
        """Обновляет информацию о выбранном спутнике в стиле панели справа"""
        # Сохраняем текущую позицию скролла
        scroll_bar = self.info_text.verticalScrollBar()
        scroll_position = scroll_bar.value()
        
        # Очищаем предыдущее содержимое
        self.info_text.clear()
        
        # Создаем документ с форматированием
        cursor = self.info_text.textCursor()
        fmt_normal = QtGui.QTextCharFormat()
        fmt_normal.setForeground(QtGui.QBrush(QtGui.QColor(200, 200, 200)))
        
        fmt_title = QtGui.QTextCharFormat()
        fmt_title.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
        fmt_title.setFontWeight(QtGui.QFont.Bold)
        fmt_title.setFontPointSize(11)
        
        fmt_section = QtGui.QTextCharFormat()
        fmt_section.setForeground(QtGui.QBrush(QtGui.QColor(170, 170, 170)))
        fmt_section.setFontWeight(QtGui.QFont.Bold)
        fmt_section.setFontPointSize(10)
        
        fmt_value = QtGui.QTextCharFormat()
        fmt_value.setForeground(QtGui.QBrush(QtGui.QColor(200, 200, 200)))
        fmt_value.setFontPointSize(10)
        
        # Заголовок с цветным индикатором
        color = self.satellites[sat.name]['color']
        cursor.insertText("   ", fmt_normal)  # Отступ для цветного индикатора
        
        # Вставляем цветной квадратик (символ с фоном)
        fmt_color = QtGui.QTextCharFormat()
        fmt_color.setBackground(QtGui.QBrush(color))
        cursor.insertText(" ", fmt_color)
        cursor.insertText(" ", fmt_normal)  # Пробел после индикатора
        
        cursor.insertText(f"{sat.name}\n", fmt_title)
        cursor.insertText("\n", fmt_normal)

        cursor.insertText(f"Проекция на землю\n", fmt_section)
        try:
            pos = sat.calculate_satellite_position(time)
            cursor.insertText(f"  Широта: {pos['latitude']:.5f}°\n", fmt_value)
            cursor.insertText(f"  Долгота: {pos['longitude']:.5f}°\n", fmt_value)
            cursor.insertText(f"  Высота: {pos['altitude']:.2f} (км)\n\n", fmt_value)
        except Exception as e:
            cursor.insertText("  Не удалось получить положение спутника\n\n", fmt_value)

        # Информация о видимости
        if azimuth is not None and elevation is not None:
            cursor.insertText("Относительно станции:\n", fmt_section)
            cursor.insertText(f"  Азимут: {azimuth:.1f}°\n", fmt_value)
            cursor.insertText(f"  Угол места: {elevation:.1f}°\n", fmt_value)
            
            # Статус с цветом
            fmt_status = QtGui.QTextCharFormat()
            if elevation > 0:
                fmt_status.setForeground(QtGui.QBrush(QtGui.QColor(76, 175, 80)))  # Зеленый
                status = "Над горизонтом"
            else:
                fmt_status.setForeground(QtGui.QBrush(QtGui.QColor(244, 67, 54)))  # Красный
                status = "За горизонтом"
            
            cursor.insertText("  Статус: ", fmt_value)
            cursor.insertText(f"{status}\n", fmt_status)
            
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
                    cursor.insertText("\n", fmt_normal)
                    cursor.insertText("Следующий контакт:\n", fmt_section)
                    cursor.insertText(f"  Начало: {next_contact[0].strftime('%Y-%m-%d %H:%M:%S')}\n", fmt_value)
                    cursor.insertText(f"  Макс. угол: {next_contact[2].strftime('%H:%M:%S')}\n", fmt_value)
                    cursor.insertText(f"  Конец: {next_contact[1].strftime('%H:%M:%S')}\n", fmt_value)
                    cursor.insertText(f"  Длительность: {(next_contact[1]-next_contact[0]).total_seconds()/60:.1f} мин\n", fmt_value)
                else:
                    cursor.insertText("\n", fmt_normal)
                    cursor.insertText(f"Нет контактов в ближайшие {5} часов\n", fmt_value)
            except Exception as e:
                cursor.insertText("\n", fmt_normal)
                cursor.insertText("Не удалось рассчитать время контакта\n", fmt_value)

        # Основные параметры
        cursor.insertText("\n", fmt_normal)
        cursor.insertText("Основные параметры:\n", fmt_section)
        cursor.insertText(f"  Время: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n", fmt_value)
        
        try:
            TLE2 = self.satellites[sat.name]['tle2']
            cursor.insertText(f"  Наклонение: {float(TLE2[8:16]):.2f}°\n", fmt_value)
            cursor.insertText(f"  RAAN: {float(TLE2[17:25]):.2f}°\n", fmt_value)
            cursor.insertText(f"  Аргумент перицентра: {float(TLE2[34:42]):.2f}°\n", fmt_value)
            cursor.insertText(f"  Эксцентриситет: {float(f'0.{TLE2[26:33]}'):.6f}\n", fmt_value)
            cursor.insertText(f"  Средняя аномалия: {float(TLE2[43:51]):.2f}°\n", fmt_value)
            cursor.insertText(f"  Период: {(1440 / float(TLE2[52:63])):.2f} мин\n", fmt_value)
        except Exception as e:
            cursor.insertText(f"  Не удалось получить параметры орбиты: {str(e)}\n", fmt_value)
        
        cursor.insertText("\n", fmt_normal)
        
        # Положение в MJ2000
        cursor.insertText("Положение в MJ2000 (км):\n", fmt_section)
        try:
            pos = sat.calculate_satellite_position(time)
            cursor.insertText(f"  X: {pos['earth_mj2000'][0]:.2f}\n", fmt_value)
            cursor.insertText(f"  Y: {pos['earth_mj2000'][1]:.2f}\n", fmt_value)
            cursor.insertText(f"  Z: {pos['earth_mj2000'][2]:.2f}\n", fmt_value)
        except Exception as e:
            cursor.insertText("  Не удалось получить положение в MJ2000\n", fmt_value)
        
        cursor.insertText("\n", fmt_normal)
        
        
        # Восстанавливаем позицию скролла
        scroll_bar.setValue(scroll_position)

    def set_dark_theme(self):
        """Устанавливает тёмную тему для всего приложения"""
        dark_palette = QPalette()
        
        # Базовые цвета
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        # Отключаем анимации и эффекты
        self.setStyleSheet("""
            QToolTip { 
                color: #ffffff; 
                background-color: #2a82da; 
                border: 1px solid white; 
            }
        """)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTextEdit, QListWidget, QLineEdit, QComboBox {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #3a3a3a;
            }
            QPushButton {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QPushButton:pressed {
                background-color: #252525;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #454545;
                min-height: 20px;
            }
        """)
        
        self.setPalette(dark_palette)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SatelliteTracker()
    window.show()
    sys.exit(app.exec())