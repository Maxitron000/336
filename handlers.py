"""
Обработчики команд и сообщений для Telegram бота учета персонала
"""

import logging
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from database import Database
from admin import AdminPanel
from notifications import NotificationSystem
from keyboards import (
    get_main_keyboard, get_location_keyboard, get_cancel_keyboard,
    admin_cb, user_cb, get_pagination_keyboard,
    get_arrival_keyboard, get_departure_keyboard
)
from utils import (
    is_admin, get_locations_list, 
    generate_user_info, generate_location_summary,
    generate_log_entry, get_current_time, format_datetime
)
from admin import handle_admin_callback

logger = logging.getLogger(__name__)

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_custom_location = State()
    waiting_for_note = State()
    waiting_for_admin_action = State()
    waiting_for_personnel_action = State()
    waiting_for_settings_action = State()
    waiting_for_confirmation = State()

def register_handlers(dp: Dispatcher, admin_panel: AdminPanel, notification_system: NotificationSystem):
    """Регистрация всех обработчиков"""
    
    # Обработчики команд
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_message_handler(status_command, commands=['status'])
    dp.register_message_handler(admin_command, commands=['admin'])
    
    # Обработчики текстовых сообщений
    dp.register_message_handler(handle_text_message, content_types=['text'])
    
    # Обработчики callback-запросов
    dp.register_callback_query_handler(handle_callback_query, lambda c: True)

async def start_command(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Удаляем сообщение с командой для чистоты чата
    try:
        await message.delete()
    except:
        pass
    
    # Проверяем, является ли пользователь админом
    is_admin = await admin_panel.is_admin(user_id)
    
    if is_admin:
        # Показываем админ-панель
        await message.answer(
            "🏠 *Главное меню админ-панели*\n\n"
            "Выберите нужный раздел:",
            reply_markup=admin_panel.get_keyboard_for_action("dashboard"),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if user:
            # Показываем обычное меню
            await message.answer(
                "👋 *Добро пожаловать в систему учета личного состава!*\n\n"
                "Выберите действие:",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Регистрируем нового пользователя
            await message.answer(
                "👋 *Добро пожаловать!*\n\n"
                "Для начала работы необходимо зарегистрироваться.\n\n"
                "📝 *Введите ваше ФИО:*\n"
                "Пример: Иванов И.И.\n"
                "Формат: Фамилия Инициалы\n"
                "Минимум 5 символов, только кириллица",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            await UserStates.waiting_for_name.set()

async def help_command(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 *Справка по командам:*\n\n"
        "🔹 `/start` - Главное меню\n"
        "🔹 `/help` - Эта справка\n"
        "🔹 `/status` - Статус системы\n\n"
        "💡 *Для админов:*\n"
        "🔹 `/admin` - Админ-панель\n"
        "🔹 `/export` - Экспорт данных\n"
        "🔹 `/backup` - Резервная копия\n\n"
        "📱 *Основные действия:*\n"
        "🔹 Нажмите '✅ Прибыл' для отметки прибытия\n"
        "🔹 Нажмите '� Убыл' для отметки убытия\n"
        "🔹 Нажмите '📍 Локация' для смены местоположения\n"
        "🔹 Нажмите '📊 Мой статус' для просмотра вашего статуса"
    )
    
    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)

async def status_command(message: types.Message):
    """Обработчик команды /status"""
    try:
        # Получаем статистику
        total_users = await admin_panel.db.get_total_users()
        present_users = await admin_panel.db.get_present_users()
        absent_users = await admin_panel.db.get_absent_users_count()
        
        status_text = (
            "📊 *Статус системы:*\n\n"
            f"👥 Всего бойцов: {total_users}\n"
            f"✅ Присутствуют: {present_users}\n"
            f"❌ Отсутствуют: {absent_users}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}"
        )
        
        await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await message.answer("❌ Ошибка получения статуса системы")

async def admin_command(message: types.Message):
    """Обработчик команды /admin"""
    user_id = message.from_user.id
    
    if await admin_panel.is_admin(user_id):
        await message.answer(
            "🏠 *Главное меню админ-панели*\n\n"
            "Выберите нужный раздел:",
            reply_markup=admin_panel.get_keyboard_for_action("dashboard"),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("❌ У вас нет доступа к админ-панели")

async def handle_text_message(message: types.Message, state: FSMContext):
    """Обработчик текстовых сообщений"""
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    if current_state == UserStates.waiting_for_name.state:
        await handle_name_input(message, state, text)
    elif current_state == UserStates.waiting_for_custom_location.state:
        await handle_custom_location_input(message, state, text)
    elif current_state == UserStates.waiting_for_note.state:
        await handle_note_input(message, state, text)
    else:
        # Обрабатываем обычные команды
        await handle_regular_commands(message, text)

async def handle_name_input(message: types.Message, state: FSMContext, name: str):
    """Обработка ввода имени при регистрации с валидацией"""
    user_id = message.from_user.id
    
    try:
        # Валидация ФИО
        is_valid, error_msg = admin_panel.db.validate_full_name(name)
        if not is_valid:
            await message.answer(
                f"❌ *Ошибка валидации:*\n{error_msg}\n\n"
                f"📝 *Правильный формат:*\n"
                f"• Иванов И.И.\n"
                f"• Петров А.А.\n"
                f"• Сидоров В.В.\n\n"
                f"Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Проверяем, не существует ли уже пользователь с таким именем
        if await admin_panel.db.check_user_exists(name=name):
            await message.answer(
                f"⚠️ *Пользователь с таким ФИО уже существует:*\n{name}\n\n"
                f"Если это вы, обратитесь к администратору.",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Добавляем пользователя
        success, result_msg = await admin_panel.db.add_user(user_id, name)
        
        if success:
            await message.answer(
                f"✅ *Регистрация завершена!*\n\n"
                f"👤 ФИО: {name}\n"
                f"🆔 ID: {user_id}\n\n"
                f"Теперь вы можете использовать все функции бота.",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Уведомляем командиров
            await notification_system.send_user_added_notification(name)
        else:
            await message.answer(
                f"❌ *Ошибка регистрации:*\n{result_msg}\n\n"
                f"Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте еще раз.",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.finish()

async def handle_note_input(message: types.Message, state: FSMContext, note: str):
    """Обработка ввода заметки"""
    user_id = message.from_user.id
    
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        action = state_data.get('action')
        location = state_data.get('location')
        
        if action == 'arrival':
            success, result_msg = await admin_panel.db.mark_attendance(user_id, location, note)
        elif action == 'departure':
            success, result_msg = await admin_panel.db.mark_departure(user_id, location, note)
        else:
            success, result_msg = False, "Неизвестное действие"
        
        if success:
            user = await admin_panel.db.get_user(user_id)
            action_text = "прибытия" if action == 'arrival' else "убытия"
            
            await message.answer(
                f"✅ *Отметка {action_text} зарегистрирована!*\n\n"
                f"👤 Боец: {user['name']}\n"
                f"📍 Локация: {location}\n"
                f"� Заметка: {note}\n"
                f"� Время: {datetime.now().strftime('%H:%M:%S')}",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Отправляем уведомления командирам
            if action == 'arrival':
                await notification_system.send_arrival_notification(user['name'], location)
            else:
                await notification_system.send_departure_notification(user['name'], location)
        else:
            await message.answer(
                f"❌ *Ошибка отметки:*\n{result_msg}",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки заметки: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
    
    await state.finish()

async def handle_custom_location_input(message: types.Message, state: FSMContext, location: str):
    """Обработка ввода кастомной локации"""
    user_id = message.from_user.id
    
    try:
        # Сохраняем локацию в состоянии и запрашиваем заметку
        await state.update_data(location=location)
        
        await message.answer(
            f"📍 *Локация выбрана:* {location}\n\n"
            f"📝 *Добавьте заметку (необязательно):*\n"
            f"Например: причина, детали, комментарий\n\n"
            f"Или нажмите 'Пропустить'",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Переходим к ожиданию заметки
        await UserStates.waiting_for_note.set()
        
    except Exception as e:
        logger.error(f"Ошибка обработки кастомной локации: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
        await state.finish()

async def handle_regular_commands(message: types.Message, text: str):
    """Обработка обычных команд"""
    user_id = message.from_user.id
    
    if text == "✅ Прибыл":
        await handle_arrival(message)
    elif text == "🚪 Убыл":
        await handle_departure(message)
    elif text == "📍 Локация":
        await handle_location_selection(message)
    elif text == "📊 Мой статус":
        await handle_my_status(message)
    elif text == "📖 Помощь":
        await help_command(message)
    elif text == "⚙️ Настройки":
        await handle_settings(message)
    else:
        await message.answer(
            "❓ Неизвестная команда. Используйте кнопки меню или /help для справки.",
            reply_markup=get_main_keyboard()
        )

async def handle_arrival(message: types.Message):
    """Обработка отметки прибытия"""
    user_id = message.from_user.id
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Проверяем текущий статус
        current_status = await admin_panel.db.get_user_status(user_id)
        if current_status == 'present':
            await message.answer(
                "ℹ️ *Вы уже отмечены как присутствующий!*",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Сохраняем действие в состоянии
        await state.update_data(current_action='arrival')
        
        # Показываем выбор локации
        await message.answer(
            "📍 *Выберите локацию прибытия:*",
            reply_markup=get_location_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки прибытия: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

async def handle_departure(message: types.Message):
    """Обработка отметки убытия"""
    user_id = message.from_user.id
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Проверяем текущий статус
        current_status = await admin_panel.db.get_user_status(user_id)
        if current_status == 'absent':
            await message.answer(
                "ℹ️ *Вы уже отмечены как отсутствующий!*",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Сохраняем действие в состоянии
        await state.update_data(current_action='departure')
        
        # Показываем выбор локации
        await message.answer(
            "📍 *Выберите направление убытия:*",
            reply_markup=get_location_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки убытия: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

async def handle_location_selection(message: types.Message):
    """Обработка выбора локации"""
    user_id = message.from_user.id
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await message.answer(
            "📍 *Выберите вашу локацию:*",
            reply_markup=get_location_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Ошибка выбора локации: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

async def handle_my_status(message: types.Message):
    """Обработка просмотра своего статуса"""
    user_id = message.from_user.id
    
    try:
        # Получаем информацию о пользователе
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Получаем текущий статус
        current_status = await admin_panel.db.get_user_status(user_id)
        
        status_text = (
            f"📊 *Ваш статус:*\n\n"
            f"👤 ФИО: {user['name']}\n"
            f"📍 Локация: {user.get('location', 'не указано')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        )
        
        if current_status == 'present':
            status_text += "✅ *Статус: Присутствующий*"
        else:
            status_text += "❌ *Статус: Отсутствующий*"
        
        await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

async def handle_settings(message: types.Message):
    """Обработка настроек пользователя"""
    user_id = message.from_user.id
    
    try:
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await message.answer(
                "❌ Вы не зарегистрированы. Используйте /start для регистрации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        await message.answer(
            f"📝 *Настройки пользователя:*\n\n"
            f"👤 ФИО: {user['name']}\n"
            f"📍 Локация: {user.get('location', 'не указано')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"🔄 *Текущий статус:*\n"
            f"✅ *Присутствующий* - если вы отмечены как присутствующий\n"
            f"❌ *Отсутствующий* - если вы отмечены как отсутствующий\n\n"
            f"💡 *Чтобы изменить статус, используйте кнопки '✅ Прибыл'/'🚪 Убыл'*\n"
            f"💡 *Чтобы сменить локацию, используйте кнопку '📍 Локация'*",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения настроек: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )

async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик callback-запросов"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    try:
        # Обработка админ-панели
        if data.startswith('admin:'):
            await handle_admin_callback(callback_query, data)
            return
        
        # Обработка пользовательских callback
        if data.startswith('user:'):
            await handle_user_callback(callback_query, data, state)
            return
        
        # Обработка военной логики
        if data in ['arrived', 'departed', 'my_status', 'summary', 'settings', 'help']:
            await handle_main_menu(callback_query)
            return
        
        if data.startswith('arrived_'):
            await handle_arrival_callback(callback_query, state)
            return
        
        if data.startswith('departed_'):
            await handle_departure_callback(callback_query, state)
            return
        
        if data == 'back_to_main':
            await back_to_main(callback_query)
            return
        
        if data == 'cancel':
            await cancel_action(callback_query, state)
            return
        
        # Обработка локаций
        if data.startswith('location:'):
            await handle_location_callback(callback_query, data, state)
            return
        
        # Обработка админ-панели
        if data.startswith('admin:'):
            await handle_admin_callback(callback_query, data)
            return
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_main_menu(callback_query: types.CallbackQuery):
    """Обработчик главного меню"""
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if data == 'arrived':
        await callback_query.message.edit_text(
            "✅ *Отметка прибытия в расположение*\n\n"
            "Выберите способ отметки:",
            reply_markup=get_arrival_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == 'departed':
        await callback_query.message.edit_text(
            "🚪 *Отметка убытия из расположения*\n\n"
            "Выберите локацию убытия:",
            reply_markup=get_departure_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == 'my_status':
        status = await admin_panel.db.get_user_status(user_id)
        user = await admin_panel.db.get_user(user_id)
        
        if user:
            message = f"📊 *Ваш статус:*\n\n"
            message += f"👤 **ФИО:** {user['name']}\n"
            message += f"📍 **Статус:** {status or 'В расположении'}\n"
            message += f"🕐 **Время:** {get_current_time().strftime('%H:%M')}\n"
            message += f"📅 **Дата:** {get_current_time().strftime('%d.%m.%Y')}"
        else:
            message = "❌ Пользователь не найден"
        
        await callback_query.message.edit_text(
            message,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == 'summary':
        # Показываем сводку только для админов
        if await admin_panel.is_admin(user_id):
            data = await admin_panel.get_dashboard_data()
            message = await admin_panel.format_dashboard_message(data)
        else:
            message = "📋 *Сводка по части*\n\n"
            total_users = await admin_panel.db.get_total_users()
            present_users = await admin_panel.db.get_present_users()
            absent_users = await admin_panel.db.get_absent_users_count()
            
            message += f"👥 **Всего личного состава:** {total_users}\n"
            message += f"✅ **В расположении:** {present_users}\n"
            message += f"❌ **Вне расположения:** {absent_users}\n"
            message += f"📊 **Процент присутствия:** {(present_users/total_users*100):.1f}%" if total_users > 0 else "0%"
        
        await callback_query.message.edit_text(
            message,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == 'settings':
        await callback_query.message.edit_text(
            "⚙️ *Настройки*\n\n"
            "🔔 Уведомления: Включены\n"
            "📊 Сводки: Ежедневно в 19:00\n"
            "🔕 Тихий режим: Отключен\n\n"
            "Для изменения настроек обратитесь к командиру.",
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == 'help':
        help_text = (
            "❓ *Помощь по использованию бота*\n\n"
            "**Основные команды:**\n"
            "✅ **Прибыл** - отметиться в расположении\n"
            "🚪 **Убыл** - отметить убытие из расположения\n"
            "📊 **Мой статус** - посмотреть свой статус\n"
            "📋 **Сводка** - общая сводка по части\n\n"
            "**Правила:**\n"
            "• Прибыл = в расположении части\n"
            "• Убыл = в любую локацию вне расположения\n"
            "• По умолчанию = в расположении\n\n"
            "**Поддержка:**\n"
            "При проблемах обращайтесь к командиру"
        )
        
        await callback_query.message.edit_text(
            help_text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_arrival_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик отметки прибытия"""
    user_id = callback_query.from_user.id
    
    if callback_query.data == 'arrived_in_location':
        success, message = await admin_panel.db.mark_attendance(user_id)
        await callback_query.message.edit_text(
            message,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_query.data == 'arrived_with_note':
        await UserStates.waiting_for_note.set()
        await callback_query.message.edit_text(
            "📝 *Добавьте примечание к отметке прибытия*\n\n"
            "Например: прибыл с утренней пробежки, вернулся с дежурства и т.д.\n\n"
            "Отправьте текст примечания или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_departure_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик отметки убытия"""
    user_id = callback_query.from_user.id
    
    # Маппинг локаций
    location_map = {
        'departed_hospital': '🏥 Больничный',
        'departed_vacation': '🏖️ Отпуск',
        'departed_training': '📚 Обучение',
        'departed_business_trip': '🚗 Командировка',
        'departed_leave': '🏠 Увольнение',
        'departed_court': '⚖️ Суд',
        'departed_military_office': '🏛️ Военкомат',
        'departed_hospital_ward': '🏥 Госпиталь',
        'departed_service': '📋 Служебная',
        'departed_home': '🏠 Домой',
        'departed_medical': '🚑 Медицинская',
        'departed_documents': '📝 Документы',
        'departed_maintenance': '🔧 Техобслуживание',
        'departed_exercises': '📊 Учения',
        'departed_guard': '🛡️ Караул',
        'departed_duty': '🏃 Наряд',
        'departed_watch': '📋 Дежурство',
        'departed_alarm': '🚨 Тревога',
        'departed_urgent': '⚡ Срочная'
    }
    
    if callback_query.data in location_map:
        location = location_map[callback_query.data]
        success, message = await admin_panel.db.mark_departure(user_id, location)
        await callback_query.message.edit_text(
            message,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif callback_query.data == 'departed_custom':
        await UserStates.waiting_for_custom_location.set()
        await callback_query.message.edit_text(
            "📍 *Укажите локацию убытия*\n\n"
            "Отправьте название локации или нажмите 'Отмена':",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

async def handle_user_callback(callback_query: types.CallbackQuery, data: str, state: FSMContext):
    """Обработка пользовательских callback-запросов"""
    try:
        user_id = callback_query.from_user.id
        
        # Парсим callback data
        parts = data.split(":")
        action = parts[1] if len(parts) > 1 else ""
        
        if action == "back_to_main":
            # Возврат в главное меню
            await callback_query.message.edit_text(
                "👋 *Главное меню*\n\nВыберите действие:",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif action.startswith("location_"):
            # Обработка выбора локации
            await handle_location_callback(callback_query, action, state)
            
        elif action == "cancel":
            # Отмена действия
            await callback_query.message.edit_text(
                "❌ Действие отменено",
                reply_markup=get_main_keyboard()
            )
            
        else:
            await callback_query.answer("❌ Неизвестное действие")
            
    except Exception as e:
        logger.error(f"Ошибка обработки пользовательского callback: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_location_callback(callback_query: types.CallbackQuery, action: str, state: FSMContext):
    """Обработка выбора локации"""
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Определяем локацию
        location_map = {
            "location_office": "🏢 Офис",
            "location_production": "� Производство",
            "location_traveling": "🚗 В пути",
            "location_sick": "🏥 Больничный",
            "location_vacation": "🏖️ Отпуск",
            "location_training": "📚 Обучение",
            "location_remote": "� Удаленка"
        }
        
        if action == "location_custom":
            # Запрашиваем кастомную локацию
            await callback_query.message.edit_text(
                "✏️ *Введите вашу локацию:*\n\n"
                "Напишите название места, где вы находитесь:",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            await UserStates.waiting_for_custom_location.set()
            await callback_query.answer()
            return
        
        location = location_map.get(action, "Неизвестная локация")
        
        # Определяем действие (прибытие или убытие) из состояния
        state_data = await state.get_data()
        current_action = state_data.get('current_action', 'arrival')  # По умолчанию прибытие
        
        # Сохраняем локацию в состоянии
        await state.update_data(location=location, action=current_action)
        
        # Запрашиваем заметку
        action_text = "прибытия" if current_action == 'arrival' else "убытия"
        await callback_query.message.edit_text(
            f"📍 *Локация выбрана:* {location}\n\n"
            f"� *Добавьте заметку для отметки {action_text} (необязательно):*\n"
            f"Например: причина, детали, комментарий\n\n"
            f"Или нажмите 'Пропустить'",
            reply_markup=get_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Переходим к ожиданию заметки
        await UserStates.waiting_for_note.set()
        await callback_query.answer()
            
    except Exception as e:
        logger.error(f"Ошибка обработки локации: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_admin_callback(callback_query: types.CallbackQuery, data: str):
    """Обработка админских callback-запросов"""
    try:
        user_id = callback_query.from_user.id
        
        # Парсим callback data
        parts = data.split(":")
        if len(parts) >= 3:
            action = parts[1]
            subaction = parts[2]
        else:
            action = parts[1] if len(parts) > 1 else ""
            subaction = ""
        
        # Обрабатываем через админ-панель
        message, keyboard = await admin_panel.handle_callback(data, user_id)
        
        await callback_query.message.edit_text(
            message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка обработки админского callback: {e}")
        await callback_query.answer("❌ Произошла ошибка")

# Вспомогательные функции для клавиатур
def get_back_to_main_keyboard():
    """Клавиатура с кнопкой возврата в главное меню"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main"))
    return keyboard