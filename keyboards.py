"""
Клавиатуры для Telegram бота учета персонала
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

# Helper to ensure compatibility with aiogram InlineKeyboardMarkup signature
def build_inline_keyboard(keyboard):
    """Return InlineKeyboardMarkup with provided inline_keyboard list."""
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Callback data для админ-панели
admin_cb = CallbackData("admin", "action", "subaction")
user_cb = CallbackData("user", "action")

def get_main_keyboard():
    """Главная клавиатура для обычных пользователей (устарела, используйте get_soldier_keyboard)"""
    return get_soldier_keyboard()

def get_soldier_keyboard():
    """Клавиатура для солдат - 3 кнопки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибыл", callback_data=user_cb.new("arrived")),
            InlineKeyboardButton("❌ Убыл", callback_data=user_cb.new("departed"))
        ],
        [
            InlineKeyboardButton("📊 Мой статус", callback_data=user_cb.new("my_status"))
        ]
    ]
    return build_inline_keyboard(keyboard)

def get_commander_keyboard():
    """Клавиатура для командиров - 4 кнопки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибыл", callback_data=user_cb.new("arrived")),
            InlineKeyboardButton("❌ Убыл", callback_data=user_cb.new("departed"))
        ],
        [
            InlineKeyboardButton("📊 Мой статус", callback_data=user_cb.new("my_status")),
            InlineKeyboardButton("⚙️ Админка", callback_data=admin_cb.new("dashboard", ""))
        ]
    ]
    return build_inline_keyboard(keyboard)

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
            InlineKeyboardButton("🔧 Техобслуживание", callback_data=admin_cb.new("maintenance", ""))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=user_cb.new("back_to_main"))]
    ]
    return build_inline_keyboard(keyboard)

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
    return build_inline_keyboard(keyboard)

def get_journal_keyboard():
    """Клавиатура журнала событий - Уровень 2: Меню «📖 Журнал событий»"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Фильтры", callback_data=admin_cb.new("journal", "filters")),
            InlineKeyboardButton("📋 Последние события", callback_data=admin_cb.new("journal", "recent"))
        ],
        [
            InlineKeyboardButton("📥 Экспорт журнала", callback_data=admin_cb.new("journal", "export")),
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb.new("journal", "stats"))
        ],
        [
            InlineKeyboardButton("🗑️ Очистить журнал", callback_data=admin_cb.new("journal", "clear")),
            InlineKeyboardButton("🔄 Обновить", callback_data=admin_cb.new("journal", "refresh"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return build_inline_keyboard(keyboard)

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
    return build_inline_keyboard(keyboard)

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
            InlineKeyboardButton("✏️ Редактировать тексты", callback_data=admin_cb.new("notifications", "edit_texts"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_admin_management_keyboard():
    """Клавиатура управления админами - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data=admin_cb.new("admins", "add")),
            InlineKeyboardButton("❌ Удалить админа", callback_data=admin_cb.new("admins", "remove"))
        ],
        [
            InlineKeyboardButton("👑 Главный админ", callback_data=admin_cb.new("admins", "main_admin")),
            InlineKeyboardButton("📋 Список админов", callback_data=admin_cb.new("admins", "list"))
        ],
        [
            InlineKeyboardButton("🔑 Права доступа", callback_data=admin_cb.new("admins", "permissions")),
            InlineKeyboardButton("⚙️ Настроить командира", callback_data=admin_cb.new("admins", "configure_commander"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_danger_zone_keyboard():
    """Клавиатура опасной зоны - Уровень 3: Меню «⚠️ Опасная зона»"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Отметить всех прибывшими", callback_data=admin_cb.new("danger_zone", "mark_all_arrived")),
            InlineKeyboardButton("🗑️ Очистить все данные", callback_data=admin_cb.new("danger_zone", "clear_all_data"))
        ],
        [
            InlineKeyboardButton("🔄 Сбросить настройки", callback_data=admin_cb.new("danger_zone", "reset_settings")),
            InlineKeyboardButton("💾 Резервная копия", callback_data=admin_cb.new("danger_zone", "backup"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_confirmation_keyboard(action: str):
    """Клавиатура подтверждения для опасных операций"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb.new("confirm", action)),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("cancel", ""))
        ]
    ]
    return build_inline_keyboard(keyboard)

def get_export_keyboard():
    """Клавиатура экспорта данных"""
    keyboard = [
        [
            InlineKeyboardButton("📄 CSV формат", callback_data=admin_cb.new("export", "csv")),
            InlineKeyboardButton("📊 Excel формат", callback_data=admin_cb.new("export", "excel"))
        ],
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb.new("export_period", "today")),
            InlineKeyboardButton("📅 За неделю", callback_data=admin_cb.new("export_period", "week"))
        ],
        [
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb.new("export_period", "month")),
            InlineKeyboardButton("📅 За все время", callback_data=admin_cb.new("export_period", "all"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("journal", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_location_keyboard():
    """Клавиатура выбора локации для убытия"""
    keyboard = [
        [
            InlineKeyboardButton("🏥 Поликлиника", callback_data=user_cb.new("location_polyclinic")),
            InlineKeyboardButton("⚓ ОБРМП", callback_data=user_cb.new("location_obrmp"))
        ],
        [
            InlineKeyboardButton("🌆 Калининград", callback_data=user_cb.new("location_kaliningrad")),
            InlineKeyboardButton("🛒 Магазин", callback_data=user_cb.new("location_shop"))
        ],
        [
            InlineKeyboardButton("🍲 Столовая", callback_data=user_cb.new("location_canteen")),
            InlineKeyboardButton("🏨 Госпиталь", callback_data=user_cb.new("location_hospital"))
        ],
        [
            InlineKeyboardButton("⚙️ Рабочка", callback_data=user_cb.new("location_workshop")),
            InlineKeyboardButton("🩺 ВВК", callback_data=user_cb.new("location_vvk"))
        ],
        [
            InlineKeyboardButton("🏛️ МФЦ", callback_data=user_cb.new("location_mfc")),
            InlineKeyboardButton("🚓 Патруль", callback_data=user_cb.new("location_patrol"))
        ],
        [
            InlineKeyboardButton("📝 Другое", callback_data=user_cb.new("location_custom")),
            InlineKeyboardButton("🔙 Отмена", callback_data=user_cb.new("cancel"))
        ]
    ]
    return build_inline_keyboard(keyboard)

def get_back_keyboard():
    """Простая клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data=user_cb.new("cancel"))]
    ]
    return build_inline_keyboard(keyboard)

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
    return build_inline_keyboard(keyboard)

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
        [
            InlineKeyboardButton("🔄 Принудительный перезапуск", callback_data=admin_cb.new("maintenance", "force_restart")),
            InlineKeyboardButton("🚨 Экстренный перезапуск", callback_data=admin_cb.new("maintenance", "emergency_restart"))
        ],
        [
            InlineKeyboardButton("📊 Статистика бэкапов", callback_data=admin_cb.new("maintenance", "backup_stats")),
            InlineKeyboardButton("📈 Статистика перезапусков", callback_data=admin_cb.new("maintenance", "restart_stats"))
        ],
        [
            InlineKeyboardButton("📋 Список бэкапов", callback_data=admin_cb.new("maintenance", "list_backups")),
            InlineKeyboardButton("🐍 PythonAnywhere", callback_data=admin_cb.new("maintenance", "pythonanywhere_info"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_maintenance_confirmation_keyboard(maintenance_type: str):
    """Клавиатура подтверждения технического обслуживания"""
    keyboard = [
        [InlineKeyboardButton(f"✅ Да, выполнить {maintenance_type}", callback_data=admin_cb.new("maintenance_confirm", maintenance_type))]
    ]
    return build_inline_keyboard(keyboard)

def get_initial_status_keyboard():
    """Клавиатура выбора начального статуса при регистрации"""
    keyboard = [
        [
            InlineKeyboardButton("🏠 В части", callback_data=user_cb.new("initial_status_in_unit")),
            InlineKeyboardButton("🚪 Вне части", callback_data=user_cb.new("initial_status_away"))
        ]
    ]
    return build_inline_keyboard(keyboard)

def get_commander_permissions_keyboard(permissions: dict = None):
    """Клавиатура настройки прав командира"""
    if not permissions:
        permissions = {}
    
    def get_status_emoji(permission_key):
        return "✅" if permissions.get(permission_key, False) else "❌"
    
    keyboard = [
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_personnel')} Просмотр л/с", 
            callback_data=admin_cb.new("permissions", "toggle_can_view_personnel")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_manage_personnel')} Управление л/с", 
            callback_data=admin_cb.new("permissions", "toggle_can_manage_personnel")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_export_data')} Экспорт данных", 
            callback_data=admin_cb.new("permissions", "toggle_can_export_data")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_journal')} Просмотр журнала", 
            callback_data=admin_cb.new("permissions", "toggle_can_view_journal")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_clear_journal')} Очистка журнала", 
            callback_data=admin_cb.new("permissions", "toggle_can_clear_journal")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_manage_notifications')} Управление уведомлениями", 
            callback_data=admin_cb.new("permissions", "toggle_can_manage_notifications")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_stats')} Просмотр статистики", 
            callback_data=admin_cb.new("permissions", "toggle_can_view_stats")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_force_operations')} Принудительные операции", 
            callback_data=admin_cb.new("permissions", "toggle_can_force_operations")
        )],
        [
            InlineKeyboardButton("💾 Сохранить", callback_data=admin_cb.new("permissions", "save")),
            InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", "admins"))
        ]
    ]
    return build_inline_keyboard(keyboard)

def get_permissions_management_keyboard():
    """Клавиатура управления правами командиров"""
    keyboard = [
        [
            InlineKeyboardButton("👑 Настроить права командира", callback_data=admin_cb.new("permissions", "configure")),
            InlineKeyboardButton("📋 Список командиров", callback_data=admin_cb.new("permissions", "list_commanders"))
        ],
        [
            InlineKeyboardButton("🔧 Массовые настройки", callback_data=admin_cb.new("permissions", "bulk_configure")),
            InlineKeyboardButton("📊 Отчет по правам", callback_data=admin_cb.new("permissions", "report"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_journal_filters_keyboard():
    """Клавиатура фильтров журнала"""
    keyboard = [
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb.new("journal_filter", "today")),
            InlineKeyboardButton("📅 За неделю", callback_data=admin_cb.new("journal_filter", "week"))
        ],
        [
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb.new("journal_filter", "month")),
            InlineKeyboardButton("📅 За все время", callback_data=admin_cb.new("journal_filter", "all"))
        ],
        [
            InlineKeyboardButton("👤 По ФИО", callback_data=admin_cb.new("journal_filter", "by_name")),
            InlineKeyboardButton("🔍 По действию", callback_data=admin_cb.new("journal_filter", "by_action"))
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb.new("journal_filter", "stats")),
            InlineKeyboardButton("🔄 Сбросить фильтры", callback_data=admin_cb.new("journal_filter", "reset"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("journal", ""))]
    ]
    return build_inline_keyboard(keyboard)

def get_date_range_keyboard():
    """Клавиатура выбора диапазона дат"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Вчера", callback_data=admin_cb.new("date_range", "yesterday")),
            InlineKeyboardButton("📅 Позавчера", callback_data=admin_cb.new("date_range", "day_before_yesterday"))
        ],
        [
            InlineKeyboardButton("📅 Последние 3 дня", callback_data=admin_cb.new("date_range", "last_3_days")),
            InlineKeyboardButton("📅 Последние 7 дней", callback_data=admin_cb.new("date_range", "last_7_days"))
        ],
        [
            InlineKeyboardButton("📅 Последние 30 дней", callback_data=admin_cb.new("date_range", "last_30_days")),
            InlineKeyboardButton("📝 Ввести период", callback_data=admin_cb.new("date_range", "custom"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("journal", "filters"))]
    ]
    return build_inline_keyboard(keyboard)

def get_danger_confirmation_keyboard(action: str):
    """Клавиатура подтверждения опасных действий"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("cancel_danger", action))]
    ]
    return build_inline_keyboard(keyboard)

def get_text_confirmation_keyboard():
    """Клавиатура после ввода текста подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb.new("confirm_text", "yes")),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("confirm_text", "no"))
        ]
    ]
    return build_inline_keyboard(keyboard)