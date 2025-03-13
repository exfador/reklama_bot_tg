from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Optional

from database.models import Advertisement


def get_main_settings_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить объявление", callback_data="add_ad")],
        [InlineKeyboardButton(text="📝 Список объявлений", callback_data="list_ads")],
        [InlineKeyboardButton(text="⚙️ Настройки бота", callback_data="bot_settings")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ads_list_keyboard(ads: List[Advertisement], page: int = 0, ads_per_page: int = 5) -> InlineKeyboardMarkup:
    buttons = []
    
    start_idx = page * ads_per_page
    end_idx = min(start_idx + ads_per_page, len(ads))
    
    for i in range(start_idx, end_idx):
        ad = ads[i]
        ad_text = ad.text[:30] + "..." if len(ad.text) > 30 else ad.text
        status = "✅" if ad.is_active else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {i+1}. {ad_text}", 
                callback_data=f"ad:{ad.id}"
            )
        ])
    
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"page:{page-1}")
        )
    
    if end_idx < len(ads):
        nav_buttons.append(
            InlineKeyboardButton(text="Вперед ▶️", callback_data=f"page:{page+1}")
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([
        InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ad_control_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_ad:{ad_id}"),
            InlineKeyboardButton(text="🔄 Вкл/Выкл", callback_data=f"toggle_ad:{ad_id}")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_ad:{ad_id}"),
            InlineKeyboardButton(text="💾 Дублировать", callback_data=f"duplicate_ad:{ad_id}")
        ],
        [InlineKeyboardButton(text="↩️ Назад к списку", callback_data="back_to_list")],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ad_creation_keyboard(step: str, current_data: Dict = None) -> InlineKeyboardMarkup:
    buttons = []
    
    if step == "media_type":
        buttons = [
            [
                InlineKeyboardButton(text="📷 Фото", callback_data="media_type:photo"),
                InlineKeyboardButton(text="🎥 Видео", callback_data="media_type:video")
            ],
            [InlineKeyboardButton(text="📝 Только текст", callback_data="media_type:none")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_ad_creation")]
        ]
    
    elif step == "need_button":
        buttons = [
            [
                InlineKeyboardButton(text="✅ Да", callback_data="need_button:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="need_button:no")
            ],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_media")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_ad_creation")]
        ]
    
    elif step == "need_topic":
        buttons = [
            [
                InlineKeyboardButton(text="✅ Да", callback_data="need_topic:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="need_topic:no")
            ],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_button")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_ad_creation")]
        ]
    
    elif step == "confirm":
        buttons = [
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_ad:yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_ad_creation")
            ],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_interval")]
        ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirmation_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete:{ad_id}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"cancel_delete:{ad_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_bot_settings_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🔄 Вкл/Выкл бота в чате", callback_data="toggle_bot")],
        [InlineKeyboardButton(text="👥 Управление админами", callback_data="manage_admins")],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="back_to_main")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_interval_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="30 минут", callback_data="interval:30"),
            InlineKeyboardButton(text="1 час", callback_data="interval:60")
        ],
        [
            InlineKeyboardButton(text="2 часа", callback_data="interval:120"),
            InlineKeyboardButton(text="4 часа", callback_data="interval:240")
        ],
        [
            InlineKeyboardButton(text="8 часов", callback_data="interval:480"),
            InlineKeyboardButton(text="12 часов", callback_data="interval:720")
        ],
        [
            InlineKeyboardButton(text="24 часа", callback_data="interval:1440"),
            InlineKeyboardButton(text="Свой", callback_data="interval:custom")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_topic")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_ad_creation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_duration_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="1 час", callback_data="duration:60"),
            InlineKeyboardButton(text="4 часа", callback_data="duration:240")
        ],
        [
            InlineKeyboardButton(text="12 часов", callback_data="duration:720"),
            InlineKeyboardButton(text="1 день", callback_data="duration:1440")
        ],
        [
            InlineKeyboardButton(text="3 дня", callback_data="duration:4320"),
            InlineKeyboardButton(text="7 дней", callback_data="duration:10080")
        ],
        [
            InlineKeyboardButton(text="30 дней", callback_data="duration:43200"),
            InlineKeyboardButton(text="Свой", callback_data="duration:custom")
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_interval")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_ad_creation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons) 