#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации Telegram бота
Проверяет настройки, зависимости и подключение к API
"""

import asyncio
import os
import sys
import platform
from pathlib import Path

def print_header():
    """Печатает заголовок диагностики"""
    print("=" * 50)
    print("🔍 ДИАГНОСТИКА КОНФИГУРАЦИИ TELEGRAM БОТА")
    print("=" * 50)
    print()

def check_python_version():
    """Проверяет версию Python"""
    print("🐍 Проверка версии Python...")
    version = platform.python_version()
    print(f"   Версия Python: {version}")
    
    if version.startswith('3.'):
        major, minor = version.split('.')[:2]
        if int(major) == 3 and int(minor) >= 8:
            print("   ✅ Версия Python подходит")
            return True
        else:
            print("   ❌ Требуется Python 3.8 или выше")
            return False
    else:
        print("   ❌ Требуется Python 3.8 или выше")
        return False

def check_env_file():
    """Проверяет наличие файла .env"""
    print("\n📁 Проверка файла .env...")
    
    if not Path('.env').exists():
        print("   ❌ Файл .env не найден")
        if Path('.env.example').exists():
            print("   📋 Найден .env.example")
            print("   💡 Создайте .env файл: cp .env.example .env")
        else:
            print("   ❌ Файл .env.example также не найден")
        return False
    else:
        print("   ✅ Файл .env найден")
        return True

def check_env_variables():
    """Проверяет переменные окружения"""
    print("\n🔧 Проверка переменных окружения...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("   ❌ Модуль python-dotenv не установлен")
        return False
    
    bot_token = os.getenv('BOT_TOKEN')
    admin_ids = os.getenv('ADMIN_IDS')
    
    # Проверка токена
    if not bot_token:
        print("   ❌ BOT_TOKEN не найден")
        return False
    elif bot_token == 'YOUR_BOT_TOKEN':
        print("   ❌ BOT_TOKEN не настроен (используется значение по умолчанию)")
        print("   📋 Получите токен у @BotFather в Telegram")
        return False
    elif len(bot_token) < 30:
        print("   ❌ BOT_TOKEN слишком короткий")
        return False
    else:
        print("   ✅ BOT_TOKEN настроен")
    
    # Проверка админов
    if not admin_ids:
        print("   ❌ ADMIN_IDS не найден")
        return False
    elif admin_ids == 'YOUR_ADMIN_ID':
        print("   ❌ ADMIN_IDS не настроен (используется значение по умолчанию)")
        print("   📋 Получите свой ID у @userinfobot в Telegram")
        return False
    else:
        print("   ✅ ADMIN_IDS настроен")
    
    return True

def check_dependencies():
    """Проверяет установленные зависимости"""
    print("\n📦 Проверка зависимостей...")
    
    required_packages = [
        'aiogram',
        'aiohttp',
        'python-dotenv',
        'aiosqlite',
        'certifi',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - не установлен")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   💡 Установите недостающие пакеты:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_aiogram_version():
    """Проверяет версию aiogram"""
    print("\n🤖 Проверка версии aiogram...")
    
    try:
        import aiogram
        version = aiogram.__version__
        print(f"   Версия aiogram: {version}")
        
        if version.startswith('3.'):
            print("   ✅ Используется aiogram 3.x")
            return True
        else:
            print("   ❌ Обнаружена устаревшая версия aiogram")
            print("   💡 Обновите: pip install aiogram>=3.0.0")
            return False
    except ImportError:
        print("   ❌ aiogram не установлен")
        return False

async def check_telegram_connection():
    """Проверяет подключение к Telegram API"""
    print("\n🌐 Проверка подключения к Telegram API...")
    
    try:
        from aiogram import Bot
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        
        if not bot_token or bot_token == 'YOUR_BOT_TOKEN':
            print("   ❌ Токен не настроен для тестирования")
            return False
        
        bot = Bot(token=bot_token)
        
        try:
            me = await bot.get_me()
            print(f"   ✅ Подключение успешно")
            print(f"   📱 Бот: @{me.username} ({me.first_name})")
            print(f"   🆔 ID: {me.id}")
            await bot.session.close()
            return True
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            await bot.session.close()
            return False
    except ImportError as e:
        print(f"   ❌ Ошибка импорта: {e}")
        return False

def check_directories():
    """Проверяет необходимые директории"""
    print("\n📂 Проверка директорий...")
    
    directories = ['data', 'logs', 'exports']
    
    for directory in directories:
        if Path(directory).exists():
            print(f"   ✅ {directory}/")
        else:
            print(f"   ❌ {directory}/ - не найдена")
            try:
                Path(directory).mkdir(exist_ok=True)
                print(f"   📁 {directory}/ создана")
            except Exception as e:
                print(f"   ❌ Не удалось создать {directory}/: {e}")
    
    return True

def print_recommendations():
    """Выводит рекомендации по настройке"""
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("   1. Создайте бота у @BotFather в Telegram")
    print("   2. Получите свой ID у @userinfobot в Telegram")
    print("   3. Настройте .env файл с правильными значениями")
    print("   4. Установите все зависимости: pip install -r requirements.txt")
    print("   5. Запустите бота: python3 main.py")
    print()

async def main():
    """Основная функция диагностики"""
    print_header()
    
    all_checks = [
        ("Python версия", check_python_version()),
        ("Файл .env", check_env_file()),
        ("Переменные окружения", check_env_variables()),
        ("Зависимости", check_dependencies()),
        ("Версия aiogram", check_aiogram_version()),
        ("Директории", check_directories()),
    ]
    
    # Проверка подключения к Telegram API
    connection_check = await check_telegram_connection()
    all_checks.append(("Подключение к API", connection_check))
    
    # Подсчет результатов
    passed = sum(1 for name, result in all_checks if result)
    total = len(all_checks)
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ: {passed}/{total}")
    print("=" * 50)
    
    if passed == total:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Бот готов к запуску")
        print("🚀 Запустите: python3 main.py")
    else:
        print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print("🔧 Исправьте ошибки выше")
        print_recommendations()
    
    print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Диагностика прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)