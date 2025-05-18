"""Модуль для загрузки, парсинга и хранения TLE-данных спутников."""
import requests
import pandas as pd
from datetime import datetime
from pyorbital.orbital import Orbital
import os


def fetch_tle_data(satellite_name, source_url="http://celestrak.com/NORAD/elements/gp.php"):
    """Загружает TLE-данные для указанного спутника с Celestrak.

    Args:
        satellite_name (str): Название спутника (например, 'ISS (ZARYA)').
        source_url (str): URL-адрес источника TLE-данных.

    Returns:
        tuple: Кортеж (line1, line2) с TLE-строками или None, если ошибка.
    """
    try:
        params = {"NAME": satellite_name, "FORMAT": "TLE"}
        response = requests.get(source_url, params=params, timeout=10)
        response.raise_for_status()
        tle_lines = response.text.strip().split("\n")
        if len(tle_lines) < 2:
            print(f"Ошибка: TLE-данные для {satellite_name} не найдены.")
            return None
        return tle_lines[1], tle_lines[2]
    except requests.RequestException as e:
        print(f"Ошибка загрузки TLE: {e}")
        return None


def parse_tle_to_dict(line1, line2):
    """Парсит TLE-строки в словарь с основными параметрами.

    Args:
        line1 (str): Первая строка TLE.
        line2 (str): Вторая строка TLE.

    Returns:
        dict: Словарь с параметрами TLE или None, если ошибка.
    """
    try:
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        epoch_year = 2000 + epoch_year if epoch_year < 50 else 1900 + epoch_year
        inclination = float(line2[8:16])
        return {
            "line1": line1,
            "line2": line2,
            "epoch_year": epoch_year,
            "epoch_day": epoch_day,
            "inclination": inclination
        }
    except (ValueError, IndexError) as e:
        print(f"Ошибка парсинга TLE: {e}")
        return None


def is_tle_valid(tle_dict, max_age_days=7):
    """Проверяет актуальность TLE по дате эпохи.

    Args:
        tle_dict (dict): Словарь с параметрами TLE.
        max_age_days (int): Максимальный возраст TLE в днях.

    Returns:
        bool: True, если TLE актуально, иначе False.
    """
    try:
        epoch_year = tle_dict["epoch_year"]
        epoch_day = tle_dict["epoch_day"]
        epoch_date = datetime(epoch_year, 1, 1) + \
            pd.Timedelta(epoch_day - 1, unit="D")
        current_date = datetime.now()
        age = (current_date - epoch_date).days
        return age <= max_age_days
    except (KeyError, ValueError) as e:
        print(f"Ошибка проверки TLE: {e}")
        return False


def save_tle_to_csv(satellite_name, tle_dict, csv_path="tle_database.csv"):
    """Сохраняет TLE-данные в CSV-файл.

    Args:
        satellite_name (str): Название спутника.
        tle_dict (dict): Словарь с параметрами TLE.
        csv_path (str): Путь к CSV-файлу.
    """
    try:
        data = {
            "satellite_name": [satellite_name],
            "line1": [tle_dict["line1"]],
            "line2": [tle_dict["line2"]],
            "epoch_year": [tle_dict["epoch_year"]],
            "epoch_day": [tle_dict["epoch_day"]],
            "inclination": [tle_dict["inclination"]],
            "timestamp": [datetime.now()]
        }
        df = pd.DataFrame(data)
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            existing_df = existing_df[existing_df["satellite_name"]
                                      != satellite_name]
            df = pd.concat([existing_df, df], ignore_index=True)
        df.to_csv(csv_path, index=False)
        print(f"TLE для {satellite_name} сохранены в {csv_path}.")
    except Exception as e:
        print(f"Ошибка сохранения TLE: {e}")


def load_tle_from_csv(satellite_name, csv_path="tle_database.csv"):
    """Загружает TLE-данные из CSV-файла.

    Args:
        satellite_name (str): Название спутника.
        csv_path (str): Путь к CSV-файлу.

    Returns:
        dict: Словарь с TLE-данными или None, если не найдено.
    """
    try:
        if not os.path.exists(csv_path):
            print(f"CSV-файл {csv_path} не существует.")
            return None
        df = pd.read_csv(csv_path)
        satellite_data = df[df["satellite_name"] == satellite_name]
        if satellite_data.empty:
            print(f"TLE для {satellite_name} не найдены в {csv_path}.")
            return None
        tle_dict = satellite_data.iloc[0].to_dict()
        if is_tle_valid(tle_dict):
            return tle_dict
        print(f"TLE для {satellite_name} устарели.")
        return None
    except Exception as e:
        print(f"Ошибка загрузки TLE из CSV: {e}")
        return None


def get_tle(satellite_name, csv_path="tle_database.csv"):
    """Получает TLE-данные, сначала проверяя CSV, затем загружая из интернета.

    Args:
        satellite_name (str): Название спутника.
        csv_path (str): Путь к CSV-файлу.

    Returns:
        tuple: Кортеж (line1, line2) или None, если ошибка.
    """
    tle_dict = load_tle_from_csv(satellite_name, csv_path)
    if tle_dict:
        return tle_dict["line1"], tle_dict["line2"]

    tle_data = fetch_tle_data(satellite_name)
    if tle_data:
        line1, line2 = tle_data
        tle_dict = parse_tle_to_dict(line1, line2)
        if tle_dict and is_tle_valid(tle_dict):
            save_tle_to_csv(satellite_name, tle_dict, csv_path)
            return line1, line2
    return None
