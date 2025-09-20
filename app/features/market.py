# -*- coding: utf-8 -*-
# app/features/market.py
from __future__ import annotations

import os
import json
import random
from typing import Dict, List, Optional, Tuple

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player

# Эмодзи-декоратор — мягкий фолбэк
try:
    from app.core.emoji import decorate_item_name
except Exception:
    def decorate_item_name(name: str, kind: Optional[str] = None, material: Optional[str] = None) -> str:
        return name

# Кампанийные предметы
from app.core.campaign_items import pick_campaign_items, find_campaign_item_by_name

router = Router(name="market")

# user_id -> [(name, price)]
_SALE_CACHE: Dict[int, List[Tuple[str, int]]] = {}

# кеш лора
_LORE_CACHE: Optional[List[Dict]] = None


# ---------- БАЗОВЫЙ ПУЛ РЫНКА (минимальный всегда доступный) ----------
def _base_pool() -> List[Dict]:
    return [
        # расходники / лагерь — эти два ДОЛЖНЫ быть в витрине всегда
        {"name": "Зелье лечения", "kind": "consumable", "price": 8,  "desc": "Восстанавливает часть здоровья.", "max_stack": 3},
        {"name": "Полевой набор", "kind": "camp",       "price": 15, "desc": "Набор для отдыха в дороге.",      "max_stack": 3},

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


# ---------- ЗАГРУЗКА ЛОРА ИЗ items_lore.txt (если есть) ----------
def _guess_kind(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ("меч", "клинок", "сабл")): return "weapon"
    if any(x in n for x in ("лук", "стрел")): return "weapon"
    if any(x in n for x in ("кинжал", "нож", "катар")): return "weapon"
    if any(x in n for x in ("посох", "жезл")): return "weapon"
    if any(x in n for x in ("булав", "молот", "мейс")): return "weapon"
    if any(x in n for x in ("манти", "роб", "риза", "одеяни")): return "armor"
    if any(x in n for x in ("кожан",)): return "armor"
    if any(x in n for x in ("латы", "панцир", "кирас", "желез", "сталь")): return "armor"
    return "misc"

def _make_item_from_line(line: str) -> Optional[Dict]:
    """
    Поддерживаем простые форматы:
    1) JSON-объект в строке
    2) 'name|kind|price|desc|dmg|def|material|bonus'
    3) 'name' (всё остальное по дефолту)
    """
    s = line.strip()
    if not s or s.startswith("#"):
        return None
    # JSON-объект?
    if s.startswith("{") and s.endswith("}"):
        try:
            obj = json.loads(s)
            if isinstance(obj, dict) and "name" in obj:
                return obj
        except Exception:
            pass
    # Разделители
    for sep in ("|", ";", ","):
        if sep in s:
            parts = [p.strip() for p in s.split(sep)]
            break
    else:
        parts = [s]

    name = parts[0]
    if not name:
        return None
    kind = parts[1].lower() if len(parts) > 1 and parts[1] else _guess_kind(name)
    try:
        price = int(parts[2]) if len(parts) > 2 and parts[2] else 12
    except Exception:
        price = 12
    desc = parts[3] if len(parts) > 3 and parts[3] else "Предмет из старых записей."
    dmg = parts[4] if len(parts) > 4 and parts[4] else None
    df  = parts[5] if len(parts) > 5 and parts[5] else None
    mat = parts[6] if len(parts) > 6 and parts[6] else None
    bon = parts[7] if len(parts) > 7 and parts[7] else None

    item: Dict = {"name": name, "kind": kind, "price": price, "desc": desc}
    if dmg: item["dmg"] = dmg
    if df:  item["def"] = df
    if mat: item["material"] = mat
    if bon: item["bonus"] = bon
    return item

def _load_lore_items() -> List[Dict]:
    global _LORE_CACHE
    if _LORE_CACHE is not None:
        return _LORE_CACHE

    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "core", "items_lore.txt"),
        os.path.join(os.path.dirname(__file__), "..", "items_lore.txt"),
        os.path.join(os.path.dirname(__file__), "items_lore.txt"),
        os.path.join(os.getcwd(), "app", "core", "items_lore.txt"),
        os.path.join(os.getcwd(), "items_lore.txt"),
    ]
    path = next((p for p in candidates if os.path.isfile(p)), None)
    items: List[Dict] = []
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read().strip()
            # Если это JSON-массив
            if data.startswith("["):
                obj = json.loads(data)
                if isinstance(obj, list):
                    for x in obj:
                        if isinstance(x, dict) and "name" in x:
                            items.append(x)
                _LORE_CACHE = items
                return items
            # Иначе — построчно
            for line in data.splitlines():
                it = _make_item_from_line(line)
                if it:
                    items.append(it)
        except Exception:
            items = []
    _LORE_CACHE = items
    return items


# ---------- СБОРКА ВИТРИНЫ ДЛЯ КОНКРЕТНОГО ИГРОКА ----------
def _roll_shop_items_for_player(p) -> List[Dict]:
    """
    Итог: 5 позиций.
    — 2 фиксированных: Зелье лечения + Полевой набор
    — 3 рандомных слота из: кампанийных предметов (до 2 шт) + лор-файл + базовый пул
    """
    base = _base_pool()
    must = [
        next(x for x in base if x["name"] == "Зелье лечения"),
        next(x for x in base if x["name"] == "Полевой набор"),
    ]
    base_rest = [x for x in base if x["name"] not in ("Зелье лечения", "Полевой набор")]

    # Кампания и класс игрока
    camp_id: Optional[str] = getattr(p, "campaign_id", None)
    class_key: Optional[str] = getattr(p, "class_key", None)

    # 1) до 2 кампанийных
    camp_items = pick_campaign_items(camp_id, k=2, class_key=class_key) or []
    # Убираем дубли по именам
    seen = {x["name"] for x in must}
    uniq_camp = []
    for it in camp_items:
        if it["name"] not in seen:
            uniq_camp.append(it)
            seen.add(it["name"])
        if len(uniq_camp) >= 2:
            break

    # 2) заполняем оставшиеся слоты лором/базой
    rest_slots = 3
    picked: List[Dict] = []
    picked.extend(uniq_camp[: min(len(uniq_camp), rest_slots)])
    rest_slots -= len(picked)

    if rest_slots > 0:
        lore = _load_lore_items()
        filler_pool = base_rest[:] + lore[:]  # если лор пуст — просто базовые
        random.shuffle(filler_pool)
        for it in filler_pool:
            if rest_slots <= 0:
                break
            if it["name"] in seen:
                continue
            picked.append(it)
            seen.add(it["name"])
            rest_slots -= 1

    # Сборка и лёгкая перетасовка
    items: List[Dict] = must + picked
    random.shuffle(items)
    return items


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
    if "bonus" in entry: extra.append(f"✨ Бонус: {entry['bonus']}")
    stats_line = ("\n" + "\n".join(extra)) if extra else ""

    body = desc.strip() if desc else ""
    return f"{head}\n{body}{stats_line}".strip()


# ---------- ВХОД В РЫНОК ----------
@router.message(F.text.contains("Рынок"))
async def open_market(message: types.Message):
    """Открыть рынок из городского меню."""
    p = get_player(message.from_user.id)

    # Обновляем витрину ТОЛЬКО если её нет или стоит флаг «грязная»
    shop = getattr(p, "shop_items", None)
    if not shop or getattr(p, "shop_dirty", False):
        shop = _roll_shop_items_for_player(p)
        p.shop_items = shop
        p.shop_dirty = False
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
def _lookup_price_for_sell(p, name: str) -> int:
    """
    Возвращает базовую цену предмета по имени:
    1) если предмет на витрине — берём его цену,
    2) иначе ищем в базе рынка,
    3) иначе ищем среди кампанийных предметов,
    4) иначе ставим дефолт 8.
    """
    # 1) текущая витрина
    shop = getattr(p, "shop_items", []) or []
    base = next((it for it in shop if it.get("name") == name), None)
    if base is not None:
        return int(base.get("price", 8))

    # 2) базовый пул
    base_pool = _base_pool()
    base = next((it for it in base_pool if it.get("name") == name), None)
    if base is not None:
        return int(base.get("price", 8))

    # 3) кампании
    camp = find_campaign_item_by_name(name)
    if camp is not None:
        return int(camp.get("price", 8))

    # 4) дефолт
    return 8


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

    for i, (name, cnt) in enumerate(sale_list, start=1):
        base_price = _lookup_price_for_sell(p, name)
        sell_price = max(1, int(base_price * 0.5))
        lines.append(f"{i}. {name} — {sell_price} зол. (в сумке: {cnt})")
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
        await cb.message.answer("Этого предмета нет.", reply_markup=_market_menu_kб()); return

    p.inventory[name] -= 1
    if p.inventory[name] <= 0:
        del p.inventory[name]
    p.gold += price
    save_player(p)

    await cb.message.answer(f"Продано: {name} за {price} зол. Баланс: {p.gold}")
