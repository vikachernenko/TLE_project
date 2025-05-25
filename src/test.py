from datetime import datetime, timedelta
from satellite_position import Satellite

# Пример TLE для спутника NOAA-19 (данные могут быть устаревшими)
tle1 = '1 06235U 72082A   25078.96535962 -.00000020  00000-0  16590-3 0  9999'
tle2 = '2 06235 102.0253  87.2007 0003765 319.2629  55.2466 12.53197307398059'

# Создаем объект спутника
satellite = Satellite(
    sat_name="NOAA-19",
    tle1=tle1,
    tle2=tle2
)

# Наземная станция в Москве (широта, долгота, высота в метрах)
ground_station = {
    'lat': 55.7558,
    'lon': 37.6173,
    'alt': 150  # высота в метрах
}

# 1. Расчет текущей позиции спутника
timestamp = datetime.utcnow()
position = satellite.calculate_satellite_position(timestamp)
print(position['earth_mj2000'])
print(f"Текущие координаты {satellite.name}:")
print(f"- Широта: {position['latitude']:.2f}°")
print(f"- Долгота: {position['longitude']:.2f}°")
print(f"- Высота: {position['altitude']:.2f} км\n")

# 2. Расчет положения относительно наблюдателя
look = satellite.get_observer_look(ground_station, timestamp)
print(f"Наблюдение со станции:")
print(f"- Азимут: {look['azimuth']:.1f}°")
print(f"- Возвышение: {look['elevation']:.1f}°\n")

# 3. Поиск контактов в ближайшие 24 часа
start_time = datetime.utcnow()
duration_hours = 24
contacts = satellite.get_contacts_times(ground_station, start_time, duration_hours, horizon=5.0)

if contacts:
    print(f"Предстоящие контакты (минимум 5° над горизонтом):")
    for i, (rise_time, max_elev_time, set_time) in enumerate(contacts, 1):
        print(f"Контакт #{i}:")
        print(f"- Начало: {rise_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"- Максимальное возвышение: {max_elev_time.strftime('%H:%M:%S UTC')}")
        print(f"- Конец: {set_time.strftime('%H:%M:%S UTC')}\n")
else:
    print("Контактов не обнаружено.")