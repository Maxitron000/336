#!/usr/bin/env python3
"""
🌐 Простая настройка бота для PythonAnywhere (1 Task в сутки)
Требует только токен бота и Telegram ID администратора
Автоматически устанавливает все зависимости в виртуальное окружение
"""

import os
import sys
import re
import subprocess
import platform
from datetime import datetime

def print_banner():
    """Красивый баннер"""
    print("=" * 60)
    print("🤖 PYTHONANYWHERE BOT SETUP (1 Task/Day)")
    print("🔄 Работа 24/7 с внутренними перезапусками")
    print("📊 Отчеты админу каждые 6 часов")
    print("🚨 Уведомления об ошибках")
    print("🐍 Автоустановка зависимостей в venv")
    print("=" * 60)
    print()

def check_python_version():
    """Проверка версии Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - совместим")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - НЕ совместим")
        print("⚠️  Требуется Python 3.8+")
        return False

def detect_pythonanywhere():
    """Определение среды PythonAnywhere"""
    indicators = [
        '/home/' in os.getcwd(),
        'pythonanywhere' in os.getcwd().lower(),
        os.path.exists('/var/log/pythonanywhere.log'),
        'PYTHONANYWHERE_SITE' in os.environ
    ]
    is_pa = any(indicators)
    
    if is_pa:
        print("✅ Обнаружена среда PythonAnywhere")
    else:
        print("⚠️ PythonAnywhere не обнаружен, но продолжаем...")
    
    return is_pa

def get_username():
    """Получение имени пользователя"""
    try:
        cwd = os.getcwd()
        if '/home/' in cwd:
            parts = cwd.split('/')
            for i, part in enumerate(parts):
                if part == 'home' and i + 1 < len(parts):
                    return parts[i + 1]
        return os.environ.get('USER', 'username')
    except:
        return 'username'

def run_command(cmd, description=""):
    """Выполнение команды с красивым выводом"""
    if description:
        print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"✅ {description} - успешно")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка:")
        if e.stdout:
            print(f"   Вывод: {e.stdout.strip()}")
        if e.stderr:
            print(f"   Ошибка: {e.stderr.strip()}")
        return False, str(e)

def create_virtual_environment():
    """Создание виртуального окружения"""
    print("\n🐍 Работа с виртуальным окружением...")
    
    venv_path = "venv_bot"
    
    # Проверяем, существует ли уже
    if os.path.exists(venv_path):
        print(f"⚠️ Виртуальное окружение {venv_path} уже существует")
        response = input("Пересоздать? (y/N): ").lower()
        if response == 'y':
            print("🗑️ Удаляем старое окружение...")
            run_command(f"rm -rf {venv_path}", "Удаление старого окружения")
        else:
            print("✅ Используем существующее окружение")
            return True
    
    # Создаем новое окружение
    success, output = run_command(f"python3 -m venv {venv_path}", "Создание виртуального окружения")
    if not success:
        print("❌ Не удалось создать виртуальное окружение")
        return False
    
    print("✅ Виртуальное окружение создано")
    return True

def install_requirements():
    """Установка зависимостей"""
    print("\n📦 Установка зависимостей...")
    
    if not os.path.exists("requirements.txt"):
        print("❌ Файл requirements.txt не найден!")
        return False
    
    # Обновляем pip
    pip_cmd = "venv_bot/bin/pip"
    success, _ = run_command(f"{pip_cmd} install --upgrade pip", "Обновление pip")
    if not success:
        print("⚠️ Не удалось обновить pip, но продолжаем...")
    
    # Устанавливаем зависимости
    success, output = run_command(f"{pip_cmd} install -r requirements.txt", "Установка зависимостей из requirements.txt")
    if not success:
        print("❌ Не удалось установить зависимости")
        return False
    
    print("✅ Все зависимости установлены")
    
    # Проверяем ключевые пакеты
    print("\n🔍 Проверка установленных пакетов...")
    key_packages = ['aiogram', 'python-dotenv', 'aiosqlite']
    
    for package in key_packages:
        success, _ = run_command(f"{pip_cmd} show {package}", f"Проверка {package}")
        if success:
            print(f"   ✅ {package}")
        else:
            print(f"   ❌ {package} - не установлен")
    
    return True

def get_input(prompt, validator=None, description=""):
    """Простой ввод с валидацией"""
    if description:
        print(f"💡 {description}")
    
    while True:
        value = input(f"🔑 {prompt}: ").strip()
        if validator:
            if validator(value):
                return value
            print("❌ Неверный формат. Попробуйте снова.")
        else:
            if value:
                return value
            print("❌ Поле не может быть пустым.")

def validate_token(token):
    """Валидация токена бота"""
    return re.match(r'^\d+:[A-Za-z0-9_-]+$', token) is not None

def validate_telegram_id(user_id):
    """Валидация Telegram ID"""
    try:
        return int(user_id) > 0
    except:
        return False

def create_directories():
    """Создание необходимых директорий"""
    directories = ['data', 'logs', 'exports', 'config']
    
    print("\n📁 Создание директорий...")
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✅ {directory}/")

def create_env_file(token, admin_id):
    """Создание .env файла"""
    env_content = f"""# 🤖 Telegram Bot для PythonAnywhere (1 Task в сутки)
BOT_TOKEN={token}
ADMIN_IDS={admin_id}

# 🗄️ Database Settings
DB_PATH=data/bot_database.db

# 🔔 Notification Settings
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30

# 📝 Logging Settings
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 📁 Export Settings
EXPORT_PATH=exports/

# ⚡ Daily Runner Settings
HEALTH_CHECK_INTERVAL=21600  # 6 hours
AUTO_RESTART_INTERVAL=3300   # 55 minutes
ERROR_NOTIFICATION_ENABLED=true
PERFORMANCE_MONITORING=true

# 🌐 PythonAnywhere Daily Settings
PA_DAILY_MODE=true
PA_MAX_SESSIONS=26          # ~24 hours / 55 minutes
PA_SESSION_TIME=3300        # 55 minutes
PA_DAILY_WORK_TIME=85800    # 23 hours 50 minutes
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл .env создан")

def create_daily_start_script(username):
    """Создание скрипта для ежедневного запуска"""
    
    script_content = f'''#!/bin/bash
# 🌐 PythonAnywhere Daily Start Script (1 Task per day)
# Запускается 1 раз в сутки и работает ~24 часа

cd /home/{username}/telegram_bot

echo "🌅 $(date): Начало дневного цикла бота"

# Проверяем, не запущен ли уже бот
if pgrep -f "pa_daily_runner.py" > /dev/null; then
    echo "⚠️ Бот уже запущен, завершаем старый процесс..."
    pkill -f "pa_daily_runner.py"
    sleep 5
fi

# Активируем виртуальное окружение
if [ -f "venv_bot/bin/activate" ]; then
    source venv_bot/bin/activate
    echo "✅ Виртуальное окружение активировано"
else
    echo "❌ Виртуальное окружение не найдено!"
    exit 1
fi

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден! Запустите setup_daily.py"
    exit 1
fi

# Создаем директории если их нет
mkdir -p logs data exports config

# Запускаем бот на целый день
echo "🚀 Запуск дневного цикла бота..."
nohup python3 pa_daily_runner.py > logs/daily_start.log 2>&1 &

echo "✅ Бот запущен в режиме дневного цикла"
echo "📝 Логи: tail -f logs/pa_daily.log"
echo "🔍 Статус: ps aux | grep pa_daily_runner"
'''
    
    with open('start_daily.sh', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # Делаем исполняемым
    os.chmod('start_daily.sh', 0o755)
    
    print("✅ Создан скрипт start_daily.sh")
    
    return f"/home/{username}/telegram_bot/start_daily.sh"

def test_bot_configuration():
    """Тестирование конфигурации бота"""
    print("\n🧪 Тестирование конфигурации...")
    
    # Тестируем импорт config
    try:
        python_cmd = "venv_bot/bin/python"
        test_cmd = f"{python_cmd} -c 'from config import Config; c = Config(); print(f\"BOT_TOKEN: {{c.BOT_TOKEN[:10]}}...\"); print(f\"ADMIN_IDS: {{c.ADMIN_IDS}}\")"
        success, output = run_command(test_cmd, "Тестирование config.py")
        
        if success and output.strip():
            print("✅ Конфигурация загружается корректно")
            print(f"   {output.strip()}")
            return True
        else:
            print("❌ Ошибка в конфигурации")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def create_installation_guide(username, script_path):
    """Создание руководства по установке"""
    
    guide_content = f"""# 🚀 Руководство по установке Telegram Bot (1 Task в сутки)

## ✅ Что настроено:
- 🐍 Виртуальное окружение `venv_bot` с зависимостями
- 🤖 Конфигурация для работы 24/7
- 🔄 Внутренние перезапуски каждые 55 минут  
- 📊 Отчеты о здоровье каждые 6 часов
- 🚨 Уведомления об ошибках админу
- 🌐 Оптимизация для PythonAnywhere Free

## 🎯 Настройка Scheduled Task:

### 1. Откройте PythonAnywhere Dashboard
### 2. Перейдите в "Tasks" → "Scheduled"  
### 3. Создайте задачу:

**Command:** `{script_path}`
**Hour:** `*` (любой час, когда хотите запускать)  
**Minute:** `0`
**Description:** `Telegram Bot Daily Runner`

**⚠️ ВАЖНО:** Задача запускается **1 раз в сутки** и работает ~24 часа

## 📊 Мониторинг:

### Логи:
```bash
# Основные логи дневного цикла
tail -f logs/pa_daily.log

# Логи запуска
tail -f logs/daily_start.log

# Основные логи бота
tail -f logs/bot.log
```

### Команды проверки:
```bash
# Статус процесса
ps aux | grep pa_daily_runner

# Использование ресурсов  
top -p $(pgrep -f pa_daily_runner)

# Ручной запуск для тестирования
./start_daily.sh

# Активация venv для отладки
source venv_bot/bin/activate
```

## 🔧 Управление:

```bash
# Остановить бота
pkill -f pa_daily_runner

# Запустить вручную в venv
source venv_bot/bin/activate
python3 pa_daily_runner.py

# Запустить через скрипт
./start_daily.sh

# Проверить установленные пакеты
venv_bot/bin/pip list
```

## 📈 Как это работает:

1. **Scheduled Task** запускается 1 раз в сутки
2. **start_daily.sh** активирует виртуальное окружение
3. **Daily Runner** работает ~24 часа (23 ч 50 мин)
4. **Внутренние сессии** по 55 минут с перезапусками
5. **Автоматическое завершение** за 10 минут до следующего Task
6. **Отчеты админу** каждые 6 часов
7. **Мгновенные уведомления** при ошибках

## 🐍 Виртуальное окружение:

- ✅ **venv_bot/** - изолированная среда Python
- ✅ **Все зависимости** установлены из requirements.txt
- ✅ **Автоматическая активация** в start_daily.sh
- ✅ **Независимость** от системных пакетов

## 🚨 Особенности PythonAnywhere Free:

- ✅ **1 Scheduled Task** - используется оптимально
- ✅ **Работа 24/7** - с внутренними перезапусками
- ✅ **Автоматическое управление** ресурсами
- ✅ **Безопасное завершение** перед следующим запуском
- ✅ **Изолированные зависимости** в venv

## 📱 Что получает админ:

### Уведомления каждые 6 часов:
- ⏰ Время работы и оставшееся время
- 🔄 Количество выполненных сессий
- ❌ Статистика ошибок
- 💾 Использование памяти
- 📊 Общий статус

### При ошибках мгновенно:
- 🚨 Описание ошибки
- 📍 Контекст возникновения
- 🔄 Номер сессии
- 📊 Общая статистика

### В конце дня:
- 🏁 Итоговая сводка за день
- ⏰ Общее время работы
- 📊 Эффективность работы
- 🎯 Время следующего запуска

## 🆘 Если что-то не работает:

1. **Проверьте виртуальное окружение:**
   ```bash
   ls -la venv_bot/
   source venv_bot/bin/activate
   python --version
   ```

2. **Проверьте зависимости:**
   ```bash
   venv_bot/bin/pip list
   venv_bot/bin/pip show aiogram
   ```

3. **Проверьте конфигурацию:**
   ```bash
   source venv_bot/bin/activate
   python -c "from config import Config; print('OK')"
   ```

4. **Проверьте логи:**
   ```bash
   tail -f logs/pa_daily.log
   tail -f logs/daily_start.log
   ```

5. **Переустановите зависимости:**
   ```bash
   source venv_bot/bin/activate
   pip install -r requirements.txt --force-reinstall
   ```

## 🔄 Переустановка:

Если нужно переустановить все с нуля:
```bash
rm -rf venv_bot .env
python3 setup_daily.py
```

**Время создания:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
**Пользователь:** {username}
**Режим:** 1 Scheduled Task в сутки с виртуальным окружением
"""
    
    with open('DAILY_SETUP_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Создано руководство DAILY_SETUP_GUIDE.md")

def main():
    """Главная функция настройки"""
    print_banner()
    
    # Проверяем Python
    if not check_python_version():
        print("❌ Несовместимая версия Python. Установка прервана.")
        return
    
    # Проверяем среду
    is_pa = detect_pythonanywhere()
    username = get_username()
    
    print(f"👤 Пользователь: {username}")
    print()
    
    # Простой ввод данных
    print("📝 Настройка бота (требуется только 2 параметра):")
    print()
    
    # Получаем токен
    token = get_input(
        "Введите BOT_TOKEN",
        validate_token,
        "Получите токен у @BotFather в Telegram"
    )
    
    # Получаем Telegram ID
    admin_id = get_input(
        "Введите ваш Telegram ID",
        validate_telegram_id,
        "Узнайте свой ID у @userinfobot в Telegram"
    )
    
    print("\n🔧 Автоматическая установка и настройка...")
    
    # Создаем виртуальное окружение
    if not create_virtual_environment():
        print("❌ Не удалось создать виртуальное окружение")
        return
    
    # Устанавливаем зависимости
    if not install_requirements():
        print("❌ Не удалось установить зависимости")
        return
    
    # Создаем директории
    create_directories()
    
    # Создаем файлы конфигурации
    create_env_file(token, admin_id)
    
    # Тестируем конфигурацию
    if not test_bot_configuration():
        print("⚠️ Конфигурация может работать некорректно")
    
    # Создаем скрипты
    script_path = create_daily_start_script(username)
    create_installation_guide(username, script_path)
    
    print("\n" + "=" * 60)
    print("🎉 УСТАНОВКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print()
    print("✅ Что установлено:")
    print("   🐍 venv_bot/ - виртуальное окружение с зависимостями")
    print("   📄 .env - конфигурация")
    print("   📜 start_daily.sh - скрипт запуска")
    print("   📚 DAILY_SETUP_GUIDE.md - руководство")
    print("   📁 data/, logs/, exports/, config/ - директории")
    print()
    print("🚀 Следующие шаги:")
    print("   1. Настройте Scheduled Task в PythonAnywhere")
    print("   2. Команда для задачи:")
    print(f"      {script_path}")
    print("   3. Расписание: 1 раз в сутки (любое время)")
    print()
    print("🧪 Быстрый тест:")
    print("   ./start_daily.sh")
    print("   tail -f logs/pa_daily.log")
    print()
    print("📖 Подробные инструкции в DAILY_SETUP_GUIDE.md")
    print()
    print("🎯 Ваш бот готов к работе 24/7 с:")
    print("   🐍 Изолированными зависимостями в venv")
    print("   🔄 Внутренними перезапусками каждые 55 минут")
    print("   📊 Отчетами админу каждые 6 часов")
    print("   🚨 Уведомлениями об ошибках")
    print("   ⏰ Автоматическим завершением перед следующим Task")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Установка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка установки: {e}")
        import traceback
        traceback.print_exc()