# -*- coding: utf-8 -*-
# app/features/character.py
from __future__ import annotations
from aiogram import Router, F, types

from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb

router = Router()

_DIGIT_EMOJI = {0:"0️⃣",1:"1️⃣",2:"2️⃣",3:"3️⃣",4:"4️⃣",5:"5️⃣",6:"6️⃣",7:"7️⃣",8:"8️⃣",9:"9️⃣"}

def _num_to_emoji(n: int) -> str:
    return "".join(_DIGIT_EMOJI[int(d)] for d in str(n))

def _character_text(p) -> str:
    need = 100 * p.level
    skills_active = [k for k,v in (p.ability_meta or {}).items() if v.get("type")=="active"]
    skills_passive = [k for k,v in (p.ability_meta or {}).items() if v.get("type")=="passive"]
    act = "Активные: " + (", ".join(skills_active) if skills_active else "—")
    pas = "Пассивные: " + (", ".join(skills_passive) if skills_passive else "—")
    return (
        "🧍 <b>Персонаж</b>\n"
        f"Имя: {p.name}\n"
        f"Класс: {p.class_label}\n"
        f"Уровень: {_num_to_emoji(p.level)}\n"
        f"Опыт: {p.exp} / {need}\n\n"
        f"Характеристики:\n"
        f"  💪 Сила: {p.strength}\n"
        f"  🏃 Ловкость: {p.dexterity}\n"
        f"  🧠 Интеллект: {p.intellect}\n"
        f"  🫀 Выносливость: {p.endurance}\n"
        f"❤️ HP: {p.hp}/{p.max_hp}\n"
        f"Оружие: {p.equipment.get('weapon') or '—'} | Броня: {p.equipment.get('armor') or '—'}\n\n"
        f"{act}\n{pas}"
    )

@router.message(F.text.in_(["🧍 Персонаж", "Персонаж"]))
async def show_character(message: types.Message):
    p = get_player(message.from_user.id)
    await message.answer(_character_text(p), reply_markup=city_menu_kb())
