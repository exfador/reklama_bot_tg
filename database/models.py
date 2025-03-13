from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union


@dataclass
class InlineButton:
    """Модель для инлайн-кнопки в рекламном сообщении"""
    text: str
    url: str


@dataclass
class Advertisement:
    """Модель для рекламного сообщения"""
    id: int = None  
    chat_id: int = None  
    text: str = None 
    media_type: Optional[str] = None  
    media_file_id: Optional[str] = None 
    topic_id: Optional[int] = None 
    button: Optional[InlineButton] = None 
    interval_minutes: int = 60  
    duration_minutes: int = 1440  
    is_active: bool = True 
    created_at: int = None  
    last_sent_at: Optional[int] = None 


@dataclass
class ChatSettings:
    """Модель для настроек чата"""
    chat_id: int   
    is_enabled: bool = True 
    admin_ids: List[int] = None  