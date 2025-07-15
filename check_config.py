#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации бота
Использование: python check_config.py
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from aiogram import Bot

async def check_config():
    """Проверка настроек конфигурации"""
    print("🔍 Проверка конфигурации Telegram бота...")
    print("=" * 50)
    
    # Проверяем файл .env
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📋 Создайте файл .env на основе .env.example")
        print("🔧 Настройте BOT_TOKEN и ADMIN_IDS")
        print("📖 Подробная инструкция в файле КАК_ЗАПУСТИТЬ_БОТА.md")
        return False
    
    print("✅ Файл .env найден")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем BOT_TOKEN
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN':
        print("❌ BOT_TOKEN не настроен!")
        print("🤖 Получите токен у @BotFather в Telegram")
        print("📝 Замените YOUR_BOT_TOKEN в файле .env на реальный токен")
        print("💡 Пример: BOT_TOKEN=1234567890:ABCDEF_ваш_токен_бота")
        return False
    
    print("✅ BOT_TOKEN найден")
    
    # Проверяем ADMIN_IDS
    admin_ids = os.getenv('ADMIN_IDS', '')
    if not admin_ids or admin_ids == 'YOUR_ADMIN_ID':
        print("⚠️  ADMIN_IDS не настроен")
        print("🆔 Получите свой ID у @userinfobot")
        print("📝 Замените YOUR_ADMIN_ID в файле .env на ваш ID")
        print("💡 Пример: ADMIN_IDS=123456789")
    else:
        print("✅ ADMIN_IDS найден")
    
    # Проверяем подключение к Telegram API
    print("\n🌐 Проверка подключения к Telegram API...")
    bot = None
    try:
        bot = Bot(token=bot_token)
        me = await bot.get_me()
        print(f"✅ Подключение успешно!")
        print(f"🤖 Бот: @{me.username} ({me.first_name})")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("🔧 Проверьте правильность BOT_TOKEN")
        print("🌐 Проверьте интернет-соединение")
        return False
    finally:
        if bot:
            await bot.session.close()

def main():
    """Основная функция"""
    try:
        result = asyncio.run(check_config())
        if result:
            print("\n🎉 Конфигурация корректна! Бот готов к запуску.")
            print("🚀 Запустите бота командой: python3 main.py")
        else:
            print("\n❌ Конфигурация содержит ошибки.")
            print("🔧 Исправьте ошибки и повторите проверку.")
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n🛑 Проверка прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())