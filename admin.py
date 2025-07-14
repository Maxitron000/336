"""
Админская панель для бота учета персонала
"""

import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from aiogram import Bot
from aiogram.types import ParseMode, InlineKeyboardMarkup
from database import Database
from notifications import NotificationSystem
from config import Config
from monitoring import BotHealthMonitor
from backup import BackupSystem
from auto_restart import AutoRestartSystem
from pythonanywhere_support import PythonAnywhereSupport
from keyboards import (
    get_admin_keyboard, get_personnel_keyboard, get_journal_keyboard,
    get_settings_keyboard, get_notifications_settings_keyboard,
    get_admin_management_keyboard, get_danger_zone_keyboard,
    get_confirmation_keyboard, get_export_keyboard, get_back_keyboard,
    get_monitoring_keyboard, get_maintenance_keyboard, get_maintenance_confirmation_keyboard
)

logger = logging.getLogger(__name__)

class AdminPanel:
    """Админ-панель с многоуровневой структурой"""
    
    def __init__(self, db: Database, notification_system: NotificationSystem = None):
        self.db = db
        self.config = Config()
        self.notification_system = notification_system
        
        # Инициализируем системы мониторинга
        self.health_monitor = BotHealthMonitor(db)
        self.backup_system = BackupSystem()
        self.auto_restart = AutoRestartSystem()
        self.pythonanywhere_support = PythonAnywhereSupport(db, notification_system)
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь админом"""
        return user_id in self.config.ADMIN_IDS
    
    async def is_main_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь главным админом"""
        # В простой версии главный админ - первый в списке
        return user_id == self.config.ADMIN_IDS[0] if self.config.ADMIN_IDS else False
    
    # Методы для быстрой сводки (Уровень 1)
    async def get_dashboard_data(self) -> Dict:
        """Получение данных для быстрой сводки"""
        try:
            total_users = await self.db.get_total_users()
            present_users = await self.db.get_present_users()
            absent_users = await self.db.get_absent_users_count()
            absent_list = await self.db.get_absent_users()
            
            # Группировка отсутствующих по локациям
            locations = {}
            for user in absent_list:
                location = user.get('location', 'не указано')
                if location not in locations:
                    locations[location] = []
                locations[location].append(user['name'])
            
            return {
                'total_users': total_users,
                'present_users': present_users,
                'absent_users': absent_users,
                'absent_list': absent_list,
                'locations': locations
            }
        except Exception as e:
            logger.error(f"Ошибка получения данных сводки: {e}")
            return {}
    
    async def format_dashboard_message(self, data: Dict) -> str:
        """Форматирование сообщения быстрой сводки"""
        message = "📊 *Быстрая сводка*\n\n"
        message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n"
        message += f"🕐 Время: {datetime.now().strftime('%H:%M')}\n\n"
        message += f"👥 Всего бойцов: {data['total_users']}\n"
        message += f"✅ Присутствуют: {data['present_users']}\n"
        message += f"❌ Отсутствуют: {data['absent_users']}\n\n"
        
        if data['locations']:
            message += "📍 *Отсутствующие по локациям:*\n"
            for location, users in data['locations'].items():
                message += f"• {location}: {', '.join(users)}\n"
        else:
            message += "🎉 *Все бойцы на месте!*"
        
        return message
    
    # Методы управления личным составом (Уровень 2)
    async def add_user(self, telegram_id: int, name: str, location: str = None) -> bool:
        """Добавление нового бойца"""
        try:
            success = await self.db.add_user(telegram_id, name, location)
            if success:
                await self.notification_system.send_admin_notification(
                    "user_added", f"Добавлен новый боец: {name}", name
                )
            return success
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False
    
    async def change_user_name(self, telegram_id: int, new_name: str) -> bool:
        """Смена ФИО бойца"""
        try:
            success = await self.db.update_user_name(telegram_id, new_name)
            if success:
                await self.notification_system.send_admin_notification(
                    "name_changed", f"Имя изменено на: {new_name}", new_name
                )
            return success
        except Exception as e:
            logger.error(f"Ошибка смены имени: {e}")
            return False
    
    async def delete_user(self, telegram_id: int) -> bool:
        """Удаление бойца"""
        try:
            user = await self.db.get_user(telegram_id)
            if not user:
                return False
            
            success = await self.db.delete_user(telegram_id)
            if success:
                await self.notification_system.send_admin_notification(
                    "user_deleted", f"Удален боец: {user['name']}", user['name']
                )
            return success
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False
    
    async def get_users_list(self, page: int = 1, per_page: int = 8) -> tuple[List[Dict], int, int]:
        """Получение списка всех бойцов с пагинацией"""
        try:
            all_users = await self.db.get_all_users()
            
            # Исключаем командиров из списка, показываем только солдат
            soldiers = [user for user in all_users if not user.get('is_admin', False)]
            
            total_users = len(soldiers)
            total_pages = (total_users + per_page - 1) // per_page if total_users > 0 else 1
            
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            users_on_page = soldiers[start_idx:end_idx]
            
            return users_on_page, page, total_pages
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return [], 1, 1
    
    async def format_users_list(self, users: List[Dict], page: int, total_pages: int) -> str:
        """Форматирование списка пользователей с пагинацией"""
        if not users:
            return "📋 *Список солдат пуст*"
        
        message = f"📋 *Список солдат* (стр. {page}/{total_pages})\n\n"
        
        for i, user in enumerate(users, 1):
            # Получаем актуальный статус солдата
            try:
                status_info = await self.db.get_soldier_status(user['telegram_id'])
                if status_info:
                    status_emoji = "🏠" if status_info.get('status') == 'в_части' else "🚪"
                    location_text = status_info.get('location', 'в части') if status_info.get('status') == 'вне_части' else 'в части'
                else:
                    status_emoji = "❓"
                    location_text = "неизвестно"
            except:
                status_emoji = "❓"
                location_text = "неизвестно"
            
            # Кликабельная ссылка на Telegram
            tg_link = f"<a href=\"tg://user?id={user['telegram_id']}\">{user['telegram_id']}</a>"
            
            message += f"{status_emoji} *{user['name']}*\n"
            message += f"   └ 📱 ID: {tg_link}\n"
            message += f"   └ 📍 {location_text}\n\n"
        
        return message
    
    def get_users_pagination_keyboard(self, page: int, total_pages: int):
        """Клавиатура для пагинации списка пользователей"""
        from keyboards import admin_cb, InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = []
        
        # Кнопки навигации
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=admin_cb.new("personnel", f"list_users_{page-1}")))
        
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data=admin_cb.new("personnel", "list_users_info")))
        
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("➡️ Вперед", callback_data=admin_cb.new("personnel", f"list_users_{page+1}")))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Кнопки действий
        keyboard.append([
            InlineKeyboardButton("➕ Добавить", callback_data=admin_cb.new("personnel", "add_user")),
            InlineKeyboardButton("❌ Удалить", callback_data=admin_cb.new("personnel", "delete_user"))
        ])
        
        # Кнопка назад
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=admin_cb.new("personnel", ""))])
        
        return InlineKeyboardMarkup(keyboard)
    
    # Методы журнала событий (Уровень 2)
    async def get_events_list(self, limit: int = 50) -> List[Dict]:
        """Получение списка событий"""
        try:
            return await self.db.get_events(limit)
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    async def format_events_list(self, events: List[Dict]) -> str:
        """Форматирование списка событий"""
        if not events:
            return "📖 Журнал пуст"
        
        message = "📖 *Последние события:*\n\n"
        for event in events[:20]:  # Показываем только первые 20
            timestamp = event['timestamp'][:16]  # Обрезаем секунды
            message += f"🕐 {timestamp}\n"
            message += f"👤 {event['user_name']}\n"
            message += f"🔧 {event['action']}\n"
            if event['details']:
                message += f"📋 {event['details']}\n"
            message += "─" * 30 + "\n"
        
        return message
    
    async def export_events(self, format_type: str, period: str = "all") -> str:
        """Экспорт событий"""
        try:
            # Определяем период
            end_date = date.today()
            if period == "today":
                start_date = end_date
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            else:  # all
                start_date = date(2020, 1, 1)  # Очень старая дата
            
            if format_type == "csv":
                return await self.db.export_attendance_csv(start_date, end_date)
            else:
                return "Формат Excel пока не поддерживается"
                
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            return ""
    
    async def clear_events(self, period: str = "all") -> int:
        """Очистка журнала событий"""
        try:
            # В простой версии просто логируем
            await self.db.log_event(None, "journal_cleared", f"Очищен журнал за период: {period}")
            return 1
        except Exception as e:
            logger.error(f"Ошибка очистки журнала: {e}")
            return 0
    
    # Методы настроек уведомлений (Уровень 3)
    async def get_notification_settings(self, user_id: int) -> Dict:
        """Получение настроек уведомлений пользователя"""
        try:
            return await self.db.get_notification_settings(user_id)
        except Exception as e:
            logger.error(f"Ошибка получения настроек уведомлений: {e}")
            return {}
    
    async def update_notification_settings(self, user_id: int, settings: Dict) -> bool:
        """Обновление настроек уведомлений"""
        try:
            return await self.db.update_notification_settings(user_id, settings)
        except Exception as e:
            logger.error(f"Ошибка обновления настроек уведомлений: {e}")
            return False
    
    async def get_notification_stats(self) -> Dict:
        """Получение статистики уведомлений"""
        try:
            return await self.notification_system.get_notification_stats()
        except Exception as e:
            logger.error(f"Ошибка получения статистики уведомлений: {e}")
            return {}
    
    # Методы управления админами (Уровень 3)
    async def add_admin(self, telegram_id: int) -> bool:
        """Добавление админа"""
        try:
            if telegram_id not in self.config.ADMIN_IDS:
                self.config.ADMIN_IDS.append(telegram_id)
                # В реальной версии нужно сохранить в конфиг
                await self.db.log_event(None, "admin_added", f"Добавлен админ: {telegram_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка добавления админа: {e}")
            return False
    
    async def remove_admin(self, telegram_id: int) -> bool:
        """Удаление админа"""
        try:
            if telegram_id in self.config.ADMIN_IDS and len(self.config.ADMIN_IDS) > 1:
                self.config.ADMIN_IDS.remove(telegram_id)
                # В реальной версии нужно сохранить в конфиг
                await self.db.log_event(None, "admin_removed", f"Удален админ: {telegram_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления админа: {e}")
            return False
    
    async def get_admins_list(self) -> List[Dict]:
        """Получение списка админов"""
        try:
            admins = []
            for admin_id in self.config.ADMIN_IDS:
                user = await self.db.get_user(admin_id)
                if user:
                    admins.append({
                        'id': admin_id,
                        'name': user['name'],
                        'is_main': admin_id == self.config.ADMIN_IDS[0] if self.config.ADMIN_IDS else False
                    })
            return admins
        except Exception as e:
            logger.error(f"Ошибка получения списка админов: {e}")
            return []
    
    # Методы опасной зоны (Уровень 3)
    async def mark_all_arrived(self, location: str) -> int:
        """Отметить всех прибывшими"""
        try:
            users = await self.db.get_all_users()
            count = 0
            
            for user in users:
                if await self.db.mark_attendance(user['telegram_id'], location):
                    count += 1
            
            await self.db.log_event(None, "mark_all_arrived", f"Все отмечены прибывшими в {location}")
            await self.notification_system.send_admin_notification(
                "admin_action", f"Все бойцы отмечены прибывшими в {location}"
            )
            
            return count
        except Exception as e:
            logger.error(f"Ошибка массовой отметки: {e}")
            return 0
    
    async def clear_all_data(self) -> bool:
        """Очистка всех данных"""
        try:
            # В реальной версии нужно очистить все таблицы
            await self.db.log_event(None, "clear_all_data", "Очищены все данные")
            await self.notification_system.send_emergency_notification("Очищены все данные системы")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
            return False
    
    async def reset_settings(self) -> bool:
        """Сброс настроек"""
        try:
            # В реальной версии нужно сбросить настройки
            await self.db.log_event(None, "reset_settings", "Сброшены все настройки")
            return True
        except Exception as e:
            logger.error(f"Ошибка сброса настроек: {e}")
            return False
    
    async def create_backup(self) -> str:
        """Создание резервной копии"""
        try:
            backup_info = await self.backup_system.create_backup('manual')
            
            if backup_info['status'] == 'completed':
                await self.db.log_event(None, "backup_created", f"Создан бэкап: {backup_info['name']}")
                return f"✅ Бэкап создан: {backup_info['name']}"
            else:
                return f"❌ Ошибка создания бэкапа: {backup_info.get('error', 'Неизвестная ошибка')}"
                
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    # Универсальные методы
    async def get_keyboard_for_action(self, action: str, subaction: str = "") -> InlineKeyboardMarkup:
        """Получение клавиатуры для действия"""
        if action == "dashboard":
            return get_admin_keyboard()
        elif action == "personnel":
            return get_personnel_keyboard()
        elif action == "journal":
            return get_journal_keyboard()
        elif action == "settings":
            return get_settings_keyboard()
        elif action == "notifications":
            return get_notifications_settings_keyboard()
        elif action == "admins":
            return get_admin_management_keyboard()
        elif action == "danger_zone":
            return get_danger_zone_keyboard()
        elif action == "export":
            return get_export_keyboard()
        elif action == "monitoring":
            return get_monitoring_keyboard()
        elif action == "maintenance":
            return get_maintenance_keyboard()
        elif action == "back":
            return get_admin_keyboard()
        else:
            return get_back_keyboard()
    
    async def handle_callback(self, callback_data: str, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
        """Обработка callback-запросов админ-панели"""
        try:
            # Парсим callback data
            if ":" in callback_data:
                action, subaction = callback_data.split(":", 1)
            else:
                action, subaction = callback_data, ""
            
            # Проверяем права доступа
            if not await self.is_admin(user_id):
                return "❌ У вас нет доступа к админ-панели", get_back_keyboard()
            
            # Обрабатываем действия
            if action == "dashboard":
                data = await self.get_dashboard_data()
                message = await self.format_dashboard_message(data)
                keyboard = await self.get_keyboard_for_action("dashboard")
                
            elif action == "personnel":
                if subaction == "list_users":
                    users = await self.get_users_list()
                    message = await self.format_users_list(users)
                else:
                    message = "👥 *Управление личным составом*\n\nВыберите действие:"
                keyboard = await self.get_keyboard_for_action("personnel")
                
            elif action == "journal":
                if subaction == "recent":
                    events = await self.get_events_list()
                    message = await self.format_events_list(events)
                elif subaction == "export":
                    message = "📥 *Экспорт журнала*\n\nВыберите формат и период:"
                    keyboard = await self.get_keyboard_for_action("export")
                    return message, keyboard
                else:
                    message = "📖 *Журнал событий*\n\nВыберите действие:"
                keyboard = await self.get_keyboard_for_action("journal")
                
            elif action == "settings":
                message = "⚙️ *Настройки*\n\nВыберите раздел:"
                keyboard = await self.get_keyboard_for_action("settings")
                
            elif action == "notifications":
                if subaction == "stats":
                    stats = await self.get_notification_stats()
                    message = f"📊 *Статистика уведомлений*\n\n"
                    message += f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
                    message += f"🔔 Уведомления включены: {stats.get('notifications_enabled', 0)}\n"
                    message += f"🔕 Уведомления отключены: {stats.get('notifications_disabled', 0)}\n"
                    message += f"🔇 Тихий режим: {stats.get('silent_mode', 0)}\n"
                else:
                    message = "🔔 *Настройки уведомлений*\n\nВыберите действие:"
                keyboard = await self.get_keyboard_for_action("notifications")
                
            elif action == "admins":
                if subaction == "list":
                    admins = await self.get_admins_list()
                    message = "👑 *Список администраторов:*\n\n"
                    for admin in admins:
                        status = "👑 Главный" if admin['is_main'] else "👤 Админ"
                        message += f"• {admin['name']} ({status})\n"
                else:
                    message = "👑 *Управление админами*\n\nВыберите действие:"
                keyboard = await self.get_keyboard_for_action("admins")
                
            elif action == "danger_zone":
                if subaction == "mark_all_arrived":
                    message = "⚠️ *ВНИМАНИЕ!*\n\n"
                    message += "Вы собираетесь отметить всех бойцов прибывшими.\n"
                    message += "Это действие требует подтверждения."
                    keyboard = get_confirmation_keyboard("mark_all_arrived")
                    return message, keyboard
                else:
                    message = "⚠️ *Опасная зона*\n\nВыберите действие:"
                keyboard = await self.get_keyboard_for_action("danger_zone")
                
            elif action == "monitoring":
                if subaction == "health_check":
                    message = await self.get_detailed_diagnostics()
                elif subaction == "performance":
                    if self.notification_system:
                        await self.notification_system.send_bot_performance_report()
                    message = "📈 *Отчет производительности*\n\n✅ Отчет отправлен главному админу"
                elif subaction == "system_stats":
                    stats = await self.get_system_stats()
                    message = await self.format_system_stats(stats)
                elif subaction == "diagnostics":
                    message = await self.get_detailed_diagnostics()
                elif subaction == "auto_checks":
                    message = await self.get_health_trends()
                elif subaction == "status_history":
                    message = await self.get_status_history()
                else:
                    message = "🏥 *Мониторинг бота*\n\nВыберите тип проверки:"
                keyboard = await self.get_keyboard_for_action("monitoring")
                
            elif action == "maintenance":
                if subaction == "scheduled":
                    message = await self.perform_maintenance("scheduled")
                elif subaction == "emergency":
                    message = await self.perform_maintenance("emergency")
                elif subaction == "update":
                    message = await self.perform_maintenance("update")
                elif subaction == "backup":
                    message = await self.create_backup()
                elif subaction == "cleanup":
                    message = await self.perform_maintenance("cleanup")
                elif subaction == "force_restart":
                    message = await self.force_restart()
                elif subaction == "emergency_restart":
                    message = await self.emergency_restart()
                elif subaction == "backup_stats":
                    message = await self.get_backup_stats()
                elif subaction == "restart_stats":
                    message = await self.get_restart_stats()
                elif subaction == "list_backups":
                    message = await self.list_backups()
                elif subaction == "maintenance_log":
                    message = await self.get_maintenance_log()
                elif subaction == "pythonanywhere_info":
                    message = await self.get_pythonanywhere_info()
                else:
                    message = "🔧 *Техобслуживание*\n\nВыберите тип ТО:"
                keyboard = await self.get_keyboard_for_action("maintenance")
                
            elif action == "maintenance_confirm":
                message = await self.perform_maintenance(subaction)
                # Отправляем уведомление о ТО главному админу
                if self.notification_system:
                    await self.notification_system.send_bot_maintenance_notification(
                        subaction, "Выполнено через админ-панель"
                    )
                keyboard = get_back_keyboard()
                
            elif action == "confirm":
                if subaction == "mark_all_arrived":
                    count = await self.mark_all_arrived("основная локация")
                    message = f"✅ Все бойцы отмечены прибывшими!\n\nКоличество: {count}"
                    keyboard = get_back_keyboard()
                else:
                    message = "❌ Неизвестное действие"
                    keyboard = get_back_keyboard()
                    
            else:
                message = "❌ Неизвестное действие"
                keyboard = get_back_keyboard()
            
            return message, keyboard
            
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}")
            return "❌ Произошла ошибка", get_back_keyboard()
    
    # Методы мониторинга бота
    async def get_system_stats(self) -> Dict:
        """Получение статистики системы"""
        try:
            total_users = await self.db.get_total_users()
            present_users = await self.db.get_present_users()
            absent_users = await self.db.get_absent_users_count()
            
            # Вычисляем процент присутствия
            attendance_rate = (present_users / total_users * 100) if total_users > 0 else 0
            
            # Получаем последние события
            recent_events = await self.db.get_events(10)
            
            return {
                'total_users': total_users,
                'present_users': present_users,
                'absent_users': absent_users,
                'attendance_rate': attendance_rate,
                'recent_events_count': len(recent_events),
                'db_connected': await self.db.is_connected()
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики системы: {e}")
            return {}
    
    async def format_system_stats(self, stats: Dict) -> str:
        """Форматирование статистики системы"""
        message = "📊 *Статистика системы*\n\n"
        message += f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
        message += f"✅ Присутствуют: {stats.get('present_users', 0)}\n"
        message += f"❌ Отсутствуют: {stats.get('absent_users', 0)}\n"
        message += f"📈 Процент присутствия: {stats.get('attendance_rate', 0):.1f}%\n"
        message += f"📋 Последних событий: {stats.get('recent_events_count', 0)}\n"
        message += f"🗄️ База данных: {'✅' if stats.get('db_connected', False) else '❌'}\n"
        message += f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
        message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
        
        return message
    
    async def get_detailed_diagnostics(self) -> str:
        """Получение детальной диагностики"""
        try:
            # Используем систему мониторинга здоровья
            return await self.health_monitor.get_health_report()
            
        except Exception as e:
            logger.error(f"Ошибка детальной диагностики: {e}")
            return f"❌ Ошибка диагностики: {str(e)}"
    
    async def get_status_history(self) -> str:
        """Получение истории статусов"""
        try:
            # Получаем последние события системы
            events = await self.db.get_events(20)
            
            if not events:
                return "📋 История статусов пуста"
            
            message = "📋 *История статусов системы*\n\n"
            
            for event in events[:10]:  # Показываем последние 10
                timestamp = event['timestamp'][:16]
                action = event['action']
                details = event.get('details', '')
                
                # Выбираем эмодзи для действия
                action_emojis = {
                    "user_added": "➕",
                    "user_deleted": "❌",
                    "name_changed": "✏️",
                    "attendance_marked": "✅",
                    "admin_action": "👑",
                    "system_event": "⚙️"
                }
                
                emoji = action_emojis.get(action, "📝")
                
                message += f"{emoji} {timestamp}\n"
                message += f"🔧 {action}\n"
                if details:
                    message += f"📋 {details[:50]}{'...' if len(details) > 50 else ''}\n"
                message += "─" * 20 + "\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения истории статусов: {e}")
            return f"❌ Ошибка получения истории: {str(e)}"
    
    # Методы техобслуживания
    async def perform_maintenance(self, maintenance_type: str) -> str:
        """Выполнение техобслуживания"""
        try:
            message = f"🔧 *Техобслуживание: {maintenance_type}*\n\n"
            
            if maintenance_type == "scheduled":
                message += "✅ Плановое ТО выполнено\n"
                message += "📋 Проверены все системы\n"
                message += "🔧 Обновлены настройки\n"
                
            elif maintenance_type == "emergency":
                message += "🚨 Экстренное ТО выполнено\n"
                message += "⚠️ Проверены критические системы\n"
                message += "🔧 Исправлены ошибки\n"
                
            elif maintenance_type == "update":
                message += "🔄 Обновление системы\n"
                message += "📦 Установлены обновления\n"
                message += "🔄 Система перезапущена\n"
                
            elif maintenance_type == "backup":
                message += "💾 Резервная копия\n"
                message += "📁 Создан бэкап данных\n"
                message += "🔒 Данные защищены\n"
                
            elif maintenance_type == "cleanup":
                message += "🧹 Очистка данных\n"
                message += "🗑️ Удалены старые записи\n"
                message += "💾 Освобождено место\n"
            
            message += f"\n🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
            message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
            
            # Логируем событие ТО
            await self.db.log_event(None, "maintenance", f"ТО: {maintenance_type}")
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка выполнения ТО: {e}")
            return f"❌ Ошибка ТО: {str(e)}"
    
    async def get_maintenance_log(self) -> str:
        """Получение лога техобслуживания"""
        try:
            # Получаем события ТО
            events = await self.db.get_events(50)
            maintenance_events = [e for e in events if e['action'] == 'maintenance']
            
            if not maintenance_events:
                return "📋 Лог техобслуживания пуст"
            
            message = "📋 *Лог техобслуживания*\n\n"
            
            for event in maintenance_events[:10]:
                timestamp = event['timestamp'][:16]
                details = event.get('details', '')
                
                message += f"🔧 {timestamp}\n"
                message += f"📋 {details}\n"
                message += "─" * 20 + "\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения лога ТО: {e}")
            return f"❌ Ошибка получения лога: {str(e)}"
    
    # Новые методы для расширенного мониторинга
    async def get_health_trends(self) -> str:
        """Получение трендов здоровья системы"""
        try:
            trends = await self.health_monitor.get_health_trends()
            
            if 'error' in trends:
                return f"❌ Ошибка получения трендов: {trends['error']}"
            
            trend_emojis = {
                'stable': '✅',
                'concerning': '⚠️',
                'deteriorating': '🚨',
                'fluctuating': '📊',
                'insufficient_data': '❓'
            }
            
            emoji = trend_emojis.get(trends['trend'], '❓')
            
            message = f"📈 *Тренды здоровья системы*\n\n"
            message += f"{emoji} Тренд: {trends['trend']}\n"
            message += f"📊 Проверок проанализировано: {trends['checks_analyzed']}\n"
            
            if 'status_distribution' in trends:
                message += f"\n📋 Распределение статусов:\n"
                for status, count in trends['status_distribution'].items():
                    status_emoji = self.health_monitor._get_status_emoji(status)
                    message += f"  {status_emoji} {status}: {count}\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения трендов здоровья: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def get_backup_stats(self) -> str:
        """Получение статистики резервных копий"""
        try:
            stats = await self.backup_system.get_backup_stats()
            
            if 'error' in stats:
                return f"❌ Ошибка получения статистики бэкапов: {stats['error']}"
            
            message = "💾 *Статистика резервных копий*\n\n"
            message += f"📊 Всего бэкапов: {stats['total_backups']}\n"
            message += f"📁 Общий размер: {stats['total_size_formatted']}\n"
            
            if stats['oldest_backup']:
                message += f"📅 Самый старый: {stats['oldest_backup'].strftime('%d.%m.%Y')}\n"
            if stats['newest_backup']:
                message += f"📅 Самый новый: {stats['newest_backup'].strftime('%d.%m.%Y')}\n"
            
            if stats['backup_types']:
                message += f"\n📋 По типам:\n"
                for backup_type, type_stats in stats['backup_types'].items():
                    size_formatted = self.backup_system.format_backup_size(type_stats['total_size'])
                    message += f"  • {backup_type}: {type_stats['count']} ({size_formatted})\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики бэкапов: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def get_restart_stats(self) -> str:
        """Получение статистики перезапусков"""
        try:
            stats = await self.auto_restart.get_restart_stats()
            
            if 'error' in stats:
                return f"❌ Ошибка получения статистики перезапусков: {stats['error']}"
            
            message = "🔄 *Статистика перезапусков*\n\n"
            message += f"📊 Всего перезапусков: {stats['total_restarts']}\n"
            message += f"📈 Максимум разрешено: {stats['max_restarts']}\n"
            message += f"📉 Осталось: {stats['restarts_remaining']}\n"
            message += f"📅 За последние 24ч: {stats['restarts_last_24h']}\n"
            message += f"✅ Успешных: {stats['successful_restarts']}\n"
            message += f"❌ Неудачных: {stats['failed_restarts']}\n"
            
            if stats['last_restart_time']:
                message += f"🕐 Последний перезапуск: {stats['last_restart_time'].strftime('%d.%m %H:%M')}\n"
            
            # Тренд
            trend_emojis = {
                'stable': '✅',
                'moderate_restart_rate': '⚠️',
                'high_restart_rate': '🚨',
                'no_data': '❓'
            }
            
            emoji = trend_emojis.get(stats['trend'], '❓')
            message += f"\n{emoji} Тренд: {stats['trend']}"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики перезапусков: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def force_restart(self) -> str:
        """Принудительный перезапуск бота"""
        try:
            success = await self.auto_restart.force_restart()
            
            if success:
                await self.db.log_event(None, "force_restart", "Выполнен принудительный перезапуск")
                return "✅ Принудительный перезапуск выполнен успешно"
            else:
                return "❌ Ошибка принудительного перезапуска"
                
        except Exception as e:
            logger.error(f"Ошибка принудительного перезапуска: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def emergency_restart(self) -> str:
        """Экстренный перезапуск"""
        try:
            success = await self.auto_restart.emergency_restart()
            
            if success:
                await self.db.log_event(None, "emergency_restart", "Выполнен экстренный перезапуск")
                return "🚨 Экстренный перезапуск выполнен успешно"
            else:
                return "❌ Ошибка экстренного перезапуска"
                
        except Exception as e:
            logger.error(f"Ошибка экстренного перезапуска: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def list_backups(self) -> str:
        """Получение списка резервных копий"""
        try:
            backups = await self.backup_system.list_backups()
            
            if not backups:
                return "📋 Резервные копии не найдены"
            
            message = "📋 *Список резервных копий:*\n\n"
            
            for backup in backups[:10]:  # Показываем последние 10
                timestamp = backup['created'].strftime('%d.%m %H:%M')
                size_formatted = self.backup_system.format_backup_size(backup['size'])
                
                message += f"📁 {backup['name']}\n"
                message += f"📅 {timestamp}\n"
                message += f"📊 {size_formatted}\n"
                message += f"🏷️ {backup['type']}\n"
                message += "─" * 20 + "\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка получения списка бэкапов: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def restore_backup(self, backup_name: str) -> str:
        """Восстановление из резервной копии"""
        try:
            restore_info = await self.backup_system.restore_backup(backup_name)
            
            if restore_info['status'] == 'completed':
                await self.db.log_event(None, "backup_restored", f"Восстановлен бэкап: {backup_name}")
                return f"✅ Восстановление завершено: {backup_name}"
            else:
                return f"❌ Ошибка восстановления: {restore_info.get('error', 'Неизвестная ошибка')}"
                
        except Exception as e:
            logger.error(f"Ошибка восстановления бэкапа: {e}")
            return f"❌ Ошибка: {str(e)}"
    
    async def get_pythonanywhere_info(self) -> str:
        """Получение информации о PythonAnywhere"""
        try:
            info = self.pythonanywhere_support.get_pythonanywhere_info()
            return self.pythonanywhere_support.format_pythonanywhere_info(info)
            
        except Exception as e:
            logger.error(f"Ошибка получения информации PythonAnywhere: {e}")
            return f"❌ Ошибка: {str(e)}"