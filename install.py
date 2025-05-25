import subprocess


def check_anaconda():
    try:
        result = subprocess.run(['conda', '--version'],
                                capture_output=True, text=True, check=True)
        print(f"Анаконда найдена: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR! Анаконда не найдена: {e}")
        return False


def create_virtual_env():
    env_name = 'satellite_tracker'
    try:
        print(f"Создание виртуальной среды {env_name}.")
        subprocess.run(['conda', 'create', '-n', env_name,
                       'python=3.8', '-y'], check=True)
        print(f"Виртуальная среда {env_name} успешно создана.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании виртуальной среды: {e}")
        return False


def install_dependencies():
    env_name = "satellite_tracker"
    conda_dependencies = ["pandas", "numpy",
                          "matplotlib", "requests", "cartopy"]
    pip_dependencies = ["vpython", "pyorbital"]

    try:
        print("Установка зависимостей через conda в виртуальной среде.")
        for dep in conda_dependencies:
            subprocess.run(['conda', 'install', '--name',
                           env_name, dep, '-y'], check=True)
            print(f"Установлен {dep}.")

        print("Установка зависимостей через pip в виртуальной среде.")
        for dep in pip_dependencies:
            subprocess.run(['conda', 'run', '-n', env_name,
                           'pip', 'install', dep], check=True)
            print(f"Установлен {dep}.")

        print("Все зависимости успешно установлены.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        return False


def main():
    print("Запуск установки для приложения трекинга спутников.")
    if check_anaconda():
        if create_virtual_env():
            if install_dependencies():
                print("Установка завершена успешно!")


if __name__ == "__main__":
    main()
