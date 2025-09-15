# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List
import random

@dataclass
class Monster:
    name: str
    emoji: str
    level: int
    hp: int
    ac: int          # класс брони (цель броска на попадание)
    attack: str      # '1d8+2'
    to_hit: int      # модификатор к попаданию
    xp: int

THEMES = {
    "Замок Теней": [
        Monster("Скелет", "💀", 1, 10, 11, "1d6+1", 3, 60),
        Monster("Зомби", "🧟", 2, 14, 10, "1d8+1", 2, 90),
        Monster("Демон Мрака", "😈", 3, 18, 12, "1d10+2", 4, 140),
    ],
    "Пещеры Безмолвия": [
        Monster("Пещерный паук", "🕷️", 1, 9, 12, "1d6+1", 3, 55),
        Monster("Каменный голем", "🗿", 3, 20, 13, "1d10+2", 5, 150),
        Monster("Тень", "🌫️", 2, 12, 12, "1d8+0", 4, 100),
    ],
    "Катакомбы Предков": [
        Monster("Призрак", "👻", 2, 12, 12, "1d8+1", 4, 110),
        Monster("Мумия", "🤐", 3, 18, 12, "1d10+1", 4, 150),
        Monster("Костяной маг", "🦴", 3, 16, 11, "1d8+3", 5, 160),
    ],
}

BOSSES = {
    "Замок Теней": Monster("Лорд Костей", "🦴👑", 5, 40, 14, "2d8+3", 6, 500),
    "Пещеры Безмолвия": Monster("Матка Пауков", "🕷️👑", 5, 42, 14, "2d6+4", 6, 520),
    "Катакомбы Предков": Monster("Хранитель Пепла", "🧱👑", 5, 45, 15, "2d8+4", 7, 540),
}

def roll_monster(theme: str, depth: int) -> Monster:
    picks = THEMES.get(theme) or THEMES["Замок Теней"]
    m = random.choice(picks)
    # легкий скейлинг по глубине
    extra = max(0, depth // 3)
    return Monster(m.name, m.emoji, m.level+extra, m.hp+2*extra, m.ac+min(1, extra), m.attack, m.to_hit+extra, m.xp+20*extra)

def theme_names_from_story(story: str) -> List[str]:
    """
    На основе лора вернём до 3 тем. Простая эвристика + рандом.
    """
    names = list(THEMES.keys())
    random.shuffle(names)
    return names[:3]
