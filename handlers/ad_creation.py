from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
import time

from database.database import Database
from database.models import Advertisement, InlineButton
from keyboards.inline import (
    get_ad_creation_keyboard,
    get_interval_keyboard,
    get_duration_keyboard,
    get_main_settings_keyboard
)

router = Router()


class AdCreationStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_media = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
    waiting_for_topic_id = State()
    waiting_for_custom_interval = State()
    waiting_for_custom_duration = State()


ad_creation_data = {}


def get_user_chat_key(user_id: int, chat_id: int) -> str:
    """Генерирует ключ для хранения временных данных"""
    return f"{user_id}_{chat_id}"


@router.callback_query(F.data == "add_ad")
async def add_advertisement(callback: CallbackQuery, state: FSMContext, is_admin: bool):
    """Обработчик начала создания нового рекламного объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на создание объявлений.", show_alert=True)
        return
    
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    ad_creation_data[user_chat_key] = {
        "chat_id": callback.message.chat.id,
        "created_at": int(time.time())
    }
    
    await state.set_state(AdCreationStates.waiting_for_text)
    
    await callback.message.edit_text(
        "📝 Отправьте текст для рекламного объявления.\n\n"
        "Для отмены, введите /cancel.",
    )
    await callback.answer()


@router.message(StateFilter(AdCreationStates.waiting_for_text))
async def process_ad_text(message: Message, state: FSMContext):
    """Обработчик получения текста объявления"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    ad_creation_data[user_chat_key]["text"] = message.text
    
    await message.answer(
        "📊 Выберите тип медиа для объявления:",
        reply_markup=get_ad_creation_keyboard("media_type")
    )
    
    await state.set_state(AdCreationStates.waiting_for_media)


@router.callback_query(StateFilter(AdCreationStates.waiting_for_media), F.data.startswith("media_type:"))
async def process_media_type(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора типа медиа"""
    media_type = callback.data.split(":")[1]
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if media_type == "none":
        ad_creation_data[user_chat_key]["media_type"] = None
        ad_creation_data[user_chat_key]["media_file_id"] = None
        
        await callback.message.edit_text(
            "🔘 Нужна ли инлайн-кнопка для этого объявления?",
            reply_markup=get_ad_creation_keyboard("need_button")
        )
        await state.set_state(None)  
        await callback.answer()
        return
    
    ad_creation_data[user_chat_key]["media_type"] = media_type
    
    await callback.message.edit_text(
        f"📤 Отправьте {'фото' if media_type == 'photo' else 'видео'} для объявления.\n\n"
        "Для отмены, нажмите кнопку 'Отмена'."
    )
    await state.set_state(AdCreationStates.waiting_for_media)
    await callback.answer()


@router.message(StateFilter(AdCreationStates.waiting_for_media))
async def process_media_file(message: Message, state: FSMContext):
    """Обработчик получения медиа-файла"""
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    media_type = ad_creation_data[user_chat_key].get("media_type")
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    file_id = None
    if media_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif media_type == "video" and message.video:
        file_id = message.video.file_id
    else:
        await message.answer(
            f"❌ Пожалуйста, отправьте {'фото' if media_type == 'photo' else 'видео'}.\n\n"
            "Для отмены, введите /cancel."
        )
        return
    
    ad_creation_data[user_chat_key]["media_file_id"] = file_id
    
    await message.answer(
        "🔘 Нужна ли инлайн-кнопка для этого объявления?",
        reply_markup=get_ad_creation_keyboard("need_button")
    )
    await state.set_state(None)  


@router.callback_query(F.data.startswith("need_button:"))
async def process_need_button(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора необходимости кнопки"""
    need_button = callback.data.split(":")[1] == "yes"
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if not need_button:
        ad_creation_data[user_chat_key]["button"] = None
        
        await callback.message.edit_text(
            "📚 Нужно ли отправлять объявление в конкретной теме? (для чатов с темами)",
            reply_markup=get_ad_creation_keyboard("need_topic")
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🔤 Введите текст для кнопки.\n\n"
        "Для отмены, введите /cancel."
    )
    await state.set_state(AdCreationStates.waiting_for_button_text)
    await callback.answer()


@router.message(StateFilter(AdCreationStates.waiting_for_button_text))
async def process_button_text(message: Message, state: FSMContext):
    """Обработчик получения текста кнопки"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    
    if "button" not in ad_creation_data[user_chat_key]:
        ad_creation_data[user_chat_key]["button"] = {}
    
    ad_creation_data[user_chat_key]["button"]["text"] = message.text
    
    await message.answer(
        "🔗 Введите URL для кнопки (должен начинаться с http:// или https://).\n\n"
        "Для отмены, введите /cancel."
    )
    await state.set_state(AdCreationStates.waiting_for_button_url)


@router.message(StateFilter(AdCreationStates.waiting_for_button_url))
async def process_button_url(message: Message, state: FSMContext):
    """Обработчик получения URL кнопки"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    
    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await message.answer(
            "❌ URL должен начинаться с http:// или https://.\n"
            "Пожалуйста, введите корректный URL.\n\n"
            "Для отмены, введите /cancel."
        )
        return
    
    ad_creation_data[user_chat_key]["button"]["url"] = url
    
    await message.answer(
        "📚 Нужно ли отправлять объявление в конкретной теме? (для чатов с темами)",
        reply_markup=get_ad_creation_keyboard("need_topic")
    )
    await state.set_state(None)  


@router.callback_query(F.data.startswith("need_topic:"))
async def process_need_topic(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора необходимости темы"""
    need_topic = callback.data.split(":")[1] == "yes"
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if not need_topic:
        ad_creation_data[user_chat_key]["topic_id"] = None
        
        await callback.message.edit_text(
            "⏱️ Выберите интервал между отправками объявления:",
            reply_markup=get_interval_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "🆔 Введите ID темы (topic_id) для отправки объявления.\n"
        "Это должно быть число.\n\n"
        "Для отмены, введите /cancel."
    )
    await state.set_state(AdCreationStates.waiting_for_topic_id)
    await callback.answer()


@router.message(StateFilter(AdCreationStates.waiting_for_topic_id))
async def process_topic_id(message: Message, state: FSMContext):
    """Обработчик получения ID темы"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    
    try:
        topic_id = int(message.text.strip())
        if topic_id <= 0:
            raise ValueError("Topic ID должен быть положительным числом")
    except ValueError:
        await message.answer(
            "❌ ID темы должен быть положительным числом.\n"
            "Пожалуйста, введите корректный ID темы.\n\n"
            "Для отмены, введите /cancel."
        )
        return
    
    ad_creation_data[user_chat_key]["topic_id"] = topic_id
    
    await message.answer(
        "⏱️ Выберите интервал между отправками объявления:",
        reply_markup=get_interval_keyboard()
    )
    await state.set_state(None)  


@router.callback_query(F.data.startswith("interval:"))
async def process_interval(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора интервала отправки"""
    interval_value = callback.data.split(":")[1]
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if interval_value == "custom":
        await callback.message.edit_text(
            "⏱️ Введите интервал в минутах (от 5 до 1440).\n\n"
            "Для отмены, введите /cancel."
        )
        await state.set_state(AdCreationStates.waiting_for_custom_interval)
        await callback.answer()
        return
    
    ad_creation_data[user_chat_key]["interval_minutes"] = int(interval_value)
    
    await callback.message.edit_text(
        "📆 Выберите длительность показа объявления:",
        reply_markup=get_duration_keyboard()
    )
    await callback.answer()


@router.message(StateFilter(AdCreationStates.waiting_for_custom_interval))
async def process_custom_interval(message: Message, state: FSMContext):
    """Обработчик получения пользовательского интервала"""
    from config import config
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    
    try:
        interval = int(message.text.strip())
        if interval < config.MIN_INTERVAL or interval > config.MAX_INTERVAL:
            raise ValueError(f"Интервал должен быть от {config.MIN_INTERVAL} до {config.MAX_INTERVAL} минут")
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}.\n"
            "Пожалуйста, введите корректное значение.\n\n"
            "Для отмены, введите /cancel."
        )
        return
    
    ad_creation_data[user_chat_key]["interval_minutes"] = interval
    
    await message.answer(
        "📆 Выберите длительность показа объявления:",
        reply_markup=get_duration_keyboard()
    )
    await state.set_state(None)  


@router.callback_query(F.data.startswith("duration:"))
async def process_duration(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора длительности показа"""
    duration_value = callback.data.split(":")[1]
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if duration_value == "custom":
        await callback.message.edit_text(
            "⏱️ Введите длительность в минутах (от 5 до 10080).\n\n"
            "Для отмены, введите /cancel."
        )
        await state.set_state(AdCreationStates.waiting_for_custom_duration)
        await callback.answer()
        return
    
    ad_creation_data[user_chat_key]["duration_minutes"] = int(duration_value)
    
    await show_ad_summary(callback, user_chat_key)


@router.message(StateFilter(AdCreationStates.waiting_for_custom_duration))
async def process_custom_duration(message: Message, state: FSMContext):
    """Обработчик получения пользовательской длительности"""
    from config import config
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Создание объявления отменено.",
            reply_markup=get_main_settings_keyboard()
        )
        return
    
    user_chat_key = get_user_chat_key(message.from_user.id, message.chat.id)
    
    try:
        duration = int(message.text.strip())
        if duration < config.MIN_DURATION or duration > config.MAX_DURATION:
            raise ValueError(f"Длительность должна быть от {config.MIN_DURATION} до {config.MAX_DURATION} минут")
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}.\n"
            "Пожалуйста, введите корректное значение.\n\n"
            "Для отмены, введите /cancel."
        )
        return
    
    ad_creation_data[user_chat_key]["duration_minutes"] = duration
    
    await show_ad_summary(message, user_chat_key)
    await state.set_state(None)  


async def show_ad_summary(message_or_callback, user_chat_key: str):
    """Показывает сводку о создаваемом объявлении и запрашивает подтверждение"""
    ad_data = ad_creation_data[user_chat_key]
    
    text = "📋 Сводка о создаваемом объявлении:\n\n"
    
    ad_text = ad_data.get("text", "Не указан")
    if len(ad_text) > 100:
        ad_text = ad_text[:97] + "..."
    text += f"📝 Текст: {ad_text}\n"
    
    media_type = ad_data.get("media_type")
    if media_type:
        text += f"📊 Тип медиа: {'Фото' if media_type == 'photo' else 'Видео'}\n"
    else:
        text += "📊 Тип медиа: Без медиа\n"
    
    button = ad_data.get("button")
    if button:
        text += f"🔘 Кнопка: {button.get('text')} ({button.get('url')})\n"
    else:
        text += "🔘 Кнопка: Без кнопки\n"
    
    topic_id = ad_data.get("topic_id")
    if topic_id:
        text += f"📚 Тема: ID {topic_id}\n"
    else:
        text += "📚 Тема: Без темы\n"
    
    interval = ad_data.get("interval_minutes", 60)
    duration = ad_data.get("duration_minutes", 1440)
    
    def format_minutes(minutes):
        if minutes < 60:
            return f"{minutes} мин."
        elif minutes < 1440:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours} ч." + (f" {mins} мин." if mins > 0 else "")
        else:
            days = minutes // 1440
            hours = (minutes % 1440) // 60
            return f"{days} д." + (f" {hours} ч." if hours > 0 else "")
    
    text += f"⏱️ Интервал: {format_minutes(interval)}\n"
    text += f"📆 Длительность: {format_minutes(duration)}\n\n"
    
    text += "Подтвердите создание объявления:"
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(
            text,
            reply_markup=get_ad_creation_keyboard("confirm")
        )
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(
            text,
            reply_markup=get_ad_creation_keyboard("confirm")
        )


@router.callback_query(F.data == "confirm_ad:yes")
async def confirm_ad_creation(callback: CallbackQuery, db: Database, state: FSMContext):
    """Обработчик подтверждения создания объявления"""
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if user_chat_key not in ad_creation_data:
        await callback.answer("❌ Ошибка: данные объявления не найдены", show_alert=True)
        return
    
    ad_data = ad_creation_data[user_chat_key]
    
    button = None
    if ad_data.get("button"):
        from database.models import InlineButton
        button = InlineButton(
            text=ad_data["button"]["text"],
            url=ad_data["button"]["url"]
        )
    
    advertisement = Advertisement(
        chat_id=ad_data["chat_id"],
        text=ad_data["text"],
        media_type=ad_data.get("media_type"),
        media_file_id=ad_data.get("media_file_id"),
        topic_id=ad_data.get("topic_id"),
        button=button,
        interval_minutes=ad_data.get("interval_minutes", 60),
        duration_minutes=ad_data.get("duration_minutes", 1440),
        is_active=True,
        created_at=ad_data["created_at"]
    )
    
    ad_id = await db.add_advertisement(advertisement)
    
    del ad_creation_data[user_chat_key]
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ Рекламное объявление успешно создано (ID: {ad_id}).\n\n"
        "Вы можете управлять созданными объявлениями через меню настроек.",
        reply_markup=get_main_settings_keyboard()
    )
    await callback.answer("✅ Объявление создано!", show_alert=True)


@router.callback_query(F.data == "cancel_ad_creation")
async def cancel_ad_creation(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены создания объявления"""
    user_chat_key = get_user_chat_key(callback.from_user.id, callback.message.chat.id)
    
    if user_chat_key in ad_creation_data:
        del ad_creation_data[user_chat_key]
    
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание объявления отменено.",
        reply_markup=get_main_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_media")
async def back_to_media(callback: CallbackQuery):
    """Возврат к выбору типа медиа"""
    await callback.message.edit_text(
        "📊 Выберите тип медиа для объявления:",
        reply_markup=get_ad_creation_keyboard("media_type")
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_button")
async def back_to_button(callback: CallbackQuery):
    """Возврат к выбору необходимости кнопки"""
    await callback.message.edit_text(
        "🔘 Нужна ли инлайн-кнопка для этого объявления?",
        reply_markup=get_ad_creation_keyboard("need_button")
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_topic")
async def back_to_topic(callback: CallbackQuery):
    """Возврат к выбору необходимости темы"""
    await callback.message.edit_text(
        "📚 Нужно ли отправлять объявление в конкретной теме? (для чатов с темами)",
        reply_markup=get_ad_creation_keyboard("need_topic")
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_interval")
async def back_to_interval(callback: CallbackQuery):
    """Возврат к выбору интервала отправки"""
    await callback.message.edit_text(
        "⏱️ Выберите интервал между отправками объявления:",
        reply_markup=get_interval_keyboard()
    )
    await callback.answer() 