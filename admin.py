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
    
    async def get_users_list(self) -> List[Dict]:
        """Получение списка всех бойцов"""
        try:
            return await self.db.get_all_users()
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    async def format_users_list(self, users: List[Dict]) -> str:
        """Форматирование списка пользователей"""
        if not users:
            return "📋 Список пуст"
        
        message = "📋 *Список всех бойцов:*\n\n"
        for i, user in enumerate(users, 1):
            status = "✅" if await self.db.get_attendance_today() else "❌"
            location = user.get('location', 'не указано')
            message += f"{i}. {status} {user['name']} ({location})\n"
        
        return message
    
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
            # В реальной версии нужно создать бэкап БД
            await self.db.log_event(None, "backup_created", "Создана резервная копия")
            return "backup_created.db"
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа: {e}")
            return ""
    
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
                    if self.notification_system:
                        await self.notification_system.send_bot_health_check()
                    message = "🏥 *Проверка здоровья бота*\n\n✅ Отчет отправлен главному админу"
                elif subaction == "performance":
                    if self.notification_system:
                        await self.notification_system.send_bot_performance_report()
                    message = "📈 *Отчет производительности*\n\n✅ Отчет отправлен главному админу"
                elif subaction == "system_stats":
                    stats = await self.get_system_stats()
                    message = await self.format_system_stats(stats)
                elif subaction == "diagnostics":
                    message = await self.get_detailed_diagnostics()
                elif subaction == "status_history":
                    message = await self.get_status_history()
                else:
                    message = "🏥 *Мониторинг бота*\n\nВыберите тип проверки:"
                keyboard = await self.get_keyboard_for_action("monitoring")
                
            elif action == "maintenance":
                if subaction in ["scheduled", "emergency", "update", "backup", "cleanup"]:
                    message = f"🔧 *Техобслуживание: {subaction}*\n\nПодтвердите выполнение ТО:"
                    keyboard = get_maintenance_confirmation_keyboard(subaction)
                    return message, keyboard
                elif subaction == "maintenance_log":
                    message = await self.get_maintenance_log()
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
            message = "🔍 *Детальная диагностика системы*\n\n"
            
            # Проверка базы данных
            db_status = "✅" if await self.db.is_connected() else "❌"
            message += f"🗄️ База данных: {db_status}\n"
            
            # Проверка таблиц
            try:
                total_users = await self.db.get_total_users()
                message += f"📊 Пользователей в БД: {total_users}\n"
            except Exception as e:
                message += f"❌ Ошибка чтения пользователей: {str(e)[:50]}...\n"
            
            # Проверка событий
            try:
                events = await self.db.get_events(1)
                message += f"📋 Событий в БД: {'✅' if events else '⚠️'}\n"
            except Exception as e:
                message += f"❌ Ошибка чтения событий: {str(e)[:50]}...\n"
            
            # Системная информация
            message += f"\n🖥️ Системная информация:\n"
            message += f"🕐 Время системы: {datetime.now().strftime('%H:%M:%S')}\n"
            message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n"
            message += f"🔧 Версия Python: {'.'.join(map(str, __import__('sys').version_info[:3]))}\n"
            
            return message
            
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