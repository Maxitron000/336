# 🤖 Telegram Bot для учета личного состава

Telegram бот для отслеживания прибытия/убытия персонала с админ-панелью и системой уведомлений.

## 🚀 Возможности

- ✅ Отметка прибытия/убытия с указанием локации
- � Админ-панель с расширенными возможностями
- 📊 Статистика и отчеты
- 🔔 Система уведомлений и напоминаний
- 📈 Экспорт данных в Excel/PDF
- 🗄️ База данных SQLite
- ⏰ Автоматические сводки

## � Требования

- Python 3.8+
- aiogram 2.25.1
- SQLite3
- Токен бота от @BotFather

## �️ Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/ваш_username/ваш_репозиторий.git
cd ваш_репозиторий
```

### 2. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации
Создайте файл `.env`:
```env
BOT_TOKEN=ваш_токен_бота
ADMIN_IDS=ваш_telegram_id
TIMEZONE=Europe/Kaliningrad
DB_PATH=data/bot_database.db
NOTIFICATIONS_ENABLED=true
DAILY_SUMMARY_TIME=19:00
REMINDERS_TIME=20:30
LOG_LEVEL=INFO
LOG_FILE=bot.log
EXPORT_PATH=exports/
```

### 5. Создание папок
```bash
mkdir -p data exports logs config
```

### 6. Инициализация базы данных
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('data/bot_database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE NOT NULL,
        name TEXT NOT NULL,
        location TEXT,
        is_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        location TEXT,
        status TEXT DEFAULT 'present',
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, date)
    )
''')
conn.commit()
conn.close()
print('✅ База данных создана!')
"
```

### 7. Запуск бота
```bash
python3 main.py
```

## 📁 Структура проекта

```
├── main.py              # Главный файл бота
├── config.py            # Конфигурация
├── database.py          # Работа с базой данных
├── handlers.py          # Обработчики сообщений
├── keyboards.py         # Клавиатуры
├── admin.py             # Админ-панель
├── notifications.py     # Система уведомлений
├── export.py            # Экспорт данных
├── utils.py             # Утилиты
├── run_bot.py           # Скрипт запуска для серверов
├── start_bot.sh         # Bash скрипт запуска
├── requirements.txt     # Зависимости
├── .env                 # Переменные окружения
├── .gitignore           # Игнорируемые файлы
├── data/                # База данных
├── logs/                # Логи
├── exports/             # Экспортированные файлы
└── config/              # Конфигурационные файлы
```

## 🔧 Команды бота

### Для всех пользователей:
- `/start` - Главное меню
- `/help` - Справка
- `/status` - Статус системы

### Для администраторов:
- `/admin` - Админ-панель
- `/export` - Экспорт данных
- `/backup` - Резервная копия

## 👑 Админ-панель

### Возможности:
- 👥 Управление пользователями
- 📊 Просмотр статистики
- 📤 Экспорт данных
- 🗑️ Очистка старых записей
- ⚙️ Настройки уведомлений
- 🔧 Системные настройки

### Права администратора:
- Просмотр всех пользователей
- Управление пользователями
- Экспорт данных
- Очистка данных
- Просмотр статистики
- Управление локациями
- Управление админами
- Системные настройки
- Настройки уведомлений

## 📊 Система уведомлений

### Автоматические уведомления:
- 📊 Ежедневная сводка в 19:00
- 🔔 Напоминания не отметившимся в 20:30
- 🏥 Проверка здоровья бота
- 📈 Отчеты о производительности

### Типы уведомлений:
- Напоминания о отметке
- Ежедневные сводки
- Системные уведомления
- Ошибки и предупреждения

## 🗄️ База данных

### Таблицы:
- `users` - Пользователи
- `attendance` - Отметки прибытия/убытия
- `events` - События и логи

### Оптимизация:
- Индексы для быстрого поиска
- Автоочистка старых записей
- Сжатие данных

## 📤 Экспорт данных

### Поддерживаемые форматы:
- 📊 Excel (.xlsx)
- 📄 PDF отчеты
- 📋 CSV файлы

### Типы отчетов:
- Отчет по пользователям
- Статистика посещаемости
- Журнал событий
- Админские логи

## 🚀 Развертывание на сервере

### PythonAnywhere (рекомендуется):
Следуйте инструкции в [PYTHONANYWHERE_SETUP.md](PYTHONANYWHERE_SETUP.md)

### Другие серверы:
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск через systemd
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Или через screen
screen -S bot
python3 main.py
```

## 🔍 Мониторинг

### Проверка статуса:
```bash
python3 monitor.py
```

### Просмотр логов:
```bash
tail -f logs/bot.log
```

### Проверка базы данных:
```bash
sqlite3 data/bot_database.db "SELECT COUNT(*) FROM users;"
```

## 🛠️ Разработка

### Структура кода:
- Модульная архитектура
- Асинхронное программирование
- Обработка ошибок
- Логирование

### Добавление новых функций:
1. Создайте обработчик в `handlers.py`
2. Добавьте клавиатуру в `keyboards.py`
3. Обновите админ-панель в `admin.py`
4. Добавьте логику в соответствующий модуль

## � Решение проблем

### Бот не запускается:
1. Проверьте токен в `.env`
2. Убедитесь, что все зависимости установлены
3. Проверьте логи в `logs/bot.log`

### Ошибки базы данных:
1. Проверьте права доступа к папке `data/`
2. Убедитесь, что SQLite установлен
3. Проверьте структуру таблиц

### Проблемы с уведомлениями:
1. Проверьте настройки в `config/notifications.json`
2. Убедитесь, что время указано в правильном формате
3. Проверьте права администраторов

## � Лицензия

MIT License

## 🤝 Поддержка

Если у вас есть вопросы или проблемы:
1. Проверьте раздел "Решение проблем"
2. Создайте Issue в репозитории
3. Обратитесь к документации

## 🎯 Планы развития

- [ ] Веб-интерфейс для администрирования
- [ ] Интеграция с внешними системами
- [ ] Расширенная аналитика
- [ ] Мобильное приложение
- [ ] API для интеграции

---

**Бот готов к работе! 🚀**