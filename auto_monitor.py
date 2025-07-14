#!/usr/bin/env python3
"""
🔍 Автоматический мониторинг бота для PythonAnywhere
Проверяет состояние бота и автоматически перезапускает при необходимости
"""

import os
import sys
import time
import psutil
import subprocess
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BotMonitor:
    """Класс для мониторинга бота"""
    
    def __init__(self):
        self.bot_process = None
        self.start_time = None
        self.restart_count = 0
        self.last_health_check = None
        self.max_restarts_per_day = 5
        
        # Создаём необходимые директории
        os.makedirs('logs', exist_ok=True)
    
    def is_bot_running(self):
        """Проверка, запущен ли бот"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('run_bot.py' in cmd or 'main.py' in cmd for cmd in cmdline):
                    if proc.info['name'] == 'python' or proc.info['name'].startswith('python'):
                        return True
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки процесса: {e}")
            return False
    
    def start_bot(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск бота...")
            
            # Проверяем наличие файлов
            if not os.path.exists('.env'):
                logger.error("❌ Файл .env не найден! Запустите setup.py")
                return False
            
            if not os.path.exists('run_bot.py'):
                logger.error("❌ Файл run_bot.py не найден!")
                return False
            
            # Запускаем в фоновом режиме
            self.bot_process = subprocess.Popen(
                [sys.executable, 'run_bot.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.start_time = datetime.now()
            self.restart_count += 1
            
            logger.info(f"✅ Бот запущен (PID: {self.bot_process.pid}, перезапуск #{self.restart_count})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def stop_bot(self):
        """Остановка бота"""
        try:
            logger.info("🛑 Остановка бота...")
            
            # Останавливаем наш процесс
            if self.bot_process and self.bot_process.poll() is None:
                self.bot_process.terminate()
                time.sleep(5)
                if self.bot_process.poll() is None:
                    self.bot_process.kill()
            
            # Останавливаем все процессы бота
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('run_bot.py' in cmd or 'main.py' in cmd for cmd in cmdline):
                        if proc.info['name'] == 'python' or proc.info['name'].startswith('python'):
                            proc.terminate()
                            time.sleep(2)
                            if proc.is_running():
                                proc.kill()
                            logger.info(f"Остановлен процесс {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            logger.info("✅ Бот остановлен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
            return False
    
    def check_bot_health(self):
        """Проверка здоровья бота"""
        try:
            current_time = datetime.now()
            
            # Проверяем, запущен ли процесс
            if not self.is_bot_running():
                logger.warning("⚠️ Бот не запущен")
                return False
            
            # Проверяем файлы логов
            log_file = 'logs/bot.log'
            if os.path.exists(log_file):
                # Проверяем, есть ли свежие записи в логе
                mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if current_time - mod_time > timedelta(minutes=10):
                    logger.warning("⚠️ Лог файл не обновлялся более 10 минут")
                    return False
            
            # Проверяем использование ресурсов
            try:
                memory_usage = 0
                cpu_usage = 0
                
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('run_bot.py' in cmd or 'main.py' in cmd for cmd in cmdline):
                        if proc.info['name'] == 'python' or proc.info['name'].startswith('python'):
                            memory_usage += proc.info['memory_info'].rss / 1024 / 1024  # МБ
                            cpu_usage += proc.info['cpu_percent']
                
                if memory_usage > 150:  # Больше 150 МБ
                    logger.warning(f"⚠️ Высокое использование памяти: {memory_usage:.1f} МБ")
                    return False
                
                logger.info(f"✅ Здоровье бота: Память {memory_usage:.1f} МБ, CPU {cpu_usage:.1f}%")
                
            except Exception as e:
                logger.warning(f"Ошибка проверки ресурсов: {e}")
            
            self.last_health_check = current_time
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
            return False
    
    def should_restart(self):
        """Определение, нужно ли перезапускать бота"""
        current_time = datetime.now()
        
                    # Проверяем лимит перезапусков в день
            if self.restart_count > self.max_restarts_per_day:
                logger.warning(f"⚠️ Превышен лимит перезапусков в день: {self.restart_count}")
                return False
            
            # Перезапуск раз в сутки для профилактики
            if self.start_time and current_time - self.start_time > timedelta(days=1):
                logger.info("⏰ Плановый перезапуск (раз в сутки)")
                return True
        
        # Проверка здоровья
        if not self.check_bot_health():
            logger.warning("🏥 Проблемы со здоровьем бота")
            return True
        
        return False
    
    def monitor_loop(self):
        """Основной цикл мониторинга"""
        logger.info("🔍 Запуск системы мониторинга...")
                    logger.info("🔄 Автоперезапуск: раз в сутки")
        logger.info("📊 Проверка здоровья: каждые 5 минут")
        
        while True:
            try:
                current_time = datetime.now()
                
                            # Сброс счётчика перезапусков каждые сутки
            if hasattr(self, '_last_reset') and current_time - self._last_reset > timedelta(days=1):
                    self.restart_count = 0
                    self._last_reset = current_time
                elif not hasattr(self, '_last_reset'):
                    self._last_reset = current_time
                
                # Проверяем, запущен ли бот
                if not self.is_bot_running():
                    logger.warning("❌ Бот не запущен, запускаем...")
                    self.start_bot()
                    time.sleep(30)  # Даём время на запуск
                    continue
                
                # Проверяем, нужно ли перезапускать
                if self.should_restart():
                    logger.info("🔄 Перезапуск бота...")
                    self.stop_bot()
                    time.sleep(10)  # Пауза между остановкой и запуском
                    self.start_bot()
                    time.sleep(30)  # Даём время на запуск
                    continue
                
                # Обычная проверка здоровья
                self.check_bot_health()
                
                # Ждём 5 минут до следующей проверки
                time.sleep(300)
                
            except KeyboardInterrupt:
                logger.info("🛑 Получен сигнал остановки")
                self.stop_bot()
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Пауза при ошибке

def main():
    """Главная функция"""
    monitor = BotMonitor()
    
    try:
        monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("🛑 Мониторинг остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка мониторинга: {e}")

if __name__ == "__main__":
    main()