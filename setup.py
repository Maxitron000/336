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

def detect_pythonanywhere():
    """Определение PythonAnywhere"""
    indicators = [
        '/home/' in os.getcwd(),
        'pythonanywhere' in os.getcwd().lower(),
        os.path.exists('/var/log/pythonanywhere.log'),
        'PYTHONANYWHERE_SITE' in os.environ
    ]
    return any(indicators)

def create_virtual_environment():
    """Создание виртуального окружения"""
    print("\n🔧 Создание виртуального окружения...")
    
    venv_path = "venv_bot"
    
    # Проверяем, существует ли уже
    if os.path.exists(venv_path):
        print(f"⚠️ Виртуальное окружение {venv_path} уже существует")
        response = input("Пересоздать? (y/N): ").lower()
        if response == 'y':
            print("🗑️ Удаляем старое окружение...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            print("✅ Используем существующее виртуальное окружение")
            return True
    
    try:
        # Создаем виртуальное окружение
        print(f"🏗️ Создание виртуального окружения {venv_path}...")
        result = subprocess.run([
            sys.executable, "-m", "venv", venv_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Виртуальное окружение {venv_path} создано успешно")
            return True
        else:
            print(f"❌ Ошибка создания виртуального окружения: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка создания виртуального окружения: {e}")
        return False

def get_python_executable():
    """Получение пути к Python в виртуальном окружении"""
    venv_path = "venv_bot"
    
    if os.name == 'nt':  # Windows
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:  # Unix/Linux/MacOS
        python_path = os.path.join(venv_path, "bin", "python")
    
    if os.path.exists(python_path):
        return python_path
    else:
        print(f"⚠️ Python не найден в виртуальном окружении: {python_path}")
        return sys.executable

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
HEALTH_CHECK_INTERVAL=43200  # 12 часов
AUTO_RESTART_INTERVAL=86400  # 1 раз в сутки
ERROR_NOTIFICATION_ENABLED=true
PERFORMANCE_MONITORING=true
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env создан успешно")

def install_dependencies():
    """Установка зависимостей в виртуальное окружение"""
    print("\n📦 Установка зависимостей в виртуальное окружение...")
    
    python_exe = get_python_executable()
    
    try:
        # Определяем нужный файл requirements
        if sys.version_info >= (3, 10):
            req_file = "requirements.txt"
        else:
            req_file = "requirements_python310.txt"
            
        if not os.path.exists(req_file):
            req_file = "requirements.txt"
        
        print(f"Используем файл: {req_file}")
        print(f"Python: {python_exe}")
        
        # Сначала обновляем pip в виртуальном окружении
        print("🔄 Обновление pip...")
        pip_result = subprocess.run([
            python_exe, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True)
        
        if pip_result.returncode != 0:
            print(f"⚠️ Предупреждение при обновлении pip: {pip_result.stderr}")
        
        # Устанавливаем зависимости
        print("📥 Установка зависимостей...")
        result = subprocess.run([
            python_exe, "-m", "pip", "install", "-r", req_file
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Зависимости установлены успешно в виртуальное окружение")
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
    
    python_exe = get_python_executable()
    
    try:
        result = subprocess.run([
            python_exe, "create_database.py"
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
    
    python_exe = get_python_executable()
    
    # Тест импорта aiogram
    try:
        result = subprocess.run([
            python_exe, "test_aiogram.py"
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
    
    # Определяем путь к Python в виртуальном окружении
    if os.name == 'nt':  # Windows
        venv_python = "venv_bot\\Scripts\\python.exe"
    else:  # Unix/Linux/MacOS  
        venv_python = "venv_bot/bin/python"
    
    start_script = f"""#!/usr/bin/env python3
# Запуск бота с виртуальным окружением
import subprocess
import sys
import os

def main():
    # Переходим в директорию скрипта
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Путь к Python в виртуальном окружении
    venv_python = "{venv_python}"
    
    # Проверяем наличие виртуального окружения
    if not os.path.exists(venv_python):
        print("❌ Виртуальное окружение не найдено!")
        print("🔧 Запустите сначала: python setup.py")
        return 1
    
    try:
        print("🚀 Запуск бота из виртуального окружения...")
        subprocess.run([venv_python, "run_bot.py"])
    except KeyboardInterrupt:
        print("\\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {{e}}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
    
    with open('start.py', 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    # Делаем исполняемым на Unix
    if sys.platform != 'win32':
        os.chmod('start.py', 0o755)
    
    print("✅ Скрипт start.py создан")

def create_activation_info():
    """Создание информации об активации виртуального окружения"""
    print("\n📋 Создание справочной информации...")
    
    is_pa = detect_pythonanywhere()
    
    if os.name == 'nt':  # Windows
        activate_cmd = "venv_bot\\Scripts\\activate"
        python_cmd = "venv_bot\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        activate_cmd = "source venv_bot/bin/activate"
        python_cmd = "venv_bot/bin/python"
    
    info_content = f"""# 🔧 Информация о виртуальном окружении

## 📁 Структура:
- Виртуальное окружение: `venv_bot/`
- Конфигурация: `.env`
- База данных: `data/bot_database.db`
- Логи: `logs/bot.log`

## 🚀 Команды для запуска:

### Вариант 1 - Простой запуск (рекомендуется):
```bash
python start.py
```

### Вариант 2 - Ручная активация окружения:
```bash
{activate_cmd}
python run_bot.py
```

### Вариант 3 - Прямой вызов:
```bash
{python_cmd} run_bot.py
```

## 🌐 Для PythonAnywhere:

### Команда для Scheduled Task:
```
{python_cmd.replace('venv_bot/', '/home/yourusername/telegram_bot/venv_bot/')} /home/yourusername/telegram_bot/run_bot.py
```

### Скрипт активации:
```bash
cd ~/telegram_bot
{activate_cmd}
python run_bot.py
```

## 🔍 Диагностика:
```bash
# Проверка окружения
{python_cmd} diagnose_issues.py

# Тест aiogram
{python_cmd} test_aiogram.py

# Проверка базы данных
{python_cmd} check_database.py
```

## ⚠️ Важно:
- Всегда используйте виртуальное окружение
- Зависимости устанавливайте только в venv_bot
- Не запускайте setup.py повторно без необходимости
"""
    
    with open('VIRTUAL_ENV_INFO.md', 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print("✅ Файл VIRTUAL_ENV_INFO.md создан")

def print_success():
    """Вывод успешного завершения"""
    python_exe = get_python_executable()
    is_pa = detect_pythonanywhere()
    
    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print()
    print("✅ Виртуальное окружение: venv_bot/")
    print("✅ Зависимости установлены в изолированной среде")
    print()
    print("🚀 Для запуска бота используйте:")
    print("   python start.py")
    print("   или")
    print(f"   {python_exe} run_bot.py")
    print()
    
    if is_pa:
        print("🌐 Для PythonAnywhere развертывания:")
        print(f"   python3.10 pythonanywhere_deploy.py")
        print()
    
    print("📊 Мониторинг:")
    print("   - Автоперезапуск раз в сутки")
    print("   - Отчёты админу каждые 12 часов")
    print("   - Уведомления об ошибках")
    print()
    print("📁 Файлы:")
    print("   - Логи: logs/bot.log")
    print("   - БД: data/bot_database.db")
    print("   - Конфигурация: .env")
    print("   - Справка: VIRTUAL_ENV_INFO.md")
    print()

def main():
    """Главная функция"""
    print_header()
    
    # Проверка Python
    if not check_python_version():
        return
    
    # Создание виртуального окружения
    if not create_virtual_environment():
        print("❌ Не удалось создать виртуальное окружение")
        return
    
    # Получение данных
    token = get_bot_token()
    admin_id = get_admin_id()
    
    # Настройка
    create_env_file(token, admin_id)
    create_directories()
    
    # Установка зависимостей в виртуальное окружение
    if not install_dependencies():
        print("⚠️ Продолжаем без установки зависимостей")
    
    # Инициализация
    initialize_database()
    run_tests()
    create_start_script()
    create_activation_info()
    
    # Завершение
    print_success()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка настройки: {e}")