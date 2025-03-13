import aiosqlite
import json
import time
from typing import List, Optional, Dict, Any, Tuple, Union
import os

from config import config
from database.models import Advertisement, ChatSettings, InlineButton


class Database:
    def __init__(self, db_path: str = config.DB_PATH):
        self.db_path = db_path
        
    async def create_tables(self):
        """Создаёт таблицы в базе данных, если они не существуют"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chat_settings (
                    chat_id INTEGER PRIMARY KEY,
                    is_enabled INTEGER DEFAULT 1,
                    admin_ids TEXT DEFAULT '[]'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS advertisements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    media_type TEXT,
                    media_file_id TEXT,
                    topic_id INTEGER,
                    button_text TEXT,
                    button_url TEXT,
                    interval_minutes INTEGER DEFAULT 60,
                    duration_minutes INTEGER DEFAULT 1440,
                    is_active INTEGER DEFAULT 1,
                    created_at INTEGER,
                    last_sent_at INTEGER,
                    FOREIGN KEY (chat_id) REFERENCES chat_settings (chat_id) ON DELETE CASCADE
                )
            """)
            
            await db.commit()
    
    
    async def get_chat_settings(self, chat_id: int) -> Optional[ChatSettings]:
        """Получает настройки чата из базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM chat_settings WHERE chat_id = ?", 
                (chat_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            admin_ids = json.loads(row['admin_ids'])
            return ChatSettings(
                chat_id=row['chat_id'],
                is_enabled=bool(row['is_enabled']),
                admin_ids=admin_ids
            )
    
    async def save_chat_settings(self, settings: ChatSettings):
        """Сохраняет настройки чата в базу данных"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO chat_settings (chat_id, is_enabled, admin_ids) 
                VALUES (?, ?, ?)
                ON CONFLICT (chat_id) DO UPDATE SET
                    is_enabled = ?,
                    admin_ids = ?
                """,
                (
                    settings.chat_id, 
                    int(settings.is_enabled), 
                    json.dumps(settings.admin_ids or []),
                    int(settings.is_enabled),
                    json.dumps(settings.admin_ids or [])
                )
            )
            await db.commit()
            
    async def delete_chat_settings(self, chat_id: int):
        """Удаляет настройки чата из базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM chat_settings WHERE chat_id = ?", (chat_id,))
            await db.commit()
    
    
    async def add_advertisement(self, ad: Advertisement) -> int:
        """Добавляет новое рекламное объявление в базу данных и возвращает его ID"""
        current_time = int(time.time())
        if ad.created_at is None:
            ad.created_at = current_time
            
        button_text = None
        button_url = None
        if ad.button:
            button_text = ad.button.text
            button_url = ad.button.url
            
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO advertisements (
                    chat_id, text, media_type, media_file_id, topic_id,
                    button_text, button_url, interval_minutes, duration_minutes,
                    is_active, created_at, last_sent_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ad.chat_id, ad.text, ad.media_type, ad.media_file_id, ad.topic_id,
                    button_text, button_url, ad.interval_minutes, ad.duration_minutes,
                    int(ad.is_active), ad.created_at, ad.last_sent_at
                )
            )
            await db.commit()
            return cursor.lastrowid
    
    async def update_advertisement(self, ad: Advertisement) -> bool:
        """Обновляет существующее рекламное объявление в базе данных"""
        if ad.id is None:
            return False
            
        button_text = None
        button_url = None
        if ad.button:
            button_text = ad.button.text
            button_url = ad.button.url
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE advertisements SET
                    text = ?, media_type = ?, media_file_id = ?, topic_id = ?,
                    button_text = ?, button_url = ?, interval_minutes = ?,
                    duration_minutes = ?, is_active = ?, last_sent_at = ?
                WHERE id = ? AND chat_id = ?
                """,
                (
                    ad.text, ad.media_type, ad.media_file_id, ad.topic_id,
                    button_text, button_url, ad.interval_minutes, ad.duration_minutes,
                    int(ad.is_active), ad.last_sent_at, ad.id, ad.chat_id
                )
            )
            await db.commit()
            return True
    
    async def get_advertisement(self, ad_id: int) -> Optional[Advertisement]:
        """Получает рекламное объявление по его ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM advertisements WHERE id = ?", 
                (ad_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            button = None
            if row['button_text'] and row['button_url']:
                button = InlineButton(text=row['button_text'], url=row['button_url'])
                
            return Advertisement(
                id=row['id'],
                chat_id=row['chat_id'],
                text=row['text'],
                media_type=row['media_type'],
                media_file_id=row['media_file_id'],
                topic_id=row['topic_id'],
                button=button,
                interval_minutes=row['interval_minutes'],
                duration_minutes=row['duration_minutes'],
                is_active=bool(row['is_active']),
                created_at=row['created_at'],
                last_sent_at=row['last_sent_at']
            )
    
    async def get_advertisements(self, chat_id: int, active_only: bool = False) -> List[Advertisement]:
        """Получает список рекламных объявлений для чата"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM advertisements WHERE chat_id = ?"
            params = [chat_id]
            
            if active_only:
                query += " AND is_active = 1"
                
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            ads = []
            for row in rows:
                button = None
                if row['button_text'] and row['button_url']:
                    button = InlineButton(text=row['button_text'], url=row['button_url'])
                    
                ad = Advertisement(
                    id=row['id'],
                    chat_id=row['chat_id'],
                    text=row['text'],
                    media_type=row['media_type'],
                    media_file_id=row['media_file_id'],
                    topic_id=row['topic_id'],
                    button=button,
                    interval_minutes=row['interval_minutes'],
                    duration_minutes=row['duration_minutes'],
                    is_active=bool(row['is_active']),
                    created_at=row['created_at'],
                    last_sent_at=row['last_sent_at']
                )
                ads.append(ad)
                
            return ads
    
    async def delete_advertisement(self, ad_id: int, chat_id: int) -> bool:
        """Удаляет рекламное объявление из базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM advertisements WHERE id = ? AND chat_id = ?",
                (ad_id, chat_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_ads_for_sending(self) -> List[Advertisement]:
        """Получает список объявлений, которые нужно отправить"""
        current_time = int(time.time())
        current_time_minutes = current_time // 60
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT a.* FROM advertisements a
                JOIN chat_settings c ON a.chat_id = c.chat_id
                WHERE a.is_active = 1 AND c.is_enabled = 1
            """)
            rows = await cursor.fetchall()
            

            ads_to_send = []
            for row in rows:
                if row['last_sent_at'] is None:
                    ads_to_send.append(self._row_to_advertisement(row))
                    continue
                
                last_sent_minutes = row['last_sent_at'] // 60
                interval_minutes = row['interval_minutes']
                
                if (current_time_minutes - last_sent_minutes) >= interval_minutes:
                    created_minutes = row['created_at'] // 60
                    duration_minutes = row['duration_minutes']
                    
                    if (current_time_minutes - created_minutes) <= duration_minutes:
                        ads_to_send.append(self._row_to_advertisement(row))
            
            return ads_to_send
    
    async def get_active_advertisements(self, current_time: int) -> List[Advertisement]:
        """Получает список активных рекламных объявлений для отправки на данный момент времени"""
        current_time_minutes = current_time // 60
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT a.* FROM advertisements a
                JOIN chat_settings c ON a.chat_id = c.chat_id
                WHERE a.is_active = 1 AND c.is_enabled = 1
            """)
            rows = await cursor.fetchall()
            
            active_ads = []
            for row in rows:
                created_at = row['created_at']
                duration_minutes = row['duration_minutes']
                ad_end_time = (created_at // 60) + duration_minutes
                
                if current_time_minutes > ad_end_time:
                    continue
                    
                active_ads.append(self._row_to_advertisement(row))
                
            return active_ads
    
    async def get_last_sent_time(self, ad_id: int) -> Optional[int]:
        """Получает время последней отправки рекламы"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT last_sent_at FROM advertisements WHERE id = ?",
                (ad_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else None
    
    async def update_last_sent_time(self, ad_id: int, timestamp: int) -> bool:
        """Обновляет время последней отправки рекламы"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE advertisements SET last_sent_at = ? WHERE id = ?",
                (timestamp, ad_id)
            )
            await db.commit()
            return True
            
    async def deactivate_chat_settings(self, chat_id: int) -> bool:
        """Деактивирует настройки чата"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE chat_settings SET is_enabled = 0 WHERE chat_id = ?",
                (chat_id,)
            )
            await db.commit()
            return True
    
    def _row_to_advertisement(self, row) -> Advertisement:
        """Преобразует строку из БД в объект Advertisement"""
        button = None
        if row['button_text'] and row['button_url']:
            button = InlineButton(text=row['button_text'], url=row['button_url'])
            
        return Advertisement(
            id=row['id'],
            chat_id=row['chat_id'],
            text=row['text'],
            media_type=row['media_type'],
            media_file_id=row['media_file_id'],
            topic_id=row['topic_id'],
            button=button,
            interval_minutes=row['interval_minutes'],
            duration_minutes=row['duration_minutes'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            last_sent_at=row['last_sent_at']
        ) 