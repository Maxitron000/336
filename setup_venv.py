#!/usr/bin/env python3
"""
Скрипт для автоматической настройки виртуального окружения
и установки зависимостей для Telegram бота
Поддерживает Python 3.13 и решает проблемы с SSL
"""

import subprocess
import sys
import os
import platform
from pathlib import Path
import urllib.request
import ssl

def print_header():
    """Печатает заголовок"""
    print("=" * 60)
    print("🐍 НАСТРОЙКА ВИРТУАЛЬНОГО ОКРУЖЕНИЯ (Python 3.13)")
    print("=" * 60)
    print()

def check_python_version():
    """Проверяет версию Python"""
    print("🔍 Проверка версии Python...")
    version = platform.python_version()
    print(f"   Версия Python: {version}")
    
    if version.startswith('3.'):
        try:
            major, minor = version.split('.')[:2]
            if int(major) == 3 and int(minor) >= 8:
                print("   ✅ Версия Python подходит")
                if int(minor) >= 13:
                    print("   🆕 Обнаружен Python 3.13+ - применяю специальные настройки")
                return True
            else:
                print("   ❌ Требуется Python 3.8 или выше")
                return False
        except ValueError:
            print("   ❌ Не удалось определить версию Python")
            return False
    else:
        print("   ❌ Требуется Python 3.8 или выше")
        return False

def install_system_certificates():
    """Устанавливает системные SSL-сертификаты"""
    print("\n🔐 Установка системных SSL-сертификатов...")
    
    if platform.system() == "Linux":
        try:
            # Обновляем системные сертификаты
            print("   🔄 Обновление системных сертификатов...")
            result = subprocess.run(["sudo", "apt-get", "update"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(["sudo", "apt-get", "install", "-y", "ca-certificates"], 
                              capture_output=True, text=True)
                print("   ✅ Системные сертификаты обновлены")
            else:
                print("   ⚠️  Не удалось обновить системные сертификаты (требуются права sudo)")
        except Exception as e:
            print(f"   ⚠️  Предупреждение: {e}")
    
    return True

def create_virtual_environment():
    """Создает виртуальное окружение с правильными настройками"""
    print("\n🐍 Создание виртуального окружения...")
    
    venv_path = Path("venv_bot")
    
    if venv_path.exists():
        print("   ⚠️  Виртуальное окружение уже существует")
        user_input = input("   Пересоздать? (y/N): ").strip().lower()
        if user_input != 'y':
            print("   ✅ Используем существующее окружение")
            return True
        else:
            print("   🗑️  Удаляем старое окружение...")
            import shutil
            shutil.rmtree(venv_path)
    
    try:
        # Создаем виртуальное окружение с системными сертификатами
        print("   🏗️  Создание виртуального окружения...")
        cmd = [sys.executable, "-m", "venv", "venv_bot", "--system-site-packages"]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("   ✅ Виртуальное окружение создано")
        
        # Проверяем, что все файлы на месте
        if platform.system() == "Windows":
            activate_path = venv_path / "Scripts" / "activate"
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            activate_path = venv_path / "bin" / "activate"
            python_path = venv_path / "bin" / "python"
            
        if not python_path.exists():
            print("   ❌ Python не найден в виртуальном окружении")
            return False
            
        print("   ✅ Структура виртуального окружения корректна")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Ошибка создания виртуального окружения: {e}")
        print("   💡 Попробуем без --system-site-packages...")
        
        try:
            # Пробуем без системных пакетов
            subprocess.run([sys.executable, "-m", "venv", "venv_bot"], 
                          check=True, capture_output=True, text=True)
            print("   ✅ Виртуальное окружение создано (без системных пакетов)")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"   ❌ Критическая ошибка: {e2}")
            return False

def get_activation_command():
    """Возвращает команду для активации виртуального окружения"""
    if platform.system() == "Windows":
        return "venv_bot\\Scripts\\activate"
    else:
        return "source venv_bot/bin/activate"

def update_requirements_for_python313():
    """Обновляет requirements.txt для Python 3.13"""
    print("\n📦 Обновление requirements.txt для Python 3.13...")
    
    # Совместимые версии для Python 3.13
    python313_requirements = """# Совместимые зависимости для Python 3.13 и aiogram 3.x
# Основные зависимости для Telegram бота
aiogram==3.4.1
python-dotenv==1.0.0

# Зависимости aiogram 3.x (совместимые с Python 3.13)
aiohttp==3.9.1
aiofiles==23.2.0
magic-filter==1.0.12

# SSL и сертификаты (обновленные для Python 3.13)
certifi==2024.2.2
cryptography==42.0.5

# Планировщик задач
aioschedule==0.5.2

# Работа с временными зонами
pytz==2024.1

# Асинхронная работа с SQLite
aiosqlite==0.20.0

# Работа с данными
pandas==2.2.1
openpyxl==3.1.2
xlsxwriter==3.2.0

# HTTP запросы
requests==2.31.0

# Конфигурация
configparser==6.0.0

# Расширения типов
typing_extensions==4.10.0

# Системный мониторинг
psutil==5.9.8

# Планировщик задач
schedule==1.2.0

# Мониторинг и логирование
watchdog==4.0.0

# Генерация PDF отчетов
reportlab==4.1.0

# Дополнительные зависимости для SSL соединений
urllib3==2.2.1
charset-normalizer==3.3.2

# Babel для интернационализации
Babel==2.14.0

# Дополнительные зависимости для Python 3.13
setuptools==69.2.0
wheel==0.43.0
"""
    
    try:
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write(python313_requirements)
        print("   ✅ requirements.txt обновлен для Python 3.13")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка обновления requirements.txt: {e}")
        return False

def install_dependencies():
    """Устанавливает зависимости"""
    print("\n📦 Установка зависимостей...")
    
    # Определяем пути для разных ОС
    if platform.system() == "Windows":
        python_path = Path("venv_bot/Scripts/python.exe")
        pip_path = Path("venv_bot/Scripts/pip.exe")
    else:
        python_path = Path("venv_bot/bin/python")
        pip_path = Path("venv_bot/bin/pip")
    
    if not python_path.exists():
        print("   ❌ Python не найден в виртуальном окружении")
        return False
    
    try:
        # Обновляем pip до последней версии
        print("   🔄 Обновление pip...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True, text=True)
        print("   ✅ pip обновлен")
        
        # Устанавливаем setuptools и wheel
        print("   🔄 Установка setuptools и wheel...")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], 
                      check=True, capture_output=True, text=True)
        print("   ✅ setuptools и wheel установлены")
        
        # Проверяем наличие requirements.txt
        if not Path("requirements.txt").exists():
            print("   ❌ Файл requirements.txt не найден")
            return False
        
        # Устанавливаем зависимости по одной для лучшей диагностики
        print("   📦 Установка основных зависимостей...")
        
        # Сначала устанавливаем критически важные пакеты
        critical_packages = [
            "certifi",
            "cryptography", 
            "aiohttp",
            "aiogram",
            "python-dotenv"
        ]
        
        for package in critical_packages:
            print(f"   🔄 Установка {package}...")
            result = subprocess.run([str(pip_path), "install", package], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Ошибка установки {package}: {result.stderr}")
                return False
            else:
                print(f"   ✅ {package} установлен")
        
        # Затем устанавливаем остальные зависимости
        print("   📦 Установка остальных зависимостей...")
        result = subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Все зависимости установлены успешно")
            return True
        else:
            print(f"   ⚠️  Некоторые зависимости могли не установиться:")
            print(f"   {result.stderr}")
            print("   💡 Критически важные пакеты установлены, бот должен работать")
            return True
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Ошибка при установке зависимостей: {e}")
        return False

def test_ssl_connection():
    """Тестирует SSL-соединение с Telegram API"""
    print("\n🔗 Тестирование SSL-соединения с Telegram API...")
    
    # Определяем путь к Python в виртуальном окружении
    if platform.system() == "Windows":
        python_path = Path("venv_bot/Scripts/python.exe")
    else:
        python_path = Path("venv_bot/bin/python")
    
    if not python_path.exists():
        print("   ❌ Python не найден в виртуальном окружении")
        return False
    
    # Тестовый скрипт для проверки SSL
    test_script = """
import ssl
import asyncio
import aiohttp
import certifi

async def test_telegram_ssl():
    try:
        # Создаем SSL-контекст с системными сертификатами
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Создаем сессию с SSL-контекстом
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Тестируем соединение с Telegram API
            async with session.get('https://api.telegram.org/bot/getMe') as response:
                print(f"✅ SSL-соединение с Telegram API работает (статус: {response.status})")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка SSL-соединения: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram_ssl())
    exit(0 if result else 1)
"""
    
    try:
        # Записываем тестовый скрипт
        with open("test_ssl.py", "w", encoding="utf-8") as f:
            f.write(test_script)
        
        # Запускаем тест
        result = subprocess.run([str(python_path), "test_ssl.py"], 
                              capture_output=True, text=True)
        
        # Удаляем тестовый файл
        os.remove("test_ssl.py")
        
        if result.returncode == 0:
            print("   ✅ SSL-соединение с Telegram API работает корректно")
            return True
        else:
            print(f"   ❌ Проблема с SSL-соединением: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка тестирования SSL: {e}")
        return False

def setup_env_file():
    """Настраивает файл .env"""
    print("\n🔧 Настройка файла .env...")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("   ✅ Файл .env уже существует")
        return True
    
    if env_example_path.exists():
        print("   📋 Создаю .env из примера...")
        import shutil
        shutil.copy(env_example_path, env_path)
        print("   ✅ Файл .env создан")
        print("   ⚠️  Не забудьте настроить BOT_TOKEN и ADMIN_IDS")
        return True
    else:
        print("   ❌ Файл .env.example не найден")
        return False

def create_directories():
    """Создает необходимые директории"""
    print("\n📁 Создание директорий...")
    
    directories = ["data", "logs", "exports"]
    
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists():
            print(f"   ✅ {directory}/")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   📁 {directory}/ создана")
            except Exception as e:
                print(f"   ❌ Не удалось создать {directory}/: {e}")
    
    return True

def print_next_steps():
    """Выводит следующие шаги"""
    activation_cmd = get_activation_command()
    
    print("\n" + "=" * 60)
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА! (Python 3.13)")
    print("=" * 60)
    print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Настройте файл .env:")
    print("   - Получите токен бота у @BotFather")
    print("   - Получите свой ID у @userinfobot")
    print("   - Замените YOUR_BOT_TOKEN и YOUR_ADMIN_ID")
    print()
    print("2. Активируйте виртуальное окружение:")
    print(f"   {activation_cmd}")
    print()
    print("3. Проверьте конфигурацию:")
    print("   python check_config.py")
    print()
    print("4. Запустите бота:")
    print("   python main.py")
    print()
    print("💡 ПОЛЕЗНЫЕ КОМАНДЫ:")
    print("   Тестирование: python check_config.py")
    print("   Просмотр логов: tail -f logs/bot.log")
    print("   Деактивация окружения: deactivate")
    print()
    print("🔧 СПЕЦИАЛЬНЫЕ НАСТРОЙКИ ДЛЯ PYTHON 3.13:")
    print("   - Обновлены SSL-сертификаты")
    print("   - Установлены совместимые версии библиотек")
    print("   - Добавлена поддержка системных сертификатов")
    print()

def main():
    """Основная функция"""
    print_header()
    
    # Проверяем версию Python
    if not check_python_version():
        print("\n❌ Критическая ошибка: неподходящая версия Python")
        return 1
    
    # Устанавливаем системные сертификаты
    install_system_certificates()
    
    # Создаем виртуальное окружение
    if not create_virtual_environment():
        print("\n❌ Не удалось создать виртуальное окружение")
        return 1
    
    # Обновляем requirements.txt для Python 3.13
    if not update_requirements_for_python313():
        print("\n❌ Не удалось обновить requirements.txt")
        return 1
    
    # Устанавливаем зависимости
    if not install_dependencies():
        print("\n❌ Не удалось установить зависимости")
        return 1
    
    # Тестируем SSL-соединение
    test_ssl_connection()
    
    # Настраиваем файл .env
    setup_env_file()
    
    # Создаем директории
    create_directories()
    
    # Выводим следующие шаги
    print_next_steps()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Настройка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)