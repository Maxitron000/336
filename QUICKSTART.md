# 🚀 Быстрый старт

## Установка за 5 минут

1. **Клонируйте проект:**
   ```bash
   git clone <repository-url>
   cd telegram-bot-personnel
   ```

2. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройте бота:**
   ```bash
   cp .env.example .env
   nano .env  # Укажите токен и админ ID
   ```

4. **Запустите:**
   ```bash
   ./start_bot.sh
   ```

## Получение токена

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Придумайте имя и username
4. Скопируйте токен в `.env`

## Получение Admin ID

1. Найдите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте `/start`
3. Скопируйте ID в `.env`

## Проверка работы

- Отправьте `/start` вашему боту
- Введите ФИО в формате "Иванов И.И."
- Нажмите "🏠 Прибыл в расположение"

✅ **Готово! Бот работает!**

---

📖 Полная документация в [README.md](README.md)