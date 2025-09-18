# -*- coding: utf-8 -*-
import asyncio
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import bot
from app.features import creation, city, market, inventory, tavern, character
from app.features import quests

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("rpg-bot")

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(creation.router)
    dp.include_router(city.router)
    dp.include_router(market.router)
    dp.include_router(inventory.router)
    dp.include_router(tavern.router)
    dp.include_router(character.router)
    dp.include_router(quests.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
