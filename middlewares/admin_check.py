from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError

from database.database import Database


class AdminCheckMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            chat_id = event.chat.id
            from_user_id = event.from_user.id
            is_private = event.chat.type == "private"
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id
            from_user_id = event.from_user.id
            is_private = event.message.chat.type == "private"
        else:
            return await handler(event, data)
        
        if is_private:
            data["is_admin"] = True
            return await handler(event, data)
        
        chat_settings = await self.db.get_chat_settings(chat_id)
        
        if chat_settings and chat_settings.admin_ids and from_user_id in chat_settings.admin_ids:
            data["is_admin"] = True
            data["chat_settings"] = chat_settings
            return await handler(event, data)
        
        try:
            bot = data["bot"]
            chat_member = await bot.get_chat_member(chat_id, from_user_id)
            
            is_admin = chat_member.status in ("administrator", "creator")
            
            if is_admin:
                if not chat_settings:
                    from database.models import ChatSettings
                    chat_settings = ChatSettings(
                        chat_id=chat_id,
                        is_enabled=True,
                        admin_ids=[from_user_id]
                    )
                    await self.db.save_chat_settings(chat_settings)
                elif chat_settings.admin_ids and from_user_id not in chat_settings.admin_ids:
                    chat_settings.admin_ids.append(from_user_id)
                    await self.db.save_chat_settings(chat_settings)
            
            data["is_admin"] = is_admin
            data["chat_settings"] = chat_settings
            
            return await handler(event, data)
            
        except TelegramAPIError:
            data["is_admin"] = False
            return await handler(event, data) 