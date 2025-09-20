# -*- coding: utf-8 -*-
# app/core/emoji.py
from __future__ import annotations

def _weapon_emoji(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["РјРµС‡", "СЃР°Р±Р»", "РєР»РёРЅРѕРє"]): return "рџ—ЎпёЏ"
    if any(x in n for x in ["Р»СѓРє", "СЃС‚СЂРµР»"]): return "рџЏ№"
    if any(x in n for x in ["Р±СѓР»Р°РІ", "РјРѕР»РѕС‚", "РєСѓР·РЅРµС‡"]): return "рџ”Ё"
    if any(x in n for x in ["С‚РѕРїРѕСЂ", "СЃРµРєРёСЂ"]): return "рџЄ“"
    if any(x in n for x in ["РєРёРЅР¶Р°Р»", "РЅРѕР¶", "РєР°С‚Р°СЂ"]): return "рџ”Є"
    if any(x in n for x in ["РїРѕСЃРѕС…", "Р¶РµР·Р»", "Р¶РµР·РµР»"]): return "рџЌў"  # РєР°Рє Рё РїСЂРѕСЃРёР»Рё СЂР°РЅРµРµ
    if any(x in n for x in ["РєРѕРїСЊ", "РїРёРєР°"]): return "рџҐў"
    return "вљ”пёЏ"

def _armor_emoji(material: str | None, name: str) -> str:
    n = (name or "").lower()
    if material == "leather" or "РєРѕР¶Р°РЅ" in n: return "рџ§Ґ"
    if material == "robe" or any(x in n for x in ["СЂРѕР±", "СЂСЏСЃР°", "РјР°РЅС‚"]): return "рџ‘"
    return "рџ›ЎпёЏ"

def _misc_emoji(name: str) -> str:
    n = name.lower()
    # рџ”ґ Р·РµР»СЊРµ Р»РµС‡РµРЅРёСЏ вЂ” СЃС‚СЂРѕРіРѕ рџЌ·
    if "Р·РµР»СЊРµ" in n or "Р»РµС‡РµРЅ" in n or "potion" in n:
        return "рџЌ·"
    if any(x in n for x in ["РїСЂРѕРІРёР°РЅС‚","РµРґР°","РїР°С‘Рє","РїР°Р№РѕРє","РјСЏСЃ","С…Р»РµР±"]): return "рџЌ—"
    if any(x in n for x in ["РєРѕСЃС‚СЂР°","РєРѕСЃС‚С‘СЂ","РєРѕСЃС‚РµСЂ","РєСЌРјРї","camp"]): return "рџЊі"
    if any(x in n for x in ["РєР°РјРЅ","СЃР°РјРѕС†РІРµС‚","РґСЂР°РіРѕС†","СЂСѓРґР°","Р¶РµР»РµР·Рѕ"]): return "рџ’Ћ"
    return "рџ“¦"

def decorate_item_name(name: str, kind: str | None, material: str | None = None) -> str:
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃС‚СЂРѕРєСѓ РІРёРґР° '<emoji> <name>'.
    kind в€€ {"weapon","armor","consumable","camp"} Р»РёР±Рѕ None.
    material в€€ {"leather","robe"} Р»РёР±Рѕ None.
    """
    if kind == "weapon":
        e = _weapon_emoji(name)
    elif kind == "armor":
        e = _armor_emoji(material, name)
    elif kind == "camp":
        e = "рџЊі"
    elif kind == "consumable":
        e = _misc_emoji(name)
    else:
        e = _misc_emoji(name)
    return f"{e} {name}"

# --- Р РµРґРєРѕСЃС‚СЊ РїСЂРµРґРјРµС‚РѕРІ (Р±РµР№РґР¶Рё) ---
RARITY_ICONS = {
    "РћР±С‹С‡РЅС‹Р№": "вљЄ",
    "Р РµРґРєРёР№": "рџ”µ",
    "Р›РµРіРµРЅРґР°СЂРЅС‹Р№": "рџЊџ",
}

def rarity_badge(rarity: str) -> str:
    r = (rarity or "").strip()
    key = (
        "РћР±С‹С‡РЅС‹Р№" if r.lower().startswith("РѕР±С‹С‡") else
        "Р РµРґРєРёР№" if r.lower().startswith("СЂРµРґРє") else
        "Р›РµРіРµРЅРґР°СЂРЅС‹Р№" if r.lower().startswith("Р»РµРіРµРЅ") else
        r
    )
    icon = RARITY_ICONS.get(key, "")
    return f"{icon} {key}" if icon else key



