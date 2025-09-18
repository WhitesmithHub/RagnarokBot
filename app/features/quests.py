# -*- coding: utf-8 -*-
# app/features/quests.py
from __future__ import annotations

from aiogram import Router, F, types
from app.ui.keyboards import city_menu_kb

router = Router()


@router.message(F.text.in_(["🧾 Задания", "Задания"]))
async def quests_stub(message: types.Message):
    await message.answer("🧾 <b>Задания</b>\nРаздел в разработке.",
                         reply_markup=city_menu_kb())
