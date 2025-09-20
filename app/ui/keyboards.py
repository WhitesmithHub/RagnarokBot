# -*- coding: utf-8 -*-
# app/ui/keyboards.py
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ---------- Пол (INLINE) ----------
def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Мужчина", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Женщина", callback_data="gender_female"),
        ]
    ])

# ---------- Классы (INLINE) ----------
def classes_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗡️ Мечник",    callback_data="class_pick_swordsman"),
            InlineKeyboardButton(text="🔮 Маг",        callback_data="class_pick_mage"),
        ],
        [
            InlineKeyboardButton(text="🗝️ Вор",        callback_data="class_pick_thief"),
            InlineKeyboardButton(text="✨ Послушник",  callback_data="class_pick_acolyte"),
        ],
        [
            InlineKeyboardButton(text="🏹 Лучник",     callback_data="class_pick_archer"),
            InlineKeyboardButton(text="🧾 Торговец",  callback_data="class_pick_merchant"),
        ],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="cancel_class")],
    ])

# ---------- Подтверждение выбора класса (INLINE) ----------
def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_class")],
        [InlineKeyboardButton(text="↩️ Назад",       callback_data="cancel_class")],
    ])

# ---------- Городское меню (REPLY) ----------
def city_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏪 Рынок"), KeyboardButton(text="🍺 Таверна")],
            [KeyboardButton(text="📜 Сюжет"), KeyboardButton(text="🧍 Персонаж")],
            [KeyboardButton(text="🎒 Инвентарь"), KeyboardButton(text="🗺️ Задания")],
            [KeyboardButton(text="⚔️ Подземелье")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
