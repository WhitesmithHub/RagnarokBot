# -*- coding: utf-8 -*-
# app/features/character.py
from __future__ import annotations

from typing import Dict, List

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb

router = Router()

def ability_uses_for_level(key: str, level: int, class_key: str) -> int:
    """
    Обязательная утилита: макс. заряды умения на уровне.
    (Здесь оставь твою существующую логику; пример базовой.)
    """
    table = {
        1: 3,
        2: 4,
        3: 5,
    }
    return table.get(level, 3)

@router.message(F.text.in_(["🧍 Персонаж", "Персонаж"]))
async def open_character(message: types.Message, state: FSMContext):
    p = get_player(message.from_user.id)

    lines: List[str] = [
        "🧍 <b>Персонаж</b>",
        f"🏷️ Имя: {p.name}",
        f"🪪 Класс: {getattr(p, 'class_emoji', '⚔️')} {getattr(p, 'class_title', p.class_label)}",
        f"⭐️ Уровень: {p.level}",
        f"🔰 Опыт: {p.exp} / {p.exp_to_next}",
        "",
        "📘 <b>Умения</b>",
        "Изученные:",
    ]

    if p.abilities_known:
        charges: Dict[str, int] = getattr(p, "ability_charges", {})
        for key, lvl in p.abilities_known.items():
            meta = p.ability_meta.get(key, {"emoji": "✨", "title": key, "uses_by_level": {lvl: ability_uses_for_level(key, lvl, p.class_key)}})
            max_uses = meta.get("uses_by_level", {}).get(lvl, ability_uses_for_level(key, lvl, p.class_key))
            cur_uses = charges.get(key, max_uses)
            lines.append(f"• {meta['emoji']} {meta['title']} — ур. {lvl}  (исп.: {cur_uses}/{max_uses})")
    else:
        lines.append("—")

    # Кандидаты на изучение/улучшение — если у тебя есть функция available_abilities, используй её
    if hasattr(p, "available_abilities"):
        lines.append("\nМожно изучить/улучшить:")
        options = p.available_abilities()
        for i, opt in enumerate(options, start=1):
            emoji = opt.get("emoji", "✨")
            title = opt.get("title", opt.get("key", "Умение"))
            lvl = opt.get("next_level", 1)
            uses_by_level = opt.get("uses_by_level", {})
            after_uses = uses_by_level.get(lvl, "∞")
            tag = "после повышения" if opt.get("already_known") else "при изучении"
            lines.append(f"{i}. {emoji} {title} — {('улучшить до ' + str(lvl)) if opt.get('already_known') else 'новое'} "
                         f"(заряды {tag}: {after_uses})")

    await message.answer("\n".join(lines), reply_markup=city_menu_kb())
