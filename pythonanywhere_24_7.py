#!/usr/bin/env python3
"""
🌐 Простое развертывание бота на PythonAnywhere для работы 24/7
Требует только токен бота и Telegram ID администратора
"""

import os
import sys
import subprocess
import re
import json
from datetime import datetime

def print_banner():
    """Красивый баннер"""
    print("=" * 70)
    print("🤖 PYTHONANYWHERE 24/7 BOT DEPLOYMENT")
    print("🔄 Автоперезапуск каждые 55 минут")
    print("📊 Отчеты о здоровье каждые 6 часов")
    print("🚨 Уведомления об ошибках")
    print("=" * 70)
    print()

def detect_pythonanywhere():
    """Определение среды PythonAnywhere"""
    indicators = [
        '/home/' in os.getcwd(),
        'pythonanywhere' in os.getcwd().lower(),
        os.path.exists('/var/log/pythonanywhere.log'),
        'PYTHONANYWHERE_SITE' in os.environ
    ]
    is_pa = any(indicators)
    
    if is_pa:
        print("✅ Обнаружена среда PythonAnywhere")
    else:
        print("⚠️ PythonAnywhere не обнаружен, но продолжаем...")
    
    return is_pa

def get_username():
    """Получение имени пользователя"""
    try:
        cwd = os.getcwd()
        if '/home/' in cwd:
            parts = cwd.split('/')
            for i, part in enumerate(parts):
                if part == 'home' and i + 1 < len(parts):
                    return parts[i + 1]
        return os.environ.get('USER', 'username')
    except:
        return 'username'

def get_simple_input(prompt, validator=None, description=""):
    """Простой ввод с валидацией"""
    if description:
        print(f"💡 {description}")
    
    while True:
        value = input(f"🔑 {prompt}: ").strip()
        if validator:
            if validator(value):
                return value
            print("❌ Неверный формат. Попробуйте снова.")
        else:
            if value:
                return value
            print("❌ Поле не может быть пустым.")

def validate_token(token):
    """Валидация токена бота"""
    return re.match(r'^\d+:[A-Za-z0-9_-]+$', token) is not None

def validate_telegram_id(user_id):
    """Валидация Telegram ID"""
    try:
        return int(user_id) > 0
    except:
        return False

def create_optimized_env(token, admin_id):
    """Создание оптимизированного .env файла"""
    env_content = f"""# 🤖 Telegram Bot Configuration for PythonAnywhere 24/7
BOT_TOKEN={token}
ADMIN_IDS={admin_id}

# 🗄️ Database Settings
DB_PATH=data/bot_database.db

# 🔔 Notification Settings
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30

# 📝 Logging Settings (optimized for PythonAnywhere)
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log

# 📁 Export Settings
EXPORT_PATH=exports/

# ⚡ Monitoring Settings (24/7 optimized)
HEALTH_CHECK_INTERVAL=21600  # 6 hours
AUTO_RESTART_INTERVAL=3300   # 55 minutes
ERROR_NOTIFICATION_ENABLED=true
PERFORMANCE_MONITORING=true

# 🌐 PythonAnywhere Specific Settings
PA_FREE_ACCOUNT=true
PA_MAX_SESSION_TIME=3300     # 55 minutes
PA_RESTART_MARGIN=300        # 5 minutes safety margin
PA_WORKING_HOURS_START=0     # 24/7 operation
PA_WORKING_HOURS_END=23
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Конфигурация .env создана")

def create_pa_optimized_runner():
    """Создание оптимизированного раннера для PythonAnywhere"""
    
    runner_content = '''#!/usr/bin/env python3
"""
🤖 PythonAnywhere 24/7 Bot Runner
Оптимизирован для работы на бесплатных аккаунтах
"""

import asyncio
import logging
import os
import sys
import time
import signal
from datetime import datetime
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_24_7.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PA247Config:
    """Конфигурация для работы 24/7"""
    MAX_SESSION_TIME = 3300      # 55 минут
    RESTART_MARGIN = 300         # 5 минут запас
    HEALTH_CHECK_INTERVAL = 300  # 5 минут
    HEALTH_REPORT_INTERVAL = 21600  # 6 часов
    MAX_MEMORY_MB = 120          # Лимит памяти
    MAX_RESTARTS = 20            # Максимум перезапусков

class BotRunner:
    """Раннер бота для PythonAnywhere"""
    
    def __init__(self):
        self.running = True
        self.start_time = time.time()
        self.session_start = None
        self.restart_count = 0
        self.error_count = 0
        self.last_health_report = time.time()
        
        # Регистрируем обработчики сигналов
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов"""
        logger.info(f"Получен сигнал {signum}, завершаем...")
        self.running = False
    
    def check_resources(self):
        """Проверка ресурсов"""
        try:
            # Проверяем память
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > PA247Config.MAX_MEMORY_MB:
                logger.warning(f"Высокое использование памяти: {memory_mb:.1f} МБ")
                return False
            
            # Проверяем время сессии
            if self.session_start:
                session_time = time.time() - self.session_start
                if session_time > PA247Config.MAX_SESSION_TIME:
                    logger.info(f"Время сессии истекло: {session_time:.0f} сек")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки ресурсов: {e}")
            return True
    
    async def send_health_report(self):
        """Отправка отчета о здоровье"""
        try:
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            uptime = time.time() - self.start_time
            uptime_hours = uptime / 3600
            
            report = f"🤖 **Отчет о работе бота**\\n\\n"
            report += f"⏰ Время работы: {uptime_hours:.1f} ч\\n"
            report += f"🔄 Перезапусков: {self.restart_count}\\n"
            report += f"❌ Ошибок: {self.error_count}\\n"
            report += f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\\n"
            report += f"💾 Память: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} МБ"
            
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, report)
            
            logger.info("📊 Отчет о здоровье отправлен")
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    async def send_error_notification(self, error_msg, context=""):
        """Отправка уведомления об ошибке"""
        try:
            from config import Config
            from notifications import NotificationSystem
            from database import Database
            from main import bot
            
            config = Config()
            db = Database()
            await db.init()
            
            notification_system = NotificationSystem(bot, db)
            
            error_report = f"🚨 **Ошибка в боте**\\n\\n"
            error_report += f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\\n"
            error_report += f"📍 Контекст: {context}\\n"
            error_report += f"❌ Ошибка: {error_msg}\\n"
            error_report += f"🔄 Всего ошибок: {self.error_count}"
            
            for admin_id in config.ADMIN_IDS:
                await notification_system.send_notification(admin_id, error_report)
            
            logger.info("🚨 Уведомление об ошибке отправлено")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    async def run_bot_session(self):
        """Запуск одной сессии бота"""
        self.session_start = time.time()
        self.restart_count += 1
        
        logger.info(f"🚀 Запуск сессии #{self.restart_count}")
        
        try:
            # Импортируем компоненты бота
            from main import dp, on_startup, on_shutdown
            
            # Инициализация
            await on_startup(dp)
            
            # Запуск с мониторингом
            await self.run_with_monitoring(dp)
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Ошибка сессии: {e}")
            await self.send_error_notification(str(e), "bot_session")
            raise
        finally:
            try:
                await on_shutdown(dp)
            except:
                pass
    
    async def run_with_monitoring(self, dp):
        """Запуск с мониторингом"""
        # Создаем задачи
        polling_task = asyncio.create_task(dp.start_polling(
            timeout=20,
            relax=0.1,
            fast=False,
            skip_updates=True
        ))
        
        monitoring_task = asyncio.create_task(self.monitoring_loop())
        
        try:
            await asyncio.gather(polling_task, monitoring_task)
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
            polling_task.cancel()
            monitoring_task.cancel()
            raise
    
    async def monitoring_loop(self):
        """Цикл мониторинга"""
        while self.running:
            try:
                current_time = time.time()
                
                # Отчет о здоровье каждые 6 часов
                if current_time - self.last_health_report >= PA247Config.HEALTH_REPORT_INTERVAL:
                    await self.send_health_report()
                    self.last_health_report = current_time
                
                # Проверка ресурсов каждые 5 минут
                await asyncio.sleep(PA247Config.HEALTH_CHECK_INTERVAL)
                
                if not self.check_resources():
                    logger.info("⏰ Время для перезапуска")
                    break
                    
            except Exception as e:
                self.error_count += 1
                logger.error(f"Ошибка мониторинга: {e}")
                await self.send_error_notification(str(e), "monitoring")
                await asyncio.sleep(60)
    
    def run_session(self):
        """Запуск одной сессии (синхронный)"""
        try:
            # Создаем новый event loop
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем сессию
            loop.run_until_complete(self.run_bot_session())
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки")
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
        
        return True
    
    def run_24_7(self):
        """Главный цикл 24/7"""
        logger.info("🤖 Запуск бота в режиме 24/7 для PythonAnywhere")
        logger.info(f"⏰ Автоперезапуск каждые {PA247Config.MAX_SESSION_TIME // 60} минут")
        logger.info(f"📊 Отчеты каждые {PA247Config.HEALTH_REPORT_INTERVAL // 3600} часов")
        
        while self.running and self.restart_count < PA247Config.MAX_RESTARTS:
            try:
                # Запускаем сессию
                success = self.run_session()
                
                if not success and self.running:
                    # Пауза перед перезапуском при ошибке
                    wait_time = min(60 * (self.error_count), 300)  # 1-5 минут
                    logger.info(f"Ожидание {wait_time} сек перед перезапуском...")
                    time.sleep(wait_time)
                elif self.running:
                    # Короткая пауза между успешными сессиями
                    logger.info("Пауза 30 сек перед следующей сессией...")
                    time.sleep(30)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"Критическая ошибка: {e}")
                time.sleep(60)
        
        # Финальная статистика
        total_time = time.time() - self.start_time
        logger.info(f"🏁 Бот завершил работу. Время: {total_time/3600:.1f} ч, перезапусков: {self.restart_count}")

def main():
    """Главная функция"""
    runner = BotRunner()
    runner.run_24_7()

if __name__ == "__main__":
    main()
'''
    
    with open('pa_24_7_runner.py', 'w', encoding='utf-8') as f:
        f.write(runner_content)
    
    print("✅ Создан оптимизированный раннер pa_24_7_runner.py")

def create_scheduled_task_script(username):
    """Создание скрипта для Scheduled Task"""
    
    task_script = f'''#!/bin/bash
# 🌐 Скрипт для PythonAnywhere Scheduled Task
# Запускается каждый час для поддержания работы 24/7

cd /home/{username}/telegram_bot

# Проверяем, есть ли уже запущенный процесс
if pgrep -f "pa_24_7_runner.py" > /dev/null; then
    echo "✅ Бот уже запущен, проверяем здоровье..."
    
    # Проверяем возраст процесса (если больше 58 минут - перезапускаем)
    PROCESS_AGE=$(ps -eo pid,etime,cmd | grep "pa_24_7_runner.py" | grep -v grep | awk '{{print $2}}' | head -1)
    
    if [[ -n "$PROCESS_AGE" ]]; then
        # Конвертируем время в секунды и проверяем
        SECONDS=$(echo $PROCESS_AGE | awk -F: '{{if (NF==3) print ($1*3600)+($2*60)+$3; else if (NF==2) print ($1*60)+$2; else print $1}}')
        
        if [[ $SECONDS -gt 3480 ]]; then  # 58 минут
            echo "⏰ Процесс работает слишком долго ($PROCESS_AGE), перезапускаем..."
            pkill -f "pa_24_7_runner.py"
            sleep 10
        else
            echo "✅ Процесс в порядке (работает $PROCESS_AGE)"
            exit 0
        fi
    fi
else
    echo "❌ Бот не запущен, запускаем..."
fi

# Активируем виртуальное окружение и запускаем
source venv_bot/bin/activate

# Проверяем .env файл
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

echo "🚀 Запуск бота в режиме 24/7..."
nohup python pa_24_7_runner.py > logs/scheduled_task.log 2>&1 &

echo "✅ Бот запущен в фоновом режиме"
'''
    
    with open('start_pa_24_7.sh', 'w', encoding='utf-8') as f:
        f.write(task_script)
    
    # Делаем исполняемым
    os.chmod('start_pa_24_7.sh', 0o755)
    
    print("✅ Создан скрипт start_pa_24_7.sh для Scheduled Task")
    
    return f"/home/{username}/telegram_bot/start_pa_24_7.sh"

def create_installation_guide(username, script_path):
    """Создание руководства по установке"""
    
    guide_content = f"""# 🚀 Руководство по установке Telegram Bot на PythonAnywhere 24/7

## ✅ Что уже настроено:
- 🤖 Конфигурация бота
- 🔄 Автоперезапуск каждые 55 минут
- 📊 Отчеты о здоровье каждые 6 часов
- 🚨 Уведомления об ошибках
- 🌐 Оптимизация для PythonAnywhere

## 🎯 Следующие шаги:

### 1. Установите зависимости (если еще не установлены):
```bash
cd ~/telegram_bot
source venv_bot/bin/activate
pip install -r requirements.txt
```

### 2. Настройте Scheduled Task в PythonAnywhere:

**a) Откройте Dashboard → Tasks → Scheduled**

**b) Создайте новую задачу:**
- **Command:** `{script_path}`
- **Hour:** `*` (каждый час)
- **Minute:** `0`
- **Description:** `Telegram Bot 24/7 Auto-restart`

**c) Сохраните задачу**

### 3. Проверьте работу:

```bash
# Проверить логи
tail -f logs/bot_24_7.log

# Проверить процессы
ps aux | grep python

# Ручной запуск для тестирования
./start_pa_24_7.sh
```

## 📊 Мониторинг:

### Логи:
- **Основные логи:** `logs/bot_24_7.log`
- **Scheduled Task:** `logs/scheduled_task.log`
- **Мониторинг:** `logs/monitor.log`

### Команды мониторинга:
```bash
# Статус процессов
ps aux | grep pa_24_7_runner

# Использование ресурсов
top -p $(pgrep -f pa_24_7_runner)

# Последние логи
tail -n 50 logs/bot_24_7.log
```

## 🔧 Управление:

```bash
# Остановить бота
pkill -f pa_24_7_runner

# Запустить вручную
python pa_24_7_runner.py

# Запустить через скрипт
./start_pa_24_7.sh
```

## 🚨 Важные особенности PythonAnywhere Free:

1. **Scheduled Tasks:** Только 1 задача, работает раз в час
2. **Время выполнения:** Ограничено на бесплатных аккаунтах
3. **Перезапуск:** Каждые 55 минут для стабильности
4. **Мониторинг:** Автоматические отчеты админу

## 📱 Что вы получите:

- ✅ Бот работает 24/7
- 🔄 Автоматический перезапуск каждые 55 минут
- 📊 Отчеты о здоровье каждые 6 часов
- 🚨 Мгновенные уведомления об ошибках
- 💾 Автоматическое управление памятью
- 📝 Подробные логи

## 🆘 Если что-то не работает:

1. Проверьте `.env` файл
2. Убедитесь, что виртуальное окружение активно
3. Проверьте логи на ошибки
4. Убедитесь, что Scheduled Task настроена правильно

**Время создания:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
**Пользователь:** {username}
"""
    
    with open('INSTALLATION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print("✅ Создано руководство INSTALLATION_GUIDE.md")

def main():
    """Главная функция простого развертывания"""
    print_banner()
    
    # Проверяем среду
    is_pa = detect_pythonanywhere()
    username = get_username()
    
    print(f"👤 Пользователь: {username}")
    print()
    
    # Простой ввод данных
    print("📝 Настройка бота (требуется только 2 параметра):")
    print()
    
    # Получаем токен
    token = get_simple_input(
        "Введите BOT_TOKEN",
        validate_token,
        "Получите токен у @BotFather в Telegram"
    )
    
    # Получаем Telegram ID
    admin_id = get_simple_input(
        "Введите ваш Telegram ID",
        validate_telegram_id,
        "Узнайте свой ID у @userinfobot в Telegram"
    )
    
    print("\n🔧 Создание конфигурации...")
    
    # Создаем директории
    for directory in ['data', 'logs', 'exports', 'config']:
        os.makedirs(directory, exist_ok=True)
    
    # Создаем файлы
    create_optimized_env(token, admin_id)
    create_pa_optimized_runner()
    script_path = create_scheduled_task_script(username)
    create_installation_guide(username, script_path)
    
    print("\n" + "=" * 70)
    print("🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 70)
    print()
    print("✅ Созданы файлы:")
    print("   📄 .env - конфигурация")
    print("   🤖 pa_24_7_runner.py - оптимизированный раннер")
    print("   📜 start_pa_24_7.sh - скрипт для Scheduled Task")
    print("   📚 INSTALLATION_GUIDE.md - руководство")
    print()
    print("🚀 Для завершения настройки:")
    print("   1. Настройте Scheduled Task в PythonAnywhere Dashboard")
    print("   2. Команда для задачи:")
    print(f"      {script_path}")
    print("   3. Расписание: каждый час (*/1 hour)")
    print()
    print("📖 Подробные инструкции в файле INSTALLATION_GUIDE.md")
    print()
    print("🎯 Ваш бот будет работать 24/7 с:")
    print("   🔄 Автоперезапуском каждые 55 минут")
    print("   📊 Отчетами каждые 6 часов")
    print("   🚨 Уведомлениями об ошибках")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Установка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка установки: {e}")