# 🚀 Запуск бота на PythonAnywhere Free с Python 3.10 (24/7)

## 🎯 **ВАЖНО: Особенности бесплатного аккаунта**

⚠️ **Ограничения Free аккаунта PythonAnywhere:**
- ❌ Нет "Always-On Tasks" (только в платной версии)
- ✅ Scheduled Tasks каждый час (можем использовать)
- ⏰ Ограничение CPU секунд в месяц (3000 сек/мес)
- 🌐 Ограниченный интернет доступ

**💡 Решение для 24/7:** Scheduled Task каждый час + проверка статуса

---

## 📋 **Предварительные требования**

1. ✅ Бесплатный аккаунт на [PythonAnywhere](https://www.pythonanywhere.com)
2. 🤖 Токен бота от [@BotFather](https://t.me/BotFather)
3. 🆔 Ваш Telegram ID от [@userinfobot](https://t.me/userinfobot)

---

## 🔧 **ПОШАГОВАЯ УСТАНОВКА**

### **Шаг 1: Подготовка аккаунта**

1. Зайдите на https://www.pythonanywhere.com
2. Создайте бесплатный аккаунт
3. Откройте **"Bash console"**

### **Шаг 2: Клонирование проекта**

```bash
# Переходим в домашнюю папку
cd ~

# Клонируем репозиторий (замените на ваш URL)
git clone YOUR_REPOSITORY_URL telegram_bot
cd telegram_bot

# Проверяем содержимое
ls -la
```

### **Шаг 3: Настройка Python 3.10**

```bash
# Проверяем доступные версии Python
ls /usr/bin/python*

# Создаем виртуальное окружение с Python 3.10
python3.10 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем версию Python
python --version
# Должно показать: Python 3.10.x

# Обновляем pip
pip install --upgrade pip
```

### **Шаг 4: Установка зависимостей**

```bash
# Убеждаемся, что виртуальное окружение активно
source venv/bin/activate

# Устанавливаем зависимости (может занять 2-3 минуты)
pip install -r requirements.txt

# Если возникают ошибки, устанавливаем по одной:
pip install aiogram==2.25.1
pip install python-dotenv==1.0.0
pip install aiosqlite==0.19.0
pip install aioschedule==0.5.2
pip install pytz==2023.3
pip install pandas==2.1.4
pip install openpyxl==3.1.2
pip install reportlab==4.0.4
```

### **Шаг 5: Конфигурация бота**

```bash
# Создаем файл .env с настройками
cat > .env << 'EOF'
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_TELEGRAM_ID_HERE
TIMEZONE=Europe/Moscow
DB_PATH=data/bot_database.db
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30
LOG_LEVEL=WARNING
LOG_FILE=logs/bot.log
EXPORT_PATH=exports/
EOF

# ⚠️ ОБЯЗАТЕЛЬНО замените YOUR_BOT_TOKEN_HERE и YOUR_TELEGRAM_ID_HERE!
```

**🔧 Как получить токен и ID:**
1. **Токен бота**: отправьте `/newbot` в [@BotFather](https://t.me/BotFather)
2. **Telegram ID**: отправьте любое сообщение в [@userinfobot](https://t.me/userinfobot)

### **Шаг 6: Создание структуры папок**

```bash
# Создаем необходимые папки
mkdir -p data exports logs config

# Проверяем структуру
ls -la
```

### **Шаг 7: Инициализация базы данных**

```bash
# Активируем окружение
source venv/bin/activate

# Инициализируем базу данных
python -c "
import asyncio
from database import Database

async def init_db():
    db = Database()
    await db.init()
    print('✅ База данных инициализирована')
    await db.close()

asyncio.run(init_db())
"
```

### **Шаг 8: Создание runner-скрипта для PythonAnywhere**

```bash
# Создаем специальный скрипт для запуска
cat > run_bot_pythonanywhere.py << 'EOF'
#!/usr/bin/env python3
"""
Специальный скрипт для запуска бота на PythonAnywhere Free
Оптимизирован для экономии CPU времени
"""

import sys
import os
import asyncio
import signal
import logging
from datetime import datetime, timedelta

# Добавляем текущую директорию в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем минимальный уровень логирования
logging.basicConfig(level=logging.WARNING)

def signal_handler(signum, frame):
    print(f"Получен сигнал {signum}, завершение работы...")
    sys.exit(0)

# Обработчики сигналов
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def run_bot():
    try:
        print(f"🚀 Запуск бота: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Импортируем и запускаем основной модуль
        from main import bot, dp, db, on_startup, on_shutdown
        from aiogram import executor
        
        # Запускаем бота
        executor.start_polling(
            dp, 
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=20
        )
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        logging.error(f"Ошибка запуска: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PythonAnywhere Bot Runner")
    print("=" * 50)
    
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
EOF

# Делаем скрипт исполняемым
chmod +x run_bot_pythonanywhere.py
```

### **Шаг 9: Создание hourly-скрипта**

```bash
# Создаем скрипт для ежечасного запуска
cat > hourly_runner.sh << 'EOF'
#!/bin/bash

# Переходим в папку бота
cd ~/telegram_bot

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, не запущен ли уже бот
EXISTING_PID=$(pgrep -f "run_bot_pythonanywhere.py")

if [ ! -z "$EXISTING_PID" ]; then
    echo "⏰ $(date): Бот уже запущен (PID: $EXISTING_PID)"
    # Проверяем, давно ли запущен (больше 50 минут)
    RUNTIME=$(ps -o etime= -p $EXISTING_PID 2>/dev/null | tr -d ' ')
    if [[ $RUNTIME == *":"* ]]; then
        MINUTES=$(echo $RUNTIME | cut -d: -f1)
        if [ "$MINUTES" -gt 50 ]; then
            echo "🔄 Бот работает больше 50 минут, перезапускаем..."
            kill $EXISTING_PID
            sleep 5
        else
            echo "✅ Бот работает нормально ($RUNTIME)"
            exit 0
        fi
    fi
fi

# Запускаем бота в фоне
echo "🚀 $(date): Запуск бота..."
nohup python run_bot_pythonanywhere.py > logs/bot_output.log 2>&1 &

# Ждем 3 секунды и проверяем запуск
sleep 3

NEW_PID=$(pgrep -f "run_bot_pythonanywhere.py")
if [ ! -z "$NEW_PID" ]; then
    echo "✅ $(date): Бот успешно запущен (PID: $NEW_PID)"
else
    echo "❌ $(date): Ошибка запуска бота"
    # Показываем последние ошибки
    tail -10 logs/bot_output.log
fi
EOF

# Делаем скрипт исполняемым
chmod +x hourly_runner.sh
```

### **Шаг 10: Тестовый запуск**

```bash
# Активируем окружение
source venv/bin/activate

# Тестируем конфигурацию
python -c "
from config import Config
config = Config()
print('✅ Конфигурация загружена')
print(f'Токен: {'✅' if config.BOT_TOKEN else '❌'}')
print(f'Админы: {config.ADMIN_IDS}')
"

# Тестируем запуск (остановится через Ctrl+C)
echo "🧪 Тестовый запуск (нажмите Ctrl+C через несколько секунд):"
python run_bot_pythonanywhere.py
```

### **Шаг 11: Настройка автозапуска в PythonAnywhere**

1. **Откройте вкладку "Tasks"** в дашборде PythonAnywhere

2. **Создайте новую задачу:**
   - Click **"Create a task"**
   - **Command**: `/home/yourusername/telegram_bot/hourly_runner.sh`
   - **Hour**: `*` (каждый час)
   - **Minute**: `5` (на 5-й минуте каждого часа)

3. **Замените `yourusername`** на ваше имя пользователя PythonAnywhere

### **Шаг 12: Мониторинг и проверка**

```bash
# Создаем скрипт мониторинга
cat > check_status.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import sqlite3
from datetime import datetime

def check_bot_status():
    print("🔍 Проверка статуса бота:")
    print("=" * 40)
    
    # Проверяем процесс
    try:
        result = subprocess.run(['pgrep', '-f', 'run_bot_pythonanywhere.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ Бот запущен (PID: {pid})")
            
            # Проверяем время работы
            runtime_result = subprocess.run(['ps', '-o', 'etime=', '-p', pid], 
                                          capture_output=True, text=True)
            if runtime_result.returncode == 0:
                runtime = runtime_result.stdout.strip()
                print(f"⏰ Время работы: {runtime}")
        else:
            print("❌ Бот не запущен")
    except Exception as e:
        print(f"❌ Ошибка проверки процесса: {e}")
    
    # Проверяем базу данных
    try:
        conn = sqlite3.connect('data/bot_database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        print(f"👥 Пользователей в БД: {users_count}")
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
    
    # Проверяем логи
    if os.path.exists('logs/bot_output.log'):
        with open('logs/bot_output.log', 'r') as f:
            lines = f.readlines()
            if lines:
                print(f"📝 Последняя запись: {lines[-1].strip()}")
    
    print("=" * 40)

if __name__ == "__main__":
    check_bot_status()
EOF

chmod +x check_status.py
```

---

## 🚀 **ЗАПУСК И ПРОВЕРКА**

### **Ручной запуск (для тестирования):**
```bash
cd ~/telegram_bot
./hourly_runner.sh
```

### **Проверка статуса:**
```bash
cd ~/telegram_bot
python check_status.py
```

### **Просмотр логов:**
```bash
# Основные логи
tail -f logs/bot_output.log

# Логи ошибок
tail -f logs/bot.log
```

### **Остановка бота:**
```bash
pkill -f "run_bot_pythonanywhere.py"
```

---

## 💡 **ОПТИМИЗАЦИЯ ДЛЯ FREE АККАУНТА**

### **В файле .env установите:**
```env
LOG_LEVEL=WARNING          # Меньше логов = экономия CPU
NOTIFICATIONS_ENABLED=false # Отключить пока не нужны
```

### **Мониторинг CPU usage:**
- Заходите в дашборд PythonAnywhere
- Проверяйте "CPU seconds used this month"
- Цель: не превысить 3000 секунд в месяц

---

## ✅ **ФИНАЛЬНЫЙ ЧЕК-ЛИСТ**

- [ ] Репозиторий склонирован в `~/telegram_bot`
- [ ] Python 3.10 venv создан и активен
- [ ] Все зависимости установлены
- [ ] Файл `.env` создан с правильным токеном и ID
- [ ] База данных инициализирована
- [ ] Hourly task создана в PythonAnywhere
- [ ] Тестовый запуск прошел успешно
- [ ] Бот отвечает в Telegram

---

## 🆘 **РЕШЕНИЕ ПРОБЛЕМ**

### **Бот не запускается:**
```bash
cd ~/telegram_bot
source venv/bin/activate
python run_bot_pythonanywhere.py
# Смотрим ошибки в выводе
```

### **Забыли токен/ID:**
```bash
nano .env
# Исправляем BOT_TOKEN и ADMIN_IDS
```

### **Превышен лимит CPU:**
- Увеличьте интервал hourly task до 2-3 часов
- Установите `LOG_LEVEL=ERROR`
- Временно отключите уведомления

### **Task не запускается:**
1. Проверьте путь в команде task
2. Убедитесь, что скрипт исполняемый: `chmod +x hourly_runner.sh`
3. Проверьте логи в дашборде PythonAnywhere

---

## 🎉 **ГОТОВО!**

Ваш бот теперь работает 24/7 на PythonAnywhere Free с автоматическими перезапусками каждый час! 

**Команды для управления:**
- `/start` - запуск бота
- `/admin` - админ-панель  
- `/status` - статус системы

**Мониторинг:**
```bash
cd ~/telegram_bot && python check_status.py
```

🚀 **Бот готов к работе!**