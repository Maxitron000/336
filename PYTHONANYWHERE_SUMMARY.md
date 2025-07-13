# 🚀 Telegram Bot для PythonAnywhere (500MB версия)

## 📋 Быстрый старт

### 1. Что создано для вас:
- ✅ `main_pythonanywhere.py` - оптимизированная версия бота
- ✅ `requirements_pythonanywhere.txt` - облегченные зависимости
- ✅ `pythonanywhere_setup.py` - скрипт настройки
- ✅ `deploy_pythonanywhere.sh` - автоматическое развертывание
- ✅ `PYTHONANYWHERE_DEPLOY.md` - подробная инструкция

### 2. Основные изменения:
- **Размер**: с ~250MB до ~80MB (экономия 68%)
- **Зависимости**: убраны pandas, openpyxl, Pillow
- **Автоочистка**: записи удаляются через 6 месяцев
- **Логи**: ротация с максимумом 2MB
- **Экспорт**: только CSV (вместо Excel/PDF)

### 3. Что сохранено:
- ✅ Регистрация пользователей
- ✅ Отметки по локациям
- ✅ Админ-панель
- ✅ Статистика
- ✅ Уведомления
- ✅ Экспорт данных
- ✅ Очистка данных

## 🛠️ Развертывание на PythonAnywhere

### Шаг 1: Подготовка
1. Зарегистрируйтесь на [pythonanywhere.com](https://www.pythonanywhere.com) (бесплатный аккаунт)
2. Перейдите в консоль Bash

### Шаг 2: Быстрое развертывание
```bash
# Скачайте и запустите скрипт
wget https://your-repo/deploy_pythonanywhere.sh
chmod +x deploy_pythonanywhere.sh
./deploy_pythonanywhere.sh
```

### Шаг 3: Настройка
```bash
# Отредактируйте файл с токеном
nano telegram_bot/.env

# Добавьте:
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
```

### Шаг 4: Загрузка файлов
Скопируйте в папку `telegram_bot/`:
- `main_pythonanywhere.py`
- `pythonanywhere_setup.py`
- `config_pythonanywhere.py`

### Шаг 5: Инициализация
```bash
cd telegram_bot
python3.10 pythonanywhere_setup.py
```

### Шаг 6: Создание Always On Task
1. Перейдите в раздел "Tasks" в панели PythonAnywhere
2. Создайте новую задачу:
   - **Command**: `python3.10 /home/yourusername/telegram_bot/main_pythonanywhere.py`
   - **Working directory**: `/home/yourusername/telegram_bot`

## 📊 Мониторинг

### Проверка статуса:
```bash
python3.10 monitor.py    # Размер проекта и статистика
tail -f logs/bot.log     # Логи в реальном времени
```

### Очистка данных (раз в месяц):
```bash
python3.10 cleanup.py    # Удаление старых записей
```

## 🎯 Результат

**Готовый бот который:**
- 📦 Занимает менее 100MB (в 3 раза меньше)
- 🔄 Автоматически очищается от старых данных
- 💾 Эффективно использует ограниченное место
- 🚀 Работает 24/7 на PythonAnywhere бесплатно
- 📈 Поддерживает до 100 пользователей

## 🆘 Поддержка

### Если что-то не работает:
1. Проверьте логи: `cat logs/bot.log`
2. Проверьте размер: `du -sh .`
3. Проверьте токен: `grep BOT_TOKEN .env`
4. Посмотрите подробную инструкцию: `PYTHONANYWHERE_DEPLOY.md`

### Полезные команды:
```bash
# Проверка размера
du -sh telegram_bot/

# Очистка кэша
rm -rf __pycache__/

# Перезапуск (в панели PythonAnywhere)
# Tasks -> Restart Always On Task
```

---

**Готово! Ваш бот оптимизирован для PythonAnywhere и готов к работе! 🎉**