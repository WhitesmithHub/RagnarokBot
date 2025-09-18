# -*- coding: utf-8 -*-
# app/features/dungeon.py
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional, Dict, List

from aiogram import Router, F, types

from app.core.storage import get_player, save_player
from app.ui.keyboards import room_actions_kb, combat_actions_kb, skills_pick_kb, dungeon_pick_kb, confirm_leave_dungeon_kb
from app.core.config import USE_OPENAI, oai_client
from app.features.market import clear_market_for_player

router = Router()
_rng = random.SystemRandom()

@dataclass
class RoomState:
    room_id: int = 1
    camped: bool = False
    has_exit: bool = True
    in_combat: bool = False
    enemy: Optional[str] = None
    enemy_hp: int = 0
    dungeon_name: Optional[str] = None

# ---------- GPT-хелпер ----------
async def _gpt(sys: str, usr: str, max_tokens: int = 180) -> str:
    if not USE_OPENAI or oai_client is None:
        return usr
    try:
        r = await oai_client.chat.completions.create(
            model="gpt-4o-mini", temperature=0.95, max_tokens=max_tokens,
            messages=[{"role":"system","content":sys},{"role":"user","content":usr}],
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return usr

def _ensure_state(p):
    if not hasattr(p, "dng") or p.dng is None:
        p.dng = RoomState()

# ---------- Вход: выбор подземелий ----------
async def show_dungeon_picker(message: types.Message):
    p = get_player(message.from_user.id)
    if not p:
        await message.answer("Сначала создай персонажа: /start"); return
    names = getattr(p, "dungeon_names", None) or ["Замок Теней","Катакомбы Мрака","Пещеры Шёпота"]
    await message.answer("Выбери подземелье:", reply_markup=dungeon_pick_kb(names))

@router.message(F.text.in_(["🕳️ Подземелья", "Подземелья"]))
async def dungeons_entry(message: types.Message):
    await show_dungeon_picker(message)

@router.callback_query(F.data == "dng_back_city")
async def dng_back_city(cb: types.CallbackQuery):
    await cb.answer()
    from app.features.city import go_city
    await go_city(cb.message)

@router.callback_query(F.data.regexp(r"^dng_pick_(\d+)$"))
async def choose_dungeon(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    names: List[str] = getattr(p, "dungeon_names", None) or ["Замок Теней","Катакомбы Мрака","Пещеры Шёпота"]
    idx = int(cb.data.split("_")[-1]) - 1
    if not (0 <= idx < len(names)):
        await cb.message.answer("Нет такого варианта."); return
    picked = names[idx]

    # Случайное событие до входа
    event_type = _rng.choice(["bandits","blessing","merchants","trap","omen"])
    delta_hp = 0; delta_gold = 0; bonus_item: Optional[str] = None

    if event_type == "bandits":
        loss = min(p.gold, _rng.randrange(3, 10))
        delta_gold = -loss; p.gold += delta_gold
        sys = "Литературно, 3–6 предложений, герой один. Добавь короткий диалог."
        usr = f"{p.name} у ворот «{picked}» сталкивается с бандитами и теряет немного золота."
    elif event_type == "blessing":
        heal = min(p.max_hp - p.hp, _rng.randrange(2, 6))
        delta_hp = heal; p.hp += heal
        sys = "Литературно, 3–6 предложений, герой один; благословение и лёгкое исцеление."
        usr = f"По дороге к «{picked}» странник-монах благословляет героя."
    elif event_type == "merchants":
        bonus_item = _rng.choice(["Провиант","Набор для костра"])
        p.inventory[bonus_item] = p.inventory.get(bonus_item,0)+1
        sys = "Литературно, 3–6 предложений; короткий торг с караваном и удачная мелочь."
        usr = f"Перед «{picked}» караван, герой выторговывает предмет: {bonus_item}."
    elif event_type == "trap":
        dmg = _rng.randrange(1, 4)
        delta_hp = -min(p.hp, dmg); p.hp += delta_hp
        sys = "Литературно, 3–6 предложений. Ловушка причиняет боль, но герой выживает."
        usr = f"На тропе к «{picked}» скрыт капкан; герой получает урон."
    else:
        sys = "Литературно, 3–6 предложений. Зловещее предзнаменование, герой собирается с духом."
        usr = f"Перед «{picked}» герой видит дурной знак, но решается идти дальше."

    save_player(p)
    prose = await _gpt(sys, usr, 220)
    tail = []
    if delta_gold: tail.append(f"👛 Золото: {p.gold} ({'−' if delta_gold<0 else '+'}{abs(delta_gold)})")
    if delta_hp:   tail.append(f"❤️ HP: {p.hp}/{p.max_hp} ({'−' if delta_hp<0 else '+'}{abs(delta_hp)})")
    if bonus_item: tail.append(f"🎁 Получено: {bonus_item}")
    tail_text = ("\n" + "\n".join(tail)) if tail else ""
    await cb.message.answer(f"🛤 {prose}{tail_text}")

    # Инициализируем комнату
    _ensure_state(p)
    p.dng = RoomState(room_id=1, camped=False, has_exit=True, in_combat=False, dungeon_name=picked)
    save_player(p)

    enter = await _gpt(
        "Единственное число героя. 3–6 предложений: вход и первый зал подземелья.",
        f"{p.name} входит в «{picked}». Холод, сырость и далёкое эхо капель."
    )
    await cb.message.answer(f"🚶 Ты входишь в «{picked}».\n{enter}",
                            reply_markup=room_actions_kb(can_camp=True, has_exit=True))

# ---------- Действия в комнате ----------
@router.callback_query(F.data == "dng_search")
async def dng_search(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st: RoomState = getattr(p, "dng", RoomState())
    desc = await _gpt(
        "Единственное число героя. 2–4 предложения, короткое описание того, что видит герой в комнате подземелья.",
        f"{p.name} осматривает зал «{st.dungeon_name or 'подземелье'}»."
    )
    # 50% пусто, 30% ресурсы, 20% предмет
    roll = _rng.random()
    found = ""
    if roll < 0.5:
        found = "Ничего полезного не находится."
    elif roll < 0.8:
        pick = _rng.choice(["Железо", "Самоцвет", "Травы", "Кость древнего зверя"])
        p.inventory[pick] = p.inventory.get(pick, 0) + 1
        save_player(p)
        found = f"Находка: {pick} (×1)."
    else:
        pick = _rng.choice(["Провиант", "Набор для костра", "Кинжал", "Лук охотника"])
        p.inventory[pick] = p.inventory.get(pick, 0) + 1
        save_player(p)
        found = f"Кажется, повезло: {pick}."
    await cb.message.answer(f"🔎 {desc}\n\n{found}",
                            reply_markup=room_actions_kb(can_camp=not st.camped, has_exit=True))

@router.callback_query(F.data == "dng_camp")
async def dng_camp(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st: RoomState = getattr(p, "dng", RoomState())
    if st.camped:
        await cb.message.answer("Здесь уже был привал.", reply_markup=room_actions_kb(can_camp=False, has_exit=True)); return
    if p.inventory.get("Набор для костра", 0) <= 0:
        await cb.message.answer("У вас нет набора для костра.", reply_markup=room_actions_kb(can_camp=False, has_exit=True)); return

    p.inventory["Набор для костра"] -= 1
    if p.inventory["Набор для костра"] <= 0:
        del p.inventory["Набор для костра"]

    heal = min(p.max_hp - p.hp, _rng.randrange(3, 7))
    p.hp += heal
    # Простейшая перезарядка умений: +1 к максимуму для каждого изученного, но не выше 5
    for k, lvl in (p.ability_charges or {}).items():
        mx = min(5, (p.abilities_known.get(k,1) + 2))
        p.ability_charges[k] = mx
    st.camped = True
    save_player(p)

    prose = await _gpt(
        "Единственное число героя. 2–4 предложения о коротком привале в мрачном зале; уникальная формулировка каждый раз.",
        f"{p.name} разводит маленький костёр и отдыхает, прислушиваясь к шёпоту из каменных щелей."
    )
    charges_line = " ".join([f"{k}: {p.ability_charges.get(k,0)}/{p.ability_charges.get(k,0)} (+1)" for k in (p.ability_charges or {})]) or "—"
    await cb.message.answer(f"🔥 {prose}\n\n❤️ Здоровье: {p.hp}/{p.max_hp} (+{heal})\n{charges_line}",
                            reply_markup=room_actions_kb(can_camp=False, has_exit=True))

@router.callback_query(F.data == "dng_next")
async def dng_next(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st: RoomState = getattr(p, "dng", RoomState())
    st.room_id += 1
    st.camped = False
    save_player(p)

    prose = await _gpt(
        "Единственное число героя. 2–4 предложения: герой идёт дальше по мрачному подземелью; атмосферно.",
        f"{p.name} углубляется в «{st.dungeon_name or 'подземелье'}», коридоры сужаются, воздух тяжелее."
    )
    await cb.message.answer(f"➡️ {prose}",
                            reply_markup=room_actions_kb(can_camp=True, has_exit=True))

# ---------- Выход ----------
@router.callback_query(F.data == "dng_escape")
async def dng_escape(cb: types.CallbackQuery):
    await cb.answer()
    await cb.message.answer("Покинуть подземелье?", reply_markup=confirm_leave_dungeon_kb())

@router.callback_query(F.data == "dng_leave_yes")
async def dng_leave_yes(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    # Обновим рынок после выхода
    clear_market_for_player(cb.from_user.id)
    picked = getattr(p, "dng", RoomState()).dungeon_name or "подземелье"
    await cb.message.answer(f"⬆️ Ты покидаешь «{picked}».")
    from app.features.city import go_city
    await go_city(cb.message)

@router.callback_query(F.data == "dng_leave_no")
async def dng_leave_no(cb: types.CallbackQuery):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st: RoomState = getattr(p, "dng", RoomState())
    await cb.message.answer("Остаёшься ещё ненадолго.",
                            reply_markup=room_actions_kb(can_camp=not st.camped, has_exit=True))
