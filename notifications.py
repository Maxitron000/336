"""
Система уведомлений для бота учета персонала
"""

import logging
import asyncio
import random
from datetime import datetime, time, timedelta
from typing import List, Optional
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

async def start_notification_scheduler(app: Application):
    """Запуск планировщика уведомлений"""
    if not is_notifications_enabled():
        logger.info("Уведомления отключены")
        return
    
    logger.info("Запуск системы уведомлений")
    
    # Запускаем различные типы уведомлений
    asyncio.create_task(schedule_morning_notifications(app))
    asyncio.create_task(schedule_evening_notifications(app))
    asyncio.create_task(schedule_periodic_reminders(app))

async def schedule_morning_notifications(app: Application):
    """Планировщик утренних уведомлений"""
    morning_time, _ = get_notification_times()
    
    while True:
        try:
            now = get_current_time()
            target_time = datetime.combine(now.date(), time.fromisoformat(morning_time))
            # Добавляем часовой пояс к target_time
            target_time = now.tzinfo.localize(target_time)
            
            # Если время уже прошло, планируем на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до целевого времени
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Отправляем утренние уведомления
            await send_morning_notifications(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике утренних уведомлений: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def schedule_evening_notifications(app: Application):
    """Планировщик вечерних уведомлений"""
    _, evening_time = get_notification_times()
    
    while True:
        try:
            now = get_current_time()
            target_time = datetime.combine(now.date(), time.fromisoformat(evening_time))
            # Добавляем часовой пояс к target_time
            target_time = now.tzinfo.localize(target_time)
            
            # Если время уже прошло, планируем на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до целевого времени
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Отправляем вечерние уведомления
            await send_evening_notifications(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике вечерних уведомлений: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def schedule_periodic_reminders(app: Application):
    """Планировщик периодических напоминаний"""
    interval_hours = get_notification_interval()
    
    while True:
        try:
            # Ждем указанный интервал
            await asyncio.sleep(interval_hours * 3600)
            
            # Отправляем напоминания
            await send_periodic_reminders(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике периодических напоминаний: {e}")
            await asyncio.sleep(3600)  # Повторить через час

async def send_morning_notifications(bot: Bot):
    """Отправка утренних уведомлений"""
    try:
        users_without_location = get_users_without_location()
        
        if not users_without_location:
            logger.info("Утренние уведомления: все пользователи указали местоположение")
            return
        
        logger.info(f"Отправка утренних уведомлений {len(users_without_location)} пользователям")
        
        for user in users_without_location:
            try:
                message = f"🌅 <b>Доброе утро, {user['full_name']}!</b>\n\n"
                message += f"📍 Не забудьте отметить свое местоположение на сегодня.\n\n"
                message += f"� Хорошего дня!"
                
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки утреннего уведомления пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке утренних уведомлений: {e}")

async def send_evening_notifications(bot: Bot):
    """Отправка вечерних уведомлений"""
    try:
        users_without_location = get_users_without_location()
        
        if not users_without_location:
            logger.info("Вечерние уведомления: все пользователи указали местоположение")
            return
        
        logger.info(f"Отправка вечерних уведомлений {len(users_without_location)} пользователям")
        
        for user in users_without_location:
            try:
                message = f"🌆 <b>Добрый вечер, {user['full_name']}!</b>\n\n"
                message += f"📍 Вы так и не указали свое местоположение сегодня.\n\n"
                message += f"⏰ Не забудьте отметиться перед завершением дня!"
                
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки вечернего уведомления пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке вечерних уведомлений: {e}")

async def send_periodic_reminders(bot: Bot):
    """Отправка периодических напоминаний"""
    try:
        users_without_location = get_users_without_location()
        
        if not users_without_location:
            logger.info("Периодические напоминания: все пользователи указали местоположение")
            return
        
        logger.info(f"Отправка периодических напоминаний {len(users_without_location)} пользователям")
        
        bro_phrases = get_bro_phrases()
        
        for user in users_without_location:
            try:
                # Выбираем случайную братскую фразу
                phrase = random.choice(bro_phrases)
                
                message = f"📢 <b>{user['full_name']}</b>\n\n"
                message += f"{phrase}\n\n"
                message += f"⏰ Время: {get_current_time().strftime('%H:%M')}"
                
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=message,
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки периодического напоминания пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке периодических напоминаний: {e}")

async def send_admin_notification(bot: Bot, message: str, admin_id: Optional[int] = None):
    """Отправка уведомления администратору"""
    try:
        if admin_id:
            # Отправляем конкретному админу
            await bot.send_message(
                chat_id=admin_id,
                text=f"🔔 <b>Уведомление администратора</b>\n\n{message}",
                parse_mode='HTML'
            )
        else:
            # Отправляем всем админам
            all_users = get_all_users()
            admins = [user for user in all_users if user['is_admin']]
            
            for admin in admins:
                try:
                    await bot.send_message(
                        chat_id=admin['telegram_id'],
                        text=f"🔔 <b>Уведомление администратора</b>\n\n{message}",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админу {admin['telegram_id']}: {e}")
                    
    except Exception as e:
        logger.error(f"Ошибка в отправке уведомления администратору: {e}")

async def send_system_notification(bot: Bot, message: str):
    """Отправка системного уведомления всем пользователям"""
    try:
        all_users = get_all_users()
        
        logger.info(f"Отправка системного уведомления {len(all_users)} пользователям")
        
        for user in all_users:
            try:
                await bot.send_message(
                    chat_id=user['telegram_id'],
                    text=f"📢 <b>Системное уведомление</b>\n\n{message}",
                    parse_mode='HTML'
                )
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Ошибка отправки системного уведомления пользователю {user['telegram_id']}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в отправке системного уведомления: {e}")

async def notify_about_user_action(bot: Bot, user_data: dict, action: str, location: str):
    """Уведомление о действии пользователя"""
    try:
        if not is_notifications_enabled():
            return
        
        # Определяем эмодзи для действия
        action_emoji = "✅" if action == "arrived" else "❌"
        action_text = "прибыл в" if action == "arrived" else "покинул"
        
        message = f"{action_emoji} <b>{user_data['full_name']}</b> {action_text} <b>{location}</b>\n"
        message += f"🕒 Время: {get_current_time().strftime('%H:%M')}\n"
        message += f"🆔 ID: <code>{user_data['telegram_id']}</code>"
        
        # Отправляем уведомление всем админам
        await send_admin_notification(bot, message)
        
    except Exception as e:
        logger.error(f"Ошибка в уведомлении о действии пользователя: {e}")

async def notify_about_registration(bot: Bot, user_data: dict):
    """Уведомление о регистрации нового пользователя"""
    try:
        if not is_notifications_enabled():
            return
        
        message = f"👤 <b>Новый пользователь зарегистрирован</b>\n\n"
        message += f"📝 ФИО: <b>{user_data['full_name']}</b>\n"
        message += f"🆔 ID: <code>{user_data['telegram_id']}</code>\n"
        
        if user_data.get('username'):
            message += f"📱 Username: @{user_data['username']}\n"
        
        message += f"🕒 Время регистрации: {get_current_time().strftime('%H:%M')}"
        
        # Отправляем уведомление всем админам
        await send_admin_notification(bot, message)
        
    except Exception as e:
        logger.error(f"Ошибка в уведомлении о регистрации: {e}")

async def send_daily_summary(bot: Bot):
    """Отправка ежедневной сводки"""
    try:
        from database import get_active_users_by_location, get_database_stats
        
        stats = get_database_stats()
        locations_data = get_active_users_by_location()
        users_without_location = get_users_without_location()
        
        summary = f"📊 <b>Ежедневная сводка</b>\n"
        summary += f"📅 Дата: {get_current_time().strftime('%d.%m.%Y')}\n"
        summary += f"🕒 Время: {get_current_time().strftime('%H:%M')}\n\n"
        
        summary += f"📈 <b>Статистика:</b>\n"
        summary += f"👥 Всего пользователей: {stats['users']}\n"
        summary += f"📍 Активных сессий: {stats['active_sessions']}\n"
        summary += f"🔴 Без местоположения: {len(users_without_location)}\n\n"
        
        if locations_data:
            summary += f"📍 <b>Распределение по локациям:</b>\n"
            for location, users in locations_data.items():
                summary += f"  • {location}: {len(users)} чел.\n"
        
        if users_without_location:
            summary += f"\n🔴 <b>Не указали местоположение:</b>\n"
            for user in users_without_location:
                summary += f"  • {user['full_name']}\n"
        
        # Отправляем сводку всем админам
        await send_admin_notification(bot, summary)
        
    except Exception as e:
        logger.error(f"Ошибка в отправке ежедневной сводки: {e}")

async def send_weekly_report(bot: Bot):
    """Отправка еженедельного отчета"""
    try:
        from database import get_location_logs, get_database_stats
        
        # Получаем логи за неделю
        week_logs = get_location_logs(limit=1000)  # Больше записей для недельного отчета
        stats = get_database_stats()
        
        report = f"📋 <b>Еженедельный отчет</b>\n"
        report += f"📅 Дата: {get_current_time().strftime('%d.%m.%Y')}\n"
        report += f"🕒 Время: {get_current_time().strftime('%H:%M')}\n\n"
        
        report += f"📊 <b>Статистика за неделю:</b>\n"
        report += f"📋 Всего записей: {len(week_logs)}\n"
        report += f"👥 Активных пользователей: {stats['active_sessions']}\n"
        report += f"📍 Всего локаций: {len(set(log['location'] for log in week_logs))}\n\n"
        
        # Анализ активности по дням
        if week_logs:
            from collections import defaultdict
            daily_activity = defaultdict(int)
            
            for log in week_logs:
                date = log['timestamp'][:10]  # Получаем дату
                daily_activity[date] += 1
            
            report += f"📈 <b>Активность по дням:</b>\n"
            for date, count in sorted(daily_activity.items()):
                report += f"  • {date}: {count} действий\n"
        
        # Отправляем отчет всем админам
        await send_admin_notification(bot, report)
        
    except Exception as e:
        logger.error(f"Ошибка в отправке еженедельного отчета: {e}")

async def send_custom_notification(bot: Bot, user_ids: List[int], message: str, sender_id: int):
    """Отправка пользовательского уведомления"""
    try:
        # Логируем отправку
        add_admin_log(sender_id, "Отправка пользовательского уведомления", 
                     details=f"Получателей: {len(user_ids)}")
        
        success_count = 0
        
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"📢 <b>Уведомление</b>\n\n{message}",
                    parse_mode='HTML'
                )
                success_count += 1
                
                # Небольшая задержка между сообщениями
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
        
        # Уведомляем отправителя о результате
        await bot.send_message(
            chat_id=sender_id,
            text=f"✅ <b>Уведомление отправлено</b>\n\n"
                 f"� Успешно: {success_count} из {len(user_ids)}\n"
                 f"🕒 Время: {get_current_time().strftime('%H:%M')}",
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в отправке пользовательского уведомления: {e}")

async def stop_notifications():
    """Остановка всех уведомлений"""
    global notification_tasks
    
    logger.info("Остановка системы уведомлений")
    
    for task in notification_tasks:
        if not task.done():
            task.cancel()
    
    notification_tasks.clear()

def is_notification_time():
    """Проверка, время ли отправлять уведомления"""
    current_time = get_current_time()
    current_hour = current_time.hour
    
    # Не отправляем уведомления ночью (с 22:00 до 7:00)
    if current_hour >= 22 or current_hour < 7:
        return False
    
    return True

async def send_emergency_notification(bot: Bot, message: str, priority: str = "high"):
    """Отправка экстренного уведомления"""
    try:
        priority_emoji = {
            "low": "🔵",
            "medium": "🟡", 
            "high": "🔴",
            "critical": "🚨"
        }.get(priority, "📢")
        
        notification_text = f"{priority_emoji} <b>ЭКСТРЕННОЕ УВЕДОМЛЕНИЕ</b>\n\n"
        notification_text += f"⚠️ Приоритет: {priority.upper()}\n\n"
        notification_text += f"{message}\n\n"
        notification_text += f"🕒 Время: {get_current_time().strftime('%d.%m.%Y %H:%M')}"
        
        # Отправляем всем пользователям
        await send_system_notification(bot, notification_text)
        
    except Exception as e:
        logger.error(f"Ошибка в отправке экстренного уведомления: {e}")

async def schedule_daily_summary(app: Application):
    """Планировщик ежедневной сводки"""
    while True:
        try:
            now = get_current_time()
            # Отправляем сводку в 19:00
            target_time = datetime.combine(now.date(), time(19, 0))
            
            # Если время уже прошло, планируем на завтра
            if target_time <= now:
                target_time += timedelta(days=1)
            
            # Ждем до целевого времени
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            # Отправляем ежедневную сводку
            await send_daily_summary(app.bot)
            
        except Exception as e:
            logger.error(f"Ошибка в планировщике ежедневной сводки: {e}")
            await asyncio.sleep(3600)  # Повторить через час