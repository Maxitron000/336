#!/bin/bash
#
# 🧹 ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ ПРОЕКТА
#

echo "🧹 Очистка временных файлов..."

# Удаляем виртуальное окружение (пользователь создаст новое)
if [[ -d "venv_bot" ]]; then
    rm -rf venv_bot
    echo "✅ Виртуальное окружение удалено"
fi

# Удаляем временные файлы
rm -f test_connection_temp.py test_bot_temp.py test_ssl.py

# Очищаем логи
rm -rf logs/
mkdir -p logs
echo "✅ Логи очищены"

# Очищаем данные
rm -rf data/
mkdir -p data
echo "✅ Данные очищены"

# Очищаем экспорты
rm -rf exports/
mkdir -p exports
echo "✅ Экспорты очищены"

# Очищаем кеш Python
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✅ Кеш Python очищен"

echo
echo "🎉 Проект готов к распространению!"
echo "💡 Пользователь может запустить: ./quick_start.sh"