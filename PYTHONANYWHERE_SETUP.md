# 🚀 Установка бота на PythonAnywhere Free

## 📋 Предварительные требования

1. **Аккаунт на PythonAnywhere** (бесплатный)
2. **Токен бота** от @BotFather
3. **Ваш Telegram ID** (можно получить у @userinfobot)

## 🔧 Пошаговая установка

### Шаг 1: Регистрация и вход
1. Перейдите на https://www.pythonanywhere.com
2. Создайте бесплатный аккаунт
3. Войдите в систему

### Шаг 2: Клонирование репозитория
```bash
# Откройте консоль Bash
cd ~
git clone https://github.com/ваш_username/ваш_репозиторий.git telegram_bot
cd telegram_bot
```

### Шаг 3: Настройка Python 3.10
```bash
# Проверяем версию Python
python3.10 --version

# Создаем виртуальное окружение
python3.10 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip
```

### Шаг 4: Установка зависимостей
```bash
# Устанавливаем все зависимости
pip install -r requirements.txt

# Если возникнут ошибки, устанавливаем по частям:
pip install python-telegram-bot==20.7
pip install python-dotenv==1.0.0
pip install schedule==1.2.0
pip install pytz==2023.3
pip install aiosqlite==0.19.0
pip install pandas==2.1.4
pip install openpyxl==3.1.2
pip install xlsxwriter==3.1.9
pip install reportlab==4.0.4
pip install requests==2.31.0
pip install configparser==6.0.0
pip install typing_extensions==4.8.0
```

### Шаг 5: Создание конфигурации
```bash
# Создаем файл .env
cat > .env << 'EOF'
BOT_TOKEN=ваш_токен_бота_здесь
ADMIN_IDS=ваш_telegram_id_здесь
TIMEZONE=Europe/Kaliningrad
DB_PATH=data/bot_database.db
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30
LOG_LEVEL=INFO
LOG_FILE=bot.log
EXPORT_PATH=exports/
EOF
```

### Шаг 6: Создание папок
```bash
# Создаем необходимые папки
mkdir -p data exports logs config

# Проверяем структуру
ls -la
```

### Шаг 7: Инициализация базы данных
```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Создаем базу данных для main_optimized.py
python3.10 -c "
import sqlite3
conn = sqlite3.connect('data/personnel.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT UNIQUE NOT NULL,
        is_admin INTEGER DEFAULT 0,
        admin_permissions TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS arrivals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        location TEXT,
        custom_location TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')
conn.commit()
conn.close()
print('✅ База данных personnel.db создана!')
"

# Создаем базу данных для main.py (если понадобится)
python3.10 -c "
import sqlite3
conn = sqlite3.connect('data/bot_database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        location TEXT,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        location TEXT,
        status TEXT DEFAULT 'present',
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, date)
    )
''')
conn.commit()
conn.close()
print('✅ База данных bot_database.db создана!')
"
```

### Шаг 8: Создание файла уведомлений
```bash
# Создаем файл уведомлений
cat > config/notifications.json << 'EOF'
{
  "reminders": [
    "🔔 Эй, боец! Не забудь отметиться!",
    "⏰ Время отметиться, товарищ!",
    "📱 Ты еще не отметился сегодня!",
    "🎯 Пора показать, что ты на месте!",
    "💪 Не подведи команду - отметьсь!"
  ],
  "daily_summary": [
    "📊 Ежедневная сводка готовности",
    "📈 Отчет по личному составу",
    "📋 Статистика на сегодня"
  ]
}
EOF
```

### Шаг 9: Тестовый запуск
```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Тестируем main_optimized.py (рекомендуется)
python3.10 main_optimized.py

# Или тестируем main.py (если нужна совместимость)
# python3.10 main.py
```

### Шаг 10: Настройка автозапуска

#### Вариант 1: Daily Task (рекомендуется)
1. Перейдите в раздел **"Tasks"**
2. Нажмите **"Add a new task"**
3. Заполните форму:
   - **Command**: `cd ~/telegram_bot && source venv/bin/activate && python3.10 main_optimized.py`
   - **Schedule**: Daily
   - **Time**: 00:00

#### Вариант 2: Always-on Task
1. В разделе **"Tasks"** создайте новую задачу
2. **Command**:
```bash
cd ~/telegram_bot
source venv/bin/activate
while true; do
    echo "Запуск бота: $(date)"
    python3.10 main_optimized.py
    echo "Бот остановлен: $(date)"
    sleep 60
done
```
3. **Schedule**: Always-on

### Шаг 11: Создание скриптов управления
```bash
# Создаем скрипт запуска
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd ~/telegram_bot
source venv/bin/activate
python3.10 main_optimized.py
EOF

# Создаем скрипт обновления
cat > update_bot.sh << 'EOF'
#!/bin/bash
cd ~/telegram_bot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
echo "Обновление завершено: $(date)"
EOF

# Создаем скрипт мониторинга
cat > monitor.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

def check_bot_status():
    try:
        # Проверяем базу данных
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        conn.close()
        
        # Проверяем логи
        log_file = 'logs/bot.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                last_line = lines[-1] if lines else "Нет логов"
        else:
            last_line = "Файл логов не найден"
        
        print(f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"Пользователей в БД: {users_count}")
        print(f"Последняя запись в логе: {last_line.strip()}")
        
    except Exception as e:
        print(f"Ошибка проверки: {e}")

if __name__ == "__main__":
    check_bot_status()
EOF

# Делаем скрипты исполняемыми
chmod +x start_bot.sh update_bot.sh
```

## 🔍 Проверка установки

### Проверка зависимостей
```bash
source venv/bin/activate
python3.10 -c "
import telegram
import aiogram
import dotenv
import schedule
import pytz
import aiosqlite
import pandas
import openpyxl
import reportlab
print('✅ Все зависимости установлены!')
"
```

### Проверка конфигурации
```bash
source venv/bin/activate
python3.10 -c "
from dotenv import load_dotenv
import os
load_dotenv()
token = os.getenv('BOT_TOKEN')
admin_ids = os.getenv('ADMIN_IDS')
print(f'Токен: {'✅ Установлен' if token else '❌ Отсутствует'}')
print(f'Админы: {'✅ Установлены' if admin_ids else '❌ Отсутствуют'}')
"
```

### Проверка базы данных
```bash
source venv/bin/activate
python3.10 -c "
import sqlite3
conn = sqlite3.connect('data/personnel.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = cursor.fetchall()
print(f'Таблицы в БД: {[t[0] for t in tables]}')
conn.close()
"
```

## 🚨 Решение проблем

### Ошибка "No module named 'aiogram'"
```bash
pip install aiogram==2.25.1
```

### Ошибка "No module named 'aiosqlite'"
```bash
pip install aiosqlite==0.19.0
```

### Ошибка "No module named 'reportlab'"
```bash
pip install reportlab==4.0.4
```

### Ошибка "Permission denied"
```bash
chmod +x *.sh
```

### Бот не запускается
```bash
# Проверяем логи
tail -f logs/bot.log

# Проверяем токен
cat .env | grep BOT_TOKEN
```

## 📊 Мониторинг работы

### Проверка статуса
```bash
python3.10 monitor.py
```

### Просмотр логов
```bash
tail -f logs/bot.log
```

### Проверка базы данных
```bash
sqlite3 data/personnel.db "SELECT COUNT(*) FROM users;"
```

## 🎯 Рекомендации для Free аккаунта

1. **Используйте `main_optimized.py`** - он более эффективен
2. **Установите `LOG_LEVEL=WARNING`** для экономии ресурсов
3. **Периодически очищайте логи** - добавьте задачу очистки
4. **Используйте Daily Task** вместо Always-on для экономии ресурсов

## ✅ Чек-лист

- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Все зависимости установлены
- [ ] Файл .env создан с правильным токеном
- [ ] Базы данных инициализированы
- [ ] Папки созданы
- [ ] Бот запускается без ошибок
- [ ] Задача автозапуска создана
- [ ] Мониторинг настроен

Бот готов к работе 24/7 на PythonAnywhere Free! 🎉