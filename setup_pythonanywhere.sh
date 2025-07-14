#!/bin/bash
# 🚀 Автоматический скрипт установки бота на PythonAnywhere Free
# Версия: 2.0 для Python 3.10

set -e  # Остановка при любой ошибке

echo "🚀 АВТОМАТИЧЕСКАЯ УСТАНОВКА TELEGRAM БОТА НА PYTHONANYWHERE"
echo "=============================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем, что мы на PythonAnywhere
if [[ ! "$HOME" == /home/* ]]; then
    log_error "Этот скрипт предназначен для PythonAnywhere"
    exit 1
fi

log_info "Начинаем установку..."

# Шаг 1: Переходим в домашнюю папку
cd ~
log_info "Переходим в домашнюю папку: $HOME"

# Шаг 2: Создаем папку для бота (если еще нет)
if [ ! -d "telegram_bot" ]; then
    mkdir telegram_bot
    log_info "Создана папка telegram_bot"
else
    log_warning "Папка telegram_bot уже существует"
fi

cd telegram_bot

# Шаг 3: Проверяем наличие Python 3.10
log_info "Проверяем Python 3.10..."
if command -v python3.10 &> /dev/null; then
    PYTHON_VERSION=$(python3.10 --version)
    log_info "Найден: $PYTHON_VERSION"
else
    log_error "Python 3.10 не найден на этой системе"
    exit 1
fi

# Шаг 4: Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    log_info "Создаем виртуальное окружение..."
    python3.10 -m venv venv
    log_info "Виртуальное окружение создано"
else
    log_warning "Виртуальное окружение уже существует"
fi

# Активируем виртуальное окружение
source venv/bin/activate
log_info "Виртуальное окружение активировано"

# Обновляем pip
log_info "Обновляем pip..."
pip install --upgrade pip > /dev/null 2>&1

# Шаг 5: Создаем requirements.txt если его нет
if [ ! -f "requirements.txt" ]; then
    log_info "Создаем requirements.txt..."
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
fi

# Шаг 6: Устанавливаем зависимости
log_info "Устанавливаем зависимости (это может занять несколько минут)..."
pip install -r requirements.txt

# Шаг 7: Создаем структуру папок
log_info "Создаем структуру папок..."
mkdir -p data exports logs config

# Шаг 8: Создаем файлы конфигурации
log_info "Создаем файлы конфигурации..."

# .env файл
if [ ! -f ".env" ]; then
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
    log_warning "Создан файл .env - ОБЯЗАТЕЛЬНО замените токен и ID!"
else
    log_warning "Файл .env уже существует"
fi

# Файл уведомлений
if [ ! -f "config/notifications.json" ]; then
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
    log_info "Создан файл уведомлений"
fi

# Файл локаций
if [ ! -f "data/locations.json" ]; then
    cat > data/locations.json << 'EOF'
{
  "locations": [
    "🏥 Поликлиника",
    "⚓ ОБРМП", 
    "🌆 Калининград",
    "🛒 Магазин",
    "🍲 Столовая",
    "🏨 Госпиталь",
    "⚙️ Рабочка",
    "🩺 ВВК",
    "🏛️ МФЦ",
    "🚓 Патруль",
    "📝 Другое"
  ]
}
EOF
    log_info "Создан файл локаций"
fi

# Шаг 9: Создаем runner скрипт
log_info "Создаем runner скрипт..."
cat > run_bot_pythonanywhere.py << 'EOF'
#!/usr/bin/env python3
"""
Специальный скрипт для запуска бота на PythonAnywhere Free
Оптимизирован для экономии CPU времени
"""

import sys
import os
import signal
import logging
from datetime import datetime

# Добавляем текущую директорию в PATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем минимальный уровень логирования для экономии CPU
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

def signal_handler(signum, frame):
    print(f"Получен сигнал {signum}, завершение работы...")
    sys.exit(0)

# Обработчики сигналов
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def run_bot():
    try:
        print(f"🚀 Запуск бота: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Проверяем наличие токена
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token or bot_token == 'REPLACE_WITH_YOUR_BOT_TOKEN':
            print("❌ Токен бота не настроен! Отредактируйте файл .env")
            return False
        
        # Импортируем и запускаем основной модуль
        from main import bot, dp, on_startup, on_shutdown
        from aiogram import executor
        
        # Запускаем бота
        executor.start_polling(
            dp, 
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            timeout=20
        )
        
    except ImportError as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        print("Убедитесь, что все файлы проекта загружены")
        return False
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        logging.error(f"Ошибка запуска: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🤖 PythonAnywhere Bot Runner v2.0")
    print("=" * 50)
    
    try:
        run_bot()
    except KeyboardInterrupt:
        print("⏹️ Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)
EOF

chmod +x run_bot_pythonanywhere.py

# Шаг 10: Создаем hourly runner
log_info "Создаем скрипт ежечасного запуска..."
USERNAME=$(whoami)
cat > hourly_runner.sh << EOF
#!/bin/bash

# Переходим в папку бота
cd /home/$USERNAME/telegram_bot

# Активируем виртуальное окружение
source venv/bin/activate

# Проверяем, не запущен ли уже бот
EXISTING_PID=\$(pgrep -f "run_bot_pythonanywhere.py")

if [ ! -z "\$EXISTING_PID" ]; then
    echo "⏰ \$(date): Бот уже запущен (PID: \$EXISTING_PID)"
    # Проверяем, давно ли запущен (больше 50 минут)
    RUNTIME=\$(ps -o etime= -p \$EXISTING_PID 2>/dev/null | tr -d ' ')
    if [[ \$RUNTIME == *":"* ]]; then
        MINUTES=\$(echo \$RUNTIME | cut -d: -f1)
        if [ "\$MINUTES" -gt 50 ]; then
            echo "🔄 Бот работает больше 50 минут, перезапускаем..."
            kill \$EXISTING_PID
            sleep 5
        else
            echo "✅ Бот работает нормально (\$RUNTIME)"
            exit 0
        fi
    fi
fi

# Запускаем бота в фоне
echo "🚀 \$(date): Запуск бота..."
nohup python run_bot_pythonanywhere.py > logs/bot_output.log 2>&1 &

# Ждем 3 секунды и проверяем запуск
sleep 3

NEW_PID=\$(pgrep -f "run_bot_pythonanywhere.py")
if [ ! -z "\$NEW_PID" ]; then
    echo "✅ \$(date): Бот успешно запущен (PID: \$NEW_PID)"
else
    echo "❌ \$(date): Ошибка запуска бота"
    tail -10 logs/bot_output.log
fi
EOF

chmod +x hourly_runner.sh

# Шаг 11: Создаем скрипт мониторинга
log_info "Создаем скрипт мониторинга..."
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
    
    # Проверяем конфигурацию
    try:
        from dotenv import load_dotenv
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        admin_ids = os.getenv('ADMIN_IDS')
        
        if bot_token and bot_token != 'REPLACE_WITH_YOUR_BOT_TOKEN':
            print("✅ Токен бота настроен")
        else:
            print("❌ Токен бота НЕ настроен")
            
        if admin_ids and admin_ids != 'REPLACE_WITH_YOUR_TELEGRAM_ID':
            print(f"✅ Админы настроены: {admin_ids}")
        else:
            print("❌ ID админов НЕ настроены")
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
    
    # Проверяем базу данных
    try:
        if os.path.exists('data/bot_database.db'):
            conn = sqlite3.connect('data/bot_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            users_count = cursor.fetchone()[0]
            print(f"👥 Пользователей в БД: {users_count}")
            conn.close()
        else:
            print("⚠️ База данных еще не создана")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
    
    # Проверяем логи
    if os.path.exists('logs/bot_output.log'):
        try:
            with open('logs/bot_output.log', 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"📝 Последняя запись: {lines[-1].strip()}")
        except Exception as e:
            print(f"❌ Ошибка чтения логов: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    check_bot_status()
EOF

chmod +x check_status.py

# Заключительные инструкции
echo ""
log_info "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo ""
echo "=============================================================="
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "=============================================================="
echo ""
echo "1. 🔧 НАСТРОЙТЕ ТОКЕН И ID:"
echo "   nano .env"
echo "   Замените:"
echo "   - BOT_TOKEN=REPLACE_WITH_YOUR_BOT_TOKEN"
echo "   - ADMIN_IDS=REPLACE_WITH_YOUR_TELEGRAM_ID"
echo ""
echo "2. 📁 ЗАГРУЗИТЕ ФАЙЛЫ ПРОЕКТА:"
echo "   Скопируйте все .py файлы в эту папку:"
echo "   $(pwd)"
echo ""
echo "3. 🧪 ТЕСТОВЫЙ ЗАПУСК:"
echo "   ./check_status.py"
echo "   python run_bot_pythonanywhere.py"
echo ""
echo "4. ⏰ СОЗДАЙТЕ HOURLY TASK в дашборде PythonAnywhere:"
echo "   Command: /home/$USERNAME/telegram_bot/hourly_runner.sh"
echo "   Hour: * (каждый час)"
echo "   Minute: 5"
echo ""
echo "=============================================================="
echo "🆘 ПОМОЩЬ:"
echo "=============================================================="
echo "Проверка статуса: ./check_status.py"
echo "Просмотр логов: tail -f logs/bot_output.log"
echo "Остановка бота: pkill -f run_bot_pythonanywhere.py"
echo ""
log_info "Установка завершена! Настройте токен и запускайте бота! 🚀"