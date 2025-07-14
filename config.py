import os
import json
from dotenv import load_dotenv

class Config:
    """Класс для управления конфигурацией бота"""
    
    def __init__(self):
        # Загружаем переменные окружения
        load_dotenv()
        
        # Основные настройки
        self.BOT_TOKEN = os.getenv('BOT_TOKEN')
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")
        
        # Настройки базы данных
        self.DB_PATH = os.getenv('DB_PATH', 'data/bot_database.db')
        
        # Настройки уведомлений
        self.NOTIFICATIONS_ENABLED = os.getenv('NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
        self.DAILY_SUMMARY_TIME = os.getenv('DAILY_SUMMARY_TIME', '19:00')
        self.REMINDERS_TIME = os.getenv('REMINDERS_TIME', '20:30')
        
        # Настройки админов
        self.ADMIN_IDS = self._parse_admin_ids()
        
        # Настройки логирования
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
        
        # Настройки экспорта
        self.EXPORT_PATH = os.getenv('EXPORT_PATH', 'exports/')
        
        # Настройки мониторинга
        self.HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '43200'))  # 12 часов  
        self.AUTO_RESTART_INTERVAL = int(os.getenv('AUTO_RESTART_INTERVAL', '86400'))  # 1 раз в сутки
        self.ERROR_NOTIFICATION_ENABLED = os.getenv('ERROR_NOTIFICATION_ENABLED', 'true').lower() == 'true'
        self.PERFORMANCE_MONITORING = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
        
        # Создаем необходимые директории
        self._create_directories()
    
    def _parse_admin_ids(self):
        """Парсинг ID администраторов"""
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            return [int(x.strip()) for x in admin_ids_str.split(',') if x.strip().isdigit()]
        return []
    
    def _create_directories(self):
        """Создание необходимых директорий"""
        directories = [
            'data',
            'exports',
            'logs',
            'config'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_notification_texts(self):
        """Получение текстов уведомлений из файла"""
        try:
            with open('config/notifications.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Возвращаем тексты по умолчанию
            return {
                "reminders": [
                    "🔔 Эй, боец! Не забудь отметиться!",
                    "⏰ Время отметиться, товарищ!",
                    "📱 Ты еще не отметился сегодня!",
                    "🎯 Пора показать, что ты на месте!",
                    "💪 Не подведи команду - отметьсь!"
                ],
                "daily_summary": [
                    "📊 Ежедневная сводка готовности",
                    "📈 Отчет по личному составу",
                    "📋 Статистика на сегодня"
                ]
            }
    
    def save_notification_texts(self, texts):
        """Сохранение текстов уведомлений в файл"""
        try:
            with open('config/notifications.json', 'w', encoding='utf-8') as f:
                json.dump(texts, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            import logging
            logging.error(f"Ошибка сохранения текстов уведомлений: {e}")
            return False