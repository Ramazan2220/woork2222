#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Асинхронный обработчик очереди задач прогрева аккаунтов
"""

import logging
import threading
import queue
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Глобальные переменные для управления очередью
warmup_executor = None
warmup_queue_running = False
active_tasks = {}
task_lock = threading.Lock()

# Настройки по умолчанию
DEFAULT_MAX_WORKERS = 3  # Количество одновременных потоков
MAX_CONCURRENT_ACCOUNTS = 5  # Максимум аккаунтов одновременно


class AsyncWarmupQueue:
    """Асинхронная очередь прогрева с поддержкой параллельной обработки"""
    
    def __init__(self, max_workers: int = DEFAULT_MAX_WORKERS):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.Queue()
        self.running = False
        self.active_accounts = set()
        self.queued_tasks = set()  # Добавляем отслеживание задач в очереди
        self.lock = threading.Lock()
        
    def start(self):
        """Запустить асинхронную очередь"""
        self.running = True
        logger.info(f"🚀 Запуск асинхронной очереди прогрева с {self.max_workers} потоками")
        
        # Запускаем обработчик очереди
        threading.Thread(target=self._process_queue, daemon=True).start()
        
    def stop(self):
        """Остановить очередь"""
        logger.info("🛑 Остановка асинхронной очереди прогрева...")
        self.running = False
        self.executor.shutdown(wait=True)
        
    def add_task(self, task):
        """Добавить задачу в очередь"""
        with self.lock:
            if task.id not in self.queued_tasks:
                self.task_queue.put(task)
                self.queued_tasks.add(task.id)
                logger.info(f"➕ Задача #{task.id} добавлена в очередь")
            
    def _process_queue(self):
        """Основной цикл обработки очереди"""
        futures = {}
        
        while self.running:
            try:
                # Проверяем завершенные задачи
                completed_futures = []
                for future in list(futures.keys()):
                    if future.done():
                        completed_futures.append(future)
                        
                # Обрабатываем завершенные задачи
                for future in completed_futures:
                    task = futures.pop(future)
                    try:
                        result = future.result()
                        logger.info(f"✅ Задача #{task.id} завершена")
                        with self.lock:
                            self.active_accounts.discard(task.account_id)
                            self.queued_tasks.discard(task.id)  # Удаляем из отслеживания
                    except Exception as e:
                        logger.error(f"❌ Ошибка в задаче #{task.id}: {e}")
                        with self.lock:
                            self.active_accounts.discard(task.account_id)
                            self.queued_tasks.discard(task.id)  # Удаляем из отслеживания
                
                # Добавляем новые задачи если есть свободные слоты
                while len(futures) < self.max_workers and not self.task_queue.empty():
                    try:
                        task = self.task_queue.get_nowait()
                        
                        # Проверяем, не обрабатывается ли уже этот аккаунт
                        with self.lock:
                            if task.account_id in self.active_accounts:
                                logger.info(f"⏳ Аккаунт {task.account_id} уже обрабатывается, откладываем")
                                self.task_queue.put(task)  # Возвращаем в очередь
                                continue
                                
                            self.active_accounts.add(task.account_id)
                        
                        # Запускаем задачу в отдельном потоке
                        future = self.executor.submit(self._process_task, task)
                        futures[future] = task
                        logger.info(f"🔄 Запущена обработка задачи #{task.id} для аккаунта {task.account_id}")
                        
                    except queue.Empty:
                        break
                
                # Небольшая пауза
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле обработки очереди: {e}")
                time.sleep(5)
                
    def _process_task(self, task):
        """Обработать одну задачу прогрева"""
        try:
            from database.db_manager import get_session
            from database.models import WarmupStatus, WarmupTask
            from instagram.client import InstagramClient
            from utils.warmup_manager import WarmupManager
            
            session = get_session()
            
            try:
                # Перезагружаем задачу из базы данных для получения актуальных данных
                task = session.query(WarmupTask).filter_by(id=task.id).first()
                if not task:
                    logger.error(f"❌ Задача #{task.id} не найдена в базе данных")
                    return
                
                # Обновляем статус задачи
                logger.info(f"🔄 Обновляем статус задачи #{task.id} на RUNNING")
                task.status = WarmupStatus.RUNNING
                task.started_at = datetime.now()
                session.commit()
                logger.info(f"✅ Статус задачи #{task.id} обновлен на {task.status.value}")
                
                # Загружаем настройки
                settings = json.loads(task.settings)
                
                # Создаем клиент Instagram
                client = InstagramClient(task.account_id)
                
                # Проверяем вход
                if not client.check_login():
                    raise Exception(f"Не удалось войти в аккаунт {task.account_id}")
                
                logger.info(f"✅ Успешно вошли в аккаунт {task.account_id} для прогрева")
                
                # Создаем менеджер прогрева
                warmup_manager = WarmupManager(
                    account_id=task.account_id,
                    client=client,
                    warmup_speed=settings.get('warmup_speed', 'NORMAL')
                )
                
                # Устанавливаем ID задачи для отслеживания прогресса
                warmup_manager.set_task_id(task.id)
                
                # Обновляем текущую фазу
                warmup_manager.current_phase = settings.get('current_phase', 'phase1')
                
                # Выполняем сессию прогрева
                logger.info(f"🚀 Запуск сессии прогрева для аккаунта {task.account_id}")
                result = warmup_manager.perform_human_warmup_session(settings)
                
                # Обновляем прогресс
                progress = task.progress or {}
                progress['sessions_count'] = progress.get('sessions_count', 0) + 1
                progress['current_phase'] = warmup_manager.current_phase
                progress['last_session'] = datetime.now().isoformat()
                progress['last_session_results'] = result
                
                # Обновляем статистику
                for action, count in result['actions_performed'].items():
                    if action not in progress.get('total_actions', {}):
                        if 'total_actions' not in progress:
                            progress['total_actions'] = {}
                        progress['total_actions'][action] = 0
                    progress['total_actions'][action] += count
                
                task.progress = progress
                session.commit()
                
                logger.info(f"📊 Аккаунт {task.account_id} - выполнено действий: {result['actions_performed']}")
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке задачи #{task.id}: {e}")
            # Обновляем статус на FAILED
            try:
                session = get_session()
                task.status = WarmupStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                session.commit()
                session.close()
            except:
                pass
            raise


def start_async_warmup_queue(max_workers: int = DEFAULT_MAX_WORKERS):
    """Запустить асинхронную очередь прогрева"""
    global warmup_executor, warmup_queue_running
    
    if warmup_queue_running:
        logger.info("🔄 Асинхронная очередь прогрева уже запущена")
        return
    
    warmup_executor = AsyncWarmupQueue(max_workers=max_workers)
    warmup_executor.start()
    warmup_queue_running = True
    
    # Запускаем поток для загрузки задач из БД
    threading.Thread(target=_load_tasks_from_db, daemon=True).start()
    

def stop_async_warmup_queue():
    """Остановить асинхронную очередь"""
    global warmup_executor, warmup_queue_running
    
    if warmup_executor:
        warmup_executor.stop()
        warmup_executor = None
    
    warmup_queue_running = False
    

def _load_tasks_from_db():
    """Загружать задачи из БД в очередь"""
    from database.db_manager import get_session
    from database.models import WarmupTask, WarmupStatus
    
    while warmup_queue_running:
        try:
            session = get_session()
            
            # Получаем активные задачи
            tasks = session.query(WarmupTask).filter(
                WarmupTask.status.in_([WarmupStatus.PENDING, WarmupStatus.RUNNING])
            ).all()
            
            # Добавляем в очередь
            for task in tasks:
                if warmup_executor and task.account_id not in warmup_executor.active_accounts:
                    warmup_executor.add_task(task)
            
            session.close()
            
            # Пауза между проверками
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке задач: {e}")
            time.sleep(30)


def set_max_workers(max_workers: int):
    """Изменить количество потоков"""
    global warmup_executor
    
    if warmup_executor:
        logger.info(f"🔧 Изменение количества потоков с {warmup_executor.max_workers} на {max_workers}")
        # Перезапускаем с новым количеством потоков
        stop_async_warmup_queue()
        time.sleep(2)
        start_async_warmup_queue(max_workers=max_workers)
    else:
        logger.info(f"🔧 Установлено количество потоков: {max_workers}")
