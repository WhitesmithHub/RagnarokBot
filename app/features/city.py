# -*- coding: utf-8 -*-
# app/features/city.py
from __future__ import annotations

from aiogram import types, Router, F

from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb

router = Router(name="city")

async def go_city(message: types.Message) -> None:
    """Показать городское меню для текущего игрока."""
    user_id = message.from_user.id
    p = get_player(user_id)
    if not p:
        await message.answer("Персонаж не найден. Набери /start")
        return

    city = p.city_name or "Город"
    await message.answer(f"🏙 <b>{city}</b>\nКуда отправишься?", reply_markup=city_menu_kb())

# ---------- КНОПКИ ГОРОДА ----------

@router.message(F.text.contains("Сюжет"))
async def story_btn(message: types.Message):
    await message.answer("<i>📖 Сюжет: В разработке</i>")
    await go_city(message)

@router.message(F.text.contains("Персонаж"))
async def character_btn(message: types.Message):
    p = get_player(message.from_user.id)
    if not p:
        await message.answer("Персонаж не найден. Набери /start"); return
    eq = p.equipment or {}
    lines = [
        "👤 <b>Персонаж</b>",
        f"Имя: {p.name}",
        f"Класс: {p.class_label or p.class_key}",
        f"Уровень: {getattr(p, 'level', 1)}",
        f"Золото: {p.gold}",
        f"HP: {p.hp}/{p.max_hp}",
        "",
        "⚙️ <b>Снаряжение</b>",
        f"Оружие: {eq.get('weapon') or '—'}",
        f"Броня: {eq.get('armor') or '—'}",
    ]
    await message.answer("\n".join(lines), reply_markup=city_menu_kb())

@router.message(F.text.contains("Инвентарь"))
async def inventory_btn(message: types.Message):
    p = get_player(message.from_user.id)
    if not p:
        await message.answer("Персонаж не найден. Набери /start"); return
    inv = p.inventory or {}
    if not inv:
        await message.answer("🎒 Инвентарь пуст.", reply_markup=city_menu_kb()); return
    lines = ["🎒 <b>Инвентарь</b>"]
    for name, cnt in inv.items():
        lines.append(f"• {name} × {cnt}")
    await message.answer("\n".join(lines), reply_markup=city_menu_kb())

@router.message(F.text.contains("Задания"))
async def quests_btn(message: types.Message):
    await message.answer("<i>🧭 Задания: В разработке</i>")
    await go_city(message)

@router.message(F.text.contains("Подземелье"))
async def dungeon_btn(message: types.Message):
    await message.answer("<i>⚔️ Подземелье: В разработке</i>")
    await go_city(message)

# На всякий случай универсальный «вернуться в город»
@router.message(F.text.contains("Город"))
async def back_to_city_legacy(message: types.Message):
    await go_city(message)
