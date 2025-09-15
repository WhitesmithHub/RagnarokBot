# -*- coding: utf-8 -*-
# main.py
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.core.config import BOT_TOKEN  # положи токен в этот модуль или в переменную среды
from app.features import creation, city, market, inventory, tavern, character, dungeon

logging.basicConfig(level=logging.INFO)

def _resolve_token() -> str:
    return os.getenv("BOT_TOKEN") or BOT_TOKEN

async def main():
    bot = Bot(token=_resolve_token(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(creation.router)
    dp.include_router(city.router)
    dp.include_router(market.router)
    dp.include_router(inventory.router)
    dp.include_router(tavern.router)
    dp.include_router(character.router)
    dp.include_router(dungeon.router)

    logging.info("rpg-bot | Бот запускается…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("rpg-bot | Остановлен.")
