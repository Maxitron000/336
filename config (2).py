# config.py

# Токен бота Telegram (для запуска!)
TOKEN = "8040939701:AAFfULuaLMrnrQggJllGkOPWcTl24KUm_q8"

# Главный Telegram ID (для полного доступа к админке)
MAIN_ADMIN_ID = 7973895358  # Замени на нужный при необходимости

# Часовой пояс для всех автоматических рассылок и экспорта
TIMEZONE = "Europe/Kaliningrad"

# Локации (с эмодзи и названиями)
LOCATIONS = [
    ("🏥", "Поликлиника"),
    ("⚓", "ОБРМП"),
    ("🌆", "Калининград"),
    ("🛒", "Магазин"),
    ("🍲", "Столовая"),
    ("🏨", "Госпиталь"),
    ("⚙️", "Рабочка"),
    ("🩺", "ВВК"),
    ("🏛️", "МФЦ"),
    ("🚓", "Патруль"),
]

# Пути к важным файлам и папкам
LOGS_FOLDER = "logs"
ADMINS_JSON = "admins.json"
NOTIFICATIONS_JSON = "notifications.json"
USERS_JSON = "users.json"  # Для личного состава (по необходимости)
SETTINGS_JSON = "settings.json"  # Для расширенных настроек

EXPORT_FOLDER = "exports"
EXPORT_FORMATS = ["csv", "xlsx", "pdf"]

LOGS_PAGE_SIZE = 12  # Кол-во записей на страницу в журнале

ADMIN_RIGHTS = [
    ("manage_users", "Управление личным составом", "👥"),
    ("view_journal", "Просмотр журнала", "📖"),
    ("export_logs", "Экспорт журналов", "📤"),
    ("edit_admins", "Управление админами", "👑"),
    ("view_summary", "Сводка", "📊"),
    ("danger_zone", "Опасная зона", "🚨"),
    ("edit_settings", "Настройки", "⚙️"),
]

BASH_ICONS = {
    "success": "✅",
    "fail": "❌",
    "wait": "⏳",
    "ready": "🚀",
    "info": "ℹ️"
}

BACKUP_FOLDER = "backup"

SUMMARY_TIME = "19:00"
REMINDER_TIME = "20:30"
