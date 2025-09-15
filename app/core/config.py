import os
import logging
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Добавь в Replit → Tools → Secrets.")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)
oai_client = None

if USE_OPENAI:
    try:
        oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        USE_OPENAI = False
        logger.warning(f"OpenAI SDK не инициализировался: {e}")
