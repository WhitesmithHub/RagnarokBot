# -*- coding: utf-8 -*-
# app/core/items_lore_repo.py
from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Tuple
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class LoreItem:
    name: str
    type: str                   # : " (/)"
    allowed_classes: List[str]  # ["","",...]
    rarity: str                 # "" | "" | ""
    level: Tuple[int, int]      # (min, max)
    description: str

DATA_TXT = Path(__file__).resolve().parents[1] / "data" / "items_lore.txt"

_BLOCK_RE = re.compile(
    r":\s*(?P<name>.+?)\s+"
    r":\s*(?P<type>.+?)\s+"
    r"  :\s*(?P<who>.+?)\s+"
    r":\s*(?P<rarity>.+?)\s+"
    r":\s*(?P<lvl_min>\d+)\s*-\s*(?P<lvl_max>\d+)\s+"
    r":\s*(?P<desc>.+?)\s*(?=(?:\n|\r|\Z):|\Z)",
    re.DOTALL | re.IGNORECASE,
)

def _clean_list(s: str) -> List[str]:
    parts = re.split(r"[;,]", s)
    return [p.strip().lower() for p in parts if p.strip()]

def _norm_rarity(r: str) -> str:
    rl = (r or "").strip().lower()
    if rl.startswith(""): return ""
    if rl.startswith(""): return ""
    if rl.startswith(""): return ""
    return (r or "").strip()

def _parse_text(text: str) -> List[LoreItem]:
    items: List[LoreItem] = []
    for m in _BLOCK_RE.finditer(text):
        items.append(
            LoreItem(
                name=m.group("name").strip(),
                type=m.group("type").strip(),
                allowed_classes=_clean_list(m.group("who")),
                rarity=_norm_rarity(m.group("rarity")),
                level=(int(m.group("lvl_min")), int(m.group("lvl_max"))),
                description=" ".join(m.group("desc").split()),
            )
        )
    return items

@lru_cache(maxsize=1)

# ...       ...

def _candidate_paths() -> list[Path]:
    here = Path(__file__).resolve()
    # 1)    (     )
    p1 = here.with_name("items_lore.txt")
    # 2)  app/data/
    p2 = here.parents[1] / "data" / "items_lore.txt"
    return [p1, p2]

def _read_first_existing() -> str | None:
    for p in _candidate_paths():
        try:
            if p.exists():
                return p.read_text(encoding="utf-8")
        except Exception:
            continue
    return None

@lru_cache(maxsize=1)
def get_all_lore_items() -> list[LoreItem]:
    """
          (app/core/items_lore.txt),
      app/data/items_lore.txt.     [].
    """
    text = _read_first_existing()
    if not text:
        return []
    try:
        return _parse_text(text)
    except Exception:
        return []
