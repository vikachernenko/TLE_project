import sys
from tle_parcer import fetch_tle
from satellite_db import get_all_satellites, search_satellites

def test_tle_loading():
    print("Тестирование загрузки TLE данных...")
    
    # Тест получения списка спутников
    print("\n1. Получение списка всех спутников:")
    satellites = get_all_satellites()
    print(f"Найдено спутников: {len(satellites)}")
    if satellites:
        print("Первые 5 спутников:", satellites[:5])
    else:
        print("ОШИБКА: Список спутников пуст!")
    
    # Тест поиска конкретного спутника
    print("\n2. Поиск МКС:")
    iss_results = search_satellites("ISS")
    print(f"Результаты поиска: {iss_results}")
    
    # Тест получения TLE данных
    if iss_results:
        print("\n3. Получение TLE данных для МКС:")
        try:
            tle1, tle2 = fetch_tle(iss_results[0])
            print("TLE1:", tle1)
            print("TLE2:", tle2)
        except Exception as e:
            print("ОШИБКА при получении TLE:", str(e))
    
if __name__ == "__main__":
    test_tle_loading() 