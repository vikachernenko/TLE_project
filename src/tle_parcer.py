"""Модуль для загрузки и кэширования TLE строк спутников."""
import requests
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

CACHE_FILE = "tle_cache.json"
CACHE_EXPIRE_HOURS = 24  # Кэширование на 24 часа

# URLs для получения данных
BASE_URL = "https://tle.ivanstanojevic.me/api/tle"
CELESTRAK_URLS = {
    "STATIONS": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
    "WEATHER": "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
    "NOAA": "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle",
    "GOES": "https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle",
    "RESOURCE": "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle",
    "SARSAT": "https://celestrak.org/NORAD/elements/gp.php?GROUP=sarsat&FORMAT=tle",
    "SCIENCE": "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
    "EDUCATION": "https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=tle"
}

def fetch_tle(satellite_name):
    """Возвращает TLE строки для заданного спутника с кэшированием."""
    # Попробуем получить данные из кэша
    cached_data = _load_from_cache()
    if cached_data and satellite_name in cached_data:
        return cached_data[satellite_name]

    # Если нет в кэше - загружаем новые данные
    tle_data = _fetch_all_tle()
    if not tle_data:
        raise ValueError("Не удалось загрузить данные о спутниках")

    # Ищем нужный спутник
    for name, lines in tle_data.items():
        if satellite_name.lower() in name.lower():
            _save_to_cache(tle_data)
            return lines[0], lines[1]

    raise ValueError(f"Спутник '{satellite_name}' не найден!")


def _fetch_all_tle():
    """Загружает все TLE данные из разных источников."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    try:
        tle_data = {}
        total_satellites = 0

        # 1. Загружаем данные из основного API
        page = 1
        while page <= 10:  # Загружаем первые 10 страниц
            try:
                url = f"{BASE_URL}?page={page}"
                print(f"Загрузка страницы {page} из основного API...")
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'member' not in data or not data['member']:
                    break
                    
                for sat in data['member']:
                    if 'name' in sat and 'line1' in sat and 'line2' in sat:
                        name = sat['name'].strip()
                        line1 = sat['line1'].strip()
                        line2 = sat['line2'].strip()
                        if len(line1) > 50 and len(line2) > 50:
                            tle_data[name] = (line1, line2)
                            total_satellites += 1
                
                print(f"Загружено {len(data['member'])} спутников со страницы {page}")
                page += 1
                
            except Exception as e:
                print(f"Ошибка при загрузке страницы {page}: {e}")
                break

        # 2. Загружаем данные из Celestrak по категориям
        for category, url in CELESTRAK_URLS.items():
            try:
                print(f"Загрузка спутников категории {category}...")
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                lines = response.text.splitlines()
                
                for i in range(0, len(lines), 3):
                    if i + 2 >= len(lines):
                        break
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    if name and len(line1) > 50 and len(line2) > 50:
                        tle_data[name] = (line1, line2)
                        total_satellites += 1
                
                print(f"Загружено спутников категории {category}: {len(lines)//3}")
                
            except Exception as e:
                print(f"Ошибка при загрузке категории {category}: {e}")
                continue

        print(f"Всего загружено уникальных спутников: {total_satellites}")
        return tle_data if tle_data else None
            
    except Exception as e:
        print(f"Ошибка при загрузке TLE данных: {e}")
        return None


def get_all_satellites():
    """Возвращает список названий всех доступных спутников."""
    # Пробуем получить данные из кэша
    cached_data = _load_from_cache()
    if cached_data:
        return sorted(list(cached_data.keys()))

    # Если кэш пуст - загружаем новые данные
    tle_data = _fetch_all_tle()
    if tle_data:
        return sorted(list(tle_data.keys()))

    return []


def search_satellites(keyword):
    """Поиск спутников по ключевому слову."""
    satellites = get_all_satellites()
    keyword = keyword.lower()
    return sorted([name for name in satellites if keyword in name.lower()])


def get_satellite_categories():
    """Возвращает список доступных категорий спутников."""
    return list(CELESTRAK_URLS.keys())


def _load_from_cache():
    """Загружает данные из кэша, если они актуальны."""
    if not Path(CACHE_FILE).exists():
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            cache_time = datetime.fromisoformat(data['timestamp'])
            if (datetime.now() - cache_time) < timedelta(hours=CACHE_EXPIRE_HOURS):
                return data['tle_data']
    except Exception as e:
        print(f"Ошибка чтения кэша: {e}")
    return None


def _save_to_cache(tle_data):
    """Сохраняет данные в кэш."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'tle_data': tle_data
            }, f)
    except Exception as e:
        print(f"Ошибка сохранения кэша: {e}")


if __name__ == "__main__":
    # Тестирование
    print("Загрузка списка спутников...")
    print("\nДоступные категории спутников:")
    for category in get_satellite_categories():
        print(f"- {category}")
        
    satellites = get_all_satellites()
    print(f"\nВсего доступно спутников: {len(satellites)}")
    
    # Тестируем поиск
    while True:
        search_term = input("\nВведите часть названия спутника для поиска (или пустую строку для выхода): ")
        if not search_term:
            break
            
        results = search_satellites(search_term)
        print(f"\nНайдено {len(results)} спутников:")
        for i, name in enumerate(results[:10], 1):
            print(f"{i}. {name}")
        
        if results:
            try:
                selected = int(input("\nВыберите номер спутника для получения TLE (или 0 для нового поиска): "))
                if 0 < selected <= len(results):
                    line1, line2 = fetch_tle(results[selected-1])
                    print("\nTLE данные:")
                    print(line1)
                    print(line2)
            except ValueError:
                print("Некорректный ввод")

# import sqlite3
# import requests
# import time
# from pathlib import Path

# DB_FILE = "satellites.db"
# CACHE_TIME = 2 * 60 * 60  # 2 часа в секундах


# def get_tle_data():
#     # Проверяем, когда последний раз обновлялись данные
#     last_update = 0
#     if Path(DB_FILE).exists():
#         conn = sqlite3.connect(DB_FILE)
#         cursor = conn.cursor()
#         cursor.execute("SELECT MAX(last_updated) FROM tle_data")
#         last_update = cursor.fetchone()[0] or 0
#         conn.close()

#     # Если прошло меньше 2 часов — используем кэш
#     if time.time() - last_update < CACHE_TIME:
#         print("Используем кэшированные данные")
#         return

#     # Если нет — загружаем новые
#     URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
#     try:
#         response = requests.get(URL, timeout=10)
#         response.raise_for_status()
#         tle_data = response.text.splitlines()

#         conn = sqlite3.connect(DB_FILE)
#         cursor = conn.cursor()
#         cursor.execute("""
#         CREATE TABLE IF NOT EXISTS tle_data (
#             norad_id INTEGER PRIMARY KEY,
#             name TEXT,
#             line1 TEXT,
#             line2 TEXT,
#             last_updated INTEGER
#         )
#         """)

#         for i in range(0, len(tle_data), 3):
#             if i + 2 >= len(tle_data):
#                 break
#             name = tle_data[i].strip()
#             line1 = tle_data[i+1]
#             line2 = tle_data[i+2]
#             norad_id = int(line1[2:7])  # NORAD ID из строки TLE

#             cursor.execute(
#                 "INSERT OR REPLACE INTO tle_data VALUES (?, ?, ?, ?, ?)",
#                 (norad_id, name, line1, line2, int(time.time()))
#             )

#         conn.commit()
#         print("Данные обновлены!")
#     except requests.exceptions.RequestException as e:
#         print(f"Ошибка запроса: {e}")
#     finally:
#         if 'conn' in locals():
#             conn.close()


# get_tle_data()
