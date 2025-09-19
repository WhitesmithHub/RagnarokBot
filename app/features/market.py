# -*- coding: utf-8 -*-
# app/features/market.py
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player

# Если модуль эмодзи недоступен — используем простой титл
try:
    from app.core.emoji import decorate_item_name
except Exception:
    def decorate_item_name(name: str, kind: Optional[str] = None, material: Optional[str] = None) -> str:
        return name

router = Router(name="market")

# user_id -> [(name, price), ...] для продажи (нумерация)
_SALE_CACHE: Dict[int, List[Tuple[str, int]]] = {}

# ---------- ДАННЫЕ МАГАЗИНА ----------

def _base_pool() -> List[Dict]:
    """Базовый пул товаров рынка."""
    return [
        # расходники / лагерь
        {"name": "Зелье лечения", "kind": "consumable", "price": 8,  "desc": "Восстанавливает часть здоровья.", "max_stack": 3},
        {"name": "Полевой набор",  "kind": "camp",       "price": 15, "desc": "Набор для отдыха в дороге.",      "max_stack": 3},

        # оружие
        {"name": "Железный меч",   "kind": "weapon", "price": 25, "desc": "Простой, но надёжный клинок.", "dmg": "+1"},
        {"name": "Дубинка",        "kind": "weapon", "price": 18, "desc": "Тяжёлая рукоять для ближнего боя.", "dmg": "+1"},
        {"name": "Посох ученика",  "kind": "weapon", "price": 20, "desc": "Лёгкий посох для начинающих магов.", "material": "robe", "dmg": "+1"},
        {"name": "Кинжал",         "kind": "weapon", "price": 23, "desc": "Лёгкое скрытное оружие.", "dmg": "+1"},
        {"name": "Короткий лук",   "kind": "weapon", "price": 28, "desc": "Удобен для охоты и разведки.", "dmg": "+1"},

        # броня
        {"name": "Кожаная куртка", "kind": "armor",  "price": 22, "desc": "Гибкая защита из выделанной кожи.", "def": "+1", "material": "leather"},
        {"name": "Тканая мантия",  "kind": "armor",  "price": 19, "desc": "Лёгкая мантия для магических занятий.", "def": "+1", "material": "robe"},
    ]

def _roll_shop_items() -> List[Dict]:
    """
    Формируем витрину: 5 предметов, обязательно 2 базовых (лечилка + полевой набор) + 3 случайных.
    """
    pool = _base_pool()
    must = [next(x for x in pool if x["name"] == "Зелье лечения"),
            next(x for x in pool if x["name"] == "Полевой набор")]
    rest = [x for x in pool if x["name"] not in ("Зелье лечения", "Полевой набор")]
    random.shuffle(rest)
    return must + rest[:3]

def _market_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить", callback_data="m_buy"),
         InlineKeyboardButton(text="💰 Продать", callback_data="m_sell")],
    ])

def _buy_pick_kb(count: int) -> InlineKeyboardMarkup:
    nums, rows = [], []
    for i in range(1, count + 1):
        nums.append(InlineKeyboardButton(text=str(i), callback_data=f"m_b_{i}"))
        if len(nums) == 5:
            rows.append(nums); nums = []
    if nums:
        rows.append(nums)
    rows.append([InlineKeyboardButton(text="↩️ Назад к рынку", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _confirm_kb(idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Купить", callback_data=f"m_conf_{idx}")],
        [InlineKeyboardButton(text="↩️ Назад к рынку", callback_data="m_back")],
    ])

def _sell_pick_kb(n: int) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i in range(1, n + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"m_s_{i}"))
        if len(row) == 5:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="↩️ Назад к рынку", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def format_item_line(entry: Dict, index: Optional[int] = None) -> str:
    name = entry["name"]; price = entry["price"]
    desc = entry.get("desc", ""); kind = entry.get("kind"); material = entry.get("material")
    title = decorate_item_name(name, kind, material)
    max_part = f" (MAX: {entry['max_stack']})" if entry.get("max_stack") else ""
    head = f"{index}. {title} — {price} зол.{max_part}" if index else f"{title} — {price} зол.{max_part}"

    extra = []
    if "dmg" in entry: extra.append(f"⚔ Урон: {entry['dmg']}")
    if "def" in entry: extra.append(f"🛡 Защита: {entry['def']}")
    stats_line = ("\n" + "\n".join(extra)) if extra else ""

    body = desc.strip() if desc else ""
    return f"{head}\n{body}{stats_line}".strip()

# ---------- ВХОД В РЫНОК ----------

@router.message(F.text.contains("Рынок"))
async def open_market(message: types.Message):
    """Открыть рынок из городского меню."""
    p = get_player(message.from_user.id)
    shop = getattr(p, "shop_items", None)
    if not shop:
        shop = _roll_shop_items()
        p.shop_items = shop
        save_player(p)

    lines = ["🛒 <b>Рынок</b>", "Что желаешь купить?", f"Монеты: {p.gold}"]
    for i, it in enumerate(shop, start=1):
        lines.append(format_item_line(it, i))
    lines.append("\nВыбери действие:")
    await message.answer("\n\n".join(lines), reply_markup=_market_menu_kb())

# ---------- ПОКУПКА ----------

@router.callback_query(F.data == "m_buy")
async def market_buy_menu(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    if not shop:
        await cb.message.answer("Пока пусто. Зайди позже.", reply_markup=_market_menu_kb())
        return
    await cb.message.answer("Что берёшь? Выбери номер товара:", reply_markup=_buy_pick_kb(min(9, len(shop))))

@router.callback_query(F.data.regexp(r"^m_b_(\d+)$"))
async def market_buy_pick(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(shop)):
        await cb.message.answer("Нет такого товара.", reply_markup=_market_menu_kb()); return
    item = shop[idx]
    text = format_item_line(item, idx + 1)
    await cb.message.answer(text, reply_markup=_confirm_kb(idx + 1))

@router.callback_query(F.data.regexp(r"^m_conf_(\d+)$"))
async def market_buy_confirm(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop: List[Dict] = getattr(p, "shop_items", [])
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(shop)):
        await cb.message.answer("Нет такого товара.", reply_markup=_market_menu_kb()); return

    item = shop[idx]
    name, price = item["name"], int(item["price"])
    max_stack = item.get("max_stack")

    if p.gold < price:
        await cb.message.answer("Не хватает монет."); return

    if max_stack:
        cur = p.inventory.get(name, 0)
        if cur >= max_stack:
            await cb.message.answer("Достигнут лимит по этому предмету."); return

    if name not in p.inventory and len(p.inventory) >= 10:
        await cb.message.answer("Инвентарь заполнен (10 слотов). Освободи место."); return

    p.gold -= price
    p.inventory[name] = p.inventory.get(name, 0) + 1
    save_player(p)

    await cb.message.answer("✅ Покупка успешна!")
    await open_market(cb.message)

@router.callback_query(F.data == "m_back")
async def market_back(cb: types.CallbackQuery):
    await cb.answer()
    await open_market(cb.message)

# ---------- ПРОДАЖА ----------

@router.callback_query(F.data == "m_sell")
async def market_sell_menu(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)

    sale_list = [(name, cnt) for name, cnt in p.inventory.items()]
    if not sale_list:
        await cb.message.answer("Продавать нечего.", reply_markup=_market_menu_kb()); return

    lines = ["💰 <b>Скупка</b>", "Цена указана за 1 шт. (50% от базовой):"]
    numbered: List[Tuple[str, int]] = []
    # считаем цену относительно базового пула
    for i, (name, cnt) in enumerate(sale_list, start=1):
        base = next((it for it in getattr(p, "shop_items", []) if it["name"] == name), None)
        if base is None:
            base = next((it for it in _base_pool() if it["name"] == name), None)
        sell_price = max(1, int((base["price"] if base else 8) * 0.5))
        titled = decorate_item_name(name, base.get("kind") if base else None, base.get("material") if base else None)
        lines.append(f"{i}. {titled} — {sell_price} зол. (в сумке: {cnt})")
        numbered.append((name, sell_price))

    _SALE_CACHE[user_id] = numbered
    await cb.message.answer("\n".join(lines), reply_markup=_sell_pick_kb(len(numbered)))

@router.callback_query(F.data.regexp(r"^m_s_(\d+)$"))
async def market_sell_pick(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    sale = _SALE_CACHE.get(user_id, [])
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(sale)):
        await cb.message.answer("Нет такого номера.", reply_markup=_market_menu_kb()); return
    name, price = sale[idx]
    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("Этого предмета нет.", reply_markup=_market_menu_kb()); return

    p.inventory[name] -= 1
    if p.inventory[name] <= 0:
        del p.inventory[name]
    p.gold += price
    save_player(p)

    await cb.message.answer(f"Продано: {name} за {price} зол. Баланс: {p.gold}")
    await open_market(cb.message)
