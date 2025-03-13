import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Callable
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError

from database.database import Database
from database.models import Advertisement


logger = logging.getLogger(__name__)


class AdvertisementScheduler:
    def __init__(self, bot: Bot, db: Database, check_interval: int = 60):
        self.bot = bot
        self.db = db
        self.check_interval = check_interval
        self.task: Optional[asyncio.Task] = None
        self.is_running = False
        
    async def start(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("Планировщик рекламы запущен")
        
    async def stop(self):
        if not self.is_running:
            return
            
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("Планировщик рекламы остановлен")
        
    async def _scheduler_loop(self):
        while self.is_running:
            try:
                await self._check_and_send_ads()
            except Exception as e:
                logger.error(f"Ошибка при проверке и отправке рекламы: {e}", exc_info=True)
                
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_send_ads(self):
        current_time = int(time.time())
        
        active_ads = await self.db.get_active_advertisements(current_time)
        
        for ad in active_ads:
            chat_settings = await self.db.get_chat_settings(ad.chat_id)
            
            if not chat_settings or not chat_settings.is_enabled:
                continue
                
            last_sent = await self.db.get_last_sent_time(ad.id)
            interval_seconds = ad.interval_minutes * 60
            
            if last_sent is None or (current_time - last_sent) >= interval_seconds:
                success = await self._send_advertisement(ad)
                
                if success:
                    await self.db.update_last_sent_time(ad.id, current_time)
    
    async def _send_advertisement(self, ad: Advertisement) -> bool:
        try:
            keyboard = None
            
            if ad.button and ad.button.url:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=ad.button.text or "Подробнее", 
                                url=ad.button.url
                            )
                        ]
                    ]
                )
            
            # Подготовим общие параметры для всех видов сообщений
            params = {
                "chat_id": ad.chat_id,
                "reply_markup": keyboard
            }
            
            # Добавляем message_thread_id только если он указан
            if ad.topic_id is not None:
                params["message_thread_id"] = ad.topic_id
                
            if ad.media_type == "photo":
                params["photo"] = ad.media_file_id
                params["caption"] = ad.text
                await self.bot.send_photo(**params)
            elif ad.media_type == "video":
                params["video"] = ad.media_file_id
                params["caption"] = ad.text
                await self.bot.send_video(**params)
            elif ad.media_type == "animation":
                params["animation"] = ad.media_file_id
                params["caption"] = ad.text
                await self.bot.send_animation(**params)
            else:
                params["text"] = ad.text
                await self.bot.send_message(**params)
                
            logger.info(f"Отправлено рекламное сообщение ID {ad.id} в чат {ad.chat_id}")
            if ad.topic_id:
                logger.info(f"Сообщение отправлено в тему ID {ad.topic_id}")
            return True
            
        except TelegramAPIError as e:
            error_message = str(e)
            
            if "chat not found" in error_message.lower() or "bot was kicked" in error_message.lower():
                logger.warning(f"Бот был удален из чата {ad.chat_id}, деактивирую настройки чата")
                await self.db.deactivate_chat_settings(ad.chat_id)
            else:
                logger.error(f"Ошибка при отправке рекламы в чат {ad.chat_id}: {e}")
                
            return False
            
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при отправке рекламы: {e}", exc_info=True)
            return False 