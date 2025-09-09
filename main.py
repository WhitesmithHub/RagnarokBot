import os
import logging
import random
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from openai import AsyncOpenAI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Загружаем токены
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# Инициализация бота и OpenAI
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Состояния FSM
class GameStates(StatesGroup):
    choosing_gender = State()
    choosing_name = State()
    choosing_class = State()
    class_confirmation = State()
    in_town = State()
    in_market = State()
    in_tavern = State()
    in_dungeon = State()
    in_battle = State()
    in_inventory = State()
    dungeon_room = State()
    battle_turn = State()

# Конфигурация игры
class GameConfig:
    MAX_INVENTORY_SLOTS = 10
    LEVELS_EXP = {
        1: 1000, 2: 2150, 3: 3472, 4: 4992, 5: 6742,
        6: 8753, 7: 11066, 8: 13726, 9: 16785, 10: 20302,
        11: 24348, 12: 29001
    }
    BASE_HEALTH = {
        "warrior": 10, "mage": 6, "rogue": 8, 
        "priest": 8, "archer": 10, "merchant": 8
    }
    HEALTH_PER_LEVEL = {
        "warrior": 6, "mage": 6, "rogue": 5, 
        "priest": 5, "archer": 6, "merchant": 5
    }
    SAVE_COST = 50

# Монстры для подземелий
MONSTERS = {
    "easy": [
        {"name": "Скелет", "health": 15, "damage": "1d6", "exp": 100, "gold": "1d10"},
        {"name": "Гоблин", "health": 12, "damage": "1d4", "exp": 80, "gold": "1d8"},
        {"name": "Волк", "health": 10, "damage": "1d4", "exp": 60, "gold": "1d6"}
    ],
    "medium": [
        {"name": "Орк", "health": 25, "damage": "1d8", "exp": 200, "gold": "2d10"},
        {"name": "Тролль", "health": 30, "damage": "1d10", "exp": 250, "gold": "3d8"},
        {"name": "Призрак", "health": 20, "damage": "1d6", "exp": 180, "gold": "2d6"}
    ],
    "hard": [
        {"name": "Дракон", "health": 50, "damage": "2d10", "exp": 500, "gold": "5d20"},
        {"name": "Демон", "health": 45, "damage": "2d8", "exp": 450, "gold": "4d15"},
        {"name": "Лич", "health": 40, "damage": "2d6", "exp": 400, "gold": "3d20"}
    ]
}

# Предметы для рынка
ITEMS = {
    "consumables": [
        {"name": "Провиант", "price": 10, "type": "food", "stackable": True, "max_stack": 3},
        {"name": "Набор для костра", "price": 15, "type": "camp", "stackable": True, "max_stack": 3},
        {"name": "Зелье здоровья", "price": 25, "type": "potion", "heal": 20},
        {"name": "Зелье маны", "price": 30, "type": "potion", "mana": 15}
    ],
    "weapons": [
        {"name": "Стальной меч", "price": 100, "type": "weapon", "damage": "+1d4", "class": "warrior"},
        {"name": "Дубовый посох", "price": 80, "type": "weapon", "damage": "+1d4", "class": "mage"},
        {"name": "Охотничий лук", "price": 90, "type": "weapon", "damage": "+1d4", "class": "archer"},
        {"name": "Священный молот", "price": 95, "type": "weapon", "damage": "+1d4", "class": "priest"}
    ],
    "armor": [
        {"name": "Кожаная броня", "price": 70, "type": "armor", "defense": 2, "class": "rogue"},
        {"name": "Кольчуга", "price": 120, "type": "armor", "defense": 4, "class": "warrior"},
        {"name": "Мантия мага", "price": 90, "type": "armor", "defense": 1, "class": "mage"},
        {"name": "Роба священника", "price": 85, "type": "armor", "defense": 2, "class": "priest"}
    ]
}

# Квесты
QUESTS = {
    5: {
        "title": "Первый вызов",
        "description": "Победить босса в первом подземелье",
        "reward_exp": 500,
        "reward_gold": 100,
        "required_level": 5
    },
    10: {
        "title": "Испытание мастера", 
        "description": "Победить могущественного врага во втором подземелье",
        "reward_exp": 1000,
        "reward_gold": 250,
        "required_level": 10
    },
    12: {
        "title": "Финальная битва",
        "description": "Победить главного босса и завершить историю",
        "reward_exp": 2000,
        "reward_gold": 500,
        "required_level": 12
    }
}

# Классы персонажей
CLASSES = {
    "warrior": {
        "name": "Мечник",
        "description": "Подобно волнам безбрежного моря, упорно и целеустремленно...",
        "skills": ["Мощный удар", "За защитная стойка", "Огненный меч"],
        "damage": "1d8"
    },
    "mage": {
        "name": "Маг",
        "description": "Жизнь мага - стремление познать что-то новое...",
        "skills": ["Огненный шар", "Ледяная ловушка", "Магический барьер"],
        "damage": "1d6"
    },
    "rogue": {
        "name": "Вор", 
        "description": "Они не жалеют никого...",
        "skills": ["Теневой удар", "Отравленный клинок", "Мгновенное исчезновение"],
        "damage": "1d6"
    },
    "priest": {
        "name": "Послушник",
        "description": "Господь не позволяет своим служителям проливать кровь...",
        "skills": ["Святое исцеление", "Благословение света", "Небесное осуждение"],
        "damage": "1d4"
    },
    "archer": {
        "name": "Лучник",
        "description": "Лучник стремится держаться подальше от противника...",
        "skills": ["Точный выстрел", "Стрела огня", "Двойной выстрел"],
        "damage": "1d8"
    },
    "merchant": {
        "name": "Торговец",
        "description": "Хороший торговец знает, когда и где покупать...",
        "skills": ["Торговый трюк", "Удар купца", "Сделка на грани"],
        "damage": "1d4"
    }
}

# Утилиты для игры
class GameUtils:
    @staticmethod
    def roll_dice(dice_str: str) -> int:
        if 'd' in dice_str:
            parts = dice_str.split('d')
            count = int(parts[0]) if parts[0] else 1
            sides = int(parts[1])
            return sum(random.randint(1, sides) for _ in range(count))
        return int(dice_str)

    @staticmethod
    def calculate_damage(attacker: Any, defender: Any, skill: Optional[str] = None) -> Tuple[int, str]:
        base_damage = GameUtils.roll_dice(attacker.get('damage', '1d4'))
        
        # Критический удар (натуральные 20)
        attack_roll = random.randint(1, 20)
        is_critical = attack_roll == 20
        
        if is_critical:
            base_damage *= 2
            message = "Критический удар! 💥"
        elif attack_roll >= 10:
            message = "Удар попадает! ⚔️"
        else:
            return 0, "Промах! ❌"
        
        # Учет защиты
        defense = defender.get('defense', 0)
        final_damage = max(1, base_damage - defense)
        
        return final_damage, message

# Генератор историй
class StoryGenerator:
    @staticmethod
    async def generate_intro(gender: str, class_name: str, character_name: str) -> str:
        try:
            prompt = f"Создай уникальное вступительное сообщение для RPG игры. Персонаж: {gender}, класс: {class_name}, имя: {character_name}."
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except:
            stories = [
                f"Древнее зло пробуждается. {character_name}, как {class_name}, должен остановить угрозу.",
                f"Королевства в хаосе войны. {character_name} оказывается в центре событий.",
                f"Магические артефакты проявляют силу. {character_name} должен найти их до темных сил."
            ]
            return random.choice(stories)

# Минимальная реализация для тестирования
async def main():
    print("Starting Telegram RPG Bot...")
    
    # Простой тест бота
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer("🎮 Добро пожаловать в RPG игру! Бот успешно запущен!")
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())