"""
🔔 Notification System - Расширенная система уведомлений
Гибкие настройки, красивый формат, автоматические рассылки
"""

import json
import sqlite3
import logging
import asyncio
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ui_helpers import NavigationBuilder, MessageFormatter, CleanChat

logger = logging.getLogger(__name__)

class NotificationSettings:
    """⚙️ Настройки уведомлений"""
    
    def __init__(self):
        self.settings = {
            'summary_time': '19:00',
            'reminder_time': '20:30',
            'summary_enabled': True,
            'reminder_enabled': True,
            'silent_mode': False,
            'admin_notifications': True,
            'user_notifications': True,
            'arrival_notifications': True,
            'departure_notifications': True
        }
    
    def get(self, key):
        """Получение настройки"""
        return self.settings.get(key, False)
    
    def set(self, key, value):
        """Установка настройки"""
        self.settings[key] = value
    
    def toggle(self, key):
        """Переключение настройки"""
        self.settings[key] = not self.settings.get(key, False)
        return self.settings[key]

class NotificationTemplates:
    """📝 Шаблоны уведомлений"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self):
        """Загрузка шаблонов из JSON"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('notification_templates', {})
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки шаблонов: {e}")
            return {}
    
    def get_reminder_texts(self):
        """Получение текстов напоминаний"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('reminder_texts', [])
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки текстов напоминаний: {e}")
            return ["Отметьтесь о прибытии!"]
    
    def format_arrival(self, name, location, time):
        """Форматирование уведомления о прибытии"""
        template = self.templates.get('arrival', {})
        return template.get('format', '🎖️ Боец: {name}\n📍 Действие: Прибыл\n📍 Локация: {location}\n🕐 Время: {time}').format(
            name=name, location=location, time=time
        )
    
    def format_departure(self, name, location, time):
        """Форматирование уведомления об убытии"""
        template = self.templates.get('departure', {})
        return template.get('format', '🎖️ Боец: {name}\n📍 Действие: Убыл\n📍 Локация: {location}\n🕐 Время: {time}').format(
            name=name, location=location, time=time
        )
    
    def format_summary(self, in_base, away, total, time):
        """Форматирование сводки"""
        template = self.templates.get('summary', {})
        
        text = template.get('header', '📊 СВОДКА ЛИЧНОГО СОСТАВА\n🕐 {time}\n\n').format(time=time)
        
        if in_base:
            text += template.get('in_base', '🟢 В РАСПОЛОЖЕНИИ ({count}):\n').format(count=len(in_base))
            for person in in_base:
                text += f"• {person}\n"
            text += "\n"
        
        if away:
            text += template.get('away', '🔴 НЕ В РАСПОЛОЖЕНИИ ({count}):\n').format(count=len(away))
            for person in away:
                text += f"• {person}\n"
            text += "\n"
        
        text += template.get('footer', '\n📋 Всего личного состава: {total}').format(total=total)
        
        return text
    
    def format_reminder(self, text):
        """Форматирование напоминания"""
        template = self.templates.get('reminder', {})
        prefix = template.get('prefix', '⏰ Напоминание:')
        suffix = template.get('suffix', '\n\n📍 Нажмите ✅ Прибыл, когда вернетесь!')
        
        return f"{prefix} {text}{suffix}"

class NotificationManager:
    """🔔 Менеджер уведомлений"""
    
    def __init__(self, application):
        self.app = application
        self.settings = NotificationSettings()
        self.templates = NotificationTemplates()
        self.nav = NavigationBuilder()
        self.formatter = MessageFormatter()
    
    async def send_arrival_notification(self, name, location, time, admin_ids):
        """📍 Уведомление о прибытии"""
        if not self.settings.get('arrival_notifications') or self.settings.get('silent_mode'):
            return
        
        message = self.templates.format_arrival(name, location, time)
        
        for admin_id in admin_ids:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления о прибытии админу {admin_id}: {e}")
    
    async def send_departure_notification(self, name, location, time, admin_ids):
        """🚪 Уведомление об убытии"""
        if not self.settings.get('departure_notifications') or self.settings.get('silent_mode'):
            return
        
        message = self.templates.format_departure(name, location, time)
        
        for admin_id in admin_ids:
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления об убытии админу {admin_id}: {e}")
    
    async def send_daily_summary(self, admin_ids):
        """📊 Ежедневная сводка в 19:00"""
        if not self.settings.get('summary_enabled') or self.settings.get('silent_mode'):
            return
        
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Получаем последнюю отметку каждого пользователя
            cursor.execute("""
                SELECT u.user_id, u.full_name, a.location, a.custom_location, a.status, a.created_at
                FROM users u
                LEFT JOIN arrivals a ON u.user_id = a.user_id
                WHERE a.created_at = (
                    SELECT MAX(created_at) FROM arrivals WHERE user_id = u.user_id
                ) OR a.created_at IS NULL
                ORDER BY u.full_name
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            # Группируем по статусу
            in_base = []
            away = []
            
            for user_id, name, location, custom_location, status, created_at in results:
                if not location or status == "✅ Прибыл":
                    in_base.append(name)
                else:
                    display_location = custom_location if custom_location else location
                    away.append(f"{name} → {display_location}")
            
            # Формируем и отправляем сводку
            time_str = datetime.now().strftime('%H:%M %d.%m.%Y')
            summary = self.templates.format_summary(in_base, away, len(results), time_str)
            
            for admin_id in admin_ids:
                try:
                    await self.app.bot.send_message(
                        chat_id=admin_id,
                        text=summary,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки сводки админу {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сводки: {e}")
    
    async def send_return_reminders(self):
        """💬 Напоминания не вернувшимся в 20:30"""
        if not self.settings.get('reminder_enabled') or self.settings.get('silent_mode'):
            return
        
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Находим пользователей, которые убыли но не отметились о возвращении
            cursor.execute("""
                SELECT u.user_id, u.full_name, a.location, a.custom_location, a.created_at
                FROM users u
                JOIN arrivals a ON u.user_id = a.user_id
                WHERE a.created_at = (
                    SELECT MAX(created_at) FROM arrivals WHERE user_id = u.user_id
                ) AND a.status = '❌ Убыл'
                AND DATE(a.created_at) = DATE('now')
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return
            
            # Получаем случайные тексты напоминаний
            reminder_texts = self.templates.get_reminder_texts()
            
            # Отправляем напоминания
            for user_id, name, location, custom_location, created_at in results:
                try:
                    # Выбираем случайную фразу
                    random_text = random.choice(reminder_texts)
                    reminder = self.templates.format_reminder(random_text)
                    
                    await self.app.bot.send_message(
                        chat_id=user_id,
                        text=reminder,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки напоминания пользователю {user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка отправки напоминаний: {e}")

class NotificationSettingsPanel:
    """🔔 Панель настроек уведомлений"""
    
    def __init__(self, notification_manager):
        self.notification_manager = notification_manager
        self.nav = NavigationBuilder()
        self.formatter = MessageFormatter()
    
    async def show_notification_settings(self, query, context):
        """🔔 Показать настройки уведомлений"""
        settings = self.notification_manager.settings
        
        summary_status = "✅ Включена" if settings.get('summary_enabled') else "❌ Отключена"
        reminder_status = "✅ Включены" if settings.get('reminder_enabled') else "❌ Отключены"
        silent_status = "🔕 Включен" if settings.get('silent_mode') else "🔔 Отключен"
        arrival_status = "✅" if settings.get('arrival_notifications') else "❌"
        departure_status = "✅" if settings.get('departure_notifications') else "❌"
        
        text = (
            f"🔔 <b>НАСТРОЙКИ УВЕДОМЛЕНИЙ</b>\n\n"
            f"📊 <b>Сводка:</b> {summary_status}\n"
            f"🕐 <b>Время сводки:</b> {settings.get('summary_time')}\n\n"
            f"💬 <b>Напоминания:</b> {reminder_status}\n"
            f"🕕 <b>Время напоминаний:</b> {settings.get('reminder_time')}\n\n"
            f"🔕 <b>Режим тишины:</b> {silent_status}\n\n"
            f"📍 <b>Уведомления о событиях:</b>\n"
            f"• Прибытие: {arrival_status}\n"
            f"• Убытие: {departure_status}\n\n"
            f"📋 <b>Всего текстов напоминаний:</b> {len(self.notification_manager.templates.get_reminder_texts())}"
        )
        
        keyboard = [
            [InlineKeyboardButton(f"📊 Сводка: {summary_status}", callback_data="toggle_summary")],
            [InlineKeyboardButton(f"💬 Напоминания: {reminder_status}", callback_data="toggle_reminders")],
            [InlineKeyboardButton(f"🔕 Режим тишины: {silent_status}", callback_data="toggle_silent")],
            [InlineKeyboardButton(f"📍 Прибытие: {arrival_status}", callback_data="toggle_arrival")],
            [InlineKeyboardButton(f"🚪 Убытие: {departure_status}", callback_data="toggle_departure")],
            [InlineKeyboardButton("⏰ Настройка времени", callback_data="settings_time")],
            [InlineKeyboardButton("🔙 Настройки", callback_data="admin_settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await CleanChat.edit_or_send(query, text, reply_markup)
    
    async def toggle_setting(self, query, context, setting_key):
        """🔄 Переключение настройки"""
        new_value = self.notification_manager.settings.toggle(setting_key)
        status = "включена" if new_value else "отключена"
        
        setting_names = {
            'summary_enabled': 'Сводка',
            'reminder_enabled': 'Напоминания',
            'silent_mode': 'Режим тишины',
            'arrival_notifications': 'Уведомления о прибытии',
            'departure_notifications': 'Уведомления об убытии'
        }
        
        setting_name = setting_names.get(setting_key, setting_key)
        
        # Показываем уведомление
        await query.answer(f"{setting_name} {status}!")
        
        # Обновляем панель
        await self.show_notification_settings(query, context)