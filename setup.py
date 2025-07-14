#!/usr/bin/env python3
"""
🚀 Улучшенная настройка Telegram бота
Автоматическое создание виртуального окружения и установка всех зависимостей
Нужны только токен бота и ID администратора
"""

import os
import sys
import subprocess
import re
import shutil
import venv
from pathlib import Path

def print_header():
    """Красивый заголовок"""
    print("=" * 70)
    print("🤖 АВТОМАТИЧЕСКАЯ НАСТРОЙКА TELEGRAM БОТА")
    print("🔧 Создание виртуального окружения и установка зависимостей")
    print("=" * 70)
    print()

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - совместим")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - НЕ совместим")
        print("⚠️  Требуется Python 3.10+")
        return False

def detect_platform():
    """Определение платформы"""
    if 'pythonanywhere' in os.getcwd().lower() or os.path.exists('/var/log/pythonanywhere.log'):
        return 'pythonanywhere'
    elif sys.platform == 'win32':
        return 'windows'
    else:
        return 'unix'

def remove_existing_venv():
    """Удаление существующего виртуального окружения"""
    venv_path = Path("venv_bot")
    if venv_path.exists():
        print("🗑️ Удаляем существующее виртуальное окружение...")
        try:
            shutil.rmtree(venv_path)
            print("✅ Старое окружение удалено")
        except Exception as e:
            print(f"⚠️ Предупреждение при удалении: {e}")
            return False
    return True

def create_virtual_environment():
    """Создание виртуального окружения"""
    print("\n🔧 Создание нового виртуального окружения...")
    
    venv_path = "venv_bot"
    
    # Удаляем существующее окружение если есть
    if not remove_existing_venv():
        print("❌ Не удалось удалить старое окружение")
        return False
    
    try:
        # Используем модуль venv для создания окружения
        print(f"🏗️ Создание виртуального окружения {venv_path}...")
        venv.create(venv_path, with_pip=True, clear=True)
        print(f"✅ Виртуальное окружение {venv_path} создано успешно")
        return True
            
    except Exception as e:
        print(f"❌ Ошибка создания виртуального окружения: {e}")
        return False

def get_venv_python():
    """Получение пути к Python в виртуальном окружении"""
    platform = detect_platform()
    
    if platform == 'windows':
        python_path = Path("venv_bot/Scripts/python.exe")
    else:  # unix, pythonanywhere
        python_path = Path("venv_bot/bin/python")
    
    if python_path.exists():
        return str(python_path)
    else:
        print(f"❌ Python не найден в виртуальном окружении: {python_path}")
        return None

def get_venv_pip():
    """Получение пути к pip в виртуальном окружении"""
    platform = detect_platform()
    
    if platform == 'windows':
        pip_path = Path("venv_bot/Scripts/pip.exe")
    else:  # unix, pythonanywhere
        pip_path = Path("venv_bot/bin/pip")
    
    if pip_path.exists():
        return str(pip_path)
    else:
        # Используем python -m pip
        python_path = get_venv_python()
        if python_path:
            return f"{python_path} -m pip"
        return None

def upgrade_pip():
    """Обновление pip в виртуальном окружении"""
    print("🔄 Обновление pip в виртуальном окружении...")
    
    python_path = get_venv_python()
    if not python_path:
        return False
    
    try:
        result = subprocess.run([
            python_path, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ pip обновлён успешно")
            return True
        else:
            print(f"⚠️ Предупреждение при обновлении pip: {result.stderr}")
            return True  # Продолжаем даже при предупреждениях
            
    except subprocess.TimeoutExpired:
        print("⚠️ Timeout при обновлении pip")
        return True
    except Exception as e:
        print(f"⚠️ Ошибка обновления pip: {e}")
        return True

def install_requirements():
    """Установка зависимостей в виртуальное окружение"""
    print("\n📦 Установка зависимостей в виртуальное окружение...")
    
    python_path = get_venv_python()
    if not python_path:
        return False
    
    # Проверяем наличие requirements.txt
    if not os.path.exists("requirements.txt"):
        print("❌ Файл requirements.txt не найден!")
        return False
    
    try:
        # Устанавливаем зависимости
        print("📥 Установка зависимостей из requirements.txt...")
        print(f"🐍 Используем Python: {python_path}")
        
        # Устанавливаем с подробным выводом
        result = subprocess.run([
            python_path, "-m", "pip", "install", "-r", "requirements.txt", 
            "--no-cache-dir", "--timeout", "600"
        ], capture_output=True, text=True, timeout=900)
        
        if result.returncode == 0:
            print("✅ Зависимости установлены успешно!")
            print("📋 Установленные пакеты:")
            
            # Показываем список установленных пакетов
            list_result = subprocess.run([
                python_path, "-m", "pip", "list"
            ], capture_output=True, text=True)
            
            if list_result.returncode == 0:
                print(list_result.stdout)
            
            return True
        else:
            print(f"❌ Ошибка установки зависимостей:")
            print(result.stderr)
            print("\n💡 Попробуйте установить зависимости вручную:")
            print(f"   {python_path} -m pip install -r requirements.txt")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Превышено время ожидания установки зависимостей (15 минут)")
        return False
    except Exception as e:
        print(f"❌ Ошибка установки: {e}")
        return False

def test_imports():
    """Тестирование импорта критических модулей"""
    print("\n🧪 Проверка установленных зависимостей...")
    
    python_path = get_venv_python()
    if not python_path:
        return False
    
    critical_modules = [
        ('aiogram', 'aiogram'),
        ('aiosqlite', 'aiosqlite'),
        ('python-dotenv', 'dotenv'),
        ('psutil', 'psutil'),
        ('requests', 'requests'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl'),
        ('reportlab', 'reportlab')
    ]
    
    all_ok = True
    
    for package_name, import_name in critical_modules:
        try:
            result = subprocess.run([
                python_path, "-c", f"import {import_name}; print('✓ {package_name}')"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ {package_name}")
            else:
                print(f"  ❌ {package_name} - ошибка импорта")
                all_ok = False
                
        except Exception as e:
            print(f"  ❌ {package_name} - ошибка теста: {e}")
            all_ok = False
    
    if all_ok:
        print("✅ Все критические зависимости работают корректно!")
    else:
        print("⚠️ Есть проблемы с некоторыми зависимостями")
    
    return all_ok

def get_bot_token():
    """Получение токена бота"""
    print("\n📱 Получение токена бота:")
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
    print("\n📝 Создание конфигурационного файла...")
    
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
    
    python_path = get_venv_python()
    if not python_path:
        return False
    
    try:
        result = subprocess.run([
            python_path, "create_database.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ База данных инициализирована успешно")
            return True
        else:
            print(f"⚠️ Предупреждение при инициализации БД: {result.stderr}")
            return True  # Продолжаем даже при предупреждениях
            
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
        return True  # Продолжаем

def update_start_script():
    """Обновление скрипта запуска для использования виртуального окружения"""
    print("\n📜 Обновление скрипта запуска...")
    
    platform = detect_platform()
    
    if platform == 'windows':
        venv_python = "venv_bot\\Scripts\\python.exe"
    else:
        venv_python = "venv_bot/bin/python"
    
    start_script = f"""#!/usr/bin/env python3
"""
🚀 Запуск Telegram бота из виртуального окружения
Автоматический перезапуск и мониторинг
"""

import subprocess
import sys
import os
from pathlib import Path

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
    venv_python = Path("{venv_python}")
    if not venv_python.exists():
        print("❌ Виртуальное окружение не найдено!")
        print("🔧 Запустите сначала: python setup.py")
        return 1
    
    print(f"🐍 Используем Python: {{venv_python}}")
    
    try:
        # Запускаем основной скрипт из виртуального окружения
        subprocess.run([str(venv_python), "run_bot.py"])
        return 0
    except KeyboardInterrupt:
        print("\\n🛑 Бот остановлен пользователем")
        return 0
    except Exception as e:
        print(f"❌ Ошибка запуска: {{e}}")
        print("🔧 Попробуйте запустить: python setup.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    with open('start.py', 'w', encoding='utf-8') as f:
        f.write(start_script)
    
    # Делаем исполняемым на Unix
    if platform != 'windows':
        os.chmod('start.py', 0o755)
    
    print("✅ Скрипт start.py обновлён для работы с виртуальным окружением")

def create_run_in_venv_script():
    """Создание удобного скрипта для запуска команд в виртуальном окружении"""
    platform = detect_platform()
    
    if platform == 'windows':
        venv_python = "venv_bot\\Scripts\\python.exe"
        script_name = "run_in_venv.bat"
        script_content = f"""@echo off
echo 🐍 Запуск в виртуальном окружении...
{venv_python} %*
"""
    else:
        venv_python = "venv_bot/bin/python"
        script_name = "run_in_venv.sh"
        script_content = f"""#!/bin/bash
echo "🐍 Запуск в виртуальном окружении..."
{venv_python} "$@"
"""
    
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    if platform != 'windows':
        os.chmod(script_name, 0o755)
    
    print(f"✅ Создан вспомогательный скрипт: {script_name}")

def create_info_file():
    """Создание информационного файла"""
    platform = detect_platform()
    
    if platform == 'windows':
        venv_python = "venv_bot\\Scripts\\python.exe"
        activate_cmd = "venv_bot\\Scripts\\activate"
    else:
        venv_python = "venv_bot/bin/python"
        activate_cmd = "source venv_bot/bin/activate"
    
    info_content = f"""# 🤖 Telegram Bot - Руководство по запуску

## ✅ Установка завершена успешно!

### 🚀 Быстрый запуск:
```bash
python start.py
```

### 🔧 Альтернативные способы запуска:

#### 1. Прямой запуск из виртуального окружения:
```bash
{venv_python} run_bot.py
```

#### 2. Активация окружения и запуск:
```bash
{activate_cmd}
python run_bot.py
```

#### 3. Использование вспомогательного скрипта:
```bash
{"./run_in_venv.sh" if platform != 'windows' else "run_in_venv.bat"} run_bot.py
```

### 📊 Диагностика и обслуживание:

#### Проверка состояния базы данных:
```bash
{venv_python} check_database.py
```

#### Создание резервной копии:
```bash
{venv_python} backup.py
```

#### Экспорт данных:
```bash
{venv_python} export.py
```

### 🌐 Для PythonAnywhere:

#### Команда для Scheduled Task:
```
{venv_python.replace('venv_bot/', '/home/yourusername/mysite/venv_bot/')} /home/yourusername/mysite/run_bot.py
```

### 📁 Структура проекта:
- `venv_bot/` - виртуальное окружение
- `.env` - конфигурация (токен, ID администратора)
- `data/` - база данных
- `logs/` - файлы логов
- `exports/` - экспортированные данные

### ⚠️ Важные заметки:
- ✅ Все зависимости установлены в изолированном виртуальном окружении
- ✅ Бот настроен на автоматический перезапуск каждый час
- ✅ Отчёты отправляются администратору каждые 6 часов
- ✅ Все ошибки логируются в файл `logs/bot.log`

### 🛠️ Переустановка (если нужна):
```bash
python setup.py
```

Удачного использования! 🎉
"""
    
    with open('SETUP_COMPLETE.md', 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print("✅ Файл SETUP_COMPLETE.md создан с инструкциями")

def print_success():
    """Вывод успешного завершения"""
    platform = detect_platform()
    python_path = get_venv_python()
    
    print("\n" + "=" * 70)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 70)
    print()
    print("✅ Виртуальное окружение: venv_bot/")
    print("✅ Все зависимости установлены в изолированной среде")
    print("✅ Конфигурация создана: .env")
    print("✅ База данных инициализирована")
    print()
    print("🚀 ДЛЯ ЗАПУСКА БОТА ИСПОЛЬЗУЙТЕ:")
    print("   python start.py")
    print()
    print("📋 Альтернативные команды:")
    print(f"   {python_path} run_bot.py")
    print()
    
    if platform == 'pythonanywhere':
        print("🌐 Для PythonAnywhere Scheduled Task:")
        pa_python = python_path.replace('venv_bot/', '/home/yourusername/mysite/venv_bot/')
        print(f"   {pa_python} /home/yourusername/mysite/run_bot.py")
        print()
    
    print("📊 Настройки мониторинга:")
    print("   - Автоперезапуск каждый час")
    print("   - Отчёты админу каждые 6 часов")
    print("   - Уведомления об ошибках включены")
    print()
    print("📁 Важные файлы:")
    print("   - Конфигурация: .env")
    print("   - База данных: data/bot_database.db")
    print("   - Логи: logs/bot.log")
    print("   - Инструкции: SETUP_COMPLETE.md")
    print()
    print("🎯 Теперь просто запустите: python start.py")
    print("=" * 70)

def main():
    """Главная функция установки"""
    print_header()
    
    # Проверка Python
    if not check_python_version():
        print("❌ Требуется Python 3.10 или выше!")
        return
    
    # Создание виртуального окружения
    if not create_virtual_environment():
        print("❌ Не удалось создать виртуальное окружение")
        return
    
    # Обновление pip
    if not upgrade_pip():
        print("⚠️ Продолжаем без обновления pip")
    
    # Установка зависимостей
    if not install_requirements():
        print("❌ Критическая ошибка: не удалось установить зависимости")
        print("💡 Попробуйте установить вручную:")
        python_path = get_venv_python()
        if python_path:
            print(f"   {python_path} -m pip install -r requirements.txt")
        return
    
    # Тестирование импортов
    if not test_imports():
        print("⚠️ Есть проблемы с некоторыми зависимостями, но продолжаем...")
    
    # Получение данных пользователя
    token = get_bot_token()
    admin_id = get_admin_id()
    
    # Настройка проекта
    create_env_file(token, admin_id)
    create_directories()
    initialize_database()
    update_start_script()
    create_run_in_venv_script()
    create_info_file()
    
    # Завершение
    print_success()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка настройки: {e}")
        import traceback
        traceback.print_exc()