"""
Вспомогательные функции для бота учета персонала
"""

import os
import re
import pytz
from datetime import datetime
from typing import Dict, List, Optional
from database import Database

# Создаем экземпляр базы данных
db = Database()

# Локации с эмодзи
LOCATIONS = {
    "🏥 Поликлиника": "🏥",
    "⚓ ОБРМП": "⚓",
    "🌆 Калининград": "🌆",
    "🛒 Магазин": "🛒",
    "🍲 Столовая": "🍲",
    "🏨 Госпиталь": "🏨",
    "⚙️ Рабочка": "⚙️",
    "🩺 ВВК": "🩺",
    "🏛️ МФЦ": "🏛️",
    "🚓 Патруль": "🚓",
    "📝 Другое": "📝"
}

# Список администраторов из переменных окружения
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]
    except ValueError:
        import logging
        logging.warning("⚠️ Ошибка в формате ADMIN_IDS")

def get_timezone():
    """Получение часового пояса из переменных окружения"""
    tz_name = os.getenv('TIMEZONE', 'Europe/Kaliningrad')
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        import logging
        logging.warning(f"⚠️ Неизвестный часовой пояс: {tz_name}, используется UTC")
        return pytz.UTC

def get_current_time():
    """Получение текущего времени в заданном часовом поясе"""
    tz = get_timezone()
    return datetime.now(tz)

def format_datetime(dt_str: str, format_type: str = 'full') -> str:
    """Форматирование даты и времени"""
    try:
        # Парсим datetime из строки
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
        # Конвертируем в нужный часовой пояс
        tz = get_timezone()
        dt = dt.astimezone(tz)
        
        if format_type == 'full':
            return dt.strftime("%d.%m.%Y %H:%M:%S")
        elif format_type == 'short':
            return dt.strftime("%d.%m %H:%M")
        elif format_type == 'date':
            return dt.strftime("%d.%m.%Y")
        elif format_type == 'time':
            return dt.strftime("%H:%M")
        else:
            return dt.strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        return dt_str

def validate_full_name(full_name: str) -> bool:
    """Валидация полного имени в формате 'Петров П.П.'"""
    if not full_name:
        return False
    
    # Убираем лишние пробелы
    full_name = full_name.strip()
    
    # Проверяем формат: Фамилия И.О. (где И.О. - инициалы)
    pattern = r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.[А-ЯЁ]\.$'
    
    return bool(re.match(pattern, full_name))

async def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    # Проверяем в переменных окружения
    if telegram_id in ADMIN_IDS:
        return True
    
    # Проверяем в базе данных
    try:
        await db.init()
        user = await db.get_user(telegram_id)
        if user and user.get('is_admin'):
            return True
    except Exception:
        pass
    
    return False

def get_locations_list() -> List[str]:
    """Получение списка доступных локаций"""
    return list(LOCATIONS.keys())

def get_location_emoji(location: str) -> str:
    """Получение эмодзи для локации"""
    return LOCATIONS.get(location, "📍")

def clean_location_name(location: str) -> str:
    """Очистка названия локации от эмодзи"""
    for loc_name, emoji in LOCATIONS.items():
        if location == loc_name:
            return loc_name
    return location

def get_action_emoji(action: str) -> str:
    """Получение эмодзи для действия"""
    if action == 'arrived':
        return '✅'
    elif action == 'left':
        return '❌'
    else:
        return '❓'

def get_status_indicator(has_location: bool) -> str:
    """Получение индикатора статуса (красный/зеленый кружок)"""
    return '🟢' if has_location else '🔴'

def generate_user_info(user_data: Dict) -> str:
    """Генерация информации о пользователе"""
    info = f"👤 <b>{user_data['full_name']}</b>\n"
    info += f"🆔 ID: <code>{user_data['telegram_id']}</code>\n"
    
    if user_data.get('username'):
        info += f"📝 @{user_data['username']}\n"
    
    if user_data.get('is_admin'):
        info += f"👑 <b>Администратор</b>\n"
    
    if user_data.get('registered_at'):
        reg_date = format_datetime(user_data['registered_at'], 'date')
        info += f"📅 Регистрация: {reg_date}\n"
    
    if user_data.get('last_activity'):
        last_activity = format_datetime(user_data['last_activity'], 'short')
        info += f"🕒 Последняя активность: {last_activity}\n"
    
    return info

def generate_location_summary(locations_data: Dict) -> str:
    """Генерация сводки по локациям"""
    if not locations_data:
        return "📍 <b>Все локации пусты</b>\n"
    
    summary = "📍 <b>Текущее распределение по локациям:</b>\n\n"
    
    for location, users in locations_data.items():
        emoji = get_location_emoji(location)
        summary += f"{emoji} <b>{location}</b> ({len(users)} чел.)\n"
        
        for user in users:
            entered_time = format_datetime(user['entered_at'], 'time')
            summary += f"  • {user['full_name']} ({entered_time})\n"
        
        summary += "\n"
    
    return summary

def generate_log_entry(log_data: Dict) -> str:
    """Генерация записи лога"""
    action_emoji = get_action_emoji(log_data['action'])
    location_emoji = get_location_emoji(log_data['location'])
    timestamp = format_datetime(log_data['timestamp'], 'short')
    
    action_text = "прибыл" if log_data['action'] == 'arrived' else "покинул"
    
    return f"{action_emoji} <b>{log_data['full_name']}</b> {action_text} {location_emoji} <b>{log_data['location']}</b> | {timestamp}"

def format_admin_log(log_data: Dict) -> str:
    """Форматирование записи админского лога"""
    timestamp = format_datetime(log_data['timestamp'], 'short')
    admin_name = log_data['admin_name']
    action = log_data['action']
    
    entry = f"🔧 <b>{admin_name}</b> | {action} | {timestamp}"
    
    if log_data.get('target_name'):
        entry += f" | Цель: {log_data['target_name']}"
    
    if log_data.get('details'):
        entry += f" | {log_data['details']}"
    
    return entry

def get_bro_phrases() -> List[str]:
    """Получение списка братских фраз для уведомлений"""
    return [
        "Бро, не забудь отметиться! 🤝",
        "Братишка, где ты? Отметься! 💪",
        "Друг, время отметить местоположение! 🎯",
        "Товарищ, напоминаю про отметку! ⏰",
        "Парень, не забывай отмечаться! 🚀",
        "Чувак, пора сказать где ты! 📍",
        "Братан, система ждет твоей отметки! 💻",
        "Дружище, не забудь про локацию! 🗺️",
        "Приятель, время обновить статус! 🔄",
        "Коллега, напоминание об отметке! 📝",
        "Товарищ, где твоя отметка? 🔍",
        "Братишка, система скучает! 😊",
        "Друзья, не забывайте отмечаться! 👥",
        "Бро, твоя отметка важна! ⭐",
        "Парень, пора обновить местоположение! 🎪",
        "Чувак, не теряйся из виду! 👀",
        "Дружище, отметка - это просто! ✨",
        "Приятель, давай активнее! 🚀",
        "Товарищ, не забывай про дисциплину! 📋",
        "Братан, каждая отметка важна! 💎",
        "Коллега, будь на связи! 📞",
        "Друг, система работает на тебя! 🔧",
        "Бро, покажи где ты! 🎭",
        "Парень, отметка - дело чести! 💪",
        "Чувак, не подводи команду! 🤜🤛",
        "Дружище, отметься и будь спокоен! 😌",
        "Приятель, система ждет сигнала! 📡",
        "Товарищ, будь ответственным! 💼",
        "Братишка, твоя отметка нужна! 🎯",
        "Коллега, не забывай про порядок! 📐",
        "Друг, отметка - это легко! 🌟",
        "Бро, покажи свой статус! 🔥",
        "Парень, время для отметки! ⏰",
        "Чувак, не оставляй систему в неведении! 🤔",
        "Дружище, отметься и расслабься! 😎",
        "Приятель, каждая минута важна! ⏱️",
        "Товарищ, отметка - твоя обязанность! 📜",
        "Братан, не забывай про товарищей! 🤗",
        "Коллега, будь в курсе дел! 📊",
        "Друг, отметка помогает всем! 🌍",
        "Бро, твое местоположение важно! 🌎",
        "Парень, отметься по-человечески! 😊",
        "Чувак, система верит в тебя! 💪",
        "Дружище, не подведи ожидания! 🎪",
        "Приятель, отметка - дело техники! 🔧",
        "Товарищ, будь на высоте! 🏔️",
        "Братишка, отметься и порадуй всех! 🎉",
        "Коллега, не забывай про команду! 👨‍👩‍👧‍👦",
        "Друг, отметка - признак уважения! 🙏",
        "Бро, покажи свою надежность! 🛡️"
    ]

def get_confirmation_phrases() -> List[str]:
    """Получение фраз для подтверждения действий"""
    return [
        "Ты уверен, что хочешь это сделать?",
        "Подтверди свое решение!",
        "Это серьезное действие. Продолжить?",
        "Еще раз подумай... Точно продолжить?",
        "Последний шанс передумать!",
        "Действие нельзя отменить. Продолжить?",
        "Уверен в своем выборе?",
        "Это важное решение. Подтверди!",
        "Точно хочешь это сделать?",
        "Подумай еще раз... Продолжить?"
    ]

def get_notification_times() -> tuple:
    """Получение времени уведомлений из переменных окружения"""
    morning_time = os.getenv('NOTIFICATION_MORNING_TIME', '08:00')
    evening_time = os.getenv('NOTIFICATION_EVENING_TIME', '18:00')
    
    return morning_time, evening_time

def is_notifications_enabled() -> bool:
    """Проверка, включены ли уведомления"""
    return os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'

def get_notification_interval() -> int:
    """Получение интервала уведомлений в часах"""
    try:
        return int(os.getenv('NOTIFICATION_INTERVAL_HOURS', '4'))
    except ValueError:
        return 4

def escape_markdown(text: str) -> str:
    """Экранирование символов для Markdown"""
    chars_to_escape = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars_to_escape:
        text = text.replace(char, f'\\{char}')
    return text

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def get_export_path() -> str:
    """Получение пути для экспорта файлов"""
    return os.getenv('EXPORT_PATH', 'exports/')

def get_log_path() -> str:
    """Получение пути для файлов логов"""
    return os.getenv('LOG_PATH', 'logs/')

def get_db_path() -> str:
    """Получение пути к файлу базы данных"""
    return os.getenv('DB_PATH', 'data/personnel.db')

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_user_display_name(user_data: Dict) -> str:
    """Получение отображаемого имени пользователя"""
    if user_data.get('full_name'):
        return user_data['full_name']
    elif user_data.get('username'):
        return f"@{user_data['username']}"
    else:
        return f"ID: {user_data['telegram_id']}"

def is_valid_date(date_string: str) -> bool:
    """Проверка корректности формата даты"""
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_date_range_text(days: int) -> str:
    """Получение текста для периода дней"""
    if days == 1:
        return "за последний день"
    elif days == 7:
        return "за последнюю неделю"
    elif days == 30:
        return "за последний месяц"
    else:
        return f"за последние {days} дней"

def format_duration(seconds: int) -> str:
    """Форматирование продолжительности в секундах"""
    if seconds < 60:
        return f"{seconds} сек."
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин."
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes == 0:
            return f"{hours} ч."
        else:
            return f"{hours} ч. {minutes} мин."

def is_main_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь главным админом"""
    from database import get_user_role
    return get_user_role(telegram_id) == 'main_admin'

def is_admin_or_main_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь админом или главным админом"""
    from database import get_user_role
    role = get_user_role(telegram_id)
    return role in ['admin', 'main_admin']

def get_user_role(telegram_id: int) -> str:
    """Получение роли пользователя"""
    from database import get_user_role as db_get_user_role
    return db_get_user_role(telegram_id)

def get_role_display_name(role: str) -> str:
    """Получение отображаемого названия роли"""
    role_names = {
        'soldier': 'Боец',
        'admin': 'Админ',
        'main_admin': 'Главный админ'
    }
    return role_names.get(role, 'Неизвестно')

def get_role_emoji(role: str) -> str:
    """Получение эмодзи для роли"""
    role_emojis = {
        'soldier': '👤',
        'admin': '👑',
        'main_admin': '👑'
    }
    return role_emojis.get(role, '❓')

def is_in_location(user_id: int) -> bool:
    """Проверка, находится ли боец в расположении (в части)"""
    from database import get_user_current_location
    current_location = get_user_current_location(user_id)
    return current_location is not None

def get_status_with_emoji(user_id: int) -> str:
    """Получение статуса с эмодзи (🟢 в расположении / 🔴 вне расположения)"""
    if is_in_location(user_id):
        return "🟢 В расположении"
    else:
        return "🔴 Вне расположения"

def generate_military_summary() -> str:
    """Генерация военной сводки с эмодзи"""
    from database import get_active_users_by_location, get_users_without_location, get_all_users
    
    active_locations = get_active_users_by_location()
    users_without_location = get_users_without_location()
    all_users = get_all_users()
    
    summary = "📊 <b>ВОЕННАЯ СВОДКА</b>\n\n"
    summary += f"📅 Дата: {get_current_time().strftime('%d.%m.%Y')}\n"
    summary += f"🕒 Время: {get_current_time().strftime('%H:%M')}\n\n"
    
    # Общая статистика
    total_users = len(all_users)
    in_location = total_users - len(users_without_location)
    out_location = len(users_without_location)
    
    summary += f"👥 <b>Общая численность:</b> {total_users} чел.\n"
    summary += f"🟢 <b>В расположении:</b> {in_location} чел.\n"
    summary += f"🔴 <b>Вне расположения:</b> {out_location} чел.\n\n"
    
    # Группировка по локациям
    if active_locations:
        summary += "📍 <b>Распределение по локациям:</b>\n"
        for location, users in active_locations.items():
            emoji = get_location_emoji(location)
            summary += f"{emoji} <b>{location}</b>: {len(users)} чел.\n"
            for user in users:
                summary += f"  • {user['full_name']}\n"
            summary += "\n"
    
    # Список вне расположения
    if users_without_location:
        summary += "🔴 <b>Вне расположения:</b>\n"
        for user in users_without_location:
            summary += f"• {user['full_name']}\n"
    
    return summary

def generate_location_summary_with_emojis(locations_data: Dict) -> str:
    """Генерация сводки по локациям с эмодзи статусов"""
    if not locations_data:
        return "📍 <b>Все локации пусты</b>\n"
    
    summary = "📍 <b>Текущее распределение по локациям:</b>\n\n"
    
    for location, users in locations_data.items():
        emoji = get_location_emoji(location)
        summary += f"{emoji} <b>{location}</b> ({len(users)} чел.)\n"
        
        for user in users:
            entered_time = format_datetime(user['entered_at'], 'time')
            summary += f"  🟢 {user['full_name']} ({entered_time})\n"
        
        summary += "\n"
    
    return summary

def get_action_emoji_military(action: str) -> str:
    """Получение военного эмодзи для действия"""
    if action == 'arrived':
        return '🟢'  # Зеленый кружок для прибытия
    elif action == 'left':
        return '🔴'  # Красный кружок для убытия
    else:
        return '❓'

def generate_log_entry_military(log_data: Dict) -> str:
    """Генерация записи лога с военными эмодзи"""
    action_emoji = get_action_emoji_military(log_data['action'])
    location_emoji = get_location_emoji(log_data['location'])
    timestamp = format_datetime(log_data['timestamp'], 'short')
    
    action_text = "прибыл" if log_data['action'] == 'arrived' else "убыл"
    
    return f"{action_emoji} <b>{log_data['full_name']}</b> {action_text} {location_emoji} <b>{log_data['location']}</b> | {timestamp}"