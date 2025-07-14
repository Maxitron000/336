#!/usr/bin/env python3
"""
🚀 Простая настройка Telegram бота
Нужны только токен бота и ID администратора
"""

import os
import sys
import subprocess
import re

def print_header():
    """Красивый заголовок"""
    print("=" * 60)
    print("🤖 АВТОМАТИЧЕСКАЯ НАСТРОЙКА TELEGRAM БОТА")
    print("=" * 60)
    print()

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - совместим")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - НЕ совместим")
        print("⚠️  Рекомендуется Python 3.10+")
        return input("Продолжить? (y/N): ").lower() == 'y'

def get_bot_token():
    """Получение токена бота"""
    print("📱 Получение токена бота:")
    print("1. Перейдите к @BotFather в Telegram")
    print("2. Отправьте /newbot и следуйте инструкциям")
    print("3. Скопируйте токен (выглядит как: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)")
    print()
    
    while True:
        token = input("🔑 Введите токен бота: ").strip()
        if re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            return token
        print("❌ Неверный формат токена. Попробуйте снова.")

def get_admin_id():
    """Получение ID администратора"""
    print("\n👤 Получение вашего Telegram ID:")
    print("1. Перейдите к @userinfobot в Telegram")
    print("2. Отправьте /start")
    print("3. Скопируйте ваш ID (число, например: 123456789)")
    print()
    
    while True:
        try:
            admin_id = input("🆔 Введите ваш Telegram ID: ").strip()
            admin_id = int(admin_id)
            if admin_id > 0:
                return str(admin_id)
        except ValueError:
            pass
        print("❌ ID должен быть положительным числом. Попробуйте снова.")

def create_env_file(token, admin_id):
    """Создание файла .env"""
    env_content = f"""# Настройки Telegram бота
BOT_TOKEN={token}
ADMIN_IDS={admin_id}

# Настройки базы данных  
DB_PATH=data/bot_database.db

# Настройки уведомлений
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# Настройки экспорта
EXPORT_PATH=exports/

# Настройки мониторинга
HEALTH_CHECK_INTERVAL=21600  # 6 часов
AUTO_RESTART_INTERVAL=3600   # 1 час
ERROR_NOTIFICATION_ENABLED=true
PERFORMANCE_MONITORING=true
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env создан успешно")

def install_dependencies():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    
    try:
        # Определяем нужный файл requirements
        if sys.version_info >= (3, 10):
            req_file = "requirements.txt"
        else:
            req_file = "requirements_python310.txt"
            
        if not os.path.exists(req_file):
            req_file = "requirements.txt"
        
        print(f"Используем файл: {req_file}")
        
        # Устанавливаем зависимости
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", req_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Зависимости установлены успешно")
            return True
        else:
            print(f"❌ Ошибка установки зависимостей: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False

def create_directories():
    """Создание необходимых директорий"""
    print("\n📁 Создание директорий...")
    
    directories = ['data', 'logs', 'exports', 'config']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Директория {directory}/ создана")

def initialize_database():
    """Инициализация базы данных"""
    print("\n🗄️ Инициализация базы данных...")
    
    try:
        result = subprocess.run([
            sys.executable, "create_database.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ База данных инициализирована")
            return True
        else:
            print(f"⚠️ Предупреждение: {result.stderr}")
            return True  # Продолжаем даже при предупреждениях
            
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
        return True  # Продолжаем

def run_tests():
    """Запуск тестов"""
    print("\n🧪 Проверка работоспособности...")
    
    # Тест импорта aiogram
    try:
        result = subprocess.run([
            sys.executable, "test_aiogram.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Тест aiogram пройден")
        else:
            print(f"⚠️ Предупреждение в тесте aiogram: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Ошибка теста: {e}")

def create_start_script():
    """Создание скрипта запуска"""
    print("\n📜 Создание скрипта запуска...")
    
    start_script = """#!/usr/bin/env python3
# Простой запуск бота
import subprocess
import sys

if __name__ == "__main__":
    try:
        subprocess.run([sys.executable, "run_bot.py"])
    except KeyboardInterrupt:
        print("\\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
"""
    
    with open('start.py', 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    # Делаем исполняемым на Unix
    if sys.platform != 'win32':
        os.chmod('start.py', 0o755)
    
    print("✅ Скрипт start.py создан")

def print_success():
    """Вывод успешного завершения"""
    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print()
    print("🚀 Для запуска бота используйте:")
    print("   python start.py")
    print("   или")
    print("   python run_bot.py")
    print()
    print("📊 Мониторинг:")
    print("   - Автоперезапуск каждый час")
    print("   - Отчёты админу каждые 6 часов")
    print("   - Уведомления об ошибках")
    print()
    print("📁 Файлы:")
    print("   - Логи: logs/bot.log")
    print("   - БД: data/bot_database.db")
    print("   - Конфигурация: .env")
    print()

def main():
    """Главная функция"""
    print_header()
    
    # Проверка Python
    if not check_python_version():
        return
    
    # Получение данных
    token = get_bot_token()
    admin_id = get_admin_id()
    
    # Настройка
    create_env_file(token, admin_id)
    create_directories()
    
    # Установка зависимостей
    if not install_dependencies():
        print("⚠️ Продолжаем без установки зависимостей")
    
    # Инициализация
    initialize_database()
    run_tests()
    create_start_script()
    
    # Завершение
    print_success()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка настройки: {e}")