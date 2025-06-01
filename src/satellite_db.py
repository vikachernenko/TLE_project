import sqlite3
import pandas as pd
from typing import List, Dict, Tuple

DB_PATH = "satellites.db"


def get_all_categories() -> List[str]:
    """Возвращает список всех доступных категорий"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT category FROM satellites ORDER BY category")
        return [row[0] for row in cursor.fetchall()]


def get_satellite_list(satellite_name: str) -> Tuple[str, str]:
    """Возвращает TLE данные для конкретного спутника"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tle1, tle2 FROM satellites WHERE name = ?",
            (satellite_name,)
        )
        result = cursor.fetchone()
        if result:
            return result[0], result[1]
        raise ValueError(f"Спутник {satellite_name} не найден")


def search_satellite(query: str) -> List[str]:
    """Поиск спутников по имени"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM satellites WHERE name LIKE ? ORDER BY name",
            (f"%{query}%",)
        )
        return [row[0] for row in cursor.fetchall()]


def get_satellites_by_category(category: str) -> List[Dict[str, str]]:
    """Возвращает список спутников в указанной категории"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        if category == "Все спутники":
            cursor.execute("SELECT name, tle1, tle2 FROM satellites")
        else:
            cursor.execute(
                "SELECT name, tle1, tle2 FROM satellites WHERE category = ?",
                (category,)
            )

        return [{
            'name': row[0],
            'tle1': row[1],
            'tle2': row[2]
        } for row in cursor.fetchall()]


def initialize_db() -> bool:
    """Проверяет доступность базы данных"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='satellites'
            """)
            return cursor.fetchone() is not None
    except:
        return False
