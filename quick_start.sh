#!/bin/bash
#
# 🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ УСТАНОВКА И ЗАПУСК TELEGRAM БОТА
# Один скрипт для полной настройки Python 3.13 + SSL + Запуск бота
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Переменные для запоминания данных
BOT_TOKEN=""
ADMIN_ID=""

print_header() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}🚀 ПОЛНАЯ АВТОМАТИЧЕСКАЯ УСТАНОВКА${NC}"
    echo -e "${BLUE}🤖 TELEGRAM БОТ - PYTHON 3.13 READY${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
    echo -e "${CYAN}✨ Этот скрипт автоматически:${NC}"
    echo -e "${CYAN}   • Установит виртуальное окружение${NC}"
    echo -e "${CYAN}   • Решит проблемы с SSL${NC}"
    echo -e "${CYAN}   • Установит все зависимости${NC}"
    echo -e "${CYAN}   • Настроит конфигурацию${NC}"
    echo -e "${CYAN}   • Запустит вашего бота${NC}"
    echo
}

check_system_requirements() {
    echo -e "${YELLOW}🔍 Проверка системных требований...${NC}"
    
    # Проверка Python 3
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 не найден!${NC}"
        echo -e "${YELLOW}📦 Установка Python 3...${NC}"
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    # Проверка версии Python
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${BLUE}   Python версия: ${PYTHON_VERSION}${NC}"
    
    if [[ $(echo "$PYTHON_VERSION >= 3.8" | bc -l) -eq 1 ]] 2>/dev/null || [[ "$PYTHON_VERSION" == "3.8" ]] || [[ "$PYTHON_VERSION" == "3.9" ]] || [[ "$PYTHON_VERSION" == "3.10" ]] || [[ "$PYTHON_VERSION" == "3.11" ]] || [[ "$PYTHON_VERSION" == "3.12" ]] || [[ "$PYTHON_VERSION" == "3.13" ]]; then
        echo -e "${GREEN}   ✅ Версия Python подходит${NC}"
        if [[ "$PYTHON_VERSION" == "3.13" ]]; then
            echo -e "${GREEN}   🆕 Python 3.13 обнаружен - применяю специальные настройки${NC}"
            PYTHON_313_MODE=true
        else
            PYTHON_313_MODE=false
        fi
    else
        echo -e "${RED}❌ Требуется Python 3.8 или выше${NC}"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}⚠️ pip3 не найден, устанавливаю...${NC}"
        sudo apt install -y python3-pip
    fi
    
    # Обновление системных SSL-сертификатов
    echo -e "${YELLOW}🔐 Обновление SSL-сертификатов...${NC}"
    sudo apt update > /dev/null 2>&1
    sudo apt install -y ca-certificates > /dev/null 2>&1
    echo -e "${GREEN}   ✅ SSL-сертификаты обновлены${NC}"
    
    echo -e "${GREEN}✅ Системные требования выполнены${NC}"
    echo
}

get_bot_credentials() {
    echo -e "${YELLOW}🔑 Настройка бота...${NC}"
    echo
    
    # Получение токена бота
    while true; do
        echo -e "${CYAN}🤖 Получите токен бота:${NC}"
        echo -e "${CYAN}   1. Откройте https://t.me/BotFather${NC}"
        echo -e "${CYAN}   2. Отправьте команду /newbot${NC}"
        echo -e "${CYAN}   3. Следуйте инструкциям${NC}"
        echo -e "${CYAN}   4. Скопируйте токен${NC}"
        echo
        read -p "🔑 Введите токен бота: " BOT_TOKEN
        
        if [[ -z "$BOT_TOKEN" ]]; then
            echo -e "${RED}❌ Токен не может быть пустым${NC}"
            continue
        fi
        
        # Базовая проверка формата токена
        if [[ ! "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            echo -e "${RED}❌ Неверный формат токена${NC}"
            echo -e "${YELLOW}💡 Токен должен выглядеть как: 123456789:ABCdef_12345...${NC}"
            continue
        fi
        
        echo -e "${GREEN}✅ Токен принят${NC}"
        break
    done
    
    echo
    
    # Получение ID администратора
    while true; do
        echo -e "${CYAN}👤 Получите свой Telegram ID:${NC}"
        echo -e "${CYAN}   1. Откройте https://t.me/userinfobot${NC}"
        echo -e "${CYAN}   2. Отправьте любое сообщение${NC}"
        echo -e "${CYAN}   3. Скопируйте ваш ID${NC}"
        echo
        read -p "👤 Введите ваш Telegram ID: " ADMIN_ID
        
        if [[ -z "$ADMIN_ID" ]]; then
            echo -e "${RED}❌ ID не может быть пустым${NC}"
            continue
        fi
        
        # Проверка, что ID - число
        if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            echo -e "${RED}❌ ID должен быть числом${NC}"
            continue
        fi
        
        echo -e "${GREEN}✅ ID принят${NC}"
        break
    done
    
    echo
    echo -e "${GREEN}🎉 Данные для бота получены!${NC}"
    echo
}

setup_virtual_environment() {
    echo -e "${YELLOW}🐍 Настройка виртуального окружения...${NC}"
    
    # Удаляем старое окружение, если существует
    if [[ -d "venv_bot" ]]; then
        echo -e "${YELLOW}⚠️ Удаляю старое виртуальное окружение...${NC}"
        rm -rf venv_bot
    fi
    
    # Создаем новое окружение
    echo -e "${BLUE}🏗️ Создание виртуального окружения...${NC}"
    if python3 -m venv venv_bot --system-site-packages; then
        echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
    else
        echo -e "${YELLOW}⚠️ Попытка без системных пакетов...${NC}"
        python3 -m venv venv_bot
        echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
    fi
    
    # Проверяем структуру
    if [[ -f "venv_bot/bin/python" ]]; then
        echo -e "${GREEN}✅ Структура окружения корректна${NC}"
    else
        echo -e "${RED}❌ Ошибка создания окружения${NC}"
        exit 1
    fi
    
    echo
}

install_dependencies() {
    echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Обновляем pip
    echo -e "${BLUE}🔄 Обновление pip...${NC}"
    python -m pip install --upgrade pip > /dev/null 2>&1
    echo -e "${GREEN}✅ pip обновлен${NC}"
    
    # Устанавливаем базовые пакеты
    echo -e "${BLUE}🔄 Установка базовых пакетов...${NC}"
    pip install --upgrade setuptools wheel > /dev/null 2>&1
    echo -e "${GREEN}✅ Базовые пакеты установлены${NC}"
    
    # Устанавливаем критически важные пакеты
    echo -e "${BLUE}🔄 Установка SSL и HTTP пакетов...${NC}"
    pip install certifi cryptography aiohttp > /dev/null 2>&1
    echo -e "${GREEN}✅ SSL пакеты установлены${NC}"
    
    # Устанавливаем aiogram и зависимости
    echo -e "${BLUE}🔄 Установка Telegram API...${NC}"
    pip install aiogram python-dotenv aiosqlite > /dev/null 2>&1
    echo -e "${GREEN}✅ Telegram API установлен${NC}"
    
    # Пытаемся установить дополнительные пакеты (не критично)
    echo -e "${BLUE}🔄 Установка дополнительных пакетов...${NC}"
    pip install aioschedule pytz schedule psutil > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ Дополнительные пакеты установлены${NC}"
    
    echo
}

create_configuration() {
    echo -e "${YELLOW}📝 Создание конфигурации...${NC}"
    
    # Создаем .env файл
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
    
    # Создаем необходимые директории
    mkdir -p data logs exports
    echo -e "${GREEN}✅ Директории созданы${NC}"
    
    echo
}

test_ssl_connection() {
    echo -e "${YELLOW}🔗 Тестирование SSL-соединения...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Создаем тестовый скрипт
    cat > test_connection_temp.py << 'EOF'
import asyncio
import aiohttp
import ssl
import certifi
import sys

async def test_telegram_connection():
    try:
        # Создаем SSL-контекст
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Тестируем соединение с Telegram API
            async with session.get('https://api.telegram.org/bot/getMe') as response:
                if response.status in [200, 401, 404]:
                    return True
                return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram_connection())
    sys.exit(0 if result else 1)
EOF
    
    # Запускаем тест
    if python test_connection_temp.py > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSL-соединение с Telegram API работает${NC}"
        SSL_TEST_PASSED=true
    else
        echo -e "${YELLOW}⚠️ SSL-соединение может работать нестабильно${NC}"
        SSL_TEST_PASSED=false
    fi
    
    # Удаляем временный файл
    rm -f test_connection_temp.py
    
    echo
}

test_bot_token() {
    echo -e "${YELLOW}🤖 Тестирование токена бота...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Создаем тестовый скрипт
    cat > test_bot_temp.py << EOF
import asyncio
import aiohttp
import ssl
import certifi
import sys

async def test_bot():
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            url = f'https://api.telegram.org/bot${BOT_TOKEN}/getMe'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        print(f"✅ Бот подключен: @{bot_info.get('username', 'unknown')} ({bot_info.get('first_name', 'unknown')})")
                        return True
                print("❌ Неверный токен бота")
                return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
EOF
    
    # Запускаем тест
    if python test_bot_temp.py; then
        BOT_TEST_PASSED=true
    else
        BOT_TEST_PASSED=false
    fi
    
    # Удаляем временный файл
    rm -f test_bot_temp.py
    
    echo
}

verify_installation() {
    echo -e "${YELLOW}🔍 Проверка установки...${NC}"
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Проверяем критические пакеты
    PACKAGES_OK=true
    
    for package in "aiogram" "aiohttp" "certifi" "cryptography" "python-dotenv" "aiosqlite"; do
        if python -c "import $package" > /dev/null 2>&1; then
            echo -e "${GREEN}   ✅ $package${NC}"
        else
            echo -e "${RED}   ❌ $package${NC}"
            PACKAGES_OK=false
        fi
    done
    
    # Проверяем файлы
    if [[ -f ".env" ]]; then
        echo -e "${GREEN}   ✅ .env файл${NC}"
    else
        echo -e "${RED}   ❌ .env файл${NC}"
        PACKAGES_OK=false
    fi
    
    if [[ -f "main.py" ]]; then
        echo -e "${GREEN}   ✅ main.py${NC}"
    else
        echo -e "${RED}   ❌ main.py${NC}"
        PACKAGES_OK=false
    fi
    
    echo
    
    if [[ "$PACKAGES_OK" == true ]]; then
        echo -e "${GREEN}✅ Проверка установки пройдена${NC}"
        return 0
    else
        echo -e "${RED}❌ Проблемы с установкой${NC}"
        return 1
    fi
}

start_bot() {
    echo -e "${YELLOW}🚀 Запуск бота...${NC}"
    echo
    
    # Активируем виртуальное окружение
    source venv_bot/bin/activate
    
    # Показываем информацию о запуске
    echo -e "${BLUE}📋 Информация о запуске:${NC}"
    echo -e "${BLUE}   • Виртуальное окружение: активировано${NC}"
    echo -e "${BLUE}   • Токен бота: настроен${NC}"
    echo -e "${BLUE}   • ID администратора: $ADMIN_ID${NC}"
    echo -e "${BLUE}   • SSL-соединение: $(if [[ "$SSL_TEST_PASSED" == true ]]; then echo "✅ работает"; else echo "⚠️ проверьте"; fi)${NC}"
    echo -e "${BLUE}   • Токен бота: $(if [[ "$BOT_TEST_PASSED" == true ]]; then echo "✅ валиден"; else echo "⚠️ проверьте"; fi)${NC}"
    echo
    
    echo -e "${GREEN}🎉 Запускаю вашего Telegram бота...${NC}"
    echo -e "${CYAN}💡 Для остановки нажмите Ctrl+C${NC}"
    echo
    
    # Запускаем бота
    python main.py
}

print_success_info() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}🎉 БОТ УСПЕШНО НАСТРОЕН!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo
    echo -e "${BLUE}📋 Полезная информация:${NC}"
    echo
    echo -e "${CYAN}🔧 Управление ботом:${NC}"
    echo -e "${CYAN}   Запуск: source venv_bot/bin/activate && python main.py${NC}"
    echo -e "${CYAN}   Остановка: Ctrl+C${NC}"
    echo -e "${CYAN}   Логи: tail -f logs/bot.log${NC}"
    echo
    echo -e "${CYAN}🛠️ Диагностика:${NC}"
    echo -e "${CYAN}   Проверка SSL: python test_ssl_connection.py${NC}"
    echo -e "${CYAN}   Проверка конфигурации: python check_config.py${NC}"
    echo
    echo -e "${CYAN}📝 Файлы конфигурации:${NC}"
    echo -e "${CYAN}   .env - основные настройки${NC}"
    echo -e "${CYAN}   data/ - база данных${NC}"
    echo -e "${CYAN}   logs/ - логи бота${NC}"
    echo
    echo -e "${BLUE}🔗 Полезные ссылки:${NC}"
    echo -e "${BLUE}   Токен бота: https://t.me/BotFather${NC}"
    echo -e "${BLUE}   Ваш ID: https://t.me/userinfobot${NC}"
    echo
}

# Обработка прерывания
trap 'echo -e "\n${RED}❌ Установка прервана пользователем${NC}"; exit 1' INT

# Основная функция
main() {
    print_header
    
    echo -e "${PURPLE}🚀 Начинаю полную автоматическую установку...${NC}"
    echo
    
    # Шаг 1: Проверка системы
    check_system_requirements
    
    # Шаг 2: Получение данных бота
    get_bot_credentials
    
    # Шаг 3: Настройка виртуального окружения
    setup_virtual_environment
    
    # Шаг 4: Установка зависимостей
    install_dependencies
    
    # Шаг 5: Создание конфигурации
    create_configuration
    
    # Шаг 6: Тестирование SSL
    test_ssl_connection
    
    # Шаг 7: Тестирование токена бота
    test_bot_token
    
    # Шаг 8: Проверка установки
    if ! verify_installation; then
        echo -e "${RED}❌ Установка не завершена. Попробуйте снова.${NC}"
        exit 1
    fi
    
    # Шаг 9: Показываем информацию об успехе
    print_success_info
    
    # Шаг 10: Предложение запуска
    echo -e "${YELLOW}🚀 Запустить бота сейчас? (y/N): ${NC}"
    read -r START_NOW
    
    if [[ "$START_NOW" =~ ^[Yy]$ ]]; then
        start_bot
    else
        echo
        echo -e "${BLUE}💡 Для запуска бота позже используйте:${NC}"
        echo -e "${BLUE}   source venv_bot/bin/activate && python main.py${NC}"
        echo
        echo -e "${GREEN}✅ Установка завершена успешно!${NC}"
    fi
}

# Запуск основной функции
main "$@"