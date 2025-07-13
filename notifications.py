"""
Система уведомлений для бота учета персонала
"""

import asyncio
import logging
import random
import json
from datetime import datetime, date, time
from typing import List, Dict, Optional
from aiogram import Bot
from aiogram.types import ParseMode
from database import Database
from config import Config

logger = logging.getLogger(__name__)

class NotificationSystem:
    """Система уведомлений с расписанием и креативными текстами"""
    
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self.config = Config()
        self.notification_texts = self.config.get_notification_texts()
        
        # Настройки уведомлений
        self.enabled = True
        self.daily_summary_enabled = True
        self.reminders_enabled = True
        self.silent_mode = False
    
    async def send_notification(self, user_id: int, message: str, disable_notification: bool = False):
        """Отправка уведомления пользователю"""
        try:
            # Проверяем настройки пользователя
            settings = await self.db.get_notification_settings(user_id)
            if not settings.get('enabled', True):
                return False
            
            # Проверяем тихий режим
            if settings.get('silent_mode', False) or self.silent_mode:
                disable_notification = True
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_notification=disable_notification
            )
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
            return False
    
    async def send_daily_summary(self):
        """Отправка ежедневной сводки в 19:00"""
        if not self.daily_summary_enabled:
            return
        
        try:
            logger.info("📊 Отправка ежедневной сводки...")
            
            # Получаем статистику
            total_users = await self.db.get_total_users()
            present_users = await self.db.get_present_users()
            absent_users = await self.db.get_absent_users_count()
            
            # Получаем отсутствующих пользователей
            absent_list = await self.db.get_absent_users()
            
            # Выбираем случайный заголовок
            header = random.choice(self.notification_texts.get("daily_summary", [
                "📊 Ежедневная сводка готовности",
                "📈 Отчет по личному составу",
                "📋 Статистика на сегодня"
            ]))
            
            # Формируем сообщение
            message = f"{header}\n\n"
            message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n"
            message += f"🕐 Время: {datetime.now().strftime('%H:%M')}\n\n"
            message += f"👥 Всего бойцов: {total_users}\n"
            message += f"✅ Присутствуют: {present_users}\n"
            message += f"❌ Отсутствуют: {absent_users}\n\n"
            
            if absent_list:
                message += "📋 *Отсутствующие:*\n"
                for user in absent_list:
                    location = user.get('location', 'не указано')
                    message += f"• {user['name']} ({location})\n"
            else:
                message += "🎉 *Все бойцы на месте!*"
            
            # Отправляем админам
            admin_ids = self.config.ADMIN_IDS
            for admin_id in admin_ids:
                await self.send_notification(admin_id, message)
            
            logger.info(f"✅ Ежедневная сводка отправлена {len(admin_ids)} админам")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки ежедневной сводки: {e}")
    
    async def send_reminders(self):
        """Отправка напоминаний в 20:30"""
        if not self.reminders_enabled:
            return
        
        try:
            logger.info("🔔 Отправка напоминаний...")
            
            # Получаем отсутствующих пользователей
            absent_users = await self.db.get_absent_users()
            
            if not absent_users:
                logger.info("✅ Все бойцы уже отметились")
                return
            
            # Выбираем случайный текст напоминания
            reminder_text = random.choice(self.notification_texts.get("reminders", [
                "🔔 Эй, боец! Не забудь отметиться!",
                "⏰ Время отметиться, товарищ!",
                "📱 Ты еще не отметился сегодня!",
                "🎯 Пора показать, что ты на месте!",
                "💪 Не подведи команду - отметьсь!",
                "🚀 Команда ждет твоей отметки!",
                "⚡ Быстрая отметка - быстрая победа!",
                "🎖️ Отметись и покажи свою готовность!",
                "🔥 Горячая отметка для горячих бойцов!",
                "🌟 Звездная отметка для звездного бойца!"
            ]))
            
            # Отправляем напоминания
            sent_count = 0
            for user in absent_users:
                user_id = user.get('telegram_id')
                if user_id:
                    message = f"{reminder_text}\n\n"
                    message += f"👤 Боец: {user['name']}\n"
                    message += f"📍 Локация: {user.get('location', 'не указано')}\n"
                    message += f"🕐 Время: {datetime.now().strftime('%H:%M')}\n\n"
                    message += "💡 Используйте /start для отметки"
                    
                    if await self.send_notification(user_id, message):
                        sent_count += 1
            
            logger.info(f"✅ Напоминания отправлены {sent_count} бойцам")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний: {e}")
    
    async def send_attendance_notification(self, user_id: int, user_name: str, location: str = None):
        """Уведомление об отметке присутствия"""
        try:
            message = (
                f"✅ *Отметка зарегистрирована!*\n\n"
                f"👤 Боец: {user_name}\n"
                f"📍 Локация: {location or 'не указано'}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
            )
            
            await self.send_notification(user_id, message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об отметке: {e}")
    
    async def send_admin_notification(self, action: str, details: str, user_name: str = None):
        """Уведомление админов о действиях"""
        try:
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
            
            message = (
                f"{emoji} *Админ-уведомление*\n\n"
                f"🔧 Действие: {action}\n"
                f"📋 Детали: {details}\n"
            )
            
            if user_name:
                message += f"👤 Пользователь: {user_name}\n"
            
            message += f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
            
            # Отправляем всем админам
            admin_ids = self.config.ADMIN_IDS
            for admin_id in admin_ids:
                await self.send_notification(admin_id, message, disable_notification=True)
            
        except Exception as e:
            logger.error(f"Ошибка отправки админ-уведомления: {e}")
    
    async def send_mass_notification(self, message: str, user_ids: List[int] = None):
        """Массовая рассылка уведомлений"""
        try:
            if not user_ids:
                # Получаем всех пользователей
                users = await self.db.get_all_users()
                user_ids = [user['telegram_id'] for user in users]
            
            sent_count = 0
            for user_id in user_ids:
                if await self.send_notification(user_id, message):
                    sent_count += 1
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
            
            logger.info(f"✅ Массовое уведомление отправлено {sent_count} пользователям")
            return sent_count
            
        except Exception as e:
            logger.error(f"Ошибка массовой рассылки: {e}")
            return 0
    
    async def send_emergency_notification(self, message: str):
        """Экстренное уведомление (игнорирует настройки)"""
        try:
            admin_ids = self.config.ADMIN_IDS
            for admin_id in admin_ids:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 *ЭКСТРЕННОЕ УВЕДОМЛЕНИЕ*\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            logger.info(f"🚨 Экстренное уведомление отправлено {len(admin_ids)} админам")
            
        except Exception as e:
            logger.error(f"Ошибка экстренного уведомления: {e}")
    
    async def update_notification_texts(self, new_texts: Dict):
        """Обновление текстов уведомлений"""
        try:
            self.notification_texts.update(new_texts)
            self.config.save_notification_texts(self.notification_texts)
            logger.info("✅ Тексты уведомлений обновлены")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления текстов уведомлений: {e}")
            return False
    
    async def get_notification_stats(self) -> Dict:
        """Получение статистики уведомлений"""
        try:
            users = await self.db.get_all_users()
            total_users = len(users)
            
            enabled_count = 0
            disabled_count = 0
            silent_count = 0
            
            for user in users:
                settings = await self.db.get_notification_settings(user['telegram_id'])
                if settings.get('enabled', True):
                    enabled_count += 1
                else:
                    disabled_count += 1
                
                if settings.get('silent_mode', False):
                    silent_count += 1
            
            return {
                'total_users': total_users,
                'notifications_enabled': enabled_count,
                'notifications_disabled': disabled_count,
                'silent_mode': silent_count,
                'system_enabled': self.enabled,
                'daily_summary_enabled': self.daily_summary_enabled,
                'reminders_enabled': self.reminders_enabled
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики уведомлений: {e}")
            return {}
    
    async def toggle_notifications(self, enabled: bool):
        """Включение/выключение системы уведомлений"""
        self.enabled = enabled
        logger.info(f"🔔 Система уведомлений {'включена' if enabled else 'отключена'}")
    
    async def toggle_daily_summary(self, enabled: bool):
        """Включение/выключение ежедневной сводки"""
        self.daily_summary_enabled = enabled
        logger.info(f"📊 Ежедневная сводка {'включена' if enabled else 'отключена'}")
    
    async def toggle_reminders(self, enabled: bool):
        """Включение/выключение напоминаний"""
        self.reminders_enabled = enabled
        logger.info(f"⏰ Напоминания {'включены' if enabled else 'отключены'}")
    
    async def toggle_silent_mode(self, enabled: bool):
        """Включение/выключение тихого режима"""
        self.silent_mode = enabled
        logger.info(f"🔇 Тихий режим {'включен' if enabled else 'отключен'}")
    
    async def test_notification(self, user_id: int):
        """Тестовое уведомление"""
        try:
            message = (
                "🧪 *Тестовое уведомление*\n\n"
                "✅ Система уведомлений работает корректно!\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
            )
            
            await self.send_notification(user_id, message)
            return True
            
        except Exception as e:
            logger.error(f"Ошибка тестового уведомления: {e}")
            return False

    async def send_bot_status_notification(self, status: str, details: str = None):
        """Отправка уведомления о статусе бота главному админу"""
        try:
            # Получаем ID главного админа (первый в списке)
            admin_ids = self.config.ADMIN_IDS
            if not admin_ids:
                logger.warning("❌ Нет настроенных админов для уведомлений о статусе бота")
                return False
            
            main_admin_id = admin_ids[0]
            
            # Выбираем эмодзи для статуса
            status_emojis = {
                "started": "🚀",
                "stopped": "🛑", 
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️",
                "success": "✅",
                "restart": "🔄",
                "maintenance": "🔧"
            }
            
            emoji = status_emojis.get(status, "📝")
            
            # Формируем сообщение
            message = f"{emoji} *Статус бота: {status.upper()}*\n\n"
            message += f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
            message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n"
            
            if details:
                message += f"📋 Детали: {details}\n"
            
            # Добавляем дополнительную информацию в зависимости от статуса
            if status == "started":
                message += "\n🎯 Бот готов к работе!"
            elif status == "stopped":
                message += "\n⏸️ Бот остановлен"
            elif status == "error":
                message += "\n🚨 Требуется внимание!"
            elif status == "restart":
                message += "\n🔄 Бот перезапускается..."
            elif status == "maintenance":
                message += "\n🔧 Режим обслуживания"
            
            # Отправляем уведомление
            success = await self.send_notification(main_admin_id, message)
            
            if success:
                logger.info(f"✅ Уведомление о статусе бота ({status}) отправлено главному админу")
            else:
                logger.error(f"❌ Не удалось отправить уведомление о статусе бота главному админу")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о статусе бота: {e}")
            return False
    
    async def send_bot_health_check(self):
        """Отправка проверки здоровья бота главному админу"""
        try:
            # Получаем статистику системы
            total_users = await self.db.get_total_users()
            present_users = await self.db.get_present_users()
            
            # Проверяем подключение к базе данных
            db_status = "✅" if await self.db.is_connected() else "❌"
            
            # Проверяем доступность бота
            bot_status = "✅"
            try:
                me = await self.bot.get_me()
                bot_name = me.first_name
            except Exception:
                bot_status = "❌"
                bot_name = "Недоступен"
            
            # Формируем отчет о здоровье
            message = (
                f"🏥 *Проверка здоровья бота*\n\n"
                f"🤖 Бот: {bot_status} {bot_name}\n"
                f"🗄️ База данных: {db_status}\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"✅ Активных сегодня: {present_users}\n"
                f"🕐 Время проверки: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
            )
            
            # Определяем общий статус
            if bot_status == "✅" and db_status == "✅":
                overall_status = "✅ Система работает нормально"
            elif bot_status == "❌" or db_status == "❌":
                overall_status = "❌ Критические проблемы"
            else:
                overall_status = "⚠️ Частичные проблемы"
            
            message += f"\n\n📊 *Общий статус:* {overall_status}"
            
            # Отправляем главному админу
            admin_ids = self.config.ADMIN_IDS
            if admin_ids:
                await self.send_notification(admin_ids[0], message)
                logger.info("✅ Отчет о здоровье бота отправлен главному админу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета о здоровье бота: {e}")
    
    async def send_bot_performance_report(self):
        """Отправка отчета о производительности бота"""
        try:
            # Получаем статистику
            total_users = await self.db.get_total_users()
            present_users = await self.db.get_present_users()
            absent_users = await self.db.get_absent_users_count()
            
            # Вычисляем процент присутствия
            attendance_rate = (present_users / total_users * 100) if total_users > 0 else 0
            
            # Определяем статус производительности
            if attendance_rate >= 90:
                performance_status = "🟢 Отличная"
                performance_emoji = "🚀"
            elif attendance_rate >= 70:
                performance_status = "🟡 Хорошая"
                performance_emoji = "✅"
            elif attendance_rate >= 50:
                performance_status = "🟠 Средняя"
                performance_emoji = "⚠️"
            else:
                performance_status = "🔴 Низкая"
                performance_emoji = "❌"
            
            message = (
                f"📈 *Отчет о производительности*\n\n"
                f"{performance_emoji} Статус: {performance_status}\n"
                f"📊 Процент присутствия: {attendance_rate:.1f}%\n"
                f"👥 Всего бойцов: {total_users}\n"
                f"✅ Присутствуют: {present_users}\n"
                f"❌ Отсутствуют: {absent_users}\n"
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}"
            )
            
            # Отправляем главному админу
            admin_ids = self.config.ADMIN_IDS
            if admin_ids:
                await self.send_notification(admin_ids[0], message)
                logger.info("✅ Отчет о производительности отправлен главному админу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета о производительности: {e}")
    
    async def send_bot_error_notification(self, error: str, context: str = None):
        """Отправка уведомления об ошибке бота"""
        try:
            message = (
                f"🚨 *Ошибка бота!*\n\n"
                f"❌ Ошибка: {error}\n"
            )
            
            if context:
                message += f"🔍 Контекст: {context}\n"
            
            message += (
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n\n"
                f"⚠️ Требуется немедленное внимание!"
            )
            
            # Отправляем всем админам
            admin_ids = self.config.ADMIN_IDS
            for admin_id in admin_ids:
                await self.send_notification(admin_id, message)
            
            logger.info(f"✅ Уведомление об ошибке отправлено {len(admin_ids)} админам")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления об ошибке: {e}")
    
    async def send_bot_maintenance_notification(self, maintenance_type: str, duration: str = None):
        """Отправка уведомления о техническом обслуживании"""
        try:
            maintenance_emojis = {
                "scheduled": "🔧",
                "emergency": "🚨",
                "update": "🔄",
                "backup": "💾",
                "cleanup": "🧹"
            }
            
            emoji = maintenance_emojis.get(maintenance_type, "🔧")
            
            message = (
                f"{emoji} *Техническое обслуживание*\n\n"
                f"🔧 Тип: {maintenance_type}\n"
            )
            
            if duration:
                message += f"⏱️ Длительность: {duration}\n"
            
            message += (
                f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n"
                f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n\n"
                f"ℹ️ Бот может быть временно недоступен"
            )
            
            # Отправляем главному админу
            admin_ids = self.config.ADMIN_IDS
            if admin_ids:
                await self.send_notification(admin_ids[0], message)
                logger.info(f"✅ Уведомление о ТО ({maintenance_type}) отправлено главному админу")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о ТО: {e}")