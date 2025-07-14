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
    
    # Новые настройки мониторинга
    AUTO_RESTART_INTERVAL = 86400  # 1 раз в сутки
HEALTH_REPORT_INTERVAL = 43200  # 12 часов
    ERROR_NOTIFICATION_ENABLED = True

# Глобальные переменные
running = True
start_time = None
session_start = None
last_health_report = None
error_count = 0
restart_count = 0

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
    """Асинхронный запуск бота с мониторингом"""
    global session_start, last_health_report, error_count
    session_start = time.time()
    
    try:
        logger.info("🚀 Запуск бота в асинхронном режиме...")
        
        # Импортируем компоненты бота
        from main import dp, on_startup, on_shutdown
        from aiogram import executor
        
        # Настраиваем executor для PythonAnywhere
        await on_startup(dp)
        
        # Планируем отчёты о здоровье каждые 12 часов
        last_health_report = time.time()
        
        # Запускаем polling с мониторингом
        await run_with_monitoring(dp)
        
    except Exception as e:
        error_count += 1
        logger.error(f"Ошибка в асинхронном режиме: {e}")
        await send_error_notification(str(e), "run_bot_async")
        raise
    finally:
        try:
            await on_shutdown(dp)
        except:
            pass

async def run_with_monitoring(dp):
    """Запуск с мониторингом и отчётами"""
    global last_health_report
    
    # Создаём задачи
    polling_task = asyncio.create_task(dp.start_polling(
        timeout=20,
        relax=0.1,
        fast=False,
        skip_updates=True
    ))
    
    monitoring_task = asyncio.create_task(monitoring_loop())
    
    # Ждём завершения любой из задач
    try:
        await asyncio.gather(polling_task, monitoring_task)
    except Exception as e:
        logger.error(f"Ошибка в мониторинге: {e}")
        polling_task.cancel()
        monitoring_task.cancel()
        raise

async def monitoring_loop():
    """Цикл мониторинга и отчётов"""
    global last_health_report
    
    while running:
        try:
            current_time = time.time()
            
            # Проверяем, нужно ли отправить отчёт о здоровье
            if current_time - last_health_report >= PythonAnywhereConfig.HEALTH_REPORT_INTERVAL:
                await send_health_report()
                last_health_report = current_time
            
            # Ждём 5 минут перед следующей проверкой
            await asyncio.sleep(300)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
            await send_error_notification(str(e), "monitoring_loop")
            await asyncio.sleep(60)  # Короткая пауза при ошибке

async def send_health_report():
    """Отправка отчёта о здоровье админу"""
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
        
        # Получаем отчёт о здоровье
        health_report = await health_monitor.get_health_report()
        
        # Добавляем информацию о работе
        uptime = time.time() - start_time if start_time else 0
        uptime_hours = uptime / 3600
        
        status_report = f"🤖 **Автоматический отчёт бота**\n\n"
        status_report += f"⏰ Время работы: {uptime_hours:.1f} часов\n"
        status_report += f"🔄 Перезапусков: {restart_count}\n"
        status_report += f"❌ Ошибок: {error_count}\n\n"
        status_report += health_report
        
        # Отправляем всем админам
        for admin_id in config.ADMIN_IDS:
            await notification_system.send_notification(admin_id, status_report)
        
        logger.info("📊 Отчёт о здоровье отправлен админам")
        
    except Exception as e:
        logger.error(f"Ошибка отправки отчёта о здоровье: {e}")

async def send_error_notification(error_msg: str, context: str = ""):
    """Отправка уведомления об ошибке админу"""
    if not PythonAnywhereConfig.ERROR_NOTIFICATION_ENABLED:
        return
        
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
        error_report += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
        error_report += f"📍 Контекст: {context}\n"
        error_report += f"❌ Ошибка: {error_msg}\n"
        error_report += f"🔄 Всего ошибок: {error_count}\n"
        error_report += f"🔄 Всего перезапусков: {restart_count}"
        
        # Отправляем всем админам
        for admin_id in config.ADMIN_IDS:
            await notification_system.send_notification(admin_id, error_report)
        
        logger.info("🚨 Уведомление об ошибке отправлено админам")
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления об ошибке: {e}")

def run_bot_session():
    """Запуск одной сессии бота"""
    global running, session_start, restart_count, error_count
    
    if not check_bot_health():
        logger.error("Проверка здоровья не пройдена")
        error_count += 1
        return False
    
    session_start = time.time()
    restart_count += 1
    logger.info(f"Начало сессии #{restart_count}: {datetime.now()}")
    
    try:
        # Создаем новый event loop
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Запускаем бота с мониторингом
        loop.run_until_complete(run_bot_async())
        
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
        return False
    except Exception as e:
        error_count += 1
        logger.error(f"Ошибка сессии: {e}")
        # Отправляем уведомление об ошибке (синхронно)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_error_notification(str(e), "run_bot_session"))
            loop.close()
        except:
            pass
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
        
            # Ждем максимум 2 часа (для Scheduled Task раз в сутки)
    wait_time = min(wait_seconds, 7200)
        time.sleep(wait_time)
        return False
    
    # В рабочих часах - короткая пауза перед следующей сессией
    logger.info("Пауза перед следующей сессией...")
    time.sleep(60)  # 1 минута
    return True

def main():
    """Главная функция для PythonAnywhere с автоматическим перезапуском раз в сутки"""
    global running, start_time, restart_count, error_count, last_health_report
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    start_time = time.time()
    last_health_report = start_time
    
    logger.info("🤖 Бот для PythonAnywhere запущен с автоматическим мониторингом")
    logger.info(f"📅 Время запуска: {datetime.now()}")
    logger.info(f"⏰ Рабочие часы: {PythonAnywhereConfig.WORK_START_HOUR}:00-{PythonAnywhereConfig.WORK_END_HOUR}:00")
    logger.info(f"🔄 Автоперезапуск: раз в сутки")
    logger.info(f"📊 Отчёты админу: каждые 12 часов")
    
    max_restarts = 10  # Увеличили лимит
    session_start_time = time.time()
    
    while running and restart_count < max_restarts:
        try:
            # Проверяем рабочие часы
            if not is_working_hours():
                logger.info("Вне рабочих часов, переходим в режим ожидания")
                if not wait_for_next_session():
                    continue
            
            # Проверяем, нужно ли перезапускаться раз в сутки
            current_time = time.time()
            session_duration = current_time - session_start_time
            
            if session_duration >= PythonAnywhereConfig.AUTO_RESTART_INTERVAL:
                logger.info(f"⏰ Автоматический перезапуск через {session_duration:.0f} сек")
                session_start_time = current_time
                # Не увеличиваем restart_count для автоматических перезапусков
            
            # Проверяем системные ресурсы
            if not check_system_resources():
                logger.warning("Ресурсы исчерпаны, завершаем сессию")
                break
            
            # Запускаем сессию бота
            logger.info(f"Запуск сессии (попытка #{restart_count + 1})")
            success = run_bot_session()
            
            if not success:
                restart_count += 1
                logger.warning(f"Сессия завершилась неуспешно. Попытка {restart_count}/{max_restarts}")
                
                if restart_count < max_restarts:
                    wait_time = min(60 * restart_count, 300)  # 1-5 минут
                    logger.info(f"Ожидание {wait_time} сек перед перезапуском...")
                    time.sleep(wait_time)
            else:
                # Успешная сессия - небольшая пауза перед следующей
                logger.info("✅ Сессия завершена успешно")
                time.sleep(30)  # 30 секунд
            
        except Exception as e:
            restart_count += 1
            error_count += 1
            logger.error(f"Критическая ошибка в главном цикле: {e}")
            
            # Отправляем уведомление об ошибке
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_error_notification(str(e), "main_loop"))
                loop.close()
            except:
                pass
            
            if restart_count < max_restarts:
                wait_time = min(120 * restart_count, 600)  # 2-10 минут
                logger.info(f"Ожидание {wait_time} сек после критической ошибки...")
                time.sleep(wait_time)
    
    # Финальная статистика
    total_time = time.time() - start_time if start_time else 0
    logger.info(f"🏁 Бот завершил работу")
    logger.info(f"📊 Общее время работы: {total_time:.0f} сек ({total_time/3600:.1f} часов)")
    logger.info(f"🔄 Количество перезапусков: {restart_count}")
    logger.info(f"❌ Всего ошибок: {error_count}")
    
    # Отправляем финальный отчёт
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        final_report = f"🏁 **Бот завершил работу**\n\n"
        final_report += f"⏰ Время работы: {total_time/3600:.1f} часов\n"
        final_report += f"🔄 Перезапусков: {restart_count}\n"
        final_report += f"❌ Ошибок: {error_count}\n"
        final_report += f"📅 Завершён: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        
        loop.run_until_complete(send_error_notification(final_report, "bot_shutdown"))
        loop.close()
    except:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")
        sys.exit(1)