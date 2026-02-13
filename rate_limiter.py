"""Simple rate limiter middleware"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class RateLimitMiddleware(BaseMiddleware):
    """Ограничивает количество запросов от пользователя"""
    
    def __init__(self, rate_limit: int = 5, time_window: int = 3600):
        """
        Args:
            rate_limit: Максимум запросов
            time_window: Временное окно в секундах (по умолчанию 1 час)
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.user_requests: Dict[int, list] = defaultdict(list)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        now = datetime.now()
        
        # Очищаем старые запросы
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < timedelta(seconds=self.time_window)
        ]
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.rate_limit:
            wait_time = self.time_window - (now - min(self.user_requests[user_id])).seconds
            wait_minutes = wait_time // 60
            
            # Определяем язык для сообщения
            lang_code = event.from_user.language_code or 'en'
            
            messages = {
                'pl': f"⚠️ Przekroczono limit ({self.rate_limit} żądań/godzinę).\nSpróbuj ponownie za {wait_minutes} minut.",
                'uk': f"⚠️ Перевищено ліміт ({self.rate_limit} запитів/годину).\nСпробуйте через {wait_minutes} хвилин.",
                'en': f"⚠️ Rate limit exceeded ({self.rate_limit} requests/hour).\nTry again in {wait_minutes} minutes."
            }
            
            # Выбираем сообщение по языку
            if lang_code.startswith('pl'):
                msg = messages['pl']
            elif lang_code.startswith('uk') or lang_code.startswith('ua'):
                msg = messages['uk']
            else:
                msg = messages['en']
            
            if isinstance(event, Message):
                await event.answer(msg)
            else:
                await event.answer(msg, show_alert=True)
            
            return  # Блокируем запрос
        
        # Добавляем новый запрос
        self.user_requests[user_id].append(now)
        
        # Продолжаем обработку
        return await handler(event, data)