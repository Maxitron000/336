#!/usr/bin/env python3
"""
🚀 Простой запуск Telegram бота
Автоматический перезапуск и мониторинг
"""

import subprocess
import sys
import os

def main():
    """Запуск бота с автоматическим мониторингом"""
    print("🤖 Запуск Telegram бота...")
            print("🔄 Автоперезапуск: раз в сутки")
        print("📊 Отчёты админу: каждые 12 часов")
    print("🛑 Для остановки нажмите Ctrl+C")
    print("-" * 40)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден!")
        print("📝 Запустите сначала: python setup.py")
        return
    
    try:
        # Запускаем основной скрипт
        subprocess.run([sys.executable, "run_bot.py"])
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        print("🔧 Попробуйте запустить: python setup.py")

if __name__ == "__main__":
    main()