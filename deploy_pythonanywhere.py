#!/usr/bin/env python3
"""
🚀 Скрипт развертывания Telegram бота на PythonAnywhere
Автоматическая настройка окружения Python 3.10
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description=""):
    """Выполнение команды с выводом результата"""
    if description:
        print(f"🔧 {description}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Успешно: {description}")
            return True
        else:
            print(f"❌ Ошибка: {description}")
            print(f"Вывод: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Исключение при выполнении команды: {e}")
        return False

def setup_python310_environment():
    """Настройка окружения Python 3.10"""
    print("🐍 Настройка окружения Python 3.10...")
    
    # Создаем виртуальное окружение с Python 3.10
    if not run_command("python3.10 -m venv venv_bot_310", "Создание виртуального окружения Python 3.10"):
        print("❌ Не удалось создать виртуальное окружение Python 3.10")
        print("💡 Убедитесь, что Python 3.10 установлен на PythonAnywhere")
        return False
    
    # Активируем окружение и обновляем pip
    if not run_command("source venv_bot_310/bin/activate && pip install --upgrade pip", "Обновление pip"):
        return False
    
    # Устанавливаем зависимости
    if not run_command("source venv_bot_310/bin/activate && pip install -r requirements_python310.txt", "Установка зависимостей"):
        print("❌ Не удалось установить зависимости")
        return False
    
    return True

def setup_database():
    """Настройка базы данных"""
    print("🗄️ Настройка базы данных...")
    
    # Создаем папку для данных
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Запускаем создание базы данных
    if not run_command("source venv_bot_310/bin/activate && python create_database.py", "Создание базы данных"):
        print("❌ Не удалось создать базу данных")
        return False
    
    return True

def create_startup_script():
    """Создание скрипта запуска для PythonAnywhere"""
    print("📝 Создание скрипта запуска...")
    
    startup_script = """#!/bin/bash
# Скрипт запуска бота на PythonAnywhere

# Переходим в директорию проекта
cd /home/yourusername/mysite

# Активируем виртуальное окружение Python 3.10
source venv_bot_310/bin/activate

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Настройте файл .env перед запуском"
    exit 1
fi

# Запускаем бота
python run_bot.py
"""
    
    with open("start_pythonanywhere.sh", "w", encoding="utf-8") as f:
        f.write(startup_script)
    
    # Делаем скрипт исполняемым
    os.chmod("start_pythonanywhere.sh", 0o755)
    
    return True

def create_task_scheduler():
    """Создание планировщика задач для PythonAnywhere"""
    print("⏰ Создание планировщика задач...")
    
    task_script = """#!/usr/bin/env python3
# Планировщик задач для PythonAnywhere

import os
import sys
import subprocess
import time
from datetime import datetime

def restart_bot():
    \"\"\"Перезапуск бота\"\"\"
    print(f"{datetime.now()}: Перезапуск бота...")
    
    # Останавливаем старый процесс
    subprocess.run("pkill -f 'python.*run_bot.py'", shell=True)
    
    # Ждем немного
    time.sleep(5)
    
    # Запускаем новый процесс
    subprocess.Popen(["/bin/bash", "start_pythonanywhere.sh"])

def main():
    \"\"\"Основная функция планировщика\"\"\"
    print("🤖 Планировщик задач запущен")
    
    while True:
        try:
            # Перезапуск каждые 55 минут
            time.sleep(3300)  # 55 минут
            restart_bot()
            
        except KeyboardInterrupt:
            print("\\n🛑 Планировщик остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка планировщика: {e}")
            time.sleep(60)  # Ждем минуту перед повтором

if __name__ == "__main__":
    main()
"""
    
    with open("task_scheduler.py", "w", encoding="utf-8") as f:
        f.write(task_script)
    
    return True

def cleanup_unnecessary_files():
    """Удаление ненужных файлов"""
    print("🧹 Очистка ненужных файлов...")
    
    # Список файлов для удаления
    files_to_remove = [
        "FINAL_REPORT.md",
        "QUICK_START_1_TASK.md",
        "README_SETUP.md",
        "ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.md",
        "auto_restart.py",  # Заменен на task_scheduler.py
        "pythonanywhere_deploy.py",  # Заменен на deploy_pythonanywhere.py
        "setup_daily.py",  # Не нужен для PythonAnywhere
        "pa_daily_runner.py",  # Заменен на task_scheduler.py
    ]
    
    # Удаляем файлы
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Удален: {file_path}")
            except Exception as e:
                print(f"❌ Не удалось удалить {file_path}: {e}")
    
    # Удаляем старое виртуальное окружение
    if os.path.exists("venv_bot"):
        try:
            shutil.rmtree("venv_bot")
            print("🗑️ Удалено старое виртуальное окружение")
        except Exception as e:
            print(f"❌ Не удалось удалить старое окружение: {e}")
    
    return True

def create_instructions():
    """Создание инструкций для PythonAnywhere"""
    print("📋 Создание инструкций...")
    
    instructions = """# 🚀 Инструкции по развертыванию на PythonAnywhere

## 1. Подготовка окружения

1. Загрузите все файлы проекта в папку `/home/yourusername/mysite`
2. Замените `yourusername` на ваше имя пользователя в файлах:
   - `.env` (строка PYTHONPATH)
   - `start_pythonanywhere.sh`

## 2. Настройка конфигурации

Отредактируйте файл `.env`:
```
BOT_TOKEN=ваш_токен_бота_от_BotFather
ADMIN_IDS=ваш_telegram_id
```

## 3. Установка зависимостей

Запустите скрипт развертывания:
```bash
python3 deploy_pythonanywhere.py
```

## 4. Запуск бота

### Вариант 1: Ручной запуск
```bash
./start_pythonanywhere.sh
```

### Вариант 2: Автоматический запуск с перезапуском
```bash
python3 task_scheduler.py
```

## 5. Настройка задач в PythonAnywhere

1. Перейдите в раздел "Tasks" в панели управления PythonAnywhere
2. Создайте новую задачу:
   - Command: `python3 /home/yourusername/mysite/task_scheduler.py`
   - Schedule: `Always on`

## 6. Мониторинг

Бот будет автоматически:
- Перезапускаться каждый час
- Отправлять отчеты админу каждые 6 часов
- Создавать резервные копии базы данных

## 7. Логи и отладка

Логи находятся в папке `data/logs/`
Для отладки используйте: `python3 check_database.py`

## 8. Обновление

Для обновления бота:
1. Загрузите новые файлы
2. Перезапустите планировщик задач
"""
    
    with open("PYTHONANYWHERE_SETUP.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    
    return True

def main():
    """Основная функция развертывания"""
    print("🚀 Развертывание Telegram бота на PythonAnywhere")
    print("=" * 50)
    
    # Проверяем наличие Python 3.10
    if not shutil.which("python3.10"):
        print("❌ Python 3.10 не найден!")
        print("💡 Убедитесь, что вы используете PythonAnywhere с Python 3.10")
        return False
    
    steps = [
        (setup_python310_environment, "Настройка окружения Python 3.10"),
        (setup_database, "Настройка базы данных"),
        (create_startup_script, "Создание скрипта запуска"),
        (create_task_scheduler, "Создание планировщика задач"),
        (cleanup_unnecessary_files, "Очистка ненужных файлов"),
        (create_instructions, "Создание инструкций"),
    ]
    
    for step_func, step_name in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"❌ Ошибка на этапе: {step_name}")
            return False
    
    print("\n✅ Развертывание завершено успешно!")
    print("📋 Следуйте инструкциям в файле PYTHONANYWHERE_SETUP.md")
    print("🔧 Не забудьте настроить файл .env")
    
    return True

if __name__ == "__main__":
    main()