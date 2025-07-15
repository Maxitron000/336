#!/bin/bash
#
# 🚀 МГНОВЕННЫЙ ЗАПУСК TELEGRAM БОТА
# Введите токен и ID, остальное автоматически
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}🚀 МГНОВЕННЫЙ ЗАПУСК TELEGRAM БОТА${NC}"
    echo -e "${BLUE}🤖 Автоматическая настройка за 30 секунд${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

check_requirements() {
    echo -e "${YELLOW}🔍 Проверка требований...${NC}"
    
    # Проверка Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 не найден!${NC}"
        echo "Установите Python 3: sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}⚠️ pip3 не найден, устанавливаю...${NC}"
        sudo apt update
        sudo apt install python3-pip -y
    fi
    
    echo -e "${GREEN}✅ Все требования выполнены${NC}"
}

get_credentials() {
    echo -e "${YELLOW}📝 Введите данные для бота:${NC}"
    echo
    
    # Получение токена
    while true; do
        read -p "🔑 Токен бота (от @BotFather): " BOT_TOKEN
        if [[ -z "$BOT_TOKEN" ]]; then
            echo -e "${RED}❌ Токен не может быть пустым!${NC}"
            continue
        fi
        
        if [[ "$BOT_TOKEN" != *":"* ]]; then
            echo -e "${RED}❌ Неверный формат токена!${NC}"
            continue
        fi
        
        break
    done
    
    # Получение Admin ID
    while true; do
        read -p "👤 Ваш Telegram ID (от @userinfobot): " ADMIN_ID
        if [[ -z "$ADMIN_ID" ]]; then
            echo -e "${RED}❌ Admin ID не может быть пустым!${NC}"
            continue
        fi
        
        if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}❌ Admin ID должен содержать только цифры!${NC}"
            continue
        fi
        
        break
    done
    
    echo -e "${GREEN}✅ Данные получены${NC}"
}

create_env() {
    echo -e "${YELLOW}📄 Создание конфигурации...${NC}"
    
    cat > .env << EOF
# Telegram Bot Configuration
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID

# Database settings
DB_PATH=data/bot.db

# Timezone
TIMEZONE=Europe/Moscow

# Debug mode
DEBUG=False

# Notifications
ENABLE_NOTIFICATIONS=True
DAILY_SUMMARY_TIME=19:00
REMINDER_TIME=20:30

# Auto-restart settings
MAX_RESTARTS=50
RESTART_INTERVAL=300

# PythonAnywhere settings
PYTHONANYWHERE_MODE=True
HEALTH_CHECK_INTERVAL=21600
AUTO_RESTART_INTERVAL=3300
SEND_ERROR_NOTIFICATIONS=True
SEND_HEALTH_REPORTS=True
EOF
    
    echo -e "${GREEN}✅ Конфигурация создана${NC}"
}

install_deps() {
    echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
    
    # Создание виртуального окружения
    python3 -m venv venv_bot
    source venv_bot/bin/activate
    
    # Установка зависимостей
    pip install -q --upgrade pip
    pip install -q aiogram aiosqlite python-dotenv aioschedule psutil pytz schedule
    
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
}

setup_dirs() {
    echo -e "${YELLOW}📁 Создание директорий...${NC}"
    
    mkdir -p logs data exports config backups monitoring
    touch logs/bot.log logs/monitoring.log logs/health.log
    
    echo -e "${GREEN}✅ Директории созданы${NC}"
}

create_monitoring_scripts() {
    echo -e "${YELLOW}🔍 Создание скриптов мониторинга...${NC}"
    
    # Скрипт автоперезапуска каждые 55 минут
    cat > monitoring/auto_restart.py << 'EOF'
#!/usr/bin/env python3
"""
Автоперезапуск бота каждые 55 минут для PythonAnywhere free
"""

import os
import sys
import time
import signal
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)

async def send_notification(message):
    """Отправка уведомления админу"""
    try:
        from aiogram import Bot
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if bot_token and admin_id:
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=admin_id,
                text=f"🔄 AutoRestart: {message}",
                parse_mode='HTML'
            )
            await bot.session.close()
    except Exception as e:
        logging.error(f"Ошибка отправки уведомления: {e}")

def find_bot_process():
    """Найти процесс бота"""
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                return proc.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

async def restart_bot():
    """Перезапуск бота"""
    try:
        # Найти и завершить процесс
        pid = find_bot_process()
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                logging.info(f"Процесс {pid} завершен")
            except ProcessLookupError:
                pass
        
        # Запуск нового процесса
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.system(f"cd {project_dir} && source venv_bot/bin/activate && nohup python3 main.py > logs/bot.log 2>&1 &")
        
        await send_notification("Бот перезапущен успешно")
        logging.info("Бот перезапущен")
        
    except Exception as e:
        error_msg = f"Ошибка перезапуска: {e}"
        logging.error(error_msg)
        await send_notification(error_msg)

if __name__ == "__main__":
    asyncio.run(restart_bot())
EOF

    # Скрипт проверки здоровья каждые 6 часов
    cat > monitoring/health_check.py << 'EOF'
#!/usr/bin/env python3
"""
Проверка здоровья бота каждые 6 часов
"""

import os
import sys
import time
import asyncio
import logging
import psutil
from datetime import datetime
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/health.log'),
        logging.StreamHandler()
    ]
)

async def send_health_report(status, details):
    """Отправка отчета о здоровье"""
    try:
        from aiogram import Bot
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if bot_token and admin_id:
            bot = Bot(token=bot_token)
            
            icon = "✅" if status == "healthy" else "❌"
            report = f"""
{icon} <b>Отчет о здоровье бота</b>

📊 <b>Статус:</b> {status}
🕐 <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 <b>Детали:</b>
{details}
"""
            
            await bot.send_message(
                chat_id=admin_id,
                text=report,
                parse_mode='HTML'
            )
            await bot.session.close()
    except Exception as e:
        logging.error(f"Ошибка отправки отчета: {e}")

def check_bot_process():
    """Проверка процесса бота"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            if proc.info['cmdline'] and 'main.py' in ' '.join(proc.info['cmdline']):
                return {
                    'pid': proc.info['pid'],
                    'memory': proc.info['memory_info'].rss / 1024 / 1024,  # MB
                    'cpu': proc.info['cpu_percent']
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return None

def check_log_file():
    """Проверка лог файла"""
    try:
        log_file = Path('logs/bot.log')
        if log_file.exists():
            size = log_file.stat().st_size / 1024  # KB
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            return {
                'size': size,
                'last_modified': modified,
                'exists': True
            }
    except Exception as e:
        logging.error(f"Ошибка проверки лог файла: {e}")
    return {'exists': False}

def check_database():
    """Проверка базы данных"""
    try:
        db_file = Path('data/bot.db')
        if db_file.exists():
            size = db_file.stat().st_size / 1024  # KB
            return {
                'size': size,
                'exists': True
            }
    except Exception as e:
        logging.error(f"Ошибка проверки БД: {e}")
    return {'exists': False}

async def health_check():
    """Основная проверка здоровья"""
    try:
        # Проверка процесса
        process_info = check_bot_process()
        
        # Проверка лог файла
        log_info = check_log_file()
        
        # Проверка базы данных
        db_info = check_database()
        
        # Системная информация
        system_info = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
        
        # Формирование отчета
        status = "healthy" if process_info else "unhealthy"
        
        details = f"""
🔧 <b>Процесс:</b> {'✅ Работает' if process_info else '❌ Не найден'}
{f"   - PID: {process_info['pid']}" if process_info else ""}
{f"   - Память: {process_info['memory']:.1f} MB" if process_info else ""}
{f"   - CPU: {process_info['cpu']:.1f}%" if process_info else ""}

📝 <b>Лог файл:</b> {'✅ Найден' if log_info['exists'] else '❌ Отсутствует'}
{f"   - Размер: {log_info['size']:.1f} KB" if log_info['exists'] else ""}
{f"   - Изменен: {log_info['last_modified']}" if log_info['exists'] else ""}

💾 <b>База данных:</b> {'✅ Найдена' if db_info['exists'] else '❌ Отсутствует'}
{f"   - Размер: {db_info['size']:.1f} KB" if db_info['exists'] else ""}

🖥️ <b>Система:</b>
   - CPU: {system_info['cpu_percent']:.1f}%
   - Память: {system_info['memory_percent']:.1f}%
   - Диск: {system_info['disk_percent']:.1f}%
"""
        
        await send_health_report(status, details)
        logging.info(f"Проверка здоровья завершена: {status}")
        
        # Если процесс не найден, попытаться перезапустить
        if not process_info:
            logging.warning("Процесс бота не найден, попытка перезапуска...")
            project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.system(f"cd {project_dir} && python3 monitoring/auto_restart.py")
        
    except Exception as e:
        error_msg = f"Ошибка проверки здоровья: {e}"
        logging.error(error_msg)
        await send_health_report("error", error_msg)

if __name__ == "__main__":
    asyncio.run(health_check())
EOF

    # Скрипт ошибок с уведомлениями
    cat > monitoring/error_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
Мониторинг ошибок в логах и отправка уведомлений
"""

import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

async def send_error_notification(error_text):
    """Отправка уведомления об ошибке"""
    try:
        from aiogram import Bot
        from dotenv import load_dotenv
        
        load_dotenv()
        bot_token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if bot_token and admin_id:
            bot = Bot(token=bot_token)
            
            message = f"""
🚨 <b>ОШИБКА БОТА</b>

🕐 <b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

❌ <b>Ошибка:</b>
<code>{error_text[:1000]}</code>
"""
            
            await bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='HTML'
            )
            await bot.session.close()
    except Exception as e:
        print(f"Ошибка отправки уведомления об ошибке: {e}")

def monitor_errors():
    """Мониторинг ошибок в логах"""
    log_file = Path('logs/bot.log')
    
    if not log_file.exists():
        return
    
    try:
        # Читаем последние строки лога
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Ищем ошибки в последних 50 строках
        for line in lines[-50:]:
            if any(word in line.lower() for word in ['error', 'exception', 'traceback', 'failed']):
                asyncio.run(send_error_notification(line.strip()))
                break
                
    except Exception as e:
        print(f"Ошибка мониторинга: {e}")

if __name__ == "__main__":
    monitor_errors()
EOF

    # Делаем скрипты исполняемыми
    chmod +x monitoring/*.py
    
    echo -e "${GREEN}✅ Скрипты мониторинга созданы${NC}"
}

setup_pythonanywhere_tasks() {
    echo -e "${YELLOW}🔧 Настройка задач PythonAnywhere...${NC}"
    
    # Создание главного скрипта для daily task
    cat > monitoring/daily_task.py << 'EOF'
#!/usr/bin/env python3
"""
Главный скрипт для ежедневной задачи PythonAnywhere
Запускает мониторинг и автоперезапуск
"""

import os
import sys
import time
import asyncio
import schedule
import threading
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию в PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_health_check():
    """Запуск проверки здоровья"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.system(f"cd {project_dir} && python3 monitoring/health_check.py")

def run_auto_restart():
    """Запуск автоперезапуска"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.system(f"cd {project_dir} && python3 monitoring/auto_restart.py")

def run_error_monitor():
    """Запуск мониторинга ошибок"""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.system(f"cd {project_dir} && python3 monitoring/error_monitor.py")

def setup_scheduler():
    """Настройка расписания"""
    # Проверка здоровья каждые 6 часов
    schedule.every(6).hours.do(run_health_check)
    
    # Автоперезапуск каждые 55 минут
    schedule.every(55).minutes.do(run_auto_restart)
    
    # Мониторинг ошибок каждые 30 минут
    schedule.every(30).minutes.do(run_error_monitor)
    
    print(f"🚀 Планировщик запущен: {datetime.now()}")
    print("📅 Расписание:")
    print("   - Проверка здоровья: каждые 6 часов")
    print("   - Автоперезапуск: каждые 55 минут")
    print("   - Мониторинг ошибок: каждые 30 минут")
    
    # Запуск начальных проверок
    run_health_check()
    run_auto_restart()
    
    # Основной цикл
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту

if __name__ == "__main__":
    setup_scheduler()
EOF

    # Инструкция по настройке PythonAnywhere
    cat > monitoring/PYTHONANYWHERE_SETUP.md << 'EOF'
# 🚀 Настройка PythonAnywhere Free

## Шаг 1: Настройка Daily Task

1. Перейдите в **Dashboard** -> **Tasks**
2. Нажмите **Create a new task**
3. Заполните поля:
   - **Command**: `python3 /home/yourusername/yourproject/monitoring/daily_task.py`
   - **Frequency**: `Daily`
   - **Time**: `00:00` (полночь)
   
⚠️ **Важно**: Замените `/home/yourusername/yourproject` на полный путь к вашему проекту!

## Шаг 2: Проверка работы

После создания задачи:
1. Бот будет автоматически перезапускаться каждые 55 минут
2. Проверка здоровья будет выполняться каждые 6 часов
3. Уведомления об ошибках будут приходить в Telegram

## Шаг 3: Мониторинг логов

Проверяйте логи:
- `logs/bot.log` - основной лог бота
- `logs/monitoring.log` - лог мониторинга
- `logs/health.log` - лог проверки здоровья

## Важные моменты:

⚠️ **Ограничения Free аккаунта:**
- Только одна Daily Task
- Время выполнения ограничено
- Нет фонового выполнения

✅ **Преимущества данного решения:**
- Автоматический перезапуск
- Мониторинг здоровья
- Уведомления об ошибках
- Работа в рамках ограничений Free

## Команды для отладки:

```bash
# Запуск проверки здоровья
python3 monitoring/health_check.py

# Запуск автоперезапуска
python3 monitoring/auto_restart.py

# Запуск мониторинга ошибок
python3 monitoring/error_monitor.py

# Запуск главного планировщика
python3 monitoring/daily_task.py
```
EOF

    chmod +x monitoring/daily_task.py
    
    echo -e "${GREEN}✅ Задачи PythonAnywhere настроены${NC}"
    echo -e "${BLUE}📋 Инструкция: monitoring/PYTHONANYWHERE_SETUP.md${NC}"
}

test_bot() {
    echo -e "${YELLOW}🔍 Тестирование бота...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Тест подключения
    python3 -c "
import asyncio
from aiogram import Bot
import sys

async def test():
    bot = Bot(token='$BOT_TOKEN')
    try:
        me = await bot.get_me()
        print('✅ Бот подключен: @' + me.username + ' (' + me.first_name + ')')
        await bot.session.close()
        return True
    except Exception as e:
        print('❌ Ошибка:', e)
        await bot.session.close()
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Тест прошел успешно${NC}"
    else
        echo -e "${RED}❌ Тест не прошел. Проверьте токен.${NC}"
        exit 1
    fi
}

create_service() {
    echo -e "${YELLOW}🔧 Настройка автозапуска...${NC}"
    
    # Создание systemd сервиса
    SERVICE_FILE="/etc/systemd/system/telegram-bot.service"
    
    if [ "$EUID" -eq 0 ]; then
        # Если запущено с sudo
        cat > $SERVICE_FILE << EOF
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$PWD
ExecStart=$PWD/venv_bot/bin/python $PWD/main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable telegram-bot
        echo -e "${GREEN}✅ Сервис создан${NC}"
    else
        # Если запущено без sudo
        echo -e "${YELLOW}⚠️ Для автозапуска нужны права администратора${NC}"
        echo "Запустите: sudo systemctl enable telegram-bot"
    fi
}

start_bot() {
    echo -e "${YELLOW}🚀 Запуск бота...${NC}"
    
    # Попытка запуска через systemd
    if systemctl start telegram-bot 2>/dev/null; then
        echo -e "${GREEN}✅ Бот запущен через systemd${NC}"
        echo -e "${BLUE}📊 Статус: sudo systemctl status telegram-bot${NC}"
    else
        # Запуск в фоновом режиме
        echo -e "${YELLOW}⚠️ Запуск в фоновом режиме...${NC}"
        source venv_bot/bin/activate
        nohup python3 main.py > logs/bot.log 2>&1 &
        sleep 2
        echo -e "${GREEN}✅ Бот запущен в фоновом режиме${NC}"
    fi
}

show_success() {
    echo
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}✅ Бот настроен и запущен${NC}"
    echo -e "${GREEN}✅ Работает в режиме 24/7${NC}"
    echo -e "${GREEN}✅ Все зависимости установлены${NC}"
    echo -e "${GREEN}✅ Мониторинг и автоперезапуск настроены${NC}"
    echo
    echo -e "${BLUE}📋 Полезные команды:${NC}"
    echo "   source venv_bot/bin/activate && python3 main.py"
    echo "   tail -f logs/bot.log"
    echo "   tail -f logs/monitoring.log"
    echo "   tail -f logs/health.log"
    echo "   sudo systemctl status telegram-bot"
    echo
    echo -e "${BLUE}🔧 Мониторинг:${NC}"
    echo "   python3 monitoring/health_check.py"
    echo "   python3 monitoring/auto_restart.py"
    echo "   python3 monitoring/daily_task.py"
    echo
    echo -e "${YELLOW}📋 Для PythonAnywhere Free:${NC}"
    echo "   Настройте Daily Task: monitoring/PYTHONANYWHERE_SETUP.md"
    echo "   Команда: python3 $PWD/monitoring/daily_task.py"
    echo
    echo -e "${BLUE}📱 Найдите бота в Telegram и отправьте /start${NC}"
    echo -e "${GREEN}============================================${NC}"
}

# Основная функция
main() {
    print_header
    check_requirements
    get_credentials
    create_env
    install_deps
    setup_dirs
    create_monitoring_scripts
    setup_pythonanywhere_tasks
    test_bot
    create_service
    start_bot
    show_success
}

# Проверка на повторный запуск
if [ -f ".last_run" ]; then
    LAST_RUN=$(cat .last_run)
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - LAST_RUN))
    
    if [ $TIME_DIFF -lt 86400 ]; then
        echo -e "${YELLOW}⏰ Ограничение: можно запускать только раз в сутки${NC}"
        echo -e "${YELLOW}🕐 Осталось: $(((86400 - TIME_DIFF) / 3600)) часов${NC}"
        read -p "❓ Игнорировать ограничение? (y/N): " FORCE
        if [ "$FORCE" != "y" ]; then
            echo -e "${RED}❌ Установка отменена${NC}"
            exit 1
        fi
    fi
fi

# Запись времени запуска
date +%s > .last_run

# Запуск основной функции
main