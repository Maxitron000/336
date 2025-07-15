#!/usr/bin/env python3
"""
Планировщик задач для PythonAnywhere
Перезапуск бота каждые 55 минут для стабильной работы 24/7
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def restart_bot():
    """Перезапуск бота"""
    print(f"{datetime.now()}: Перезапуск бота...")
    
    # Останавливаем старый процесс
    subprocess.run("pkill -f 'python.*main.py'", shell=True)
    
    # Ждем немного
    time.sleep(5)
    
    # Запускаем новый процесс
    subprocess.Popen(["/bin/bash", "2_start.sh"])

def main():
    """Основная функция планировщика"""
    print("🤖 Планировщик задач запущен")
    print("⏰ Интервал перезапуска: 55 минут")
    
    while True:
        try:
            # Перезапуск каждые 55 минут
            time.sleep(3300)  # 55 минут = 3300 секунд
            restart_bot()
            
        except KeyboardInterrupt:
            print("\n🛑 Планировщик остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка планировщика: {e}")
            time.sleep(60)  # Ждем минуту перед повтором

if __name__ == "__main__":
    main()