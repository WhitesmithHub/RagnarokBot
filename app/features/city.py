# -*- coding: utf-8 -*-
# app/features/city.py
from __future__ import annotations

from aiogram import types, Router, F

from app.core.storage import get_player
from app.ui.keyboards import city_menu_kb

router = Router()

async def go_city(message: types.Message):
    """
    Безопасный показ «экрана города».
    Берём user_id из chat.id (в личке == id пользователя), чтобы не падать в колбэках.
    """
    user_id = message.chat.id
    p = get_player(user_id)
    if not p:
        await message.answer("Сначала создай персонажа: /start")
        return
    city = p.city_name or "Город"
    await message.answer(f"🏘️ {city}\nКуда отправимся?", reply_markup=city_menu_kb())

# (Опционально) если когда-то вернём кнопку «В город»
@router.message(F.text.in_(["🏘️ В город"]))
async def back_to_city(message: types.Message):
    await go_city(message)
