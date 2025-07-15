#!/usr/bin/env python3
"""
🚀 Минимальная установка зависимостей для Telegram бота
Работает с Python 3.13 без pandas
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Выполнение команды с выводом результата"""
    if description:
        print(f"🔧 {description}")
    
    try:
        # Для команд с активацией виртуального окружения используем bash
        if "venv_bot/bin/activate" in command:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, executable="/bin/bash")
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
        if result.returncode == 0:
            print(f"✅ Успешно: {description}")
            return True
        else:
            print(f"❌ Ошибка: {description}")
            if result.stderr.strip():
                print(f"Ошибка: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Исключение при выполнении команды: {e}")
        return False

def main():
    """Основная функция установки"""
    print("🚀 Минимальная установка зависимостей для Telegram бота")
    print("=" * 50)
    
    # Создаем необходимые директории
    directories = ['logs', 'data', 'exports', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Создана директория: {directory}")
    
    # Создаем виртуальное окружение
    print("\n🐍 Создание виртуального окружения...")
    if not run_command("python3 -m venv venv_bot", "Создание виртуального окружения"):
        print("❌ Не удалось создать виртуальное окружение")
        return False
    
    # Обновляем pip
    print("\n📦 Обновление pip...")
    if not run_command(". venv_bot/bin/activate && pip install --upgrade pip", "Обновление pip"):
        return False
    
    # Устанавливаем минимальные зависимости
    print("\n📥 Установка минимальных зависимостей...")
    if not run_command(". venv_bot/bin/activate && pip install -r requirements_minimal.txt", "Установка зависимостей"):
        return False
    
    # Создаем скрипт запуска
    print("\n📜 Создание скрипта запуска...")
    script_content = '''#!/bin/bash
# Скрипт запуска бота в локальной среде

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
. venv_bot/bin/activate

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Настройте файл .env перед запуском"
    echo "   BOT_TOKEN=ваш_токен_бота"
    echo "   ADMIN_IDS=ваш_telegram_id"
    exit 1
fi

# Создаем папки для логов если их нет
mkdir -p logs
mkdir -p data

# Проверяем базу данных
echo "🗄️ Проверка базы данных..."
if [ -f check_database.py ]; then
    python check_database.py
else
    echo "⚠️  Файл check_database.py не найден, пропускаем проверку"
fi

# Запускаем бота
echo "🤖 Запуск бота..."
python main.py
'''
    
    with open('start_bot.sh', 'w') as f:
        f.write(script_content)
    
    # Делаем скрипт исполняемым
    os.chmod('start_bot.sh', 0o755)
    print("✅ Создан скрипт запуска: start_bot.sh")
    
    print("\n" + "=" * 50)
    print("🎉 Минимальная установка завершена!")
    print()
    print("📋 Следующие шаги:")
    print("1. Настройте файл .env:")
    print("   BOT_TOKEN=ваш_токен_от_BotFather")
    print("   ADMIN_IDS=ваш_telegram_id")
    print("2. Запустите бота: ./start_bot.sh")
    print()
    print("🔧 Получить токен бота: @BotFather")
    print("🆔 Получить свой ID: @userinfobot")
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)