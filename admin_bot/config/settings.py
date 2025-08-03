"""
Основные настройки админ бота
"""

import os
from typing import List, Dict, Any

# Токен админ бота (отдельный от основного бота)
ADMIN_BOT_TOKEN = os.getenv(
    'ADMIN_BOT_TOKEN', 
    None  # По умолчанию None - нужно установить отдельный токен
)

# Если не установлен отдельный токен, используем основной (для разработки)
if not ADMIN_BOT_TOKEN:
    ADMIN_BOT_TOKEN = os.getenv(
        'TELEGRAM_BOT_TOKEN',
        '7775814314:AAE27Z2NvgUNl5zR1tnACrTPRu5hmkPjlBc'  # Основной токен как fallback
    )
    print("⚠️ ВНИМАНИЕ: Используется основной токен бота для админ панели!")
    print("🔧 Для продакшена создайте отдельного бота через @BotFather")

# Настройки пагинации
USERS_PER_PAGE = 10
ACCOUNTS_PER_PAGE = 15
LOGS_PER_PAGE = 20

# Настройки экспорта
EXPORT_FORMATS = ['csv', 'txt', 'json']
MAX_EXPORT_RECORDS = 10000

# Настройки статистики
STATS_REFRESH_INTERVAL = 300  # 5 минут
SYSTEM_MONITOR_INTERVAL = 60  # 1 минута

# Настройки уведомлений
ALERT_LEVELS = {
    'info': '🟢',
    'warning': '🟡', 
    'error': '🔴',
    'critical': '🚨'
}

# Настройки системы
MAX_MESSAGE_LENGTH = 4000  # Максимальная длина сообщения в Telegram
TIMEOUT_SECONDS = 30       # Таймаут для операций

# Команды бота
BOT_COMMANDS = [
    {'command': 'start', 'description': '🏠 Главное меню'},
    {'command': 'stats', 'description': '📊 Статистика системы'},
    {'command': 'users', 'description': '👥 Управление пользователями'},
    {'command': 'alerts', 'description': '⚠️ Системные алерты'},
    {'command': 'export', 'description': '📄 Экспорт данных'},
    {'command': 'help', 'description': '❓ Помощь'}
]

# Настройки авторизации
AUTH_TIMEOUT_MINUTES = 60  # Время жизни сессии
MAX_LOGIN_ATTEMPTS = 3     # Максимальное количество попыток входа

# Сообщения
MESSAGES = {
    'welcome': """
🚀 <b>Instagram Bot Admin Panel</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Добро пожаловать в панель администратора!

Выберите действие из меню ниже:
""",
    
    'unauthorized': """
🔒 <b>Доступ запрещен</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
У вас нет прав доступа к админ панели.

Обратитесь к супер-администратору для получения доступа.
""",
    
    'loading': '⏳ Загрузка данных...',
    'error': '❌ Произошла ошибка: {error}',
    'success': '✅ Операция выполнена успешно!',
    
    'no_admin_token': """
⚠️ <b>Не настроен токен админ бота</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Для работы админ панели нужен отдельный токен бота.

<b>Как создать:</b>
1. Идите к @BotFather
2. Отправьте /newbot
3. Создайте бота (например: Instagram Admin Panel)
4. Скопируйте токен
5. Установите: export ADMIN_BOT_TOKEN="ваш_токен"
"""
}

# Настройки базы данных (используем существующую)
DATABASE_PATH = 'data/database.sqlite'

# Проверка конфигурации
def validate_config():
    """Проверка корректности конфигурации"""
    issues = []
    
    if not ADMIN_BOT_TOKEN:
        issues.append("ADMIN_BOT_TOKEN не установлен")
    
    if ADMIN_BOT_TOKEN and len(ADMIN_BOT_TOKEN) < 20:
        issues.append("ADMIN_BOT_TOKEN слишком короткий")
    
    return issues

# Информация о конфигурации
def get_config_info():
    """Получить информацию о текущей конфигурации"""
    return {
        'admin_token_set': bool(os.getenv('ADMIN_BOT_TOKEN')),
        'using_fallback_token': not bool(os.getenv('ADMIN_BOT_TOKEN')),
        'database_path': DATABASE_PATH,
        'stats_interval': STATS_REFRESH_INTERVAL,
        'users_per_page': USERS_PER_PAGE
    } 