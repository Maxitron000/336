# 🪖 Telegram-бот учёта личного состава

Полнофункциональный Telegram-бот для учета входа/выхода и управления личным составом в режиме 24/7.

## ✨ Основные функции

### Пользовательские функции:
- 📝 **Регистрация по ФИО** с валидацией формата "Петров П.П."
- 🏠 **Быстрая отметка прибытия** одной кнопкой
- 🚶‍♂️ **Отметка убытия** с выбором локации и комментарием
- 📜 **Личный журнал** последних действий
- 🔒 **Защита от двойных отметок** и случайных нажатий

### Админ-панель Enterprise-уровня:
- 👥 **Управление личным составом** (добавление/удаление бойцов)
- 👑 **Гибкая система прав** администраторов
- 📊 **Просмотр журналов** и статистики
- 💾 **Экспорт данных** в CSV, Excel, PDF
- 🚨 **"Опасная зона"** с двойным подтверждением
- ⚙️ **Настройки уведомлений**

### Автоматические уведомления:
- 🔔 **Мгновенные уведомления** админам о всех действиях
- 📈 **Ежедневная сводка** в 19:00
- 💬 **Вечерние напоминания** в 20:30 (50+ рандомных фраз)
- 🎯 **Персонализированные сообщения** с clickable TG ID

## 📁 Структура проекта

```
telegram-bot-personnel/
├── 📁 config/           # Конфигурационные файлы
│   └── notifications.json
├── 📁 data/            # Данные
│   └── locations.json  # Локации для убытия
├── 📁 exports/         # Экспортированные отчеты
├── 📁 logs/           # Логи работы бота
├── 📄 main.py         # Главный файл запуска
├── 📄 config.py       # Конфигурация
├── 📄 database.py     # Работа с базой данных
├── 📄 handlers.py     # Обработчики сообщений
├── 📄 keyboards.py    # Клавиатуры
├── 📄 admin.py        # Админ-функции
├── 📄 notifications.py # Система уведомлений
├── 📄 export.py       # Экспорт данных
├── 📄 utils.py        # Вспомогательные функции
└── 📄 requirements.txt # Зависимости
```

## 🚀 Быстрая установка

### 1. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone <repository-url>
cd telegram-bot-personnel

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 2. Настройка бота

1. **Создайте бота в BotFather:**
   - Отправьте `/newbot` боту @BotFather
   - Выберите имя и username для бота
   - Сохраните токен

2. **Настройте переменные окружения:**
   ```bash
   # Скопируйте файл примера
   cp .env.example .env
   
   # Отредактируйте .env файл
   nano .env
   ```
   
   **Обязательно заполните:**
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:AABBCCDDEEFFgghhiijjkkllmmnnoopp
   ADMIN_ID=123456789
   ```

3. **Узнайте свой Telegram ID:**
   - Напишите боту @userinfobot
   - Или воспользуйтесь @myidbot
   - Вставьте полученный ID в `ADMIN_ID`

### 3. Запуск

```bash
# Простой запуск
python main.py

# Или с логированием
python main.py > logs/bot.log 2>&1 &
```

## 🎯 Использование

### Для бойцов/сотрудников:

1. **Регистрация:** Отправьте `/start` и введите ФИО в формате "Иванов И.И."
2. **Прибытие:** Нажмите "🏠 Прибыл в расположение"
3. **Убытие:** Нажмите "🚶‍♂️ Убыл" → выберите локацию → добавьте комментарий (по желанию)
4. **История:** "📜 История действий" показывает последние 3 действия

### Для администраторов:

1. **Вход в админку:** Команда `/admin` или кнопка "👑 Админ-панель"
2. **Управление ЛС:** Просмотр, добавление, удаление бойцов
3. **Журналы:** Просмотр и экспорт логов за любую дату
4. **Права админов:** Гибкое управление разрешениями
5. **Экспорт:** CSV, Excel, PDF отчеты автоматически сохраняются в папки по датам

## 🔧 Настройка локаций

Локации настраиваются в файле `data/locations.json`:

```json
[
  {
    "id": 1,
    "emoji": "🏥",
    "name": "Поликлиника",
    "description": "Медицинское учреждение"
  }
]
```

**Текущие локации:**
- 🏥 Поликлиника
- ⚓ ОБРМП  
- 🌆 Калининград
- 🛒 Магазин
- 🍲 Столовая
- 🏨 Госпиталь
- ⚙️ Рабочка
- 🩺 ВВК
- 🏛️ МФЦ
- 🚓 Патруль

## 📱 Настройка уведомлений

В файле `config/notifications.json`:

- **bro_phrases** - фразы для вечерних напоминаний (20:30)
- **admin_notify_arrival** - шаблон уведомления о прибытии
- **admin_notify_departure** - шаблон уведомления об убытии

## 🔒 Система безопасности

- ✅ **Защита от двойных отметок** - нельзя убыть без прибытия
- ✅ **Debounce защита** - 3 секунды между действиями
- ✅ **Валидация ФИО** - строгий формат "Фамилия И.О."
- ✅ **Права админов** - детальная настройка доступов
- ✅ **Логирование** - все действия записываются
- ✅ **Двойное подтверждение** для критических операций

## 🏗️ Деплой на продакшн

### Вариант 1: VPS/VDS

```bash
# Установка как системный сервис
sudo nano /etc/systemd/system/personnel-bot.service
```

```ini
[Unit]
Description=Personnel Telegram Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/bot
Environment=PATH=/path/to/bot/venv/bin
ExecStart=/path/to/bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable personnel-bot
sudo systemctl start personnel-bot
```

### Вариант 2: PythonAnywhere

1. Загрузите файлы через Web interface
2. Установите зависимости в Bash console
3. Настройте Always-On Task в Dashboard
4. Command: `python3.8 /home/yourusername/personnel-bot/main.py`

### Вариант 3: Heroku

1. Создайте `Procfile`:
   ```
   bot: python main.py
   ```

2. Деплой:
   ```bash
   git add .
   git commit -m "Deploy bot"
   git push heroku main
   ```

## 📊 Мониторинг

### UptimeRobot настройка:
- **Monitor Type:** HTTP(s)
- **URL:** Ваш webhook URL (если настроен)
- **Monitoring Interval:** 5 minutes

### Логи:
```bash
# Просмотр логов в реальном времени
tail -f logs/bot.log

# Поиск ошибок
grep ERROR logs/bot.log

# Статистика по действиям
grep "Боец" logs/bot.log | wc -l
```

## 🛠️ API расширения

Бот готов к интеграции с внешними системами:

```python
# Пример webhook для внешней системы
@app.route('/api/personnel', methods=['GET'])
def get_personnel_status():
    users = get_all_users()
    return jsonify({
        'status': 'success',
        'data': users,
        'timestamp': get_current_time().isoformat()
    })
```

## 🔍 Troubleshooting

### Проблема: Бот не отвечает
```bash
# Проверьте токен
python -c "from telegram import Bot; print(Bot('YOUR_TOKEN').get_me())"

# Проверьте подключение к интернету
ping telegram.org
```

### Проблема: Ошибки в базе данных
```bash
# Пересоздание базы
rm personnel.db
python -c "from database import init_db; init_db()"
```

### Проблема: Не приходят уведомления
```bash
# Проверьте часовой пояс
python -c "from utils import get_current_time; print(get_current_time())"

# Проверьте файл notifications.json
python -c "import json; print(json.load(open('config/notifications.json')))"
```

## 🤝 Поддержка и развитие

### Планы развития:
- 📅 Интеграция с календарем смен
- 📍 GPS-метки для локаций
- 📱 Мобильное приложение
- 🔗 API для интеграции с 1С
- 📈 Аналитика и дашборды
- 🎯 Автоматические отчеты

### Известные ограничения:
- Максимум 10 локаций (можно расширить)
- SQLite не подходит для >1000 пользователей
- Telegram API лимиты: 30 сообщений/секунду

## 📄 Лицензия

MIT License - см. файл LICENSE

## 👨‍💻 Автор

Создано для военных подразделений и силовых структур с требованиями максимальной надежности и простоты использования.

---

**🚀 Готов к работе из коробки! Просто настройте токен и запускайте!**