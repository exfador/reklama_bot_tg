from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from database.database import Database
from database.models import ChatSettings
from keyboards.inline import get_bot_settings_keyboard, get_main_settings_keyboard

router = Router()


class AdminSettingsStates(StatesGroup):
    """Состояния для настройки администраторов"""
    waiting_for_admin_id = State()
    waiting_for_confirm_remove = State()


@router.callback_query(F.data == "bot_settings")
async def bot_settings(callback: CallbackQuery, is_admin: bool):
    """Обработчик кнопки настроек бота"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на использование этих настроек.", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚙️ Настройки бота для этого чата",
        reply_markup=get_bot_settings_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_bot")
async def toggle_bot(callback: CallbackQuery, db: Database, is_admin: bool, chat_settings: ChatSettings = None):
    """Обработчик включения/выключения бота в чате"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на использование этих настроек.", show_alert=True)
        return
    
    if not chat_settings:
        await callback.answer("❌ Ошибка получения настроек чата", show_alert=True)
        return
    
    chat_settings.is_enabled = not chat_settings.is_enabled
    await db.save_chat_settings(chat_settings)
    
    status = "включен" if chat_settings.is_enabled else "выключен"
    
    await callback.answer(f"✅ Бот {status} в этом чате", show_alert=True)
    await bot_settings(callback, is_admin=True)


@router.callback_query(F.data == "manage_admins")
async def manage_admins(callback: CallbackQuery, is_admin: bool, chat_settings: ChatSettings = None):
    """Обработчик кнопки управления администраторами"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на использование этих настроек.", show_alert=True)
        return
    
    if not chat_settings or not chat_settings.admin_ids:
        admin_list = "Список пуст"
    else:
        admin_list = "\n".join([f"• {admin_id}" for admin_id in chat_settings.admin_ids])
    
    message_text = (
        "👥 Управление администраторами бота\n\n"
        f"Текущие администраторы бота:\n{admin_list}\n\n"
        "Для добавления нового администратора, отправьте его ID.\n"
        "Для удаления администратора, отправьте его ID с минусом впереди (например, -12345678).\n\n"
        "Чтобы отменить, нажмите кнопку 'Назад'."
    )
    
    keyboard = get_bot_settings_keyboard()
    
    await callback.message.edit_text(message_text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:"))
async def admin_action(callback: CallbackQuery, db: Database, is_admin: bool, chat_settings: ChatSettings = None):
    """Обработчик действий с администраторами"""
    if not is_admin:
        await callback.answer("⛔ У вас нет прав на использование этих настроек.", show_alert=True)
        return
    
    action, admin_id = callback.data.split(":", 1)
    admin_id = int(admin_id)
    
    if not chat_settings:
        await callback.answer("❌ Ошибка получения настроек чата", show_alert=True)
        return
    
    if action == "remove_admin":
        if admin_id in chat_settings.admin_ids:
            chat_settings.admin_ids.remove(admin_id)
            await db.save_chat_settings(chat_settings)
            await callback.answer("✅ Администратор удален", show_alert=True)
        else:
            await callback.answer("❌ Администратор не найден", show_alert=True)
    
    await manage_admins(callback, is_admin=True, chat_settings=chat_settings) 