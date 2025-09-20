# -*- coding: utf-8 -*-
# app/features/tavern.py
from __future__ import annotations

from typing import List, Dict, Tuple, Optional

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player
from app.core.config import USE_OPENAI, oai_client

# РРќРР¦РРђР›РР—РђР¦РРЇ Р РћРЈРўР•Р Рђ
router = Router(name="tavern")

REST_FEE = 10  # СЃС‚РѕРёРјРѕСЃС‚СЊ РѕС‚РґС‹С…Р°

# РљСЌС€Рё РІС‹Р±РѕСЂР° СЌРєРёРїРёСЂРѕРІРєРё: user_id -> ...
_EQUIP_IDX_MAP: Dict[int, List[str]] = {}
_EQUIP_CHOICE: Dict[int, Tuple[str, str]] = {}  # (name, kind: 'weapon'|'armor')

# ---------- РљР›РђР’РРђРўРЈР Р« ----------

def tavern_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"рџ›Џ РћС‚РґРѕС…РЅСѓС‚СЊ ({REST_FEE} Р·РѕР».)", callback_data="t_rest"),
         InlineKeyboardButton(text="вљ™пёЏ Р­РєРёРїРёСЂРѕРІРєР°", callback_data="t_equip")],
    ])

def equip_pick_kb(keys: List[int]) -> InlineKeyboardMarkup:
    rows, row = [], []
    for n in keys:
        row.append(InlineKeyboardButton(text=str(n), callback_data=f"t_eq_{n}"))
        if len(row) == 4:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ", callback_data="t_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def equip_confirm_kb(slot_idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="вњ… РќР°РґРµС‚СЊ", callback_data=f"t_econf_{slot_idx}")],
        [InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ", callback_data="t_back")],
    ])

def unequip_menu_kb(can_weapon: bool, can_armor: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_weapon:
        rows.append([InlineKeyboardButton(text="рџ—Ў РЎРЅСЏС‚СЊ РѕСЂСѓР¶РёРµ", callback_data="t_u_weap")])
    if can_armor:
        rows.append([InlineKeyboardButton(text="рџ›Ў РЎРЅСЏС‚СЊ Р±СЂРѕРЅСЋ", callback_data="t_u_arm")])
    rows.append([InlineKeyboardButton(text="в†©пёЏ РќР°Р·Р°Рґ", callback_data="t_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- Р Р•РџР›РРљР РўР РђРљРўРР Р©РРљРђ (РІСЃРµРіРґР° РєСѓСЂСЃРёРІРѕРј Рё СЃ рџ‘ґ) ----------

def _wrap_barkeeper(text: str) -> str:
    text = (text or "").strip()
    # Р•СЃР»Рё СѓР¶Рµ РІ РєР°РІС‹С‡РєР°С… вЂ” РЅРµ РґСѓР±Р»РёСЂСѓРµРј
    if not (text.startswith("В«") or text.startswith('"')):
        text = f'В«{text}В»'
    return f'рџ‘ґ <i>РўСЂР°РєС‚РёСЂС‰РёРє: {text}</i>'

async def _npc_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=80,
                messages=[
                    {"role": "system", "content": "РљРѕСЂРѕС‚РєР°СЏ Р°С‚РјРѕСЃС„РµСЂРЅР°СЏ СЂРµРїР»РёРєР° С‚СЂР°РєС‚РёСЂС‰РёРєР° (РґРѕ 12 СЃР»РѕРІ). Р‘РµР· СЂР°Р·РјРµС‚РєРё."},
                    {"role": "user", "content": "РўРµРјРЅРѕ РІ РіРѕСЂРѕРґРµ, С…РѕРґСЏС‚ СЃР»СѓС…Рё Рѕ РЅРѕС‡РЅС‹С… РІРёР·РёС‚С‘СЂР°С…."},
                ],
            )
            return _wrap_barkeeper(resp.choices[0].message.content)
        except Exception:
            pass
    return _wrap_barkeeper("Р Р°Р· СѓР¶ Р·Р°РЅРµСЃР»Рѕ вЂ” РіСЂРµР№СЃСЏ Сѓ РѕРіРЅСЏ Рё РґРµСЂР¶Рё СЃРІРµС‡Сѓ РїРѕРґ СЂСѓРєРѕР№.")

async def _npc_no_money_line(fee: int) -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.9, max_tokens=50,
                messages=[
                    {"role": "system", "content": "РљРѕСЂРѕС‚РєР°СЏ СЂРµРїР»РёРєР° С‚СЂР°РєС‚РёСЂС‰РёРєР° СЃ РѕС‚РєР°Р·РѕРј РёР·-Р·Р° РЅРµС…РІР°С‚РєРё РґРµРЅРµРі. Р‘РµР· СЂР°Р·РјРµС‚РєРё."},
                    {"role": "user", "content": f"Р“РѕСЃС‚СЊ РЅРµ РјРѕР¶РµС‚ РѕРїР»Р°С‚РёС‚СЊ РїРѕСЃС‚РѕР№ ({fee} РјРѕРЅРµС‚)."},
                ],
            )
            return _wrap_barkeeper(resp.choices[0].message.content)
        except Exception:
            pass
    return _wrap_barkeeper("Р­С…, РґСЂСѓР¶РёС‰Рµ, Р±РµР· РјРѕРЅРµС‚ Рё РїРѕСЃС‚РµР»СЊ РЅРµ СЃРѕРіСЂРµРµС‚.")

async def _npc_rest_success_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini", temperature=0.8, max_tokens=60,
                messages=[
                    {"role": "system", "content": "РљРѕСЂРѕС‚РєР°СЏ РѕР±РѕРґСЂСЏСЋС‰Р°СЏ СЂРµРїР»РёРєР° С‚СЂР°РєС‚РёСЂС‰РёРєР° РїРѕСЃР»Рµ С…РѕСЂРѕС€РµРіРѕ РѕС‚РґС‹С…Р°. Р‘РµР· СЂР°Р·РјРµС‚РєРё."},
                    {"role": "user", "content": "Р“РѕСЃС‚СЊ РІС‹СЃРїР°Р»СЃСЏ Рё РіРѕС‚РѕРІ Рє РґРѕСЂРѕРіРµ."},
                ],
            )
            return _wrap_barkeeper(resp.choices[0].message.content)
        except Exception:
            pass
    return _wrap_barkeeper("Р›РёС†Рѕ РїРѕСЃРІРµР¶РµР»Рѕ вЂ” Р·РЅР°С‡РёС‚, РєСЂРѕРІР°С‚СЊ С‡РµСЃС‚РЅРѕ РѕС‚СЂР°Р±РѕС‚Р°Р»Р°!")

# ---------- Р’РЎРџРћРњРћР“РђРўР•Р›Р¬РќРћР• ----------

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
    if "Р»СѓРє" in low: return "bow"
    if "РїРѕСЃРѕС…" in low: return "staff"
    if "Р±СѓР»Р°РІ" in low: return "mace"
    if "РјРѕР»РѕС‚" in low: return "hammer"
    if "С‚РѕРїРѕСЂ" in low: return "axe"
    if "РєРёРЅР¶Р°Р»" in low: return "dagger"
    if "РјРµС‡" in low: return "sword"
    return "other"

def _armor_material(name: str) -> Optional[str]:
    low = (name or "").lower()
    if "РјР°РЅС‚" in low: return "robe"
    if "РєРѕР¶Р°РЅ" in low: return "leather"
    if any(x in low for x in ["Р»Р°С‚С‹", "Р»Р°С‚РЅР°СЏ", "СЃС‚Р°Р»СЊ", "Р¶РµР»РµР·"]): return "heavy"
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

# ---------- Р­РљР РђРќ РўРђР’Р•Р РќР« ----------

async def _show_tavern(message: types.Message, user_id: int) -> None:
    p = get_player(user_id)
    if p is None:
        await message.answer("РќРµС‚ РїРµСЂСЃРѕРЅР°Р¶Р°: РЅР°Р±РµСЂРё /start")
        return

    line = await _npc_line()
    await message.answer(
        f"рџЌє <b>РўР°РІРµСЂРЅР°</b>\n{line}\n\n"
        f"вќ¤пёЏ Р—РґРѕСЂРѕРІСЊРµ: {p.hp}/{p.max_hp}\n"
        f"рџЄ™ РњРѕРЅРµС‚С‹: {p.gold}\n"
        f"рџ›Џ РќРѕС‡Р»РµРі: {REST_FEE} Р·РѕР».",
        reply_markup=tavern_menu_kb()
    )

# РћС‚РєСЂС‹С‚РёРµ РїРѕ РєРЅРѕРїРєРµ РёР· РіРѕСЂРѕРґСЃРєРѕРіРѕ РјРµРЅСЋ
@router.message(F.text.contains("РўР°РІРµСЂРЅР°"))
async def tavern_open_msg(message: types.Message):
    await _show_tavern(message, message.from_user.id)

# ---------- РћРўР”Р«РҐ ----------

@router.callback_query(F.data == "t_rest")
async def tavern_rest(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("РќРµС‚ РїРµСЂСЃРѕРЅР°Р¶Р°: РЅР°Р±РµСЂРё /start")
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
        f"РўС‹ РѕС‚РґРѕС…РЅСѓР»(-Р°).\n"
        f"{success_line}\n\n"
        f"вќ¤пёЏ Р’РѕСЃСЃС‚Р°РЅРѕРІР»РµРЅРѕ: +{heal}\n"
        f"рџЄ™ РћСЃС‚Р°Р»РѕСЃСЊ РјРѕРЅРµС‚: {p.gold} (в€’{REST_FEE})"
    )
    await _show_tavern(cb.message, user_id)

# ---------- Р­РљРРџРР РћР’РљРђ ----------

@router.callback_query(F.data == "t_equip")
async def tavern_equip(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("РќРµС‚ РїРµСЂСЃРѕРЅР°Р¶Р°: РЅР°Р±РµСЂРё /start")
        return

    items = list(p.inventory.items())
    lines = ["вљ™пёЏ <b>Р­РєРёРїРёСЂРѕРІРєР°</b>", "Р”РѕСЃС‚СѓРїРЅРѕ РґР»СЏ РЅР°РґРµРІР°РЅРёСЏ:"]
    idx_map: List[str] = []

    for i, (name, cnt) in enumerate(items, start=1):
        low = name.lower()
        kind = "weapon" if any(x in low for x in ["Р»СѓРє","РїРѕСЃРѕС…","Р±СѓР»Р°РІ","РјРѕР»РѕС‚","С‚РѕРїРѕСЂ","РєРёРЅР¶Р°Р»","РјРµС‡"]) else (
               "armor" if any(x in low for x in ["РјР°РЅС‚","РєРѕР¶Р°РЅ","Р»Р°С‚С‹","Р»Р°С‚РЅР°СЏ","СЃС‚Р°Р»СЊ","Р¶РµР»РµР·"]) else "consumable")
        if kind == "consumable":
            continue
        lines.append(f"{i}. {'рџ—Ў' if kind=='weapon' else 'рџ›Ў'} {name} (x{cnt})")
        idx_map.append(name)

    if not idx_map:
        await cb.message.answer("РџРѕРєР° РЅРµС‡РµРіРѕ РЅР°РґРµС‚СЊ.\nР—Р°РіР»СЏРЅРё РЅР° СЂС‹РЅРѕРє.", reply_markup=tavern_menu_kb())
        return

    lines.append("\nР’С‹Р±РµСЂРё РЅРѕРјРµСЂ РїСЂРµРґРјРµС‚Р° (СЃРЅР°С‡Р°Р»Р° РЅР°РґРµС‚СЊ, РЅРёР¶Рµ вЂ” РјРѕР¶РЅРѕ СЃРЅСЏС‚СЊ С‚РµРєСѓС‰РµРµ).")
    _EQUIP_IDX_MAP[user_id] = idx_map

    cur_w = (p.equipment or {}).get("weapon") if p.equipment else None
    cur_a = (p.equipment or {}).get("armor") if p.equipment else None
    can_unw, can_una = cur_w is not None, cur_a is not None

    await cb.message.answer("\n".join(lines), reply_markup=equip_pick_kb(list(range(1, len(idx_map)+1))))
    await cb.message.answer("РЎРЅСЏС‚СЊ С‚РµРєСѓС‰РµРµ СЃРЅР°СЂСЏР¶РµРЅРёРµ?", reply_markup=unequip_menu_kb(can_unw, can_una))

@router.callback_query(F.data.regexp(r"^t_eq_(\d+)$"))
async def tavern_equip_pick(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("РќРµС‚ РїРµСЂСЃРѕРЅР°Р¶Р°: РЅР°Р±РµСЂРё /start")
        return

    idx_map: List[str] = _EQUIP_IDX_MAP.get(user_id, [])
    if not idx_map:
        await cb.message.answer("РЎРїРёСЃРѕРє РїСѓСЃС‚. РћС‚РєСЂРѕР№ СЌРєРёРїРёСЂРѕРІРєСѓ Р·Р°РЅРѕРІРѕ."); return

    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(idx_map)):
        await cb.message.answer("РќРµРІРµСЂРЅС‹Р№ РЅРѕРјРµСЂ."); return

    name = idx_map[idx]
    low = name.lower()
    kind = "weapon" if any(x in low for x in ["Р»СѓРє","РїРѕСЃРѕС…","Р±СѓР»Р°РІ","РјРѕР»РѕС‚","С‚РѕРїРѕСЂ","РєРёРЅР¶Р°Р»","РјРµС‡"]) else "armor"

    if not _class_can_wear(p, name, is_armor=(kind == "armor")):
        await cb.message.answer("РўРІРѕР№ РєР»Р°СЃСЃ РЅРµ РјРѕР¶РµС‚ РёСЃРїРѕР»СЊР·РѕРІР°С‚СЊ СЌС‚РѕС‚ РїСЂРµРґРјРµС‚.", reply_markup=tavern_menu_kb())
        return

    _EQUIP_CHOICE[user_id] = (name, kind)
    await cb.message.answer(f"РќР°РґРµС‚СЊ: {name}?", reply_markup=equip_confirm_kb(idx+1))

@router.callback_query(F.data.regexp(r"^t_econf_(\d+)$"))
async def tavern_equip_confirm(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p is None:
        await cb.message.answer("РќРµС‚ РїРµСЂСЃРѕРЅР°Р¶Р°: РЅР°Р±РµСЂРё /start")
        return

    choice = _EQUIP_CHOICE.pop(user_id, None)
    if not choice:
        await cb.message.answer("РќРµС‚ РІС‹Р±СЂР°РЅРЅРѕРіРѕ РїСЂРµРґРјРµС‚Р°.", reply_markup=tavern_menu_kb()); return

    name, kind = choice
    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("РўР°РєРѕРіРѕ РїСЂРµРґРјРµС‚Р° Р±РѕР»СЊС€Рµ РЅРµС‚ РІ СЃСѓРјРєРµ.", reply_markup=tavern_menu_kb()); return

    if not p.equipment:
        p.equipment = {}
    p.equipment["weapon" if kind == "weapon" else "armor"] = name
    save_player(p)

    await cb.message.answer(f"РќР°РґРµС‚Рѕ: {name} ({'РѕСЂСѓР¶РёРµ' if kind=='weapon' else 'Р±СЂРѕРЅСЏ'}).")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_weap")
async def tavern_unequip_weapon(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("weapon"):
        p.equipment["weapon"] = None
        save_player(p)
        await cb.message.answer("РћСЂСѓР¶РёРµ СЃРЅСЏС‚Рѕ.")
    else:
        await cb.message.answer("РќРµС‡РµРіРѕ СЃРЅРёРјР°С‚СЊ.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_u_arm")
async def tavern_unequip_armor(cb: types.CallbackQuery):
    await cb.answer()
    user_id = cb.from_user.id
    p = get_player(user_id)
    if p and p.equipment and p.equipment.get("armor"):
        p.equipment["armor"] = None
        save_player(p)
        await cb.message.answer("Р‘СЂРѕРЅСЏ СЃРЅСЏС‚Р°.")
    else:
        await cb.message.answer("РќРµС‡РµРіРѕ СЃРЅРёРјР°С‚СЊ.")
    await _show_tavern(cb.message, user_id)

@router.callback_query(F.data == "t_back")
async def tavern_back(cb: types.CallbackQuery):
    await cb.answer()
    await _show_tavern(cb.message, cb.from_user.id)



