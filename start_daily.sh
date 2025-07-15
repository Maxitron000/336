#!/bin/bash
# 🚀 Скрипт запуска бота для PythonAnywhere

# Переходим в директорию проекта
cd /workspace

# Активируем виртуальное окружение
source venv_bot/bin/activate

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Пожалуйста, отредактируйте файл .env и добавьте:"
    echo "   - BOT_TOKEN=ваш_токен_бота"
    echo "   - ADMIN_IDS=ваш_telegram_id"
    exit 1
fi

# Запускаем бота
echo "🤖 Запуск бота..."
python start.py