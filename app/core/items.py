from dataclasses import dataclass
from typing import Dict, List, Optional
import random

MAX_SLOTS = 10  # максимум слотов инвентаря

@dataclass(frozen=True)
class Item:
    id: str
    name: str
    price: int
    stackable: bool = False
    stack_max: int = 1
    type: str = "misc"           # weapon | armor | consumable | misc
    desc: str = ""
    # характеристики
    attack: int = 0              # бонус к урону (для оружия)
    defense: int = 0             # бонус к защите (для брони)
    # категорийность для ограничений
    weapon_cat: Optional[str] = None   # sword | dagger | bow | staff | mace …
    armor_cat: Optional[str] = None    # light | medium | heavy

# ---- КАТАЛОГ ----
CATALOG: Dict[str, Item] = {
    "proviant": Item(
        id="proviant", name="Провиант", price=8,
        stackable=True, stack_max=3, type="consumable",
        desc="Простой дорожный паёк."
    ),
    "campkit": Item(
        id="campkit", name="Набор для костра", price=15,
        stackable=True, stack_max=3, type="consumable",
        desc="Даст возможность привала в подземелье."
    ),
    "sabre": Item(
        id="sabre", name="Простая сабля", price=25,
        stackable=False, type="weapon",
        desc="Надёжное клинковое оружие.", attack=1, weapon_cat="sword"
    ),
    "leather": Item(
        id="leather", name="Кожаная броня", price=22,
        stackable=False, type="armor",
        desc="Лёгкая защита от ударов.", defense=1, armor_cat="light"
    ),
    "shortbow": Item(
        id="shortbow", name="Короткий лук", price=24,
        stackable=False, type="weapon",
        desc="Базовое луковое оружие.", attack=1, weapon_cat="bow"
    ),
    "staff": Item(
        id="staff", name="Деревянный посох", price=20,
        stackable=False, type="weapon",
        desc="Простой магический фокус.", attack=1, weapon_cat="staff"
    ),
    "mace": Item(
        id="mace", name="Булава послушника", price=23,
        stackable=False, type="weapon",
        desc="Удобна для сокрушительных ударов.", attack=1, weapon_cat="mace"
    ),
    "dagger": Item(
        id="dagger", name="Кинжал", price=18,
        stackable=False, type="weapon",
        desc="Лёгок и быстр.", attack=1, weapon_cat="dagger"
    ),
}

# Всегда в наличии на рынке
ALWAYS_IN_STOCK = ["proviant", "campkit"]

# ---- КЛАССОВЫЕ ОГРАНИЧЕНИЯ ----
# какие категории оружия может носить базовый класс
CLASS_WEAPON_ALLOW: Dict[str, set] = {
    "swordsman": {"sword"},     # мечник — меч
    "mage": {"staff"},          # маг — посох
    "archer": {"bow"},          # лучник — луки
    "rogue": {"dagger"},        # вор — кинжалы
    "acolyte": {"mace"},        # послушник — булавы
    "merchant": {"dagger"},     # торговец — что-то простое
}
# какие типы брони может носить базовый класс
CLASS_ARMOR_ALLOW: Dict[str, set] = {
    "swordsman": {"light", "medium"},
    "mage": {"light"},
    "archer": {"light"},
    "rogue": {"light"},
    "acolyte": {"light", "medium"},   # по ТЗ — тяжёлую нельзя
    "merchant": {"light"},
}

def generate_market(seed: int | None = None) -> List[Item]:
    """
    Генерирует ассортимент рынка:
    - Всегда включает Провиант и Набор для костра
    - Плюс 3–5 случайных позиции из каталога (без дублей)
    """
    rng = random.Random(seed)
    pool = [i for i in CATALOG.keys() if i not in ALWAYS_IN_STOCK]
    rng.shuffle(pool)
    extra = pool[:rng.randint(3, 5)]
    ids = ALWAYS_IN_STOCK + extra
    return [CATALOG[i] for i in ids]
