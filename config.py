# config.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен твоего бота из переменных окружения
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения!")

# Пути к файлам
ADMINS_JSON = "data/admins.json"
NOTIFICATIONS_JSON = "config/notifications.json"
LOCATIONS_JSON = "data/locations.json"
DB_NAME = "data/personnel.db"

# Права админов (код, название, описание)
ADMIN_RIGHTS = [
    ("manage_users", "👥", "Управление личным составом"),
    ("view_journal", "📖", "Просмотр и экспорт журнала"),
    ("export_logs", "💾", "Экспорт логов"),
    ("edit_admins", "👑", "Добавлять/удалять админов"),
    ("view_summary", "📊", "Просмотр сводки"),
    ("danger_zone", "🚨", "Доступ к опасным действиям"),
    ("edit_settings", "⚙️", "Изменение настроек"),
]
