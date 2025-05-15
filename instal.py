import subprocess
import sys
import os
import shutil


def check_anaconda():
    try:
        result = subprocess.run(['conda', '--version'],
                                capture_output=True, text=True, check=True)
        print(f"Anaconda найдена: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Ошибка: Anaconda не найдена. Установите Anaconda и добавьте в PATH.")
        return False


def create_virtual_env():
    env_name = "satellite_tracker"
    try:
        print(f"Создание виртуальной среды {env_name}...")
        subprocess.run(['conda', 'create', '-n', env_name,
                       'python=3.8', '-y'], check=True)
        print(f"Виртуальная среда {env_name} успешно создана.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании виртуальной среды: {e}")
        return False


def install_dependencies():
    env_name = "satellite_tracker"
    dependencies = [
        "pandas",
        "numpy",
        "matplotlib"
    ]
    pip_dependencies = [
        "visual",
        "pyorbital"
    ]

    try:
        conda_path = shutil.which('conda')
        if not conda_path:
            raise FileNotFoundError("Conda не найдена в PATH.")

        print("Установка зависимостей через conda...")
        for dep in dependencies:
            subprocess.run([conda_path, 'install', '-n',
                           env_name, dep, '-y'], check=True)
            print(f"Установлен {dep}.")

        print("Установка зависимостей через pip...")
        python_path = os.path.join(os.path.dirname(
            conda_path), '..', 'envs', env_name, 'python.exe')
        for dep in pip_dependencies:
            subprocess.run([python_path, '-m', 'pip',
                           'install', dep], check=True)
            print(f"Установлен {dep}.")

        print("Все зависимости успешно установлены.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Ошибка при установке зависимостей: {e}")
        return False


def main():
    print("Запуск установки для приложения трекинга спутников...")

    if not check_anaconda():
        sys.exit(1)

    if not create_virtual_env():
        sys.exit(1)

    if not install_dependencies():
        sys.exit(1)

    print("Установка завершена успешно!")
    print("Для активации среды выполните: conda activate satellite_tracker")
    print("Проверьте установку, запустив: python -c \"import pandas, numpy, matplotlib, visual, pyorbital\"")


if __name__ == "__main__":
    main()
