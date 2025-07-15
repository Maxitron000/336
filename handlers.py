"""
Обработчики команд и сообщений для Telegram бота учета персонала
"""

import logging
from datetime import datetime
from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from database import Database
from admin import AdminPanel
from notifications import NotificationSystem
from keyboards import (
    get_main_keyboard, get_soldier_keyboard, get_commander_keyboard,
    get_location_keyboard, get_cancel_keyboard, get_initial_status_keyboard,
    admin_cb, user_cb
)
from utils import (
    validate_full_name, is_admin, get_locations_list, 
    generate_user_info, generate_location_summary,
    generate_log_entry, get_current_time, format_datetime
)
# Удаляем некорректный импорт - функция определена в этом же файле

logger = logging.getLogger(__name__)

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_location = State()
    waiting_for_custom_location = State()
    waiting_for_initial_status = State()
    waiting_for_admin_action = State()
    waiting_for_personnel_action = State()
    waiting_for_settings_action = State()
    waiting_for_confirmation = State()
    waiting_for_danger_confirmation = State()
    waiting_for_filter_input = State()

def register_handlers(dp: Dispatcher, admin_panel: AdminPanel, notification_system: NotificationSystem):
    """Регистрация всех обработчиков - заглушка для совместимости"""
    # В aiogram 3.x обработчики регистрируются декораторами в main.py
    # Эта функция оставлена для совместимости
    pass

async def start_command(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    # Удаляем сообщение с командой для чистоты чата
    try:
        await message.delete()
    except:
        pass
    
    # Проверяем, зарегистрирован ли пользователь
    user = await admin_panel.db.get_user(user_id)
    if user:
        # Проверяем, является ли пользователь командиром
        is_commander = await admin_panel.is_admin(user_id)
        
        if is_commander:
            # Показываем меню командира
            await message.answer(
                "🎖️ *Меню командира*\n\n"
                "Выберите действие:",
                reply_markup=get_commander_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            # Показываем меню солдата
            await message.answer(
                "🪖 *Меню солдата*\n\n"
                "Выберите действие:",
                reply_markup=get_soldier_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        # Регистрируем нового пользователя
        await message.answer(
            "👋 *Добро пожаловать!*\n\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Введите ваше ФИО в формате: *Иванов И.И.*",
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
    elif current_state == UserStates.waiting_for_danger_confirmation.state:
        await handle_danger_confirmation_input(message, state, text)
    elif current_state == UserStates.waiting_for_filter_input.state:
        await handle_filter_input(message, state, text)
    else:
        # Если не в состоянии ожидания ввода, игнорируем текстовые сообщения
        # Все действия теперь выполняются через инлайн-кнопки
        pass

async def handle_name_input(message: types.Message, state: FSMContext, name: str):
    """Обработка ввода имени при регистрации"""
    user_id = message.from_user.id
    
    try:
        # Получаем username пользователя если есть
        username = message.from_user.username
        
        # Добавляем пользователя (пока без статуса)
        success = await admin_panel.db.add_user(user_id, name, username=username)
        
        if success:
            # Сохраняем имя в состояние для дальнейшего использования
            await state.update_data(user_name=name)
            
            await message.answer(
                f"✅ *Регистрация почти завершена!*\n\n"
                f"🪖 Солдат: {name}\n"
                f"🆔 ID: {user_id}\n\n"
                f"📍 *Выберите ваш текущий статус:*\n"
                f"🏠 *В части* - если вы сейчас в расположении\n"
                f"🚪 *Вне части* - если вы сейчас вне части",
                reply_markup=get_initial_status_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
            await UserStates.waiting_for_initial_status.set()
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

async def handle_custom_location_input(message: types.Message, state: FSMContext, location: str):
    """Обработка ввода кастомной локации (при убытии или регистрации)"""
    user_id = message.from_user.id
    
    try:
        # Удаляем сообщение пользователя для чистоты чата
        try:
            await message.delete()
        except:
            pass
        
        # Валидация локации: минимум 4 символа, только кириллица
        if len(location) < 4:
            await message.answer(
                "❌ Локация слишком короткая. Минимум 4 символа.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        import re
        if not re.match(r'^[А-Яа-яёЁ\s\-]+$', location):
            await message.answer(
                "❌ Используйте только кириллицу для названия локации.",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Проверяем, это регистрация или обычное убытие
        data = await state.get_data()
        is_registration = data.get('is_registration', False)
        
        if is_registration:
            # Обработка для регистрации
            user_name = data.get('user_name')
            if not user_name:
                await message.answer("❌ Ошибка: имя пользователя не найдено")
                return
            
            # Устанавливаем статус "вне части" с кастомной локацией
            success = await admin_panel.db.set_soldier_status(user_id, "вне_части", location)
            
            if success:
                # Определяем правильную клавиатуру
                is_commander = await admin_panel.is_admin(user_id)
                keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
                
                await message.answer(
                    f"🎉 *Регистрация завершена!*\n\n"
                    f"🪖 Солдат: {user_name}\n"
                    f"🚪 Статус: Вне части\n"
                    f"📍 Локация: {location}\n"
                    f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
                    f"Добро пожаловать в систему!",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Уведомляем командиров
                await notification_system.send_admin_notification(
                    "user_registered", f"Новый солдат зарегистрирован вне части ({location})", user_name
                )
                
                await state.finish()
            else:
                await message.answer(
                    "❌ Ошибка установки статуса. Попробуйте еще раз.",
                    reply_markup=get_cancel_keyboard()
                )
        else:
            # Обработка для обычного убытия
            status = await admin_panel.db.get_soldier_status(user_id)
            if not status:
                await message.answer("❌ Вы не зарегистрированы")
                return
            
            # Отмечаем убытие с кастомной локацией
            success = await admin_panel.db.mark_soldier_departure(user_id, location)
            
            if success:
                # Определяем правильную клавиатуру
                is_commander = await admin_panel.is_admin(user_id)
                keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
                
                await message.answer(
                    f"❌ *Убытие зарегистрировано!*\n\n"
                    f"🪖 Солдат: {status['name']}\n"
                    f"🚪 Статус: Вне части\n"
                    f"📍 Локация: {location}\n"
                    f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Уведомляем командиров
                await notification_system.send_admin_notification(
                    "soldier_departed", f"Убыл в {location}", status['name']
                )
                
                await state.finish()
            else:
                await message.answer(
                    "❌ Ошибка регистрации убытия. Попробуйте еще раз.",
                    reply_markup=get_cancel_keyboard()
                )
            
    except Exception as e:
        logger.error(f"Ошибка обработки кастомной локации: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте еще раз.",
            reply_markup=get_cancel_keyboard()
        )





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
        
        # Специальная обработка для фильтров журнала
        if action == "journal_filter" and subaction in ["by_name", "by_action"]:
            # Запрашиваем ввод фильтра
            filter_type = subaction
            await callback_query.message.edit_text(
                f"🔍 **Фильтр журнала**\n\n"
                f"Введите {'ФИО пользователя' if filter_type == 'by_name' else 'тип действия'} для поиска:",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Переходим в состояние ожидания ввода
            state = dp.current_state(user=user_id)
            await state.set_state(UserStates.waiting_for_filter_input)
            await state.update_data(filter_type=filter_type)
            
            await callback_query.answer()
            return
        
        # Специальная обработка для опасных операций
        dangerous_actions = [
            "danger_zone:clear_all_data",
            "danger_zone:reset_settings", 
            "danger_zone:mark_all_arrived"
        ]
        
        if f"{action}:{subaction}" in dangerous_actions:
            from keyboards import get_danger_confirmation_keyboard
            action_names = {
                "clear_all_data": "Очистка всех данных",
                "reset_settings": "Сброс настроек",
                "mark_all_arrived": "Отметка всех прибывшими"
            }
            
            await callback_query.message.edit_text(
                f"⚠️ **ОПАСНАЯ ОПЕРАЦИЯ**\n\n"
                f"Вы собираетесь выполнить: **{action_names.get(subaction, 'Неизвестная операция')}**\n\n"
                f"Для подтверждения введите текст: **Да**\n\n"
                f"⚠️ Это действие нельзя отменить!",
                reply_markup=get_danger_confirmation_keyboard(subaction),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Переходим в состояние ожидания подтверждения
            state = dp.current_state(user=user_id)
            await state.set_state(UserStates.waiting_for_danger_confirmation)
            await state.update_data(danger_action=action_names.get(subaction, 'Неизвестная операция'))
            
            await callback_query.answer()
            return
        
        # Обработка подтверждения текстом "Да"
        if action == "confirm_text":
            state = dp.current_state(user=user_id)
            state_data = await state.get_data()
            
            if subaction == "yes" and state_data.get('text_confirmed'):
                # Выполняем подтвержденную операцию
                danger_action = state_data.get('danger_action')
                
                if "Очистка всех данных" in danger_action:
                    success = await admin_panel.clear_all_data()
                    message = "✅ Все данные очищены!" if success else "❌ Ошибка очистки данных"
                elif "Сброс настроек" in danger_action:
                    success = await admin_panel.reset_settings()
                    message = "✅ Настройки сброшены!" if success else "❌ Ошибка сброса настроек"
                elif "Отметка всех прибывшими" in danger_action:
                    count = await admin_panel.mark_all_arrived("основная локация")
                    message = f"✅ Все бойцы отмечены прибывшими!\n\nКоличество: {count}"
                else:
                    message = "❌ Неизвестная операция"
                
                from keyboards import get_admin_keyboard
                await callback_query.message.edit_text(
                    message,
                    reply_markup=get_admin_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                await state.finish()
            else:
                await callback_query.message.edit_text(
                    "❌ **Операция отменена**",
                    reply_markup=get_admin_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                await state.finish()
            
            await callback_query.answer()
            return
        
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
            is_commander = await admin_panel.is_admin(user_id)
            if is_commander:
                await callback_query.message.edit_text(
                    "🎖️ *Меню командира*\n\nВыберите действие:",
                    reply_markup=get_commander_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await callback_query.message.edit_text(
                    "🪖 *Меню солдата*\n\nВыберите действие:",
                    reply_markup=get_soldier_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            
        elif action == "arrived":
            # Отметка прибытия
            await handle_arrival_callback(callback_query)
            
        elif action == "departed":
            # Отметка убытия
            await handle_departure_callback(callback_query)
            
        elif action == "my_status":
            # Просмотр статуса
            await handle_my_status_callback(callback_query)
            
        elif action == "help":
            # Справка
            help_text = (
                "📖 *Справка по системе:*\n\n"
                "🔹 `/start` - Главное меню\n"
                "🔹 `/help` - Эта справка\n"
                "🔹 `/status` - Статус системы\n\n"
                "💡 *Для командиров:*\n"
                "🔹 `/admin` - Админ-панель\n"
                "🔹 Доступ к управлению личным составом\n\n"
                "📱 *Основные действия:*\n"
                "🔹 Нажмите '✅ Прибыл' для отметки прибытия в часть\n"
                "🔹 Нажмите '❌ Убыл' для отметки убытия из части\n"
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
            
        elif action == "initial_status_in_unit":
            # Выбор начального статуса "В части"
            await handle_initial_status_callback(callback_query, "в_части", state)
            
        elif action == "initial_status_away":
            # Выбор начального статуса "Вне части" 
            await handle_initial_status_callback(callback_query, "вне_части", state)
            
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
    """Обработка выбора локации для убытия или при регистрации"""
    try:
        user_id = callback_query.from_user.id
        
        # Проверяем состояние - это может быть регистрация или обычное убытие
        current_state = await state.get_state()
        if current_state == UserStates.waiting_for_initial_status.state:
            # Обработка выбора локации при регистрации
            await handle_initial_location_callback(callback_query, action, state)
            return
        
        # Получаем статус солдата (для обычного убытия)
        status = await admin_panel.db.get_soldier_status(user_id)
        if not status:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Определяем локацию
        location_map = {
            "location_polyclinic": "🏥 Поликлиника",
            "location_obrmp": "⚓ ОБРМП",
            "location_kaliningrad": "🌆 Калининград",
            "location_shop": "🛍️ Магазин",
            "location_canteen": "🍽️ Столовая",
            "location_hospital": "🏥 Госпиталь",
            "location_workshop": "⚙️ Рабочка",
            "location_vvk": "🩺 ВВК",
            "location_mfc": "🏛️ МФЦ",
            "location_patrol": "🚓 Патруль"
        }
        
        if action == "location_custom":
            # Запрашиваем кастомную локацию
            await callback_query.message.edit_text(
                "✏️ *Введите локацию убытия:*\n\n"
                "Напишите название места, куда направляетесь.\n"
                "Минимум 4 символа, только кириллица.\n\n"
                "Пример: Штаб, Склад, Гараж",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            await UserStates.waiting_for_custom_location.set()
            await callback_query.answer()
            return
        
        if action == "cancel":
            # Отмена выбора локации
            is_commander = await admin_panel.is_admin(user_id)
            keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
            await callback_query.message.edit_text(
                f"{'🎖️ Меню командира' if is_commander else '🪖 Меню солдата'}\n\n"
                "Выберите действие:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            await state.finish()
            return
        
        location = location_map.get(action, "Неизвестная локация")
        
        # Отмечаем убытие
        success = await admin_panel.db.mark_soldier_departure(user_id, location)
        
        if success:
            # Определяем правильную клавиатуру
            is_commander = await admin_panel.is_admin(user_id)
            keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
            
            await callback_query.message.edit_text(
                f"❌ *Убытие зарегистрировано!*\n\n"
                f"🪖 Солдат: {status['name']}\n"
                f"🚪 Статус: Вне части\n"
                f"📍 Локация: {location}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Уведомляем командиров
            await notification_system.send_admin_notification(
                "soldier_departed", f"Убыл в {location}", status['name']
            )
            
            await callback_query.answer("❌ Убытие зарегистрировано!")
            await state.finish()
        else:
            await callback_query.answer("❌ Ошибка регистрации")
            
    except Exception as e:
        logger.error(f"Ошибка выбора локации: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_arrival_callback(callback_query: types.CallbackQuery):
    """Обработка отметки прибытия в часть"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем текущий статус солдата
        status = await admin_panel.db.get_soldier_status(user_id)
        if not status:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Проверяем, не в части ли уже солдат
        if status.get('status') == 'в_части':
            # Креативное уведомление для повторного действия
            try:
                creative_messages = notification_system.notification_texts.get("already_in_unit", [
                    "🪖 Товарищ, вы уже в расположении! Может, хотите прогуляться?"
                ])
                import random
                await callback_query.answer(random.choice(creative_messages))
            except:
                await callback_query.answer("🪖 Вы уже в части!")
            return
        
        # Отмечаем прибытие
        success = await admin_panel.db.mark_soldier_arrival(user_id)
        
        if success:
            # Определяем правильную клавиатуру
            is_commander = await admin_panel.is_admin(user_id)
            keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
            
            await callback_query.message.edit_text(
                f"✅ *Прибытие зарегистрировано!*\n\n"
                f"🪖 Солдат: {status['name']}\n"
                f"🏠 Статус: В части\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Уведомляем командиров
            await notification_system.send_admin_notification(
                "soldier_arrived", f"Прибыл в часть", status['name']
            )
            
            await callback_query.answer("✅ Прибытие зарегистрировано!")
        else:
            await callback_query.answer("❌ Ошибка регистрации")
            
    except Exception as e:
        logger.error(f"Ошибка отметки прибытия: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_departure_callback(callback_query: types.CallbackQuery):
    """Обработка отметки убытия из части"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем текущий статус солдата
        status = await admin_panel.db.get_soldier_status(user_id)
        if not status:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Проверяем, не вне части ли уже солдат
        if status.get('status') == 'вне_части':
            # Креативное уведомление для повторного действия
            try:
                creative_messages = notification_system.notification_texts.get("already_away", [
                    "🚪 Солдат, вы уже вне части! Когда планируете вернуться?"
                ])
                import random
                await callback_query.answer(random.choice(creative_messages))
            except:
                await callback_query.answer("🚪 Вы уже вне части!")
            return
        
        # Показываем выбор локации
        await callback_query.message.edit_text(
            f"📍 *Выберите локацию убытия:*\n\n"
            f"🪖 Солдат: {status['name']}\n"
            f"🚪 Убытие из части\n\n"
            f"Обязательно укажите, куда направляетесь:",
            reply_markup=get_location_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Сохраняем состояние в FSM
        await UserStates.waiting_for_location.set()
        
    except Exception as e:
        logger.error(f"Ошибка отметки убытия: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_my_status_callback(callback_query: types.CallbackQuery):
    """Обработка просмотра статуса через callback"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем статус солдата
        status = await admin_panel.db.get_soldier_status(user_id)
        if not status:
            await callback_query.answer("❌ Вы не зарегистрированы")
            return
        
        # Форматируем время последней отметки
        last_change = status.get('last_status_change')
        if last_change:
            try:
                # Парсим время и форматируем
                from datetime import datetime
                if isinstance(last_change, str):
                    time_obj = datetime.fromisoformat(last_change.replace('Z', '+00:00'))
                else:
                    time_obj = last_change
                time_str = time_obj.strftime('%H:%M')
                date_str = time_obj.strftime('%d.%m.%Y')
            except:
                time_str = "неизвестно"
                date_str = "неизвестно"
        else:
            time_str = "неизвестно" 
            date_str = "неизвестно"
        
        # Определяем статус и локацию
        current_status = status.get('status', 'в_части')
        location = status.get('location', '')
        
        if current_status == 'в_части':
            status_emoji = "🏠"
            status_text_line = "В части"
            location_line = ""
        else:
            status_emoji = "🚪"
            status_text_line = "Вне части"
            location_line = f"📍 Локация: {location}\n" if location else ""
        
        status_text = (
            f"📊 *Ваш статус:*\n\n"
            f"🪖 Солдат: {status['name']}\n"
            f"{status_emoji} Статус: {status_text_line}\n"
            f"{location_line}"
            f"🕐 Время отметки: {time_str}\n"
            f"📅 Дата: {date_str}\n"
        )
        
        # Определяем правильную клавиатуру
        is_commander = await admin_panel.is_admin(user_id)
        keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
        
        await callback_query.message.edit_text(
            status_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await callback_query.answer("📊 Статус обновлен")
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_initial_status_callback(callback_query: types.CallbackQuery, status: str, state: FSMContext):
    """Обработка выбора начального статуса при регистрации"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        user_name = data.get('user_name')
        
        if not user_name:
            await callback_query.answer("❌ Ошибка: имя пользователя не найдено")
            return
        
        if status == "вне_части":
            # Если выбрал "Вне части", показываем выбор локации
            await callback_query.message.edit_text(
                f"📍 *Выберите локацию:*\n\n"
                f"🪖 Солдат: {user_name}\n"
                f"🚪 Начальный статус: Вне части\n\n"
                f"Укажите, где вы сейчас находитесь:",
                reply_markup=get_location_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            # Остаемся в состоянии waiting_for_initial_status
            return
        else:
            # Если выбрал "В части", устанавливаем статус без локации
            success = await admin_panel.db.set_soldier_status(user_id, status, None)
            
            if success:
                # Определяем правильную клавиатуру
                is_commander = await admin_panel.is_admin(user_id)
                keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
                
                await callback_query.message.edit_text(
                    f"🎉 *Регистрация завершена!*\n\n"
                    f"🪖 Солдат: {user_name}\n"
                    f"🏠 Статус: В части\n"
                    f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
                    f"Добро пожаловать в систему!",
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Уведомляем командиров
                await notification_system.send_admin_notification(
                    "user_registered", f"Новый солдат зарегистрирован в части", user_name
                )
                
                await callback_query.answer("✅ Регистрация завершена!")
                await state.finish()
            else:
                await callback_query.answer("❌ Ошибка установки статуса")
                
    except Exception as e:
        logger.error(f"Ошибка установки начального статуса: {e}")
        await callback_query.answer("❌ Произошла ошибка")

async def handle_initial_location_callback(callback_query: types.CallbackQuery, action: str, state: FSMContext):
    """Обработка выбора локации при начальной регистрации"""
    user_id = callback_query.from_user.id
    
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        user_name = data.get('user_name')
        
        if not user_name:
            await callback_query.answer("❌ Ошибка: имя пользователя не найдено")
            return
        
        # Определяем локацию
        location_map = {
            "location_polyclinic": "🏥 Поликлиника",
            "location_obrmp": "⚓ ОБРМП",
            "location_kaliningrad": "🌆 Калининград",
            "location_shop": "🛍️ Магазин",
            "location_canteen": "🍽️ Столовая",
            "location_hospital": "🏥 Госпиталь",
            "location_workshop": "⚙️ Рабочка",
            "location_vvk": "🩺 ВВК",
            "location_mfc": "🏛️ МФЦ",
            "location_patrol": "🚓 Патруль"
        }
        
        if action == "location_custom":
            # Запрашиваем кастомную локацию
            await callback_query.message.edit_text(
                "✏️ *Введите локацию:*\n\n"
                f"🪖 Солдат: {user_name}\n"
                f"🚪 Начальный статус: Вне части\n\n"
                "Напишите название места, где вы сейчас находитесь.\n"
                "Минимум 4 символа, только кириллица.\n\n"
                "Пример: Штаб, Склад, Гараж",
                reply_markup=get_cancel_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            await UserStates.waiting_for_custom_location.set()
            # Сохраняем флаг что это для регистрации
            await state.update_data(is_registration=True)
            return
        
        if action == "cancel":
            # Отмена - возвращаемся к выбору статуса
            await callback_query.message.edit_text(
                f"📍 *Выберите ваш текущий статус:*\n\n"
                f"🪖 Солдат: {user_name}\n\n"
                f"🏠 *В части* - если вы сейчас в расположении\n"
                f"🚪 *Вне части* - если вы сейчас вне части",
                reply_markup=get_initial_status_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        location = location_map.get(action, "Неизвестная локация")
        
        # Устанавливаем статус "вне части" с выбранной локацией
        success = await admin_panel.db.set_soldier_status(user_id, "вне_части", location)
        
        if success:
            # Определяем правильную клавиатуру
            is_commander = await admin_panel.is_admin(user_id)
            keyboard = get_commander_keyboard() if is_commander else get_soldier_keyboard()
            
            await callback_query.message.edit_text(
                f"🎉 *Регистрация завершена!*\n\n"
                f"🪖 Солдат: {user_name}\n"
                f"🚪 Статус: Вне части\n"
                f"📍 Локация: {location}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M')}\n"
                f"📅 Дата: {datetime.now().strftime('%d.%m.%Y')}\n\n"
                f"Добро пожаловать в систему!",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Уведомляем командиров
            await notification_system.send_admin_notification(
                "user_registered", f"Новый солдат зарегистрирован вне части ({location})", user_name
            )
            
            await callback_query.answer("✅ Регистрация завершена!")
            await state.finish()
        else:
            await callback_query.answer("❌ Ошибка установки статуса")
    
    except Exception as e:
        logger.error(f"Ошибка выбора локации при регистрации: {e}")
        await callback_query.answer("❌ Произошла ошибка")
        await state.finish()

async def handle_danger_confirmation_input(message: types.Message, state: FSMContext, text: str):
    """Обработка ввода подтверждения для опасных операций"""
    user_id = message.from_user.id
    
    try:
        # Удаляем сообщение пользователя для чистоты чата
        await message.delete()
    except:
        pass
    
    # Получаем данные о подтверждаемом действии
    state_data = await state.get_data()
    action = state_data.get('danger_action')
    
    if text.strip().lower() == 'да':
        from keyboards import get_text_confirmation_keyboard
        
        await message.answer(
            f"⚠️ **ВНИМАНИЕ!**\n\n"
            f"Вы уверены, что хотите выполнить операцию:\n"
            f"**{action}**\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=get_text_confirmation_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Сохраняем подтверждение в состояние
        await state.update_data(text_confirmed=True)
    else:
        await message.answer(
            f"❌ **Операция отменена**\n\n"
            f"Для подтверждения опасной операции необходимо ввести текст: **Да**\n"
            f"Вы ввели: `{text}`",
            parse_mode=ParseMode.MARKDOWN
        )
        await state.finish()

async def handle_filter_input(message: types.Message, state: FSMContext, text: str):
    """Обработка ввода фильтра для журнала"""
    user_id = message.from_user.id
    
    try:
        # Удаляем сообщение пользователя для чистоты чата
        await message.delete()
    except:
        pass
    
    # Получаем данные о фильтре
    state_data = await state.get_data()
    filter_type = state_data.get('filter_type')
    
    if filter_type == 'by_name':
        # Фильтр по ФИО
        filters = {'user_name': text}
        events = await admin_panel.db.get_events(limit=50, filters=filters)
        
        if events:
            message_text = f"📋 **Журнал событий (фильтр по ФИО: {text})**\n\n"
            for event in events[:20]:  # Показываем только первые 20
                timestamp = event['timestamp']
                user_name = event['user_name']
                action = event['action']
                details = event.get('details', '')
                
                message_text += f"🕐 {timestamp}\n"
                message_text += f"👤 {user_name}\n"
                message_text += f"📝 {action}"
                if details:
                    message_text += f" - {details}"
                message_text += "\n\n"
            
            if len(events) > 20:
                message_text += f"... и еще {len(events) - 20} записей"
        else:
            message_text = f"📋 Записей по фильтру ФИО `{text}` не найдено"
        
        from keyboards import get_journal_filters_keyboard
        await message.answer(
            message_text,
            reply_markup=get_journal_filters_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif filter_type == 'by_action':
        # Фильтр по действию
        filters = {'action': text}
        events = await admin_panel.db.get_events(limit=50, filters=filters)
        
        if events:
            message_text = f"📋 **Журнал событий (фильтр по действию: {text})**\n\n"
            for event in events[:20]:  # Показываем только первые 20
                timestamp = event['timestamp']
                user_name = event['user_name']
                action = event['action']
                details = event.get('details', '')
                
                message_text += f"🕐 {timestamp}\n"
                message_text += f"👤 {user_name}\n"
                message_text += f"📝 {action}"
                if details:
                    message_text += f" - {details}"
                message_text += "\n\n"
            
            if len(events) > 20:
                message_text += f"... и еще {len(events) - 20} записей"
        else:
            message_text = f"📋 Записей по фильтру действие `{text}` не найдено"
        
        from keyboards import get_journal_filters_keyboard
        await message.answer(
            message_text,
            reply_markup=get_journal_filters_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
        await state.finish()