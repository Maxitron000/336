#!/bin/bash

# Скрипт быстрого развертывания на PythonAnywhere
# Запускать в домашней папке PythonAnywhere

echo "🚀 Развертывание бота на PythonAnywhere..."

# Создаем структуру папок
mkdir -p telegram_bot/logs
mkdir -p telegram_bot/data
cd telegram_bot

# Создаем файл .env (нужно будет заполнить токен)
if [ ! -f .env ]; then
    cat > .env << 'EOF'
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
EOF
    echo "⚠️  Не забудьте заполнить .env файл!"
fi

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3.10 install --user python-telegram-bot==20.7 python-dotenv==1.0.0 pytz==2023.3 schedule==1.2.0

# Создаем .gitignore
cat > .gitignore << 'EOF'
.env
logs/
data/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env
venv
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
EOF

# Создаем файл мониторинга
cat > monitor.py << 'EOF'
#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime

def check_system_health():
    print(f"📊 Мониторинг системы - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Проверка размера БД
    if os.path.exists('data/personnel.db'):
        db_size = os.path.getsize('data/personnel.db') / 1024 / 1024
        print(f"💾 Размер БД: {db_size:.2f} MB")
        
        # Проверка количества записей
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM arrivals")
        record_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"📝 Записей: {record_count}")
        print(f"👥 Пользователей: {user_count}")
    else:
        print("💾 БД не найдена")
    
    # Проверка размера логов
    if os.path.exists('logs/bot.log'):
        log_size = os.path.getsize('logs/bot.log') / 1024 / 1024
        print(f"📋 Размер лога: {log_size:.2f} MB")
    else:
        print("📋 Лог-файл не найден")
    
    # Проверка общего размера
    total_size = 0
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    
    total_size_mb = total_size / 1024 / 1024
    free_space = 500 - total_size_mb
    
    print(f"📊 Общий размер: {total_size_mb:.2f} MB")
    print(f"💽 Свободно: {free_space:.2f} MB")
    
    # Предупреждения
    if total_size_mb > 400:
        print("⚠️  ВНИМАНИЕ: Близко к лимиту!")
    elif total_size_mb > 300:
        print("⚡ Рекомендуется очистка данных")
    else:
        print("✅ Размер в норме")

if __name__ == "__main__":
    check_system_health()
EOF

chmod +x monitor.py

# Создаем скрипт очистки
cat > cleanup.py << 'EOF'
#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime, timedelta

def cleanup_old_data():
    print("🧹 Очистка старых данных...")
    
    # Очистка БД
    if os.path.exists('data/personnel.db'):
        conn = sqlite3.connect('data/personnel.db')
        cursor = conn.cursor()
        
        # Удаляем записи старше 6 месяцев
        cursor.execute("DELETE FROM arrivals WHERE created_at < datetime('now', '-6 months')")
        deleted = cursor.rowcount
        print(f"🗑️  Удалено записей из БД: {deleted}")
        
        # Оптимизация БД
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        print("🔧 БД оптимизирована")
    
    # Очистка старых логов
    if os.path.exists('logs/bot.log'):
        # Если лог больше 5MB, обрезаем
        if os.path.getsize('logs/bot.log') > 5 * 1024 * 1024:
            with open('logs/bot.log', 'r') as f:
                lines = f.readlines()
            
            # Оставляем только последние 1000 строк
            with open('logs/bot.log', 'w') as f:
                f.writelines(lines[-1000:])
            
            print("📋 Лог-файл обрезан")
    
    # Удаляем временные файлы
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.tmp') or file.startswith('temp_'):
                os.remove(os.path.join(root, file))
                print(f"🗑️  Удален временный файл: {file}")
    
    print("✅ Очистка завершена")

if __name__ == "__main__":
    cleanup_old_data()
EOF

chmod +x cleanup.py

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Отредактируйте файл .env и добавьте токен бота"
echo "2. Скопируйте файлы: main_pythonanywhere.py, pythonanywhere_setup.py"
echo "3. Запустите: python3.10 pythonanywhere_setup.py"
echo "4. Создайте Always On Task в панели PythonAnywhere"
echo "5. Команда для задачи: python3.10 /home/yourusername/telegram_bot/main_pythonanywhere.py"
echo ""
echo "🛠️  Полезные команды:"
echo "python3.10 monitor.py     # Мониторинг системы"
echo "python3.10 cleanup.py     # Очистка данных"
echo "tail -f logs/bot.log      # Просмотр логов"
echo ""
echo "📖 Подробности в файле: PYTHONANYWHERE_DEPLOY.md"