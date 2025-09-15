# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, Optional

CLASS_HP = {
    "swordsman": (10, 6),
    "archer": (10, 6),
    "rogue": (8, 5),
    "merchant": (8, 5),
    "acolyte": (8, 5),
    "mage": (6, 6),
}

@dataclass
class Player:
    user_id: int
    gender: str = "male"
    name: str = "Герой"
    class_key: str = "swordsman"
    class_label: str = "Мечник"

    level: int = 1
    exp: int = 0
    gold: int = 50

    # Базовое здоровье
    hp: int = 10
    max_hp: int = 10

    # Мир
    city_name: str = "Безымянный город"
    world_story: str = ""

    # Характеристики
    strength: int = 4
    dexterity: int = 4
    intellect: int = 4
    endurance: int = 4

    inventory: Dict[str, int] = field(default_factory=dict)
    equipment: Dict[str, Optional[str]] = field(default_factory=lambda: {"weapon": None, "armor": None})

    # Умения
    abilities_known: Dict[str, int] = field(default_factory=dict)   # key -> level
    abilities_pool: list[str] = field(default_factory=list)

    def init_combat_stats(self):
        base, per = CLASS_HP.get(self.class_key, (10, 6))
        # Выносливость даёт доп. здоровье (по 1 за каждую ед.)
        self.max_hp = base + (self.level - 1) * per + max(0, self.endurance)
        self.hp = min(self.hp, self.max_hp) if self.hp else self.max_hp
