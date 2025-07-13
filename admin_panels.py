"""
👑 Admin Panels - Многоуровневые админ-панели
3-уровневая структура управления для администраторов
"""

import sqlite3
import logging
from datetime import datetime
from ui_helpers import NavigationBuilder, MessageFormatter, CleanChat

logger = logging.getLogger(__name__)

class AdminPanels:
    """👑 Главный класс админ-панелей"""
    
    def __init__(self):
        self.nav = NavigationBuilder()
        self.formatter = MessageFormatter()
    
    async def show_admin_panel(self, query, context):
        """🏠 Уровень 1: Главное админ-меню"""
        text = self.formatter.format_admin_panel()
        keyboard = self.nav.build_admin_panel()
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_quick_summary(self, query, context):
        """📊 Быстрая сводка"""
        summary = await self._generate_quick_summary()
        keyboard = self.nav.build_back_menu("admin_panel")
        await CleanChat.edit_or_send(query, summary, keyboard)
    
    async def show_personnel_management(self, query, context):
        """👥 Уровень 2: Управление л/с"""
        text = (
            "👥 <b>УПРАВЛЕНИЕ ЛИЧНЫМ СОСТАВОМ</b>\n\n"
            "Работа с личным составом:"
        )
        keyboard = self.nav.build_personnel_menu()
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_event_log(self, query, context):
        """📖 Уровень 2: Журнал событий"""
        text = (
            "📖 <b>ЖУРНАЛ СОБЫТИЙ</b>\n\n"
            "История действий:"
        )
        keyboard = self.nav.build_event_log_menu()
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_settings(self, query, context):
        """⚙️ Уровень 2: Настройки"""
        text = (
            "⚙️ <b>НАСТРОЙКИ</b>\n\n"
            "Конфигурация системы:"
        )
        keyboard = self.nav.build_settings_menu()
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def show_danger_zone(self, query, context):
        """⚠️ Уровень 3: Опасная зона"""
        text = (
            "⚠️ <b>ОПАСНАЯ ЗОНА</b>\n\n"
            "🚨 <b>ВНИМАНИЕ!</b> Массовые операции:\n\n"
            "• Изменения необратимы\n"
            "• Требуют подтверждения\n"
            "• Влияют на всю систему\n\n"
            "Действуйте осторожно!"
        )
        keyboard = self.nav.build_danger_zone_menu()
        await CleanChat.edit_or_send(query, text, keyboard)

    async def _generate_quick_summary(self):
        """📊 Генерация быстрой сводки"""
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
                    away.append(f"• {name} → {display_location}")
            
            # Формируем сводку
            summary = f"📊 <b>БЫСТРАЯ СВОДКА</b>\n"
            summary += f"🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
            
            if in_base:
                summary += f"🟢 <b>В РАСПОЛОЖЕНИИ ({len(in_base)}):</b>\n"
                for name in in_base:
                    summary += f"• {name}\n"
                summary += "\n"
            
            if away:
                summary += f"🔴 <b>НЕ В РАСПОЛОЖЕНИИ ({len(away)}):</b>\n"
                summary += "\n".join(away) + "\n\n"
            
            summary += f"📋 <b>Всего личного состава:</b> {len(results)}"
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации сводки: {e}")
            return self.formatter.format_error("Не удалось сгенерировать сводку")

class DangerZoneOperations:
    """🚨 Операции опасной зоны"""
    
    def __init__(self):
        self.nav = NavigationBuilder()
        self.formatter = MessageFormatter()
    
    async def mark_all_arrived_confirmation(self, query, context):
        """🚨 Подтверждение отметки всех прибывшими"""
        text = (
            "🚨 <b>МАССОВАЯ ОПЕРАЦИЯ</b>\n\n"
            "⚠️ <b>Вы уверены?</b>\n\n"
            "Действие:\n"
            "• Отметить ВСЕХ бойцов как \"✅ Прибыл\"\n"
            "• Локация: ОБРМП\n"
            "• Время: текущее\n\n"
            "❗ Это действие необратимо!"
        )
        keyboard = self.nav.build_confirmation_menu("mark_all_arrived")
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def execute_mark_all_arrived(self, query, context):
        """✅ Выполнение отметки всех прибывшими"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Получаем всех пользователей
            cursor.execute("SELECT user_id, full_name FROM users")
            users = cursor.fetchall()
            
            # Отмечаем всех как прибывших
            for user_id, name in users:
                cursor.execute(
                    "INSERT INTO arrivals (user_id, location, status) VALUES (?, ?, ?)",
                    (user_id, "ОБРМП", "✅ Прибыл")
                )
            
            conn.commit()
            conn.close()
            
            text = self.formatter.format_success(
                f"Все {len(users)} бойцов отмечены как прибывшие в ОБРМП"
            )
            keyboard = self.nav.build_back_menu("settings_danger")
            await CleanChat.edit_or_send(query, text, keyboard)
            
        except Exception as e:
            logger.error(f"❌ Ошибка массовой отметки: {e}")
            text = self.formatter.format_error("Не удалось выполнить массовую отметку")
            keyboard = self.nav.build_back_menu("settings_danger")
            await CleanChat.edit_or_send(query, text, keyboard)
    
    async def clear_log_confirmation(self, query, context):
        """🗑️ Подтверждение очистки журнала"""
        text = (
            "🗑️ <b>ОЧИСТКА ЖУРНАЛА</b>\n\n"
            "⚠️ <b>ОПАСНОСТЬ!</b>\n\n"
            "Действие:\n"
            "• Удалить ВСЕ записи журнала\n"
            "• Потеря всей истории\n"
            "• Восстановление невозможно\n\n"
            "❗ Это действие НЕОБРАТИМО!"
        )
        keyboard = self.nav.build_confirmation_menu("clear_log")
        await CleanChat.edit_or_send(query, text, keyboard)
    
    async def execute_clear_log(self, query, context):
        """💥 Выполнение очистки журнала"""
        try:
            conn = sqlite3.connect('data/personnel.db')
            cursor = conn.cursor()
            
            # Считаем записи перед удалением
            cursor.execute("SELECT COUNT(*) FROM arrivals")
            count = cursor.fetchone()[0]
            
            # Очищаем журнал
            cursor.execute("DELETE FROM arrivals")
            conn.commit()
            conn.close()
            
            text = self.formatter.format_success(
                f"Журнал очищен. Удалено записей: {count}"
            )
            keyboard = self.nav.build_back_menu("settings_danger")
            await CleanChat.edit_or_send(query, text, keyboard)
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки журнала: {e}")
            text = self.formatter.format_error("Не удалось очистить журнал")
            keyboard = self.nav.build_back_menu("settings_danger")
            await CleanChat.edit_or_send(query, text, keyboard)