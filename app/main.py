# -*- coding: utf-8 -*-
# app/main.py
from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from app.features import creation, market, tavern
from app.ui.keyboards import gender_kb

async def on_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в <b>Ragnarok</b>!\nВыбери пол, чтобы начать:",
        reply_markup=gender_kb()
    )

def setup_logging():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

async def main():
    setup_logging()

    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана.")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # /start
    dp.message.register(on_start, CommandStart())

    # наши роутеры
    dp.include_router(creation.router)
    dp.include_router(market.router)
    dp.include_router(tavern.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

