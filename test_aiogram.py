#!/usr/bin/env python3
"""
Тестовый файл для проверки работы aiogram
"""

def test_imports():
    """Тестирование импорта основных модулей"""
    try:
        print("Тестируем импорт aiogram...")
        import aiogram
        print(f"✅ aiogram импортирован, версия: {aiogram.__version__}")
        
        from aiogram import Bot, Dispatcher
        print("✅ Bot и Dispatcher импортированы")
        
        from aiogram.types import Message
        print("✅ Message импортирован")
        
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_bot_creation():
    """Тестирование создания бота"""
    try:
        from aiogram import Bot
        
        # Создаем бота с фиктивным токеном для теста
        bot = Bot(token="123456789:FAKE_TOKEN_FOR_TESTING")
        print("✅ Бот создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return False

def main():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ AIOGRAM")
    print("=" * 50)
    
    # Тест импорта
    if test_imports():
        print("\n" + "=" * 30)
        print("ИМПОРТ: УСПЕШНО")
        
        # Тест создания бота
        if test_bot_creation():
            print("СОЗДАНИЕ БОТА: УСПЕШНО")
        else:
            print("СОЗДАНИЕ БОТА: НЕУДАЧНО")
    else:
        print("\nИМПОРТ: НЕУДАЧНО")
        print("Пожалуйста, проверьте установку aiogram")
    
    print("=" * 50)

if __name__ == "__main__":
    main()