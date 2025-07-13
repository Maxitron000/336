#!/bin/bash

# Скрипт для запуска Telegram бота

# Проверяем, что мы находимся в правильной директории
if [ ! -f "main.py" ]; then
    echo "❌ Файл main.py не найден. Запустите скрипт из корневой директории проекта."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден. Создайте его на основе .env.example"
    exit 1
fi

# Создаем необходимые директории
mkdir -p logs data exports config

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не установлен"
    exit 1
fi

# Устанавливаем зависимости
echo "� Устанавливаем зависимости..."
pip3 install -r requirements.txt

# Запускаем бота
echo "🚀 Запускаем бота..."
python3 main.py