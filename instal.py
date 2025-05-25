import subprocess
import sys

def check_anaconda():
    """Проверяет наличие Anaconda в системе."""
    try:
        result = subprocess.run(['conda', '--version'], capture_output=True, text=True, check=True)
        print(f"Anaconda найдена: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ошибка: Anaconda не найдена. Установите Anaconda и добавьте в PATH.")
        return False

def create_virtual_env():
    """Создает виртуальную среду satellite_tracker."""
    env_name = "satellite_tracker"
    try:
        print(f"Создание виртуальной среды {env_name}...")
        subprocess.run(['conda', 'create', '-n', env_name, 'python=3.8', '-y'], check=True)
        print(f"Виртуальная среда {env_name} успешно создана.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании виртуальной среды: {e}")
        return False

def install_dependencies():
    """Устанавливает зависимости в виртуальную среду."""
    env_name = "satellite_tracker"
    conda_dependencies = ["pandas", "numpy", "matplotlib", "pyqt", "requests", "cartopy", "geos", "proj", "shapely", "mkl"]
    pip_dependencies = ["vpython", "pyorbital"]
    
    try:
        print("Установка зависимостей через conda с канала conda-forge...")
        for dep in conda_dependencies:
            subprocess.run(['conda', 'install', '-n', env_name, '-c', 'conda-forge', dep, '-y'], check=True)
            print(f"Установлен {dep}.")
        
        print("Установка зависимостей через pip в виртуальной среде...")
        for dep in pip_dependencies:
            subprocess.run(['conda', 'run', '-n', env_name, 'pip', 'install', dep], check=True)
            print(f"Установлен {dep}.")
        
        print("Все зависимости успешно установлены.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        return False

def main():
    """Основная функция для выполнения установки."""
    print("Запуск установки для приложения трекинга спутников...")
    
    if not check_anaconda():
        sys.exit(1)
    
    if not create_virtual_env():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    print("Установка завершена успешно!")
    print("Для активации среды выполните: conda activate satellite_tracker")
    print("Проверьте установку, запустив: python -c \"import pandas, numpy, matplotlib, vpython, pyorbital, PyQt5, cartopy\"")

if __name__ == "__main__":
    main()