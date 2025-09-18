# -*- coding: utf-8 -*-
# app/features/inventory.py
from __future__ import annotations
from aiogram import Router, F, types
from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb
from app.core.emoji import decorate_item_name

router = Router()

@router.message(F.text.in_(["📦 Инвентарь", "Инвентарь"]))
async def open_inventory(message: types.Message):
    p = get_player(message.from_user.id)
    lines = ["📦 <b>Инвентарь</b>"]
    inv = p.inventory or {}
    if not inv:
        lines.append("Пусто.")
    else:
        for name, cnt in inv.items():
            low = name.lower()
            if any(x in low for x in ["меч","сабл","клинок","кинжал","нож","топор","лук","посох","булав","жезл"]):
                kind = "weapon"
            elif any(x in low for x in ["брон","латы","кольчуг","панцир","роб","ряса","мант"]):
                kind = "armor"
            else:
                kind = "consumable"
            material = "leather" if "кожан" in low else ("robe" if any(x in low for x in ["роб","ряса","мант"]) else None)
            lines.append(f"• {decorate_item_name(name, kind, material)} ×{cnt}")
    await message.answer("\n".join(lines), reply_markup=city_menu_kb())
