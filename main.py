import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import config
from database.database import Database
from handlers.router import setup_routers
from middlewares.router import setup_middlewares
from utils.scheduler import AdvertisementScheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    logger.info("Запуск бота...")
    db = Database()
    await db.create_tables()
    logger.info("Таблицы базы данных созданы")
    bot = Bot(
        token=config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["db"] = db
    dp["bot"] = bot
    setup_middlewares(dp, db)
    dp.include_router(setup_routers())
    scheduler = AdvertisementScheduler(bot, db)
    await scheduler.start()
    logger.info("Бот запущен")
    await dp.start_polling(bot, skip_updates=True)
    await scheduler.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}", exc_info=True) 