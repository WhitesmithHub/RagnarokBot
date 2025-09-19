# -*- coding: utf-8 -*-
# app/features/tavern.py
from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player
from app.core.config import USE_OPENAI, oai_client

# ИНИЦИАЛИЗАЦИЯ РОУТЕРА
router = Router(name="tavern")

REST_FEE = 10  # стоимость отдыха

# Кэши выбора экипировки: user_id -> ...
_EQUIP_IDX_MAP: Dict[int, List[str]] = {}
_EQUIP_CHOICE: Dict[int, Tuple[str, str]] = {}  # (name, kind: 'weapon'|'armor')

# ---------- КЛАВИАТУРЫ ----------

def tavern_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🛏 Отдохнуть ({REST_FEE} зол.)", callback_data="t_rest"),
         InlineKeyboardButton(text="⚙️ Экипировка", callback_data="t_equip")],
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
        [InlineKeyboardButton(text="↩️ Назад", callback_data="t_back")],
    ])

def unequip_menu_kb(can_weapon: bool, can_armor: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_weapon:
        rows.append([InlineKeyboardButton(text="🗡 Снять оружие", callback_data="t_u_weap")])
    if can_armor:
        rows.append([InlineKeyboardButton(text="🛡 Снять броню", callback_data="t_u_arm")])
    rows.append([InlineKeyboardButton(text="↩️ Назад", callback_data="t_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- РЕПЛИКИ ТРАКТИРЩИКА ----------

async def _npc_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=80,
                messages=[
                    {"role": "system", "content": "Скажи короткую фразу (до 12 слов) от трактирщика. Без Markdown."},
                    {"role": "user", "content": "Темно в городе, ходят слухи о ночных визитёрах. Дай атмосферную реплику."},
                ],
            )
            return f"Хозяин: {resp.choices[0].message.content.strip()}"
        except Exception:
            pass
    return "Хозяин: Раз уж занесло — грейся у огня и держи свечу под рукой."

async def _npc_no_money_line(fee: int) -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=50,
                messages=[
                    {"role": "system", "content": "Одна короткая реплика трактирщика, отказ из-за нехватки денег. Без Markdown."},
                    {"role": "user", "content": f"Гость не может оплатить постой ({fee} монет)."},
                ],
            )
            return f"Хозяин: {resp.choices[0].message.content.strip()}"
        except Exception:
            pass
    return "Хозяин: Эх, дружище, без монет и постель не согреет."

async def _npc_rest_success_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.8, max_tokens=60,
                messages=[
                    {"role": "system", "content": "Одна короткая ободряющая реплика после хорошего отдыха. Без Markdown."},
                    {"role": "user", "content": "Гость выспался и готов к дороге."},
                ],
            )
            return f"Хозяин: {resp.choices[0].message.content.strip()}"
        except Exception:
            pass
    return "Хозяин: Лицо посвежело — значит, кровать честно отработала!"

# ---------- ВСПОМОГАТЕЛЬНОЕ ----------

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

def _weapon_category(name: str) -> str:
    low = (name or "").lower()
    if "лук" in low: return "bow"
    if "посох" in low: return "staff"
    if "булав" in low: return "mace"
    if "молот" in low: return "hammer"
    if "топор" in low: return "axe"
    if "кинжал" in low: return "dagger"
    if "меч" in low: return "sword"
    return "other"

def _armor_material(name: str) -> Optional[str]:
    low = (name or "").lower()
    if "мант" in low: return "robe"
    if "кожан" in low: return "leather"
    if any(x in low for x in ["латы", "латная", "сталь", "желез"]): return "heavy"
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

# ---------- ЭКРАН ТАВЕРНЫ ----------

async def _show_tavern(message: types.Message, user_id: int) -> None:
    p = get_player(user_id)
    if p is None:
        await message.answer("Нет персонажа: набери /start")
        return

    line = await _npc_line()
    await message.answer(
        f"🍺 <b>Таверна</b>\n{line}\n\n"
        f"❤️ Здоровье: {p.hp}/{p.max_hp}\n"
        f"🪙 Монеты: {p.gold}\n"
        f"🛏 Ночлег: {REST_FEE} зол.",
        reply_markup=tavern_menu_kb()
    )

# Открытие по кнопке из городского меню
@router.message(F.text.contains("Таверна"))
async def tavern_open_msg(message: types.Message):
    await _show_tavern(message, message.from_user.id)

# ---------- ОТДЫХ ----------

@router.callback_query(F.data == "t_rest")
async def tavern_rest(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Нет персонажа: набери /start")
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
        f"Ты отдохнул(-а).\n"
        f"{success_line}\n\n"
        f"❤️ Восстановлено: +{heal}\n"
        f"🪙 Осталось монет: {p.gold} (−{REST_FEE})"
    )
    await _show_tavern(cb.message, user_id)

# ---------- ЭКИПИРОВКА ----------

@router.callback_query(F.data == "t_equip")
async def tavern_equip(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Нет персонажа: набери /start")
        return

    items = list(p.inventory.items())
    lines = ["⚙️ <b>Экипировка</b>", "Доступно для надевания:"]
    idx_map: List[str] = []

    for i, (name, cnt) in enumerate(items, start=1):
        low = name.lower()
        kind = "weapon" if any(x in low for x in ["лук","посох","булав","молот","топор","кинжал","меч"]) else (
               "armor" if any(x in low for x in ["мант","кожан","латы","латная","сталь","желез"]) else "consumable")
        if kind == "consumable":
            continue
        lines.append(f"{i}. {'🗡' if kind=='weapon' else '🛡'} {name} (x{cnt})")
        idx_map.append(name)

    if not idx_map:
        await cb.message.answer("Пока нечего надеть.\nЗагляни на рынок.", reply_markup=tavern_menu_kb())
        return

    lines.append("\nВыбери номер предмета (сначала надеть, ниже — можно снять текущее).")
    _EQUIP_IDX_MAP[user_id] = idx_map

    cur_w = (p.equipment or {}).get("weapon") if p.equipment else None
    cur_a = (p.equipment or {}).get("armor") if p.equipment else None
    can_unw, can_una = cur_w is not None, cur_a is not None

    await cb.message.answer("\n".join(lines), reply_markup=equip_pick_kb(list(range(1, len(idx_map)+1))))
    await cb.message.answer("Снять текущее снаряжение?", reply_markup=unequip_menu_kb(can_unw, can_una))

@router.callback_query(F.data.regexp(r"^t_eq_(\d+)$"))
async def tavern_equip_pick(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Нет персонажа: набери /start")
        return

    idx_map: List[str] = _EQUIP_IDX_MAP.get(user_id, [])
    if not idx_map:
        await cb.message.answer("Список пуст. Открой экипировку заново."); return

    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(idx_map)):
        await cb.message.answer("Неверный номер."); return

    name = idx_map[idx]
    low = name.lower()
    kind = "weapon" if any(x in low for x in ["лук","посох","булав","молот","топор","кинжал","меч"]) else "armor"

    if not _class_can_wear(p, name, is_armor=(kind == "armor")):
        await cb.message.answer("Твой класс не может использовать этот предмет.", reply_markup=tavern_menu_kb())
        return

    _EQUIP_CHOICE[user_id] = (name, kind)
    await cb.message.answer(f"Надеть: {name}?", reply_markup=equip_confirm_kb(idx+1))

@router.callback_query(F.data.regexp(r"^t_econf_(\d+)$"))
async def tavern_equip_confirm(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("Нет персонажа: набери /start")
        return

    choice = _EQUIP_CHOICE.pop(user_id, None)
    if not choice:
        await cb.message.answer("Нет выбранного предмета.", reply_markup=tavern_menu_kb()); return

    name, kind = choice
    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("Такого предмета больше нет в сумке.", reply_markup=tavern_menu_kb()); return

    if not p.equipment:
        p.equipment = {}
    p.equipment["weapon" if kind == "weapon" else "armor"] = name
    save_player(p)

    await cb.message.answer(f"Надето: {name} ({'оружие' if kind=='weapon' else 'броня'}).")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_weap")
async def tavern_unequip_weapon(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("weapon"):
        p.equipment["weapon"] = None
        save_player(p)
        await cb.message.answer("Оружие снято.")
    else:
        await cb.message.answer("Нечего снимать.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_arm")
async def tavern_unequip_armor(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("armor"):
        p.equipment["armor"] = None
        save_player(p)
        await cb.message.answer("Броня снята.")
    else:
        await cb.message.answer("Нечего снимать.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_back")
async def tavern_back(cb: types.CallbackQuery):
    await cb.answer()
    await _show_tavern(cb.message, cb.from_user.id)
