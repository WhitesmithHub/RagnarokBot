# -*- coding: utf-8 -*-
# app/features/city.py
from __future__ import annotations

from aiogram import types, Router, F

from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb

router = Router()

async def go_city(message: types.Message):
    """
       .
     user_id  chat.id (  == id ),     .
    """
    user_id = message.chat.id
    p = get_player(user_id)
    if not p:
        await message.answer("  : /start")
        return
    city = p.city_name or ""
    await message.answer(f" {city}\n ?", reply_markup=city_menu_kb())

# ()  -    
@router.message(F.text.in_(["  "]))
async def back_to_city(message: types.Message):
    await go_city(message)
