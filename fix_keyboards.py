#!/usr/bin/env python3
"""
Временный скрипт для обновления keyboards.py под aiogram 3.x
"""

import re

def fix_keyboards():
    """Исправляет keyboards.py для aiogram 3.x"""
    
    # Читаем файл
    with open('keyboards.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем user_cb.new() на UserCallbackData()
    content = re.sub(
        r'user_cb\.new\("([^"]+)"\)',
        r'user_cb(action="\1")',
        content
    )
    
    # Заменяем admin_cb.new() на AdminCallbackData()
    content = re.sub(
        r'admin_cb\.new\("([^"]+)",\s*"([^"]*)"\)',
        r'admin_cb(action="\1", subaction="\2")',
        content
    )
    
    # Записываем обратно
    with open('keyboards.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ keyboards.py обновлен для aiogram 3.x")

if __name__ == "__main__":
    fix_keyboards()