import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database.db_manager import get_instagram_account

logger = logging.getLogger(__name__)

class AdvancedHealthMonitor:
    """Комплексный мониторинг здоровья Instagram аккаунтов"""
    
    def __init__(self):
        self.health_cache = {}
        self.cache_timeout = 300  # 5 минут
    
    def calculate_comprehensive_health_score(self, account_id: int) -> int:
        """Расчет health score (0-100) на основе множественных метрик"""
        try:
            # Проверяем кэш
            if self._is_cache_valid(account_id):
                return self.health_cache[account_id]['score']
            
            account = get_instagram_account(account_id)
            if not account:
                return 0
            
            score = 100
            
            # 1. Account Age Factor (25 баллов)
            age_score = self.assess_account_age_factor(account_id)
            score = min(score, score * (age_score / 100))
            
            # 2. Activity Patterns (25 баллов)  
            activity_score = self.check_activity_patterns(account_id)
            score = min(score, score * (activity_score / 100))
            
            # 3. Restriction Status (30 баллов)
            restriction_score = self._check_restriction_status(account_id)
            score = min(score, score * (restriction_score / 100))
            
            # 4. Session Health (20 баллов)
            session_score = self._check_session_health(account_id)
            score = min(score, score * (session_score / 100))
            
            final_score = max(0, min(100, int(score)))
            
            # Кэшируем результат
            self.health_cache[account_id] = {
                'score': final_score,
                'timestamp': time.time(),
                'components': {
                    'age': age_score,
                    'activity': activity_score,
                    'restrictions': restriction_score,
                    'session': session_score
                }
            }
            
            logger.info(f"Health score для аккаунта {account_id}: {final_score}/100")
            return final_score
            
        except Exception as e:
            logger.error(f"Ошибка расчета health score для аккаунта {account_id}: {e}")
            return 0
    
    def check_activity_patterns(self, account_id: int) -> int:
        """Анализ паттернов активности (0-100)"""
        try:
            account = get_instagram_account(account_id)
            if not account:
                return 0
            
            # Базовая проверка - если аккаунт активен
            if account.is_active:
                # Симуляция проверки активности
                # В реальной реализации здесь была бы проверка:
                # - Частота действий
                # - Время между действиями
                # - Разнообразие активности
                return 90
            else:
                return 30
                
        except Exception as e:
            logger.error(f"Ошибка анализа активности для аккаунта {account_id}: {e}")
            return 0
    
    def assess_account_age_factor(self, account_id: int) -> int:
        """Оценка фактора возраста аккаунта (0-100)"""
        try:
            account = get_instagram_account(account_id)
            if not account:
                return 0
            
            # Вычисляем возраст аккаунта
            account_age = datetime.now() - account.created_at
            age_days = account_age.days
            
            # Очки на основе возраста
            if age_days >= 365:  # Больше года
                return 100
            elif age_days >= 90:  # 3+ месяца
                return 80
            elif age_days >= 30:  # 1+ месяц
                return 60
            elif age_days >= 7:   # 1+ неделя
                return 40
            else:  # Новый аккаунт
                return 20
                
        except Exception as e:
            logger.error(f"Ошибка оценки возраста аккаунта {account_id}: {e}")
            return 0
    
    def get_health_recommendations(self, account_id: int) -> List[str]:
        """Получение рекомендаций по улучшению здоровья аккаунта"""
        try:
            if account_id not in self.health_cache:
                self.calculate_comprehensive_health_score(account_id)
            
            if account_id not in self.health_cache:
                return ["Не удалось получить данные о здоровье аккаунта"]
            
            components = self.health_cache[account_id]['components']
            recommendations = []
            
            if components['age'] < 60:
                recommendations.append("Аккаунт слишком новый - требуется время для созревания")
            
            if components['activity'] < 70:
                recommendations.append("Недостаточная активность - увеличьте взаимодействие")
            
            if components['restrictions'] < 80:
                recommendations.append("Обнаружены ограничения - снизьте активность")
            
            if components['session'] < 70:
                recommendations.append("Проблемы с сессией - требуется повторная авторизация")
            
            if not recommendations:
                recommendations.append("Аккаунт в отличном состоянии!")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций для аккаунта {account_id}: {e}")
            return ["Ошибка при анализе аккаунта"]
    
    def _check_restriction_status(self, account_id: int) -> int:
        """Проверка статуса ограничений (внутренний метод)"""
        try:
            # В реальной реализации здесь была бы проверка:
            # - API лимиты
            # - Shadowban
            # - Временные блокировки
            # - Challenge статус
            
            # Симуляция - возвращаем высокий балл если аккаунт активен
            account = get_instagram_account(account_id)
            if account and account.is_active:
                return 95
            else:
                return 50
                
        except Exception as e:
            logger.error(f"Ошибка проверки ограничений для аккаунта {account_id}: {e}")
            return 0
    
    def _check_session_health(self, account_id: int) -> int:
        """Проверка здоровья сессии (внутренний метод)"""
        try:
            # В реальной реализации здесь была бы проверка:
            # - Валидность сессии
            # - Время последней активности
            # - Статус авторизации
            
            account = get_instagram_account(account_id)
            if account and account.is_active:
                return 90
            else:
                return 40
                
        except Exception as e:
            logger.error(f"Ошибка проверки сессии для аккаунта {account_id}: {e}")
            return 0
    
    def _is_cache_valid(self, account_id: int) -> bool:
        """Проверка валидности кэша"""
        if account_id not in self.health_cache:
            return False
        
        cache_time = self.health_cache[account_id]['timestamp']
        return (time.time() - cache_time) < self.cache_timeout
    
    def clear_cache(self, account_id: Optional[int] = None):
        """Очистка кэша"""
        if account_id:
            if account_id in self.health_cache:
                del self.health_cache[account_id]
        else:
            self.health_cache.clear()
        
        logger.info(f"Кэш health monitor очищен для {'всех аккаунтов' if not account_id else f'аккаунта {account_id}'}") 