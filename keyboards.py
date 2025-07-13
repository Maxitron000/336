"""
Клавиатуры для Telegram бота учета персонала
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

# Callback data для админ-панели
admin_cb = CallbackData("admin", "action", "subaction")
user_cb = CallbackData("user", "action")

def get_main_keyboard():
    """Главная клавиатура для обычных пользователей"""
    keyboard = [
        [
            KeyboardButton("✅ Отметиться"),
            KeyboardButton("📍 Указать локацию")
        ],
        [
            KeyboardButton("📊 Мой статус"),
            KeyboardButton("📖 Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    """Главная админская клавиатура - Уровень 1: 🏠 Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Быстрая сводка", callback_data=admin_cb.new("dashboard", "")),
            InlineKeyboardButton("👥 Управление л/с", callback_data=admin_cb.new("personnel", ""))
        ],
        [
            InlineKeyboardButton("📖 Журнал событий", callback_data=admin_cb.new("journal", "")),
            InlineKeyboardButton("⚙️ Настройки", callback_data=admin_cb.new("settings", ""))
        ],
        [
            InlineKeyboardButton("🏥 Мониторинг бота", callback_data=admin_cb.new("monitoring", "")),
            InlineKeyboardButton("� Техобслуживание", callback_data=admin_cb.new("maintenance", ""))
        ],
        [InlineKeyboardButton("� Назад", callback_data=user_cb.new("back_to_main"))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_personnel_keyboard():
    """Клавиатура управления личным составом - Уровень 2: Меню «👥 Управление л/с»"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Сменить ФИО бойца", callback_data=admin_cb.new("personnel", "change_name")),
            InlineKeyboardButton("➕ Добавить нового бойца", callback_data=admin_cb.new("personnel", "add_user"))
        ],
        [
            InlineKeyboardButton("❌ Удалить бойца", callback_data=admin_cb.new("personnel", "delete_user")),
            InlineKeyboardButton("📋 Список всех бойцов", callback_data=admin_cb.new("personnel", "list_users"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_journal_keyboard():
    """Клавиатура журнала событий - Уровень 2: Меню «📖 Журнал событий»"""
    keyboard = [
        [
            InlineKeyboardButton("📥 Экспорт журнала", callback_data=admin_cb.new("journal", "export")),
            InlineKeyboardButton("� Статистика", callback_data=admin_cb.new("journal", "stats"))
        ],
        [
            InlineKeyboardButton("�️ Очистить журнал", callback_data=admin_cb.new("journal", "clear")),
            InlineKeyboardButton("� Последние события", callback_data=admin_cb.new("journal", "recent"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Клавиатура настроек - Уровень 2: Меню «⚙️ Настройки»"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data=admin_cb.new("settings", "notifications")),
            InlineKeyboardButton("👑 Управление админами", callback_data=admin_cb.new("settings", "admins"))
        ],
        [
            InlineKeyboardButton("⚠️ Опасная зона", callback_data=admin_cb.new("settings", "danger_zone")),
            InlineKeyboardButton("🔧 Системные настройки", callback_data=admin_cb.new("settings", "system"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notifications_settings_keyboard():
    """Клавиатура настроек уведомлений - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Включить уведомления", callback_data=admin_cb.new("notifications", "enable")),
            InlineKeyboardButton("🔕 Отключить уведомления", callback_data=admin_cb.new("notifications", "disable"))
        ],
        [
            InlineKeyboardButton("📊 Ежедневная сводка", callback_data=admin_cb.new("notifications", "daily_summary")),
            InlineKeyboardButton("⏰ Напоминания", callback_data=admin_cb.new("notifications", "reminders"))
        ],
        [
            InlineKeyboardButton("🔇 Тихий режим", callback_data=admin_cb.new("notifications", "silent_mode")),
            InlineKeyboardButton("� Редактировать тексты", callback_data=admin_cb.new("notifications", "edit_texts"))
        ],
        [InlineKeyboardButton("� Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_management_keyboard():
    """Клавиатура управления админами - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data=admin_cb.new("admins", "add")),
            InlineKeyboardButton("❌ Удалить админа", callback_data=admin_cb.new("admins", "remove"))
        ],
        [
            InlineKeyboardButton("� Главный админ", callback_data=admin_cb.new("admins", "main_admin")),
            InlineKeyboardButton("� Список админов", callback_data=admin_cb.new("admins", "list"))
        ],
        [InlineKeyboardButton("� Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_danger_zone_keyboard():
    """Клавиатура опасной зоны - Уровень 3: Меню «⚠️ Опасная зона»"""
    keyboard = [
        [
            InlineKeyboardButton("� Отметить всех прибывшими", callback_data=admin_cb.new("danger_zone", "mark_all_arrived")),
            InlineKeyboardButton("🗑️ Очистить все данные", callback_data=admin_cb.new("danger_zone", "clear_all_data"))
        ],
        [
            InlineKeyboardButton("� Сбросить настройки", callback_data=admin_cb.new("danger_zone", "reset_settings")),
            InlineKeyboardButton("� Резервная копия", callback_data=admin_cb.new("danger_zone", "backup"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str):
    """Клавиатура подтверждения для опасных операций"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb.new("confirm", action)),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("cancel", ""))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_export_keyboard():
    """Клавиатура экспорта данных"""
    keyboard = [
        [
            InlineKeyboardButton("� CSV формат", callback_data=admin_cb.new("export", "csv")),
            InlineKeyboardButton("� Excel формат", callback_data=admin_cb.new("export", "excel"))
        ],
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb.new("export_period", "today")),
            InlineKeyboardButton("� За неделю", callback_data=admin_cb.new("export_period", "week"))
        ],
        [
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb.new("export_period", "month")),
            InlineKeyboardButton("� За все время", callback_data=admin_cb.new("export_period", "all"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("journal", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_location_keyboard():
    """Клавиатура выбора локации"""
    keyboard = [
        [
            InlineKeyboardButton("🏢 Офис", callback_data=user_cb.new("location_office")),
            InlineKeyboardButton("🏠 Дом", callback_data=user_cb.new("location_home"))
        ],
        [
            InlineKeyboardButton("🏥 Больница", callback_data=user_cb.new("location_hospital")),
            InlineKeyboardButton("� В пути", callback_data=user_cb.new("location_traveling"))
        ],
        [
            InlineKeyboardButton("🏖️ Отпуск", callback_data=user_cb.new("location_vacation")),
            InlineKeyboardButton("🏥 Больничный", callback_data=user_cb.new("location_sick"))
        ],
        [
            InlineKeyboardButton("✏️ Другое", callback_data=user_cb.new("location_custom")),
            InlineKeyboardButton("🔙 Отмена", callback_data=user_cb.new("cancel"))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    """Простая клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data=user_cb.new("cancel"))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_monitoring_keyboard():
    """Клавиатура мониторинга бота - Уровень 2: Меню «🏥 Мониторинг бота»"""
    keyboard = [
        [
            InlineKeyboardButton("🏥 Проверка здоровья", callback_data=admin_cb.new("monitoring", "health_check")),
            InlineKeyboardButton("📈 Отчет производительности", callback_data=admin_cb.new("monitoring", "performance"))
        ],
        [
            InlineKeyboardButton("📊 Статистика системы", callback_data=admin_cb.new("monitoring", "system_stats")),
            InlineKeyboardButton("🔍 Детальная диагностика", callback_data=admin_cb.new("monitoring", "diagnostics"))
        ],
        [
            InlineKeyboardButton("⏰ Автоматические проверки", callback_data=admin_cb.new("monitoring", "auto_checks")),
            InlineKeyboardButton("📋 История статусов", callback_data=admin_cb.new("monitoring", "status_history"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_maintenance_keyboard():
    """Клавиатура техобслуживания - Уровень 2: Меню «🔧 Техобслуживание»"""
    keyboard = [
        [
            InlineKeyboardButton("🔧 Плановое ТО", callback_data=admin_cb.new("maintenance", "scheduled")),
            InlineKeyboardButton("🚨 Экстренное ТО", callback_data=admin_cb.new("maintenance", "emergency"))
        ],
        [
            InlineKeyboardButton("🔄 Обновление системы", callback_data=admin_cb.new("maintenance", "update")),
            InlineKeyboardButton("💾 Резервная копия", callback_data=admin_cb.new("maintenance", "backup"))
        ],
        [
            InlineKeyboardButton("🧹 Очистка данных", callback_data=admin_cb.new("maintenance", "cleanup")),
            InlineKeyboardButton("📋 Лог ТО", callback_data=admin_cb.new("maintenance", "maintenance_log"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_maintenance_confirmation_keyboard(maintenance_type: str):
    """Клавиатура подтверждения техобслуживания"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить ТО", callback_data=admin_cb.new("maintenance_confirm", maintenance_type)),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("maintenance", ""))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)