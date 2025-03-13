from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from database.database import Database
from middlewares.admin_check import AdminCheckMiddleware


def setup_middlewares(dp: Dispatcher, db: Database):
    dp.message.middleware(AdminCheckMiddleware(db))
    dp.callback_query.middleware(AdminCheckMiddleware(db)) 