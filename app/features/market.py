# -*- coding: utf-8 -*-
# app/features/market.py
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player

# Р­РјРѕРґР·Рё-РґРµРєРѕСЂР°С‚РѕСЂ вЂ” РјСЏРіРєРёР№ С„РѕР»Р±СЌРє
try:
    from app.core.emoji import decorate_item_name
except Exception:
    def decorate_item_name(name: str, kind: Optional[str] = None, material: Optional[str] = None) -> str:
        return name

# РљР°РјРїР°РЅРёР№РЅС‹Рµ РїСЂРµРґРјРµС‚С‹
from app.core.campaign_items import pick_campaign_items, find_campaign_item_by_name

router = Router(name="market")

# user_id -> [(name, price)]
_SALE_CACHE: Dict[int, List[Tuple[str, int]]] = {}


# ---------- Р‘РђР—РћР’Р«Р™ РџРЈР› Р Р«РќРљРђ (РјРёРЅРёРјР°Р»СЊРЅС‹Р№ РІСЃРµРіРґР° РґРѕСЃС‚СѓРїРЅС‹Р№) ----------
def _base_pool() -> List[Dict]:
    return [
        # СЂР°СЃС…РѕРґРЅРёРєРё / Р»Р°РіРµСЂСЊ
        {"name": "Р—РµР»СЊРµ Р»РµС‡РµРЅРёСЏ", "kind": "consumable", "price": 8,  "desc": "Р’РѕСЃСЃС‚Р°РЅР°РІР»РёРІР°РµС‚ С‡Р°СЃС‚СЊ Р·РґРѕСЂРѕРІСЊСЏ.", "max_stack": 3},
        {"name": "РџРѕР»РµРІРѕР№ РЅР°Р±РѕСЂ",  "kind": "camp",       "price": 15, "desc": "РќР°Р±РѕСЂ РґР»СЏ РѕС‚РґС‹С…Р° РІ РґРѕСЂРѕРіРµ.",      "max_stack": 3},

        # РѕСЂСѓР¶РёРµ
        {"name": "Р–РµР»РµР·РЅС‹Р№ РјРµС‡",   "kind": "weapon", "price": 25, "desc": "РџСЂРѕСЃС‚РѕР№, РЅРѕ РЅР°РґС‘Р¶РЅС‹Р№ РєР»РёРЅРѕРє.", "dmg": "+1"},
        {"name": "Р”СѓР±РёРЅРєР°",        "kind": "weapon", "price": 18, "desc": "РўСЏР¶С‘Р»Р°СЏ СЂСѓРєРѕСЏС‚СЊ РґР»СЏ Р±Р»РёР¶РЅРµРіРѕ Р±РѕСЏ.", "dmg": "+1"},
        {"name": "РџРѕСЃРѕС… СѓС‡РµРЅРёРєР°",  "kind": "weapon", "price": 20, "desc": "Р›С‘РіРєРёР№ РїРѕСЃРѕС… РґР»СЏ РЅР°С‡РёРЅР°СЋС‰РёС… РјР°РіРѕРІ.", "material": "robe", "dmg": "+1"},
        {"name": "РљРёРЅР¶Р°Р»",         "kind": "weapon", "price": 23, "desc": "Р›С‘РіРєРѕРµ СЃРєСЂС‹С‚РЅРѕРµ РѕСЂСѓР¶РёРµ.", "dmg": "+1"},
        {"name": "РљРѕСЂРѕС‚РєРёР№ Р»СѓРє",   "kind": "weapon", "price": 28, "desc": "РЈРґРѕР±РµРЅ РґР»СЏ РѕС…РѕС‚С‹ Рё СЂР°Р·РІРµРґРєРё.", "dmg": "+1"},

        # Р±СЂРѕРЅСЏ
        {"name": "РљРѕР¶Р°РЅР°СЏ РєСѓСЂС‚РєР°", "kind": "armor",  "price": 22, "desc": "Р“РёР±РєР°СЏ Р·Р°С‰РёС‚Р° РёР· РІС‹РґРµР»Р°РЅРЅРѕР№ РєРѕР¶Рё.", "def": "+1", "material": "leather"},
        {"name": "РўРєР°РЅР°СЏ РјР°РЅС‚РёСЏ",  "kind": "armor",  "price": 19, "desc": "Р›С‘РіРєР°СЏ РјР°РЅС‚РёСЏ РґР»СЏ РјР°РіРёС‡РµСЃРєРёС… Р·Р°РЅСЏС‚РёР№.", "def": "+1", "material": "robe"},
    ]


# ---------- РЎР‘РћР РљРђ Р’РРўР РРќР« Р”Р›РЇ РљРћРќРљР Р•РўРќРћР“Рћ РР“Р РћРљРђ ----------
def _roll_shop_items_for_player(p) -> List[Dict]:
    """
    5 РїРѕР·РёС†РёР№: 2 С„РёРєСЃРёСЂРѕРІР°РЅРЅС‹С… (Р·РµР»СЊРµ + РїРѕР»РµРІРѕР№ РЅР°Р±РѕСЂ) + 3 РјРµСЃС‚Р°,
    РІ РєРѕС‚РѕСЂС‹С… РїС‹С‚Р°РµРјСЃСЏ РїРѕРєР°Р·Р°С‚СЊ РґРѕ 2 РєР°РјРїР°РЅРёР№РЅС‹С… РїСЂРµРґРјРµС‚РѕРІ РёРіСЂРѕРєР°.
    """
    pool = _base_pool()
    must = [
        next(x for x in pool if x["name"] == "Р—РµР»СЊРµ Р»РµС‡РµРЅРёСЏ"),
        next(x for x in pool if x["name"] == "РџРѕР»РµРІРѕР№ РЅР°Р±РѕСЂ"),
    ]
    rest = [x for x in pool if x["name"] not in ("Р—РµР»СЊРµ Р»РµС‡РµРЅРёСЏ", "РџРѕР»РµРІРѕР№ РЅР°Р±РѕСЂ")]
    random.shuffle(rest)

    items: List[Dict] = must.copy()
    rest_slots = 3

    # РљР°РјРїР°РЅРёСЏ Рё РєР»Р°СЃСЃ РёРіСЂРѕРєР°
    camp_id: Optional[str] = getattr(p, "campaign_id", None)
    class_key: Optional[str] = getattr(p, "class_key", None)

    # РґРѕ 2 С€С‚ РёР· РєР°РјРїР°РЅРёРё
    camp_items = pick_campaign_items(camp_id, k=min(2, rest_slots), class_key=class_key)
    items += camp_items
    rest_slots -= len(camp_items)

    # РґРѕР±РёРІР°РµРј Р±Р°Р·РѕР№
    if rest_slots > 0:
        items += rest[:rest_slots]

    # РЅРµРјРЅРѕРіРѕ РїРµСЂРµРјРµС€Р°РµРј, С‡С‚РѕР±С‹ В«РѕР±СЏР·Р°С‚РµР»СЊРЅС‹РµВ» РЅРµ РІСЃРµРіРґР° Р±С‹Р»Рё СЃРІРµСЂС…Сѓ
    random.shuffle(items)
    return items


def _market_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="рџ›’ РљСѓРїРёС‚СЊ", callback_data="m_buy"),
         InlineKeyboardButton(text="рџ’° РџСЂРѕРґР°С‚СЊ", callback_data="m_sell")],
    ])


def _buy_pick_kb(count: int) -> InlineKeyboardMarkup:
    nums, rows = [], []
    for i in range(1, count + 1):
        nums.append(InlineKeyboardButton(text=str(i), callback_data=f"m_b_{i}"))
        if len(nums) == 5:
            rows.append(nums); nums = []
    if nums:
        rows.append(nums)
    rows.append([InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ Рє СЂС‹РЅРєСѓ", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _confirm_kb(idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="вњ… РљСѓРїРёС‚СЊ", callback_data=f"m_conf_{idx}")],
        [InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ Рє СЂС‹РЅРєСѓ", callback_data="m_back")],
    ])


def _sell_pick_kb(n: int) -> InlineKeyboardMarkup:
    rows, row = [], []
    for i in range(1, n + 1):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"m_s_{i}"))
        if len(row) == 5:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ Рє СЂС‹РЅРєСѓ", callback_data="m_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_item_line(entry: Dict, index: Optional[int] = None) -> str:
    name = entry["name"]; price = entry["price"]
    desc = entry.get("desc", ""); kind = entry.get("kind"); material = entry.get("material")
    title = decorate_item_name(name, kind, material)
    max_part = f" (MAX: {entry['max_stack']})" if entry.get("max_stack") else ""
    head = f"{index}. {title} вЂ” {price} Р·РѕР».{max_part}" if index else f"{title} вЂ” {price} Р·РѕР».{max_part}"

    extra = []
    if "dmg" in entry: extra.append(f"вљ” РЈСЂРѕРЅ: {entry['dmg']}")
    if "def" in entry: extra.append(f"рџ›Ў Р—Р°С‰РёС‚Р°: {entry['def']}")
    if "bonus" in entry: extra.append(f"вњЁ Р‘РѕРЅСѓСЃ: {entry['bonus']}")
    stats_line = ("\n" + "\n".join(extra)) if extra else ""

    body = desc.strip() if desc else ""
    return f"{head}\n{body}{stats_line}".strip()


# ---------- Р’РҐРћР” Р’ Р Р«РќРћРљ ----------
@router.message(F.text.contains("Р С‹РЅРѕРє"))
async def open_market(message: types.Message):
    """РћС‚РєСЂС‹С‚СЊ СЂС‹РЅРѕРє РёР· РіРѕСЂРѕРґСЃРєРѕРіРѕ РјРµРЅСЋ."""
    p = get_player(message.from_user.id)

    # РћР±РЅРѕРІР»СЏРµРј РІРёС‚СЂРёРЅСѓ РўРћР›Р¬РљРћ РµСЃР»Рё РµС‘ РЅРµС‚ РёР»Рё СЃС‚РѕРёС‚ С„Р»Р°Рі В«РіСЂСЏР·РЅР°СЏВ»
    shop = getattr(p, "shop_items", None)
    if not shop or getattr(p, "shop_dirty", False):
        shop = _roll_shop_items_for_player(p)
        p.shop_items = shop
        p.shop_dirty = False
        save_player(p)

    lines = ["рџ›’ <b>Р С‹РЅРѕРє</b>", "Р§С‚Рѕ Р¶РµР»Р°РµС€СЊ РєСѓРїРёС‚СЊ?", f"РњРѕРЅРµС‚С‹: {p.gold}"]
    for i, it in enumerate(shop, start=1):
        lines.append(format_item_line(it, i))
    lines.append("\nР’С‹Р±РµСЂРё РґРµР№СЃС‚РІРёРµ:")
    await message.answer("\n\n".join(lines), reply_markup=_market_menu_kb())


# ---------- РџРћРљРЈРџРљРђ ----------
@router.callback_query(F.data == "m_buy")
async def market_buy_menu(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    if not shop:
        await cb.message.answer("РџРѕРєР° РїСѓСЃС‚Рѕ. Р—Р°Р№РґРё РїРѕР·Р¶Рµ.", reply_markup=_market_menu_kb())
        return
    await cb.message.answer("Р§С‚Рѕ Р±РµСЂС‘С€СЊ? Р’С‹Р±РµСЂРё РЅРѕРјРµСЂ С‚РѕРІР°СЂР°:", reply_markup=_buy_pick_kb(min(9, len(shop))))


@router.callback_query(F.data.regexp(r"^m_b_(\d+)$"))
async def market_buy_pick(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    shop = getattr(p, "shop_items", [])
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(shop)):
        await cb.message.answer("РќРµС‚ С‚Р°РєРѕРіРѕ С‚РѕРІР°СЂР°.", reply_markup=_market_menu_kb()); return
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
        await cb.message.answer("РќРµС‚ С‚Р°РєРѕРіРѕ С‚РѕРІР°СЂР°.", reply_markup=_market_menu_kb()); return

    item = shop[idx]
    name, price = item["name"], int(item["price"])
    max_stack = item.get("max_stack")

    if p.gold < price:
        await cb.message.answer("РќРµ С…РІР°С‚Р°РµС‚ РјРѕРЅРµС‚."); return

    if max_stack:
        cur = p.inventory.get(name, 0)
        if cur >= max_stack:
            await cb.message.answer("Р”РѕСЃС‚РёРіРЅСѓС‚ Р»РёРјРёС‚ РїРѕ СЌС‚РѕРјСѓ РїСЂРµРґРјРµС‚Сѓ."); return

    if name not in p.inventory and len(p.inventory) >= 10:
        await cb.message.answer("РРЅРІРµРЅС‚Р°СЂСЊ Р·Р°РїРѕР»РЅРµРЅ (10 СЃР»РѕС‚РѕРІ). РћСЃРІРѕР±РѕРґРё РјРµСЃС‚Рѕ."); return

    p.gold -= price
    p.inventory[name] = p.inventory.get(name, 0) + 1
    save_player(p)

    await cb.message.answer("вњ… РџРѕРєСѓРїРєР° СѓСЃРїРµС€РЅР°!")
    await open_market(cb.message)


@router.callback_query(F.data == "m_back")
async def market_back(cb: types.CallbackQuery):
    await cb.answer()
    await open_market(cb.message)


# ---------- РџР РћР”РђР–Рђ ----------
def _lookup_price_for_sell(p, name: str) -> int:
    """
    Р’РѕР·РІСЂР°С‰Р°РµС‚ Р±Р°Р·РѕРІСѓСЋ С†РµРЅСѓ РїСЂРµРґРјРµС‚Р° РїРѕ РёРјРµРЅРё:
    1) РµСЃР»Рё РїСЂРµРґРјРµС‚ РЅР° РІРёС‚СЂРёРЅРµ вЂ” Р±РµСЂС‘Рј РµРіРѕ С†РµРЅСѓ,
    2) РёРЅР°С‡Рµ РёС‰РµРј РІ Р±Р°Р·Рµ СЂС‹РЅРєР°,
    3) РёРЅР°С‡Рµ РёС‰РµРј СЃСЂРµРґРё РєР°РјРїР°РЅРёР№РЅС‹С… РїСЂРµРґРјРµС‚РѕРІ,
    4) РёРЅР°С‡Рµ СЃС‚Р°РІРёРј РґРµС„РѕР»С‚ 8.
    """
    # 1) С‚РµРєСѓС‰Р°СЏ РІРёС‚СЂРёРЅР°
    shop = getattr(p, "shop_items", []) or []
    base = next((it for it in shop if it.get("name") == name), None)
    if base is not None:
        return int(base.get("price", 8))

    # 2) Р±Р°Р·РѕРІС‹Р№ РїСѓР»
    base_pool = _base_pool()
    base = next((it for it in base_pool if it.get("name") == name), None)
    if base is not None:
        return int(base.get("price", 8))

    # 3) РєР°РјРїР°РЅРёРё
    camp = find_campaign_item_by_name(name)
    if camp is not None:
        return int(camp.get("price", 8))

    # 4) РґРµС„РѕР»С‚
    return 8


@router.callback_query(F.data == "m_sell")
async def market_sell_menu(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)

    sale_list = [(name, cnt) for name, cnt in p.inventory.items()]
    if not sale_list:
        await cb.message.answer("РџСЂРѕРґР°РІР°С‚СЊ РЅРµС‡РµРіРѕ.", reply_markup=_market_menu_kb()); return

    lines = ["рџ’° <b>РЎРєСѓРїРєР°</b>", "Р¦РµРЅР° СѓРєР°Р·Р°РЅР° Р·Р° 1 С€С‚. (50% РѕС‚ Р±Р°Р·РѕРІРѕР№):"]
    numbered: List[Tuple[str, int]] = []

    for i, (name, cnt) in enumerate(sale_list, start=1):
        base_price = _lookup_price_for_sell(p, name)
        sell_price = max(1, int(base_price * 0.5))
        lines.append(f"{i}. {name} вЂ” {sell_price} Р·РѕР». (РІ СЃСѓРјРєРµ: {cnt})")
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
        await cb.message.answer("РќРµС‚ С‚Р°РєРѕРіРѕ РЅРѕРјРµСЂР°.", reply_markup=_market_menu_kb()); return

    name, price = sale[idx]
    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("Р­С‚РѕРіРѕ РїСЂРµРґРјРµС‚Р° РЅРµС‚.", reply_markup=_market_menu_kb()); return

    p.inventory[name] -= 1
    if p.inventory[name] <= 0:
        del p.inventory[name]
    p.gold += price
    save_player(p)

    await cb.message.answer(f"РџСЂРѕРґР°РЅРѕ: {name} Р·Р° {price} Р·РѕР». Р‘Р°Р»Р°РЅСЃ: {p.gold}")
    await open_market(cb.message)



