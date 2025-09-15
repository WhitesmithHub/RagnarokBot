# -*- coding: utf-8 -*-
# app/features/dungeon.py
from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from app.core.storage import get_player, save_player
from app.core.monsters import theme_names_from_story, roll_monster
from app.core.dice import d, roll, check_dc
from app.core.emoji import decorate_item_name
from app.ui.keyboards import (
    dungeon_pick_kb, room_actions_kb, confirm_leave_dungeon_kb,
    combat_actions_kb, skills_pick_kb, back_to_city_kb
)
from app.features.market import clear_market_for_player
from app.core.config import USE_OPENAI, oai_client

router = Router()

MAX_ROOMS_PER_FLOOR = 10

@dataclass
class DungeonState:
    active: bool = False
    theme: str = ""
    floor: int = 1
    room: int = 0
    found_exit: bool = False
    camped_in_room: bool = False
    in_combat: bool = False
    enemy: Optional[dict] = None
    turn: str = "player"
    player_defending: bool = False  # флаг защиты на ход

def _get_dng(user_id: int) -> DungeonState:
    p = get_player(user_id)
    if not hasattr(p, "dungeon"):
        p.dungeon = DungeonState().__dict__
        save_player(p)
    return DungeonState(**p.dungeon)

def _save_dng(user_id: int, st: DungeonState):
    p = get_player(user_id)
    p.dungeon = asdict(st)
    save_player(p)

def _reset_ability_charges(p):
    from app.features.character import ability_uses_for_level
    p.ability_charges = p.__dict__.get("ability_charges", {})
    p.ability_charges.clear()
    for key, lvl in (p.abilities_known or {}).items():
        uses = ability_uses_for_level(key, lvl, p.class_key)
        if uses > 0:
            p.ability_charges[key] = uses
    save_player(p)

def _room_text(st: DungeonState) -> str:
    return f"🕳️ <b>{st.theme}</b>\nЭтаж: {st.floor} | Комната: {st.room}/{MAX_ROOMS_PER_FLOOR}"

# -------- Генераторы текста (ОДИН герой) --------

async def generate_travel_text(city: str, theme: str, name: str, gender: str) -> str:
    if not USE_OPENAI or oai_client is None:
        return (f"🚶 Путь из {city} к «{theme}» тянется через сумрачные перелески. "
                f"{name} идёт один, прислушиваясь к каждому шороху.")
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.95,
            max_tokens=180,
            messages=[
                {"role": "system", "content": (
                    "Опиши 2–4 предложения о дороге ОДИНОКОГО героя из города к подземелью. "
                    "Единственное число, третье лицо. Без Markdown."
                )},
                {"role": "user", "content": f"Герой: {name} ({'м' if gender=='male' else 'ж'})\nГород: {city}\nПодземелье: {theme}"}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return (f"{name} оставляет позади {city}. Тропа к «{theme}» уходит в сумрак — он идёт один и внимателен к темноте."
                if gender == "male" else
                f"{name} оставляет позади {city}. Тропа к «{theme}» уходит в сумрак — она идёт одна и внимательна к темноте.")

async def generate_travel_event(city: str, name: str, gender: str) -> tuple[str, Dict[str, int]]:
    """
    Вернёт (литературный текст, {'hp':±N,'gold':±N}).
    Форматим одиночного героя. Внутри текста не пишем сухие цифры — ниже добавим сводку.
    """
    if not USE_OPENAI or oai_client is None:
        if d(100) <= 40:
            heal = d(6)+2
            t = (f"✨ По дороге {name} находит чистый источник и ощущает благословение воды — силы возвращаются.")
            return t, {"hp": heal}
        if d(100) <= 50:
            loss = d(12)+6
            t = (f"🪤 Бандиты вымогают плату за «безопасный путь». Приходится расстаться с частью монет.")
            return t, {"gold": -loss}
        gain = d(10)+5
        t = (f"🧺 Доброжелательный торговец делится провизией и мелкими монетами — дорога кажется легче.")
        return t, {"gold": gain}
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.95,
            max_tokens=240,
            messages=[
                {"role": "system", "content": (
                    "Сгенерируй одно случайное дорожное событие для ОДИНОКОГО героя (2–4 предложения), с уместными эмодзи. "
                    "Без множественного числа, только один герой. В конце на новой строке добавь строго: "
                    "EFFECT: HP=+N/HP=-N или GOLD=+N/GOLD=-N (только один параметр)."
                )},
                {"role": "user", "content": f"Город отправления: {city}\nГерой: {name} ({'м' if gender=='male' else 'ж'})"}
            ],
        )
        text = resp.choices[0].message.content.strip()
        eff = {"hp": 0, "gold": 0}
        import re
        m = re.search(r"EFFECT:\s*(HP|GOLD)\s*=\s*([+-]?\d+)", text, re.I)
        if m:
            typ = m.group(1).upper()
            val = int(m.group(2))
            if typ == "HP":
                eff["hp"] = val
            else:
                eff["gold"] = val
            text = re.sub(r"EFFECT:.*", "", text, flags=re.I).strip()
        return text, eff
    except Exception:
        gain = d(8)+3
        t = (f"🧺 По обочине пути {name} находит потерянный кошель и благодарную записку. "
             f"Совесть велит оставить монеты за труды путника.")
        return t, {"gold": gain}

async def generate_dungeon_intro(theme: str) -> str:
    if not USE_OPENAI or oai_client is None:
        return (f"🏰 У входа в «{theme}» тьма шевелится, как живая. Камень холоден, и воздух тягуч.")
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=150,
            messages=[
                {"role": "system", "content": (
                    "Опиши 2–3 предложения атмосферного вступления у входа в указанное подземелье. Без Markdown."
                )},
                {"role": "user", "content": f"Подземелье: {theme}"}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return (f"Перед входом в «{theme}» даже пламя фонаря дрожит — тьма будто всматривается в пришельца.")

async def generate_room_lore(theme: str, room_num: int) -> str:
    if not USE_OPENAI or oai_client is None:
        return "В комнате пыль, отпечатки когтей на стенах и древние паутины."
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=160,
            messages=[
                {"role": "system", "content": (
                    "Опиши кратко (1–3 предложения) обстановку комнаты в подземелье: детали, запахи, звуки. Без Markdown."
                )},
                {"role": "user", "content": f"Подземелье: {theme}\nКомната: {room_num}"}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "Комната сырая и затхлая; в углах — тёмные пятна и старинные щербатые камни."

async def generate_search_result() -> str:
    if not USE_OPENAI or oai_client is None:
        return "Осматривая ниши и трещины, ты почти ничего не находишь — лишь пыль и отбитую гвоздь."
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=140,
            messages=[
                {"role": "system", "content": (
                    "Сгенерируй короткий литературный результат поиска комнаты: либо находка, либо пусто. "
                    "1–2 предложения, без Markdown."
                )},
                {"role": "user", "content": "Фэнтези подземелье, случайный результат поиска."}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "Кажется, здесь давно никто не ходил… Ничего ценного не видно."

async def generate_camp_text(theme: str, name: str, gender: str) -> str:
    if not USE_OPENAI or oai_client is None:
        return f"🔥 {name} разводит небольшой огонь и, прикрывшись плащом, пытается расслабиться, слушая гул глубин."
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=140,
            messages=[
                {"role": "system", "content": (
                    "Опиши короткую сцену привала ОДИНОКОГО героя в мрачном подземелье (1–3 предложения). Без Markdown."
                )},
                {"role": "user", "content": f"Герой: {name} ({'м' if gender=='male' else 'ж'})\nПодземелье: {theme}"}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"🔥 {name} делает глоток воды и слушает, как тишина подземелья расползается по камням."

async def generate_enemy_reaction(enemy_name: str) -> str:
    if not USE_OPENAI or oai_client is None:
        return f"{enemy_name} отшатывается и рычит."
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=80,
            messages=[
                {"role": "system", "content": "Короткая реакция монстра (1 предложение). Без Markdown."},
                {"role": "user", "content": f"Монстр: {enemy_name}"}
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"{enemy_name} содрогается, теряя равновесие."

# ---------- Вход в подземелье ----------

@router.message(F.text == "🕳️ Подземелья")
async def dng_menu(message: types.Message, state: FSMContext):
    p = get_player(message.from_user.id)
    names = theme_names_from_story(p.world_story)
    await state.update_data(dng_themes=names)
    await message.answer("Выбери место, куда отправиться:", reply_markup=dungeon_pick_kb(names))

@router.callback_query(F.data == "dng_back_city")
async def dng_back_city(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    from app.features.city import go_city
    await go_city(cb.message)

@router.callback_query(F.data.regexp(r"^dng_pick_(\d+)$"))
async def dng_pick(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    idx = int(cb.data.split("_")[-1]) - 1
    themes = data.get("dng_themes", [])
    if not (0 <= idx < len(themes)):
        await cb.message.answer("Нет такого варианта.", reply_markup=back_to_city_kb())
        return
    theme = themes[idx]
    p = get_player(cb.from_user.id)

    # init
    st = DungeonState(active=True, theme=theme, floor=1, room=0, found_exit=False, camped_in_room=False,
                      in_combat=False, enemy=None, turn="player", player_defending=False)
    _save_dng(p.user_id, st)
    _reset_ability_charges(p)

    # 1) маркер + дорога
    travel = await generate_travel_text(p.city_name, theme, p.name, p.gender)
    await cb.message.answer(f"🚶 Ты покидаешь {p.city_name} и отправляешься в «{theme}».")
    await cb.message.answer(travel)

    # 2) дорожное событие
    evt_text, eff = await generate_travel_event(p.city_name, p.name, p.gender)
    hp_delta = eff.get("hp", 0)
    gold_delta = eff.get("gold", 0)
    changed = []
    if hp_delta:
        p.hp = max(0, min(p.max_hp, p.hp + hp_delta))
        changed.append(f"❤️ HP {'+' if hp_delta>0 else ''}{hp_delta} → {p.hp}/{p.max_hp}")
    if gold_delta:
        p.gold = max(0, p.gold + gold_delta)
        changed.append(f"👛 Золото {'+' if gold_delta>0 else ''}{gold_delta} → {p.gold}")
    save_player(p)
    await cb.message.answer(evt_text + (("\n" + " | ".join(changed)) if changed else ""))

    # 3) вступление у входа
    intro = await generate_dungeon_intro(theme)
    await cb.message.answer(intro)

    # 4) первая комната
    await _enter_next_room(cb.message)

# ---------- Комнаты ----------

async def _enter_next_room(message: types.Message):
    p = get_player(message.from_user.id)
    st = _get_dng(p.user_id)
    if not st.active:
        await message.answer("Сначала выбери подземелье.")
        return

    st.room += 1
    st.camped_in_room = False
    st.found_exit = False

    # шанс найти выход заранее
    if st.room < MAX_ROOMS_PER_FLOOR and d(100) <= 18:
        st.found_exit = True

    # при входе показываем атмосферу комнаты
    lore = await generate_room_lore(st.theme, st.room)
    _save_dng(p.user_id, st)
    await message.answer(_room_text(st))
    await message.answer(lore, reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit))

@router.callback_query(F.data == "dng_search")
async def dng_search(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    # литературное описание поиска
    text = await generate_search_result()
    await cb.message.answer(text)

    # случайная находка (с шансом)
    if d(100) <= 45:
        # золото или предмет
        if d(100) <= 55:
            gold = d(12)+4
            p.gold += gold
            save_player(p)
            await cb.message.answer(f"💰 Найдено золото: +{gold}. 👛 Итого: {p.gold}")
        else:
            found = random.choice([
                ("Провиант", "consumable", None),
                ("Набор для костра", "camp", None),
                ("Кинжал", "weapon", None),
                ("Кожаная броня", "armor", "leather"),
                ("Деревянный посох", "weapon", "robe"),
                ("Железная руда", "consumable", None),
                ("Самоцвет", "consumable", None),
            ])
            name, kind, material = found
            p.inventory[name] = p.inventory.get(name, 0) + 1
            save_player(p)
            await cb.message.answer(f"🎁 Найдено: {decorate_item_name(name, kind, material)} ×1")
    else:
        await cb.message.answer("Похоже, ничего полезного…")

    await cb.message.answer("Что дальше?", reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit))

@router.callback_query(F.data == "dng_next")
async def dng_next(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    # литературный переход
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    trans_text = ("Ты углубляешься дальше, прислушиваясь к шорохам и гулу древних залов.")
    if USE_OPENAI and oai_client is not None:
        try:
            resp = await oai_client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.9,
                max_tokens=120,
                messages=[
                    {"role": "system", "content": "Опиши 1–2 предложения о том, как герой движется дальше в подземелье. Без Markdown."},
                    {"role": "user", "content": f"Герой: {p.name} ({'м' if p.gender=='male' else 'ж'}). Подземелье: {st.theme}."}
                ],
            )
            trans_text = resp.choices[0].message.content.strip()
        except Exception:
            pass
    await cb.message.answer(trans_text)
    await _maybe_spawn_encounter(cb.message)

async def _maybe_spawn_encounter(message: types.Message):
    p = get_player(message.from_user.id)
    st = _get_dng(p.user_id)

    st.found_exit = st.found_exit or (st.room < MAX_ROOMS_PER_FLOOR and d(100) <= 18)
    # 45% монстр, 20% ловушка, 15% сокровище, остальное пусто
    roll_kind = d(100)

    if roll_kind <= 45:
        m = roll_monster(st.theme, depth=(st.floor-1)*MAX_ROOMS_PER_FLOOR + st.room)
        st.in_combat = True
        st.turn = random.choice(["player", "enemy"])
        st.player_defending = False
        st.enemy = {
            "name": m.name, "emoji": m.emoji, "hp": m.hp, "ac": m.ac,
            "attack": m.attack, "to_hit": m.to_hit, "xp": m.xp, "level": m.level
        }
        _save_dng(p.user_id, st)

        # литературное описание встречи
        desc = f"{st.enemy['emoji']} Из тени выступает {st.enemy['name']}."
        if USE_OPENAI and oai_client is not None:
            try:
                resp = await oai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.9,
                    max_tokens=120,
                    messages=[
                        {"role": "system", "content": "Опиши 1–2 предложения о том, как монстр появляется перед героем. Без Markdown."},
                        {"role": "user", "content": f"Монстр: {st.enemy['name']}. Подземелье: {st.theme}."}
                    ],
                )
                desc = resp.choices[0].message.content.strip()
            except Exception:
                pass

        await message.answer(
            f"{_room_text(st)}\n\n{desc}\nHP врага: {st.enemy['hp']}  | AC: {st.enemy['ac']}\n"
            f"Первым ходит: <b>{'герой' if st.turn=='player' else 'враг'}</b>.",
            reply_markup=combat_actions_kb(has_skills=bool(p.ability_charges))
        )
        if st.turn == "enemy":
            await _enemy_turn(message)
        return

    elif roll_kind <= 65:
        dc = 12 + (st.floor//2)
        mod = (p.dexterity - 10)//2
        r, ok, crit = check_dc(mod, dc)
        dmg = roll("1d6+1")
        await message.answer(_room_text(st))
        if ok:
            await message.answer(f"🪤 Ловушка! Проверка Ловкости d20({r}){' КРИТ!' if crit else ''} — УСПЕХ. Урона нет.",
                                 reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit))
        else:
            p.hp = max(0, p.hp - dmg)
            save_player(p)
            await message.answer(
                f"🪤 Ловушка! Проверка Ловкости d20({r}){' КРИТ.ПРОВАЛ!' if crit else ''} — ПРОВАЛ. "
                f"Получено {dmg} урона. ❤️ {p.hp}/{p.max_hp}",
                reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit)
            )
        return

    elif roll_kind <= 80:
        gold = d(12)+4
        p.gold += gold
        loot_line = ""
        if d(100) <= 30:
            found = random.choice([
                ("Провиант", "consumable", None),
                ("Набор для костра", "camp", None),
                ("Кинжал", "weapon", None),
                ("Кожаная броня", "armor", "leather"),
                ("Деревянный посох", "weapon", "robe"),
            ])
            name, kind, material = found
            p.inventory[name] = p.inventory.get(name, 0) + 1
            loot_line = f"\n🎁 Найдено: {decorate_item_name(name, kind, material)} ×1"
        save_player(p)
        await message.answer(_room_text(st))
        await message.answer(f"💰 Сокровища! Золото +{gold}.{loot_line}",
                             reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit))
        return

    else:
        await message.answer(_room_text(st))
        await message.answer("Комната пуста…", reply_markup=room_actions_kb(can_camp=not st.camped_in_room, has_exit=st.found_exit))
        return

@router.callback_query(F.data == "dng_camp")
async def dng_camp(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    if st.camped_in_room:
        await cb.message.answer("Здесь уже был привал.")
        return
    if p.inventory.get("Набор для костра", 0) <= 0:
        await cb.message.answer("У вас нет набора для костра.")
        return

    # литературное описание привала
    camp_text = await generate_camp_text(st.theme, p.name, p.gender)
    await cb.message.answer(camp_text)

    # восстановление: HP + 50% недостающего (округлим вниз, минимум 1), заряды +1 (не выше макс.)
    heal = max(1, (p.max_hp - p.hp)//2)
    p.hp = min(p.max_hp, p.hp + heal)
    from app.features.character import ability_uses_for_level
    charges = p.__dict__.get("ability_charges", {})
    changes = [f"❤️ Здоровье: {p.hp}/{p.max_hp} (+{heal})"]
    for key, cur in list(charges.items()):
        lvl = p.abilities_known.get(key, 1)
        mx = ability_uses_for_level(key, lvl, p.class_key)
        if mx > 0:
            new = min(mx, cur + 1)
            if new != cur:
                charges[key] = new
                meta = p.ability_meta.get(key, {"emoji":"✨","title":key})
                changes.append(f"{meta['emoji']} {meta['title']}: {new}/{mx} (+1)")
    p.ability_charges = charges

    # тратим набор
    p.inventory["Набор для костра"] -= 1
    if p.inventory["Набор для костра"] <= 0:
        del p.inventory["Набор для костра"]
    save_player(p)

    st.camped_in_room = True
    _save_dng(p.user_id, st)

    await cb.message.answer("\n".join(changes),
                            reply_markup=room_actions_kb(can_camp=False, has_exit=st.found_exit))

@router.callback_query(F.data == "dng_escape")
async def dng_escape(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    st = _get_dng(cb.from_user.id)
    if not st.found_exit:
        await cb.message.answer("Выхода рядом нет.")
        return
    await cb.message.answer("Покинуть подземелье и вернуться в город?", reply_markup=confirm_leave_dungeon_kb())

@router.callback_query(F.data.in_(["dng_leave_yes", "dng_town_confirm"]))
async def dng_leave_yes(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    p.dungeon = DungeonState().__dict__
    save_player(p)
    clear_market_for_player(p.user_id)  # обновим ассортимент в городе

    from app.features.city import go_city
    await cb.message.answer("Ты возвращаешься в город. Торговцы сменили ассортимент.")
    await go_city(cb.message)

@router.callback_query(F.data == "dng_leave_no")
async def dng_leave_no(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer("Продолжаем исследование.")

# ---------- Бой ----------

def _player_ac(p) -> int:
    ac = 10 + max(0, p.endurance // 3)
    arm = (p.equipment or {}).get("armor")
    if arm:
        low = arm.lower()
        if any(x in low for x in ["кожан", "лег", "лёг"]):
            ac += 1
        elif any(x in low for x in ["латы", "тяж", "кольчуг", "панцир"]):
            ac += 2
    return ac

def _player_weapon_dmg(p) -> str:
    w = (p.equipment or {}).get("weapon") or ""
    low = w.lower()
    if "лук" in low:
        base = "1d8"; mod = (p.dexterity - 10)//2
    elif any(x in low for x in ["посох","жезл"]):
        base = "1d8"; mod = (p.intellect - 10)//2
    elif any(x in low for x in ["булав","молот"]):
        base = "1d8"; mod = (p.strength - 10)//2
    elif any(x in low for x in ["кинжал","нож"]):
        base = "1d6"; mod = (p.dexterity - 10)//2
    elif any(x in low for x in ["топор"]):
        base = "1d10"; mod = (p.strength - 10)//2
    else:
        base = "1d8"; mod = (p.strength - 10)//2
    mod = max(0, mod)
    return f"{base}+{mod}" if mod > 0 else base

def _to_hit_mod(p) -> int:
    w = (p.equipment or {}).get("weapon") or ""
    low = w.lower()
    if "лук" in low or "арбалет" in low:
        return max(0, (p.dexterity - 10)//2)
    if any(x in low for x in ["посох","жезл"]):
        return max(0, (p.intellect - 10)//2)
    if any(x in low for x in ["кинжал","нож"]):
        return max(0, (p.dexterity - 10)//2)
    return max(0, (p.strength - 10)//2)

async def _enemy_turn(message: types.Message):
    p = get_player(message.from_user.id)
    st = _get_dng(p.user_id)
    if not st.in_combat or not st.enemy:
        return

    r = d(20)
    to_hit = st.enemy["to_hit"]
    ac = _player_ac(p)
    # учтём защиту игрока
    if st.player_defending:
        ac += 2

    total = r + to_hit
    log = f"Ход врага: d20={r}+{to_hit} против твоего AC={ac} → "
    if r == 20 or total >= ac:
        dmg = roll(st.enemy["attack"])
        p.hp = max(0, p.hp - dmg)
        save_player(p)
        log += f"ПОПАДАНИЕ! Урон {dmg}. ❤️ {p.hp}/{p.max_hp}"
    else:
        log += "промах."

    st.turn = "player"
    st.player_defending = False  # защита работает 1 «вражий» ход
    _save_dng(p.user_id, st)

    if p.hp <= 0:
        await message.answer(log)
        await _player_death(message)
    else:
        await message.answer(log, reply_markup=combat_actions_kb(has_skills=bool(p.ability_charges)))

async def _player_death(message: types.Message):
    p = get_player(message.from_user.id)
    lost_gold = min(p.gold, max(5, p.gold // 3))
    p.gold -= lost_gold
    lost_exp = max(0, p.exp // 5)
    p.exp = max(0, p.exp - lost_exp)
    p.inventory = {}
    p.dungeon = DungeonState().__dict__
    save_player(p)

    await message.answer(
        f"☠️ Ты пал в глубинах. Потеряно {lost_gold} зол. и {lost_exp} опыта.\n"
        "Тебя нашли жители и дотащили до городских ворот…"
    )
    from app.features.city import go_city
    await go_city(message)

@router.callback_query(F.data == "cmb_attack")
async def cmb_attack(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    if not st.in_combat or not st.enemy:
        await cb.message.answer("Сейчас не с кем сражаться.")
        return
    r = d(20)
    mod = _to_hit_mod(p)
    total = r + mod
    log = f"Ты атакуешь: d20={r}+{mod} → "
    if r == 1:
        log += "крит.провал — промах."
        st.turn = "enemy"
        _save_dng(p.user_id, st)
        await cb.message.answer(log)
        await _enemy_turn(cb.message)
        return
    if r == 20 or total >= st.enemy["ac"]:
        dmg = roll(_player_weapon_dmg(p))
        if r == 20:
            dmg += roll("1d6")
        st.enemy["hp"] = max(0, st.enemy["hp"] - dmg)
        react = await generate_enemy_reaction(st.enemy["name"])
        log += f"ПОПАДАНИЕ! Урон {dmg}. Враг HP: {st.enemy['hp']}\n{react}"
    else:
        log += "промах."

    if st.enemy["hp"] <= 0:
        xp = st.enemy["xp"]
        p.exp += xp
        gold = d(10)+3
        p.gold += gold
        save_player(p)
        st.in_combat = False
        st.enemy = None
        st.player_defending = False
        _save_dng(p.user_id, st)
        await cb.message.answer(log)
        await cb.message.answer(f"🏆 Победа! Опыт +{xp}, золото +{gold}.")
        await cb.message.answer("Что дальше?", reply_markup=room_actions_kb(can_camp=True, has_exit=True))
    else:
        st.turn = "enemy"
        _save_dng(p.user_id, st)
        await cb.message.answer(log)
        await _enemy_turn(cb.message)

@router.callback_query(F.data == "cmb_defend")
async def cmb_defend(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    if not st.in_combat or not st.enemy:
        await cb.message.answer("Сейчас не с кем сражаться.")
        return
    st.player_defending = True
    st.turn = "enemy"
    _save_dng(p.user_id, st)
    await cb.message.answer("🛡️ Ты принимаешь защитную стойку (AC +2 до конца хода врага).")
    await _enemy_turn(cb.message)

@router.callback_query(F.data == "cmb_flee")
async def cmb_flee(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    p = get_player(cb.from_user.id)
    st = _get_dng(p.user_id)
    if not st.in_combat:
        await cb.message.answer("Некуда бежать.")
        return
    dc = 17
    mod = (p.dexterity - 10)//2
    r, ok, crit = check_dc(mod, dc)
    if ok:
        st.in_combat = False
        st.enemy = None
        st.player_defending = False
        _save_dng(p.user_id, st)
        await cb.message.answer(f"🥾 Бросок d20={r}{' КРИТ!' if crit else ''} — побег УДАЛСЯ. Ты ускользнул.")
        await cb.message.answer("Что дальше?", reply_markup=room_actions_kb(can_camp=True, has_exit=st.found_exit))
    else:
        dmg = roll("1d6+2")
        p.hp = max(0, p.hp - dmg)
        save_player(p)
        await cb.message.answer(f"❌ Бросок d20={r}{' КРИТ.ПРОВАЛ!' if crit else ''} — неудача, получаешь {dmg} урона. ❤️ {p.hp}/{p.max_hp}")
        if p.hp <= 0:
            await _player_death(cb.message)
        else:
                    await _enemy_turn(cb.message)

        @router.callback_query(F.data == "cmb_back")
        async def cmb_back(cb: types.CallbackQuery, state: FSMContext):
            await cb.answer()
            p = get_player(cb.from_user.id)
            st = _get_dng(p.user_id)
            if not (st.in_combat and st.enemy):
                await cb.message.answer("Сейчас не с кем сражаться.")
                return
            await cb.message.answer(
                f"{st.enemy['emoji']} {st.enemy['name']} наготове.\nТвой ход.",
                reply_markup=combat_actions_kb(has_skills=bool(p.ability_charges))
            )

        @router.callback_query(F.data == "cmb_skills")
        async def cmb_skills(cb: types.CallbackQuery, state: FSMContext):
            await cb.answer()
            p = get_player(cb.from_user.id)
            st = _get_dng(p.user_id)
            if not (st.in_combat and st.enemy):
                await cb.message.answer("Сейчас не с кем сражаться.")
                return

            charges: Dict[str, int] = p.__dict__.get("ability_charges", {})
            avail = [k for k, v in charges.items() if v > 0]
            if not avail:
                await cb.message.answer("Нет доступных зарядов умений.", reply_markup=combat_actions_kb(False))
                return

            # Сохраним порядок доступных ключей в FSM
            await state.update_data(skill_keys=avail)

            # Список с текущими зарядами
            lines = ["Выбери умение номером:"]
            for i, key in enumerate(avail, start=1):
                meta = p.ability_meta.get(key, {"emoji": "✨", "title": key})
                uses = charges.get(key, 0)
                # Определим макс-заряды на текущем уровне
                from app.features.character import ability_uses_for_level
                lvl = p.abilities_known.get(key, 1)
                mx = ability_uses_for_level(key, lvl, p.class_key)
                lines.append(f"{i}. {meta['emoji']} {meta['title']}: {uses}/{mx}")
            await cb.message.answer("\n".join(lines), reply_markup=skills_pick_kb(avail))

        @router.callback_query(F.data.regexp(r"^sk_(\d+)$"))
        async def cmb_skill_pick(cb: types.CallbackQuery, state: FSMContext):
            await cb.answer()
            p = get_player(cb.from_user.id)
            st = _get_dng(p.user_id)
            if not (st.in_combat and st.enemy):
                await cb.message.answer("Сейчас не с кем сражаться.")
                return

            data = await state.get_data()
            keys: List[str] = data.get("skill_keys", [])
            idx = int(cb.data.split("_")[-1]) - 1
            if not (0 <= idx < len(keys)):
                await cb.message.answer("Нет такого номера.")
                return

            key = keys[idx]
            charges: Dict[str, int] = p.__dict__.get("ability_charges", {})
            cur = charges.get(key, 0)
            if cur <= 0:
                await cb.message.answer("Зарядов не осталось.", reply_markup=combat_actions_kb(False))
                return

            # Простая модель урона умениями:
            # магические — INT, стрелковые — DEX, прочее — STR
            # здесь используем INT как базу (универсально), можно расширить по ключам
            to_hit = max(0, (p.intellect - 10) // 2)
            r = d(20)
            total = r + to_hit
            log = f"✨ Умение: d20={r}+{to_hit} → "

            if r == 1:
                log += "крит.провал — промах."
                st.turn = "enemy"
                _save_dng(p.user_id, st)
                await cb.message.answer(log)
                await _enemy_turn(cb.message)
                return

            if r == 20 or total >= st.enemy["ac"]:
                # Базовый магический урон
                dmg = roll("1d8") + max(0, (p.intellect - 10)//2)
                if r == 20:
                    dmg += roll("1d6")
                st.enemy["hp"] = max(0, st.enemy["hp"] - dmg)

                # Списываем заряд
                charges[key] = cur - 1
                p.ability_charges = charges
                save_player(p)

                react = await generate_enemy_reaction(st.enemy["name"])
                log += f"ПОПАДАНИЕ! Урон {dmg}. Враг HP: {st.enemy['hp']}\n{react}"
            else:
                log += "промах."

            if st.enemy["hp"] <= 0:
                xp = st.enemy["xp"]
                p.exp += xp
                gold = d(10)+3
                p.gold += gold
                save_player(p)

                st.in_combat = False
                st.enemy = None
                st.player_defending = False
                _save_dng(p.user_id, st)

                await cb.message.answer(log)
                await cb.message.answer(f"🏆 Победа! Опыт +{xp}, золото +{gold}.")
                await cb.message.answer("Что дальше?", reply_markup=room_actions_kb(can_camp=True, has_exit=True))
            else:
                st.turn = "enemy"
                _save_dng(p.user_id, st)
                await cb.message.answer(log)
                await _enemy_turn(cb.message)
