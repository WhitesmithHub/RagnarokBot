# -*- coding: utf-8 -*-
# app/core/emoji.py
import re

# Базовые словари по ключевым словам в названии
WEAPON_EMOJI = {
    r"меч|сабля|клинок|рапира": "🗡️",
    r"лук|арбалет": "🏹",
    r"посох|жезл|жезлы|жезель|сфера": "🍢",   # по запросу: посох = 🍢
    r"булава|молот|кистень|цеп|пернач": "🔨",
    r"топор|секира|бердыш": "🪓",
    r"кинжал|нож(?!ницы)": "🔪",
}

ARMOR_MATERIAL_EMOJI = {
    r"кожан": "🧥",      # кожаная/кожаный/кожаное
    r"роб|ряса|мант": "👘",  # роба/ряса/мантия
}
ARMOR_GENERIC = "🛡️"

FOOD_KEYS = [r"провиант|еда|пай|паёк|рацион|хлеб|мясо|сухпай"]
CAMP_KEYS = [r"костра|костёр|привал|палатка|лагер"]

def _match_any(name: str, patterns: dict[str, str]) -> str | None:
    for rx, em in patterns.items():
        if re.search(rx, name, flags=re.IGNORECASE):
            return em
    return None

def _match_list(name: str, patterns: list[str]) -> bool:
    return any(re.search(rx, name, flags=re.IGNORECASE) for rx in patterns)

def emoji_for_item(name: str, kind: str | None = None, material_hint: str | None = None) -> str:
    """
    Подбирает подходящий эмодзи для предмета по названию.
    kind — опционально: 'weapon' | 'armor' | 'consumable' | 'camp' | 'misc'
    material_hint — опционально: 'leather'|'robe'
    """
    n = (name or "").strip()

    # Consumables
    if kind == "consumable" or _match_list(n, FOOD_KEYS):
        return "🍗"
    if kind == "camp" or _match_list(n, CAMP_KEYS):
        return "🌳"

    # Weapons
    if kind == "weapon" or _match_any(n, WEAPON_EMOJI):
        # если явно оружие — ищем конкретный вид
        em = _match_any(n, WEAPON_EMOJI)
        return em or "⚔"

    # Armor
    if kind == "armor" or re.search(r"брон|кольчуг|латы|доспех|панцир", n, re.I):
        # материал приоритетнее
        if material_hint == "leather" or re.search(r"кожан", n, re.I):
            return ARMOR_MATERIAL_EMOJI[r"кожан"]
        if material_hint == "robe" or re.search(r"роб|ряса|мант", n, re.I):
            return ARMOR_MATERIAL_EMOJI[r"роб|ряса|мант"]
        return ARMOR_GENERIC

    # Попытка угадать по словам оружия
    em_weap = _match_any(n, WEAPON_EMOJI)
    if em_weap:
        return em_weap

    # По умолчанию
    return "📦"

def decorate_item_name(name: str, kind: str | None = None, material_hint: str | None = None) -> str:
    """ Возвращает строку 'EMOJI Название' """
    return f"{emoji_for_item(name, kind, material_hint)} {name}"
