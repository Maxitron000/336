"""
Клавиатуры для Telegram бота учета персонала
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData

# Callback data для админ-панели
admin_cb = CallbackData("admin", "action", "subaction")
user_cb = CallbackData("user", "action")
commander_cb = CallbackData("commander", "action")

def get_main_keyboard():
    """Главная клавиатура для обычных пользователей"""
    keyboard = [
        [
            KeyboardButton("✅ Прибыл"),
            KeyboardButton("� Убыл"),
            KeyboardButton("📍 Локация")
        ],
        [
            KeyboardButton("📊 Мой статус"),
            KeyboardButton("📖 Помощь"),
            KeyboardButton("⚙️ Настройки")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    """Главная админская клавиатура - Уровень 1: 🏠 Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Быстрая сводка", callback_data=admin_cb.new("dashboard", "")),
            InlineKeyboardButton("👥 ЛС", callback_data=admin_cb.new("personnel", "")),
            InlineKeyboardButton("🛡️ Командиры", callback_data=admin_cb.new("commanders", ""))
        ],
        [
            InlineKeyboardButton("📖 Журнал", callback_data=admin_cb.new("journal", "")),
            InlineKeyboardButton("📤 Экспорт", callback_data=admin_cb.new("export", "")),
            InlineKeyboardButton("⚙️ Настройки", callback_data=admin_cb.new("settings", ""))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=user_cb.new("back_to_main"))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_personnel_keyboard():
    """Клавиатура управления личным составом - Уровень 2: Меню «👥 ЛС»"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить бойца", callback_data=admin_cb.new("personnel", "add_user")),
            InlineKeyboardButton("✏️ Изменить ФИО", callback_data=admin_cb.new("personnel", "change_name")),
            InlineKeyboardButton("❌ Удалить бойца", callback_data=admin_cb.new("personnel", "delete_user"))
        ],
        [
            InlineKeyboardButton("📋 Список бойцов", callback_data=admin_cb.new("personnel", "list_users")),
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb.new("personnel", "stats")),
            InlineKeyboardButton("🔍 Поиск", callback_data=admin_cb.new("personnel", "search"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_commanders_keyboard():
    """Клавиатура управления командирами - Уровень 2: Меню «�️ Командиры»"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить командира", callback_data=admin_cb.new("commanders", "add")),
            InlineKeyboardButton("❌ Удалить командира", callback_data=admin_cb.new("commanders", "remove")),
            InlineKeyboardButton("📋 Список командиров", callback_data=admin_cb.new("commanders", "list"))
        ],
        [
            InlineKeyboardButton("🔔 PUSH права", callback_data=admin_cb.new("commanders", "push_rights")),
            InlineKeyboardButton("� Права отчетов", callback_data=admin_cb.new("commanders", "report_rights")),
            InlineKeyboardButton("⚙️ Настройки командира", callback_data=admin_cb.new("commanders", "settings"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_journal_keyboard():
    """Клавиатура журнала событий - Уровень 2: Меню «📖 Журнал»"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Последние события", callback_data=admin_cb.new("journal", "recent")),
            InlineKeyboardButton("📊 Статистика", callback_data=admin_cb.new("journal", "stats")),
            InlineKeyboardButton("🔍 Поиск", callback_data=admin_cb.new("journal", "search"))
        ],
        [
            InlineKeyboardButton("🗑️ Очистить журнал", callback_data=admin_cb.new("journal", "clear")),
            InlineKeyboardButton("📥 Экспорт журнала", callback_data=admin_cb.new("journal", "export")),
            InlineKeyboardButton("⚙️ Настройки журнала", callback_data=admin_cb.new("journal", "settings"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_export_keyboard():
    """Клавиатура экспорта данных - Уровень 2: Меню «📤 Экспорт»"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Отчет по ЛС", callback_data=admin_cb.new("export", "personnel")),
            InlineKeyboardButton("📈 Статистика", callback_data=admin_cb.new("export", "stats")),
            InlineKeyboardButton("📋 Журнал событий", callback_data=admin_cb.new("export", "journal"))
        ],
        [
            InlineKeyboardButton("📅 За сегодня", callback_data=admin_cb.new("export_period", "today")),
            InlineKeyboardButton("📅 За неделю", callback_data=admin_cb.new("export_period", "week")),
            InlineKeyboardButton("📅 За месяц", callback_data=admin_cb.new("export_period", "month"))
        ],
        [
            InlineKeyboardButton("📄 CSV формат", callback_data=admin_cb.new("export_format", "csv")),
            InlineKeyboardButton("📊 Excel формат", callback_data=admin_cb.new("export_format", "excel")),
            InlineKeyboardButton("📋 PDF формат", callback_data=admin_cb.new("export_format", "pdf"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Клавиатура настроек - Уровень 2: Меню «⚙️ Настройки»"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data=admin_cb.new("settings", "notifications")),
            InlineKeyboardButton("👑 Админы", callback_data=admin_cb.new("settings", "admins")),
            InlineKeyboardButton("📍 Локации", callback_data=admin_cb.new("settings", "locations"))
        ],
        [
            InlineKeyboardButton("⚠️ Опасная зона", callback_data=admin_cb.new("settings", "danger_zone")),
            InlineKeyboardButton("🔧 Система", callback_data=admin_cb.new("settings", "system")),
            InlineKeyboardButton("💾 Резервная копия", callback_data=admin_cb.new("settings", "backup"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notifications_settings_keyboard():
    """Клавиатура настроек уведомлений - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Включить PUSH", callback_data=admin_cb.new("notifications", "enable_push")),
            InlineKeyboardButton("🔕 Отключить PUSH", callback_data=admin_cb.new("notifications", "disable_push")),
            InlineKeyboardButton("📊 Сводки", callback_data=admin_cb.new("notifications", "daily_summary"))
        ],
        [
            InlineKeyboardButton("⏰ Напоминания", callback_data=admin_cb.new("notifications", "reminders")),
            InlineKeyboardButton("✅ Прибытие", callback_data=admin_cb.new("notifications", "arrival")),
            InlineKeyboardButton("🚪 Убытие", callback_data=admin_cb.new("notifications", "departure"))
        ],
        [
            InlineKeyboardButton("🔇 Тихий режим", callback_data=admin_cb.new("notifications", "silent_mode")),
            InlineKeyboardButton("📝 Шаблоны", callback_data=admin_cb.new("notifications", "templates")),
            InlineKeyboardButton("⚙️ Расписание", callback_data=admin_cb.new("notifications", "schedule"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_management_keyboard():
    """Клавиатура управления админами - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data=admin_cb.new("admins", "add")),
            InlineKeyboardButton("❌ Удалить админа", callback_data=admin_cb.new("admins", "remove")),
            InlineKeyboardButton("📋 Список админов", callback_data=admin_cb.new("admins", "list"))
        ],
        [
            InlineKeyboardButton("👑 Главный админ", callback_data=admin_cb.new("admins", "main_admin")),
            InlineKeyboardButton("🔐 Права доступа", callback_data=admin_cb.new("admins", "permissions")),
            InlineKeyboardButton("📊 Активность", callback_data=admin_cb.new("admins", "activity"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_locations_keyboard():
    """Клавиатура управления локациями - Уровень 3"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить локацию", callback_data=admin_cb.new("locations", "add")),
            InlineKeyboardButton("✏️ Изменить локацию", callback_data=admin_cb.new("locations", "edit")),
            InlineKeyboardButton("❌ Удалить локацию", callback_data=admin_cb.new("locations", "delete"))
        ],
        [
            InlineKeyboardButton("📋 Список локаций", callback_data=admin_cb.new("locations", "list")),
            InlineKeyboardButton("� Статистика", callback_data=admin_cb.new("locations", "stats")),
            InlineKeyboardButton("⚙️ Настройки", callback_data=admin_cb.new("locations", "settings"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_danger_zone_keyboard():
    """Клавиатура опасной зоны - Уровень 3: Меню «⚠️ Опасная зона»"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Отметить всех прибывшими", callback_data=admin_cb.new("danger_zone", "mark_all_arrived")),
            InlineKeyboardButton("❌ Отметить всех убывшими", callback_data=admin_cb.new("danger_zone", "mark_all_departed"))
        ],
        [
            InlineKeyboardButton("�️ Очистить все данные", callback_data=admin_cb.new("danger_zone", "clear_all_data")),
            InlineKeyboardButton("🔄 Сбросить настройки", callback_data=admin_cb.new("danger_zone", "reset_settings"))
        ],
        [
            InlineKeyboardButton("� Резервная копия", callback_data=admin_cb.new("danger_zone", "backup")),
            InlineKeyboardButton("📊 Экспорт всего", callback_data=admin_cb.new("danger_zone", "export_all"))
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("settings", ""))]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, text: str = "Да, я уверен"):
    """Клавиатура подтверждения для опасных операций"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=admin_cb.new("confirm", action)),
            InlineKeyboardButton("❌ Отменить", callback_data=admin_cb.new("cancel", ""))
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_location_keyboard(locations: list = None):
    """Клавиатура выбора локации с динамической загрузкой"""
    if not locations:
        # Базовые локации
        locations = [
            ("🏢 Офис", "office"),
            ("🏭 Производство", "production"),
            ("🚗 В пути", "traveling"),
            ("🏥 Больничный", "sick"),
            ("🏖️ Отпуск", "vacation"),
            ("📚 Обучение", "training"),
            ("🏠 Удаленка", "remote")
        ]
    
    keyboard = []
    row = []
    
    for name, location_id in locations:
        row.append(InlineKeyboardButton(name, callback_data=user_cb.new(f"location_{location_id}")))
        
        if len(row) == 3:  # 3 столбца
            keyboard.append(row)
            row = []
    
    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)
    
    # Добавляем кнопки управления
    keyboard.append([
        InlineKeyboardButton("✏️ Другое", callback_data=user_cb.new("location_custom")),
        InlineKeyboardButton("🔙 Отмена", callback_data=user_cb.new("cancel"))
    ])
    
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

def get_pagination_keyboard(current_page: int, total_pages: int, action: str, **kwargs):
    """Клавиатура пагинации"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=admin_cb.new(action, f"page_{current_page-1}")))
    
    nav_buttons.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data=admin_cb.new("info", "page_info")))
    
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=admin_cb.new(action, f"page_{current_page+1}")))
    
    keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("back", ""))])
    
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