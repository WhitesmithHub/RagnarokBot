# -*- coding: utf-8 -*-
# app/ui/keyboards.py
from __future__ import annotations

from typing import List

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ---------- СОЗДАНИЕ ПЕРСОНАЖА (reply-клавиатура) ----------

def gender_kb() -> ReplyKeyboardMarkup:
    """Клавиатура выбора пола"""
    rows = [
        [
            KeyboardButton(text="👨 Мужчина"),
            KeyboardButton(text="👩 Женщина"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите пол персонажа"
    )

def classes_kb() -> ReplyKeyboardMarkup:
    """Клавиатура выбора класса"""
    rows = [
        [
            KeyboardButton(text="🗡️ Мечник"),
            KeyboardButton(text="✨ Послушник"),
        ],
        [
            KeyboardButton(text="🔮 Маг"),
            KeyboardButton(text="🏹 Лучник"),
        ],
        [
            KeyboardButton(text="🧾 Торговец"),
            KeyboardButton(text="🗝️ Вор"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите класс персонажа"
    )

def confirm_kb() -> ReplyKeyboardMarkup:
    """Клавиатура подтверждения"""
    rows = [
        [
            KeyboardButton(text="✅ Подтвердить"),
            KeyboardButton(text="❌ Отменить"),
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Подтвердите выбор"
    )

# ---------- ГОРОД (reply-клавиатура) ----------

def city_menu_kb() -> ReplyKeyboardMarkup:
    # Лейблы ДОЛЖНЫ совпадать с хендлерами
    rows = [
        [
            KeyboardButton(text="🛒 Рынок"),
            KeyboardButton(text="🕳️ Подземелья"),
        ],
        [
            KeyboardButton(text="🍺 Таверна"),
            KeyboardButton(text="🧍 Персонаж"),
        ],
        [
            KeyboardButton(text="📦 Инвентарь"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="…"
    )

def back_to_city_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏘️ В город")]],
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
    rows = []
    rows.append([InlineKeyboardButton(text="🔎 Исследовать", callback_data="dng_search")])
    if can_camp:
        rows.append([InlineKeyboardButton(text="🔥 Привал", callback_data="dng_camp")])
    rows.append([InlineKeyboardButton(text="➡️ Идти дальше", callback_data="dng_next")])
    if has_exit:
        rows.append([InlineKeyboardButton(text="⬆️ К выходу", callback_data="dng_escape")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_leave_dungeon_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="✅ Да, уйти", callback_data="dng_leave_yes"),
            InlineKeyboardButton(text="❌ Остаться", callback_data="dng_leave_no"),
        ]
    ]
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
    rows = []
    row = []
    for i, _ in enumerate(keys, start=1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"sk_{i}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="cmb_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
