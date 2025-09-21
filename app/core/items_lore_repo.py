# -*- coding: utf-8 -*-
# app/core/items_lore_repo.py
from __future__ import annotations

import os
import re
import random
from typing import Dict, List, Optional, Tuple

_LORE_CACHE: List[Dict] = []

_THIS_DIR = os.path.dirname(__file__)
_TXT_PATH = os.path.join(_THIS_DIR, "items_lore.txt")

_NAME_RE   = re.compile(r"^\s*Имя:\s*(.+?)\s*$", re.I)
_TYPE_RE   = re.compile(r"^\s*Тип:\s*(.+?)\s*$", re.I)
_WHO_RE    = re.compile(r"^\s*Кто может носить:\s*(.+?)\s*$", re.I)
_RARE_RE   = re.compile(r"^\s*Редкость:\s*(.+?)\s*$", re.I)
_LEVEL_RE  = re.compile(r"^\s*Уровень:\s*(.+?)\s*$", re.I)
_BONUS_RE  = re.compile(r"^\s*Бонус:\s*(.+?)\s*$", re.I)
_PRICE_RE  = re.compile(r"^\s*Цена:\s*(\d+)", re.I)
_DESC_RE   = re.compile(r"^\s*Описание:\s*(.+?)\s*$", re.I)

def _kind_material_from_type(type_line: str) -> Tuple[str, Optional[str]]:
    s = (type_line or "").lower()
    if "роба" in s:
        return "armor", "robe"
    if "тяж" in s or "латы" in s or "кольчуга" in s or "броня" in s:
        return "armor", "heavy"
    if any(w in s for w in ["оружие", "кинжал", "катар", "меч", "лук", "посох", "жезл", "топор", "булава", "молот", "копь", "кастет"]):
        return "weapon", None
    return "misc", None

def _parse_blocks(text: str) -> List[Dict]:
    items: List[Dict] = []
    blocks = re.split(r"\n\s*\n", text)
    for block in blocks:
        name = desc = rare = level = type_line = who = bonus = None
        price: Optional[int] = None

        for line in block.splitlines():
            if not name:
                m = _NAME_RE.match(line);   name  = m.group(1).strip() if m else name
            if not type_line:
                m = _TYPE_RE.match(line);   type_line = m.group(1).strip() if m else type_line
            if who is None:
                m = _WHO_RE.match(line);    who   = m.group(1).strip() if m else who
            if not rare:
                m = _RARE_RE.match(line);   rare  = m.group(1).strip() if m else rare
            if not level:
                m = _LEVEL_RE.match(line);  level = m.group(1).strip() if m else level
            if bonus is None:
                m = _BONUS_RE.match(line);  bonus = m.group(1).strip() if m else bonus
            if price is None:
                m = _PRICE_RE.match(line);  price = int(m.group(1)) if m else price
            if not desc:
                m = _DESC_RE.match(line);   desc  = m.group(1).strip() if m else desc

        if not name:
            continue
        kind, material = _kind_material_from_type(type_line or "")
        if price is None:
            price = 12

        items.append({
            "name": name,
            "kind": "consumable" if "зелье" in (name.lower()) else kind,
            "material": material,
            "price": int(price),
            "rarity": rare,
            "level": level,
            "bonus": bonus,
            "who": who,
            "desc": (desc or "Предмет из старых записей.").strip(),
        })
    return items

def _load_lore() -> List[Dict]:
    global _LORE_CACHE
    if _LORE_CACHE:
        return _LORE_CACHE
    if not os.path.isfile(_TXT_PATH):
        _LORE_CACHE = []
        return _LORE_CACHE
    with open(_TXT_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    _LORE_CACHE = _parse_blocks(text)
    return _LORE_CACHE

def _fits_class(item: Dict, class_key: Optional[str]) -> bool:
    if not class_key:
        return True
    name = (item.get("name") or "").lower()
    kind = item.get("kind")
    material = item.get("material")

    if kind == "weapon":
        if class_key == "swordsman":  return any(w in name for w in ("меч","клинок"))
        if class_key == "archer":     return "лук" in name
        if class_key == "thief":      return any(w in name for w in ("кинжал","катар"))
        if class_key == "mage":       return any(w in name for w in ("посох","жезл"))
        if class_key == "acolyte":    return any(w in name for w in ("булава","молот","посох"))
        if class_key == "merchant":   return any(w in name for w in ("кинжал","булава","молот"))
    if kind == "armor":
        if class_key == "mage":       return material == "robe"
        if class_key in ("thief","archer","merchant"): return material == "leather"
        if class_key == "acolyte":    return material in ("robe","leather")
        if class_key == "swordsman":  return material in ("leather","heavy")
    return True

def sample_random_items(k: int, class_key: Optional[str] = None, exclude_names: Optional[set] = None) -> List[Dict]:
    pool = [x for x in _load_lore() if _fits_class(x, class_key)]
    if not pool:
        return []
    if exclude_names:
        pool = [x for x in pool if (x.get("name") not in exclude_names)]
    k = max(0, min(k, len(pool)))
    return random.sample(pool, k=k) if k else []
