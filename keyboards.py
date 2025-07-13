"""
Клавиатуры для Telegram бота учета персонала
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from utils import get_locations_list, get_location_emoji
from typing import List, Optional

def get_main_keyboard():
    """Главная клавиатура с основными действиями"""
    keyboard = [
        [KeyboardButton("📍 Отметить местоположение")],
        [KeyboardButton("� Мой статус"), KeyboardButton("� Справка")],
        [KeyboardButton("� Админ-панель")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_locations_keyboard():
    """Клавиатура для выбора локации"""
    locations = get_locations_list()
    keyboard = []
    
    # Разбиваем локации на строки по 2 кнопки
    for i in range(0, len(locations), 2):
        row = []
        for j in range(2):
            if i + j < len(locations):
                location = locations[i + j]
                emoji = get_location_emoji(location)
                row.append(InlineKeyboardButton(
                    f"{emoji} {location.replace(emoji + ' ', '')}",
                    callback_data=f"location:{location}"
                ))
        keyboard.append(row)
    
    # Добавляем кнопку отмены
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    
    return InlineKeyboardMarkup(keyboard)

def get_action_keyboard(location: str):
    """Клавиатура для выбора действия (прибыл/покинул)"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибыл", callback_data=f"action:arrived:{location}"),
            InlineKeyboardButton("❌ Покинул", callback_data=f"action:left:{location}")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_locations")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    """Главная админская клавиатура"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Пользователи", callback_data="admin:users"),
            InlineKeyboardButton("📊 Статистика", callback_data="admin:stats")
        ],
        [
            InlineKeyboardButton("📋 Логи", callback_data="admin:logs"),
            InlineKeyboardButton("� Локации", callback_data="admin:locations")
        ],
        [
            InlineKeyboardButton("📁 Экспорт", callback_data="admin:export"),
            InlineKeyboardButton("🔧 Управление", callback_data="admin:manage")
        ],
        [
            InlineKeyboardButton("🧹 Очистка", callback_data="admin:cleanup"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="admin:settings")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_users_keyboard():
    """Клавиатура для управления пользователями"""
    keyboard = [
        [
            InlineKeyboardButton("� Список пользователей", callback_data="admin:users:list"),
            InlineKeyboardButton("� Поиск пользователя", callback_data="admin:users:search")
        ],
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data="admin:users:add_admin"),
            InlineKeyboardButton("➖ Удалить админа", callback_data="admin:users:remove_admin")
        ],
        [
            InlineKeyboardButton("🗑️ Удалить пользователя", callback_data="admin:users:delete"),
            InlineKeyboardButton("� Статистика пользователей", callback_data="admin:users:stats")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_logs_keyboard():
    """Клавиатура для просмотра логов"""
    keyboard = [
        [
            InlineKeyboardButton("📋 Все логи", callback_data="admin:logs:all"),
            InlineKeyboardButton("🔍 Поиск по имени", callback_data="admin:logs:search_name")
        ],
        [
            InlineKeyboardButton("📅 Поиск по дате", callback_data="admin:logs:search_date"),
            InlineKeyboardButton("👤 Мои действия", callback_data="admin:logs:my_actions")
        ],
        [
            InlineKeyboardButton("🔧 Админские логи", callback_data="admin:logs:admin"),
            InlineKeyboardButton("📊 Статистика логов", callback_data="admin:logs:stats")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_locations_admin_keyboard():
    """Клавиатура для управления локациями"""
    keyboard = [
        [
            InlineKeyboardButton("📍 Текущие локации", callback_data="admin:locations:current"),
            InlineKeyboardButton("� Статистика", callback_data="admin:locations:stats")
        ],
        [
            InlineKeyboardButton("🏠 Все покинули", callback_data="admin:locations:clear_all"),
            InlineKeyboardButton("🎯 Массовое прибытие", callback_data="admin:locations:mass_arrival")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_export_keyboard():
    """Клавиатура для экспорта данных"""
    keyboard = [
        [
            InlineKeyboardButton("� CSV", callback_data="admin:export:csv"),
            InlineKeyboardButton("� Excel", callback_data="admin:export:excel")
        ],
        [
            InlineKeyboardButton("� PDF", callback_data="admin:export:pdf"),
            InlineKeyboardButton("� Все форматы", callback_data="admin:export:all")
        ],
        [
            InlineKeyboardButton("📅 За период", callback_data="admin:export:period"),
            InlineKeyboardButton("👤 По пользователю", callback_data="admin:export:user")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_manage_keyboard():
    """Клавиатура для управления системой"""
    keyboard = [
        [
            InlineKeyboardButton("💾 Бэкап БД", callback_data="admin:manage:backup"),
            InlineKeyboardButton("� Восстановить БД", callback_data="admin:manage:restore")
        ],
        [
            InlineKeyboardButton("📊 Статистика системы", callback_data="admin:manage:system_stats"),
            InlineKeyboardButton("🔄 Перезагрузить", callback_data="admin:manage:restart")
        ],
        [
            InlineKeyboardButton("📋 Системные логи", callback_data="admin:manage:system_logs"),
            InlineKeyboardButton("🔧 Обслуживание", callback_data="admin:manage:maintenance")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cleanup_keyboard():
    """Клавиатура для очистки данных"""
    keyboard = [
        [
            InlineKeyboardButton("🗑️ Очистить логи", callback_data="admin:cleanup:logs"),
            InlineKeyboardButton("🗑️ Очистить админ-логи", callback_data="admin:cleanup:admin_logs")
        ],
        [
            InlineKeyboardButton("🏠 Сбросить локации", callback_data="admin:cleanup:locations"),
            InlineKeyboardButton("🔄 Полная очистка", callback_data="admin:cleanup:full")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cleanup_period_keyboard():
    """Клавиатура для выбора периода очистки"""
    keyboard = [
        [
            InlineKeyboardButton("📅 За день", callback_data="admin:cleanup:period:day"),
            InlineKeyboardButton("� За неделю", callback_data="admin:cleanup:period:week")
        ],
        [
            InlineKeyboardButton("� За месяц", callback_data="admin:cleanup:period:month"),
            InlineKeyboardButton("🗑️ Все", callback_data="admin:cleanup:period:all")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:cleanup")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_mass_arrival_keyboard():
    """Клавиатура для массового прибытия"""
    locations = get_locations_list()
    keyboard = []
    
    # Разбиваем локации на строки по 2 кнопки
    for i in range(0, len(locations), 2):
        row = []
        for j in range(2):
            if i + j < len(locations):
                location = locations[i + j]
                emoji = get_location_emoji(location)
                row.append(InlineKeyboardButton(
                    f"{emoji} {location.replace(emoji + ' ', '')}",
                    callback_data=f"admin:mass_arrival:{location}"
                ))
        keyboard.append(row)
    
    # Добавляем кнопки управления
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin:locations")])
    
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str):
    """Клавиатура для подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, выполнить", callback_data=f"confirm:{action}"),
            InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_double_confirmation_keyboard(action: str):
    """Клавиатура для двойного подтверждения критических действий"""
    keyboard = [
        [
            InlineKeyboardButton("⚠️ Точно выполнить!", callback_data=f"double_confirm:{action}"),
            InlineKeyboardButton("🛑 Отменить", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(page: int, total_pages: int, callback_prefix: str):
    """Клавиатура для пагинации"""
    keyboard = []
    
    # Строка с навигацией
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Пред", callback_data=f"{callback_prefix}:page:{page-1}"))
    
    nav_row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("След ➡️", callback_data=f"{callback_prefix}:page:{page+1}"))
    
    keyboard.append(nav_row)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"{callback_prefix}:back")])
    
    return InlineKeyboardMarkup(keyboard)

def get_user_actions_keyboard(user_id: int):
    """Клавиатура для действий с пользователем"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Статистика", callback_data=f"admin:user:{user_id}:stats"),
            InlineKeyboardButton("📋 История", callback_data=f"admin:user:{user_id}:history")
        ],
        [
            InlineKeyboardButton("👑 Сделать админом", callback_data=f"admin:user:{user_id}:make_admin"),
            InlineKeyboardButton("👤 Убрать админа", callback_data=f"admin:user:{user_id}:remove_admin")
        ],
        [
            InlineKeyboardButton("🗑️ Удалить", callback_data=f"admin:user:{user_id}:delete"),
            InlineKeyboardButton("📝 Изменить", callback_data=f"admin:user:{user_id}:edit")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:users")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Простая клавиатура с кнопкой отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback_data: str):
    """Простая клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """Клавиатура для настроек"""
    keyboard = [
        [
            InlineKeyboardButton("⏰ Уведомления", callback_data="admin:settings:notifications"),
            InlineKeyboardButton("🌍 Часовой пояс", callback_data="admin:settings:timezone")
        ],
        [
            InlineKeyboardButton("🔧 Система", callback_data="admin:settings:system"),
            InlineKeyboardButton("📊 Отчеты", callback_data="admin:settings:reports")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_settings_keyboard():
    """Клавиатура для настроек уведомлений"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Включить", callback_data="admin:settings:notifications:on"),
            InlineKeyboardButton("🔕 Выключить", callback_data="admin:settings:notifications:off")
        ],
        [
            InlineKeyboardButton("⏰ Время", callback_data="admin:settings:notifications:time"),
            InlineKeyboardButton("🔄 Интервал", callback_data="admin:settings:notifications:interval")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_inline_menu_keyboard(items: List[tuple], callback_prefix: str, back_callback: str = None):
    """Универсальная клавиатура для меню"""
    keyboard = []
    
    # Разбиваем элементы на строки по 2 кнопки
    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                text, callback = items[i + j]
                row.append(InlineKeyboardButton(text, callback_data=f"{callback_prefix}:{callback}"))
        keyboard.append(row)
    
    # Добавляем кнопку назад если указана
    if back_callback:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(yes_callback: str, no_callback: str = "cancel"):
    """Клавиатура да/нет"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=yes_callback),
            InlineKeyboardButton("❌ Нет", callback_data=no_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)