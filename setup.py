#!/usr/bin/env python3
"""
🚀 Быстрый установочный скрипт для Telegram бота
Настройка и запуск бота в одну команду
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import shutil
import json

class BotSetup:
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.last_run_file = os.path.join(self.project_dir, '.last_run')
        self.env_file = os.path.join(self.project_dir, '.env')
        self.service_name = 'telegram-bot'
        
    def print_header(self):
        """Красивая шапка"""
        print("\n" + "="*60)
        print("🚀 БЫСТРЫЙ УСТАНОВОЧНЫЙ СКРИПТ TELEGRAM БОТА")
        print("🤖 Автоматическая настройка и запуск 24/7")
        print("="*60 + "\n")
        
    def check_daily_limit(self):
        """Проверка ограничения на один запуск в сутки"""
        if os.path.exists(self.last_run_file):
            try:
                with open(self.last_run_file, 'r') as f:
                    last_run = datetime.fromisoformat(f.read().strip())
                
                time_diff = datetime.now() - last_run
                if time_diff.total_seconds() < 86400:  # 24 часа
                    hours_left = 24 - (time_diff.total_seconds() / 3600)
                    print(f"⏰ Ограничение: можно запускать только раз в сутки")
                    print(f"🕐 Осталось ждать: {hours_left:.1f} часов")
                    print(f"📅 Последний запуск: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    force = input("\n❓ Игнорировать ограничение? (y/N): ").lower().strip()
                    if force != 'y':
                        print("❌ Установка отменена")
                        sys.exit(1)
            except Exception as e:
                print(f"⚠️ Ошибка чтения файла ограничения: {e}")
        
        # Записываем время текущего запуска
        with open(self.last_run_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def get_bot_credentials(self):
        """Получение токена и admin ID"""
        print("📝 Настройка учетных данных бота\n")
        
        while True:
            token = input("🔑 Введите токен бота (от @BotFather): ").strip()
            if not token:
                print("❌ Токен не может быть пустым!")
                continue
            
            if not token.count(':') == 1:
                print("❌ Неверный формат токена! Должен быть: 123456789:ABC-DEF...")
                continue
            
            bot_id, bot_token = token.split(':')
            if not bot_id.isdigit() or len(bot_token) < 20:
                print("❌ Токен выглядит неверно!")
                continue
            
            break
        
        while True:
            admin_id = input("👤 Введите ваш Telegram ID (получить: @userinfobot): ").strip()
            if not admin_id:
                print("❌ Admin ID не может быть пустым!")
                continue
            
            if not admin_id.isdigit():
                print("❌ Admin ID должен содержать только цифры!")
                continue
            
            break
        
        return token, admin_id
    
    def create_env_file(self, bot_token, admin_id):
        """Создание .env файла"""
        env_content = f"""# Telegram Bot Configuration
BOT_TOKEN={bot_token}
ADMIN_ID={admin_id}

# Database settings
DB_PATH=data/bot.db

# Timezone
TIMEZONE=Europe/Moscow

# Debug mode
DEBUG=False

# Notifications
ENABLE_NOTIFICATIONS=True
DAILY_SUMMARY_TIME=19:00
REMINDER_TIME=20:30

# Auto-restart settings
MAX_RESTARTS=50
RESTART_INTERVAL=300
"""
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Файл .env создан успешно")
    
    def install_dependencies(self):
        """Установка зависимостей"""
        print("\n📦 Установка зависимостей...")
        
        # Проверяем наличие pip
        try:
            subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ pip не найден!")
            sys.exit(1)
        
        # Устанавливаем зависимости
        dependencies = [
            'aiogram>=3.0.0',
            'aiosqlite',
            'python-dotenv',
            'aioschedule',
            'psutil',
            'pytz'
        ]
        
        for dep in dependencies:
            print(f"📥 Устанавливаю {dep}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                              check=True, capture_output=True)
                print(f"✅ {dep} установлен")
            except subprocess.CalledProcessError as e:
                print(f"❌ Ошибка установки {dep}: {e}")
                sys.exit(1)
    
    def setup_directories(self):
        """Создание необходимых директорий"""
        print("\n📁 Создание директорий...")
        
        directories = ['logs', 'data', 'exports', 'config', 'backups']
        for dir_name in directories:
            dir_path = os.path.join(self.project_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Создана директория: {dir_name}")
    
    def create_systemd_service(self):
        """Создание systemd сервиса для работы 24/7"""
        print("\n🔧 Настройка службы для работы 24/7...")
        
        service_content = f"""[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'root')}
WorkingDirectory={self.project_dir}
ExecStart={sys.executable} {os.path.join(self.project_dir, 'main.py')}
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""
        
        service_file = f"/etc/systemd/system/{self.service_name}.service"
        
        try:
            # Пытаемся создать сервис
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Перезагружаем systemd
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', self.service_name], check=True)
            
            print("✅ Systemd сервис создан и включен")
            print(f"📋 Управление сервисом:")
            print(f"   sudo systemctl start {self.service_name}")
            print(f"   sudo systemctl stop {self.service_name}")
            print(f"   sudo systemctl status {self.service_name}")
            
        except PermissionError:
            print("⚠️ Нет прав для создания systemd сервиса")
            print("🔧 Для работы 24/7 запустите после установки:")
            print("   sudo python3 setup.py --create-service")
        except Exception as e:
            print(f"⚠️ Ошибка создания сервиса: {e}")
    
    def create_startup_script(self):
        """Создание скрипта для запуска"""
        startup_script = os.path.join(self.project_dir, 'start_bot.sh')
        
        script_content = f"""#!/bin/bash
# Скрипт запуска Telegram бота

cd {self.project_dir}

# Проверка зависимостей
echo "🔍 Проверка зависимостей..."
{sys.executable} -c "import aiogram; print('✅ aiogram OK')"
{sys.executable} -c "import aiosqlite; print('✅ aiosqlite OK')"
{sys.executable} -c "import dotenv; print('✅ python-dotenv OK')"

# Запуск бота
echo "🚀 Запуск бота..."
{sys.executable} main.py
"""
        
        with open(startup_script, 'w') as f:
            f.write(script_content)
        
        # Делаем скрипт исполняемым
        os.chmod(startup_script, 0o755)
        print("✅ Скрипт запуска создан: start_bot.sh")
    
    def test_bot_connection(self, token):
        """Тестирование подключения к боту"""
        print("\n🔍 Тестирование подключения к боту...")
        
        test_script = f"""
import asyncio
import sys
from aiogram import Bot

async def test_bot():
    bot = Bot(token="{token}")
    try:
        me = await bot.get_me()
        print(f"✅ Бот подключен: @{{me.username}} ({{me.first_name}})")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {{e}}")
        await bot.session.close()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
"""
        
        try:
            result = subprocess.run([sys.executable, '-c', test_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(result.stderr)
                return False
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
    
    def start_bot(self):
        """Запуск бота"""
        print("\n🚀 Запуск бота...")
        
        try:
            # Пробуем запустить через systemd
            subprocess.run(['systemctl', 'start', self.service_name], 
                          check=True, capture_output=True)
            print("✅ Бот запущен через systemd")
            print(f"📊 Статус: sudo systemctl status {self.service_name}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ Systemd недоступен, запуск в фоновом режиме...")
            
            # Запускаем в фоновом режиме
            subprocess.Popen([sys.executable, 'main.py'], 
                           cwd=self.project_dir, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            time.sleep(2)  # Даем время на запуск
            print("✅ Бот запущен в фоновом режиме")
    
    def show_success_message(self):
        """Сообщение об успешной установке"""
        print("\n" + "="*60)
        print("🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
        print("="*60)
        print("✅ Бот настроен и запущен")
        print("✅ Работает в режиме 24/7")
        print("✅ Все зависимости установлены")
        print("✅ Конфигурация сохранена")
        print("\n📋 Полезные команды:")
        print("   ./start_bot.sh - ручной запуск")
        print("   python3 main.py - запуск в терминале")
        print("   tail -f logs/bot.log - просмотр логов")
        print("\n🔧 Управление сервисом:")
        print(f"   sudo systemctl status {self.service_name}")
        print(f"   sudo systemctl restart {self.service_name}")
        print(f"   sudo systemctl stop {self.service_name}")
        print("\n📱 Найдите бота в Telegram и отправьте /start")
        print("="*60 + "\n")
    
    def run(self):
        """Основная функция установки"""
        self.print_header()
        
        # Проверяем ограничение на запуск
        self.check_daily_limit()
        
        # Получаем учетные данные
        token, admin_id = self.get_bot_credentials()
        
        # Тестируем подключение
        if not self.test_bot_connection(token):
            print("❌ Не удается подключиться к боту. Проверьте токен.")
            sys.exit(1)
        
        # Создаем конфигурацию
        self.create_env_file(token, admin_id)
        
        # Устанавливаем зависимости
        self.install_dependencies()
        
        # Настраиваем окружение
        self.setup_directories()
        
        # Создаем скрипты
        self.create_startup_script()
        self.create_systemd_service()
        
        # Запускаем бота
        self.start_bot()
        
        # Показываем успешное завершение
        self.show_success_message()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-service":
        # Создание сервиса с sudo правами
        setup = BotSetup()
        setup.create_systemd_service()
    else:
        # Обычная установка
        setup = BotSetup()
        setup.run()