"""
Обработчики команд и сообщений для Telegram бота учета персонала
"""

import logging
from datetime import datetime
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from database import Database
from admin import AdminPanel
from notifications import NotificationSystem
from keyboards import (
    get_main_keyboard, get_location_keyboard, get_cancel_keyboard,
    admin_cb, user_cb
)
from utils import (
    validate_full_name, is_admin, get_locations_list, 
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
    
    # Обработчики текстовых сообщений (только для регистрации и кастомных локаций)
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
                "Для начала работы необходимо зарегистрироваться.\n"
                "Введите ваше ФИО:",
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
        "🔹 Нажмите '✅ Отметиться' для отметки присутствия\n"
        "🔹 Нажмите '📍 Указать локацию' для смены местоположения\n"
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
    """Обработчик текстовых сообщений (только для регистрации и кастомных локаций)"""
    user_id = message.from_user.id
    text = message.text
    
    # Проверяем текущее состояние
    current_state = await state.get_state()
    
    if current_state == UserStates.waiting_for_name.state:
        await handle_name_input(message, state, text)
    elif current_state == UserStates.waiting_for_custom_location.state:
        await handle_custom_location_input(message, state, text)
    else:
        # Если не в состоянии ожидания ввода, игнорируем текстовые сообщения
        # Все действия теперь выполняются через инлайн-кнопки
        pass

async def handle_name_input(message: types.Message, state: FSMContext, name: str):
    """Обработка ввода имени при регистрации"""
    user_id = message.from_user.id
    
    try:
        # Добавляем пользователя
        success = await admin_panel.db.add_user(user_id, name)
        
        if success:
            await message.answer(
                f"✅ *Регистрация завершена!*\n\n"
                f"👤 ФИО: {name}\n"
                f"🆔 ID: {user_id}\n\n"
                f"Теперь вы можете использовать все функции бота.",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Уведомляем админов
            await notification_system.send_admin_notification(
                "user_added", f"Новый пользователь зарегистрирован: {name}", name
            )
        else:
            await message.answer(
                "❌ Ошибка регистрации. Попробуйте еще раз.",
                reply_markup=get_cancel_keyboard()
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

async def handle_custom_location_input(message: types.Message, state: FSMContext, location: str):
    """Обработка ввода кастомной локации"""
    user_id = message.from_user.id
    
    try:
        # Отмечаем присутствие с кастомной локацией
        success = await admin_panel.db.mark_attendance(user_id, location)
        
        if success:
            user = await admin_panel.db.get_user(user_id)
            await message.answer(
                f"✅ *Отметка зарегистрирована!*\n\n"
                f"👤 Боец: {user['name']}\n"
                f"📍 Локация: {location}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Отправляем уведомление
            await notification_system.send_attendance_notification(user_id, user['name'], location)
            
            # Уведомляем админов
            await notification_system.send_admin_notification(
                "attendance_marked", f"Отметка: {location}", user['name']
            )
        else:
            await message.answer(
                "❌ Ошибка отметки. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка отметки с кастомной локацией: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_main_keyboard()
        )
    
    await state.finish()





async def handle_callback_query(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик callback-запросов"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Обрабатываем админские callback
        if data.startswith("admin:"):
            await handle_admin_callback(callback_query, data)
        # Обрабатываем пользовательские callback
        elif data.startswith("user:"):
            await handle_user_callback(callback_query, data, state)
        else:
            await callback_query.answer("❌ Неизвестный callback")
            
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}")
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
            
        elif action == "mark_attendance":
            # Отметка присутствия
            await handle_attendance_callback(callback_query)
            
        elif action == "set_location":
            # Указание локации
            await callback_query.message.edit_text(
                "📍 *Выберите вашу локацию:*",
                reply_markup=get_location_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        elif action == "my_status":
            # Просмотр статуса
            await handle_my_status_callback(callback_query)
            
        elif action == "help":
            # Справка
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
                "🔹 Нажмите '✅ Отметиться' для отметки присутствия\n"
                "🔹 Нажмите '📍 Указать локацию' для смены местоположения\n"
                "🔹 Нажмите '📊 Мой статус' для просмотра вашего статуса"
            )
            await callback_query.message.edit_text(
                help_text,
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
            "location_home": "🏠 Дом",
            "location_hospital": "🏥 Больница",
            "location_traveling": "🚗 В пути",
            "location_vacation": "🏖️ Отпуск",
            "location_sick": "🏥 Больничный"
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
        
        # Отмечаем присутствие
        success = await admin_panel.db.mark_attendance(user_id, location)
        
        if success:
            await callback_query.message.edit_text(
                f"✅ *Отметка зарегистрирована!*\n\n"
                f"👤 Боец: {user['name']}\n"
                f"📍 Локация: {location}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Отправляем уведомление
            await notification_system.send_attendance_notification(user_id, user['name'], location)
            
            # Уведомляем админов
            await notification_system.send_admin_notification(
                "attendance_marked", f"Отметка: {location}", user['name']
            )
            
            await callback_query.answer("✅ Отметка зарегистрирована!")
        else:
            await callback_query.answer("❌ Ошибка отметки")
            
    except Exception as e:
        logger.error(f"Ошибка обработки локации: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_attendance_callback(callback_query: types.CallbackQuery):
    """Обработка отметки присутствия через callback"""
    user_id = callback_query.from_user.id
    
    try:
        # Проверяем, зарегистрирован ли пользователь
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Проверяем, не отметился ли уже сегодня
        attendance_today = await admin_panel.db.get_attendance_today()
        user_attended = any(a['name'] == user['name'] for a in attendance_today)
        
        if user_attended:
            await callback_query.answer("ℹ️ Вы уже отметились сегодня!")
            return
        
        # Отмечаем присутствие
        success = await admin_panel.db.mark_attendance(user_id, user.get('location'))
        
        if success:
            await callback_query.message.edit_text(
                f"✅ *Отметка зарегистрирована!*\n\n"
                f"👤 Боец: {user['name']}\n"
                f"📍 Локация: {user.get('location', 'не указано')}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                reply_markup=get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Отправляем уведомление
            await notification_system.send_attendance_notification(
                user_id, user['name'], user.get('location')
            )
            
            # Уведомляем админов
            await notification_system.send_admin_notification(
                "attendance_marked", f"Отметка: {user.get('location', 'не указано')}", user['name']
            )
            
            await callback_query.answer("✅ Отметка зарегистрирована!")
        else:
            await callback_query.answer("❌ Ошибка отметки")
            
    except Exception as e:
        logger.error(f"Ошибка отметки присутствия: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_my_status_callback(callback_query: types.CallbackQuery):
    """Обработка просмотра статуса через callback"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем информацию о пользователе
        user = await admin_panel.db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Проверяем отметку за сегодня
        attendance_today = await admin_panel.db.get_attendance_today()
        user_attended = any(a['name'] == user['name'] for a in attendance_today)
        
        status_text = (
            f"📊 *Ваш статус:*\n\n"
            f"👤 ФИО: {user['name']}\n"
            f"📍 Локация: {user.get('location', 'не указано')}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        )
        
        if user_attended:
            status_text += "✅ *Статус: Отмечен сегодня*"
        else:
            status_text += "❌ *Статус: Не отмечен сегодня*"
        
        await callback_query.message.edit_text(
            status_text,
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        await callback_query.answer("📊 Статус обновлен")
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await callback_query.answer("❌ Произошла ошибка")