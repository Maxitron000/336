#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Запуск Telegram-бота учёта личного состава...${NC}"
echo "================================================================"

# Проверка файла .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Файл .env не найден!${NC}"
    echo -e "${YELLOW}📝 Создайте файл .env на основе .env.example${NC}"
    exit 1
fi

# Проверка зависимостей
echo -e "${CYAN}📦 Проверка зависимостей...${NC}"
if ! python3 -c "import telegram, pandas, openpyxl" 2>/dev/null; then
    echo -e "${RED}❌ Не все зависимости установлены!${NC}"
    echo -e "${YELLOW}💡 Выполните: pip install -r requirements.txt${NC}"
    exit 1
fi

# Создание необходимых папок
echo -e "${CYAN}📁 Создание структуры папок...${NC}"
mkdir -p data config logs exports

# Проверка токена
echo -e "${CYAN}🔑 Проверка токена бота...${NC}"
source .env
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo -e "${RED}❌ TELEGRAM_BOT_TOKEN не задан в .env файле!${NC}"
    exit 1
fi

# Инициализация базы данных
echo -e "${CYAN}🗄️ Инициализация базы данных...${NC}"
python3 -c "from database import init_db; init_db(); print('✅ База данных готова')"

# Проверка файла локаций
if [ ! -f "data/locations.json" ]; then
    echo -e "${YELLOW}⚠️ Создание файла локаций...${NC}"
    python3 -c "from utils import load_locations; load_locations(); print('✅ Файл локаций создан')"
fi

echo "================================================================"
echo -e "${GREEN}🚀 Запуск бота...${NC}"
echo -e "${PURPLE}📊 Логи сохраняются в logs/bot.log${NC}"
echo -e "${PURPLE}📁 База данных: data/personnel.db${NC}"
echo -e "${PURPLE}🔧 Локации: data/locations.json${NC}"
echo -e "${PURPLE}💬 Уведомления: config/notifications.json${NC}"
echo "================================================================"

# Запуск бота
python3 main.py

# Если бот завершился
echo -e "${RED}⚠️ Бот завершил работу!${NC}"
echo -e "${YELLOW}📋 Последние строки лога:${NC}"
tail -10 logs/bot.log