#!/bin/bash

# Скрипт для запуска Telegram бота

echo "🤖 Запуск Instagram Telegram Bot..."

# Проверяем, не запущен ли уже бот
if pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Бот уже запущен. Останавливаем старый процесс..."
    pkill -f "python.*main.py"
    sleep 2
fi

# Запускаем бота
echo "🚀 Запуск бота..."
./bot_env_final/bin/python main.py

echo "✅ Бот остановлен" 