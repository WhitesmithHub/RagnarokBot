# -*- coding: utf-8 -*-
# app/features/creation.py
from __future__ import annotations

from typing import Dict
import random

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.core.storage import get_player, save_player, Player
from app.core.config import USE_OPENAI, oai_client
from app.ui.keyboards import gender_kb, classes_kb, confirm_kb, city_menu_kb

router = Router()

# ---------- FSM: только для шага ввода имени ----------
class CreateFlow(StatesGroup):
    ask_name = State()

# Названия и эмодзи классов
CLASS_LABELS = {
    "swordsman": "🗡️ Мечник",
    "acolyte":   "✨ Послушник",
    "mage":      "🔮 Маг",
    "archer":    "🏹 Лучник",
    "merchant":  "🧾 Торговец",
    "thief":     "🗝️ Вор",
}

# Описания классов (литературные)
CLASS_DESCRIPTIONS = {
    "swordsman": (
        "Подобно волнам безбрежного моря, упорно и целеустремлённо, мечник идёт по пути познания силы, "
        "оттачивая мастерство и закаляя характер. В бою полагается на холодное оружие и храбрость."
    ),
    "mage": (
        "Жизнь мага — стремление познать что-то новое. Ради этого он покидает библиотеку и отправляется в путь, "
        "чтобы стать сильнее и добыть знание — ценность дороже золота. Познав силы природы, маг поражает врагов "
        "огнём, льдом и молниями."
    ),
    "thief": (
        "Они действуют по собственному кодексу. У Воров есть Гильдия и свои правила. В бою вор полагается не на "
        "силу, а на точность и уклонение."
    ),
    "acolyte": (
        "Служитель света, умеющий исцелять и защищать себя. В бою опирается на благословение и булаву, "
        "но его призвание — помогать и исцелять."
    ),
    "archer": (
        "Лучник держится на расстоянии, полагаясь на зоркий глаз и тугой лук. Слаб в ближнем бою, но добраться до "
        "хорошего стрелка непросто."
    ),
    "merchant": (
        "Хороший торговец знает, что, когда и где покупать и кому продавать. Он хитёр и практичен, "
        "умеет провернуть выгодную сделку даже в дороге."
    ),
}

# Умения
CLASS_ABILITIES: Dict[str, Dict[str, Dict[str, str]]] = {
    "swordsman": {
        "active": {
            "Мощный удар": "🗡️ Мощный удар – Мечник наносит мощный удар, наносящий высокий урон.",
            "Защитная стойка": "🛡️ Защитная стойка – Повышает броню на 50% на 1 ход.",
            "Огненный меч": "🗡️🔥 Огненный меч – +25% урона и доп. урон огнём 2 хода.",
        },
        "passive": {
            "Боевая выносливость": "💪 Боевая выносливость – +10% к максимальному здоровью.",
            "Ударный инстинкт":   "🎯 Ударный инстинкт – +5% к шансу крита после блока (1 ход).",
        },
        "start": ("Мощный удар", "🗡️"),
    },
    "mage": {
        "active": {
            "Огненный шар": "🔮🔥 Огненный шар – Взрывной урон по цели/области.",
            "Ледяная ловушка": "🔮❄️ Ледяная ловушка – Заморозка цели на 1 ход.",
            "Магический барьер": "🔮🛡️ Магический барьер – Поглощает часть урона до следующей атаки.",
        },
        "passive": {
            "Энергия воли": "🔮 Энергия воли – +10% к максимальному здоровью.",
            "Магический поток": "🔮 Магический поток – После магии +5% к шансу крита (1 ход).",
        },
        "start": ("Огненный шар", "🔮🔥"),
    },
    "thief": {
        "active": {
            "Теневой удар": "🔪 Теневой удар – Критический урон; -10% урона врага на 2 хода.",
            "Отравленный клинок": "🔪☠️ Отравленный клинок – Яд и -защита цели.",
            "Мгновенное исчезновение": "🫥 Мгновенное исчезновение – Уклон и +10 HP.",
        },
        "passive": {
            "Невидимость": "🫥 Невидимость – Старт в скрытности, +20% уклонения.",
            "Быстрота в действиях": "⚡ Быстрота – +10% к шансу крита.",
        },
        "start": ("Теневой удар", "🔪"),
    },
    "acolyte": {
        "active": {
            "Святое исцеление": "✨ Святое исцеление – Лечит себя на 30% HP.",
            "Благословение света": "✨ Благословение света – +15% к защите на 2 хода.",
            "Небесное осуждение": "✨ Небесное осуждение – Наносит урон светом.",
        },
        "passive": {
            "Вера в свет": "✨ Вера в свет – +10% к силе исцеления.",
            "Священное сопротивление": "✨ Священное сопротивление – -20% урона от тьмы.",
        },
        "start": ("Святое исцеление", "✨"),
    },
    "archer": {
        "active": {
            "Точный выстрел": "🏹 Точный выстрел – Высокая точность и урон.",
            "Стрела огня": "🏹🔥 Стрела огня – Накладывает горение на 2 хода.",
            "Двойной выстрел": "🏹🏹 Двойной выстрел – Две стрелы подряд.",
        },
        "passive": {
            "Лёгкость в движении": "🏃 Лёгкость – +10% уклонения.",
            "Природный инстинкт": "🌿 Инстинкт – +10% крита, если ход первый.",
        },
        "start": ("Точный выстрел", "🏹"),
    },
    "merchant": {
        "active": {
            "Торговый трюк": "💼 Торговый трюк – Урон и -10% защиты врага (1 ход).",
            "Удар купца": "💼🔨 Удар купца – Оглушение (1 ход).",
            "Сделка на грани": "💼🎯 Сделка на грани – +15% крита (1 ход).",
        },
        "passive": {
            "Блестящий оратор": "🗣️ Блестящий оратор – 10% скидка на рынке.",
            "Торговый ум": "🧠 Торговый ум – +5% к крита после удара.",
        },
        "start": ("Торговый трюк", "💼"),
    },
}

# Распределение статов (16 очков; 2..7)
def fallback_stats_for_class(class_key: str) -> Dict[str, int]:
    if class_key == "mage":
        base = {"str": 2, "dex": 3, "int": 7, "end": 4}
    elif class_key == "archer":
        base = {"str": 2, "dex": 7, "int": 3, "end": 4}
    elif class_key == "swordsman":
        base = {"str": 7, "dex": 3, "int": 2, "end": 4}
    elif class_key == "thief":
        base = {"str": 3, "dex": 7, "int": 3, "end": 3}
    elif class_key == "acolyte":
        base = {"str": 3, "dex": 3, "int": 5, "end": 5}
    else:  # merchant
        base = {"str": 3, "dex": 4, "int": 5, "end": 4}
    return base

async def gpt_stats_for_class(class_key: str) -> Dict[str, int]:
    if not USE_OPENAI or oai_client is None:
        return fallback_stats_for_class(class_key)
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=80,
            messages=[
                {"role": "system", "content": "Распредели 16 очков между STR, DEX, INT, END логично для класса. Формат: STR=x DEX=y INT=z END=w, числа 2..7."},
                {"role": "user", "content": f"Класс: {class_key}"},
            ],
        )
        txt = resp.choices[0].message.content.strip()
        vals = fallback_stats_for_class(class_key)
        up = txt.replace(",", " ").replace(";", " ")
        for token in up.split():
            t = token.upper()
            if "STR" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["str"] = int(num)
            elif "DEX" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["dex"] = int(num)
            elif "INT" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["int"] = int(num)
            elif "END" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["end"] = int(num)
        for k in vals:
            vals[k] = max(2, min(7, int(vals[k])))
        return vals
    except Exception:
        return fallback_stats_for_class(class_key)

def starting_hp_for_class(class_key: str) -> int:
    if class_key in ("swordsman", "archer"):
        return 10
    if class_key in ("acolyte", "thief", "merchant"):
        return 8
    if class_key == "mage":
        return 6
    return 8

# Пролог
async def gpt_prologue() -> str:
    if not USE_OPENAI or oai_client is None:
        return ("📜 <b>Пролог твоей саги</b>\n"
                "Веками мир балансировал на грани, и лишь редкие герои решались встать на пути тьмы.")
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.95,
            max_tokens=220,
            messages=[
                {"role": "system", "content": "Напиши эпический пролог (3–6 предложений) для фэнтези-приключения. Без Markdown."},
                {"role": "user", "content": "Глобальный лор, герой один."},
            ],
        )
        return "📜 <b>Пролог твоей саги</b>\n" + resp.choices[0].message.content.strip()
    except Exception:
        return ("📜 <b>Пролог твоей саги</b>\n"
                "Из глубин забытых веков поднимается древняя угроза. Но там, где рождается тьма, загорается новый свет.")

_CITY_PRESET = [
    "Златоверск", "Седолесье", "Лунолесье", "Горевск",
    "Пронтера", "Эйнброх", "Сумеречный Перевал", "Кровавый Утёс",
    "Ночной Карст", "Туманная Гавань", "Черноречье", "Старая Тьма",
]

async def gpt_city_name() -> str:
    if not USE_OPENAI or oai_client is None:
        return random.choice(_CITY_PRESET)
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=20,
            messages=[
                {"role": "system", "content": "Придумай одно уникальное название фэнтези-городка (1–2 слова), можно с трансильванским оттенком. Только слово/фраза, без кавычек."},
                {"role": "user", "content": "Русский язык."},
            ],
        )
        name = resp.choices[0].message.content.strip().splitlines()[0]
        return name[:24]
    except Exception:
        return random.choice(_CITY_PRESET)

async def gpt_arrival_text(city_name: str, hero_name: str, gender: str) -> str:
    if not USE_OPENAI or oai_client is None:
        return (f"🏘️ <b>{city_name}</b>\n"
                f"{hero_name} прибывает в город: шум рынков, пахнет хлебом и смолой. Впереди — пути в таверну, на рынок и в подземелья.")
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=220,
            messages=[
                {"role": "system", "content": "Опиши 2–4 предложения о прибытии ОДНОГО героя в город: атмосфера, люди, настроение. Только единственное число."},
                {"role": "user", "content": f"Город: {city_name}. Герой: {hero_name} ({'м' if gender=='male' else 'ж'})."},
            ],
        )
        return f"🏘️ <b>{city_name}</b>\n" + resp.choices[0].message.content.strip()
    except Exception:
        return (f"🏘️ <b>{city_name}</b>\n"
                f"{hero_name} входит через древние ворота. Город полон слухов и ожиданий грядущих перемен.")

# ---------- Старт / Гендер ----------

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Кто ты?", reply_markup=gender_kb())

@router.callback_query(F.data.regexp(r"^gender_(male|female)$"))
async def pick_gender(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    gender = "male" if cb.data.endswith("male") else "female"
    await state.update_data(gender=gender)
    await state.set_state(CreateFlow.ask_name)
    await cb.message.answer("Как тебя зовут?")

# ---------- Имя ----------

@router.message(CreateFlow.ask_name, F.text)
async def handle_name(message: types.Message, state: FSMContext):
    name_raw = message.text.strip()
    bad = any(x in name_raw.lower() for x in ["хуй", "пизд", "сука", "бля", "fuck"])
    if bad or len(name_raw) < 2 or len(name_raw) > 20:
        await message.answer("Имя неподходит. Введи другое, 2–20 символов, без вульгарщины.")
        return
    await state.update_data(name=name_raw)
    await message.answer("Выбери класс:", reply_markup=classes_kb())

# ---------- Класс / Подтверждение ----------

@router.callback_query(F.data.regexp(r"^class_pick_(\w+)$"))
async def pick_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    class_key = cb.data.split("_")[-1]
    if class_key not in CLASS_LABELS:
        await cb.message.answer("Такого класса нет.")
        return

    stats = await gpt_stats_for_class(class_key)
    label = CLASS_LABELS[class_key]
    desc = CLASS_DESCRIPTIONS[class_key]
    abil = CLASS_ABILITIES[class_key]
    start_name, start_emoji = abil["start"]

    act_lines = [f"• {v}" for v in abil["active"].values()]
    pas_lines = [f"• {v}" for v in abil["passive"].values()]

    text = (
        f"{label}\n{desc}\n\n"
        f"<b>Характеристики:</b>\n"
        f"💪 Сила: {stats['str']}\n"
        f"🏃 Ловкость: {stats['dex']}\n"
        f"🧠 Интеллект: {stats['int']}\n"
        f"🫀 Выносливость: {stats['end']}\n\n"
        f"<b>Умения</b>\n\n"
        f"<b>Активные:</b>\n" + "\n".join(act_lines) + "\n\n"
        f"<b>Пассивные:</b>\n" + "\n".join(pas_lines) + "\n\n"
        f"<b>В начале доступно только одно умение:</b> {start_emoji} {start_name}"
    )
    await state.update_data(class_key=class_key, class_label=label, stats=stats)
    await cb.message.answer(text, reply_markup=confirm_kb())

@router.callback_query(F.data == "cancel_class")
async def cancel_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.answer("Выбери класс:", reply_markup=classes_kb())

@router.callback_query(F.data == "confirm_class")
async def confirm_class(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    name = data.get("name", "Герой")
    gender = data.get("gender", "male")
    class_key = data.get("class_key")
    class_label = data.get("class_label")
    stats = data.get("stats") or fallback_stats_for_class(class_key or "swordsman")
    if not class_key:
        await cb.message.answer("Сначала выбери класс.")
        return

    p = get_player(cb.from_user.id) or Player(user_id=cb.from_user.id)

    p.user_id = cb.from_user.id
    p.gender = gender
    p.name = name
    p.class_key = class_key
    p.class_label = class_label

    p.level = 1
    p.exp = 0
    p.gold = 50
    p.inventory = {}
    p.equipment = {"weapon": None, "armor": None}

    p.strength = stats["str"]
    p.dexterity = stats["dex"]
    p.intellect = stats["int"]
    p.endurance = stats["end"]

    p.max_hp = starting_hp_for_class(class_key)
    p.hp = p.max_hp

    abil = CLASS_ABILITIES[class_key]
    start_name, start_emoji = abil["start"]
    p.abilities_known = {start_name: 1}
    p.ability_meta = {start_name: {"emoji": start_emoji, "title": start_name, "type": "active"}}
    p.ability_charges = {start_name: 3}

    prologue = await gpt_prologue()
    city = await gpt_city_name()
    p.city_name = city
    p.world_story = prologue

    save_player(p)

    await cb.message.answer(prologue)
    await cb.message.answer(f"🌟 Начальное умение: {start_emoji} {start_name} — добавлено в книгу умений.")
    arrive = await gpt_arrival_text(city, name, gender)
    await cb.message.answer(arrive)
    await cb.message.answer("Куда отправимся?", reply_markup=city_menu_kb())

    await state.clear()
