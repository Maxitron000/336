#!/usr/bin/env python3
"""
Оптимизированный скрипт запуска бота для PythonAnywhere
Учитывает ограничения бесплатного аккаунта
"""

import asyncio
import logging
import os
import sys
import time
import signal
from datetime import datetime, time as dt_time
import psutil
import subprocess

# Настройка логирования для PythonAnywhere
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_pa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация для PythonAnywhere
class PythonAnywhereConfig:
    # Рабочие часы (для экономии CPU времени)
    WORK_START_HOUR = 6
    WORK_END_HOUR = 23
    
    # Максимальное время работы за один сеанс (в секундах)
    MAX_SESSION_TIME = 3300  # 55 минут (остальные 5 мин на перезапуск)
    
    # Интервал проверки состояния
    HEALTH_CHECK_INTERVAL = 300  # 5 минут
    
    # Максимальное использование памяти (в МБ)
    MAX_MEMORY_MB = 100

# Глобальные переменные
running = True
start_time = None
session_start = None

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    global running
    logger.info(f"Получен сигнал {signum}, завершаем работу...")
    running = False

def is_working_hours():
    """Проверка рабочих часов"""
    now = datetime.now()
    current_hour = now.hour
    
    return PythonAnywhereConfig.WORK_START_HOUR <= current_hour <= PythonAnywhereConfig.WORK_END_HOUR

def check_system_resources():
    """Проверка системных ресурсов"""
    try:
        # Проверяем использование памяти
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb > PythonAnywhereConfig.MAX_MEMORY_MB:
            logger.warning(f"Высокое использование памяти: {memory_mb:.1f} МБ")
            return False
        
        # Проверяем время работы сессии
        if session_start:
            session_time = time.time() - session_start
            if session_time > PythonAnywhereConfig.MAX_SESSION_TIME:
                logger.info(f"Время сессии превышено: {session_time:.0f} сек")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки ресурсов: {e}")
        return True  # Продолжаем работу при ошибке проверки

def check_bot_health():
    """Проверка здоровья бота"""
    try:
        # Проверяем доступность файлов
        required_files = ['config.py', 'database.py', 'handlers.py']
        for file in required_files:
            if not os.path.exists(file):
                logger.error(f"Отсутствует файл: {file}")
                return False
        
        # Проверяем .env файл
        if not os.path.exists('.env'):
            logger.error("Отсутствует файл .env")
            return False
        
        # Проверяем базу данных
        db_path = os.getenv('DB_PATH', 'data/bot_database.db')
        if not os.path.exists(db_path):
            logger.warning(f"База данных не найдена: {db_path}")
            # Попытаемся создать
            try:
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                logger.info("Директория для БД создана")
            except Exception as e:
                logger.error(f"Ошибка создания директории БД: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья: {e}")
        return False

async def run_bot_async():
    """Асинхронный запуск бота"""
    global session_start
    session_start = time.time()
    
    try:
        logger.info("🚀 Запуск бота в асинхронном режиме...")
        
        # Импортируем компоненты бота
        from main import dp, on_startup, on_shutdown
        from aiogram import executor
        
        # Настраиваем executor для PythonAnywhere
        await on_startup(dp)
        
        # Запускаем polling с таймаутом
        await dp.start_polling(
            timeout=20,  # Короткий таймаут для PythonAnywhere
            relax=0.1,   # Небольшая пауза между запросами
            fast=False,  # Не использовать fast polling
            skip_updates=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка в асинхронном режиме: {e}")
        raise
    finally:
        try:
            await on_shutdown(dp)
        except:
            pass

def run_bot_session():
    """Запуск одной сессии бота"""
    global running, session_start
    
    if not check_bot_health():
        logger.error("Проверка здоровья не пройдена")
        return False
    
    session_start = time.time()
    logger.info(f"Начало сессии: {datetime.now()}")
    
    try:
        # Создаем новый event loop
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота
        loop.run_until_complete(run_bot_async())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        return False
    except Exception as e:
        logger.error(f"Ошибка сессии: {e}")
        return False
    finally:
        try:
            loop.close()
        except:
            pass
        
        session_time = time.time() - session_start if session_start else 0
        logger.info(f"Сессия завершена, время работы: {session_time:.0f} сек")
    
    return True

def wait_for_next_session():
    """Ожидание следующей сессии"""
    if not is_working_hours():
        # Вне рабочих часов - ждем до начала следующего рабочего дня
        now = datetime.now()
        next_start = now.replace(hour=PythonAnywhereConfig.WORK_START_HOUR, minute=0, second=0)
        
        if now.hour >= PythonAnywhereConfig.WORK_START_HOUR:
            # Завтра
            next_start = next_start.replace(day=next_start.day + 1)
        
        wait_seconds = (next_start - now).total_seconds()
        logger.info(f"Вне рабочих часов. Следующий запуск: {next_start}")
        
        # Ждем максимум 1 час (для Scheduled Task)
        wait_time = min(wait_seconds, 3600)
        time.sleep(wait_time)
        return False
    
    # В рабочих часах - короткая пауза перед следующей сессией
    logger.info("Пауза перед следующей сессией...")
    time.sleep(60)  # 1 минута
    return True

def main():
    """Главная функция для PythonAnywhere"""
    global running, start_time
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_time = time.time()
    
    logger.info("🤖 Бот для PythonAnywhere запущен")
    logger.info(f"📅 Время запуска: {datetime.now()}")
    logger.info(f"⏰ Рабочие часы: {PythonAnywhereConfig.WORK_START_HOUR}:00-{PythonAnywhereConfig.WORK_END_HOUR}:00")
    
    restart_count = 0
    max_restarts = 5
    
    while running and restart_count < max_restarts:
        try:
            # Проверяем рабочие часы
            if not is_working_hours():
                logger.info("Вне рабочих часов, переходим в режим ожидания")
                if not wait_for_next_session():
                    continue
            
            # Проверяем системные ресурсы
            if not check_system_resources():
                logger.warning("Ресурсы исчерпаны, завершаем сессию")
                break
            
            # Запускаем сессию бота
            logger.info(f"Запуск сессии #{restart_count + 1}")
            success = run_bot_session()
            
            if not success:
                restart_count += 1
                logger.warning(f"Сессия завершилась неуспешно. Попытка {restart_count}/{max_restarts}")
                
                if restart_count < max_restarts:
                    wait_time = min(60 * restart_count, 300)  # 1-5 минут
                    logger.info(f"Ожидание {wait_time} сек перед перезапуском...")
                    time.sleep(wait_time)
            else:
                restart_count = 0  # Сброс счетчика при успешной сессии
                
                # Пауза между сессиями
                if not wait_for_next_session():
                    continue
            
        except Exception as e:
            restart_count += 1
            logger.error(f"Критическая ошибка в главном цикле: {e}")
            
            if restart_count < max_restarts:
                wait_time = min(120 * restart_count, 600)  # 2-10 минут
                logger.info(f"Ожидание {wait_time} сек после критической ошибки...")
                time.sleep(wait_time)
    
    # Финальная статистика
    total_time = time.time() - start_time if start_time else 0
    logger.info(f"🏁 Бот завершил работу")
    logger.info(f"📊 Общее время работы: {total_time:.0f} сек")
    logger.info(f"🔄 Количество перезапусков: {restart_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        sys.exit(1)