# app/core/persistence.py
import os, json
from typing import Optional
from .models import Player
from .stats import max_hp_for

SAVES_DIR = "saves"

def ensure_dir():
    if not os.path.isdir(SAVES_DIR):
        os.makedirs(SAVES_DIR, exist_ok=True)

def save_to_disk(p: Player) -> str:
    ensure_dir()
    path = os.path.join(SAVES_DIR, f"{p.user_id}.json")
    data = {
        "user_id": p.user_id,
        "gender": p.gender,
        "name": p.name,
        "class_key": p.class_key,
        "class_label": p.class_label,
        "level": p.level,
        "xp": p.xp,
        "gold": p.gold,
        "hp": p.hp,
        "max_hp": p.max_hp,
        "equipment": p.equipment,
        "inventory": p.inventory,
        "location": p.location,
        "city_name": p.city_name,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def load_from_disk(user_id: int) -> Optional[Player]:
    path = os.path.join(SAVES_DIR, f"{user_id}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    p = Player(
        user_id=d["user_id"],
        gender=d["gender"],
        name=d["name"],
        class_key=d["class_key"],
        class_label=d["class_label"],
        level=d.get("level", 1),
        xp=d.get("xp", 0),
        gold=d.get("gold", 0),
        hp=d.get("hp", 0),
        max_hp=d.get("max_hp", 0),
        equipment=d.get("equipment", {"weapon": None, "armor": None}),
        inventory=d.get("inventory", {}),
        location=d.get("location", "city"),
        city_name=d.get("city_name", "Безымянный город"),
    )
    # sanity check
    if p.max_hp <= 0:
        p.max_hp = max_hp_for(p.level, p.class_key)
    if p.hp <= 0 or p.hp > p.max_hp:
        p.hp = p.max_hp
    return p
