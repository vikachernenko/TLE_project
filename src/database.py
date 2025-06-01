import sys
import os
import sqlite3
import pickle
import pandas as pd
from typing import List, Dict, Tuple, Any, Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                               QComboBox, QLabel, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt
from datetime import datetime
from pyorbital.orbital import Orbital
import math
import requests

# Пути к файлам
WORK_DIR = "work/data"
DB_PATH = "satellites.db"

# Пути к справочникам в бинарном формате
CATEGORIES_FILE = os.path.join(WORK_DIR, "categories.bin")
ORBIT_TYPES_FILE = os.path.join(WORK_DIR, "orbit_types.bin")


class Satellite:
    """Класс для работы с данными конкретного спутника"""

    def __init__(self, sat_name: str, tle1: str, tle2: str):
        """
        Инициализация спутника

        :param sat_name: Название спутника
        :param tle1: Первая строка TLE
        :param tle2: Вторая строка TLE
        """
        self.name = sat_name
        self.tle1 = tle1
        self.tle2 = tle2
        self.orb = Orbital(sat_name, line1=tle1, line2=tle2)

    def calculate_satellite_position(self, timestamp: datetime) -> Dict[str, Any]:
        """
        Рассчитывает позицию спутника в системе EarthMJ2000 и географические координаты.

        :param timestamp: Временная метка (datetime в UTC)
        :return: Словарь с координатами спутника
        """
        position = self.orb.get_position(timestamp, normalize=False)[0]
        lon, lat, alt = self.orb.get_lonlatalt(timestamp)
        x, y, z = self.lla_to_ecef(lat, lon, alt)

        return {
            'latitude': lat,
            'longitude': lon,
            'ecef': (x, y, z),
            'earth_mj2000': position,
            'altitude': alt
        }

    def get_observer_look(self, ground_station: Dict[str, float], timestamp: datetime) -> Dict[str, float]:
        """
        Рассчитывает позицию спутника в сферической системе координат относительно наблюдателя

        :param ground_station: Словарь с 'lat', 'lon', 'alt' станции
        :param timestamp: Временная метка (datetime в UTC)
        :return: Словарь с азимутом и возвышением
        """
        az, elev = self.orb.get_observer_look(
            timestamp, ground_station['lon'], ground_station['lat'], ground_station['alt'])
        return {
            'azimuth': az,
            'elevation': elev
        }

    def get_contacts_times(self, ground_station: Dict[str, float], timestamp: datetime,
                           duration: int, horizon: float = 0) -> List[Tuple[datetime, datetime, datetime]]:
        """
        Находит ближайшее время контакта спутника с наземной станцией.

        :param ground_station: Словарь с 'lat', 'lon', 'alt' станции
        :param timestamp: Начало периода поиска (datetime в UTC)
        :param duration: В течении скольки часов искать контакт
        :param horizon: Минимальный угол возвыщения (по умочанию 0.0)
        :return: Массив кортежей (время начала контакта, время конца контакта, время максимального возвышения)
        """
        return self.orb.get_next_passes(timestamp, duration, ground_station['lon'],
                                        ground_station['lat'], ground_station['alt'], horizon)

    def lla_to_ecef(self, lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """
        Конвертация широты, долготы, высоты в ECEF

        :param lat: Широта в градусах
        :param lon: Долгота в градусах
        :param alt: Высота в километрах
        :return: Координаты x, y, z в километрах
        """
        # WGS84 параметры
        a = 6378137.0  # большая полуось (м)
        e = 0.0818191908426  # эксцентриситет

        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        # Вычисление N - радиус кривизны
        N = a / math.sqrt(1 - (e * math.sin(lat_rad))**2)

        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = ((1 - e**2) * N + alt) * math.sin(lat_rad)

        return x/1000, y/1000, z/1000  # Конвертируем в км


class Database:
    """Класс для работы со справочниками в памяти"""

    def __init__(self):
        """Инициализация базы данных"""
        # Создаем директорию для данных, если её нет
        os.makedirs(WORK_DIR, exist_ok=True)

        # Инициализируем пустые списки для хранения данных в памяти
        self.categories = []
        self.orbit_types = []
        self.satellites = []
        self.tle_data = {}  # Словарь для хранения TLE данных {name: (tle1, tle2)}

        print("Инициализация справочников...")
        # Пытаемся загрузить справочники из файлов
        if not self.load_references():
            print("Справочники не найдены, создаем новые...")
            self.initialize_references()
            self.save_references()

        # Загружаем данные спутников из Celestrak
        self._load_celestrak_data()

    def _load_celestrak_data(self):
        """Загрузка актуальных данных спутников из Celestrak"""
        celestrak_categories = {
            "Навигационные": [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=glonass-operational&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=galileo&FORMAT=tle"
            ],
            "Метеорологические": [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle"
            ],
            "Научные": [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"
            ],
            "Связь": [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle"
            ],
            "Наблюдение Земли": [
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle",
                "https://celestrak.org/NORAD/elements/gp.php?GROUP=sarsat&FORMAT=tle"
            ]
        }

        print("Загрузка данных спутников из Celestrak...")
        for category, urls in celestrak_categories.items():
            for url in urls:
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        lines = response.text.strip().split('\n')
                        # Обрабатываем данные по три строки (имя и две строки TLE)
                        for i in range(0, len(lines), 3):
                            if i + 2 < len(lines):
                                name = lines[i].strip()
                                tle1 = lines[i + 1].strip()
                                tle2 = lines[i + 2].strip()
                                self.tle_data[name] = (tle1, tle2)
                except Exception as e:
                    print(f"Ошибка загрузки данных из {url}: {str(e)}")

        print(f"Загружено {len(self.tle_data)} спутников с TLE данными")

    def search_satellites(self, search_term: str) -> List[str]:
        """Поиск спутников по имени"""
        search_term = search_term.lower()
        return [name for name in self.tle_data.keys() 
                if search_term in name.lower()]

    def get_satellite_tle(self, satellite_name: str) -> Optional[Tuple[str, str]]:
        """Получение TLE данных для спутника"""
        return self.tle_data.get(satellite_name)

    def get_default_categories(self) -> List[Dict[str, Any]]:
        """Возвращает список стандартных категорий спутников"""
        return [
            {
                'name': 'Навигационные',
                'description': 'Спутники для навигации и позиционирования (GPS, ГЛОНАСС, Galileo)',
                'priority': 1
            },
            {
                'name': 'Связь',
                'description': 'Телекоммуникационные спутники',
                'priority': 2
            },
            {
                'name': 'Научные',
                'description': 'Спутники для научных исследований',
                'priority': 3
            },
            {
                'name': 'Метеорологические',
                'description': 'Спутники для наблюдения за погодой и климатом',
                'priority': 4
            },
            {
                'name': 'Военные',
                'description': 'Спутники военного назначения',
                'priority': 5
            },
            {
                'name': 'Наблюдение Земли',
                'description': 'Спутники для дистанционного зондирования Земли',
                'priority': 6
            }
        ]

    def get_default_orbit_types(self) -> List[Dict[str, Any]]:
        """Возвращает список стандартных типов орбит"""
        return [
            {
                'name': 'LEO',
                'min_altitude': 160,
                'max_altitude': 2000,
                'typical_inclination': 51.6,
                'description': 'Низкая околоземная орбита'
            },
            {
                'name': 'MEO',
                'min_altitude': 2000,
                'max_altitude': 35786,
                'typical_inclination': 55.0,
                'description': 'Средняя околоземная орбита'
            },
            {
                'name': 'GEO',
                'min_altitude': 35786,
                'max_altitude': 35786,
                'typical_inclination': 0.0,
                'description': 'Геостационарная орбита'
            },
            {
                'name': 'HEO',
                'min_altitude': 500,
                'max_altitude': 50000,
                'typical_inclination': 63.4,
                'description': 'Высокоэллиптическая орбита'
            }
        ]

    def initialize_references(self):
        """Инициализация справочников начальными данными"""
        print("Создание стандартных справочников...")
        
        # Добавляем стандартные категории
        for category in self.get_default_categories():
            self.categories.append({
                'id': len(self.categories) + 1,
                'name': category['name'],
                'description': category['description'],
                'priority': category['priority'],
                'is_active': True,
                'last_update': datetime.now()
            })
        print(f"Создано категорий: {len(self.categories)}")

        # Добавляем стандартные типы орбит
        for orbit in self.get_default_orbit_types():
            self.orbit_types.append({
                'id': len(self.orbit_types) + 1,
                'name': orbit['name'],
                'min_altitude': orbit['min_altitude'],
                'max_altitude': orbit['max_altitude'],
                'typical_inclination': orbit['typical_inclination'],
                'description': orbit['description'],
                'last_update': datetime.now()
            })
        print(f"Создано типов орбит: {len(self.orbit_types)}")

    def save_references(self) -> bool:
        """Сохранение справочников в бинарные файлы"""
        try:
            print("Сохранение справочников...")
            with open(CATEGORIES_FILE, 'wb') as f:
                pickle.dump(self.categories, f)
            print(f"Категории сохранены в {CATEGORIES_FILE}")

            with open(ORBIT_TYPES_FILE, 'wb') as f:
                pickle.dump(self.orbit_types, f)
            print(f"Типы орбит сохранены в {ORBIT_TYPES_FILE}")
            return True
        except Exception as e:
            print(f"Ошибка сохранения справочников: {str(e)}")
            return False

    def load_references(self) -> bool:
        """Загрузка справочников из бинарных файлов"""
        try:
            if not os.path.exists(CATEGORIES_FILE) or not os.path.exists(ORBIT_TYPES_FILE):
                print("Файлы справочников не найдены")
                return False

            print("Загрузка справочников...")
            with open(CATEGORIES_FILE, 'rb') as f:
                self.categories = pickle.load(f)
            print(f"Загружено категорий: {len(self.categories)}")

            with open(ORBIT_TYPES_FILE, 'rb') as f:
                self.orbit_types = pickle.load(f)
            print(f"Загружено типов орбит: {len(self.orbit_types)}")
            return True
        except Exception as e:
            print(f"Ошибка загрузки справочников: {str(e)}")
            return False

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Получение списка всех категорий"""
        return sorted(self.categories, key=lambda x: (x['priority'], x['name']))

    def get_all_orbit_types(self) -> List[Dict[str, Any]]:
        """Получение списка всех типов орбит"""
        return sorted(self.orbit_types, key=lambda x: x['min_altitude'])

    def get_satellites_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Получение списка спутников по категории"""
        # Для демонстрации возвращаем все спутники, так как у нас нет привязки к категориям
        if category_name == "Все спутники":
            return [{'name': name} for name in self.tle_data.keys()]
        
        # Распределяем спутники по категориям на основе их названий
        satellites = []
        for name in self.tle_data.keys():
            if any(nav in name for nav in ["GPS", "GLONASS", "GALILEO"]) and category_name == "Навигационные":
                satellites.append({'name': name})
            elif any(met in name for met in ["NOAA", "METEOR", "METOP"]) and category_name == "Метеорологические":
                satellites.append({'name': name})
            elif any(sci in name for sci in ["ISS", "HUBBLE", "SWOT"]) and category_name == "Научные":
                satellites.append({'name': name})
            elif any(com in name for com in ["INTELSAT", "EUTELSAT"]) and category_name == "Связь":
                satellites.append({'name': name})
            elif any(obs in name for obs in ["LANDSAT", "SENTINEL"]) and category_name == "Наблюдение Земли":
                satellites.append({'name': name})
        return satellites

    def add_category(self, name: str, description: str, priority: int) -> bool:
        """Добавление новой категории"""
        try:
            # Проверяем уникальность имени
            if any(c['name'] == name for c in self.categories):
                print(f"Категория {name} уже существует")
                return False

            self.categories.append({
                'id': len(self.categories) + 1,
                'name': name,
                'description': description,
                'priority': priority,
                'is_active': True,
                'last_update': datetime.now()
            })
            self.save_references()
            return True
        except Exception as e:
            print(f"Ошибка добавления категории: {str(e)}")
            return False

    def add_orbit_type(self, name: str, min_alt: float, max_alt: float,
                      typical_incl: float, description: str) -> bool:
        """Добавление нового типа орбиты"""
        try:
            # Проверяем уникальность имени
            if any(o['name'] == name for o in self.orbit_types):
                print(f"Тип орбиты {name} уже существует")
                return False

            self.orbit_types.append({
                'id': len(self.orbit_types) + 1,
                'name': name,
                'min_altitude': min_alt,
                'max_altitude': max_alt,
                'typical_inclination': typical_incl,
                'description': description,
                'last_update': datetime.now()
            })
            self.save_references()
            return True
        except Exception as e:
            print(f"Ошибка добавления типа орбиты: {str(e)}")
            return False

    def add_satellite(self, name: str, category_id: int, orbit_type_id: int,
                     norad_id: Optional[int] = None) -> bool:
        """Добавление нового спутника"""
        try:
            # Проверяем уникальность имени
            if any(s['name'] == name for s in self.satellites):
                print(f"Спутник {name} уже существует")
                return False

            # Проверяем существование категории и типа орбиты
            if not any(c['id'] == category_id for c in self.categories):
                print(f"Категория с ID {category_id} не найдена")
                return False
            if not any(o['id'] == orbit_type_id for o in self.orbit_types):
                print(f"Тип орбиты с ID {orbit_type_id} не найден")
                return False

            self.satellites.append({
                'id': len(self.satellites) + 1,
                'name': name,
                'norad_id': norad_id,
                'category_id': category_id,
                'orbit_type_id': orbit_type_id,
                'last_update': datetime.now()
            })
            return True
        except Exception as e:
            print(f"Ошибка добавления спутника: {str(e)}")
            return False


class ReferenceManager(QMainWindow):
    """Графический интерфейс для управления справочниками"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление справочниками")
        self.setGeometry(100, 100, 800, 600)

        # Инициализируем базу данных при запуске
        self.db = Database()
        
        # Создаем центральный виджет и общий layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем вкладки для разных справочников
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Вкладка категорий
        categories_tab = QWidget()
        tabs.addTab(categories_tab, "Категории спутников")
        self._setup_categories_tab(categories_tab)

        # Вкладка спутников
        satellites_tab = QWidget()
        tabs.addTab(satellites_tab, "Спутники")
        self._setup_satellites_tab(satellites_tab)

        # Кнопки для сохранения/загрузки в двоичном формате
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        save_bin_btn = QPushButton("Сохранить в двоичном формате")
        save_bin_btn.clicked.connect(self._save_binary)
        btn_layout.addWidget(save_bin_btn)

        load_bin_btn = QPushButton("Загрузить из двоичного формата")
        load_bin_btn.clicked.connect(self._load_binary)
        btn_layout.addWidget(load_bin_btn)

    def _setup_categories_tab(self, tab):
        layout = QVBoxLayout(tab)

        # Таблица категорий
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels([
            "Название", "Описание", "Количество спутников", "Последнее обновление"
        ])
        layout.addWidget(self.categories_table)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        add_btn = QPushButton("Добавить категорию")
        add_btn.clicked.connect(self._add_category)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Удалить категорию")
        del_btn.clicked.connect(self._delete_category)
        btn_layout.addWidget(del_btn)

        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self._save_categories)
        btn_layout.addWidget(save_btn)

        self._load_categories()

    def _setup_satellites_tab(self, tab):
        layout = QVBoxLayout(tab)

        # Фильтр по категории
        filter_layout = QHBoxLayout()
        layout.addLayout(filter_layout)

        filter_layout.addWidget(QLabel("Фильтр по категории:"))
        self.category_filter = QComboBox()
        self.category_filter.currentIndexChanged.connect(
            self._filter_satellites)
        filter_layout.addWidget(self.category_filter)

        # Таблица спутников
        self.satellites_table = QTableWidget()
        self.satellites_table.setColumnCount(7)
        self.satellites_table.setHorizontalHeaderLabels([
            "Название", "NORAD ID", "Категория", "Период (мин)",
            "Наклонение (град)", "Апогей (км)", "Перигей (км)"
        ])
        layout.addWidget(self.satellites_table)

        # Кнопки управления
        btn_layout = QHBoxLayout()
        layout.addLayout(btn_layout)

        add_btn = QPushButton("Добавить спутник")
        add_btn.clicked.connect(self._add_satellite)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("Удалить спутник")
        del_btn.clicked.connect(self._delete_satellite)
        btn_layout.addWidget(del_btn)

        save_btn = QPushButton("Сохранить изменения")
        save_btn.clicked.connect(self._save_satellites)
        btn_layout.addWidget(save_btn)

        self._load_satellites()

    def _load_categories(self):
        """Загрузка категорий из базы данных"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT c.name, c.description, COUNT(s.satellite_id) as total_satellites, c.last_update
                FROM satellite_categories c
                LEFT JOIN satellites s ON c.category_id = s.category_id
                GROUP BY c.category_id, c.name, c.description, c.last_update
                ORDER BY c.priority, c.name
                ''')
                
                # Очищаем таблицу
                self.categories_table.setRowCount(0)
                
                # Заполняем данными из базы
                for row_data in cursor.fetchall():
                    row = self.categories_table.rowCount()
                    self.categories_table.insertRow(row)
                    for col, value in enumerate(row_data):
                        item = QTableWidgetItem(str(value))
                        self.categories_table.setItem(row, col, item)
                
                self._update_category_filter()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки категорий: {str(e)}")

    def _load_satellites(self):
        """Загрузка спутников из базы данных"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT s.name, s.norad_id, c.name as category, 
                       s.period_minutes, s.inclination_deg, s.apogee_km, s.perigee_km
                FROM satellites s
                LEFT JOIN satellite_categories c ON s.category_id = c.category_id
                ORDER BY s.name
                ''')
                
                # Очищаем таблицу
                self.satellites_table.setRowCount(0)
                
                # Заполняем данными из базы
                for row_data in cursor.fetchall():
                    row = self.satellites_table.rowCount()
                    self.satellites_table.insertRow(row)
                    for col, value in enumerate(row_data):
                        item = QTableWidgetItem(str(value))
                        self.satellites_table.setItem(row, col, item)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка загрузки спутников: {str(e)}")

    def _update_category_filter(self):
        self.category_filter.clear()
        self.category_filter.addItem("Все категории")
        categories = []
        for i in range(self.categories_table.rowCount()):
            category = self.categories_table.item(i, 0)
            if category:
                categories.append(category.text())
        self.category_filter.addItems(categories)

    def _add_category(self):
        row = self.categories_table.rowCount()
        self.categories_table.insertRow(row)
        self._update_category_filter()

    def _delete_category(self):
        current_row = self.categories_table.currentRow()
        if current_row >= 0:
            self.categories_table.removeRow(current_row)
            self._update_category_filter()

    def _add_satellite(self):
        row = self.satellites_table.rowCount()
        self.satellites_table.insertRow(row)

    def _delete_satellite(self):
        current_row = self.satellites_table.currentRow()
        if current_row >= 0:
            self.satellites_table.removeRow(current_row)

    def _save_categories(self):
        """Сохранение изменений в категориях"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем все текущие категории из таблицы интерфейса
                categories = []
                for row in range(self.categories_table.rowCount()):
                    category = {
                        'name': self.categories_table.item(row, 0).text(),
                        'description': self.categories_table.item(row, 1).text(),
                        'priority': row + 1  # Приоритет по порядку строк
                    }
                    categories.append(category)
                
                # Обновляем базу данных
                for category in categories:
                    cursor.execute('''
                    INSERT OR REPLACE INTO satellite_categories 
                    (name, description, priority, is_active, last_update)
                    VALUES (?, ?, ?, 1, datetime('now'))
                    ''', (category['name'], category['description'], category['priority']))
                
                conn.commit()
                self._load_categories()  # Перезагружаем данные
                QMessageBox.information(self, "Успех", "Категории сохранены успешно")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения категорий: {str(e)}")

    def _save_satellites(self):
        """Сохранение изменений в спутниках"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Получаем все текущие спутники из таблицы интерфейса
                satellites = []
                for row in range(self.satellites_table.rowCount()):
                    satellite = {
                        'name': self.satellites_table.item(row, 0).text(),
                        'norad_id': self.satellites_table.item(row, 1).text(),
                        'category': self.satellites_table.item(row, 2).text(),
                        'period_minutes': self.satellites_table.item(row, 3).text(),
                        'inclination_deg': self.satellites_table.item(row, 4).text(),
                        'apogee_km': self.satellites_table.item(row, 5).text(),
                        'perigee_km': self.satellites_table.item(row, 6).text()
                    }
                    satellites.append(satellite)
                
                # Обновляем базу данных
                for satellite in satellites:
                    # Получаем ID категории
                    cursor.execute('SELECT category_id FROM satellite_categories WHERE name = ?',
                                 (satellite['category'],))
                    result = cursor.fetchone()
                    if result:
                        category_id = result[0]
                        cursor.execute('''
                        INSERT OR REPLACE INTO satellites 
                        (name, norad_id, category_id, period_minutes, 
                         inclination_deg, apogee_km, perigee_km, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        ''', (
                            satellite['name'],
                            int(satellite['norad_id']) if satellite['norad_id'] else None,
                            category_id,
                            float(satellite['period_minutes']) if satellite['period_minutes'] else None,
                            float(satellite['inclination_deg']) if satellite['inclination_deg'] else None,
                            float(satellite['apogee_km']) if satellite['apogee_km'] else None,
                            float(satellite['perigee_km']) if satellite['perigee_km'] else None
                        ))
                
                conn.commit()
                self._load_satellites()  # Перезагружаем данные
                QMessageBox.information(self, "Успех", "Спутники сохранены успешно")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка сохранения спутников: {str(e)}")

    def _filter_satellites(self):
        """Фильтрация спутников по выбранной категории"""
        try:
            category = self.category_filter.currentText()
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                if category == "Все категории":
                    cursor.execute('''
                    SELECT s.name, s.norad_id, c.name as category, 
                           s.period_minutes, s.inclination_deg, s.apogee_km, s.perigee_km
                    FROM satellites s
                    LEFT JOIN satellite_categories c ON s.category_id = c.category_id
                    ORDER BY s.name
                    ''')
                else:
                    cursor.execute('''
                    SELECT s.name, s.norad_id, c.name as category, 
                           s.period_minutes, s.inclination_deg, s.apogee_km, s.perigee_km
                    FROM satellites s
                    LEFT JOIN satellite_categories c ON s.category_id = c.category_id
                    WHERE c.name = ?
                    ORDER BY s.name
                    ''', (category,))
                
                # Очищаем таблицу
                self.satellites_table.setRowCount(0)
                
                # Заполняем отфильтрованными данными
                for row_data in cursor.fetchall():
                    row = self.satellites_table.rowCount()
                    self.satellites_table.insertRow(row)
                    for col, value in enumerate(row_data):
                        item = QTableWidgetItem(str(value))
                        self.satellites_table.setItem(row, col, item)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка фильтрации: {str(e)}")

    def _save_binary(self):
        try:
            # Получаем данные из таблиц
            categories_data = []
            for i in range(self.categories_table.rowCount()):
                row = []
                for j in range(self.categories_table.columnCount()):
                    item = self.categories_table.item(i, j)
                    row.append(item.text() if item else "")
                categories_data.append(row)

            satellites_data = []
            for i in range(self.satellites_table.rowCount()):
                row = []
                for j in range(self.satellites_table.columnCount()):
                    item = self.satellites_table.item(i, j)
                    row.append(item.text() if item else "")
                satellites_data.append(row)

            # Создаем объект для сохранения
            data = {
                'categories': categories_data,
                'satellites': satellites_data
            }

            # Сохраняем в двоичном формате
            binary_file = os.path.join(WORK_DIR, 'references.bin')
            with open(binary_file, 'wb') as f:
                pickle.dump(data, f)

            QMessageBox.information(self, "Успех",
                                    f"Данные сохранены в двоичном формате: {binary_file}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Ошибка сохранения в двоичном формате: {str(e)}")

    def _load_binary(self):
        try:
            binary_file = os.path.join(WORK_DIR, 'references.bin')
            if not os.path.exists(binary_file):
                raise FileNotFoundError("Файл с двоичными данными не найден")

            # Загружаем данные
            with open(binary_file, 'rb') as f:
                data = pickle.load(f)

            # Обновляем таблицу категорий
            self.categories_table.setRowCount(len(data['categories']))
            for i, row in enumerate(data['categories']):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.categories_table.setItem(i, j, item)

            # Обновляем таблицу спутников
            self.satellites_table.setRowCount(len(data['satellites']))
            for i, row in enumerate(data['satellites']):
                for j, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.satellites_table.setItem(i, j, item)

            self._update_category_filter()
            QMessageBox.information(
                self, "Успех", "Данные загружены из двоичного формата")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка",
                                f"Ошибка загрузки из двоичного формата: {str(e)}")


def main():
    """Точка входа для запуска графического интерфейса"""
    app = QApplication(sys.argv)
    window = ReferenceManager()
    window.show()
    sys.exit(app.exec())
