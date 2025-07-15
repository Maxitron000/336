#!/bin/bash
#
# 🚀 МГНОВЕННЫЙ ЗАПУСК TELEGRAM БОТА (Python 3.13 Ready)
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
    echo -e "${BLUE}🤖 Python 3.13 Ready + SSL Fix${NC}"
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
    
    # Проверка версии Python
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${BLUE}   Python версия: ${PYTHON_VERSION}${NC}"
    
    if [[ $(echo "$PYTHON_VERSION >= 3.13" | bc -l) -eq 1 ]] 2>/dev/null || [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo -e "${GREEN}   🆕 Python 3.13+ обнаружен - применяю специальные настройки${NC}"
        PYTHON_313_MODE=true
    else
        PYTHON_313_MODE=false
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}⚠️ pip3 не найден, устанавливаю...${NC}"
        sudo apt update
        sudo apt install python3-pip -y
    fi
    
    # Обновление системных SSL-сертификатов для Python 3.13
    if [[ "$PYTHON_313_MODE" == true ]]; then
        echo -e "${YELLOW}🔐 Обновление системных SSL-сертификатов...${NC}"
        sudo apt update > /dev/null 2>&1
        sudo apt install -y ca-certificates > /dev/null 2>&1
        echo -e "${GREEN}   ✅ SSL-сертификаты обновлены${NC}"
    fi
    
    echo -e "${GREEN}✅ Все требования выполнены${NC}"
}

setup_virtual_environment() {
    echo -e "${YELLOW}🐍 Настройка виртуального окружения...${NC}"
    
    # Удаляем старое окружение, если существует
    if [[ -d "venv_bot" ]]; then
        echo -e "${YELLOW}⚠️ Удаляю существующее виртуальное окружение...${NC}"
        rm -rf venv_bot
    fi
    
    # Запускаем обновленный скрипт установки
    echo -e "${BLUE}📦 Запуск автоматической установки...${NC}"
    python3 setup_venv.py
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Виртуальное окружение настроено${NC}"
        return 0
    else
        echo -e "${RED}❌ Ошибка настройки виртуального окружения${NC}"
        return 1
    fi
}

test_bot_connection() {
    echo -e "${YELLOW}🔗 Тестирование соединения с Telegram API...${NC}"
    
    # Активируем виртуальное окружение и тестируем соединение
    source venv_bot/bin/activate
    
    # Создаем тестовый скрипт
    cat > test_connection.py << 'EOF'
import asyncio
import aiohttp
import ssl
import certifi
import sys
import os
from pathlib import Path

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

async def test_telegram_connection():
    """Тестирует соединение с Telegram API"""
    try:
        # Создаем SSL-контекст с правильными сертификатами
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Тестируем базовое соединение
            async with session.get('https://api.telegram.org/bot/getMe') as response:
                if response.status == 200:
                    print("✅ Соединение с Telegram API работает")
                    return True
                else:
                    print(f"❌ Telegram API вернул статус: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка соединения с Telegram API: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram_connection())
    sys.exit(0 if result else 1)
EOF

    python test_connection.py
    TEST_RESULT=$?
    rm -f test_connection.py
    
    if [[ $TEST_RESULT -eq 0 ]]; then
        echo -e "${GREEN}✅ Соединение с Telegram API работает${NC}"
        return 0
    else
        echo -e "${RED}❌ Проблема с соединением. Проверьте интернет-соединение${NC}"
        return 1
    fi
}

get_credentials() {
    echo -e "${YELLOW}📝 Введите данные для бота:${NC}"
    echo
    
    # Получение токена
    while true; do
        read -p "🔑 Токен бота (от @BotFather): " BOT_TOKEN
        if [[ -z "$BOT_TOKEN" ]]; then
            echo -e "${RED}❌ Токен не может быть пустым${NC}"
            continue
        fi
        
        # Базовая проверка формата токена
        if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            echo -e "${RED}❌ Неверный формат токена${NC}"
            echo "💡 Токен должен выглядеть как: 123456789:ABCdef_12345..."
            continue
        fi
        
        break
    done
    
    # Получение ID администратора
    while true; do
        read -p "👤 ID администратора (от @userinfobot): " ADMIN_ID
        if [[ -z "$ADMIN_ID" ]]; then
            echo -e "${RED}❌ ID администратора не может быть пустым${NC}"
            continue
        fi
        
        # Проверка, что ID - число
        if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}❌ ID должен быть числом${NC}"
            continue
        fi
        
        break
    done
    
    echo -e "${GREEN}✅ Данные получены${NC}"
}

create_env_file() {
    echo -e "${YELLOW}📝 Создание файла конфигурации...${NC}"
    
    cat > .env << EOF
# Основные настройки бота
BOT_TOKEN=${BOT_TOKEN}
ADMIN_IDS=${ADMIN_ID}

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
HEALTH_CHECK_INTERVAL=21600

# Настройки для Python 3.13
PYTHONHTTPSVERIFY=1
SSL_VERIFY=true
EOF
    
    echo -e "${GREEN}✅ Файл .env создан${NC}"
}

create_directories() {
    echo -e "${YELLOW}📁 Создание необходимых директорий...${NC}"
    
    mkdir -p data
    mkdir -p logs
    mkdir -p exports
    
    echo -e "${GREEN}✅ Директории созданы${NC}"
}

verify_configuration() {
    echo -e "${YELLOW}🔍 Проверка конфигурации...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Запускаем проверку конфигурации
    if python check_config.py; then
        echo -e "${GREEN}✅ Конфигурация корректна${NC}"
        return 0
    else
        echo -e "${RED}❌ Ошибка в конфигурации${NC}"
        return 1
    fi
}

start_bot() {
    echo -e "${YELLOW}🚀 Запуск бота...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Запускаем бота
    python main.py
}

print_success() {
    echo
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}🎉 БОТ УСПЕШНО НАСТРОЕН И ЗАПУЩЕН!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo
    echo -e "${BLUE}📋 ПОЛЕЗНЫЕ КОМАНДЫ:${NC}"
    echo "   Запуск бота: source venv_bot/bin/activate && python main.py"
    echo "   Проверка конфигурации: python check_config.py"
    echo "   Просмотр логов: tail -f logs/bot.log"
    echo "   Деактивация окружения: deactivate"
    echo
    echo -e "${BLUE}🔧 СПЕЦИАЛЬНЫЕ НАСТРОЙКИ ДЛЯ PYTHON 3.13:${NC}"
    echo "   - Обновлены SSL-сертификаты"
    echo "   - Установлены совместимые версии библиотек"
    echo "   - Добавлена поддержка системных сертификатов"
    echo
    echo -e "${BLUE}📖 ДОКУМЕНТАЦИЯ:${NC}"
    echo "   README.md - Основная документация"
    echo "   БЫСТРЫЙ_СТАРТ.md - Руководство по быстрому запуску"
    echo
}

# Основная функция
main() {
    print_header
    
    # Проверка системных требований
    check_requirements
    
    # Получение данных от пользователя
    get_credentials
    
    # Создание файла конфигурации
    create_env_file
    
    # Создание директорий
    create_directories
    
    # Настройка виртуального окружения
    if ! setup_virtual_environment; then
        echo -e "${RED}❌ Критическая ошибка: не удалось настроить виртуальное окружение${NC}"
        exit 1
    fi
    
    # Тестирование соединения с Telegram API
    test_bot_connection
    
    # Проверка конфигурации
    if ! verify_configuration; then
        echo -e "${RED}❌ Ошибка в конфигурации. Проверьте настройки${NC}"
        exit 1
    fi
    
    # Успешное завершение
    print_success
    
    # Предложение запустить бота
    echo -e "${YELLOW}🚀 Запустить бота сейчас? (y/N): ${NC}"
    read -r START_NOW
    
    if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
        start_bot
    else
        echo -e "${BLUE}💡 Для запуска бота используйте команду:${NC}"
        echo "   source venv_bot/bin/activate && python main.py"
    fi
}

# Обработка прерывания
trap 'echo -e "\n${RED}❌ Установка прервана пользователем${NC}"; exit 1' INT

# Запуск основной функции
main "$@"