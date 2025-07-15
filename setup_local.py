#!/usr/bin/env python3
"""
🚀 Скрипт развертывания Telegram бота для локальной среды
Автоматическая настройка окружения с доступным Python
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
            if result.stdout.strip():
                print(f"Вывод: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Ошибка: {description}")
            if result.stderr.strip():
                print(f"Вывод: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Исключение при выполнении команды: {e}")
        return False

def setup_environment():
    """Настройка окружения"""
    print("🐍 Настройка виртуального окружения...")
    
    # Проверяем версию Python
    result = subprocess.run("python3 --version", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"📋 Найденная версия Python: {result.stdout.strip()}")
    
    # Создаем виртуальное окружение
    if not run_command("python3 -m venv venv_bot", "Создание виртуального окружения"):
        print("❌ Не удалось создать виртуальное окружение")
        return False
    
    # Активируем окружение и обновляем pip
    if not run_command(". venv_bot/bin/activate && pip install --upgrade pip", "Обновление pip"):
        return False
    
    # Устанавливаем зависимости
    if not run_command(". venv_bot/bin/activate && pip install -r requirements.txt", "Установка зависимостей"):
        return False
    
    return True

def create_directories():
    """Создание необходимых директорий"""
    print("📁 Создание директорий...")
    
    directories = ['logs', 'data', 'exports', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Создана директория: {directory}")

def check_env_file():
    """Проверка файла .env"""
    print("🔍 Проверка файла .env...")
    
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        return False
    
    # Проверяем наличие обязательных переменных
    with open('.env', 'r') as f:
        content = f.read()
        
    required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
    missing_vars = []
    
    for var in required_vars:
        if f"{var}=YOUR_" in content or f"{var}=" not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Не настроены переменные: {', '.join(missing_vars)}")
        print("📝 Отредактируйте файл .env и укажите:")
        print("   - BOT_TOKEN (получить у @BotFather)")
        print("   - ADMIN_IDS (получить у @userinfobot)")
        return False
    
    print("✅ Файл .env настроен корректно")
    return True

def create_database():
    """Создание базы данных"""
    print("🗄️ Создание базы данных...")
    
    if not run_command(". venv_bot/bin/activate && python create_database.py", "Инициализация базы данных"):
        return False
    
    return True

def create_start_script():
    """Создание скрипта запуска для локальной среды"""
    print("📜 Создание скрипта запуска...")
    
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
    exit 1
fi

# Создаем папки для логов если их нет
mkdir -p logs
mkdir -p data

# Проверяем базу данных
echo "🗄️ Проверка базы данных..."
python check_database.py

# Запускаем бота
echo "🤖 Запуск бота..."
python main.py
'''
    
    with open('start_bot.sh', 'w') as f:
        f.write(script_content)
    
    # Делаем скрипт исполняемым
    os.chmod('start_bot.sh', 0o755)
    print("✅ Создан скрипт запуска: start_bot.sh")

def main():
    """Основная функция настройки"""
    print("🚀 Настройка Telegram бота для локальной среды")
    print("=" * 50)
    
    # Проверяем Python
    result = subprocess.run("python3 --version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Python3 не найден! Установите Python 3.7+")
        return False
    
    # Создаем директории
    create_directories()
    
    # Настраиваем окружение
    if not setup_environment():
        print("❌ Ошибка настройки окружения")
        return False
    
    # Создаем базу данных
    if not create_database():
        print("❌ Ошибка создания базы данных")
        return False
    
    # Создаем скрипт запуска
    create_start_script()
    
    print("=" * 50)
    print("🎉 Настройка завершена!")
    print()
    print("📋 Следующие шаги:")
    print("1. Настройте файл .env (укажите BOT_TOKEN и ADMIN_IDS)")
    print("2. Запустите бота командой: ./start_bot.sh")
    print()
    print("🔧 Получить токен бота: @BotFather")
    print("🆔 Получить свой ID: @userinfobot")
    
    return True

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)