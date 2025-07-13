#!/bin/bash

# Скрипт запуска Telegram бота на aiogram
# Для работы на PythonAnywhere и других серверах

echo "🚀 Запуск Telegram бота..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден"
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python версия: $PYTHON_VERSION"

# Переходим в директорию бота
cd "$(dirname "$0")"

# Создаем необходимые папки
mkdir -p logs data exports config

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt не найден, устанавливаем основные пакеты..."
    pip install aiogram==2.25.1 python-dotenv==1.0.0 aioschedule==0.5.2 pytz==2023.3 aiosqlite==0.19.0
fi

# Проверяем наличие файла .env
if [ ! -f ".env" ]; then
    echo "⚠️ Файл .env не найден!"
    echo "Создайте файл .env с настройками:"
    echo "BOT_TOKEN=ваш_токен_бота"
    echo "ADMIN_IDS=ваш_telegram_id"
    echo "TIMEZONE=Europe/Kaliningrad"
    exit 1
fi

# Проверяем токен бота
if ! grep -q "BOT_TOKEN=" .env; then
    echo "❌ BOT_TOKEN не найден в .env"
    exit 1
fi

echo "✅ Все проверки пройдены"

# Запускаем бота
echo "🤖 Запуск бота..."
python3 main.py

# Если бот упал, ждем и перезапускаем
echo "🔄 Перезапуск через 30 секунд..."
sleep 30
exec "$0"