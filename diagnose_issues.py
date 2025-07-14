#!/usr/bin/env python3
"""
Скрипт диагностики проблем для Telegram бота
Проверяет состояние всех компонентов системы
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def print_header(title):
    """Красивый заголовок"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def print_success(message):
    """Сообщение об успехе"""
    print(f"✅ {message}")

def print_error(message):
    """Сообщение об ошибке"""
    print(f"❌ {message}")

def print_warning(message):
    """Предупреждение"""
    print(f"⚠️  {message}")

def check_python_version():
    """Проверка версии Python"""
    print_header("Проверка версии Python")
    
    version = sys.version_info
    print(f"🐍 Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 10:
        print_success("Python 3.10 - отлично для aiogram 2.25.1")
        return True
    elif version.major == 3 and version.minor >= 11:
        print_warning(f"Python {version.major}.{version.minor} может иметь проблемы с aiogram 2.25.1")
        print("💡 Рекомендуется использовать Python 3.10")
        return False
    else:
        print_error(f"Python {version.major}.{version.minor} не поддерживается")
        return False

def check_files_exist():
    """Проверка наличия необходимых файлов"""
    print_header("Проверка файлов проекта")
    
    required_files = [
        'main.py',
        'handlers.py', 
        'database.py',
        'config.py',
        'keyboards.py',
        '.env'
    ]
    
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Файл {file} найден")
        else:
            print_error(f"Файл {file} отсутствует")
            all_exist = False
    
    return all_exist

def check_directories():
    """Проверка необходимых директорий"""
    print_header("Проверка директорий")
    
    required_dirs = ['data', 'logs', 'exports', 'config']
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print_success(f"Директория {dir_name}/ существует")
        else:
            print_warning(f"Директория {dir_name}/ отсутствует - создаю...")
            os.makedirs(dir_name, exist_ok=True)
            print_success(f"Директория {dir_name}/ создана")

def check_env_file():
    """Проверка файла .env"""
    print_header("Проверка файла .env")
    
    if not os.path.exists('.env'):
        print_error("Файл .env отсутствует")
        print("💡 Создайте файл .env с настройками:")
        print("   BOT_TOKEN=ваш_токен_бота")
        print("   ADMIN_IDS=ваш_telegram_id")
        return False
    
    # Проверяем содержимое .env
    with open('.env', 'r') as f:
        content = f.read()
    
    if 'YOUR_BOT_TOKEN' in content:
        print_warning("В .env файле есть placeholder токен")
        print("💡 Замените YOUR_BOT_TOKEN на реальный токен от @BotFather")
    
    if 'YOUR_ADMIN_ID' in content:
        print_warning("В .env файле есть placeholder admin ID")
        print("💡 Замените YOUR_ADMIN_ID на ваш Telegram ID от @userinfobot")
    
    print_success("Файл .env найден")
    return True

def check_imports():
    """Проверка импорта библиотек"""
    print_header("Проверка импорта библиотек")
    
    libraries = [
        ('aiogram', 'aiogram'),
        ('aiosqlite', 'aiosqlite'),
        ('python-dotenv', 'dotenv'),
        ('aioschedule', 'aioschedule'),
        ('aiohttp', 'aiohttp')
    ]
    
    all_imported = True
    for lib_name, import_name in libraries:
        try:
            module = importlib.import_module(import_name)
            version = getattr(module, '__version__', 'неизвестно')
            print_success(f"{lib_name} {version} импортирован")
        except ImportError:
            print_error(f"{lib_name} не установлен")
            all_imported = False
    
    return all_imported

def check_aiogram_compatibility():
    """Проверка совместимости aiogram"""
    print_header("Проверка aiogram")
    
    try:
        import aiogram
        version = aiogram.__version__
        print_success(f"aiogram версия: {version}")
        
        # Проверяем импорт основных компонентов
        from aiogram import Bot, Dispatcher, types
        from aiogram.contrib.fsm_storage.memory import MemoryStorage
        print_success("Основные компоненты aiogram импортированы")
        
        # Проверяем создание бота с фиктивным токеном
        try:
            bot = Bot(token="123456789:FAKE_TOKEN_FOR_TESTING")
            print_success("Создание объекта Bot работает")
            return True
        except Exception as e:
            print_error(f"Ошибка создания Bot: {e}")
            return False
            
    except ImportError as e:
        print_error(f"Ошибка импорта aiogram: {e}")
        return False

def check_database():
    """Проверка базы данных"""
    print_header("Проверка базы данных")
    
    try:
        from database import Database
        print_success("Модуль database импортирован")
        
        # Создаем экземпляр базы данных
        db = Database()
        print_success("Объект Database создан")
        
        return True
    except Exception as e:
        print_error(f"Ошибка с базой данных: {e}")
        return False

def generate_install_commands():
    """Генерация команд для установки"""
    print_header("Команды для исправления проблем")
    
    print("🔧 Для установки совместимых зависимостей выполните:")
    print("   pip install -r requirements_python310.txt")
    print()
    print("🔧 Если возникают конфликты версий:")
    print("   pip uninstall aiogram aiohttp Babel -y")
    print("   pip install aiogram==2.25.1 'aiohttp>=3.8.0,<3.9.0' 'Babel>=2.9.1,<2.10.0'")
    print()
    print("🔧 Для создания виртуального окружения:")
    print("   python3.10 -m venv venv")
    print("   source venv/bin/activate  # Linux/Mac")
    print("   venv\\Scripts\\activate     # Windows")
    print("   pip install -r requirements_python310.txt")

def main():
    """Главная функция диагностики"""
    print("🚀 ДИАГНОСТИКА TELEGRAM БОТА")
    print("=" * 60)
    
    checks = [
        ("Python версия", check_python_version),
        ("Файлы проекта", check_files_exist),
        ("Директории", check_directories), 
        ("Файл .env", check_env_file),
        ("Импорт библиотек", check_imports),
        ("aiogram совместимость", check_aiogram_compatibility),
        ("База данных", check_database)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Ошибка при проверке {name}: {e}")
            results.append((name, False))
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: OK")
        else:
            print_error(f"{name}: ПРОБЛЕМА")
    
    print(f"\n📊 Результат: {success_count}/{total_count} проверок пройдено")
    
    if success_count == total_count:
        print_success("Все проверки пройдены! Бот готов к запуску.")
    else:
        print_warning("Обнаружены проблемы. См. команды для исправления ниже.")
        generate_install_commands()

if __name__ == "__main__":
    main()