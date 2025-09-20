# -*- coding: utf-8 -*-
from __future__ import annotations

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from app.core.campaign import welcome_text, campaigns_index, get_brief, get_epic
from app.ui.keyboards import campaigns_kb, campaign_confirm_kb, gender_kb

UNAVAILABLE = {"plague", "dragon"}


router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(campaign_id=None)
    items = campaigns_index()
    await message.answer(welcome_text())
    await message.answer("Выбери кампанию:", reply_markup=campaigns_kb(items))

@router.callback_query(F.data.startswith("camp:"))
async def on_pick_campaign(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    camp_id = cb.data.split(":", 1)[1]
    text = get_epic(camp_id) if camp_id in UNAVAILABLE else get_brief(camp_id)
    await cb.message.answer(text, reply_markup=campaign_confirm_kb(camp_id))

@router.callback_query(F.data.startswith("campok:"))
async def on_campaign_confirm(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    camp_id = cb.data.split(":", 1)[1]
    if camp_id in UNAVAILABLE:
        await state.update_data(campaign_id=None)
        await cb.message.answer("Кампания не доступна в данный момент. Следите за обновлениями!")
        items = campaigns_index()
        await cb.message.answer("Выбери кампанию:", reply_markup=campaigns_kb(items))
        return

    await state.update_data(campaign_id=camp_id)
    await cb.message.answer("Кто ты?", reply_markup=gender_kb())

@router.callback_query(F.data == "campback")
async def on_campaigns_back(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    items = campaigns_index()
    await cb.message.answer("Выбери кампанию:", reply_markup=campaigns_kb(items))

@router.callback_query(F.data.startswith("campok:"))
async def on_campaign_confirm(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer("Кампания выбрана")
    camp_id = cb.data.split(":", 1)[1]
    await state.update_data(campaign_id=camp_id)
    await cb.message.answer("Кто ты?", reply_markup=gender_kb())
