"""
Система уведомлений v2.0 для бота учета персонала
Соответствует чек-листу v2.0 с красивым форматом и гибкими настройками
"""

import logging
import asyncio
import random
import json
import os
from datetime import datetime, time, timedelta
from typing import List, Optional, Dict, Any
from telegram import Bot
from telegram.ext import Application

from database import get_all_users, get_users_without_location, add_admin_log
from utils import (
    is_notifications_enabled, get_notification_times, get_notification_interval,
    get_bro_phrases, get_current_time, is_admin
)

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения задач
notification_tasks = []

class NotificationManager:
    """Менеджер уведомлений v2.0"""
    
    def __init__(self):
        self.notification_config = self.load_notification_config()
        self.bro_phrases = self.load_bro_phrases()
        
    def load_notification_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации уведомлений"""
        config_path = "config/notifications.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации уведомлений: {e}")
            return self.get_default_config()
    
    def load_bro_phrases(self) -> List[str]:
        """Загрузка братских фраз из конфигурации"""
        try:
            return self.notification_config.get("bro_phrases", [])
        except Exception as e:
            logger.error(f"Ошибка загрузки братских фраз: {e}")
            return self.get_default_bro_phrases()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Получение конфигурации по умолчанию"""
        return {
            "bro_phrases": self.get_default_bro_phrases(),
            "admin_notify_arrival": "<b>🟢 Боец прибыл!</b>\nФИО: <b>{fio}</b>\nID: <a href=\"tg://user?id={tg_id}\">{tg_id}</a>\nВремя: {dt}",
            "admin_notify_departure": "<b>🔴 Боец убыл!</b>\nФИО: <b>{fio}</b>\nID: <a href=\"tg://user?id={tg_id}\">{tg_id}</a>\nВремя: {dt}\nЛокация: {location}",
            "admin_summary": "🗂️ <b>Краткая сводка по личному составу</b>\n{summary}"
        }
    
    def get_default_bro_phrases(self) -> List[str]:
        """Получение братских фраз по умолчанию"""
        return [
            "Братан, ты где завис? В табеле дыра напротив твоей фамилии. Жми кнопку.",
            "Эй, чемпион, тебя не видно. Дай знать, что ты на базе.",
            "Друг, не заставляй командира напрягаться. Секундное дело — отметиться.",
            "Ты снова в режиме «призрака»? Выходи на связь, ждем твою отметку.",
            "Все уже отметились, тебя одного ждем. Не будь тем самым парнем."
        ]

notification_manager = NotificationManager()

async def start_notification_scheduler_v2(app: Application):
    """Запуск планировщика уведомлений v2.0"""
    if not is_notifications_enabled():
        logger.info("🔕 Уведомления отключены")
        return
    
    logger.info("🔔 Запуск системы уведомлений v2.0")
    
    # Запускаем различные типы уведомлений
    asyncio.create_task(schedule_daily_summary_19_00(app))
    asyncio.create_task(schedule_reminders_20_30(app))
    asyncio.create_task(schedule_periodic_reminders_v2(app))

async def schedule_daily_summary_19_00(app: Application):
    """Планировщик ежедневной сводки для командиров в 19:00"""
    while True:
        try:
            now = get_current_time()
            target_time = datetime.combine(now.date(), time(19, 0))  # 19:00
            
            # Если время уже прошло, планируем на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до целевого времени
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Отправляем ежедневную сводку
            await send_daily_summary_v2(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике ежедневной сводки: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def schedule_reminders_20_30(app: Application):
    """Планировщик напоминаний для неотметившихся бойцов в 20:30"""
    while True:
        try:
            now = get_current_time()
            target_time = datetime.combine(now.date(), time(20, 30))  # 20:30
            
            # Если время уже прошло, планируем на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до целевого времени
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Отправляем напоминания
            await send_creative_reminders_v2(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике напоминаний 20:30: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def schedule_periodic_reminders_v2(app: Application):
    """Планировщик периодических напоминаний v2.0"""
    interval_hours = get_notification_interval()
    
    while True:
        try:
            # Ждем указанный интервал
            await asyncio.sleep(interval_hours * 3600)
            
            # Отправляем периодические напоминания
            await send_periodic_reminders_v2(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике периодических напоминаний v2: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def send_daily_summary_v2(bot: Bot):
    """Отправка ежедневной сводки для командиров в 19:00"""
    try:
        active_locations = get_active_users_by_location()
        users_without_location = get_users_without_location()
        all_users = get_all_users()
        
        summary_text = "🗂️ <b>Ежедневная сводка по личному составу</b>\n\n"
        summary_text += f"📅 Дата: {get_current_time().strftime('%d.%m.%Y')}\n"
        summary_text += f"🕒 Время: {get_current_time().strftime('%H:%M')}\n\n"
        
        # Общая статистика
        summary_text += f"👥 <b>Общая численность:</b> {len(all_users)} чел.\n"
        summary_text += f"✅ <b>Отметились:</b> {len(all_users) - len(users_without_location)} чел.\n"
        summary_text += f"❌ <b>Не отметились:</b> {len(users_without_location)} чел.\n\n"
        
        # Группировка по локациям
        if active_locations:
            summary_text += "📍 <b>Распределение по локациям:</b>\n"
            for location, users in active_locations.items():
                emoji = get_location_emoji(location)
                summary_text += f"{emoji} <b>{location}</b>: {len(users)} чел.\n"
                for user in users:
                    summary_text += f"  • {user['full_name']}\n"
                summary_text += "\n"
        
        # Список отсутствующих
        if users_without_location:
            summary_text += "❌ <b>Не отметились:</b>\n"
            for user in users_without_location:
                summary_text += f"• {user['full_name']}\n"
        
        # Отправляем сводку всем админам
        admin_users = [user for user in all_users if user.get('is_admin')]
        for admin in admin_users:
            try:
                await bot.send_message(
                    chat_id=admin['telegram_id'],
                    text=summary_text,
                    parse_mode='HTML'
                )
                await asyncio.sleep(0.5)  # Небольшая задержка
            except Exception as e:
                logger.error(f"Ошибка отправки сводки админу {admin['telegram_id']}: {e}")
        
        logger.info(f"Отправлена ежедневная сводка {len(admin_users)} админам")
        
    except Exception as e:
        logger.error(f"Ошибка в отправке ежедневной сводки: {e}")

async def send_creative_reminders_v2(bot: Bot):
    """Отправка креативных напоминаний для неотметившихся бойцов в 20:30"""
    try:
        users_without_location = get_users_without_location()
        
        if not users_without_location:
            logger.info("Напоминания 20:30: все пользователи указали местоположение")
            return
        
        logger.info(f"Отправка креативных напоминаний {len(users_without_location)} пользователям")
        
        for user in users_without_location:
            try:
                # Выбираем случайную братскую фразу
                phrase = random.choice(notification_manager.bro_phrases)
                
                message = f"🎮 <b>Внимание, {user['full_name']}!</b>\n\n"
                message += f"💬 {phrase}\n\n"
                message += f"📍 <b>Действие:</b> Отметить местоположение\n"
                message += f"⏰ <b>Время:</b> {get_current_time().strftime('%H:%M')}\n\n"
                message += f"🚀 <b>Нажми кнопку «📍 Отметить местоположение»</b>"
                
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки креативного напоминания пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке креативных напоминаний: {e}")

async def send_periodic_reminders_v2(bot: Bot):
    """Отправка периодических напоминаний v2.0"""
    try:
        users_without_location = get_users_without_location()
        
        if not users_without_location:
            logger.info("Периодические напоминания v2: все пользователи указали местоположение")
            return
        
        logger.info(f"Отправка периодических напоминаний v2 {len(users_without_location)} пользователям")
        
        for user in users_without_location:
            try:
                # Выбираем случайную братскую фразу
                phrase = random.choice(notification_manager.bro_phrases)
                
                message = f"📢 <b>Напоминание для {user['full_name']}</b>\n\n"
                message += f"💭 {phrase}\n\n"
                message += f"📍 <b>Действие:</b> Отметить местоположение\n"
                message += f"⏰ <b>Время:</b> {get_current_time().strftime('%H:%M')}"
                
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки периодического напоминания v2 пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке периодических напоминаний v2: {e}")

async def send_admin_notification_v2(bot: Bot, message: str, admin_id: Optional[int] = None):
    """Отправка уведомления администратору v2.0 с красивым форматом"""
    try:
        all_users = get_all_users()
        admin_users = [user for user in all_users if user.get('is_admin')]
        
        if admin_id:
            # Отправляем конкретному админу
            target_admins = [admin for admin in admin_users if admin['telegram_id'] == admin_id]
        else:
            # Отправляем всем админам
            target_admins = admin_users
        
        for admin in target_admins:
            try:
                formatted_message = f"🔔 <b>Админское уведомление</b>\n\n{message}\n\n"
                formatted_message += f"👤 <b>Получатель:</b> {admin['full_name']}\n"
                formatted_message += f"⏰ <b>Время:</b> {get_current_time().strftime('%H:%M:%S')}"
                
                await bot.send_message(
                    chat_id=admin['telegram_id'],
                    text=formatted_message,
                    parse_mode='HTML'
                )
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки админского уведомления {admin['telegram_id']}: {e}")
        
        logger.info(f"Отправлено админское уведомление {len(target_admins)} админам")
        
    except Exception as e:
        logger.error(f"Ошибка в отправке админского уведомления v2: {e}")

async def notify_about_user_action_v2(bot: Bot, user_data: dict, action: str, location: str):
    """Уведомление о действии пользователя v2.0 с красивым форматом"""
    try:
        current_time = get_current_time()
        time_str = current_time.strftime("%H:%M:%S")
        
        if action == "arrived":
            message = f"🟢 <b>Боец прибыл!</b>\n\n"
            message += f"👤 <b>Боец:</b> {user_data['full_name']}\n"
            message += f"📍 <b>Действие:</b> Прибыл в {location}\n"
            message += f"⏰ <b>Время:</b> {time_str}"
        elif action == "left":
            message = f"🔴 <b>Боец убыл!</b>\n\n"
            message += f"👤 <b>Боец:</b> {user_data['full_name']}\n"
            message += f"📍 <b>Действие:</b> Покинул {location}\n"
            message += f"⏰ <b>Время:</b> {time_str}"
        else:
            message = f"ℹ️ <b>Действие бойца</b>\n\n"
            message += f"👤 <b>Боец:</b> {user_data['full_name']}\n"
            message += f"📍 <b>Действие:</b> {action}\n"
            message += f"⏰ <b>Время:</b> {time_str}"
        
        await send_admin_notification_v2(bot, message)
        
    except Exception as e:
        logger.error(f"Ошибка в уведомлении о действии пользователя v2: {e}")

# Вспомогательные функции
def get_location_emoji(location: str) -> str:
    """Получить эмодзи для локации"""
    emoji_map = {
        "🏥 Поликлиника": "🏥",
        "⚓ ОБРМП": "⚓", 
        "🌆 Калининград": "🌆",
        "🛒 Магазин": "🛒",
        "🍲 Столовая": "🍲",
        "🏨 Госпиталь": "🏨",
        "⚙️ Рабочка": "⚙️",
        "🩺 ВВК": "🩺",
        "🏛️ МФЦ": "🏛️",
        "🚓 Патруль": "🚓"
    }
    return emoji_map.get(location, "📍")

# Функции для обратной совместимости
async def start_notification_scheduler(app: Application):
    """Запуск планировщика уведомлений (обратная совместимость)"""
    await start_notification_scheduler_v2(app)

async def send_admin_notification(bot: Bot, message: str, admin_id: Optional[int] = None):
    """Отправка уведомления администратору (обратная совместимость)"""
    await send_admin_notification_v2(bot, message, admin_id)

async def notify_about_user_action(bot: Bot, user_data: dict, action: str, location: str):
    """Уведомление о действии пользователя (обратная совместимость)"""
    await notify_about_user_action_v2(bot, user_data, action, location)