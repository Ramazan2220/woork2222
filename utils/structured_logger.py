# -*- coding: utf-8 -*-
"""
Structured Logging с Sampling - Оптимизированная система логирования

Обеспечивает:
- Структурированные логи в JSON формате для лучшего анализа
- Умный сэмплинг для снижения объема логов
- Различные стратегии сэмплинга (частота, время, хэш)
- Метрики производительности логирования
- Автоматическое управление уровнями логов
"""

import json
import time
import logging
import hashlib
import threading
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class SamplingStrategy(Enum):
    """Стратегии сэмплинга логов"""
    FREQUENCY = "frequency"      # Каждый N-й лог
    TIME_WINDOW = "time_window"  # Ограничение по времени
    HASH_BASED = "hash_based"    # На основе хэша сообщения
    ADAPTIVE = "adaptive"        # Адаптивный сэмплинг
    NONE = "none"               # Без сэмплинга

@dataclass
class SamplingConfig:
    """Конфигурация сэмплинга"""
    strategy: SamplingStrategy = SamplingStrategy.ADAPTIVE
    frequency: int = 10          # Каждый 10-й лог (для FREQUENCY)
    time_window: int = 60        # Окно в секундах (для TIME_WINDOW)
    max_logs_per_window: int = 100  # Максимум логов в окне
    hash_sample_rate: float = 0.1   # 10% логов (для HASH_BASED)
    min_level: int = logging.INFO   # Минимальный уровень для сэмплинга

@dataclass
class LoggingStats:
    """Статистика логирования"""
    total_logs: int = 0
    sampled_logs: int = 0
    discarded_logs: int = 0
    logs_by_level: Dict[str, int] = field(default_factory=dict)
    logs_by_category: Dict[str, int] = field(default_factory=dict)
    avg_log_size: float = 0.0
    last_reset: float = field(default_factory=time.time)

class StructuredLogger:
    """Structured Logger с умным сэмплингом"""
    
    def __init__(self, name: str = "structured_logger", 
                 config: Optional[SamplingConfig] = None):
        """
        Инициализация Structured Logger
        
        Args:
            name: Имя логгера
            config: Конфигурация сэмплинга
        """
        self.name = name
        self.config = config or SamplingConfig()
        self.logger = logging.getLogger(name)
        
        # Статистика и состояние
        self.stats = LoggingStats()
        self._lock = threading.RLock()
        
        # Состояние для разных стратегий сэмплинга
        self._frequency_counter = 0
        self._time_window_logs: Dict[int, int] = {}  # timestamp -> count
        self._adaptive_rates: Dict[str, float] = {}  # category -> rate
        
        logger.info(f"📝 Structured Logger '{name}' инициализирован с стратегией: {config.strategy.value}")
    
    def log_structured(self, level: int, message: str, 
                      category: str = "general",
                      extra_data: Optional[Dict[str, Any]] = None,
                      force: bool = False) -> bool:
        """
        Логирование структурированного сообщения
        
        Args:
            level: Уровень логирования (logging.INFO, etc.)
            message: Основное сообщение
            category: Категория лога
            extra_data: Дополнительные данные
            force: Принудительное логирование (игнорировать сэмплинг)
            
        Returns:
            True если лог был записан, False если отброшен
        """
        with self._lock:
            self.stats.total_logs += 1
            
            # Проверяем нужно ли логировать
            if not force and not self._should_log(level, message, category):
                self.stats.discarded_logs += 1
                return False
            
            # Создаем структурированный лог
            log_entry = self._create_log_entry(level, message, category, extra_data)
            
            # Записываем лог
            self._write_log(level, log_entry)
            
            # Обновляем статистику
            self._update_stats(level, category, log_entry)
            self.stats.sampled_logs += 1
            
            return True
    
    def _should_log(self, level: int, message: str, category: str) -> bool:
        """Определяет нужно ли логировать сообщение"""
        
        # Проверяем минимальный уровень
        if level < self.config.min_level:
            return False
        
        # Критические сообщения всегда логируем
        if level >= logging.ERROR:
            return True
        
        # Применяем стратегию сэмплинга
        if self.config.strategy == SamplingStrategy.NONE:
            return True
        elif self.config.strategy == SamplingStrategy.FREQUENCY:
            return self._frequency_sampling()
        elif self.config.strategy == SamplingStrategy.TIME_WINDOW:
            return self._time_window_sampling()
        elif self.config.strategy == SamplingStrategy.HASH_BASED:
            return self._hash_based_sampling(message)
        elif self.config.strategy == SamplingStrategy.ADAPTIVE:
            return self._adaptive_sampling(category, level)
        
        return True
    
    def _frequency_sampling(self) -> bool:
        """Сэмплинг по частоте"""
        self._frequency_counter += 1
        return (self._frequency_counter % self.config.frequency) == 0
    
    def _time_window_sampling(self) -> bool:
        """Сэмплинг по временному окну"""
        current_window = int(time.time()) // self.config.time_window
        
        # Очищаем старые окна
        self._cleanup_time_windows(current_window)
        
        # Проверяем лимит для текущего окна
        current_count = self._time_window_logs.get(current_window, 0)
        if current_count < self.config.max_logs_per_window:
            self._time_window_logs[current_window] = current_count + 1
            return True
        
        return False
    
    def _hash_based_sampling(self, message: str) -> bool:
        """Сэмплинг на основе хэша сообщения"""
        message_hash = hashlib.md5(message.encode()).hexdigest()
        hash_value = int(message_hash[:8], 16) / 0xffffffff
        return hash_value < self.config.hash_sample_rate
    
    def _adaptive_sampling(self, category: str, level: int) -> bool:
        """Адаптивный сэмплинг на основе категории и уровня"""
        # Базовый коэффициент в зависимости от уровня
        base_rate = {
            logging.DEBUG: 0.05,    # 5% debug логов
            logging.INFO: 0.2,      # 20% info логов  
            logging.WARNING: 0.7,   # 70% warning логов
            logging.ERROR: 1.0,     # 100% error логов
            logging.CRITICAL: 1.0   # 100% critical логов
        }.get(level, 0.1)
        
        # Адаптивный коэффициент для категории
        if category not in self._adaptive_rates:
            self._adaptive_rates[category] = base_rate
        else:
            # Динамически корректируем коэффициент
            current_rate = self._adaptive_rates[category]
            
            # Если много логов в категории - снижаем коэффициент
            category_count = self.stats.logs_by_category.get(category, 0)
            if category_count > 1000:
                current_rate *= 0.9
            elif category_count < 100:
                current_rate *= 1.1
            
            self._adaptive_rates[category] = max(0.01, min(1.0, current_rate))
        
        # Генерируем случайное число для сравнения
        import random
        return random.random() < self._adaptive_rates[category]
    
    def _cleanup_time_windows(self, current_window: int):
        """Очистка старых временных окон"""
        cutoff = current_window - 5  # Храним 5 окон
        keys_to_remove = [k for k in self._time_window_logs.keys() if k < cutoff]
        for key in keys_to_remove:
            del self._time_window_logs[key]
    
    def _create_log_entry(self, level: int, message: str, 
                         category: str, extra_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Создание структурированной записи лога"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": logging.getLevelName(level),
            "message": message,
            "category": category,
            "logger": self.name
        }
        
        if extra_data:
            entry["data"] = extra_data
        
        return entry
    
    def _write_log(self, level: int, log_entry: Dict[str, Any]):
        """Запись лога в файл/консоль"""
        json_message = json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
        self.logger.log(level, json_message)
    
    def _update_stats(self, level: int, category: str, log_entry: Dict[str, Any]):
        """Обновление статистики логирования"""
        level_name = logging.getLevelName(level)
        
        # Статистика по уровням
        if level_name not in self.stats.logs_by_level:
            self.stats.logs_by_level[level_name] = 0
        self.stats.logs_by_level[level_name] += 1
        
        # Статистика по категориям
        if category not in self.stats.logs_by_category:
            self.stats.logs_by_category[category] = 0
        self.stats.logs_by_category[category] += 1
        
        # Средний размер лога
        log_size = len(json.dumps(log_entry))
        if self.stats.avg_log_size == 0:
            self.stats.avg_log_size = log_size
        else:
            self.stats.avg_log_size = (self.stats.avg_log_size * 0.9 + log_size * 0.1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получение статистики логирования"""
        with self._lock:
            return {
                "logger_name": self.name,
                "sampling_strategy": self.config.strategy.value,
                "total_logs": self.stats.total_logs,
                "sampled_logs": self.stats.sampled_logs,
                "discarded_logs": self.stats.discarded_logs,
                "sampling_rate": self.stats.sampled_logs / max(1, self.stats.total_logs),
                "logs_by_level": dict(self.stats.logs_by_level),
                "logs_by_category": dict(self.stats.logs_by_category),
                "avg_log_size_bytes": round(self.stats.avg_log_size, 2),
                "adaptive_rates": dict(self._adaptive_rates) if self.config.strategy == SamplingStrategy.ADAPTIVE else None,
                "uptime_seconds": time.time() - self.stats.last_reset
            }
    
    def reset_stats(self):
        """Сброс статистики"""
        with self._lock:
            self.stats = LoggingStats()
            self._frequency_counter = 0
            self._time_window_logs.clear()
            self._adaptive_rates.clear()
            logger.info(f"📊 Статистика Structured Logger '{self.name}' сброшена")
    
    def update_config(self, config: SamplingConfig):
        """Обновление конфигурации сэмплинга"""
        with self._lock:
            old_strategy = self.config.strategy
            self.config = config
            logger.info(f"⚙️ Конфигурация сэмплинга обновлена: {old_strategy.value} → {config.strategy.value}")

# Глобальные экземпляры логгеров
_loggers: Dict[str, StructuredLogger] = {}
_default_logger: Optional[StructuredLogger] = None

def get_structured_logger(name: str = "default", 
                         config: Optional[SamplingConfig] = None) -> StructuredLogger:
    """Получить Structured Logger по имени"""
    global _loggers, _default_logger
    
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, config)
        
    if name == "default" and _default_logger is None:
        _default_logger = _loggers[name]
    
    return _loggers[name]

def log_structured(level: int, message: str, category: str = "general",
                  extra_data: Optional[Dict[str, Any]] = None,
                  logger_name: str = "default") -> bool:
    """Удобная функция для структурированного логирования"""
    logger_instance = get_structured_logger(logger_name)
    return logger_instance.log_structured(level, message, category, extra_data)

# Удобные функции для разных уровней
def log_debug(message: str, category: str = "debug", **kwargs):
    """Логирование debug сообщений"""
    return log_structured(logging.DEBUG, message, category, kwargs)

def log_info(message: str, category: str = "info", **kwargs):
    """Логирование info сообщений"""
    return log_structured(logging.INFO, message, category, kwargs)

def log_warning(message: str, category: str = "warning", **kwargs):
    """Логирование warning сообщений"""
    return log_structured(logging.WARNING, message, category, kwargs)

def log_error(message: str, category: str = "error", **kwargs):
    """Логирование error сообщений"""
    return log_structured(logging.ERROR, message, category, kwargs)

# Специализированные функции для Instagram бота
def log_instagram_action(action: str, account_id: int, success: bool, **kwargs):
    """Логирование действий Instagram"""
    return log_structured(
        logging.INFO, 
        f"Instagram action: {action}", 
        "instagram",
        {"action": action, "account_id": account_id, "success": success, **kwargs}
    )

def log_telegram_interaction(user_id: int, command: str, success: bool, **kwargs):
    """Логирование взаимодействий Telegram"""
    return log_structured(
        logging.INFO,
        f"Telegram command: {command}",
        "telegram", 
        {"user_id": user_id, "command": command, "success": success, **kwargs}
    )

def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs):
    """Логирование метрик производительности"""
    return log_structured(
        logging.INFO,
        f"Performance metric: {metric_name}",
        "performance",
        {"metric": metric_name, "value": value, "unit": unit, **kwargs}
    )

def get_all_logger_stats() -> Dict[str, Any]:
    """Получение статистики всех логгеров"""
    return {name: logger.get_stats() for name, logger in _loggers.items()}

def reset_all_stats():
    """Сброс статистики всех логгеров"""
    for logger_instance in _loggers.values():
        logger_instance.reset_stats()

def init_structured_logging(configs: Optional[Dict[str, SamplingConfig]] = None):
    """Инициализация структурированного логирования с конфигурациями"""
    default_configs = {
        "default": SamplingConfig(SamplingStrategy.ADAPTIVE),
        "instagram": SamplingConfig(SamplingStrategy.ADAPTIVE, min_level=logging.INFO),
        "telegram": SamplingConfig(SamplingStrategy.TIME_WINDOW, max_logs_per_window=50),
        "performance": SamplingConfig(SamplingStrategy.FREQUENCY, frequency=5),
        "debug": SamplingConfig(SamplingStrategy.HASH_BASED, hash_sample_rate=0.05)
    }
    
    if configs:
        default_configs.update(configs)
    
    for name, config in default_configs.items():
        get_structured_logger(name, config)
    
    logger.info("📝 Structured Logging инициализировано с несколькими логгерами")

# Автоматическая инициализация с умными настройками
init_structured_logging()

logger.info("📦 Structured Logger модуль загружен") 