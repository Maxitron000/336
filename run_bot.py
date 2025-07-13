#!/usr/bin/env python3
"""
Скрипт для запуска бота на PythonAnywhere
Поддерживает работу 24/7 с автоматическим перезапуском
"""

import os
import sys
import time
import logging
import signal
from datetime import datetime, time as dt_time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
running = True
restart_count = 0
max_restarts = 10

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    global running
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    running = False

def is_working_hours():
    """Проверка, находимся ли мы в рабочих часах (5:00-24:00)"""
    now = datetime.now()
    start_time = dt_time(5, 0)  # 5:00
    end_time = dt_time(23, 59)  # 23:59
    
    return start_time <= now.time() <= end_time

def run_bot():
    """Запуск бота с обработкой ошибок"""
    global restart_count
    
    try:
        logger.info("🚀 Запуск бота...")
        
        # Импортируем и запускаем бота
        from main import dp, on_startup, on_shutdown
        from aiogram import executor
        
        # Запуск бота
        executor.start_polling(
            dp,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True
        )
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        restart_count += 1
        
        if restart_count <= max_restarts:
            logger.info(f"🔄 Перезапуск #{restart_count} через 30 секунд...")
            time.sleep(30)
            return True  # Сигнал для перезапуска
        else:
            logger.error(f"❌ Превышено максимальное количество перезапусков ({max_restarts})")
            return False  # Сигнал для завершения
    
    return False

def main():
    """Главная функция"""
    global running, restart_count
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🤖 Бот инициализирован")
    logger.info(f"📅 Дата запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    while running:
        try:
            # Проверяем рабочие часы
            if not is_working_hours():
                logger.info("😴 Вне рабочих часов (5:00-24:00), ожидаем...")
                time.sleep(3600)  # Ждем час
                continue
            
            # Запускаем бота
            should_restart = run_bot()
            
            if not should_restart:
                break
                
        except Exception as e:
            logger.error(f"❌ Ошибка в главном цикле: {e}")
            restart_count += 1
            
            if restart_count > max_restarts:
                logger.error("❌ Критическая ошибка, завершаем работу")
                break
            
            logger.info(f"🔄 Перезапуск через 60 секунд...")
            time.sleep(60)
    
    logger.info("✅ Бот завершил работу")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        sys.exit(1)