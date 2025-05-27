"""Модуль для работы со списком спутников."""
from tle_parcer import get_all_satellites, search_satellites


def get_satellite_list():
    """Возвращает отсортированный список всех доступных спутников."""
    return get_all_satellites()


def search_satellite(keyword):
    """Поиск спутников по ключевому слову."""
    if not keyword:
        return []
    return search_satellites(keyword)


if __name__ == "__main__":
    # Тестирование
    print("Загрузка списка спутников...")
    satellites = get_satellite_list()
    print(f"Всего доступно спутников: {len(satellites)}")
    print("\nПервые 10 спутников:")
    for i, name in enumerate(satellites[:10], 1):
        print(f"{i}. {name}")

    # Тестируем поиск
    while True:
        search_term = input("\nВведите часть названия спутника для поиска (или пустую строку для выхода): ")
        if not search_term:
            break
            
        results = search_satellite(search_term)
        print(f"\nНайдено {len(results)} спутников:")
        for i, name in enumerate(results[:10], 1):
            print(f"{i}. {name}")
