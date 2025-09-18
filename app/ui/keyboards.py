# -*- coding: utf-8 -*-
# app/ui/keyboards.py
from __future__ import annotations

from typing import List

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ---------- СОЗДАНИЕ ПЕРСОНАЖА (inline) ----------

def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🧔 Мужчина", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женщина", callback_data="gender_female"),
        ]]
    )

def classes_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🗡️ Мечник", callback_data="class_pick_swordsman"),
            InlineKeyboardButton(text="✨ Послушник", callback_data="class_pick_acolyte"),
        ],
        [
            InlineKeyboardButton(text="🔮 Маг", callback_data="class_pick_mage"),
            InlineKeyboardButton(text="🏹 Лучник", callback_data="class_pick_archer"),
        ],
        [
            InlineKeyboardButton(text="🧾 Торговец", callback_data="class_pick_merchant"),
            InlineKeyboardButton(text="🗝️ Вор", callback_data="class_pick_thief"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_class"),
            InlineKeyboardButton(text="↩️ Выбрать другой", callback_data="cancel_class"),
        ]]
    )

# ---------- ГОРОД (reply-клавиатура) ----------
# Убрали «🏘️ В город». Добавили «🧾 Задания».

def city_menu_kb() -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🛒 Рынок"), KeyboardButton(text="🕳️ Подземелья")],
        [KeyboardButton(text="🍺 Таверна"), KeyboardButton(text="🧍 Персонаж")],
        [KeyboardButton(text="📦 Инвентарь"), KeyboardButton(text="🧾 Задания")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="…"
    )

# Оставляем на случай, если где-то используется
def back_to_city_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🧾 Задания")]],
        resize_keyboard=True
    )

# ---------- ПОДЗЕМЕЛЬЯ (inline) ----------

def dungeon_pick_kb(names: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for i, name in enumerate(names, start=1):
        rows.append([InlineKeyboardButton(text=f"{i}. {name}", callback_data=f"dng_pick_{i}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="dng_back_city")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def room_actions_kb(*, can_camp: bool, has_exit: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="🔎 Исследовать", callback_data="dng_search")]]
    if can_camp:
        rows.append([InlineKeyboardButton(text="🔥 Привал", callback_data="dng_camp")])
    rows.append([InlineKeyboardButton(text="➡️ Идти дальше", callback_data="dng_next")])
    if has_exit:
        rows.append([InlineKeyboardButton(text="⬆️ К выходу", callback_data="dng_escape")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_leave_dungeon_kb() -> InlineKeyboardMarkup:
    rows = [[
        InlineKeyboardButton(text="✅ Да, уйти", callback_data="dng_leave_yes"),
        InlineKeyboardButton(text="❌ Остаться", callback_data="dng_leave_no"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- БОЙ (inline) ----------

def combat_actions_kb(has_skills: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_skills:
        rows.append([InlineKeyboardButton(text="✨ Умения", callback_data="cmb_skills")])
    rows.append([InlineKeyboardButton(text="⚔️ Атака", callback_data="cmb_attack")])
    rows.append([InlineKeyboardButton(text="🛡️ Защита", callback_data="cmb_defend")])
    rows.append([InlineKeyboardButton(text="🥾 Сбежать", callback_data="cmb_flee")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

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
