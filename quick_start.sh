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
    pip install -q aiogram aiosqlite python-dotenv aioschedule psutil pytz
    
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
}

setup_dirs() {
    echo -e "${YELLOW}📁 Создание директорий...${NC}"
    
    mkdir -p logs data exports config backups
    touch logs/bot.log
    
    echo -e "${GREEN}✅ Директории созданы${NC}"
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
    echo
    echo -e "${BLUE}📋 Полезные команды:${NC}"
    echo "   source venv_bot/bin/activate && python3 main.py"
    echo "   tail -f logs/bot.log"
    echo "   sudo systemctl status telegram-bot"
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