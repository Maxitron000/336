# Руководство по решению проблемы с базой данных

## Проблема
При запуске бота на PythonAnywhere появляется ошибка "база данных не создана"

## Причины проблемы

1. **Права доступа** - нет прав на создание файлов в директории `data/`
2. **Пути файлов** - проблемы с относительными путями на PythonAnywhere
3. **Инициализация** - база данных не инициализируется при запуске
4. **Переменные окружения** - не настроен путь к БД

## Диагностика

### Шаг 1: Запустите диагностический скрипт
```bash
python3 check_database.py
```

Этот скрипт проверит:
- ✅ Существование директорий
- ✅ Права доступа
- ✅ Переменные окружения  
- ✅ Текущие пути
- ✅ Процесс создания БД

### Шаг 2: Анализ результатов
Обратите внимание на:
- Рабочую директорию
- Права записи в `data/`
- Абсолютные пути к файлам
- Ошибки при создании БД

## Решение проблемы

### Вариант 1: Принудительное создание БД (быстрое решение)
```bash
python3 create_database.py
```

Этот скрипт:
- 🔧 Создаст все нужные директории
- 🗄️ Инициализирует базу данных
- ✅ Проверит корректность создания
- 📊 Покажет статистику таблиц

### Вариант 2: Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
BOT_TOKEN=ваш_токен_бота
DB_PATH=/home/ваш_пользователь/mysite/data/bot_database.db
ADMIN_IDS=ваш_telegram_id
```

### Вариант 3: Исправление путей в коде
Если у вас есть доступ к редактированию файлов:

1. **В `database.py` (строка 17)** изменить:
```python
# Было:
def __init__(self, db_path: str = 'data/bot_database.db'):

# Стало:
def __init__(self, db_path: str = None):
    if db_path is None:
        from config import Config
        config = Config()
        db_path = config.DB_PATH
    self.db_path = db_path
```

2. **В `config.py` добавить абсолютный путь**:
```python
# Добавить после строки 18:
if not os.path.isabs(self.DB_PATH):
    self.DB_PATH = os.path.abspath(self.DB_PATH)
```

### Вариант 4: Ручное создание БД (крайний случай)
```bash
# Создать директории
mkdir -p data logs exports

# Создать пустую БД
touch data/bot_database.db

# Установить права
chmod 755 data/
chmod 644 data/bot_database.db
```

## Проверка решения

После любого из вариантов выполните:

1. **Проверка файла БД**:
```bash
ls -la data/bot_database.db
```

2. **Запуск диагностики**:
```bash
python3 check_database.py
```

3. **Тестовый запуск бота**:
```bash
python3 main.py
```

## Типичные ошибки на PythonAnywhere

### 1. Проблема с путями
**Ошибка**: `FileNotFoundError: [Errno 2] No such file or directory: 'data/bot_database.db'`

**Решение**: Использовать абсолютные пути:
```python
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'bot_database.db')
```

### 2. Права доступа
**Ошибка**: `PermissionError: [Errno 13] Permission denied: 'data'`

**Решение**: 
```bash
chmod 755 data/
chmod 644 data/bot_database.db
```

### 3. Рабочая директория
**Ошибка**: БД создается не в том месте

**Решение**: Перейти в директорию проекта:
```bash
cd /home/ваш_пользователь/mysite/
python3 create_database.py
```

## Мониторинг БД

### Проверка статуса БД
```python
# В консоли Python
import sqlite3
conn = sqlite3.connect('data/bot_database.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
conn.close()
```

### Размер БД
```bash
du -h data/bot_database.db
```

### Логи БД
Проверьте логи в `logs/bot.log` на наличие ошибок БД.

## Автоматизация

Добавьте в начало `main.py` проверку БД:
```python
async def ensure_database():
    """Убедиться что БД существует"""
    if not os.path.exists('data/bot_database.db'):
        print("⚠️ БД не найдена, создаем...")
        from database import Database
        db = Database()
        await db.init()
        await db.close()
        print("✅ БД создана")

# В on_startup добавить:
await ensure_database()
```

## Поддержка

Если проблема не решается:

1. Запустите полную диагностику
2. Сохраните вывод команд
3. Проверьте права доступа к файлам
4. Убедитесь что все зависимости установлены

## Файлы для диагностики
- `check_database.py` - диагностика проблем
- `create_database.py` - принудительное создание БД
- `logs/bot.log` - логи работы бота