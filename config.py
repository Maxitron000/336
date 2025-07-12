# config.py

# Токен твоего бота (для публичного кода лучше хранить в .env!)
TOKEN = "8040939701:AAFfULuaLMrnrQggJllGkOPWcTl24KUm_q8"

# Пути к файлам
ADMINS_JSON = "admins.json"
NOTIFICATIONS_JSON = "notifications.json"

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
