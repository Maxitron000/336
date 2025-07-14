#!/usr/bin/env python3
"""
🌐 Простая настройка бота для PythonAnywhere (1 Task в сутки)
Требует только токен бота и Telegram ID администратора
"""

import os
import sys
import re
from datetime import datetime

def print_banner():
    """Красивый баннер"""
    print("=" * 60)
    print("🤖 PYTHONANYWHERE BOT SETUP (1 Task/Day)")
    print("🔄 Работа 24/7 с внутренними перезапусками")
    print("📊 Отчеты админу каждые 6 часов")
    print("🚨 Уведомления об ошибках")
    print("=" * 60)
    print()

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
    echo "⚠️ Виртуальное окружение не найдено, используем системный Python"
fi

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден! Запустите setup_daily.py"
    exit 1
fi

# Создаем директории
mkdir -p logs data exports

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

def create_installation_guide(username, script_path):
    """Создание руководства по установке"""
    
    guide_content = f"""# 🚀 Руководство по установке Telegram Bot (1 Task в сутки)

## ✅ Что настроено:
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
```

## 🔧 Управление:

```bash
# Остановить бота
pkill -f pa_daily_runner

# Запустить вручную
python3 pa_daily_runner.py

# Запустить через скрипт
./start_daily.sh
```

## 📈 Как это работает:

1. **Scheduled Task** запускается 1 раз в сутки
2. **Daily Runner** работает ~24 часа (23 ч 50 мин)
3. **Внутренние сессии** по 55 минут с перезапусками
4. **Автоматическое завершение** за 10 минут до следующего Task
5. **Отчеты админу** каждые 6 часов
6. **Мгновенные уведомления** при ошибках

## 🚨 Особенности PythonAnywhere Free:

- ✅ **1 Scheduled Task** - используется оптимально
- ✅ **Работа 24/7** - с внутренними перезапусками
- ✅ **Автоматическое управление** ресурсами
- ✅ **Безопасное завершение** перед следующим запуском

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

1. Проверьте `.env` файл
2. Убедитесь, что виртуальное окружение создано
3. Проверьте логи: `tail -f logs/pa_daily.log`
4. Убедитесь, что Scheduled Task настроена правильно
5. Попробуйте ручной запуск: `./start_daily.sh`

**Время создания:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
**Пользователь:** {username}
**Режим:** 1 Scheduled Task в сутки
"""
    
    with open('DAILY_SETUP_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Создано руководство DAILY_SETUP_GUIDE.md")

def main():
    """Главная функция настройки"""
    print_banner()
    
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
    
    print("\n🔧 Создание конфигурации...")
    
    # Создаем директории
    for directory in ['data', 'logs', 'exports', 'config']:
        os.makedirs(directory, exist_ok=True)
    
    # Создаем файлы
    create_env_file(token, admin_id)
    script_path = create_daily_start_script(username)
    create_installation_guide(username, script_path)
    
    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print()
    print("✅ Созданы файлы:")
    print("   📄 .env - конфигурация")
    print("   🤖 pa_daily_runner.py - дневной раннер")
    print("   📜 start_daily.sh - скрипт запуска")
    print("   📚 DAILY_SETUP_GUIDE.md - руководство")
    print()
    print("🚀 Следующие шаги:")
    print("   1. Настройте Scheduled Task в PythonAnywhere")
    print("   2. Команда для задачи:")
    print(f"      {script_path}")
    print("   3. Расписание: 1 раз в сутки (любое время)")
    print()
    print("📖 Подробные инструкции в DAILY_SETUP_GUIDE.md")
    print()
    print("🎯 Ваш бот будет работать 24/7 с:")
    print("   🔄 Внутренними перезапусками каждые 55 минут")
    print("   📊 Отчетами админу каждые 6 часов")
    print("   🚨 Уведомлениями об ошибках")
    print("   ⏰ Автоматическим завершением перед следующим Task")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка настройки: {e}")