#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы мониторинга бота
"""

import asyncio
import logging
from datetime import datetime
from database import Database
from notifications import NotificationSystem
from config import Config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_monitoring_system():
    """Тестирование системы мониторинга"""
    logger.info("🧪 Начинаем тестирование системы мониторинга...")
    
    try:
        # Инициализация компонентов
        config = Config()
        db = Database()
        await db.init()
        
        # Создаем мок-бот для тестирования
        class MockBot:
            async def get_me(self):
                class MockMe:
                    first_name = "TestBot"
                return MockMe()
            
            async def send_message(self, chat_id, text, **kwargs):
                logger.info(f"📤 Отправлено сообщение в {chat_id}: {text[:100]}...")
                return True
        
        bot = MockBot()
        notification_system = NotificationSystem(bot, db)
        
        logger.info("✅ Компоненты инициализированы")
        
        # Тест 1: Уведомление о статусе бота
        logger.info("🔍 Тест 1: Уведомление о статусе бота")
        success = await notification_system.send_bot_status_notification(
            "started", 
            "Тестовый запуск бота"
        )
        logger.info(f"Результат: {'✅' if success else '❌'}")
        
        # Тест 2: Проверка здоровья бота
        logger.info("🔍 Тест 2: Проверка здоровья бота")
        await notification_system.send_bot_health_check()
        logger.info("✅ Проверка здоровья выполнена")
        
        # Тест 3: Отчет производительности
        logger.info("🔍 Тест 3: Отчет производительности")
        await notification_system.send_bot_performance_report()
        logger.info("✅ Отчет производительности выполнен")
        
        # Тест 4: Уведомление об ошибке
        logger.info("🔍 Тест 4: Уведомление об ошибке")
        await notification_system.send_bot_error_notification(
            "Тестовая ошибка", 
            "Тестовый контекст"
        )
        logger.info("✅ Уведомление об ошибке отправлено")
        
        # Тест 5: Уведомление о ТО
        logger.info("🔍 Тест 5: Уведомление о ТО")
        await notification_system.send_bot_maintenance_notification(
            "scheduled", 
            "30 минут"
        )
        logger.info("✅ Уведомление о ТО отправлено")
        
        # Тест 6: Проверка подключения к БД
        logger.info("🔍 Тест 6: Проверка подключения к БД")
        db_connected = await db.is_connected()
        logger.info(f"База данных: {'✅' if db_connected else '❌'}")
        
        # Тест 7: Статистика уведомлений
        logger.info("🔍 Тест 7: Статистика уведомлений")
        stats = await notification_system.get_notification_stats()
        logger.info(f"Статистика: {stats}")
        
        logger.info("🎉 Все тесты завершены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестах: {e}")
        raise
    finally:
        await db.close()

async def test_admin_panel():
    """Тестирование админ-панели с мониторингом"""
    logger.info("🧪 Начинаем тестирование админ-панели...")
    
    try:
        # Инициализация компонентов
        config = Config()
        db = Database()
        await db.init()
        
        # Создаем мок-бот и систему уведомлений
        class MockBot:
            async def get_me(self):
                class MockMe:
                    first_name = "TestBot"
                return MockMe()
            
            async def send_message(self, chat_id, text, **kwargs):
                logger.info(f"📤 Отправлено сообщение в {chat_id}: {text[:100]}...")
                return True
        
        bot = MockBot()
        notification_system = NotificationSystem(bot, db)
        
        # Импортируем AdminPanel
        from admin import AdminPanel
        admin_panel = AdminPanel(db, notification_system)
        
        logger.info("✅ Админ-панель инициализирована")
        
        # Тест 1: Статистика системы
        logger.info("🔍 Тест 1: Статистика системы")
        stats = await admin_panel.get_system_stats()
        logger.info(f"Статистика системы: {stats}")
        
        # Тест 2: Форматирование статистики
        logger.info("🔍 Тест 2: Форматирование статистики")
        formatted_stats = await admin_panel.format_system_stats(stats)
        logger.info(f"Форматированная статистика:\n{formatted_stats}")
        
        # Тест 3: Детальная диагностика
        logger.info("🔍 Тест 3: Детальная диагностика")
        diagnostics = await admin_panel.get_detailed_diagnostics()
        logger.info(f"Диагностика:\n{diagnostics}")
        
        # Тест 4: История статусов
        logger.info("🔍 Тест 4: История статусов")
        history = await admin_panel.get_status_history()
        logger.info(f"История статусов:\n{history}")
        
        # Тест 5: Выполнение ТО
        logger.info("🔍 Тест 5: Выполнение ТО")
        maintenance_result = await admin_panel.perform_maintenance("scheduled")
        logger.info(f"Результат ТО:\n{maintenance_result}")
        
        # Тест 6: Лог ТО
        logger.info("🔍 Тест 6: Лог ТО")
        maintenance_log = await admin_panel.get_maintenance_log()
        logger.info(f"Лог ТО:\n{maintenance_log}")
        
        logger.info("🎉 Тесты админ-панели завершены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестах админ-панели: {e}")
        raise
    finally:
        await db.close()

async def test_commands():
    """Тестирование новых команд"""
    logger.info("🧪 Начинаем тестирование команд...")
    
    try:
        # Инициализация компонентов
        config = Config()
        db = Database()
        await db.init()
        
        # Создаем мок-бот
        class MockBot:
            async def get_me(self):
                class MockMe:
                    first_name = "TestBot"
                return MockMe()
            
            async def send_message(self, chat_id, text, **kwargs):
                logger.info(f"📤 Команда отправлена в {chat_id}: {text[:100]}...")
                return True
        
        bot = MockBot()
        notification_system = NotificationSystem(bot, db)
        
        logger.info("✅ Компоненты для команд инициализированы")
        
        # Тест команды /health
        logger.info("🔍 Тест команды /health")
        await notification_system.send_bot_health_check()
        
        # Тест команды /performance
        logger.info("🔍 Тест команды /performance")
        await notification_system.send_bot_performance_report()
        
        # Тест команды /maintenance
        logger.info("🔍 Тест команды /maintenance")
        await notification_system.send_bot_maintenance_notification(
            "emergency", 
            "15 минут"
        )
        
        logger.info("🎉 Тесты команд завершены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестах команд: {e}")
        raise
    finally:
        await db.close()

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск тестов системы мониторинга")
    
    try:
        # Тест 1: Система уведомлений
        await test_monitoring_system()
        
        # Тест 2: Админ-панель
        await test_admin_panel()
        
        # Тест 3: Команды
        await test_commands()
        
        logger.info("🎉 Все тесты завершены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в тестах: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)