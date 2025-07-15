"""
Клавиатуры для Telegram бота учета персонала
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

# Callback data для админ-панели
class AdminCallbackData(CallbackData, prefix="admin"):
    action: str
    subaction: str = ""

class UserCallbackData(CallbackData, prefix="user"):
    action: str
    data: str = ""

# Совместимость со старым кодом
admin_cb = AdminCallbackData
user_cb = UserCallbackData

def get_main_keyboard():
    """Главная клавиатура для обычных пользователей (устарела, используйте get_soldier_keyboard)"""
    return get_soldier_keyboard()

def get_soldier_keyboard():
    """Клавиатура для солдат - 3 кнопки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибыл", callback_data=user_cb(action="arrived")),
            InlineKeyboardButton("❌ Убыл", callback_data=user_cb(action="departed"))
        ],
        [
            InlineKeyboardButton("📊 Мой статус", callback_data=user_cb(action="my_status"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_commander_keyboard():
    """Клавиатура для командиров - 4 кнопки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибыл", callback_data=user_cb(action="arrived")),
            InlineKeyboardButton("❌ Убыл", callback_data=user_cb(action="departed"))
        ],
        [
            InlineKeyboardButton("📊 Мой статус", callback_data=user_cb(action="my_status")),
            InlineKeyboardButton("⚙️ Админка", callback_data=admin_cb(action="dashboard", subaction=""))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard():
    """Главная админская клавиатура - Уровень 1: 🏠 Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Быстрая сводка", callback_data=admin_cb(action="dashboard", subaction="")),
            InlineKeyboardButton("👥 Управление л/с", callback_data=admin_cb(action="personnel", subaction=""))
        ],
        [
            InlineKeyboardButton("📖 Журнал событий", callback_data=admin_cb(action="journal", subaction="")),
            InlineKeyboardButton("⚙️ Настройки", callback_data=admin_cb(action="settings", subaction=""))
        ],
        [
            InlineKeyboardButton("🏥 Мониторинг бота", callback_data=admin_cb(action="monitoring", subaction="")),
            InlineKeyboardButton("🔧 Техобслуживание", callback_data=admin_cb(action="maintenance", subaction=""))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=user_cb(action="back_to_main"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_personnel_keyboard():
    """Клавиатура управления личным составом - Уровень 2: Меню «👥 Управление л/с»"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Сменить ФИО бойца", callback_data=admin_cb(action="personnel", subaction="change_name")),
            InlineKeyboardButton("➕ Добавить нового бойца", callback_data=admin_cb(action="personnel", subaction="add_user"))
        ],
        [
            InlineKeyboardButton("❌ Удалить бойца", callback_data=admin_cb(action="personnel", subaction="delete_user")),
            InlineKeyboardButton("📋 Список всех бойцов", callback_data=admin_cb(action="personnel", subaction="list_users"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_keyboard():
    """Клавиатура журнала событий - Уровень 2: Меню «📖 Журнал событий»"""
    keyboard = [
        [
            InlineKeyboardButton("🔍 Фильтры", callback_data=admin_cb(action="journal", subaction="filters")),
            InlineKeyboardButton("📋 Последние события", callback_data=admin_cb(action="journal", subaction="recent"))
        ],
        [
            InlineKeyboardButton("📥 Экспорт журнала", callback_data=admin_cb(action="journal", subaction="export")),
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb(action="journal", subaction="stats"))
        ],
        [
            InlineKeyboardButton("🗑️ Очистить журнал", callback_data=admin_cb(action="journal", subaction="clear")),
            InlineKeyboardButton("🔄 Обновить", callback_data=admin_cb(action="journal", subaction="refresh"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_keyboard():
    """Клавиатура настроек - Уровень 2: Меню «⚙️ Настройки»"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data=admin_cb(action="settings", subaction="notifications")),
            InlineKeyboardButton("👑 Управление админами", callback_data=admin_cb(action="settings", subaction="admins"))
        ],
        [
            InlineKeyboardButton("⚠️ Опасная зона", callback_data=admin_cb(action="settings", subaction="danger_zone")),
            InlineKeyboardButton("🔧 Системные настройки", callback_data=admin_cb(action="settings", subaction="system"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_notifications_settings_keyboard():
    """Клавиатура настроек уведомлений - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Включить уведомления", callback_data=admin_cb(action="notifications", subaction="enable")),
            InlineKeyboardButton("🔕 Отключить уведомления", callback_data=admin_cb(action="notifications", subaction="disable"))
        ],
        [
            InlineKeyboardButton("📊 Ежедневная сводка", callback_data=admin_cb(action="notifications", subaction="daily_summary")),
            InlineKeyboardButton("⏰ Напоминания", callback_data=admin_cb(action="notifications", subaction="reminders"))
        ],
        [
            InlineKeyboardButton("🔇 Тихий режим", callback_data=admin_cb(action="notifications", subaction="silent_mode")),
            InlineKeyboardButton("✏️ Редактировать тексты", callback_data=admin_cb(action="notifications", subaction="edit_texts"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="settings", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_management_keyboard():
    """Клавиатура управления админами - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data=admin_cb(action="admins", subaction="add")),
            InlineKeyboardButton("❌ Удалить админа", callback_data=admin_cb(action="admins", subaction="remove"))
        ],
        [
            InlineKeyboardButton("👑 Главный админ", callback_data=admin_cb(action="admins", subaction="main_admin")),
            InlineKeyboardButton("📋 Список админов", callback_data=admin_cb(action="admins", subaction="list"))
        ],
        [
            InlineKeyboardButton("🔑 Права доступа", callback_data=admin_cb(action="admins", subaction="permissions")),
            InlineKeyboardButton("⚙️ Настроить командира", callback_data=admin_cb(action="admins", subaction="configure_commander"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="settings", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_danger_zone_keyboard():
    """Клавиатура опасной зоны - Уровень 3: Меню «⚠️ Опасная зона»"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Отметить всех прибывшими", callback_data=admin_cb(action="danger_zone", subaction="mark_all_arrived")),
            InlineKeyboardButton("🗑️ Очистить все данные", callback_data=admin_cb(action="danger_zone", subaction="clear_all_data"))
        ],
        [
            InlineKeyboardButton("🔄 Сбросить настройки", callback_data=admin_cb(action="danger_zone", subaction="reset_settings")),
            InlineKeyboardButton("💾 Резервная копия", callback_data=admin_cb(action="danger_zone", subaction="backup"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="settings", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard(action: str):
    """Клавиатура подтверждения для опасных операций"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb.new("confirm", action)),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb(action="cancel", subaction=""))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_export_keyboard():
    """Клавиатура экспорта данных"""
    keyboard = [
        [
            InlineKeyboardButton("📄 CSV формат", callback_data=admin_cb(action="export", subaction="csv")),
            InlineKeyboardButton("📊 Excel формат", callback_data=admin_cb(action="export", subaction="excel"))
        ],
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb(action="export_period", subaction="today")),
            InlineKeyboardButton("📅 За неделю", callback_data=admin_cb(action="export_period", subaction="week"))
        ],
        [
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb(action="export_period", subaction="month")),
            InlineKeyboardButton("📅 За все время", callback_data=admin_cb(action="export_period", subaction="all"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="journal", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_location_keyboard():
    """Клавиатура выбора локации для убытия"""
    keyboard = [
        [
            InlineKeyboardButton("🏥 Поликлиника", callback_data=user_cb(action="location_polyclinic")),
            InlineKeyboardButton("⚓ ОБРМП", callback_data=user_cb(action="location_obrmp"))
        ],
        [
            InlineKeyboardButton("🌆 Калининград", callback_data=user_cb(action="location_kaliningrad")),
            InlineKeyboardButton("🛒 Магазин", callback_data=user_cb(action="location_shop"))
        ],
        [
            InlineKeyboardButton("🍲 Столовая", callback_data=user_cb(action="location_canteen")),
            InlineKeyboardButton("🏨 Госпиталь", callback_data=user_cb(action="location_hospital"))
        ],
        [
            InlineKeyboardButton("⚙️ Рабочка", callback_data=user_cb(action="location_workshop")),
            InlineKeyboardButton("🩺 ВВК", callback_data=user_cb(action="location_vvk"))
        ],
        [
            InlineKeyboardButton("🏛️ МФЦ", callback_data=user_cb(action="location_mfc")),
            InlineKeyboardButton("🚓 Патруль", callback_data=user_cb(action="location_patrol"))
        ],
        [
            InlineKeyboardButton("📝 Другое", callback_data=user_cb(action="location_custom")),
            InlineKeyboardButton("🔙 Отмена", callback_data=user_cb(action="cancel"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard():
    """Простая клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data=user_cb(action="cancel"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_monitoring_keyboard():
    """Клавиатура мониторинга бота - Уровень 2: Меню «🏥 Мониторинг бота»"""
    keyboard = [
        [
            InlineKeyboardButton("🏥 Проверка здоровья", callback_data=admin_cb(action="monitoring", subaction="health_check")),
            InlineKeyboardButton("📈 Отчет производительности", callback_data=admin_cb(action="monitoring", subaction="performance"))
        ],
        [
            InlineKeyboardButton("📊 Статистика системы", callback_data=admin_cb(action="monitoring", subaction="system_stats")),
            InlineKeyboardButton("🔍 Детальная диагностика", callback_data=admin_cb(action="monitoring", subaction="diagnostics"))
        ],
        [
            InlineKeyboardButton("⏰ Автоматические проверки", callback_data=admin_cb(action="monitoring", subaction="auto_checks")),
            InlineKeyboardButton("📋 История статусов", callback_data=admin_cb(action="monitoring", subaction="status_history"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_maintenance_keyboard():
    """Клавиатура техобслуживания - Уровень 2: Меню «🔧 Техобслуживание»"""
    keyboard = [
        [
            InlineKeyboardButton("🔧 Плановое ТО", callback_data=admin_cb(action="maintenance", subaction="scheduled")),
            InlineKeyboardButton("🚨 Экстренное ТО", callback_data=admin_cb(action="maintenance", subaction="emergency"))
        ],
        [
            InlineKeyboardButton("🔄 Обновление системы", callback_data=admin_cb(action="maintenance", subaction="update")),
            InlineKeyboardButton("💾 Резервная копия", callback_data=admin_cb(action="maintenance", subaction="backup"))
        ],
        [
            InlineKeyboardButton("🧹 Очистка данных", callback_data=admin_cb(action="maintenance", subaction="cleanup")),
            InlineKeyboardButton("📋 Лог ТО", callback_data=admin_cb(action="maintenance", subaction="maintenance_log"))
        ],
        [
            InlineKeyboardButton("🔄 Принудительный перезапуск", callback_data=admin_cb(action="maintenance", subaction="force_restart")),
            InlineKeyboardButton("🚨 Экстренный перезапуск", callback_data=admin_cb(action="maintenance", subaction="emergency_restart"))
        ],
        [
            InlineKeyboardButton("📊 Статистика бэкапов", callback_data=admin_cb(action="maintenance", subaction="backup_stats")),
            InlineKeyboardButton("📈 Статистика перезапусков", callback_data=admin_cb(action="maintenance", subaction="restart_stats"))
        ],
        [
            InlineKeyboardButton("📋 Список бэкапов", callback_data=admin_cb(action="maintenance", subaction="list_backups")),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="back", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_maintenance_confirmation_keyboard(maintenance_type: str):
    """Клавиатура подтверждения технического обслуживания"""
    keyboard = [
        [InlineKeyboardButton(f"✅ Да, выполнить {maintenance_type}", callback_data=admin_cb.new("maintenance_confirm", maintenance_type))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_initial_status_keyboard():
    """Клавиатура выбора начального статуса при регистрации"""
    keyboard = [
        [
            InlineKeyboardButton("🏠 В части", callback_data=user_cb(action="initial_status_in_unit")),
            InlineKeyboardButton("🚪 Вне части", callback_data=user_cb(action="initial_status_away"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_commander_permissions_keyboard(permissions: dict = None):
    """Клавиатура настройки прав командира"""
    if not permissions:
        permissions = {}
    
    def get_status_emoji(permission_key):
        return "✅" if permissions.get(permission_key, False) else "❌"
    
    keyboard = [
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_personnel')} Просмотр л/с", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_view_personnel")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_manage_personnel')} Управление л/с", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_manage_personnel")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_export_data')} Экспорт данных", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_export_data")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_journal')} Просмотр журнала", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_view_journal")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_clear_journal')} Очистка журнала", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_clear_journal")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_manage_notifications')} Управление уведомлениями", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_manage_notifications")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_view_stats')} Просмотр статистики", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_view_stats")
        )],
        [InlineKeyboardButton(
            f"{get_status_emoji('can_force_operations')} Принудительные операции", 
            callback_data=admin_cb(action="permissions", subaction="toggle_can_force_operations")
        )],
        [
            InlineKeyboardButton("💾 Сохранить", callback_data=admin_cb(action="permissions", subaction="save")),
            InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="settings", subaction="admins"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_permissions_management_keyboard():
    """Клавиатура управления правами командиров"""
    keyboard = [
        [
            InlineKeyboardButton("👑 Настроить права командира", callback_data=admin_cb(action="permissions", subaction="configure")),
            InlineKeyboardButton("📋 Список командиров", callback_data=admin_cb(action="permissions", subaction="list_commanders"))
        ],
        [
            InlineKeyboardButton("🔧 Массовые настройки", callback_data=admin_cb(action="permissions", subaction="bulk_configure")),
            InlineKeyboardButton("📊 Отчет по правам", callback_data=admin_cb(action="permissions", subaction="report"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="settings", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_journal_filters_keyboard():
    """Клавиатура фильтров журнала"""
    keyboard = [
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb(action="journal_filter", subaction="today")),
            InlineKeyboardButton("📅 За неделю", callback_data=admin_cb(action="journal_filter", subaction="week"))
        ],
        [
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb(action="journal_filter", subaction="month")),
            InlineKeyboardButton("📅 За все время", callback_data=admin_cb(action="journal_filter", subaction="all"))
        ],
        [
            InlineKeyboardButton("👤 По ФИО", callback_data=admin_cb(action="journal_filter", subaction="by_name")),
            InlineKeyboardButton("🔍 По действию", callback_data=admin_cb(action="journal_filter", subaction="by_action"))
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb(action="journal_filter", subaction="stats")),
            InlineKeyboardButton("🔄 Сбросить фильтры", callback_data=admin_cb(action="journal_filter", subaction="reset"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="journal", subaction=""))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_date_range_keyboard():
    """Клавиатура выбора диапазона дат"""
    keyboard = [
        [
            InlineKeyboardButton("📅 Вчера", callback_data=admin_cb(action="date_range", subaction="yesterday")),
            InlineKeyboardButton("📅 Позавчера", callback_data=admin_cb(action="date_range", subaction="day_before_yesterday"))
        ],
        [
            InlineKeyboardButton("📅 Последние 3 дня", callback_data=admin_cb(action="date_range", subaction="last_3_days")),
            InlineKeyboardButton("📅 Последние 7 дней", callback_data=admin_cb(action="date_range", subaction="last_7_days"))
        ],
        [
            InlineKeyboardButton("📅 Последние 30 дней", callback_data=admin_cb(action="date_range", subaction="last_30_days")),
            InlineKeyboardButton("📝 Ввести период", callback_data=admin_cb(action="date_range", subaction="custom"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb(action="journal", subaction="filters"))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_danger_confirmation_keyboard(action: str):
    """Клавиатура подтверждения опасных действий"""
    keyboard = [
        [InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("cancel_danger", action))]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_text_confirmation_keyboard():
    """Клавиатура после ввода текста подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb(action="confirm_text", subaction="yes")),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb(action="confirm_text", subaction="no"))
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)