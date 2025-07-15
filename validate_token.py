#!/usr/bin/env python3
"""
Простой скрипт для проверки действительности токена Telegram бота
Используйте этот скрипт для тестирования нового токена перед обновлением .env
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path

async def validate_token(token):
    """Проверяет действительность токена через getMe API"""
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('ok'):
                        bot_info = data['result']
                        print(f"✅ Токен действителен!")
                        print(f"   Имя бота: {bot_info.get('first_name', 'Не указано')}")
                        print(f"   Username: @{bot_info.get('username', 'Не указано')}")
                        print(f"   ID: {bot_info.get('id', 'Не указано')}")
                        print(f"   Может принимать сообщения: {'Да' if bot_info.get('can_receive_messages') else 'Нет'}")
                        return True
                    else:
                        print(f"❌ Ошибка API: {data.get('description', 'Неизвестная ошибка')}")
                        return False
                elif response.status == 401:
                    print("❌ Токен недействителен (401 Unauthorized)")
                    print("   Проверьте правильность токена и что бот не был удален")
                    return False
                else:
                    print(f"❌ HTTP ошибка: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def main():
    print("🔍 Проверка токена Telegram бота\n")
    
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"Тестируем токен: {token[:20]}...")
    else:
        # Запрашиваем токен интерактивно
        token = input("Введите токен бота: ").strip()
        if not token:
            print("❌ Токен не может быть пустым")
            return
    
    # Базовая проверка формата токена
    if ':' not in token or len(token) < 20:
        print("❌ Токен имеет неправильный формат")
        print("   Правильный формат: 1234567890:ABCDEF1234567890abcdef1234567890ABC")
        return
    
    # Проверяем токен
    is_valid = await validate_token(token)
    
    if is_valid:
        print("\n🎉 Токен прошел проверку! Теперь можете обновить .env файл:")
        print(f"   BOT_TOKEN={token}")
        print("\n💡 Команды для обновления:")
        print("   1. Откройте .env файл: nano .env")
        print("   2. Замените значение BOT_TOKEN")
        print("   3. Сохраните файл")
        print("   4. Запустите бота: python main.py")
    else:
        print("\n📋 Что делать дальше:")
        print("   1. Проверьте токен в @BotFather")
        print("   2. Убедитесь, что бот не был удален")
        print("   3. Создайте нового бота если нужно: /newbot")
        print("   4. Скопируйте токен полностью")

if __name__ == "__main__":
    asyncio.run(main())