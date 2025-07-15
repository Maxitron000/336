#!/bin/bash
# Скрипт запуска бота на PythonAnywhere

# Переходим в директорию проекта
cd /home/yourusername/mysite

# Активируем виртуальное окружение Python 3.10
source venv_bot_310/bin/activate

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Настройте файл .env перед запуском"
    exit 1
fi

# Создаем папки для логов если их нет
mkdir -p logs
mkdir -p data

# Проверяем базу данных
echo "🗄️ Проверка базы данных..."
python check_database.py

# Запускаем бота
echo "🤖 Запуск бота..."
python main.py