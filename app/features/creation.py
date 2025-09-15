# -*- coding: utf-8 -*-
# app/features/creation.py
from __future__ import annotations

from typing import Dict
import random

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from ..core.storage import get_player, save_player, Player
from ..core.config import USE_OPENAI, oai_client
from ..ui.keyboards import gender_kb, classes_kb, confirm_kb, city_menu_kb  # важно: city_menu_kb

router = Router()

CLASS_LABELS = {
    "swordsman": "🗡️ Мечник",
    "acolyte":   "✨ Послушник",
    "mage":      "🔮 Маг",
    "archer":    "🏹 Лучник",
    "merchant":  "🧾 Торговец",
    "thief":     "🗝️ Вор",
}

CLASS_ABILITIES: Dict[str, Dict[str, Dict[str, str]]] = {
    "swordsman": {
        "active": {
            "Мощный удар": "🗡️ Мощный удар – Мечник наносит мощный удар, наносящий высокий урон. Если враг рядом с союзником, урон делится меж двумя целями.",
            "Защитная стойка": "🛡️ Защитная стойка – Повышает броню на 50% на 1 ход.",
            "Огненный меч": "🗡️🔥 Огненный меч – Наделяет клинок огнём: +25% урона и доп. огонь в течение 2 ходов.",
        },
        "passive": {
            "Боевая выносливость": "💪 Боевая выносливость – +10% к максимальному здоровью.",
            "Ударный инстинкт":   "🎯 Ударный инстинкт – +5% к шансу крита после успешного блока (на 1 ход).",
        },
        "start": ("Мощный удар", "🗡️"),
    },
    "mage": {
        "active": {
            "Огненный шар": "🔮🔥 Огненный шар – Маг создаёт огненный шар, который наносит урон в радиусе взрыва.",
            "Ледяная ловушка": "🔮❄️ Ледяная ловушка – Замораживает наступивших врагов на 1 ход.",
            "Магический барьер": "🔮🛡️ Магический барьер – Поглощает часть магического урона следующей атаки.",
        },
        "passive": {
            "Энергия воли": "🔮 Энергия воли – +10% к максимальному здоровью.",
            "Магический поток": "🔮 Магический поток – После применения магии +5% к шансу крита на 1 ход.",
        },
        "start": ("Огненный шар", "🔮🔥"),
    },
    "thief": {
        "active": {
            "Теневой удар": "🔪 Теневой удар – Критический удар из тени; -10% урона врага на 2 хода.",
            "Отравленный клинок": "🔪☠️ Отравленный клинок – Яд и -защита цели.",
            "Мгновенное исчезновение": "🫥 Мгновенное исчезновение – Уклон от следующей атаки и +10 HP.",
        },
        "passive": {
            "Невидимость": "🫥 Невидимость – Бой начинается в скрытности, +20% уклонения.",
            "Быстрота в действиях": "⚡ Быстрота – +10% к шансу крита.",
        },
        "start": ("Теневой удар", "🔪"),
    },
    "acolyte": {
        "active": {
            "Святое исцеление": "✨ Святое исцеление – Лечит себя на 30% здоровья.",
            "Благословение света": "✨ Благословение света – +15% к защите на 2 хода.",
            "Небесное осуждение": "✨ Небесное осуждение – Наносит урон врагам светом.",
        },
        "passive": {
            "Вера в свет": "✨ Вера в свет – +10% к силе исцеления.",
            "Священное сопротивление": "✨ Священное сопротивление – -20% урона от тьмы.",
        },
        "start": ("Святое исцеление", "✨"),
    },
    "archer": {
        "active": {
            "Точный выстрел": "🏹 Точный выстрел – Высокая точность и повышенный урон.",
            "Стрела огня": "🏹🔥 Стрела огня – Доп. огненный урон в течение 2 ходов.",
            "Двойной выстрел": "🏹🏹 Двойной выстрел – Выпускает две стрелы сразу.",
        },
        "passive": {
            "Лёгкость в движении": "👣 Лёгкость – +10% уклонения.",
            "Природный инстинкт": "🌿 Инстинкт – +10% к шансу крита, если ход первый.",
        },
        "start": ("Точный выстрел", "🏹"),
    },
    "merchant": {
        "active": {
            "Торговый трюк": "💼 Торговый трюк – Наносит урон и -10% защиты врага на 1 ход.",
            "Удар купца": "💼🔨 Удар купца – Оглушает на 1 ход.",
            "Сделка на грани": "💼🎯 Сделка на грани – +15% к шансу крита на 1 ход.",
        },
        "passive": {
            "Блестящий оратор": "🗣️ Блестящий оратор – 10% скидка на рынке.",
            "Торговый ум": "🧠 Торговый ум – +5% к шансу крита после каждого удара.",
        },
        "start": ("Торговый трюк", "💼"),
    },
}

CLASS_DESCRIPTIONS = {
    "swordsman": "Подобно волнам безбрежного моря, упорно и целеустремлённо мечник идёт по пути силы. В бою полагается на мастерство клинка и храбрость.",
    "mage":      "Жизнь мага — стремление к знанию. Познав силы природы, маги поражают врагов огнём, льдом и молнией.",
    "thief":     "У воров есть свой кодекс и гильдия. В бою полагаются на точность и уклонение, а не на грубую силу.",
    "acolyte":   "Служитель света. Редко проливает кровь, но владеет булавой и силой исцеления.",
    "archer":    "Держится на расстоянии, полагаясь на зоркий глаз и тугой лук. Слаб в ближнем бою, но до него ещё надо добежать.",
    "merchant":  "Знает, что, где и когда покупать и кому продавать. Вечно в пути с тележкой товаров.",
}

def fallback_stats_for_class(class_key: str) -> Dict[str, int]:
    if class_key == "mage":
        base = {"str": 2, "dex": 3, "int": 7, "end": 3}
    elif class_key == "archer":
        base = {"str": 3, "dex": 7, "int": 3, "end": 3}
    elif class_key == "swordsman":
        base = {"str": 7, "dex": 4, "int": 2, "end": 3}
    elif class_key == "thief":
        base = {"str": 3, "dex": 7, "int": 3, "end": 3}
    elif class_key == "acolyte":
        base = {"str": 3, "dex": 3, "int": 5, "end": 4}
    else:  # merchant
        base = {"str": 3, "dex": 4, "int": 5, "end": 3}
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
                {"role": "system", "content": "Распредели 16 очков между Силой, Ловкостью, Интеллектом и Выносливостью логично для класса. Формат: STR=x DEX=y INT=z END=w, числа 2..7."},
                {"role": "user", "content": f"Класс: {class_key}"},
            ],
        )
        txt = resp.choices[0].message.content.strip()
        vals = fallback_stats_for_class(class_key)
        up = txt.replace(",", " ").replace(";", " ")
        for token in up.split():
            t = token.upper()
            if "STR" in t or "СИЛ" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["str"] = int(num)
            elif "DEX" in t or "ЛОВ" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["dex"] = int(num)
            elif "INT" in t or "ИНТ" in t:
                num = "".join(ch for ch in t if ch.isdigit())
                if num: vals["int"] = int(num)
            elif "END" in t or "ВЫН" in t:
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

async def gpt_prologue() -> str:
    if not USE_OPENAI or oai_client is None:
        return ("📜 <b>Пролог твоей саги</b>\n"
                "Веками мир балансировал на грани, и лишь редкие герои решались встать на пути тьмы. "
                "Судьба выбирает тех, кто делает шаг вперёд — сегодня очередь за тобой.")
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.95,
            max_tokens=220,
            messages=[
                {"role": "system", "content": "Напиши эпический пролог (3–6 предложений) для фэнтези-приключения. Без Markdown."},
                {"role": "user", "content": "Глобальный лор, не зависящий от класса героя."},
            ],
        )
        return "📜 <b>Пролог твоей саги</b>\n" + resp.choices[0].message.content.strip()
    except Exception:
        return ("📜 <b>Пролог твоей саги</b>\n"
                "Из глубин забытых веков поднимается древняя угроза. Но там, где рождается тьма, всегда загорается новый свет.")

async def gpt_city_name() -> str:
    if not USE_OPENAI or oai_client is None:
        return random.choice(["Златоград", "Седолесье", "Горевск", "Лунолесье", "Руалслав", "Златоверск"])
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.9,
            max_tokens=20,
            messages=[
                {"role": "system", "content": "Придумай одно уникальное название фэнтези-городка. Только слово, без кавычек."},
                {"role": "user", "content": "Славянский/русский оттенок приветствуется."},
            ],
        )
        name = resp.choices[0].message.content.strip().splitlines()[0]
        return name[:24]
    except Exception:
        return random.choice(["Златоград", "Седолесье", "Горевск"])

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
                {"role": "system", "content": "Опиши 2–4 предложения о том, как ОДИН герой прибыл в город, настроение горожан и обстановку. Единственное число."},
                {"role": "user", "content": f"Город: {city_name}. Герой: {hero_name} ({'м' if gender=='male' else 'ж'})."},
            ],
        )
        return f"🏘️ <b>{city_name}</b>\n" + resp.choices[0].message.content.strip()
    except Exception:
        return (f"🏘️ <b>{city_name}</b>\n"
                f"{hero_name} входит через древние ворота. Город полон слухов и ожиданий грядущих перемен.")

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.update_data(step="gender")
    await message.answer("Кто ты?", reply_markup=gender_kb())

@router.callback_query(F.data.in_(["gender_male", "gender_female"]))
async def pick_gender(cb: types.CallbackQuery, state: FSMContext):
    await cb.answer()
    gender = "male" if cb.data.endswith("male") else "female"
    await state.update_data(gender=gender, step="ask_name")
    await cb.message.answer("Как тебя зовут? Напиши имя (без мата и вульгарщины).")

@router.message(F.text)
async def handle_name_or_ignore(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("step") != "ask_name":
        return
    name_raw = message.text.strip()
    bad = any(x in name_raw.lower() for x in ["хуй", "пизд", "сука", "бля", "fuck"])
    if bad or len(name_raw) < 2 or len(name_raw) > 20:
        await message.answer("Имя неподходит. Введи другое, 2–20 символов, без вульгарщины.")
        return
    await state.update_data(name=name_raw, step="class")
    await message.answer("Выбери класс:", reply_markup=classes_kb())

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
        f"<b>Активные:</b>\n" + "\n".join(act_lines) + "\n\n"
        f"<b>Пассивные:</b>\n" + "\n".join(pas_lines) + "\n\n"
        f"<b>В начале доступно только одно умение:</b> {start_emoji} {start_name}\n"
        f"<b>Характеристики:</b>\n"
        f"💪 Сила: {stats['str']}\n"
        f"🦊 Ловкость: {stats['dex']}\n"
        f"🧠 Интеллект: {stats['int']}\n"
        f"🫀 Выносливость: {stats['end']}"
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

    p = get_player(cb.from_user.id)
    if p is None:
        p = Player(user_id=cb.from_user.id)

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
    await cb.message.answer("Куда отправимся?", reply_markup=city_menu_kb())  # ReplyKeyboard

    await state.clear()
