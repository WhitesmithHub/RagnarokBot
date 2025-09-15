# -*- coding: utf-8 -*-
# app/features/city.py
from __future__ import annotations

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from ..core.storage import get_player, save_player
from ..ui.keyboards import city_menu_kb, back_to_city_kb

router = Router()

@router.message(F.text == "🏘️ В город")
async def back_to_city(message: types.Message, state: FSMContext):
    """Возврат в город"""
    await state.clear()
    player = get_player(message.from_user.id)
    
    if not player:
        await message.answer("Сначала создайте персонажа командой /start")
        return
    
    await message.answer(
        f"🏘️ <b>{player.name}</b> возвращается в город.\n\n"
        f"💰 Золото: <b>{player.gold}</b>\n"
        f"❤️ Здоровье: <b>{player.hp}/{player.max_hp}</b>\n"
        f"⭐ Уровень: <b>{player.level}</b>\n\n"
        f"Что будем делать?",
        reply_markup=city_menu_kb()
    )

@router.message(F.text.in_(["🛒 Рынок", "🕳️ Подземелья", "🍺 Таверна", "🧍 Персонаж", "📦 Инвентарь"]))
async def city_navigation(message: types.Message):
    """Навигация по городу"""
    player = get_player(message.from_user.id)
    
    if not player:
        await message.answer("Сначала создайте персонажа командой /start")
        return
    
    text = message.text
    
    if text == "🛒 Рынок":
        await message.answer("Переходим на рынок...", reply_markup=back_to_city_kb())
    elif text == "🕳️ Подземелья":
        await message.answer("Выбираем подземелье...", reply_markup=back_to_city_kb())
    elif text == "🍺 Таверна":
        await message.answer("Идем в таверну...", reply_markup=back_to_city_kb())
    elif text == "🧍 Персонаж":
        await message.answer("Просматриваем персонажа...", reply_markup=back_to_city_kb())
    elif text == "📦 Инвентарь":
        await message.answer("Открываем инвентарь...", reply_markup=back_to_city_kb())