from telegram_bot.handlers.account_handlers import get_account_handlers
from telegram_bot.handlers.publish_handlers import get_publish_handlers
from telegram_bot.handlers.task_handlers import get_task_handlers
from telegram_bot.handlers.group_handlers import get_group_handlers
from telegram_bot.handlers.analytics_handlers import get_analytics_handlers

def get_all_handlers():
    """Возвращает все обработчики"""
    handlers = []
    handlers.extend(get_account_handlers())
    # Proxy handlers находятся в основном handlers.py
    handlers.extend(get_publish_handlers())
    handlers.extend(get_task_handlers())
    handlers.extend(get_group_handlers())
    handlers.extend(get_analytics_handlers())
    return handlers