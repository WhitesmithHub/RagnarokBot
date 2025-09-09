import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import OpenAI

# Загружаем токены из переменных окружения (Secrets в Replit)
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
Ты — мастер текстовой RPG в стиле Dungeons & Dragons и Ragnarok Online.
Правила:
- Игроки выбирают класс и имя, бот ведёт их через сюжет.
- Всегда показывай окно «УМЕНИЯ» перед выбором.
- Действия игрока имеют риск, никогда не раскрывай последствия заранее.
- Бой проходит по кубам (d20 атака, XdY урон).
- Никогда не делай игрока бессмертным.
"""


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Добро пожаловать в Ragnarok RPG!\nНапиши /new чтобы создать персонажа."
    )


@dp.message(Command("new"))
async def new(message: types.Message):
    await message.answer(
        "Введите пол, класс и имя персонажа.\nНапример: Мужчина, Мечник, Альберт."
    )


@dp.message()
async def chat_with_ai(message: types.Message):
    user_text = message.text

    response = client.responses.create(model="gpt-4.1-mini",
                                       input=[{
                                           "role": "system",
                                           "content": SYSTEM_PROMPT
                                       }, {
                                           "role": "user",
                                           "content": user_text
                                       }])

    await message.answer(response.output_text)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
фш