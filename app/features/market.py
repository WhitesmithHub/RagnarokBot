# -*- coding: utf-8 -*-
# app/features/market.py
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player
from app.core.emoji import decorate_item_name

router = Router()

# Временный кэш выбора на продажу: user_id -> [(name, price), ...]
_SALE_CACHE: Dict[int, List[Tuple[str, int]]] = {}

# ---------- Утилиты ассортимента ----------

def _base_pool() -> List[Dict]:
    return [
        # consumables / camp
        {"name": "Провиант", "kind": "consumable", "price": 8,  "desc": "Простой дорожный паёк.", "max_stack": 3},
        {"name": "Набор для костра", "kind": "camp", "price": 15, "desc": "Даёт возможность привала в подземелье.", "max_stack": 3},

        # weapons
        {"name": "Простая сабля", "kind": "weapon", "price": 25, "desc": "Лёгкий клинок.", "dmg":"+1"},
        {"name": "Кинжал", "kind": "weapon", "price": 18, "desc": "Удобен для быстрых ударов.", "dmg":"+1"},
        {"name": "Деревянный посох", "kind": "weapon", "price": 20, "desc": "Простой магический фокус.", "material": "robe", "dmg":"+1"},
        {"name": "Лук охотника", "kind": "weapon", "price": 28, "desc": "Простой лук и тетива.", "dmg":"+1"},
        {"name": "Булава послушника", "kind": "weapon", "price": 23, "desc": "Подходит для послушников.", "dmg":"+1"},

        # armors
        {"name": "Кожаная броня", "kind": "armor", "price": 22, "desc": "Лёгкая защита.", "def":"+1", "material": "leather"},
        {"name": "Роба ученика", "kind": "armor", "price": 19, "desc": "Ткань с простыми рунами.", "def":"+1", "material": "robe"},
    ]

def _roll_shop_items() -> List[Dict]:
    """
    Генерируем 5 случайных позиций, гарантируя наличие провианта и костра.
    Ассортимент сохраняется у игрока и обновляется только при выходе из подземелья.
    """
    pool = _base_pool()
    must = [next(x for x in pool if x["name"] == "Провиант"),
            next(x for x in pool if x["name"] == "Набор для костра")]
    rest = [x for x in pool if x["name"] not in ("Провиант", "Набор для костра")]
    random.shuffle(rest)
    items = must + rest[:3]
    return items

def format_item_line(entry: Dict, index: Optional[int] = None) -> str:
    """Формат карточки товара — без слов «Стакается»."""
    name = entry["name"]
    price = entry["price"]
    desc = entry.get("desc", "")
    kind = entry.get("kind")
    material = entry.get("material")
    title = decorate_item_name(name, kind, material)

    max_part = f" (MAX: {entry['max_stack']})" if entry.get("max_stack") else ""
    head = f"{index}. {title} — {price} зол.{max_part}" if index else f"{title} — {price} зол.{max_part}"

    extra = []
    if "dmg" in entry:
        extra.append(f"Урон: {entry['dmg']}")
    if "def" in entry:
        extra.append(f"Защита: {entry['def']}")
    stats_line = ("\n" + "\n".join(extra)) if extra else ""

    body = desc.strip() if desc else ""
    return f"{head}\n{body}{stats_line}".strip()

def _market_menu_kb() -> InlineKeyboardMarkup:
    # Убрали «🏘️ В город»
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Купить", callback_data="m_buy"),
         InlineKeyboardButton(text="💰 Продать", callback_data="m_sell")],
    ])

def _buy_pick_kb(count: int) -> InlineKeyboardMarkup:
    nums, rows = [], []
    for i in range(1, count+1):
        nums.append(InlineKeyboardButton(text=str(i), callback_data=f"m_b_{i}"))
        if len(nums) == 5:
            rows.append(nums); nums = []
    if nums:
        rows.append(nums)
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _confirm_kb(idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"m_conf_{idx}")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="m_back")],
    ])

def _sell_pick_kb(n: int) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i in range(1, n+1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"m_s_{i}"))
        if len(row) == 5:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- Публичный API для других модулей ----------

def clear_market_for_player(user_id: int):
    """Вызывается при выходе из подземелья — обновляет ассортимент."""
    p = get_player(user_id)
    if hasattr(p, "shop_items"):
        delattr(p, "shop_items")
    save_player(p)

# ---------- Открытие рынка ----------

@router.message(F.text.in_(["🛒 Рынок", "Рынок"]))
async def open_market(message: types.Message):
    p = get_player(message.from_user.id)
    shop = getattr(p, "shop_items", None)
    if not shop:
        shop = _roll_shop_items()
        p.shop_items = shop
        save_player(p)

    lines = ["🛒 <b>Рынок</b>", "👨‍🦱 Торговец: «Чего желаете?»", f"👛 Кошелёк: {p.gold}"]
    for i, it in enumerate(shop, start=1):
        lines.append(format_item_line(it, i))
    lines.append("\nВыберите действие ниже.")
    await message.answer("\n\n".join(lines), reply_markup=_market_menu_kb())

# ---------- Покупка ----------

@router.callback_query(F.data == "m_buy")
async def market_buy_menu(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    if not shop:
        await cb.message.answer("Ассортимент пуст. Зайдите позже.", reply_markup=_market_menu_kb())
        return
    await cb.message.answer("👨‍🦱 Торговец: «Чего желаете? Выберите номер.»", reply_markup=_buy_pick_kb(min(9, len(shop))))

@router.callback_query(F.data.regexp(r"^m_b_(\d+)$"))
async def market_buy_pick(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(shop)):
        await cb.message.answer("Нет такого товара.", reply_markup=_market_menu_kb()); return
    item = shop[idx]
    text = format_item_line(item, idx+1)
    await cb.message.answer(text, reply_markup=_confirm_kb(idx+1))

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
        await cb.message.answer("Не хватает золота."); return

    if max_stack:
        cur = p.inventory.get(name, 0)
        if cur >= max_stack:
            await cb.message.answer("Достигнут лимит по этому предмету."); return

    if name not in p.inventory and len(p.inventory) >= 10:
        await cb.message.answer("Инвентарь заполнен (10 слотов). Продайте что-нибудь."); return

    p.gold -= price
    p.inventory[name] = p.inventory.get(name, 0) + 1
    save_player(p)

    await cb.message.answer("✅ Спасибо за покупку!")
    await open_market(cb.message)

@router.callback_query(F.data == "m_back")
async def market_back(cb: types.CallbackQuery):
    await cb.answer()
    await open_market(cb.message)

# ---------- Продажа ----------

@router.callback_query(F.data == "m_sell")
async def market_sell_menu(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)

    sale_list = [(name, cnt) for name, cnt in p.inventory.items()]
    if not sale_list:
        await cb.message.answer("Инвентарь пуст.", reply_markup=_market_menu_kb()); return

    lines = ["💰 <b>Продажа</b>", "Доступно к продаже по 1 шт. за 50% цены:"]
    numbered: List[Tuple[str,int]] = []
    for i, (name, cnt) in enumerate(sale_list, start=1):
        base = next((it for it in getattr(p, "shop_items", []) if it["name"] == name), None)
        if base is None:
            base = next((it for it in _base_pool() if it["name"] == name), None)
        sell_price = max(1, int((base["price"] if base else 8) * 0.5))

        kind = "weapon" if any(x in name.lower() for x in ["меч","сабл","кинжал","лук","посох","булав","жезл","топор","молот"]) else (
               "armor" if any(x in name.lower() for x in ["брон","латы","кольчуг","панцир","роб","ряса","мант","кожан"]) else "consumable")
        material = "leather" if "кожан" in name.lower() else ("robe" if any(x in name.lower() for x in ["роб","ряса","мант"]) else None)
        titled = decorate_item_name(name, kind, material)
        lines.append(f"{i}. {titled} — {sell_price} зол. (×{cnt})")
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

    await cb.message.answer(f"✅ Продано: {name} за {price} зол. 👛 Итого: {p.gold}")
    await open_market(cb.message)

from aiogram.filters import Command
from app.core.items_lore_repo import get_all_lore_items
from app.core.emoji import rarity_badge

@router.message(Command("lore_preview"))
async def lore_preview(message: types.Message):
    items = get_all_lore_items()
    if not items:
        await message.answer("Лоровый список не найден или пуст (app/data/items_lore.txt).")
        return

    head = items[:10]
    lines = []
    for it in head:
        lvl = f"{it.level[0]}–{it.level[1]}"
        lines.append(
            f"• {it.name} [{rarity_badge(it.rarity)}] ({lvl})\n"
            f"  {it.type}; классы: {', '.join(it.allowed_classes)}\n"
            f"  {it.description}"
        )
    await message.answer(f"Всего предметов: {len(items)}\n\n" + "\n\n".join(lines))
