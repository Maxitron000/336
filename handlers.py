"""
Обработчики команд и сообщений для Telegram бота учета персонала
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from database import (
    get_user, add_user, update_user_activity, add_location_log,
    get_user_current_location, get_user_location_history,
    add_admin_log, get_active_users_by_location, get_users_without_location
)
from keyboards import (
    get_main_keyboard, get_locations_keyboard, get_action_keyboard,
    get_admin_keyboard, get_cancel_keyboard
)
from utils import (
    validate_full_name, is_admin, get_locations_list, 
    generate_user_info, generate_location_summary,
    generate_log_entry, get_current_time, format_datetime
)
from admin import handle_admin_callback

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Получаем пользователя из базы
    user = get_user(user_id)
    
    if not user:
        # Новый пользователь
        await update.message.reply_text(
            "👋 Добро пожаловать в систему учета персонала!\n\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Используйте команду /register для регистрации.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Обновляем активность пользователя
    update_user_activity(user_id)
    
    # Приветственное сообщение
    welcome_text = f"👋 Привет, <b>{user['full_name']}</b>!\n\n"
    welcome_text += "📍 Система учета персонала готова к работе.\n\n"
    
    current_location = get_user_current_location(user_id)
    if current_location:
        welcome_text += f"📍 Текущее местоположение: <b>{current_location}</b>\n\n"
    else:
        welcome_text += "📍 Местоположение не указано\n\n"
    
    welcome_text += "Выберите действие:"
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /register"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Проверяем, не зарегистрирован ли уже пользователь
    existing_user = get_user(user_id)
    if existing_user:
        await update.message.reply_text(
            f"✅ Вы уже зарегистрированы как <b>{existing_user['full_name']}</b>",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Сохраняем состояние ожидания ФИО
    context.user_data['waiting_for_fullname'] = True
    
    await update.message.reply_text(
        "📝 <b>Регистрация в системе</b>\n\n"
        "Введите ваше ФИО в формате: <b>Фамилия И.О.</b>\n"
        "Например: <code>Петров П.П.</code>\n\n"
        "⚠️ Обязательно указывайте инициалы с точками!",
        parse_mode='HTML',
        reply_markup=get_cancel_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Справка по боту учета персонала</b>

<b>Основные команды:</b>
• /start - Запуск бота
• /register - Регистрация в системе
• /status - Мой текущий статус
• /help - Эта справка

<b>Основные функции:</b>
📍 <b>Отметить местоположение</b> - Указать где вы находитесь
📊 <b>Мой статус</b> - Просмотр текущего статуса
🔧 <b>Админ-панель</b> - Для администраторов

<b>Доступные локации:</b>
🏥 Поликлиника
⚓ ОБРМП
🌆 Калининград
🛒 Магазин
🍲 Столовая
🏨 Госпиталь
⚙️ Рабочка
🩺 ВВК
🏛️ МФЦ
🚓 Патруль

<b>Действия с локациями:</b>
✅ Прибыл - Отметить прибытие
❌ Покинул - Отметить убытие

<b>Для администраторов:</b>
• Управление пользователями
• Просмотр логов и статистики
• Экспорт данных
• Системные настройки

❓ По вопросам работы бота обращайтесь к администратору.
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    user_id = update.effective_user.id
    
    user = get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы в системе.\n"
            "Используйте команду /register для регистрации.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Обновляем активность
    update_user_activity(user_id)
    
    # Информация о пользователе
    status_text = generate_user_info(user)
    
    # Текущее местоположение
    current_location = get_user_current_location(user_id)
    if current_location:
        status_text += f"\n📍 <b>Текущее местоположение:</b> {current_location}\n"
    else:
        status_text += f"\n📍 <b>Местоположение не указано</b>\n"
    
    # Последние действия
    recent_history = get_user_location_history(user_id, days=7)
    if recent_history:
        status_text += f"\n📋 <b>Последние действия:</b>\n"
        for log in recent_history[:5]:  # Показываем только последние 5
            log_entry = generate_log_entry(log)
            status_text += f"• {log_entry}\n"
    
    await update.message.reply_text(
        status_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /cancel"""
    # Очищаем состояние пользователя
    context.user_data.clear()
    
    if update.message:
        await update.message.reply_text(
            "❌ Действие отменено.",
            reply_markup=get_main_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            "❌ Действие отменено.",
            reply_markup=get_main_keyboard()
        )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /admin"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text(
            "❌ У вас нет прав администратора.",
            reply_markup=get_main_keyboard()
        )
        return
    
    user = get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы в системе.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Логируем вход в админ-панель
    add_admin_log(user_id, "Вход в админ-панель")
    
    admin_text = f"🔧 <b>Админ-панель</b>\n\n"
    admin_text += f"Добро пожаловать, <b>{user['full_name']}</b>!\n\n"
    admin_text += "Выберите действие:"
    
    await update.message.reply_text(
        admin_text,
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем, ждем ли мы ввод ФИО
    if context.user_data.get('waiting_for_fullname'):
        await handle_fullname_input(update, context, text)
        return
    
    # Проверяем, ждем ли мы ввод для поиска
    if context.user_data.get('waiting_for_search'):
        await handle_search_input(update, context, text)
        return
    
    # Обработка кнопок главного меню
    if text == "📍 Отметить местоположение":
        await handle_location_request(update, context)
    elif text == "📊 Мой статус":
        await status_command(update, context)
    elif text == "📋 Справка":
        await help_command(update, context)
    elif text == "🔧 Админ-панель":
        await admin_command(update, context)
    else:
        # Неизвестная команда
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте кнопки меню или /help для справки.",
            reply_markup=get_main_keyboard()
        )

async def handle_fullname_input(update: Update, context: ContextTypes.DEFAULT_TYPE, full_name: str):
    """Обработка ввода ФИО при регистрации"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Валидация ФИО
    if not validate_full_name(full_name):
        await update.message.reply_text(
            "❌ <b>Неверный формат ФИО!</b>\n\n"
            "Используйте формат: <b>Фамилия И.О.</b>\n"
            "Например: <code>Петров П.П.</code>\n\n"
            "⚠️ Обязательно указывайте инициалы с точками!",
            parse_mode='HTML',
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Регистрируем пользователя
    if add_user(user_id, full_name, username):
        # Очищаем состояние
        context.user_data.clear()
        
        await update.message.reply_text(
            f"✅ <b>Регистрация завершена!</b>\n\n"
            f"Добро пожаловать, <b>{full_name}</b>!\n\n"
            f"Теперь вы можете отмечать свое местоположение.",
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        
        logger.info(f"Новый пользователь зарегистрирован: {full_name} (ID: {user_id})")
    else:
        await update.message.reply_text(
            "❌ Ошибка при регистрации. Попробуйте еще раз.",
            reply_markup=get_cancel_keyboard()
        )

async def handle_search_input(update: Update, context: ContextTypes.DEFAULT_TYPE, search_text: str):
    """Обработка ввода для поиска"""
    # Передаем управление в админ-модуль
    await handle_admin_callback(update, context, f"search_input:{search_text}")

async def handle_location_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка запроса на отметку местоположения"""
    user_id = update.effective_user.id
    
    # Проверяем регистрацию
    user = get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ Вы не зарегистрированы в системе.\n"
            "Используйте команду /register для регистрации.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Обновляем активность
    update_user_activity(user_id)
    
    # Показываем клавиатуру с локациями
    await update.message.reply_text(
        "📍 <b>Выберите локацию:</b>",
        parse_mode='HTML',
        reply_markup=get_locations_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на inline кнопки"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    try:
        await query.answer()
        
        # Проверяем регистрацию пользователя
        user = get_user(user_id)
        if not user and not data.startswith('cancel'):
            await query.edit_message_text(
                "❌ Вы не зарегистрированы в системе.\n"
                "Используйте команду /register для регистрации."
            )
            return
        
        # Обновляем активность
        if user:
            update_user_activity(user_id)
        
        # Обработка различных callback_data
        if data == "cancel":
            await handle_cancel_callback(update, context)
        elif data.startswith("location:"):
            await handle_location_callback(update, context, data)
        elif data.startswith("action:"):
            await handle_action_callback(update, context, data)
        elif data == "back_to_locations":
            await handle_back_to_locations(update, context)
        elif data == "back_to_main":
            await handle_back_to_main(update, context)
        elif data.startswith("admin:"):
            await handle_admin_callback(update, context, data)
        elif data.startswith("confirm:"):
            await handle_confirmation_callback(update, context, data)
        elif data.startswith("double_confirm:"):
            await handle_double_confirmation_callback(update, context, data)
        else:
            await query.edit_message_text(
                "❌ Неизвестная команда.",
                reply_markup=get_cancel_keyboard()
            )
            
    except TelegramError as e:
        logger.error(f"Ошибка в button_handler: {e}")
        try:
            await query.message.reply_text(
                "⚠️ Произошла ошибка. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )
        except:
            pass

async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отмены действия"""
    context.user_data.clear()
    
    await update.callback_query.edit_message_text(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard()
    )

async def handle_location_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка выбора локации"""
    location = data.split(":", 1)[1]
    
    # Проверяем, что локация существует
    if location not in get_locations_list():
        await update.callback_query.edit_message_text(
            "❌ Неизвестная локация.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Показываем клавиатуру с действиями
    await update.callback_query.edit_message_text(
        f"📍 <b>Локация: {location}</b>\n\n"
        f"Выберите действие:",
        parse_mode='HTML',
        reply_markup=get_action_keyboard(location)
    )

async def handle_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка выбора действия (прибыл/покинул)"""
    parts = data.split(":", 2)
    if len(parts) != 3:
        await update.callback_query.edit_message_text(
            "❌ Неверный формат команды.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    action = parts[1]  # arrived или left
    location = parts[2]
    user_id = update.callback_query.from_user.id
    
    # Проверяем валидность действия
    if action not in ['arrived', 'left']:
        await update.callback_query.edit_message_text(
            "❌ Неизвестное действие.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Проверяем валидность локации
    if location not in get_locations_list():
        await update.callback_query.edit_message_text(
            "❌ Неизвестная локация.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    # Получаем текущее местоположение пользователя
    current_location = get_user_current_location(user_id)
    
    # Проверяем логику действий
    if action == 'arrived':
        if current_location == location:
            await update.callback_query.edit_message_text(
                f"⚠️ Вы уже находитесь в локации <b>{location}</b>.",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return
    elif action == 'left':
        if current_location != location:
            await update.callback_query.edit_message_text(
                f"⚠️ Вы не находитесь в локации <b>{location}</b>.\n"
                f"Ваше текущее местоположение: <b>{current_location or 'не указано'}</b>",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return
    
    # Записываем действие в базу
    if add_location_log(user_id, location, action):
        user = get_user(user_id)
        action_text = "прибыл в" if action == 'arrived' else "покинул"
        emoji = "✅" if action == 'arrived' else "❌"
        
        current_time = get_current_time()
        time_str = current_time.strftime("%H:%M")
        
        success_text = f"{emoji} <b>{user['full_name']}</b> {action_text} <b>{location}</b>\n"
        success_text += f"🕒 Время: {time_str}\n\n"
        
        # Показываем текущий статус
        new_location = get_user_current_location(user_id)
        if new_location:
            success_text += f"📍 Текущее местоположение: <b>{new_location}</b>"
        else:
            success_text += f"📍 Местоположение не указано"
        
        await update.callback_query.edit_message_text(
            success_text,
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        
        logger.info(f"Пользователь {user['full_name']} (ID: {user_id}) {action_text} {location}")
    else:
        await update.callback_query.edit_message_text(
            "❌ Ошибка при записи действия. Попробуйте еще раз.",
            reply_markup=get_cancel_keyboard()
        )

async def handle_back_to_locations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору локаций"""
    await update.callback_query.edit_message_text(
        "📍 <b>Выберите локацию:</b>",
        parse_mode='HTML',
        reply_markup=get_locations_keyboard()
    )

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к главному меню"""
    user_id = update.callback_query.from_user.id
    user = get_user(user_id)
    
    if user:
        welcome_text = f"👋 <b>{user['full_name']}</b>\n\n"
        current_location = get_user_current_location(user_id)
        if current_location:
            welcome_text += f"📍 Текущее местоположение: <b>{current_location}</b>\n\n"
        else:
            welcome_text += "📍 Местоположение не указано\n\n"
        welcome_text += "Выберите действие:"
    else:
        welcome_text = "👋 Добро пожаловать!\n\nВыберите действие:"
    
    await update.callback_query.edit_message_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=get_main_keyboard()
    )

async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка подтверждения действия"""
    action = data.split(":", 1)[1]
    await handle_admin_callback(update, context, f"execute:{action}")

async def handle_double_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    """Обработка двойного подтверждения действия"""
    action = data.split(":", 1)[1]
    await handle_admin_callback(update, context, f"final_execute:{action}")

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неизвестных сообщений"""
    await update.message.reply_text(
        "❓ Неизвестная команда.\n"
        "Используйте кнопки меню или /help для справки.",
        reply_markup=get_main_keyboard()
    )