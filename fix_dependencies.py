#!/usr/bin/env python3
"""
Скрипт автоматического исправления зависимостей
Исправляет конфликты версий aiogram для Python 3.10
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Выполнение команды с логированием"""
    print(f"\n🔧 {description}")
    print(f"Выполняю: {command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 минут таймаут
        )
        
        if result.returncode == 0:
            print("✅ Успешно")
            if result.stdout:
                print("Вывод:", result.stdout.strip())
            return True
        else:
            print("❌ Ошибка")
            if result.stderr:
                print("Ошибка:", result.stderr.strip())
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут команды")
        return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    print(f"🐍 Python версия: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and 8 <= version.minor <= 10:
        print("✅ Версия Python подходящая")
        return True
    else:
        print("⚠️  Рекомендуется Python 3.8-3.10 для стабильной работы")
        return False

def fix_dependencies():
    """Исправление зависимостей"""
    print("=" * 60)
    print("🚀 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ЗАВИСИМОСТЕЙ")
    print("=" * 60)
    
    # Проверяем Python
    check_python_version()
    
    steps = [
        # Шаг 1: Удаление конфликтующих пакетов
        (
            "pip uninstall aiogram aiohttp Babel certifi -y",
            "Удаление конфликтующих пакетов"
        ),
        
        # Шаг 2: Очистка кэша pip
        (
            "pip cache purge",
            "Очистка кэша pip"
        ),
        
        # Шаг 3: Обновление pip
        (
            "pip install --upgrade pip",
            "Обновление pip"
        ),
        
        # Шаг 4: Установка совместимых версий основных пакетов
        (
            "pip install 'aiohttp>=3.8.0,<3.9.0'",
            "Установка совместимой версии aiohttp"
        ),
        
        (
            "pip install 'Babel>=2.9.1,<2.10.0'",
            "Установка совместимой версии Babel"
        ),
        
        (
            "pip install aiogram==2.25.1",
            "Установка aiogram 2.25.1"
        ),
        
        # Шаг 5: Установка остальных зависимостей
        (
            "pip install python-dotenv==1.0.0",
            "Установка python-dotenv"
        ),
        
        (
            "pip install aiosqlite==0.19.0",
            "Установка aiosqlite"
        ),
        
        (
            "pip install aioschedule==0.5.2",
            "Установка aioschedule"
        ),
        
        (
            "pip install magic-filter==1.0.12",
            "Установка magic-filter"
        ),
        
        (
            "pip install pytz==2023.3",
            "Установка pytz"
        ),
        
        (
            "pip install 'pandas>=2.0.0,<2.2.0'",
            "Установка pandas"
        ),
        
        (
            "pip install 'openpyxl>=3.1.0,<3.2.0'",
            "Установка openpyxl"
        ),
        
        (
            "pip install 'reportlab>=4.0.0,<4.1.0'",
            "Установка reportlab"
        ),
        
        (
            "pip install 'requests>=2.31.0,<2.32.0'",
            "Установка requests"
        ),
        
        (
            "pip install 'psutil>=5.9.0,<6.0.0'",
            "Установка psutil"
        )
    ]
    
    failed_steps = []
    
    for command, description in steps:
        success = run_command(command, description)
        if not success:
            failed_steps.append((command, description))
    
    # Итоговая проверка
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ")
    print("=" * 60)
    
    if failed_steps:
        print("❌ Некоторые шаги завершились с ошибками:")
        for command, description in failed_steps:
            print(f"   - {description}")
        print("\n💡 Попробуйте выполнить неудачные команды вручную")
    else:
        print("✅ Все зависимости установлены успешно!")
    
    # Проверка импорта
    print("\n🔍 Проверка импорта aiogram...")
    try:
        import aiogram
        print(f"✅ aiogram {aiogram.__version__} импортирован успешно")
        
        from aiogram import Bot, Dispatcher
        print("✅ Bot и Dispatcher импортированы")
        
        print("\n🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
        print("Теперь можно запускать диагностику: python diagnose_issues.py")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта aiogram: {e}")
        print("💡 Возможно нужно использовать виртуальное окружение")

def create_virtual_environment():
    """Создание виртуального окружения"""
    print("=" * 60)
    print("📦 СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ")
    print("=" * 60)
    
    venv_steps = [
        ("python3.10 -m venv venv_bot", "Создание виртуального окружения"),
        ("source venv_bot/bin/activate && pip install --upgrade pip", "Обновление pip в venv"),
        ("source venv_bot/bin/activate && pip install -r requirements_python310.txt", "Установка зависимостей в venv")
    ]
    
    for command, description in venv_steps:
        run_command(command, description)
    
    print("\n✅ Виртуальное окружение создано!")
    print("Для активации используйте:")
    print("   source venv_bot/bin/activate")
    print("   python diagnose_issues.py")

def main():
    """Главная функция"""
    print("Выберите действие:")
    print("1. Исправить зависимости в текущем окружении")
    print("2. Создать виртуальное окружение")
    print("3. Выход")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == "1":
        fix_dependencies()
    elif choice == "2":
        create_virtual_environment()
    elif choice == "3":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()