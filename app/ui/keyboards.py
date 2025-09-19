# -*- coding: utf-8 -*-
# app/ui/keyboards.py
from __future__ import annotations
from typing import List, Iterable, Tuple
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ---------- КАМПАНИИ ----------
def campaigns_kb(items: Iterable[Tuple[str, str]]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📜 {title}", callback_data=f"camp:{cid}")]
            for cid, title in items]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def campaign_confirm_kb(campaign_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"campok:{campaign_id}"),
            InlineKeyboardButton(text="↩️ Вернуться",   callback_data="campback"),
        ]]
    )

# ---------- ПОЛ / КЛАССЫ ----------
def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="👩 Женщина", callback_data="gender_female"),
            InlineKeyboardButton(text="👨 Мужчина",  callback_data="gender_male"),
        ]]
    )

def classes_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🗡️ Мечник",   callback_data="class_pick_swordsman"),
            InlineKeyboardButton(text="🔮 Маг",      callback_data="class_pick_mage"),
            InlineKeyboardButton(text="🗝️ Вор",      callback_data="class_pick_thief"),
        ],
        [
            InlineKeyboardButton(text="✨ Послушник", callback_data="class_pick_acolyte"),
            InlineKeyboardButton(text="🏹 Лучник",    callback_data="class_pick_archer"),
            InlineKeyboardButton(text="🧾 Торговец",  callback_data="class_pick_merchant"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_class"),
            InlineKeyboardButton(text="↩️ Назад",       callback_data="cancel_class"),
        ]]
    )

# ---------- ГОРОД (reply) ----------
def city_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🛒 Рынок"),     KeyboardButton(text="🕳️ Подземелья")],
        [KeyboardButton(text="🍺 Таверна"),   KeyboardButton(text="🧍 Персонаж")],
        [KeyboardButton(text="📦 Инвентарь"), KeyboardButton(text="🧾 Задания")],
        [KeyboardButton(text="📜 Сюжет")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="…"
    )

# (на будущее)
def skills_pick_kb(keys: List[str]) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i, _ in enumerate(keys, start=1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"sk_{i}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="cmb_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
