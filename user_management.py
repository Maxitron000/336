"""
👥 User Management - Управление личным составом
Добавление, удаление, редактирование пользователей
"""

import sqlite3
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ui_helpers import NavigationBuilder, MessageFormatter, CleanChat

logger = logging.getLogger(__name__)

class UserManager:
    """👥 Менеджер пользователей"""
    
    def __init__(self):
        self.nav = NavigationBuilder()
        self.formatter = MessageFormatter()
    
    async def show_add_user_prompt(self, query, context):
        """➕ Запрос добавления пользователя"""
        text = (
            "➕ <b>ДОБАВЛЕНИЕ НОВОГО БОЙЦА</b>\n\n"
            "📝 Введите данные в формате:\n"
            "<code>USER_ID ФИО</code>\n\n"
            "📋 <b>Пример:</b>\n"
            "<code>123456789 Новиков Н.Н.</code>\n\n"
            "💡 <b>Где взять USER_ID?</b>\n"
            "• Попросите бойца написать любое сообщение боту\n"
            "• ID будет показан в логах\n"
            "• Или используйте @userinfobot"
        )
        keyboard = self.nav.build_back_menu("admin_personnel")
        await CleanChat.edit_or_send(query, text, keyboard)
        
        # Устанавливаем состояние ожидания ввода
        context.user_data['waiting_for'] = 'add_user'
    
    async def show_edit_name_list(self, query, context):
        """✏️ Список пользователей для редактирования"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, full_name FROM users ORDER BY full_name")
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                text = self.formatter.format_warning("Список пользователей пуст")
                keyboard = self.nav.build_back_menu("admin_personnel")
                await CleanChat.edit_or_send(query, text, keyboard)
                return
            
            text = "✏️ <b>РЕДАКТИРОВАНИЕ ФИО</b>\n\n📋 Выберите бойца:\n\n"
            keyboard = []
            
            for user_id, name in users:
                keyboard.append([InlineKeyboardButton(
                    f"✏️ {name}", 
                    callback_data=f"edit_user_{user_id}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_personnel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await CleanChat.edit_or_send(query, text, reply_markup)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка пользователей: {e}")
            text = self.formatter.format_error("Не удалось загрузить список пользователей")
            keyboard = self.nav.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_edit_name_prompt(self, query, context, user_id):
        """✏️ Запрос нового ФИО"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                text = self.formatter.format_error("Пользователь не найден")
                keyboard = self.nav.build_back_menu("admin_personnel")
                await CleanChat.edit_or_send(query, text, keyboard)
                return
            
            current_name = result[0]
            text = (
                f"✏️ <b>РЕДАКТИРОВАНИЕ ФИО</b>\n\n"
                f"👤 <b>Текущее ФИО:</b> {current_name}\n\n"
                f"📝 Введите новое ФИО в формате:\n"
                f"<code>Фамилия И.О.</code>\n\n"
                f"📋 <b>Пример:</b> <code>Петров П.П.</code>"
            )
            keyboard = self.nav.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, text, keyboard)
            
            # Сохраняем ID для редактирования
            context.user_data['waiting_for'] = 'edit_name'
            context.user_data['edit_user_id'] = user_id
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных пользователя: {e}")
            text = self.formatter.format_error("Не удалось загрузить данные пользователя")
            keyboard = self.nav.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_delete_user_list(self, query, context):
        """❌ Список пользователей для удаления"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, full_name FROM users ORDER BY full_name")
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                text = self.formatter.format_warning("Список пользователей пуст")
                keyboard = self.nav.build_back_menu("admin_personnel")
                await CleanChat.edit_or_send(query, text, keyboard)
                return
            
            text = "❌ <b>УДАЛЕНИЕ БОЙЦА</b>\n\n⚠️ Выберите бойца для удаления:\n\n"
            keyboard = []
            
            for user_id, name in users:
                keyboard.append([InlineKeyboardButton(
                    f"❌ {name}", 
                    callback_data=f"delete_user_{user_id}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_personnel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await CleanChat.edit_or_send(query, text, reply_markup)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка пользователей: {e}")
            text = self.formatter.format_error("Не удалось загрузить список пользователей")
            keyboard = self.nav.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_delete_confirmation(self, query, context, user_id):
        """❌ Подтверждение удаления"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                text = self.formatter.format_error("Пользователь не найден")
                keyboard = self.nav.build_back_menu("admin_personnel")
                await CleanChat.edit_or_send(query, text, keyboard)
                return
            
            name = result[0]
            text = (
                f"❌ <b>УДАЛЕНИЕ БОЙЦА</b>\n\n"
                f"⚠️ <b>ВНИМАНИЕ!</b>\n\n"
                f"👤 <b>Боец:</b> {name}\n"
                f"📋 <b>ID:</b> <code>{user_id}</code>\n\n"
                f"🗑️ <b>Будет удалено:</b>\n"
                f"• Данные пользователя\n"
                f"• Вся история отметок\n"
                f"• Права доступа\n\n"
                f"❗ Это действие НЕОБРАТИМО!"
            )
            keyboard = self.nav.build_confirmation_menu("delete_user", user_id)
            await CleanChat.edit_or_send(query, text, keyboard)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных пользователя: {e}")
            text = self.formatter.format_error("Не удалось загрузить данные пользователя")
            keyboard = self.nav.build_back_menu("admin_personnel")
            await CleanChat.edit_or_send(query, text, keyboard)
    
    async def process_add_user(self, text, context):
        """➕ Обработка добавления пользователя"""
        try:
            # Парсим ввод
            parts = text.strip().split(' ', 1)
            if len(parts) != 2:
                return self.formatter.format_error(
                    "Неверный формат. Используйте: USER_ID ФИО"
                )
            
            user_id_str, full_name = parts
            
            # Валидация USER_ID
            try:
                user_id = int(user_id_str)
            except ValueError:
                return self.formatter.format_error("USER_ID должен быть числом")
            
            # Валидация ФИО
            if len(full_name) < 5 or '.' not in full_name:
                return self.formatter.format_error(
                    "ФИО должно быть в формате 'Фамилия И.О.'"
                )
            
            # Добавляем в базу
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, full_name) VALUES (?, ?)",
                    (user_id, full_name)
                )
                conn.commit()
                conn.close()
                
                return self.formatter.format_success(
                    f"Боец {full_name} (ID: {user_id}) добавлен в систему"
                )
                
            except sqlite3.IntegrityError:
                conn.close()
                return self.formatter.format_error(
                    "Пользователь с таким ID или ФИО уже существует"
                )
                
        except Exception as e:
            logger.error(f"❌ Ошибка добавления пользователя: {e}")
            return self.formatter.format_error("Не удалось добавить пользователя")
    
    async def process_edit_name(self, text, context):
        """✏️ Обработка редактирования ФИО"""
        try:
            user_id = context.user_data.get('edit_user_id')
            if not user_id:
                return self.formatter.format_error("Ошибка: ID пользователя не найден")
            
            # Валидация ФИО
            new_name = text.strip()
            if len(new_name) < 5 or '.' not in new_name:
                return self.formatter.format_error(
                    "ФИО должно быть в формате 'Фамилия И.О.'"
                )
            
            # Обновляем в базе
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Получаем старое имя
            cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
            old_result = cursor.fetchone()
            
            if not old_result:
                conn.close()
                return self.formatter.format_error("Пользователь не найден")
            
            old_name = old_result[0]
            
            try:
                cursor.execute(
                    "UPDATE users SET full_name = ? WHERE user_id = ?",
                    (new_name, user_id)
                )
                conn.commit()
                conn.close()
                
                return self.formatter.format_success(
                    f"ФИО изменено:\n• Было: {old_name}\n• Стало: {new_name}"
                )
                
            except sqlite3.IntegrityError:
                conn.close()
                return self.formatter.format_error("ФИО уже используется другим пользователем")
                
        except Exception as e:
            logger.error(f"❌ Ошибка редактирования ФИО: {e}")
            return self.formatter.format_error("Не удалось изменить ФИО")
    
    async def execute_delete_user(self, user_id):
        """🗑️ Выполнение удаления пользователя"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Получаем данные пользователя
            cursor.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return self.formatter.format_error("Пользователь не найден")
            
            name = result[0]
            
            # Удаляем записи из arrivals
            cursor.execute("DELETE FROM arrivals WHERE user_id = ?", (user_id,))
            arrivals_deleted = cursor.rowcount
            
            # Удаляем пользователя
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            user_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if user_deleted > 0:
                return self.formatter.format_success(
                    f"Боец {name} удален из системы\n"
                    f"• Удалено записей: {arrivals_deleted}"
                )
            else:
                return self.formatter.format_error("Пользователь не найден")
                
        except Exception as e:
            logger.error(f"❌ Ошибка удаления пользователя: {e}")
            return self.formatter.format_error("Не удалось удалить пользователя")