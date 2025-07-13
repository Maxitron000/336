# 🚀 Выгрузка на GitHub

## 📋 Пошаговая инструкция

### 1. Создание репозитория на GitHub

1. Перейдите на [GitHub.com](https://github.com)
2. Нажмите кнопку "New repository" (зеленый "+")
3. Заполните форму:
   - **Repository name**: `military-telegram-bot`
   - **Description**: `🛡️ Telegram Bot for military unit personnel management`
   - **Visibility**: Public или Private (по вашему выбору)
   - **Initialize**: НЕ ставьте галочки (у нас уже есть файлы)
4. Нажмите "Create repository"

### 2. Подключение к удаленному репозиторию

```bash
# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваше имя пользователя)
git remote add origin https://github.com/YOUR_USERNAME/military-telegram-bot.git

# Или если используете SSH:
git remote add origin git@github.com:YOUR_USERNAME/military-telegram-bot.git
```

### 3. Выгрузка кода

```bash
# Переименуйте основную ветку в main (современный стандарт)
git branch -M main

# Выгрузите код
git push -u origin main
```

### 4. Проверка

1. Перейдите в созданный репозиторий на GitHub
2. Убедитесь, что все файлы загружены
3. Проверьте README файлы

## 📁 Структура репозитория

```
military-telegram-bot/
├── 📄 README_MILITARY.md          # Документация для военной части
├── 📄 UPGRADE_ROLES.md            # Инструкция по обновлению ролей
├── 📄 GITHUB_DEPLOY.md            # Эта инструкция
├── 🐍 main.py                     # Главный файл бота
├── 🐍 database.py                 # База данных и логика
├── 🐍 handlers.py                 # Обработчики команд
├── 🐍 keyboards.py                # Клавиатуры
├── 🐍 admin.py                    # Админ-панель
├── 🐍 notifications.py            # Система уведомлений
├── 🐍 config.py                   # Конфигурация
├── 🐍 utils.py                    # Утилиты
├── 🐍 export.py                   # Экспорт данных
├── 🐍 migrate_roles.py            # Миграция ролей
├── 📁 data/                       # База данных
├── 📁 logs/                       # Логи
├── 📁 exports/                    # Экспортированные файлы
└── 📄 requirements.txt            # Зависимости
```

## 🔐 Настройка секретов

### GitHub Secrets (для CI/CD)

Если планируете использовать GitHub Actions, добавьте секреты:

1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте секреты:
   - `BOT_TOKEN` - токен вашего Telegram бота
   - `ADMIN_IDS` - ID администраторов через запятую
   - `DB_PATH` - путь к базе данных

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_IDS=123456,789012
DB_PATH=data/bot_database.db
LOG_LEVEL=INFO
```

## 🚀 GitHub Actions (опционально)

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy Military Bot

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Run migration
      run: |
        python migrate_roles.py
```

## 📊 GitHub Pages (опционально)

Для документации:

1. Перейдите в Settings → Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: / (root)
5. Нажмите Save

## 🔄 Обновления

### Для будущих обновлений:

```bash
# Внесите изменения в код
git add .
git commit -m "📝 Description of changes"
git push origin main
```

### Для других разработчиков:

```bash
# Клонирование
git clone https://github.com/YOUR_USERNAME/military-telegram-bot.git
cd military-telegram-bot

# Установка зависимостей
pip install -r requirements.txt

# Настройка
cp .env.example .env
# Отредактируйте .env

# Миграция
python migrate_roles.py

# Запуск
python main.py
```

## 🆘 Проблемы

### Ошибка "Permission denied"
```bash
# Настройте SSH ключи или используйте HTTPS
git remote set-url origin https://github.com/YOUR_USERNAME/military-telegram-bot.git
```

### Ошибка "Repository not found"
- Проверьте правильность URL репозитория
- Убедитесь, что репозиторий создан
- Проверьте права доступа

### Ошибка "Authentication failed"
```bash
# Настройте токен доступа
git config --global credential.helper store
# При следующем push введите токен как пароль
```

## 📞 Поддержка

- GitHub Issues: для багов и предложений
- GitHub Discussions: для обсуждений
- GitHub Wiki: для дополнительной документации

---

**Готово!** 🎉

Ваш военный Telegram бот теперь доступен на GitHub и готов к использованию.