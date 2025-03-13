from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
import time

from database.database import Database
from database.models import Advertisement, InlineButton
from keyboards.inline import (
    get_ads_list_keyboard,
    get_ad_control_keyboard,
    get_delete_confirmation_keyboard,
    get_main_settings_keyboard
)

router = Router()



current_page_cache = {}


@router.callback_query(F.data == "list_ads")
async def list_advertisements(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик просмотра списка рекламных объявлений"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на просмотр объявлений.", show_alert=True)
        return
    
    ads = await db.get_advertisements(callback.message.chat.id)
    
    if not ads:
        await callback.message.edit_text(
            "📝 В этом чате пока нет рекламных объявлений.\n\n"
            "Нажмите кнопку 'Добавить объявление', чтобы создать новое.",
            reply_markup=get_main_settings_keyboard()
        )
        await callback.answer()
        return
    
    current_page_cache[callback.from_user.id] = 0
    
    await callback.message.edit_text(
        "📝 Список рекламных объявлений:\n"
        "Выберите объявление для управления:",
        reply_markup=get_ads_list_keyboard(ads, page=0)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def navigate_pages(callback: CallbackQuery, db: Database):
    """Обработчик навигации по страницам списка объявлений"""
    page = int(callback.data.split(":")[1])
    
    current_page_cache[callback.from_user.id] = page
    
    ads = await db.get_advertisements(callback.message.chat.id)
    
    if not ads:
        await callback.message.edit_text(
            "📝 В этом чате пока нет рекламных объявлений.\n\n"
            "Нажмите кнопку 'Добавить объявление', чтобы создать новое.",
            reply_markup=get_main_settings_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📝 Список рекламных объявлений:\n"
        "Выберите объявление для управления:",
        reply_markup=get_ads_list_keyboard(ads, page=page)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_list")
async def back_to_ads_list(callback: CallbackQuery, db: Database):
    """Обработчик возврата к списку объявлений"""
    page = current_page_cache.get(callback.from_user.id, 0)
    
    ads = await db.get_advertisements(callback.message.chat.id)
    
    if not ads:
        await callback.message.edit_text(
            "📝 В этом чате пока нет рекламных объявлений.\n\n"
            "Нажмите кнопку 'Добавить объявление', чтобы создать новое.",
            reply_markup=get_main_settings_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        "📝 Список рекламных объявлений:\n"
        "Выберите объявление для управления:",
        reply_markup=get_ads_list_keyboard(ads, page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ad:"))
async def show_advertisement(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик выбора объявления из списка"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на управление объявлениями.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    
    ad = await db.get_advertisement(ad_id)
    
    if not ad or ad.chat_id != callback.message.chat.id:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return
    
    status = "✅ Активно" if ad.is_active else "❌ Отключено"
    
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
    
    topic_info = f"Тема: ID {ad.topic_id}" if ad.topic_id else "Без темы"
    button_info = f"Кнопка: {ad.button.text} ({ad.button.url})" if ad.button else "Без кнопки"
    media_info = f"Медиа: {'Фото' if ad.media_type == 'photo' else 'Видео'}" if ad.media_type else "Без медиа"
    
    text = (
        f"📋 Информация о рекламном объявлении ID: {ad.id}\n\n"
        f"Статус: {status}\n"
        f"Интервал: {format_minutes(ad.interval_minutes)}\n"
        f"Длительность: {format_minutes(ad.duration_minutes)}\n"
        f"{topic_info}\n"
        f"{button_info}\n"
        f"{media_info}\n\n"
        f"Текст объявления:\n{ad.text}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_ad_control_keyboard(ad.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_ad:"))
async def toggle_advertisement(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик включения/выключения объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на управление объявлениями.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    
    ad = await db.get_advertisement(ad_id)
    
    if not ad or ad.chat_id != callback.message.chat.id:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return
    
    ad.is_active = not ad.is_active
    
    await db.update_advertisement(ad)
    
    await show_advertisement(callback, db, is_admin)
    
    status = "включено" if ad.is_active else "выключено"
    await callback.answer(f"✅ Объявление {status}", show_alert=True)


@router.callback_query(F.data.startswith("delete_ad:"))
async def delete_advertisement_confirm(callback: CallbackQuery, is_admin: bool):
    """Обработчик запроса на удаление объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на удаление объявлений.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "🗑️ Вы уверены, что хотите удалить это объявление?\n\n"
        "Это действие нельзя отменить.",
        reply_markup=get_delete_confirmation_keyboard(ad_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_advertisement(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик подтверждения удаления объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на удаление объявлений.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    chat_id = callback.message.chat.id
    
    result = await db.delete_advertisement(ad_id, chat_id)
    
    if result:
        await callback.answer("✅ Объявление успешно удалено", show_alert=True)
    else:
        await callback.answer("❌ Ошибка при удалении объявления", show_alert=True)
    
    await back_to_ads_list(callback, db)


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cancel_delete_advertisement(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик отмены удаления объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на управление объявлениями.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    
    await show_advertisement(callback, db, is_admin)
    await callback.answer("Удаление отменено")


@router.callback_query(F.data.startswith("duplicate_ad:"))
async def duplicate_advertisement(callback: CallbackQuery, db: Database, is_admin: bool):
    """Обработчик дублирования объявления"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на управление объявлениями.", show_alert=True)
        return
    
    ad_id = int(callback.data.split(":")[1])
    
    original_ad = await db.get_advertisement(ad_id)
    
    if not original_ad or original_ad.chat_id != callback.message.chat.id:
        await callback.answer("❌ Объявление не найдено", show_alert=True)
        return
    
    new_ad = Advertisement(
        chat_id=original_ad.chat_id,
        text=original_ad.text,
        media_type=original_ad.media_type,
        media_file_id=original_ad.media_file_id,
        topic_id=original_ad.topic_id,
        button=original_ad.button,
        interval_minutes=original_ad.interval_minutes,
        duration_minutes=original_ad.duration_minutes,
        is_active=True,  
        created_at=int(time.time())  
    )
    
    new_ad_id = await db.add_advertisement(new_ad)
    
    await callback.answer(f"✅ Объявление скопировано с ID: {new_ad_id}", show_alert=True)
    
    await back_to_ads_list(callback, db) 