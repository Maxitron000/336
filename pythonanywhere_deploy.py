#!/usr/bin/env python3
"""
🌐 Автоматическое развёртывание бота на PythonAnywhere
"""

import os
import sys
import subprocess
import json

def print_header():
    """Заголовок"""
    print("=" * 60)
    print("🌐 РАЗВЁРТЫВАНИЕ НА PYTHONANYWHERE")
    print("=" * 60)

def detect_pythonanywhere():
    """Определение PythonAnywhere"""
    indicators = [
        '/home/' in os.getcwd(),
        'pythonanywhere' in os.getcwd().lower(),
        os.path.exists('/var/log/pythonanywhere.log'),
        'PYTHONANYWHERE_SITE' in os.environ
    ]
    return any(indicators)

def get_username():
    """Получение имени пользователя PythonAnywhere"""
    try:
        # Пытаемся получить из пути
        cwd = os.getcwd()
        if '/home/' in cwd:
            parts = cwd.split('/')
            for i, part in enumerate(parts):
                if part == 'home' and i + 1 < len(parts):
                    return parts[i + 1]
        
        # Пытаемся получить из переменных окружения
        return os.environ.get('USER', 'yourusername')
        
    except:
        return 'yourusername'

def create_task_command(username):
    """Создание команды для Scheduled Task"""
    home_path = f"/home/{username}"
    project_path = f"{home_path}/telegram_bot"
    
    # Команда для запуска
    command = f"{project_path}/venv_bot/bin/python {project_path}/run_bot.py"
    
    return command

def create_bash_script(username):
    """Создание bash скрипта для запуска"""
    script_content = f"""#!/bin/bash
# Автоматический запуск бота на PythonAnywhere

cd /home/{username}/telegram_bot
source venv_bot/bin/activate

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден! Запустите setup.py"
    exit 1
fi

# Запускаем бота
python run_bot.py
"""
    
    with open('start_pa.sh', 'w') as f:
        f.write(script_content)
    
    # Делаем исполняемым
    os.chmod('start_pa.sh', 0o755)
    
    print("✅ Создан start_pa.sh")
    return f"/home/{username}/telegram_bot/start_pa.sh"

def create_scheduled_task_info(username):
    """Создание информации о Scheduled Task"""
    command = create_task_command(username)
    bash_script = create_bash_script(username)
    
    info = {
        "task_type": "hourly",
        "command": command,
        "bash_script": bash_script,
        "description": "Telegram Bot Auto-restart",
        "instructions": [
            "1. Откройте PythonAnywhere Dashboard",
            "2. Перейдите в 'Tasks' → 'Scheduled'",
            "3. Нажмите 'Create a scheduled task'",
            "4. Заполните:",
            f"   Command: {command}",
            "   Hour: * (каждый час)",
            "   Minute: 0",
            f"   Description: Telegram Bot Auto-restart",
            "5. Сохраните задачу"
        ]
    }
    
    return info

def check_environment():
    """Проверка окружения PythonAnywhere"""
    print("\n🔍 Проверка окружения PythonAnywhere...")
    
    checks = [
        ("Python 3.10+", sys.version_info >= (3, 10)),
        ("Виртуальное окружение", 'venv_bot' in os.getcwd() or os.path.exists('venv_bot')),
        ("Файл .env", os.path.exists('.env')),
        ("Зависимости", os.path.exists('requirements.txt')),
        ("База данных", os.path.exists('data') or os.path.exists('bot_database.db'))
    ]
    
    all_ok = True
    for name, status in checks:
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {name}")
        if not status:
            all_ok = False
    
    return all_ok

def create_cron_alternative():
    """Создание альтернативы cron для бесплатного аккаунта"""
    script_content = """#!/usr/bin/env python3
# Альтернатива cron для бесплатного аккаунта PythonAnywhere
import time
import subprocess
import sys
import os
from datetime import datetime

def run_hourly_task():
    try:
        print(f"🔄 Hourly restart: {datetime.now()}")
        subprocess.run([sys.executable, "run_bot.py"], timeout=3500)  # 58 минут
    except subprocess.TimeoutExpired:
        print("⏰ Timeout reached, restarting...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        run_hourly_task()
        time.sleep(60)  # 1 минута пауза перед следующим запуском
"""
    
    with open('cron_alternative.py', 'w') as f:
        f.write(script_content)
    
    print("✅ Создан cron_alternative.py (для бесплатного аккаунта)")

def print_deployment_instructions(username, task_info):
    """Вывод инструкций по развёртыванию"""
    print("\n" + "=" * 60)
    print("📋 ИНСТРУКЦИИ ПО РАЗВЁРТЫВАНИЮ")
    print("=" * 60)
    
    print("\n🚀 1. АВТОМАТИЧЕСКИЙ ПЕРЕЗАПУСК (24/7):")
    print("\nВариант A - Scheduled Task (рекомендуется для 24/7):")
    for instruction in task_info["instructions"]:
        print(f"  {instruction}")
    
    print(f"\nВариант B - Bash скрипт:")
    print(f"  Команда: {task_info['bash_script']}")
    
    print(f"\nВариант C - Новый 24/7 раннер (оптимальный):")
    print(f"  python pythonanywhere_24_7.py  # Простая настройка")
    print(f"  python pa_24_7_runner.py       # Оптимизированный запуск")
    
    print("\n📊 2. МОНИТОРИНГ 24/7:")
    print("  - Логи 24/7: tail -f logs/bot_24_7.log")
    print("  - Основные логи: tail -f logs/bot.log")
    print("  - Scheduled Task: tail -f logs/scheduled_task.log")
    print("  - Мониторинг: python auto_monitor.py")
    print("  - Статус: ps aux | grep pa_24_7_runner")
    print("  - Ресурсы: top -p $(pgrep -f pa_24_7_runner)")
    
    print("\n🔧 3. УПРАВЛЕНИЕ 24/7:")
    print("  - Быстрая настройка: python pythonanywhere_24_7.py")
    print("  - Запуск 24/7: python pa_24_7_runner.py")
    print("  - Запуск через скрипт: ./start_pa_24_7.sh")
    print("  - Остановка: pkill -f pa_24_7_runner")
    print("  - Статус: ps aux | grep pa_24_7")
    
    print("\n📂 4. ФАЙЛЫ:")
    print("  - Конфигурация: .env")
    print("  - База данных: data/bot_database.db")
    print("  - Логи 24/7: logs/bot_24_7.log")
    print("  - Логи Scheduled Task: logs/scheduled_task.log")
    print("  - Экспорт: exports/")
    print("  - Гид по установке: INSTALLATION_GUIDE.md")
    
    print("\n⚡ 5. ОСОБЕННОСТИ 24/7:")
    print("  🔄 Автоперезапуск каждые 55 минут")
    print("  📊 Отчеты о здоровье каждые 6 часов")
    print("  🚨 Мгновенные уведомления об ошибках")
    print("  💾 Автоматическое управление памятью")

def main():
    """Главная функция"""
    print_header()
    
    # Проверяем PythonAnywhere
    if not detect_pythonanywhere():
        print("⚠️ Не обнаружена среда PythonAnywhere")
        print("Этот скрипт оптимизирован для PythonAnywhere")
        if input("Продолжить? (y/N): ").lower() != 'y':
            return
    
    # Получаем имя пользователя
    username = get_username()
    print(f"👤 Пользователь: {username}")
    
    # Проверяем окружение
    if not check_environment():
        print("\n❌ Есть проблемы с окружением!")
        print("🔧 Запустите сначала: python setup.py")
        return
    
    # Создаём файлы развёртывания
    print("\n📁 Создание файлов развёртывания...")
    task_info = create_scheduled_task_info(username)
    create_cron_alternative()
    
    # Выводим инструкции
    print_deployment_instructions(username, task_info)
    
    print("\n" + "=" * 60)
    print("🎉 РАЗВЁРТЫВАНИЕ ПОДГОТОВЛЕНО!")
    print("=" * 60)
    print("\n✅ Все файлы созданы")
    print("📋 Следуйте инструкциям выше для настройки")
    print("🚀 После настройки бот будет работать автоматически!")
    print()
    print("💡 РЕКОМЕНДАЦИЯ:")
    print("   Для простой настройки 24/7 запустите:")
    print("   python pythonanywhere_24_7.py")
    print()
    print("   Требуется только токен бота и ваш Telegram ID!")

if __name__ == "__main__":
    main()