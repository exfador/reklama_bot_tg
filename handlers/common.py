from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.enums import ParseMode

from database.database import Database
from database.models import ChatSettings
from keyboards.inline import get_main_settings_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    if message.chat.type == "private":
        await message.answer(
            "👋 Привет! Я бот для управления рекламными сообщениями в группах.\n\n"
            "Добавьте меня в группу и выдайте права администратора, чтобы я мог публиковать сообщения.\n"
            "После этого используйте команду /reklama_settings для настройки рекламы."
        )
    else:
        await message.answer(
            "Для настройки рекламных сообщений используйте команду /reklama_settings"
        )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added_to_group(event, bot: Bot, db: Database):
    """Обработчик события добавления бота в группу"""
    chat_id = event.chat.id
    
    chat_settings = ChatSettings(
        chat_id=chat_id,
        is_enabled=True,
        admin_ids=[event.from_user.id] 
    )
    await db.save_chat_settings(chat_settings)
    
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "👋 Спасибо за добавление меня в группу!\n\n"
            "Я помогу вам настроить автоматическую рекламу в этом чате.\n"
            "Администраторы могут использовать команду /reklama_settings для настройки рекламных сообщений."
        )
    )


@router.message(Command("reklama_settings"))
async def cmd_reklama_settings(message: Message, is_admin: bool):
    """Обработчик команды /reklama_settings"""
    if not is_admin:
        await message.answer("⛔ У вас нет прав на использование этой команды.")
        return
    
    await message.answer(
        "⚙️ Настройки рекламных сообщений",
        reply_markup=get_main_settings_keyboard()
    )


@router.callback_query(F.data == "close")
async def close_menu(callback: CallbackQuery):
    """Обработчик нажатия на кнопку 'Закрыть'"""
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Обработчик возврата в главное меню"""
    await callback.message.edit_text(
        "⚙️ Настройки рекламных сообщений",
        reply_markup=get_main_settings_keyboard()
    )
    await callback.answer() 