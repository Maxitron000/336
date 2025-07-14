#!/usr/bin/env python3
"""
🤖 Оптимизированная система мониторинга для PythonAnywhere 24/7
Перезапуск каждые 55 минут, отчеты каждые 6 часов, уведомления об ошибках
"""

import os
import sys
import time
import subprocess
import logging
import asyncio
import signal
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pa_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PythonAnywhere24x7Monitor:
    """Оптимизированный мониторинг для PythonAnywhere"""
    
    def __init__(self):
        # Конфигурация для оптимальной работы на PA
        self.RESTART_INTERVAL = 3300  # 55 минут (3300 секунд)
        self.HEALTH_REPORT_INTERVAL = 21600  # 6 часов (21600 секунд)
        self.ERROR_CHECK_INTERVAL = 60  # 1 минута
        self.MAX_MEMORY_MB = 100  # Лимит памяти для PA
        
        # Состояние системы
        self.bot_process = None
        self.monitor_start_time = datetime.now()
        self.last_restart = datetime.now()
        self.last_health_report = datetime.now()
        self.restart_count = 0
        self.error_count = 0
        self.running = True
        
        # Создаем директории
        Path('logs').mkdir(exist_ok=True)
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 PA 24x7 Monitor инициализирован")
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        logger.info(f"Получен сигнал {signum}, завершаем мониторинг...")
        self.running = False
        self._stop_bot()
    
    def _get_python_executable(self):
        """Получение пути к Python в виртуальном окружении"""
        venv_python = "venv_bot/bin/python"
        if os.path.exists(venv_python):
            return venv_python
        return sys.executable
    
    def _check_environment(self):
        """Проверка окружения перед запуском"""
        errors = []
        
        # Проверяем .env файл
        if not os.path.exists('.env'):
            errors.append("Отсутствует файл .env")
        
        # Проверяем основные файлы
        required_files = ['run_bot.py', 'main.py', 'database.py', 'handlers.py']
        for file in required_files:
            if not os.path.exists(file):
                errors.append(f"Отсутствует файл {file}")
        
        # Проверяем виртуальное окружение
        if not os.path.exists('venv_bot'):
            errors.append("Отсутствует виртуальное окружение venv_bot")
        
        if errors:
            for error in errors:
                logger.error(f"❌ {error}")
            return False
        
        logger.info("✅ Проверка окружения пройдена")
        return True
    
    def _start_bot(self):
        """Запуск бота"""
        try:
            if not self._check_environment():
                logger.error("❌ Проверка окружения не пройдена")
                return False
            
            # Останавливаем предыдущий процесс если есть
            self._stop_bot()
            
            python_exe = self._get_python_executable()
            logger.info(f"🚀 Запуск бота: {python_exe} run_bot.py")
            
            # Запускаем бота в новом процессе
            self.bot_process = subprocess.Popen(
                [python_exe, 'run_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                cwd=os.getcwd()
            )
            
            self.restart_count += 1
            self.last_restart = datetime.now()
            
            logger.info(f"✅ Бот запущен (PID: {self.bot_process.pid}, перезапуск #{self.restart_count})")
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Ошибка запуска бота: {e}")
            asyncio.create_task(self._send_error_notification(f"Ошибка запуска: {e}"))
            return False
    
    def _stop_bot(self):
        """Остановка бота"""
        try:
            if self.bot_process and self.bot_process.poll() is None:
                logger.info("🛑 Остановка бота...")
                
                # Пытаемся корректно завершить
                self.bot_process.terminate()
                
                # Ждем 10 секунд
                try:
                    self.bot_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Принудительное завершение
                    self.bot_process.kill()
                    self.bot_process.wait()
                
                logger.info("✅ Бот остановлен")
                self.bot_process = None
                
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
    
    def _is_bot_running(self):
        """Проверка, работает ли бот"""
        if self.bot_process is None:
            return False
        
        return self.bot_process.poll() is None
    
    def _should_restart(self):
        """Определение необходимости перезапуска"""
        now = datetime.now()
        
        # Плановый перезапуск каждые 55 минут
        time_since_restart = (now - self.last_restart).total_seconds()
        if time_since_restart >= self.RESTART_INTERVAL:
            logger.info(f"⏰ Плановый перезапуск (прошло {time_since_restart:.0f} сек)")
            return True
        
        # Проверяем, работает ли процесс
        if not self._is_bot_running():
            logger.warning("❌ Процесс бота не работает")
            return True
        
        return False
    
    async def _send_error_notification(self, error_msg: str):
        """Отправка уведомления об ошибке админу"""
        try:
            # Импортируем только при необходимости
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            error_report = f"🚨 **Ошибка в мониторинге PA**\n\n"
            error_report += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            error_report += f"❌ Ошибка: {error_msg}\n"
            error_report += f"🔄 Перезапусков: {self.restart_count}\n"
            error_report += f"🚨 Всего ошибок: {self.error_count}\n"
            error_report += f"⏰ Время работы монитора: {(datetime.now() - self.monitor_start_time).total_seconds()/3600:.1f} ч"
            
            # Отправляем всем админам
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, error_report)
            
            logger.info("🚨 Уведомление об ошибке отправлено")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления: {e}")
    
    async def _send_health_report(self):
        """Отправка отчета о здоровье админу"""
        try:
            from config import Config
            from monitoring import BotHealthMonitor
            from database import Database
            from notifications import NotificationSystem
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            health_monitor = BotHealthMonitor(db)
            notification_system = NotificationSystem(bot, db)
            
            # Получаем отчет о здоровье
            try:
                health_report = await health_monitor.get_health_report()
            except:
                health_report = "Не удалось получить детальный отчет"
            
            # Формируем отчет
            uptime = (datetime.now() - self.monitor_start_time).total_seconds() / 3600
            
            status_report = f"📊 **Отчет о здоровье бота PA**\n\n"
            status_report += f"🤖 Статус: {'🟢 Работает' if self._is_bot_running() else '🔴 Не работает'}\n"
            status_report += f"⏰ Время работы монитора: {uptime:.1f} часов\n"
            status_report += f"🔄 Количество перезапусков: {self.restart_count}\n"
            status_report += f"🚨 Количество ошибок: {self.error_count}\n"
            status_report += f"📅 Последний перезапуск: {self.last_restart.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            status_report += f"📋 Детали:\n{health_report}"
            
            # Отправляем всем админам
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, status_report)
            
            self.last_health_report = datetime.now()
            logger.info("📊 Отчет о здоровье отправлен")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета: {e}")
    
    def _should_send_health_report(self):
        """Проверка необходимости отправки отчета о здоровье"""
        time_since_report = (datetime.now() - self.last_health_report).total_seconds()
        return time_since_report >= self.HEALTH_REPORT_INTERVAL
    
    async def _monitor_cycle(self):
        """Один цикл мониторинга"""
        try:
            # Проверяем необходимость перезапуска
            if self._should_restart():
                logger.info("🔄 Выполняем перезапуск...")
                success = self._start_bot()
                if not success:
                    await self._send_error_notification("Не удалось перезапустить бота")
                    return False
            
            # Проверяем необходимость отчета о здоровье
            if self._should_send_health_report():
                logger.info("📊 Отправляем отчет о здоровье...")
                await self._send_health_report()
            
            # Проверяем статус бота
            if not self._is_bot_running():
                logger.warning("❌ Бот не работает, попытка запуска...")
                success = self._start_bot()
                if not success:
                    await self._send_error_notification("Не удалось запустить остановленного бота")
                    return False
            
            return True
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
            await self._send_error_notification(f"Ошибка мониторинга: {e}")
            return False
    
    async def start_monitoring(self):
        """Запуск системы мониторинга 24/7"""
        logger.info("🚀 Запуск системы мониторинга PA 24/7")
        logger.info(f"⏰ Интервал перезапуска: {self.RESTART_INTERVAL/60:.0f} минут")
        logger.info(f"📊 Интервал отчетов: {self.HEALTH_REPORT_INTERVAL/3600:.0f} часов")
        
        # Первый запуск бота
        if not self._start_bot():
            logger.error("❌ Не удалось запустить бота изначально")
            return
        
        # Отправляем стартовый отчет
        await self._send_health_report()
        
        # Основной цикл мониторинга
        while self.running:
            try:
                # Выполняем проверки
                await self._monitor_cycle()
                
                # Ждем перед следующей проверкой
                await asyncio.sleep(self.ERROR_CHECK_INTERVAL)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Критическая ошибка мониторинга: {e}")
                await self._send_error_notification(f"Критическая ошибка: {e}")
                
                # Пауза при критических ошибках
                await asyncio.sleep(300)  # 5 минут
        
        # Финальная остановка
        logger.info("🛑 Завершение мониторинга...")
        self._stop_bot()
        
        # Отправляем финальный отчет
        try:
            final_report = f"🏁 **Мониторинг PA завершен**\n\n"
            final_report += f"⏰ Время работы: {(datetime.now() - self.monitor_start_time).total_seconds()/3600:.1f} ч\n"
            final_report += f"🔄 Перезапусков: {self.restart_count}\n"
            final_report += f"🚨 Ошибок: {self.error_count}\n"
            final_report += f"📅 Завершен: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            
            await self._send_error_notification(final_report)
        except:
            pass

def main():
    """Главная функция"""
    monitor = PythonAnywhere24x7Monitor()
    
    try:
        # Запускаем мониторинг
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        logger.info("🛑 Мониторинг остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")

if __name__ == "__main__":
    main()