# -*- coding: utf-8 -*-
# app/features/creation.py
from __future__ import annotations
from typing import Dict

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.core.storage import get_player, save_player, Player
from app.ui.keyboards import (
    gender_kb, classes_kb, confirm_kb, city_menu_kb
)
from app.core.campaign import (
    get_epic, arrival_city_name, arrival_text
)

router = Router()

# ---------- FSM:   ----------
class CreateFlow(StatesGroup):
    ask_name = State()

#    
CLASS_LABELS = {
    "swordsman": " ",
    "acolyte":   " ",
    "mage":      " ",
    "archer":    " ",
    "merchant":  " ",
    "thief":     " ",
}

#  
CLASS_DESCRIPTIONS = {
    "swordsman": "   ...        .",
    "mage": "     - ...   ,   .",
    "thief": "    ...    ,     .",
    "acolyte": " ...     .",
    "archer": "   ...     .",
    "merchant": "  ...      .",
}

#  (/ + )
CLASS_ABILITIES: Dict[str, Dict[str, Dict[str, str]]] = {
    "swordsman": {
        "active": {
            " ": "     .",
            " ": "    +  1 .",
            " ": "    + 2 .",
        },
        "passive": {
            " ": " +10%  .",
            " ":   " +5%   .",
        },
        "start": (" ", ""),
    },
    "mage": {
        "active": {
            " ": "  .",
            " ": "   1 .",
            " ": "    .",
        },
        "passive": {
            " ": " +10%  .",
            " ": " +5%   .",
        },
        "start": (" ", ""),
    },
    "thief": {
        "active": {
            " ": "  +  .",
            " ": "   - .",
            " ": "   +10 HP.",
        },
        "passive": {
            "": "   .",
            "  ": " +10%   .",
        },
        "start": (" ", ""),
    },
    "acolyte": {
        "active": {
            " ": "  30% HP.",
            " ": " +  2 .",
            " ": "  .",
        },
        "passive": {
            "  ": " +10%   .",
            " ": " -  .",
        },
        "start": (" ", ""),
    },
    "archer": {
        "active": {
            " ": "  .",
            " ": "  2 .",
            " ": "  .",
        },
        "passive": {
            "˸  ": " +10% .",
            " ": " +10% ,   .",
        },
        "start": (" ", ""),
    },
    "merchant": {
        "active": {
            " ": "   - .",
            " ": " .",
            "  ": " +15%  1 .",
        },
        "passive": {
            " ": "   .",
            " ": " +  .",
        },
        "start": (" ", ""),
    },
}

def fallback_stats_for_class(class_key: str) -> Dict[str, int]:
    if class_key == "mage":
        base = {"str": 2, "dex": 3, "int": 7, "end": 4}
    elif class_key == "archer":
        base = {"str": 2, "dex": 7, "int": 3, "end": 4}
    elif class_key == "swordsman":
        base = {"str": 7, "dex": 3, "int": 2, "end": 4}
    elif class_key == "thief":
        base = {"str": 3, "dex": 7, "int": 3, "end": 3}
    elif class_key == "acolyte":
        base = {"str": 3, "dex": 3, "int": 5, "end": 5}
    else:  # merchant
        base = {"str": 3, "dex": 4, "int": 5, "end": 4}
    return base

def starting_hp_for_class(class_key: str) -> int:
    if class_key in ("swordsman", "archer"):
        return 10
    if class_key in ("acolyte", "thief", "merchant"):
        return 8
    if class_key == "mage":
        return 6
    return 8

# ----------  ----------
@router.callback_query(F.data.regexp(r"^gender_(male|female)$"))
async def pick_gender(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    gender = "male" if cb.data == "gender_male" else "female"  #  
    await state.update_data(gender=gender)
    await state.set_state(CreateFlow.ask_name)
    await cb.message.answer("  ?")

# ----------  ----------
@router.message(CreateFlow.ask_name, F.text)
async def handle_name(message: types.Message, state: FSMContext):
    name_raw = message.text.strip()
    bad = any(x in name_raw.lower() for x in ["", "", "", "", "fuck"])
    if bad or len(name_raw) < 2 or len(name_raw) > 20:
        await message.answer(" .  , 220 ,  .")
        return
    await state.update_data(name=name_raw)
    await message.answer(" :", reply_markup=classes_kb())

# ----------  /  ----------
@router.callback_query(F.data.regexp(r"^class_pick_(\w+)$"))
async def pick_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    class_key = cb.data.split("_")[-1]
    if class_key not in CLASS_LABELS:
        await cb.message.answer("  .")
        return

    stats = fallback_stats_for_class(class_key)
    label = CLASS_LABELS[class_key]
    desc = CLASS_DESCRIPTIONS[class_key]
    abil = CLASS_ABILITIES[class_key]
    start_name, start_emoji = abil["start"]

    act_lines = [f" {v}" for v in abil["active"].values()]
    pas_lines = [f" {v}" for v in abil["passive"].values()]

    text = (
        f"{label}\n{desc}\n\n"
        f"<b>:</b>\n"
        f" : {stats['str']}\n"
        f" : {stats['dex']}\n"
        f" : {stats['int']}\n"
        f" : {stats['end']}\n\n"
        f"<b></b>\n\n"
        f"<b>:</b>\n" + "\n".join(act_lines) + "\n\n"
        f"<b>:</b>\n" + "\n".join(pas_lines) + "\n\n"
        f"<b>     :</b> {start_emoji} {start_name}"
    )
    await state.update_data(class_key=class_key, class_label=label, stats=stats)
    await cb.message.answer(text, reply_markup=confirm_kb())

@router.callback_query(F.data == "cancel_class")
async def cancel_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.answer(" :", reply_markup=classes_kb())

@router.callback_query(F.data == "confirm_class")
async def confirm_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    name = data.get("name", "")
    gender_raw = data.get("gender", "")
    class_key = data.get("class_key")
    class_label = data.get("class_label")
    campaign_id = data.get("campaign_id")
    stats = data.get("stats") or fallback_stats_for_class(class_key or "swordsman")
    if not class_key:
        await cb.message.answer("  .")
        return

    nm = (name or "").strip().lower()
    fem_by_name = nm.endswith(("","","","","","","","","","","",""))
    gender = gender_raw if gender_raw in ("male", "female") else ("female" if fem_by_name else "male")

    p = get_player(cb.from_user.id) or Player(user_id=cb.from_user.id)

    p.user_id = cb.from_user.id
    p.gender = gender
    p.name = name
    p.class_key = class_key
    p.class_label = class_label

    p.level = 1
    p.exp = 0
    p.gold = 50
    p.inventory = {}
    p.equipment = {"weapon": None, "armor": None}

    p.strength = stats["str"]
    p.dexterity = stats["dex"]
    p.intellect = stats["int"]
    p.endurance = stats["end"]

    p.max_hp = starting_hp_for_class(class_key)
    p.hp = p.max_hp

    abil = CLASS_ABILITIES[class_key]
    start_name, start_emoji = abil["start"]
    p.abilities_known = {start_name: 1}
    p.ability_meta = {start_name: {"emoji": start_emoji, "title": start_name, "type": "active"}}
    p.ability_charges = {start_name: 3}

    epic = get_epic(campaign_id)
    city = arrival_city_name(campaign_id)
    p.city_name = city
    p.world_story = epic

    save_player(p)

    await cb.message.answer(epic)
    arrive = arrival_text(name, gender, campaign_id)
    await cb.message.answer(arrive)
    await cb.message.answer(" ?", reply_markup=city_menu_kb())

    await state.clear()
