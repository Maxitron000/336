#!/usr/bin/env python3
"""
🚀 Запуск Telegram бота из виртуального окружения
Автоматический перезапуск и мониторинг
"""

import subprocess
import sys
import os
from pathlib import Path

def detect_platform():
    """Определение платформы"""
    if sys.platform == 'win32':
        return 'windows'
    else:
        return 'unix'

def get_venv_python():
    """Получение пути к Python в виртуальном окружении"""
    platform = detect_platform()
    
    if platform == 'windows':
        python_path = Path("venv_bot/Scripts/python.exe")
    else:
        python_path = Path("venv_bot/bin/python")
    
    return python_path

def main():
    """Запуск бота с автоматическим мониторингом из виртуального окружения"""
    print("🤖 Запуск Telegram бота из виртуального окружения...")
    print("🔄 Автоперезапуск: каждый час")
    print("📊 Отчёты админу: каждые 6 часов")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Запустите сначала: python setup.py")
        return 1
    
    # Проверяем наличие виртуального окружения
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("❌ Виртуальное окружение не найдено!")
        print("🔧 Запустите сначала: python setup.py")
        return 1
    
    print(f"🐍 Используем Python: {venv_python}")
    
    try:
        # Запускаем основной скрипт из виртуального окружения
        subprocess.run([str(venv_python), "run_bot.py"])
        return 0
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
        return 0
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("🔧 Попробуйте запустить: python setup.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())