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

# Полные описания классов с умениями
CLASSES = {
    "warrior": {
        "name": "Мечник",
        "description": "Подобно волнам безбрежного моря, упорно и целеустремленно, с открытой душой и сердцем мечник идет по пути познания силы, оттачивая свое мастерство и набираясь опыта. В бою мечник полагается на свое мастерство обращения с холодным оружием и храбрость.",
        "skills": {
            "Активные умения": [
                "Мощный удар – Мечник наносит мощный удар, наносящий высокий урон противнику.",
                "Защитная стойка – Мечник встает в защитную стойку, повышая свою броню на 50% на 1 ход.",
                "Огненный меч – Мечник наделяет свой меч огненной магией, увеличивая урон на 25% и нанося дополнительные повреждения огнем в течение 2 ходов."
            ],
            "Пассивные умения": [
                "Боевая выносливость – Увеличивает максимальное здоровье на 10%.",
                "Ударный инстинкт – Увеличивает шанс критического удара на 5% при каждом успешном блоке."
            ]
        },
        "damage": "1d8"
    },
    "mage": {
        "name": "Маг",
        "description": "Жизнь мага - стремление познать что-то новое. Именно из-за этого они готовы покинуть библиотеки и отправиться в путь, чтобы стать еще сильней, добыв то, что гораздо дороже денег - знание. Познав силы природы и научившись пользоваться ими, маги способны поражать своих врагов огнем, льдом, разрядами молний и обращать их в камень.",
        "skills": {
            "Активные умения": [
                "Огненный шар – Маг создает огненный шар, который наносит урон в радиусе взрыва.",
                "Ледяная ловушка – Маг создает ловушку на земле, замораживающую врагов, которые на нее наступят, на 1 ход.",
                "Магический барьер – Маг создает барrier, который поглощает часть магического урона от следующей атаки."
            ],
            "Пассивные умения": [
                "Энергия воли – Увеличивает максимальное здоровье на 10%.",
                "Магический поток – После использования магии шанс на критический урон увеличивается на 5% на 1 ход."
            ]
        },
        "damage": "1d6"
    },
    "rogue": {
        "name": "Вор", 
        "description": "Они не жалеют никого, и мало кто знает, что у Воров есть свой кодекс чести и их Гильдия всегда поможет своим членам. В бою вор полагается не на силу удара, а на точность и с легкостью уклоняется от атак противника.",
        "skills": {
            "Активные умения": [
                "Теневой удар – Вор наносит удар из тени, наносящий критический урон и уменьшающий урон врага на 10% на 2 хода.",
                "Отравленный клинок – Вор наносит удар отравленным клинком, который вызывает отравление и снижает защиту цели.",
                "Мгновенное исчезновение – Вор скрывается в тени, избегая следующей атаки и восстанавливая 10 единиц здоровья."
            ],
            "Пассивные умения": [
                "Невидимость – Вор начинает бой скрытым, увеличивая шанс уклонения от атак на 20%.",
                "Быстрота в действиях – Увеличивает шанс критического удара на 10%."
            ]
        },
        "damage": "1d6"
    },
    "priest": {
        "name": "Послушник",
        "description": "Господь не позволяет своим служителям проливать кровь, но выход все-таки был найден. В бою послушники полагаются не только на слово Божье, но и на любую булаву или другое тупое оружие. Правда, пользуются они им редко, ибо их задача - прежде всего нести добро людям, а не воевать.",
        "skills": {
            "Активные умения": [
                "Молитва силы – Послушник молится, восстанавливая себе 20% здоровья и увеличивая защиту на 10% на 1 ход.",
                "Священное исцеление – Послушник призывает свет для исцеления, восстанавливая 30% здоровья себе.",
                "Божественная защита – Послушник использует защиту веры, уменьшая получаемый урон на 20% на 2 хода."
            ],
            "Пассивные умения": [
                "Смирение – Увеличивает физическую защиту на 10%.",
                "Вера в свет – Каждый успешный удар увеличивает сопротивление магии на 5% на 1 ход (стекание)."
            ]
        },
        "damage": "1d4"
    },
    "archer": {
        "name": "Лучник",
        "description": "В бою лучник стремится держаться подальше от противника, полагаясь на зоркий глаз и тугой лук. Лучник откровенно слаб в ближнем бою, хотя разве сможет кто-нибудь подойти к хорошему стрелку?",
        "skills": {
            "Активные умения": [
                "Точный выстрел – Лучник выпускает стрелу с высокой точностью, наносящую увеличенный урон.",
                "Стрела огня – Лучник выпускает стрелу, которая наносит урон и оставляет след огня, продолжая наносить урон врагам на протяжении 2 ходов.",
                "Двойный выстрел – Лучник стреляет двумя стрелами одновременно, нанося двойной урон."
            ],
            "Пассивные умения": [
                "Легкость в движении – Увеличивает шанс уклонения от атак на 10%.",
                "Природный инстинкт – Увеличивает шанс критического удара на 10% в начале боя, если первый ход за вами."
            ]
        },
        "damage": "1d8"
    },
    "merchant": {
        "name": "Торговец",
        "description": "Если вы считаете, что купив подешевле, а продав подороже, вы станете хорошим торговцем, вы ошибаетесь. Хороший торговец знает, что, когда и где покупать и кому продавать. Нагрузив свои тележки товаром, Торговцы странствуют по миру, чтобы любой мог купить то, что ему нужно, даже вдали от городов.",
        "skills": {
            "Активные умения": [
                "Торговый трюк – Торговец манипулирует предметами, чтобы нанести урон врагу и снизить его защиту на 10% на 1 ход.",
                "Удар купца – Торговец использует тяжелый предмет для удара, нанося урон и оглушая врага на 1 ход.",
                "Сделка на грани – Торговец повышает шанс на критический удар на 15% на 1 ход."
            ],
            "Пассивные умения": [
                "Блестящий оратор – Скидка на любые товары на рынке на 10%.",
                "Торговый ум – Каждый успешный удар увеличивает вероятность на критический удар на 5%."
            ]
        },
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

# Генератор текстов с помощью ChatGPT
class TextGenerator:
    @staticmethod
    async def generate_text(prompt: str, max_tokens: int = 200) -> str:
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты мастер повествования в RPG игре. Создай эпические, подробные описания событий."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Ошибка генерации текста: {e}")
            # Fallback текст
            return "Что-то пошло не так при генерации описания. Продолжаем приключение!"

    @staticmethod
    async def generate_intro(gender: str, class_name: str, character_name: str) -> str:
        prompt = f"""Создай эпическое вступительное сообщение для RPG игры длиной 5-7 предложений. 
Персонаж: {gender}, класс: {class_name}, имя: {character_name}.
История должна быть глобальной: древнее зло, война королевств, магические артефакты.
Сделай текст захватывающим и уникальным."""
        return await TextGenerator.generate_text(prompt, 250)

    @staticmethod
    async def generate_town_description(character_name: str, class_name: str) -> str:
        prompt = f"""Опиши город в RPG игре. {character_name} ({class_name}) прибывает в город. 
Опиши атмосферу города, жителей, последние слухи и интересные события.
Сделай описание живым и immersive, 4-6 предложений."""
        return await TextGenerator.generate_text(prompt)

    @staticmethod
    async def generate_dungeon_intro(dungeon_name: str, difficulty: str, character_name: str) -> str:
        difficulty_ru = {"easy": "легко", "medium": "средне", "hard": "сложно"}.get(difficulty, difficulty)
        prompt = f"""Опиши вход в подземелье {dungeon_name} сложности {difficulty_ru}. 
Персонаж {character_name} стоит перед входом. Опиши его ощущения, внешний вид подземелья, предчувствия.
Сделай текст напряженным и атмосферным, 3-5 предложений."""
        return await TextGenerator.generate_text(prompt)

    @staticmethod
    async def generate_room_description(room_type: str, dungeon_name: str, character_name: str, details: Dict = None) -> str:
        prompts = {
            "monster": f"""Опиши встречу с монстром в подземелье {dungeon_name}. 
Персонаж {character_name} входит в комнату и видит {details['monster_name']}. 
Опиши монстра, атмосферу комнаты, чувства персонажа.""",
            "trap": f"""Опиши ловушку в подземелье {dungeon_name}. 
Персонаж {character_name} активирует ловушку. Опиши саму ловушку, как она срабатывает, реакцию персонажа.""",
            "treasure": f"""Опиши находку сокровищ в подземелье {dungeon_name}. 
Персонаж {character_name} находит сундук. Опиши содержимое, атмосферу комнаты, эмоции персонажа.""",
            "rest": f"""Опиши безопасное место для отдыха в подземелье {dungeon_name}. 
Персонаж {character_name} находит укромное место. Опиши обстановку, чувство безопасности, процесс отдыха.""",
            "empty": f"""Опиши пустую комнату в подземелье {dungeon_name}. 
Персонаж {character_name} осматривает комнату. Опиши атмосферу, детали комнату, мысли персонажа."""
        }

        prompt = prompts.get(room_type, f"Опиши комнату в подземелье {dungeon_name}.")
        return await TextGenerator.generate_text(prompt)

    @staticmethod
    async def generate_battle_description(monster_name: str, character_name: str, class_name: str) -> str:
        prompt = f"""Опиши начало битвы с {monster_name} в стиле RPG. 
Персонаж {character_name} ({class_name}) готовится к бою. 
Опиши монстра, атмосферу боя, первые действия противников."""
        return await TextGenerator.generate_text(prompt)

# Генератор подземелий
class DungeonGenerator:
    @staticmethod
    def generate_dungeon(level: int) -> Dict:
        difficulty = "easy" if level < 5 else "medium" if level < 10 else "hard"
        themes = ["Замок", "Пещера", "Лес", "Храм", "Гробница"]

        return {
            "id": str(uuid.uuid4()),
            "name": f"{random.choice(themes)} Уровня {level}",
            "difficulty": difficulty,
            "rooms": random.randint(5, 10),
            "current_room": 0,
            "monsters_defeated": 0,
            "rooms_cleared": 0
        }

    @staticmethod
    def generate_room(dungeon: Dict, player_level: int) -> Dict:
        room_types = ["empty", "monster", "treasure", "trap", "rest"]
        weights = [30, 40, 15, 10, 5]  # Вероятности комнат

        room_type = random.choices(room_types, weights=weights, k=1)[0]
        room_data = {"type": room_type, "description": ""}

        if room_type == "monster":
            difficulty = dungeon["difficulty"]
            monster = random.choice(MONSTERS[difficulty]).copy()
            room_data["monster"] = monster
            room_data["monster_name"] = monster["name"]

        elif room_type == "treasure":
            gold = random.randint(10, 50) * player_level
            room_data["gold"] = gold

        elif room_type == "trap":
            damage = random.randint(5, 15)
            room_data["damage"] = damage

        elif room_type == "rest":
            heal = random.randint(10, 30)
            room_data["heal"] = heal

        return room_data

# Система сохранения
class SaveSystem:
    @staticmethod
    def save_character(character: Dict):
        try:
            os.makedirs("saves", exist_ok=True)
            with open(f"saves/{character['user_id']}.json", 'w') as f:
                json.dump(character, f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")

    @staticmethod
    def load_character(user_id: int) -> Optional[Dict]:
        try:
            with open(f"saves/{user_id}.json", 'r') as f:
                return json.load(f)
        except:
            return None

# Класс персонажа
class Character:
    def __init__(self, user_id: int, name: str, gender: str, class_type: str):
        self.user_id = user_id
        self.name = name
        self.gender = gender
        self.class_type = class_type
        self.level = 1
        self.exp = 0
        self.gold = 100
        self.inventory = []
        self.equipment = {"weapon": None, "armor": None}
        self.location = "town"
        self.max_health = self.calculate_max_health()
        self.current_health = self.max_health
        self.current_dungeon = None
        self.current_battle = None
        self.quests = {"active": None, "completed": []}
        self.story_intro = None
        self.last_save = datetime.now().isoformat()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "gender": self.gender,
            "class_type": self.class_type,
            "level": self.level,
            "exp": self.exp,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "current_health": self.current_health,
            "max_health": self.max_health,
            "quests": self.quests,
            "last_save": self.last_save
        }

    @classmethod
    def from_dict(cls, data: Dict):
        character = cls(data['user_id'], data['name'], data['gender'], data['class_type'])
        character.level = data['level']
        character.exp = data['exp']
        character.gold = data['gold']
        character.inventory = data['inventory']
        character.equipment = data['equipment']
        character.current_health = data['current_health']
        character.max_health = data['max_health']
        character.quests = data['quests']
        character.last_save = data['last_save']
        return character

    def calculate_max_health(self) -> int:
        base = GameConfig.BASE_HEALTH.get(self.class_type, 10)
        per_level = GameConfig.HEALTH_PER_LEVEL.get(self.class_type, 5)
        return base + (self.level - 1) * per_level

    def add_exp(self, amount: int) -> str:
        self.exp += amount
        if self.exp >= GameConfig.LEVELS_EXP.get(self.level, 999999):
            return self.level_up()
        return ""

    def level_up(self) -> str:
        self.level += 1
        old_max = self.max_health
        self.max_health = self.calculate_max_health()
        self.current_health = self.max_health
        return f"🎉 Уровень up! Теперь ты {self.level} уровня!\n❤️ Здоровье: {self.current_health}/{self.max_health}"

# Менеджер игры
class GameManager:
    def __init__(self):
        self.characters: Dict[int, Character] = {}

    def get_character(self, user_id: int) -> Optional[Character]:
        if user_id not in self.characters:
            # Попытка загрузить из сохранения
            saved_data = SaveSystem.load_character(user_id)
            if saved_data:
                self.characters[user_id] = Character.from_dict(saved_data)
        return self.characters.get(user_id)

    async def create_character(self, user_id: int, name: str, gender: str, class_type: str):
        character = Character(user_id, name, gender, class_type)
        character.story_intro = await TextGenerator.generate_intro(gender, CLASSES[class_type]["name"], name)
        self.characters[user_id] = character
        SaveSystem.save_character(character.to_dict())
        return character

    def save_character(self, user_id: int):
        if user_id in self.characters:
            SaveSystem.save_character(self.characters[user_id].to_dict())

game_manager = GameManager()

# Клавиатуры
def get_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👨 Мужчина"), KeyboardButton(text="👩 Женщина")]],
        resize_keyboard=True
    )

def get_class_keyboard():
    buttons = []
    for class_id in CLASSES.keys():
        buttons.append([KeyboardButton(text=CLASSES[class_id]["name"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_town_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Рынок"), KeyboardButton(text="🍺 Таверна")],
            [KeyboardButton(text="🏔️ Подземелье"), KeyboardButton(text="📊 Статус")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="💾 Сохраниться")]
        ],
        resize_keyboard=True
    )

def get_battle_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚔️ Атаковать"), KeyboardButton(text="🛡️ Защита")],
            [KeyboardButton(text="🧪 Использовать предмет"), KeyboardButton(text="🏃 Сбежать")]
        ],
        resize_keyboard=True
    )

def get_dungeon_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚶 Идти дальше"), KeyboardButton(text="🏕️ Сделать привал")],
            [KeyboardButton(text="🔍 Осмотреть комнату"), KeyboardButton(text="🏃 Вернуться в город")]
        ],
        resize_keyboard=True
    )

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Сбрасываем состояние
    await state.clear()

    character = game_manager.get_character(message.from_user.id)
    if character:
        # Персонаж уже существует
        town_description = "Добро пожаловать обратно в город! Жители рады видеть вас снова."
        await message.answer(
            f"{town_description}\n\nДобро пожаловать обратно, {character.name}! 🎮", 
            reply_markup=get_town_keyboard()
        )
        await state.set_state(GameStates.in_town)
        return

    # Новый игрок
    welcome_text = """
🌟 *Добро пожаловать в мир приключений!* 🌟

Ты вступаешь на путь, где каждое твое решение имеет значение, а каждый шаг может привести к величайшей славе или к гибели. 

💫 *Как это работает?*
• Твой путь — это история, которая будет развиваться в зависимости от твоих решений
• Каждая битва, каждое испытание будут случайно сгенерированы
• Твоя судьба будет определяться в процессе игры!

🔮 *Что тебя ждёт?*
• Сражения с могущественными врагами
• Тайны, которые скрыты в самых темных уголках
• Необычные союзники и загадочные враги
• Великие выборы, которые могут изменить ход истории

💬 *Готов к действию?* Выбери свой пол и начни путь к величию!
"""

    await message.answer(welcome_text, reply_markup=get_gender_keyboard(), parse_mode="Markdown")
    await state.set_state(GameStates.choosing_gender)

@dp.message(GameStates.choosing_gender, F.text.in_(["👨 Мужчина", "👩 Женщина"]))
async def process_gender(message: types.Message, state: FSMContext):
    gender = "male" if "Мужчина" in message.text else "female"
    await state.update_data(gender=gender)
    await message.answer("Отлично! Как тебя зовут? Напиши своё имя:")
    await state.set_state(GameStates.choosing_name)

@dp.message(GameStates.choosing_gender)
async def invalid_gender(message: types.Message):
    await message.answer("Пожалуйста, выбери пол используя кнопки ниже:", reply_markup=get_gender_keyboard())

@dp.message(GameStates.choosing_name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 20:
        await message.answer("Имя должно быть от 2 до 20 символов. Попробуй еще раз:")
        return

    # Простая проверка на недопустимые слова
    forbidden_words = ["мат", "fuck", "shit", "asshole"]
    if any(word in name.lower() for word in forbidden_words):
        await message.answer("Имя содержит недопустимые слова. Выбери другое имя:")
        return

    await state.update_data(name=name)
    await message.answer("Отличное имя! Теперь выбери класс:", reply_markup=get_class_keyboard())
    await state.set_state(GameStates.choosing_class)

@dp.message(GameStates.choosing_class, F.text.in_([cls["name"] for cls in CLASSES.values()]))
async def process_class(message: types.Message, state: FSMContext):
    class_name = message.text
    class_id = next(key for key, value in CLASSES.items() if value["name"] == class_name)

    class_info = CLASSES[class_id]
    await state.update_data(class_type=class_id)

    # Форматируем умения для отображения
    skills_text = "⚡️ *Навыки:*\n\n"
    for skill_type, skills in class_info["skills"].items():
        skills_text += f"*{skill_type}:*\n"
        for skill in skills:
            skills_text += f"• {skill}\n"
        skills_text += "\n"

    # Клавиатура подтверждения
    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="↩️ Выбрать другой класс")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        f"🎯 *{class_info['name']}*\n\n"
        f"{class_info['description']}\n\n"
        f"{skills_text}"
        f"*Подтверждаешь выбор?*",
        reply_markup=confirm_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(GameStates.class_confirmation)

@dp.message(GameStates.choosing_class)
async def invalid_class(message: types.Message):
    await message.answer("Пожалуйста, выбери класс используя кнопки ниже:", reply_markup=get_class_keyboard())

@dp.message(GameStates.class_confirmation, F.text == "✅ Подтвердить")
async def confirm_class(message: types.Message, state: FSMContext):
    data = await state.get_data()
    character = await game_manager.create_character(
        message.from_user.id,
        data['name'],
        data['gender'],
        data['class_type']
    )

    await message.answer(
        f"🎊 *Персонаж создан!*\n\n"
        f"👤 Имя: {character.name}\n"
        f"🚻 Пол: {'Мужчина' if character.gender == 'male' else 'Женщина'}\n"
        f"⚔️ Класс: {CLASSES[character.class_type]['name']}\n"
        f"⭐ Уровень: {character.level}\n"
        f"❤️ Здоровье: {character.current_health}/{character.max_health}\n"
        f"💰 Золото: {character.gold}\n\n"
        f"{character.story_intro}",
        reply_markup=get_town_keyboard(),
        parse_mode="Markdown"
    )

    town_description = await TextGenerator.generate_town_description(character.name, CLASSES[character.class_type]["name"])
    await message.answer(f"{town_description}\n\nТы находишься в городе. Куда отправишься?")
    await state.set_state(GameStates.in_town)

@dp.message(GameStates.class_confirmation, F.text == "↩️ Выбрать другой класс")
async def change_class(message: types.Message, state: FSMContext):
    await message.answer("Выбери класс:", reply_markup=get_class_keyboard())
    await state.set_state(GameStates.choosing_class)

@dp.message(GameStates.class_confirmation)
async def invalid_confirmation(message: types.Message):
    confirm_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Подтвердить"), KeyboardButton(text="↩️ Выбрать другой класс")]
        ],
        resize_keyboard=True
    )
    await message.answer("Пожалуйста, подтверди выбор класса или выбери другой:", reply_markup=confirm_keyboard)

# Остальные обработчики остаются без изменений...

# Запуск бота
async def main():
    logger.info("Бот запускается...")
    # Создаем папку для сохранений
    os.makedirs("saves", exist_ok=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())