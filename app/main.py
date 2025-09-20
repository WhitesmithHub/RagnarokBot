# -*- coding: utf-8 -*-
# app/main.py
from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from app.features import creation, market, tavern
from app.ui.keyboards import gender_kb

# Подхватываем .env, если есть
load_dotenv(override=True)


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


def acquire_single_instance_lock(token: str):
    """
    Простой файловый лок: пока существует файл в %TEMP% — считаем, что бот уже запущен.
    Второй процесс сразу завершится с сообщением.
    """
    lock_path = os.path.join(
        tempfile.gettempdir(),
        f"ragnarok_{abs(hash(token))}.lock",
    )
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd, str(os.getpid()).encode("utf-8", errors="ignore"))
        return fd, lock_path
    except FileExistsError:
        print("⚠️ Уже запущен другой экземпляр бота (getUpdates конфликт). "
              "Останови предыдущий и запусти снова.")
        sys.exit(1)


async def main():
    setup_logging()

    token = (os.environ.get("BOT_TOKEN") or "").strip()
    if not token or ":" not in token:
        raise RuntimeError("BOT_TOKEN пуст или неверного формата (ожидается 123456789:AA...).")

    # Анти-дубль на время работы процесса
    lock_fd, lock_path = acquire_single_instance_lock(token)

    try:
        bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()

        # /start
        dp.message.register(on_start, CommandStart())

        # Роутеры
        dp.include_router(creation.router)
        dp.include_router(market.router)
        dp.include_router(tavern.router)

        await dp.start_polling(bot)
    finally:
        # снимаем лок
        try:
            os.close(lock_fd)
        except Exception:
            pass
        try:
            os.remove(lock_path)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
