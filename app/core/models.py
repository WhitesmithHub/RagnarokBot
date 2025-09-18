# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class Player:
    user_id: int
    # базовые
    gender: str = "male"         # "male"/"female"
    name: str = "Герой"
    class_key: str = "swordsman"
    class_label: str = "🗡️ Мечник"

    # прогресс и характеристики
    level: int = 1
    exp: int = 0
    gold: int = 50

    strength: int = 5
    dexterity: int = 5
    intellect: int = 3
    endurance: int = 3

    max_hp: int = 8
    hp: int = 8

    # мир/локации
    city_name: str = "Златоград"
    world_story: str = ""

    # инвентарь/экип
    inventory: Dict[str, int] = field(default_factory=dict)
    equipment: Dict[str, Optional[str]] = field(default_factory=lambda: {"weapon": None, "armor": None})

    # умения
    abilities_known: Dict[str, int] = field(default_factory=dict)     # имя -> уровень умения
    ability_meta: Dict[str, Dict] = field(default_factory=dict)       # имя -> {emoji,title,type}
    ability_charges: Dict[str, int] = field(default_factory=dict)     # имя -> заряды
