# -*- coding: utf-8 -*-
# app/features/tavern.py
from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player
from app.core.config import USE_OPENAI, oai_client

router = Router()

REST_FEE = 10  # стоимость отдыха

# кэши выбора (user_id -> ...)
_EQUIP_IDX_MAP: Dict[int, List[str]] = {}
_EQUIP_CHOICE: Dict[int, Tuple[str, str]] = {}

# ---------- Клавиатуры ----------

def tavern_menu_kb() -> InlineKeyboardMarkup:
    # Убрали «🏘️ В город»
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛌 Отдохнуть", callback_data="t_rest"),
         InlineKeyboardButton(text="⚔ Экипировка", callback_data="t_equip")],
    ])

def equip_pick_kb(keys: List[int]) -> InlineKeyboardMarkup:
    rows, row = [], []
    for n in keys:
        row.append(InlineKeyboardButton(text=str(n), callback_data=f"t_eq_{n}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="t_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def equip_confirm_kb(slot_idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Надеть", callback_data=f"t_econf_{slot_idx}")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="t_back")],
    ])

def unequip_menu_kb(can_weapon: bool, can_armor: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_weapon:
        rows.append([InlineKeyboardButton(text="🗡️ Снять оружие", callback_data="t_u_weap")])
    if can_armor:
        rows.append([InlineKeyboardButton(text="🛡️ Снять броню", callback_data="t_u_arm")])
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="t_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- Реплики ----------

async def _npc_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=80,
                messages=[
                    {"role": "system", "content": "Одна короткая тёплая реплика трактирщика-старика (1–2 предложения). Без Markdown."},
                    {"role": "user", "content": "Герой заходит в таверну. Единственное число."},
                ],
            )
            return f"👴 Трактирщик: «{resp.choices[0].message.content.strip()}»"
        except Exception:
            pass
    return "👴 Трактирщик: «Добро пожаловать, путник. У нас в таверне всегда тепло, а угощения с душой.»"

async def _npc_no_money_line(fee: int) -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=50,
                messages=[
                    {"role": "system", "content": "Одна короткая колкая реплика трактирщика (1 предложение), но без оскорблений. Без Markdown."},
                    {"role": "user", "content": f"Герою не хватает денег ({fee}) на отдых."},
                ],
            )
            return f"👴 Трактирщик: «{resp.choices[0].message.content.strip()}»"
        except Exception:
            pass
    return "👴 Трактирщик: «Кошель пуст — постель не для тебя. Возвращайся с монетами!»"

async def _npc_rest_success_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.8, max_tokens=60,
                messages=[
                    {"role": "system", "content": "Одна короткая приятная реплика трактирщика (1 предложение) о том, что герой выспался и окреп. Без Markdown."},
                    {"role": "user", "content": "Единственное число."},
                ],
            )
            return f"👴 Трактирщик: «{resp.choices[0].message.content.strip()}»"
        except Exception:
            pass
    return "👴 Трактирщик: «Лицо посвежело — видно, отдых пошёл на пользу!»"

# ---------- Заряды умений ----------

def _ability_uses_for_level(_: str, lvl: int, __: Optional[str]) -> int:
    lvl = max(1, int(lvl or 1))
    return 2 + lvl  # 1->3, 2->4, 3->5, ...

def _recharge_all_abilities(p) -> Dict[str, int]:
    charges: Dict[str, int] = {}
    for key, lvl in (p.abilities_known or {}).items():
        mx = _ability_uses_for_level(key, lvl, p.class_key)
        if mx > 0:
            charges[key] = mx
    return charges

# ---------- Вьюха ----------

async def _show_tavern(message: types.Message, user_id: int) -> None:
    p = get_player(user_id)
    if p is None:
        await message.answer("Сначала создай персонажа: /start")
        return

    line = await _npc_line()
    await message.answer(
        f"🍺 <b>Таверна</b>\n{line}\n\n"
        f"❤️ Здоровье: {p.hp}/{p.max_hp}\n"
        f"🪙 Золото: {p.gold}\n"
        f"💤 Отдых стоит {REST_FEE} 🪙",
        reply_markup=tavern_menu_kb()
    )

@router.message(F.text.in_(["🍺 Таверна", "Таверна"]))
async def tavern_open_msg(message: types.Message):
    await _show_tavern(message, message.from_user.id)

# ---------- Отдых ----------

@router.callback_query(F.data == "t_rest")
async def tavern_rest(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Сначала создай персонажа: /start")
        return

    if p.gold < REST_FEE:
        await cb.message.answer(await _npc_no_money_line(REST_FEE))
        await _show_tavern(cb.message, user_id)
        return

    p.gold -= REST_FEE
    heal = p.max_hp - p.hp
    p.hp = p.max_hp
    p.ability_charges = _recharge_all_abilities(p)
    save_player(p)

    success_line = await _npc_rest_success_line()
    await cb.message.answer(
        f"🛌 Ты хорошо отдохнул.\n"
        f"{success_line}\n\n"
        f"❤️ Здоровье и заряды умений восстановлены!\n"
        f"❤️ {p.hp}/{p.max_hp} (+{heal})\n"
        f"🪙 Золото: {p.gold} (−{REST_FEE})"
    )
    await _show_tavern(cb.message, user_id)

# ---------- Ограничения на экипировку ----------

def _weapon_category(name: str) -> str:
    low = (name or "").lower()
    if "лук" in low: return "bow"
    if any(x in low for x in ["посох","жезл"]): return "staff"
    if any(x in low for x in ["булав","палиц"]): return "mace"
    if "молот" in low: return "hammer"
    if "топор" in low: return "axe"
    if any(x in low for x in ["кинжал","нож"]): return "dagger"
    if any(x in low for x in ["меч","сабл","клинок"]): return "sword"
    return "other"

def _armor_material(name: str) -> Optional[str]:
    low = (name or "").lower()
    if any(x in low for x in ["роб","ряса","мант"]): return "robe"
    if "кожан" in low: return "leather"
    if any(x in low for x in ["латы","кольчуг","панцир","тяж"]): return "heavy"
    return None

_WEAPON_ALLOW = {
    "swordsman": {"sword", "axe"},
    "archer":    {"bow"},
    "thief":     {"dagger"},
    "mage":      {"staff"},
    "acolyte":   {"mace", "hammer"},
    "merchant":  {"dagger", "mace"},
}

_ARMOR_ALLOW = {
    "swordsman": {"leather", "heavy"},
    "archer":    {"leather"},
    "thief":     {"leather"},
    "mage":      {"robe"},
    "acolyte":   {"robe", "leather"},
    "merchant":  {"leather"},
}

def _class_can_wear(p, item_name: str, is_armor: bool) -> bool:
    ck = (p.class_key or "").lower()
    if is_armor:
        mat = _armor_material(item_name)
        if mat is None:
            return True
        return mat in _ARMOR_ALLOW.get(ck, {"leather"})
    else:
        cat = _weapon_category(item_name)
        return cat in _WEAPON_ALLOW.get(ck, {"dagger"})

# ---------- Экипировка ----------

@router.callback_query(F.data == "t_equip")
async def tavern_equip(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Сначала создай персонажа: /start")
        return

    items = list(p.inventory.items())
    lines = ["⚔ <b>Экипировка</b>", "Оружие и броня:"]
    idx_map: List[str] = []

    for i, (name, cnt) in enumerate(items, start=1):
        low = name.lower()
        kind = "weapon" if any(x in low for x in ["меч","сабл","клинок","кинжал","нож","топор","лук","посох","булав","жезл","молот"]) else (
               "armor" if any(x in low for x in ["брон","латы","кольчуг","панцир","роб","ряса","мант","кожан"]) else "consumable")
        if kind == "consumable":
            continue
        lines.append(f"{i}. {'🗡️' if kind=='weapon' else '🛡️'} {name} (×{cnt})")
        idx_map.append(name)

    if not idx_map:
        await cb.message.answer("⚔ Экипировка\nНечего надевать.", reply_markup=tavern_menu_kb())
        return

    lines.append("\nНажми номер, что надеть (🗡️ — оружие, 🛡️ — броня).")
    _EQUIP_IDX_MAP[user_id] = idx_map

    cur_w = (p.equipment or {}).get("weapon") if p.equipment else None
    cur_a = (p.equipment or {}).get("armor") if p.equipment else None
    can_unw, can_una = cur_w is not None, cur_a is not None

    await cb.message.answer("\n".join(lines), reply_markup=equip_pick_kb(list(range(1, len(idx_map)+1))))
    await cb.message.answer("Снять экипировку?", reply_markup=unequip_menu_kb(can_unw, can_una))

@router.callback_query(F.data.regexp(r"^t_eq_(\d+)$"))
async def tavern_equip_pick(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Сначала создай персонажа: /start")
        return

    idx_map: List[str] = _EQUIP_IDX_MAP.get(user_id, [])
    if not idx_map:
        await cb.message.answer("Список устарел. Откройте заново «Экипировку»."); return

    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(idx_map)):
        await cb.message.answer("Нет такого номера."); return

    name = idx_map[idx]
    low = name.lower()
    kind = "weapon" if any(x in low for x in ["меч","сабл","клинок","кинжал","нож","топор","лук","посох","булав","жезл","молот"]) else "armor"

    if not _class_can_wear(p, name, is_armor=(kind == "armor")):
        await cb.message.answer("Этот предмет не подходит для вашего класса.", reply_markup=tavern_menu_kb())
        return

    _EQUIP_CHOICE[user_id] = (name, kind)
    await cb.message.answer(f"Выбран предмет: {name}\nНадеть?", reply_markup=equip_confirm_kb(idx+1))

@router.callback_query(F.data.regexp(r"^t_econf_(\d+)$"))
async def tavern_equip_confirm(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Сначала создай персонажа: /start")
        return

    choice = _EQUIP_CHOICE.pop(user_id, None)
    if not choice:
        await cb.message.answer("Выбор устарел. Откройте заново «Экипировку».", reply_markup=tavern_menu_kb()); return

    name, kind = choice
    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("Такого предмета уже нет в инвентаре.", reply_markup=tavern_menu_kb()); return

    if not p.equipment:
        p.equipment = {}
    p.equipment["weapon" if kind == "weapon" else "armor"] = name
    save_player(p)

    await cb.message.answer(f"✅ Надето: {name} ({'оружие' if kind=='weapon' else 'броня'}).")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_weap")
async def tavern_unequip_weapon(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("weapon"):
        p.equipment["weapon"] = None
        save_player(p)
        await cb.message.answer("🗡️ Оружие снято.")
    else:
        await cb.message.answer("Оружие не надето.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_arm")
async def tavern_unequip_armor(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("armor"):
        p.equipment["armor"] = None
        save_player(p)
        await cb.message.answer("🛡️ Броня снята.")
    else:
        await cb.message.answer("Броня не надета.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_back")
async def tavern_back(cb: types.CallbackQuery):
    await cb.answer()
    await _show_tavern(cb.message, cb.from_user.id)
