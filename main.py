# -*- coding: utf-8 -*-
# app/main.py
from __future__ import annotations

import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

# Наши роутеры
from app.features import creation, market, tavern

# (опционально) инициализация стораджа, если есть
try:
    from app.core.storage import init_storage  # type: ignore
except Exception:
    init_storage = None


async def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана")

    # ✅ aiogram 3.7+: parse_mode задаём через default=DefaultBotProperties
    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_cmd(m: types.Message):
        await m.answer(
            "Привет! Я запущен.\n"
            "Жми «Город» в меню или создавай персонажа."
        )

    # Подключаем фичи
    dp.include_router(creation.router)
    dp.include_router(market.router)
    dp.include_router(tavern.router)

    if init_storage:
        init_storage()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    asyncio.run(main())
