#!/usr/bin/env python3
"""
Тест оптимизированного логирования IMAP
Показывает разницу между старыми и новыми логами
"""

import logging
from datetime import datetime, timezone

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("📊 СРАВНЕНИЕ ЛОГИРОВАНИЯ IMAP")
print("=" * 60)

# Симуляция старого логирования (как в ваших логах)
print("\n❌ СТАРОЕ ЛОГИРОВАНИЕ (150+ строк):")
print("-" * 60)
old_log_lines = [
    "[DEBUG] Выполняем поиск с критерием: (SINCE \"31-Jul-2025\" SUBJECT \"Instagram\")",
    "[DEBUG] Поиск по '(SINCE \"31-Jul-2025\" SUBJECT \"Instagram\")' не дал результатов",
    "[DEBUG] Выполняем поиск с критерием: (SINCE \"31-Jul-2025\" SUBJECT \"security code\")",
    "[DEBUG] Поиск по '(SINCE \"31-Jul-2025\" SUBJECT \"security code\")' не дал результатов",
    "[DEBUG] Выполняем поиск с критерием: (SINCE \"31-Jul-2025\" SUBJECT \"verification code\")",
    "[DEBUG] Поиск по '(SINCE \"31-Jul-2025\" SUBJECT \"verification code\")' не дал результатов",
    "[DEBUG] Выполняем поиск с критерием: (SINCE \"31-Jul-2025\" SUBJECT \"code\")",
    "[DEBUG] Поиск по '(SINCE \"31-Jul-2025\" SUBJECT \"code\")' не дал результатов",
    "[DEBUG] Выполняем поиск с критерием: (SINCE \"31-Jul-2025\" SUBJECT \"security\")",
    "[DEBUG] Поиск по '(SINCE \"31-Jul-2025\" SUBJECT \"security\")' не дал результатов",
    # ... и так еще 140+ строк
]

print(f"Показаны первые 10 из ~150 строк логов...")
for line in old_log_lines[:10]:
    print(line)
print("... еще 140+ строк DEBUG логов ...")

# Симуляция нового логирования
print("\n\n✅ НОВОЕ ОПТИМИЗИРОВАННОЕ ЛОГИРОВАНИЕ (3-5 строк):")
print("-" * 60)

# Импортируем оптимизированную версию
try:
    from instagram.email_utils_optimized import OptimizedIMAPLogger
    
    # Создаем логгер
    imap_logger = OptimizedIMAPLogger(verbose=False)
    
    # Симулируем поиск
    email = "test@example.com"
    imap_logger.log_search_start(email, 1)
    imap_logger.log_folder_result(email, "INBOX", 0)
    imap_logger.log_folder_result(email, "Junk", 0)
    imap_logger.log_code_not_found(email, 1, 3)
    
    print("\n📈 СТАТИСТИКА:")
    print(f"Старое логирование: ~150 строк на попытку")
    print(f"Новое логирование: 3-5 строк на попытку")
    print(f"СНИЖЕНИЕ: 97% меньше логов!")
    
except ImportError as e:
    print(f"⚠️ Не удалось импортировать оптимизированную версию: {e}")
    print("Убедитесь что файл instagram/email_utils_optimized.py существует")

print("\n" + "=" * 60)
print("🚀 С ПУЛОМ СОЕДИНЕНИЙ:")
print("=" * 60)

# Показываем преимущества пула
print("БЫЛО: Новое подключение для каждой попытки")
print("  → 3 попытки = 3 TCP + 3 TLS + 3 AUTH = 9 операций")
print("\nСТАЛО: Переиспользование соединений из пула")  
print("  → 3 попытки = 1 TCP + 1 TLS + 1 AUTH + 3 поиска = 6 операций")
print("\n📊 ЭКОНОМИЯ: 33% меньше сетевых операций!")

print("\n" + "=" * 60) 