# -*- coding: utf-8 -*-
# app/ui/keyboards.py
from __future__ import annotations
from typing import List, Iterable, Tuple
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ---------- РљРђРњРџРђРќРР ----------
def campaigns_kb(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"рџ“њ {title}", callback_data=f"camp:{cid}")]
            for cid, title in items]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def campaign_confirm_kb(campaign_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="вњ… РџРѕРґС‚РІРµСЂРґРёС‚СЊ", callback_data=f"campok:{campaign_id}"),
            InlineKeyboardButton(text="в†©пёЏ Р’РµСЂРЅСѓС‚СЊСЃСЏ",   callback_data="campback"),
        ]]
    )

# ---------- РџРћР› / РљР›РђРЎРЎР« ----------
def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="рџ‘© Р–РµРЅС‰РёРЅР°", callback_data="gender_female"),
            InlineKeyboardButton(text="рџ‘Ё РњСѓР¶С‡РёРЅР°",  callback_data="gender_male"),
        ]]
    )

def classes_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="рџ—ЎпёЏ РњРµС‡РЅРёРє",   callback_data="class_pick_swordsman"),
            InlineKeyboardButton(text="рџ”® РњР°Рі",      callback_data="class_pick_mage"),
            InlineKeyboardButton(text="рџ—ќпёЏ Р’РѕСЂ",      callback_data="class_pick_thief"),
        ],
        [
            InlineKeyboardButton(text="вњЁ РџРѕСЃР»СѓС€РЅРёРє", callback_data="class_pick_acolyte"),
            InlineKeyboardButton(text="рџЏ№ Р›СѓС‡РЅРёРє",    callback_data="class_pick_archer"),
            InlineKeyboardButton(text="рџ§ѕ РўРѕСЂРіРѕРІРµС†",  callback_data="class_pick_merchant"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="вњ… РџРѕРґС‚РІРµСЂРґРёС‚СЊ", callback_data="confirm_class"),
            InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ",       callback_data="cancel_class"),
        ]]
    )

# ---------- Р“РћР РћР” (reply) ----------
def city_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="рџ›’ Р С‹РЅРѕРє"),     KeyboardButton(text="рџ•іпёЏ РџРѕРґР·РµРјРµР»СЊСЏ")],
        [KeyboardButton(text="рџЌє РўР°РІРµСЂРЅР°"),   KeyboardButton(text="рџ§Ќ РџРµСЂСЃРѕРЅР°Р¶")],
        [KeyboardButton(text="рџ“¦ РРЅРІРµРЅС‚Р°СЂСЊ"), KeyboardButton(text="рџ§ѕ Р—Р°РґР°РЅРёСЏ")],
        [KeyboardButton(text="рџ“њ РЎСЋР¶РµС‚")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="вЂ¦"
    )

# (РЅР° Р±СѓРґСѓС‰РµРµ)
def skills_pick_kb(keys: List[str]) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i, _ in enumerate(keys, start=1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"sk_{i}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ", callback_data="cmb_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)



