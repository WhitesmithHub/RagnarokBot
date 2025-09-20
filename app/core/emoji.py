# -*- coding: utf-8 -*-
# app/core/emoji.py

from __future__ import annotations

def _weapon_emoji(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["меч", "сабл", "клинок"]): return "🗡️"
    if any(x in n for x in ["лук", "стрел"]): return "🏹"
    if any(x in n for x in ["булав", "молот", "кузнеч"]): return "🔨"
    if any(x in n for x in ["топор", "секир"]): return "🪓"
    if any(x in n for x in ["кинжал", "нож"]): return "🔪"
    if any(x in n for x in ["посох", "жезл", "жезел"]): return "🍢"
    if any(x in n for x in ["копь", "пика"]): return "🥢"
    return "⚔️"

def _armor_emoji(material: str | None, name: str) -> str:
    n = (name or "").lower()
    if material == "leather" or "кожан" in n: return "🧥"
    if material == "robe" or any(x in n for x in ["роб", "ряса", "мант"]): return "👘"
    return "🛡️"

def _misc_emoji(name: str) -> str:
    n = name.lower()
    if "зелье" in n or "эликсир" in n: return "🍷"  # эмодзи для лечебного зелья
    if any(x in n for x in ["провиант","еда","паёк","пайок","мяс","хлеб"]): return "🍗"
    if any(x in n for x in ["костра","костёр","костер","кэмп","camp"]): return "🌳"
    if any(x in n for x in ["камн","самоцвет","драгоц","руда","железо"]): return "💎"
    return "📦"

def decorate_item_name(name: str, kind: str | None, material: str | None = None) -> str:
    """
    Вернёт строку '<emoji> <name>' по типу предмета.
    """
    if kind == "weapon":
        e = _weapon_emoji(name)
    elif kind == "armor":
        e = _armor_emoji(material, name)
    elif kind == "camp":
        e = "🌳"
    elif kind == "consumable":
        e = _misc_emoji(name)
    else:
        e = _misc_emoji(name)
    return f"{e} {name}"

# --- Бейджи редкости ---
RARITY_ICONS = {
    "Обычный": "⚪",
    "Редкий": "🔵",
    "Легендарный": "🌟",
}

def rarity_badge(rarity: str) -> str:
    r = (rarity or "").strip()
    key = (
        "Обычный" if r.lower().startswith("обыч") else
        "Редкий" if r.lower().startswith("редк") else
        "Легендарный" if r.lower().startswith("леген") else
        r
    )
    icon = RARITY_ICONS.get(key, "")
    return f"{icon} {key}" if icon else key
