# app/core/config.py
from __future__ import annotations
import os

from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Если используешь OpenAI:
try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None  # чтобы не падать, если пакет не установлен

# 1) Загружаем .env
load_dotenv()

# 2) Телеграм
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Добавь его в .env в корне проекта.")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# 3) Флаг использования OpenAI (чтобы другие модули могли импортировать)
def _to_bool(v: str | None) -> bool:
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

USE_OPENAI: bool = _to_bool(os.getenv("USE_OPENAI", "0"))
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Клиент OpenAI создаём только если включено
OPENAI_CLIENT: AsyncOpenAI | None = None
if USE_OPENAI:
    if not OPENAI_API_KEY:
        raise RuntimeError("USE_OPENAI=1, но OPENAI_API_KEY не задан в .env")
    if AsyncOpenAI is None:
        raise RuntimeError("Пакет 'openai' не установлен. Установи: python -m pip install openai")
    OPENAI_CLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Что можно импортировать из config.py
__all__ = [
    "bot",
    "USE_OPENAI",
    "OPENAI_API_KEY",
    "OPENAI_CLIENT",
    "BOT_TOKEN",
]
