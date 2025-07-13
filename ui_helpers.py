"""
🎨 UI Helpers - Помощники пользовательского интерфейса
Модуль для чистого чата и навигации
"""

import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class UITexts:
    """📝 Класс для работы с текстами интерфейса"""
    
    def __init__(self):
        self.texts = self._load_texts()
    
    def _load_texts(self):
        """Загрузка текстов из JSON файла"""
        try:
            with open('notifications.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('ui_texts', {})
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки текстов UI: {e}")
            return {}
    
    def get(self, key, subkey=None):
        """Получение текста по ключу"""
        if subkey:
            return self.texts.get(key, {}).get(subkey, f"[{key}.{subkey}]")
        return self.texts.get(key, {})

class CleanChat:
    """🧹 Класс для поддержания чистоты чата"""
    
    @staticmethod
    async def delete_command(update, context: ContextTypes.DEFAULT_TYPE):
        """Удаление команды после вызова панели"""
        try:
            if update.message:
                await update.message.delete()
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение: {e}")
    
    @staticmethod
    async def edit_or_send(query_or_update, text, reply_markup=None):
        """Редактирование сообщения или отправка нового"""
        try:
            if hasattr(query_or_update, 'edit_message_text'):
                # Это CallbackQuery
                await query_or_update.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                # Это Update с сообщением
                await query_or_update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения: {e}")

class NavigationBuilder:
    """🧭 Конструктор навигации"""
    
    def __init__(self):
        self.ui_texts = UITexts()
    
    def build_main_menu(self, is_admin=False):
        """🏠 Главное меню"""
        keyboard = [
            [InlineKeyboardButton("✅ Прибыл", callback_data="user_arrived")],
            [InlineKeyboardButton("❌ Убыл", callback_data="user_departed")],
            [InlineKeyboardButton("📋 Мой журнал", callback_data="user_journal")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])
        
        return InlineKeyboardMarkup(keyboard)
    
    def build_admin_panel(self):
        """👑 Админ-панель (Уровень 1)"""
        keyboard = [
            [InlineKeyboardButton("📊 Быстрая сводка", callback_data="admin_quick_summary")],
            [InlineKeyboardButton("👥 Управление л/с", callback_data="admin_personnel")],
            [InlineKeyboardButton("📖 Журнал событий", callback_data="admin_event_log")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="admin_settings")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_personnel_menu(self):
        """👥 Управление л/с (Уровень 2)"""
        keyboard = [
            [InlineKeyboardButton("✏️ Сменить ФИО бойца", callback_data="personnel_edit_name")],
            [InlineKeyboardButton("➕ Добавить нового бойца", callback_data="personnel_add_user")],
            [InlineKeyboardButton("❌ Удалить бойца", callback_data="personnel_delete_user")],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_event_log_menu(self):
        """📖 Журнал событий (Уровень 2)"""
        keyboard = [
            [InlineKeyboardButton("📥 Экспорт журнала", callback_data="log_export")],
            [InlineKeyboardButton("📊 Статистика", callback_data="log_statistics")],
            [InlineKeyboardButton("🔍 Поиск по журналу", callback_data="log_search")],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_settings_menu(self):
        """⚙️ Настройки (Уровень 2)"""
        keyboard = [
            [InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton("👑 Управление админами", callback_data="settings_admins")],
            [InlineKeyboardButton("⚠️ Опасная зона", callback_data="settings_danger")],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin_panel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_danger_zone_menu(self):
        """⚠️ Опасная зона (Уровень 3)"""
        keyboard = [
            [InlineKeyboardButton("🚨 Отметить всех прибывшими", callback_data="danger_mark_all_arrived")],
            [InlineKeyboardButton("🗑️ Очистить весь журнал", callback_data="danger_clear_log")],
            [InlineKeyboardButton("💥 Сброс всех настроек", callback_data="danger_reset_settings")],
            [InlineKeyboardButton("🔙 Настройки", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_export_menu(self):
        """📥 Меню экспорта"""
        keyboard = [
            [InlineKeyboardButton("📄 Экспорт в CSV", callback_data="export_csv")],
            [InlineKeyboardButton("📊 Экспорт в XLSX", callback_data="export_xlsx")],
            [InlineKeyboardButton("🔙 Журнал событий", callback_data="admin_event_log")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_locations_menu(self, action="arrived"):
        """📍 Меню выбора локаций"""
        locations = {
            "🏥 Поликлиника": "Поликлиника",
            "⚓ ОБРМП": "ОБРМП", 
            "🌆 Калининград": "Калининград",
            "🛒 Магазин": "Магазин",
            "🍲 Столовая": "Столовая",
            "🏨 Госпиталь": "Госпиталь",
            "⚙️ Рабочка": "Рабочка",
            "🩺 ВВК": "ВВК",
            "🏛️ МФЦ": "МФЦ",
            "🚔 Патруль": "Патруль",
            "📝 Другое": "Другое"
        }
        
        keyboard = []
        for emoji_location, location in locations.items():
            keyboard.append([InlineKeyboardButton(
                emoji_location, 
                callback_data=f"location_{action}_{location}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    def build_confirmation_menu(self, action, data=""):
        """✅ Меню подтверждения"""
        keyboard = [
            [InlineKeyboardButton("✅ Да, подтверждаю", callback_data=f"confirm_{action}_{data}")],
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def build_back_menu(self, back_to="main_menu"):
        """🔙 Простое меню возврата"""
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=back_to)]]
        return InlineKeyboardMarkup(keyboard)

class MessageFormatter:
    """📝 Форматирование сообщений"""
    
    def __init__(self):
        self.ui_texts = UITexts()
    
    def format_main_menu(self, user_name, is_admin=False):
        """🏠 Форматирование главного меню"""
        status = "👑 Администратор" if is_admin else "🎖️ Боец"
        text = f"{status}: <b>{user_name}</b>\n\n"
        text += f"{self.ui_texts.get('main_menu', 'title')}\n"
        text += f"{self.ui_texts.get('main_menu', 'description')}"
        return text
    
    def format_admin_panel(self):
        """👑 Форматирование админ-панели"""
        text = f"{self.ui_texts.get('admin_panel', 'title')}\n\n"
        text += f"{self.ui_texts.get('admin_panel', 'description')}"
        return text
    
    def format_action_confirmation(self, name, action, location, time):
        """✅ Форматирование подтверждения действия"""
        action_emoji = "✅" if action == "arrived" else "❌"
        action_text = "прибыл" if action == "arrived" else "убыл"
        
        return (
            f"✅ <b>Отметка сохранена!</b>\n\n"
            f"🎖️ <b>Боец:</b> {name}\n"
            f"📍 <b>Действие:</b> {action_emoji} {action_text.capitalize()}\n"
            f"📍 <b>Локация:</b> {location}\n"
            f"🕐 <b>Время:</b> {time}"
        )
    
    def format_error(self, message):
        """❌ Форматирование ошибки"""
        return f"❌ <b>Ошибка:</b> {message}"
    
    def format_success(self, message):
        """✅ Форматирование успеха"""
        return f"✅ <b>Успех:</b> {message}"
    
    def format_warning(self, message):
        """⚠️ Форматирование предупреждения"""
        return f"⚠️ <b>Внимание:</b> {message}"