# 📋 ГОТОВЫЕ КОМАНДЫ ДЛЯ ДЕПЛОЙМЕНТА НА PYTHONANYWHERE

## 🚀 **КОПИРУЙТЕ И ВСТАВЛЯЙТЕ ПО ПОРЯДКУ**

### **📁 Способ 1: Если у вас есть Git репозиторий**

```bash
# 1. Клонирование проекта
cd ~
git clone YOUR_REPOSITORY_URL telegram_bot
cd telegram_bot

# 2. Автоматическая установка
bash setup_pythonanywhere.sh

# 3. Настройка токена (откроется редактор)
nano .env
# Замените BOT_TOKEN=... и ADMIN_IDS=... на реальные значения

# 4. Проверка установки
./check_status.py

# 5. Тестовый запуск (остановите через 10 сек Ctrl+C)
python run_bot_pythonanywhere.py
```

### **📤 Способ 2: Загрузка файлов вручную**

```bash
# 1. Создание структуры
cd ~
mkdir telegram_bot
cd telegram_bot

# 2. Автоматическая установка (создаст всё необходимое)
curl -O https://raw.githubusercontent.com/YOUR_REPO/setup_pythonanywhere.sh
bash setup_pythonanywhere.sh

# 3. Загрузите файлы через Files tab в PythonAnywhere:
# - main.py
# - config.py  
# - database.py
# - handlers.py
# - keyboards.py
# - admin.py
# - notifications.py
# - export.py
# - utils.py
# - monitoring.py
# - backup.py
# - auto_restart.py
# - pythonanywhere_support.py

# 4. Настройка токена
nano .env
# Замените BOT_TOKEN=... и ADMIN_IDS=...

# 5. Проверка
./check_status.py
```

### **🔧 Способ 3: Полностью ручная установка**

```bash
# 1. Создание папки проекта
cd ~
mkdir telegram_bot
cd telegram_bot

# 2. Создание виртуального окружения Python 3.10
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 3. Создание requirements.txt
cat > requirements.txt << 'EOF'
aiogram==2.25.1
python-dotenv==1.0.0
aiosqlite==0.19.0
aioschedule==0.5.2
pytz==2023.3
pandas==2.1.4
openpyxl==3.1.2
reportlab==4.0.4
requests==2.31.0
configparser==6.0.0
typing_extensions==4.8.0
psutil==5.9.6
EOF

# 4. Установка зависимостей
pip install -r requirements.txt

# 5. Создание структуры папок
mkdir -p data exports logs config

# 6. Создание конфигурации
cat > .env << 'EOF'
BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN
ADMIN_IDS=REPLACE_WITH_YOUR_TELEGRAM_ID
TIMEZONE=Europe/Moscow
DB_PATH=data/bot_database.db
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30
LOG_LEVEL=WARNING
LOG_FILE=logs/bot.log
EXPORT_PATH=exports/
EOF

# 7. Настройка токена
nano .env
# Замените REPLACE_WITH_YOUR_BOT_TOKEN и REPLACE_WITH_YOUR_TELEGRAM_ID

# Теперь загрузите все .py файлы проекта через Files tab
```

---

## ⏰ **СОЗДАНИЕ HOURLY TASK**

После установки **любым способом**:

1. Откройте https://www.pythonanywhere.com
2. Перейдите в раздел **"Tasks"**
3. Нажмите **"Create a task"**
4. Заполните форму:

```
Command: /home/YOURUSERNAME/telegram_bot/hourly_runner.sh
Hour: *
Minute: 5
```

**⚠️ Замените YOURUSERNAME на ваше имя пользователя!**

**Узнать имя пользователя:**
```bash
whoami
```

---

## 🔍 **КОМАНДЫ ПРОВЕРКИ И УПРАВЛЕНИЯ**

```bash
# Переходим в папку проекта
cd ~/telegram_bot

# Проверка статуса бота
./check_status.py

# Ручной запуск для тестирования
python run_bot_pythonanywhere.py

# Запуск через hourly runner
./hourly_runner.sh

# Просмотр логов в реальном времени
tail -f logs/bot_output.log

# Просмотр последних 20 строк логов
tail -20 logs/bot_output.log

# Остановка бота
pkill -f "run_bot_pythonanywhere.py"

# Проверка запущенных процессов
pgrep -f "run_bot_pythonanywhere.py"

# Показать информацию о процессе
ps aux | grep "run_bot_pythonanywhere.py"
```

---

## 🧪 **КОМАНДЫ ТЕСТИРОВАНИЯ**

```bash
# Активация виртуального окружения
cd ~/telegram_bot
source venv/bin/activate

# Проверка конфигурации
python -c "
from config import Config
config = Config()
print('✅ Конфигурация загружена')
print(f'Токен: {'✅ OK' if config.BOT_TOKEN and config.BOT_TOKEN != 'REPLACE_WITH_YOUR_BOT_TOKEN' else '❌ НЕ НАСТРОЕН'}')
print(f'Админы: {config.ADMIN_IDS}')
"

# Проверка зависимостей
python -c "
try:
    import aiogram, aiosqlite, pandas, openpyxl
    print('✅ Все зависимости установлены')
except ImportError as e:
    print(f'❌ Ошибка зависимостей: {e}')
"

# Инициализация базы данных
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

---

## 📊 **МОНИТОРИНГ CPU USAGE**

```bash
# Текущее использование CPU (в секундах)
# Проверяйте в дашборде PythonAnywhere: Dashboard > Account

# Если превышен лимит 3000 сек/месяц:
# 1. Измените hourly task на каждые 2 часа:
#    Hour: */2 вместо *
# 2. Уменьшите логирование:
nano .env
# Установите: LOG_LEVEL=ERROR

# 3. Отключите уведомления временно:
# Установите: NOTIFICATIONS_ENABLED=false
```

---

## 🆘 **РЕШЕНИЕ ЧАСТЫХ ПРОБЛЕМ**

### **Проблема: "No module named 'aiogram'"**
```bash
cd ~/telegram_bot
source venv/bin/activate
pip install aiogram==2.25.1
```

### **Проблема: "Permission denied"**
```bash
chmod +x hourly_runner.sh
chmod +x check_status.py
chmod +x run_bot_pythonanywhere.py
```

### **Проблема: Task не запускается**
```bash
# Проверьте путь в Task:
whoami  # Узнайте ваше имя пользователя
# Путь должен быть: /home/YOURUSERNAME/telegram_bot/hourly_runner.sh
```

### **Проблема: Бот не отвечает**
```bash
cd ~/telegram_bot
./check_status.py

# Если показывает "❌ Токен бота НЕ настроен":
nano .env
# Исправьте BOT_TOKEN и ADMIN_IDS
```

### **Проблема: Ошибки в логах**
```bash
tail -50 logs/bot_output.log  # Смотрим последние ошибки
tail -50 logs/bot.log        # Смотрим системные логи
```

---

## ✅ **ФИНАЛЬНАЯ ПРОВЕРКА**

После выполнения всех команд проверьте:

```bash
cd ~/telegram_bot

# 1. Статус
./check_status.py

# 2. Конфигурация
cat .env | grep -E "(BOT_TOKEN|ADMIN_IDS)"

# 3. Права на файлы
ls -la | grep -E "(runner|check_status)"

# 4. Процессы
pgrep -f "run_bot_pythonanywhere.py"

# 5. Отправьте /start вашему боту в Telegram
```

**Если всё ✅, то бот работает 24/7!** 🚀