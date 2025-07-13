"""
Дополнительные клавиатуры для админ-панели v2.0
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

def get_confirmation_keyboard(action: str):
    """Клавиатура подтверждения действия"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm:{action}"),
            InlineKeyboardButton("❌ Отменить", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_double_confirmation_keyboard(action: str):
    """Клавиатура двойного подтверждения для опасных действий"""
    keyboard = [
        [
            InlineKeyboardButton("🚨 ПОДТВЕРДИТЬ", callback_data=f"double_confirm:{action}"),
            InlineKeyboardButton("❌ Отменить", callback_data="cancel")
        ],
        [InlineKeyboardButton("⚠️ Я понимаю последствия", callback_data=f"double_confirm:{action}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback_data: str):
    """Клавиатура с кнопкой назад"""
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=callback_data)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_export_format_keyboard():
    """Клавиатура выбора формата экспорта"""
    keyboard = [
        [
            InlineKeyboardButton("📄 CSV", callback_data="admin:export:format:csv"),
            InlineKeyboardButton("📊 Excel", callback_data="admin:export:format:excel")
        ],
        [
            InlineKeyboardButton("📋 Все форматы", callback_data="admin:export:format:all"),
            InlineKeyboardButton("🔍 Фильтрованный", callback_data="admin:export:format:filtered")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:journal:export")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_recipients_keyboard():
    """Клавиатура выбора получателей уведомлений"""
    keyboard = [
        [
            InlineKeyboardButton("👑 Только админы", callback_data="admin:notifications:recipients:admins"),
            InlineKeyboardButton("👥 Все пользователи", callback_data="admin:notifications:recipients:all")
        ],
        [
            InlineKeyboardButton("🎯 По группам", callback_data="admin:notifications:recipients:groups"),
            InlineKeyboardButton("👤 Выборочно", callback_data="admin:notifications:recipients:selective")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings:notifications")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_notification_event_types_keyboard():
    """Клавиатура настройки типов событий для уведомлений"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Прибытие", callback_data="admin:notifications:events:arrival"),
            InlineKeyboardButton("❌ Убытие", callback_data="admin:notifications:events:departure")
        ],
        [
            InlineKeyboardButton("👤 Регистрация", callback_data="admin:notifications:events:registration"),
            InlineKeyboardButton("🔧 Админские действия", callback_data="admin:notifications:events:admin")
        ],
        [
            InlineKeyboardButton("📊 Статистика", callback_data="admin:notifications:events:stats"),
            InlineKeyboardButton("⚠️ Системные", callback_data="admin:notifications:events:system")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings:notifications")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_silence_mode_keyboard():
    """Клавиатура настройки режима тишины"""
    keyboard = [
        [
            InlineKeyboardButton("🔇 Включить тишину", callback_data="admin:notifications:silence:on"),
            InlineKeyboardButton("🔊 Выключить тишину", callback_data="admin:notifications:silence:off")
        ],
        [
            InlineKeyboardButton("⏰ На 1 час", callback_data="admin:notifications:silence:1h"),
            InlineKeyboardButton("⏰ На 4 часа", callback_data="admin:notifications:silence:4h")
        ],
        [
            InlineKeyboardButton("⏰ На 8 часов", callback_data="admin:notifications:silence:8h"),
            InlineKeyboardButton("⏰ До завтра", callback_data="admin:notifications:silence:tomorrow")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings:notifications")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_maintenance_keyboard():
    """Клавиатура обслуживания системы"""
    keyboard = [
        [
            InlineKeyboardButton("💾 Создать бэкап", callback_data="admin:maintenance:backup"),
            InlineKeyboardButton("🔄 Восстановить", callback_data="admin:maintenance:restore")
        ],
        [
            InlineKeyboardButton("🔧 Оптимизировать БД", callback_data="admin:maintenance:optimize"),
            InlineKeyboardButton("📊 Проверить целостность", callback_data="admin:maintenance:integrity")
        ],
        [
            InlineKeyboardButton("🗑️ Очистить логи", callback_data="admin:maintenance:clean_logs"),
            InlineKeyboardButton("📁 Очистить экспорты", callback_data="admin:maintenance:clean_exports")
        ],
        [
            InlineKeyboardButton("📈 Статистика системы", callback_data="admin:maintenance:stats"),
            InlineKeyboardButton("🔄 Перезапуск", callback_data="admin:maintenance:restart")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_management_keyboard():
    """Клавиатура управления админами"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить админа", callback_data="admin:admins:add"),
            InlineKeyboardButton("➖ Удалить админа", callback_data="admin:admins:remove")
        ],
        [
            InlineKeyboardButton("📋 Список админов", callback_data="admin:admins:list"),
            InlineKeyboardButton("🔐 Права доступа", callback_data="admin:admins:permissions")
        ],
        [
            InlineKeyboardButton("📊 Активность админов", callback_data="admin:admins:activity"),
            InlineKeyboardButton("⚙️ Настройки ролей", callback_data="admin:admins:roles")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_system_settings_keyboard():
    """Клавиатура системных настроек"""
    keyboard = [
        [
            InlineKeyboardButton("🌍 Часовой пояс", callback_data="admin:system:timezone"),
            InlineKeyboardButton("📅 Формат даты", callback_data="admin:system:date_format")
        ],
        [
            InlineKeyboardButton("🔒 Безопасность", callback_data="admin:system:security"),
            InlineKeyboardButton("📝 Логирование", callback_data="admin:system:logging")
        ],
        [
            InlineKeyboardButton("💾 Хранение данных", callback_data="admin:system:storage"),
            InlineKeyboardButton("🔄 Автоматизация", callback_data="admin:system:automation")
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin:settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(yes_callback: str, no_callback: str = "cancel"):
    """Универсальная клавиатура Да/Нет"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=yes_callback),
            InlineKeyboardButton("❌ Нет", callback_data=no_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pagination_keyboard(page: int, total_pages: int, callback_prefix: str, back_callback: str = None):
    """Клавиатура пагинации"""
    keyboard = []
    
    # Кнопки навигации
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}:page:{page-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="no_action"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}:page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопка назад
    if back_callback:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)

def get_inline_menu_keyboard(items: List[tuple], callback_prefix: str, back_callback: str = None):
    """Универсальная клавиатура для меню"""
    keyboard = []
    
    for text, callback_suffix in items:
        keyboard.append([InlineKeyboardButton(text, callback_data=f"{callback_prefix}:{callback_suffix}")])
    
    if back_callback:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback)])
    
    return InlineKeyboardMarkup(keyboard)