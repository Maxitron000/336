#!/usr/bin/env python3
"""
🌐 PythonAnywhere Daily Runner - Оптимизированный запуск бота 24/7
Учитывает ограничение: 1 Scheduled Task в сутки

Архитектура:
- Task запускается 1 раз в сутки
- Бот работает почти 24 часа с внутренними перезапусками каждые 55 минут
- Автоматическое завершение за 10 минут до следующего запуска Task
- Отчеты админу каждые 6 часов
- Мгновенные уведомления об ошибках
"""

import asyncio
import logging
import os
import sys
import time
import signal
from datetime import datetime, timedelta
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pa_daily.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PADailyConfig:
    """Конфигурация для работы с 1 Task в сутки"""
    
    # Время работы одной сессии (55 минут)
    SESSION_TIME = 3300  # 55 минут
    
    # Общее время работы в сутки (23 часа 50 минут)
    DAILY_WORK_TIME = 86400 - 600  # 24 часа - 10 минут запас
    
    # Интервалы мониторинга
    HEALTH_CHECK_INTERVAL = 300     # 5 минут
    HEALTH_REPORT_INTERVAL = 21600  # 6 часов
    
    # Лимиты ресурсов
    MAX_MEMORY_MB = 120
    MAX_SESSIONS_PER_DAY = 26  # ~24 часа / 55 минут
    
    # Безопасные паузы
    SESSION_PAUSE = 30      # 30 секунд между сессиями
    ERROR_PAUSE_BASE = 60   # Базовая пауза при ошибке

class BotDailyRunner:
    """Ежедневный раннер бота для PythonAnywhere"""
    
    def __init__(self):
        self.running = True
        self.start_time = time.time()
        self.session_count = 0
        self.error_count = 0
        self.last_health_report = time.time()
        
        # Создаем необходимые директории
        os.makedirs('logs', exist_ok=True)
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🚀 PythonAnywhere Daily Runner инициализирован")
        logger.info(f"📅 Планируемое время работы: {PADailyConfig.DAILY_WORK_TIME // 3600:.1f} часов")
        logger.info(f"🔄 Сессии по {PADailyConfig.SESSION_TIME // 60} минут")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        logger.info(f"Получен сигнал {signum}, корректное завершение...")
        self.running = False
    
    def should_continue_daily_work(self):
        """Проверка, следует ли продолжать работу в течение дня"""
        elapsed_time = time.time() - self.start_time
        
        # Проверяем общее время работы
        if elapsed_time >= PADailyConfig.DAILY_WORK_TIME:
            logger.info(f"⏰ Дневной лимит времени достигнут: {elapsed_time // 3600:.1f} часов")
            return False
        
        # Проверяем количество сессий
        if self.session_count >= PADailyConfig.MAX_SESSIONS_PER_DAY:
            logger.info(f"🔄 Дневной лимит сессий достигнут: {self.session_count}")
            return False
        
        # Проверяем критические ошибки
        if self.error_count > 10:
            logger.warning(f"❌ Слишком много ошибок: {self.error_count}")
            return False
        
        return True
    
    def check_session_resources(self, session_start_time):
        """Проверка ресурсов текущей сессии"""
        try:
            # Проверяем время сессии
            session_time = time.time() - session_start_time
            if session_time >= PADailyConfig.SESSION_TIME:
                logger.info(f"⏰ Время сессии истекло: {session_time:.0f} сек")
                return False
            
            # Проверяем память
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > PADailyConfig.MAX_MEMORY_MB:
                logger.warning(f"💾 Высокое использование памяти: {memory_mb:.1f} МБ")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки ресурсов сессии: {e}")
            return True  # Продолжаем при ошибке проверки
    
    async def send_health_report(self):
        """Отправка отчета о здоровье админу"""
        try:
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            # Рассчитываем статистику
            elapsed_time = time.time() - self.start_time
            uptime_hours = elapsed_time / 3600
            remaining_time = (PADailyConfig.DAILY_WORK_TIME - elapsed_time) / 3600
            
            # Статистика памяти
            try:
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            except:
                memory_mb = 0
            
            report = f"🤖 **Ежедневный отчет бота**\n\n"
            report += f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            report += f"⏰ Время работы: {uptime_hours:.1f} ч\n"
            report += f"⏳ Осталось: {remaining_time:.1f} ч\n"
            report += f"🔄 Сессий: {self.session_count}/{PADailyConfig.MAX_SESSIONS_PER_DAY}\n"
            report += f"❌ Ошибок: {self.error_count}\n"
            report += f"💾 Память: {memory_mb:.1f} МБ\n"
            report += f"📊 Статус: Работает штатно"
            
            # Отправляем всем админам
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, report)
            
            logger.info("📊 Отчет о здоровье отправлен админам")
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета о здоровье: {e}")
    
    async def send_error_notification(self, error_msg, context=""):
        """Отправка уведомления об ошибке админу"""
        try:
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            error_report = f"🚨 **Ошибка в боте**\n\n"
            error_report += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            error_report += f"📍 Контекст: {context}\n"
            error_report += f"❌ Ошибка: {error_msg}\n"
            error_report += f"🔄 Сессия: {self.session_count}\n"
            error_report += f"❌ Всего ошибок: {self.error_count}"
            
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, error_report)
            
            logger.info("🚨 Уведомление об ошибке отправлено")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    async def send_daily_summary(self):
        """Отправка итоговой сводки за день"""
        try:
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            total_time = time.time() - self.start_time
            total_hours = total_time / 3600
            
            summary = f"🏁 **Дневная сводка бота**\n\n"
            summary += f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
            summary += f"⏰ Общее время работы: {total_hours:.1f} ч\n"
            summary += f"🔄 Всего сессий: {self.session_count}\n"
            summary += f"❌ Всего ошибок: {self.error_count}\n"
            summary += f"📊 Эффективность: {((total_hours / 24) * 100):.1f}%\n"
            summary += f"🎯 Следующий запуск: завтра в то же время"
            
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, summary)
            
            logger.info("📋 Дневная сводка отправлена")
            
        except Exception as e:
            logger.error(f"Ошибка отправки дневной сводки: {e}")
    
    async def run_bot_session(self):
        """Запуск одной сессии бота (55 минут)"""
        session_start = time.time()
        self.session_count += 1
        
        logger.info(f"🚀 Запуск сессии #{self.session_count}")
        
        try:
            # Импортируем компоненты бота
            from main import dp, on_startup, on_shutdown
            
            # Инициализация
            await on_startup(dp)
            
            # Запуск с мониторингом
            await self.run_session_with_monitoring(dp, session_start)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Ошибка сессии #{self.session_count}: {e}")
            await self.send_error_notification(str(e), f"session_{self.session_count}")
            raise
        finally:
            try:
                await on_shutdown(dp)
            except:
                pass
            
            session_time = time.time() - session_start
            logger.info(f"✅ Сессия #{self.session_count} завершена за {session_time:.0f} сек")
    
    async def run_session_with_monitoring(self, dp, session_start):
        """Запуск сессии с мониторингом"""
        # Создаем задачи
        polling_task = asyncio.create_task(dp.start_polling(
            timeout=20,
            relax=0.1,
            fast=False,
            skip_updates=True
        ))
        
        monitoring_task = asyncio.create_task(
            self.session_monitoring_loop(session_start)
        )
        
        try:
            await asyncio.gather(polling_task, monitoring_task)
        except Exception as e:
            logger.error(f"Ошибка в мониторинге сессии: {e}")
            polling_task.cancel()
            monitoring_task.cancel()
            raise
    
    async def session_monitoring_loop(self, session_start):
        """Цикл мониторинга текущей сессии"""
        while self.running:
            try:
                current_time = time.time()
                
                # Отчет о здоровье каждые 6 часов
                if current_time - self.last_health_report >= PADailyConfig.HEALTH_REPORT_INTERVAL:
                    await self.send_health_report()
                    self.last_health_report = current_time
                
                # Проверка ресурсов каждые 5 минут
                await asyncio.sleep(PADailyConfig.HEALTH_CHECK_INTERVAL)
                
                # Проверяем, нужно ли завершить сессию
                if not self.check_session_resources(session_start):
                    logger.info("⏰ Время сессии завершено")
                    break
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"Ошибка в мониторинге сессии: {e}")
                await self.send_error_notification(str(e), "session_monitoring")
                await asyncio.sleep(60)
    
    def run_single_session(self):
        """Запуск одной сессии (синхронный wrapper)"""
        try:
            # Создаем новый event loop
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем сессию
            loop.run_until_complete(self.run_bot_session())
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки сессии")
            return False
        except Exception as e:
            self.error_count += 1
            logger.error(f"Ошибка сессии: {e}")
            return False
        finally:
            try:
                loop.close()
            except:
                pass
    
    def run_daily_cycle(self):
        """Главный дневной цикл работы"""
        logger.info("🌅 Начало дневного цикла работы бота")
        logger.info(f"🎯 Планируется {PADailyConfig.MAX_SESSIONS_PER_DAY} сессий по {PADailyConfig.SESSION_TIME // 60} минут")
        
        # Отправляем уведомление о начале работы
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_report = f"🌅 **Бот начал дневную работу**\n\n"
            start_report += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            start_report += f"🎯 Планируется: {PADailyConfig.MAX_SESSIONS_PER_DAY} сессий\n"
            start_report += f"⏰ Общее время: ~{PADailyConfig.DAILY_WORK_TIME // 3600} часов"
            
            loop.run_until_complete(self.send_error_notification(start_report, "daily_start"))
            loop.close()
        except:
            pass
        
        # Основной цикл сессий
        while self.running and self.should_continue_daily_work():
            try:
                # Запускаем сессию
                success = self.run_single_session()
                
                if not success and self.running:
                    # Пауза при ошибке
                    error_pause = min(
                        PADailyConfig.ERROR_PAUSE_BASE * self.error_count, 
                        300  # Максимум 5 минут
                    )
                    logger.info(f"⏸️ Пауза {error_pause} сек после ошибки...")
                    time.sleep(error_pause)
                elif self.running and self.should_continue_daily_work():
                    # Короткая пауза между успешными сессиями
                    logger.info(f"⏸️ Пауза {PADailyConfig.SESSION_PAUSE} сек между сессиями...")
                    time.sleep(PADailyConfig.SESSION_PAUSE)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Критическая ошибка в дневном цикле: {e}")
                time.sleep(60)
        
        # Отправляем итоговую сводку
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_daily_summary())
            loop.close()
        except:
            pass
        
        # Финальная статистика
        total_time = time.time() - self.start_time
        logger.info(f"🌙 Дневной цикл завершен")
        logger.info(f"⏰ Общее время работы: {total_time // 3600:.1f} часов")
        logger.info(f"🔄 Выполнено сессий: {self.session_count}")
        logger.info(f"❌ Всего ошибок: {self.error_count}")
        logger.info(f"📊 Эффективность: {((total_time / PADailyConfig.DAILY_WORK_TIME) * 100):.1f}%")

def main():
    """Главная функция для ежедневного запуска"""
    runner = BotDailyRunner()
    
    try:
        runner.run_daily_cycle()
    except KeyboardInterrupt:
        logger.info("🛑 Дневной цикл прерван пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка дневного цикла: {e}")

if __name__ == "__main__":
    main()