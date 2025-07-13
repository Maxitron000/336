# 🚀 Развертывание бота на PythonAnywhere

## 📋 Пошаговая инструкция

### 1. Подготовка файлов

**Используйте оптимизированные файлы:**
- `main_pythonanywhere.py` - основной файл бота
- `requirements_pythonanywhere.txt` - облегченные зависимости
- `config_pythonanywhere.py` - конфигурация для PythonAnywhere

### 2. Настройка PythonAnywhere

#### 2.1 Создание аккаунта
1. Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com)
2. Выберите бесплатный план (Beginner Account)

#### 2.2 Загрузка файлов
```bash
# В консоли PythonAnywhere
cd ~
mkdir telegram_bot
cd telegram_bot

# Загрузите файлы через веб-интерфейс или git
git clone your_repository.git .
```

#### 2.3 Установка зависимостей
```bash
# Используйте pip3.10 для Python 3.10
pip3.10 install --user -r requirements_pythonanywhere.txt
```

### 3. Настройка переменных окружения

#### 3.1 Создайте файл `.env`
```bash
nano .env
```

#### 3.2 Добавьте переменные:
```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
```

### 4. Первоначальная настройка

#### 4.1 Запустите скрипт настройки:
```bash
python3.10 pythonanywhere_setup.py
```

#### 4.2 Создайте необходимые папки:
```bash
mkdir -p logs data
```

### 5. Настройка Always On Task

#### 5.1 Перейдите в раздел "Tasks" в панели PythonAnywhere
#### 5.2 Создайте новый Always On Task:
- **Command**: `python3.10 /home/yourusername/telegram_bot/main_pythonanywhere.py`
- **Working directory**: `/home/yourusername/telegram_bot`

### 6. Мониторинг и обслуживание

#### 6.1 Проверка логов:
```bash
tail -f logs/bot.log
```

#### 6.2 Проверка размера файлов:
```bash
du -sh * | sort -hr
```

#### 6.3 Очистка данных (выполнять раз в месяц):
```bash
# Очистка старых логов
find logs/ -name "*.log.*" -mtime +30 -delete

# Очистка старых записей в БД
sqlite3 data/personnel.db "DELETE FROM arrivals WHERE created_at < datetime('now', '-6 months');"
```

## 🔧 Оптимизации для 500MB лимита

### Экономия места:
- ❌ Убраны pandas, openpyxl, Pillow (экономия ~100MB)
- ✅ Использован базовый CSV экспорт
- ✅ Ротация логов (максимум 2MB)
- ✅ Автоочистка БД (6 месяцев)
- ✅ Убраны эмодзи из сообщений

### Мониторинг размера:
```bash
# Проверка общего размера
du -sh ~/telegram_bot

# Проверка размера БД
ls -lh data/personnel.db

# Проверка размера логов
ls -lh logs/
```

## 🚨 Важные ограничения PythonAnywhere Free

### Ограничения:
- **Дисковое пространство**: 512MB
- **CPU seconds**: 100 секунд в день
- **Internet access**: только из задач
- **Always On Tasks**: 1 задача

### Рекомендации:
1. **Мониторьте место** - регулярно проверяйте размер файлов
2. **Очищайте данные** - удаляйте старые записи и логи
3. **Минимизируйте логирование** - используйте уровень WARNING в продакшене
4. **Оптимизируйте БД** - используйте индексы и VACUUM

## 🛠️ Устранение неполадок

### Бот не запускается:
```bash
# Проверьте токен
grep BOT_TOKEN .env

# Проверьте права на файлы
chmod +x main_pythonanywhere.py

# Проверьте логи
cat logs/bot.log
```

### Превышение лимита места:
```bash
# Найдите большие файлы
find . -type f -size +10M -exec ls -lh {} \;

# Очистите временные файлы
rm -rf __pycache__/
rm -rf .git/
```

### Проблемы с зависимостями:
```bash
# Переустановите пакеты
pip3.10 install --user --force-reinstall -r requirements_pythonanywhere.txt
```

## 📊 Мониторинг производительности

### Создайте скрипт мониторинга:
```python
import os
import sqlite3

def check_system_health():
    # Проверка размера БД
    db_size = os.path.getsize('data/personnel.db') / 1024 / 1024  # MB
    
    # Проверка количества записей
    conn = sqlite3.connect('data/personnel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM arrivals")
    record_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"DB Size: {db_size:.2f} MB")
    print(f"Records: {record_count}")
    
    # Проверка общего размера
    total_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk('.')
                    for filename in filenames) / 1024 / 1024
    
    print(f"Total Size: {total_size:.2f} MB")
    print(f"Free Space: {500 - total_size:.2f} MB")

if __name__ == "__main__":
    check_system_health()
```

## 🎯 Заключение

Оптимизированная версия бота займет ~50-100MB вместо 200-300MB оригинала, оставляя достаточно места для данных и логов на PythonAnywhere Free.

**Ключевые преимущества:**
- ✅ Подходит для лимита 500MB
- ✅ Автоматическая очистка данных
- ✅ Облегченные зависимости
- ✅ Эффективное использование ресурсов
- ✅ Простота развертывания

**Время работы:** без перерывов благодаря Always On Task
**Стоимость:** бесплатно
**Поддержка:** все основные функции сохранены