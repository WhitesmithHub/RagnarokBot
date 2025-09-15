# -*- coding: utf-8 -*-
# app/features/tavern.py
from __future__ import annotations

from typing import List, Dict

from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.core.storage import get_player, save_player
from app.ui.keyboards import city_menu_kb
from app.core.config import USE_OPENAI, oai_client

router = Router()

# ---------- Клавиатуры ----------

def tavern_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛌 Отдохнуть", callback_data="t_rest"),
         InlineKeyboardButton(text="💾 Сохранить", callback_data="t_save")],
        [InlineKeyboardButton(text="⚔ Экипировка", callback_data="t_equip")],
        [InlineKeyboardButton(text="🏘️ В город", callback_data="t_town")],
    ])

def equip_pick_kb(keys: List[int]) -> InlineKeyboardMarkup:
    rows = []
    row = []
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

# ---------- Трактир ----------

async def _npc_line() -> str:
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.9,
                max_tokens=80,
                messages=[
                    {"role": "system", "content": "Одна короткая тёплая реплика трактирщика-старика (1–2 предложения). Без Markdown."},
                    {"role": "user", "content": "Городская таверна, герой заходит отдохнуть."},
                ],
            )
            return f"👴 Трактирщик: «{resp.choices[0].message.content.strip()}»"
        except Exception:
            pass
    return "👴 Трактирщик: «Добро пожаловать, странник! У нас всегда найдётся место и кружка эля для поднятия духа.»"

@router.message(F.text.in_(["🍺 Таверна", "Таверна"]))
async def tavern_open(message: types.Message):
    p = get_player(message.from_user.id)
    line = await _npc_line()
    await message.answer(
        f"🍺 <b>Таверна</b>\n{line}\n\nЗдоровье: {p.hp}/{p.max_hp}\nЗолото: {p.gold}",
        reply_markup=tavern_menu_kb()
    )

# ---------- Отдых / сохранение ----------

@router.callback_query(F.data == "t_rest")
async def tavern_rest(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)

    # восстановление полностью + перезаряд умений
    heal = p.max_hp - p.hp
    p.hp = p.max_hp

    from app.features.character import ability_uses_for_level
    charges: Dict[str, int] = {}
    for key, lvl in (p.abilities_known or {}).items():
        mx = ability_uses_for_level(key, lvl, p.class_key)
        if mx > 0:
            charges[key] = mx
    p.ability_charges = charges
    save_player(p)

    await cb.message.answer(
        f"🛌 Ты отдыхаешь и чувствуешь прилив сил.\n❤️ Здоровье: {p.hp}/{p.max_hp} (+{heal})"
    )
    await tavern_open(cb.message)

@router.callback_query(F.data == "t_save")
async def tavern_save(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)

    fee = 5  # цена сохранения
    if p.gold < fee:
        await cb.message.answer("👴 Трактирщик: «Эй, без денег — без постели! Проваливай.»")
        # но по ТЗ прогресс всё равно сохраняется (без бонусов)
    else:
        p.gold -= fee
        save_player(p)
        await cb.message.answer(f"💾 Игра сохранена. Золото -{fee}. 👛 {p.gold}")
    # здесь можно добавить фактическую запись snapshot в файлы
    await tavern_open(cb.message)

# ---------- Экипировка ----------

def _class_can_wear(p, item_name: str, is_armor: bool, material: str | None) -> bool:
    """
    Ограничения:
    - Робу/рясы/мантии (material='robe') НЕ могут носить: Мечник/Лучник/Вор/Торговец и их ветки.
    - Тяжёлая/металл (по словам 'латы','кольчуг','панцир') запрещена для Послушника/Мага и их веток.
    """
    low = (item_name or "").lower()
    ck = (p.class_key or "").lower()

    if is_armor:
        if material == "robe":
            if any(x in ck for x in ["swordsman","archer","thief","merchant"]):
                return False
        if any(x in low for x in ["латы","кольчуг","панцир","тяж"]):
            if any(x in ck for x in ["acolyte","mage"]):
                return False
    else:
        # оружие: тривиальные запреты можно расширить позже
        pass
    return True

@router.callback_query(F.data == "t_equip")
async def tavern_equip(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)

    # список кандидатов из инвентаря
    items = list(p.inventory.items())
    if not items:
        await cb.message.answer("⚔ Экипировка\nОружия нет.\n\nБрони нет.", reply_markup=tavern_menu_kb())
        return

    lines = ["⚔ <b>Экипировка</b>", "Оружие:"]
    idx_map: List[str] = []
    # показываем только подходящее?
    for i, (name, cnt) in enumerate(items, start=1):
        low = name.lower()
        kind = "weapon" if any(x in low for x in ["меч","сабл","клинок","кинжал","нож","топор","лук","посох","булав","жезл"]) else (
               "armor" if any(x in low for x in ["брон","латы","кольчуг","панцир","роб","ряса","мант"]) else "consumable")
        material = "leather" if "кожан" in low else ("robe" if any(x in low for x in ["роб","ряса","мант"]) else None)

        if kind == "weapon":
            lines.append(f"{i}. 🗡️ {name} (×{cnt})")
        elif kind == "armor":
            lines.append(f"{i}. 🛡️ {name} (×{cnt})")
        else:
            # расходники тут не предлагаем надеть
            continue

        idx_map.append(name)

    if not idx_map:
        lines.append("\nНечего надевать.")
        await cb.message.answer("\n".join(lines), reply_markup=tavern_menu_kb())
        return

    # покажем текущую экипировку и меню «снять»
    cur_w = (p.equipment or {}).get("weapon") if p.equipment else None
    cur_a = (p.equipment or {}).get("armor") if p.equipment else None
    lines.append("\nНажми номер, что надеть (🗡️ — оружие, 🛡️ — броня).")

    can_unw = cur_w is not None
    can_una = cur_a is not None
    await cb.message.answer("\n".join(lines), reply_markup=equip_pick_kb(list(range(1, len(idx_map)+1))))
    await cb.message.answer("Снять экипировку?", reply_markup=unequip_menu_kb(can_unw, can_una))

    # привяжем карту индексов к сообщению
    cb.message.eq_map = idx_map

@router.callback_query(F.data.regexp(r"^t_eq_(\d+)$"))
async def tavern_equip_pick(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    idx_map: List[str] = getattr(cb.message, "eq_map", [])
    if not idx_map:
        await cb.message.answer("Список устарел. Откройте заново «Экипировку»."); return
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(idx_map)):
        await cb.message.answer("Нет такого номера."); return

    name = idx_map[idx]
    # определим тип
    low = name.lower()
    kind = "weapon" if any(x in low for x in ["меч","сабл","клинок","кинжал","нож","топор","лук","посох","булав","жезл"]) else (
           "armor" if any(x in low for x in ["брон","латы","кольчуг","панцир","роб","ряса","мант"]) else "consumable")
    material = "leather" if "кожан" in low else ("robe" if any(x in low for x in ["роб","ряса","мант"]) else None)

    if kind == "consumable":
        await cb.message.answer("Этот предмет нельзя надеть.", reply_markup=tavern_menu_kb()); return

    # проверка класса/материала
    if not _class_can_wear(p, name, is_armor=(kind=="armor"), material=material):
        await cb.message.answer(
            "Этот предмет не подходит для вашего класса.",
            reply_markup=tavern_menu_kb()
        )
        return

    # карточка + подтверждение
    await cb.message.answer(f"Выбран предмет: {name}\nНадеть?", reply_markup=equip_confirm_kb(idx+1))
    cb.message.eq_choice = (name, kind)

@router.callback_query(F.data.regexp(r"^t_econf_(\d+)$"))
async def tavern_equip_confirm(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    choice = getattr(cb.message, "eq_choice", None)
    if not choice:
        await cb.message.answer("Выбор устарел. Откройте заново «Экипировку».", reply_markup=tavern_menu_kb()); return
    name, kind = choice

    if p.inventory.get(name, 0) <= 0:
        await cb.message.answer("Такого предмета уже нет в инвентаре.", reply_markup=tavern_menu_kb()); return

    if not p.equipment:
        p.equipment = {}
    # экипируем (предыдущий предмет не удаляем, он «в сундук» — остаётся в инвентаре)
    p.equipment["weapon" if kind == "weapon" else "armor"] = name
    save_player(p)

    await cb.message.answer(f"✅ Надето: {name} ({'оружие' if kind=='weapon' else 'броня'}).")
    await tavern_open(cb.message)

@router.callback_query(F.data == "t_u_weap")
async def tavern_unequip_weapon(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    if p.equipment and p.equipment.get("weapon"):
        p.equipment["weapon"] = None
        save_player(p)
        await cb.message.answer("🗡️ Оружие снято.")
    else:
        await cb.message.answer("Оружие не надето.")
    await tavern_open(cb.message)

@router.callback_query(F.data == "t_u_arm")
async def tavern_unequip_armor(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    if p.equipment and p.equipment.get("armor"):
        p.equipment["armor"] = None
        save_player(p)
        await cb.message.answer("🛡️ Броня снята.")
    else:
        await cb.message.answer("Броня не надета.")
    await tavern_open(cb.message)

@router.callback_query(F.data == "t_back")
async def tavern_back(cb: types.CallbackQuery):
    await cb.answer()
    await tavern_open(cb.message)

@router.callback_query(F.data == "t_town")
async def tavern_to_town(cb: types.CallbackQuery):
    await cb.answer()
    from app.features.city import go_city
    await go_city(cb.message)
