# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict
from .config import USE_OPENAI, oai_client

# Кэш «один раз на запуск» для базовых статов каждого класса
_BASE_STATS_CACHE: Dict[str, Dict[str, int]] = {}

# Фолбэк-базы (если ChatGPT недоступен)
FALLBACK_BASE = {
    "swordsman":  {"str": 6, "dex": 3, "int": 2, "end": 5},
    "mage":       {"str": 2, "dex": 3, "int": 7, "end": 4},
    "rogue":      {"str": 3, "dex": 7, "int": 2, "end": 4},
    "acolyte":    {"str": 3, "dex": 2, "int": 6, "end": 5},
    "archer":     {"str": 3, "dex": 7, "int": 3, "end": 3},
    "merchant":   {"str": 3, "dex": 4, "int": 4, "end": 5},
}

# Фолбэк-приросты на уровень
FALLBACK_PER_LEVEL = {
    "swordsman": {"str": 2, "dex": 1, "int": 0, "end": 1},
    "mage":      {"str": 0, "dex": 1, "int": 2, "end": 1},
    "rogue":     {"str": 1, "dex": 2, "int": 0, "end": 1},
    "acolyte":   {"str": 1, "dex": 0, "int": 2, "end": 1},
    "archer":    {"str": 1, "dex": 2, "int": 0, "end": 1},
    "merchant":  {"str": 1, "dex": 1, "int": 1, "end": 1},
}

def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

async def get_base_stats_for_class(class_key: str) -> Dict[str, int]:
    """
    Возвращает базовые статы для класса. Если ещё не генерировали — просим ChatGPT один раз
    (и кэшируем на процесс), иначе берём из кэша. При недоступности — FALLBACK_BASE.
    Правила: сумма 16–20, логичная специализация (маг=инт, лучник=ловк, мечник=сила и т.д.).
    Формат строго: JSON {"str":X,"dex":Y,"int":Z,"end":W}
    """
    if class_key in _BASE_STATS_CACHE:
        return _BASE_STATS_CACHE[class_key]

    if not USE_OPENAI or oai_client is None:
        _BASE_STATS_CACHE[class_key] = FALLBACK_BASE.get(class_key, {"str": 4, "dex": 4, "int": 4, "end": 4})
        return _BASE_STATS_CACHE[class_key]

    prompt = (
        "Распредели 16–20 очков по характеристикам класса логично для RPG:\n"
        "str=Сила, dex=Ловкость, int=Интеллект, end=Выносливость.\n"
        "Приоритеты: мечник=str, маг=int, вор=dex, послушник=int/end, лучник=dex, торговец=сбалансирован.\n"
        "Верни ТОЛЬКО JSON вида: {\"str\":X,\"dex\":Y,\"int\":Z,\"end\":W}"
    )
    try:
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            max_tokens=60,
            messages=[
                {"role": "system", "content": "Ты — балансировщик RPG-атрибутов."},
                {"role": "user", "content": f"Класс: {class_key}\n{prompt}"}
            ],
        )
        text = resp.choices[0].message.content.strip()
        import json, re
        json_text = text
        if "{" not in text:
            m = re.search(r'(\{.*\})', text, re.S)
            if m:
                json_text = m.group(1)
        data = json.loads(json_text)
        stats = {
            "str": _safe_int(data.get("str"), 4),
            "dex": _safe_int(data.get("dex"), 4),
            "int": _safe_int(data.get("int"), 4),
            "end": _safe_int(data.get("end"), 4),
        }
        _BASE_STATS_CACHE[class_key] = stats
        return stats
    except Exception:
        _BASE_STATS_CACHE[class_key] = FALLBACK_BASE.get(class_key, {"str": 4, "dex": 4, "int": 4, "end": 4})
        return _BASE_STATS_CACHE[class_key]

async def get_levelup_increase(class_key: str, current: Dict[str, int], new_level: int) -> Dict[str, int]:
    """
    Возвращает приращение статов на ап уровня (обычно 3–4 очка суммарно).
    Если ChatGPT недоступен — используем FALLBACK_PER_LEVEL.
    Формат: {"str":+a,"dex":+b,"int":+c,"end":+d}
    """
    if not USE_OPENAI or oai_client is None:
        return FALLBACK_PER_LEVEL.get(class_key, {"str": 1, "dex": 1, "int": 1, "end": 1})

    try:
        prompt = (
            "Дай приращение характеристик для апа на +1 уровень (3–4 очка суммарно), JSON.\n"
            "Учитывай специализацию класса и текущие значения.\n"
            "Формат: {\"str\":X,\"dex\":Y,\"int\":Z,\"end\":W} — только числа, только этот JSON."
        )
        cur_txt = f'{{"str":{current["str"]},"dex":{current["dex"]},"int":{current["int"]},"end":{current["end"]}}}'
        resp = await oai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=60,
            messages=[
                {"role": "system", "content": "Ты — балансировщик RPG-атрибутов."},
                {"role": "user", "content": f"Класс: {class_key}\nТекущие: {cur_txt}\n{prompt}"}
            ],
        )
        import json, re
        text = resp.choices[0].message.content.strip()
        json_text = text
        if "{" not in text:
            m = re.search(r'(\{.*\})', text, re.S)
            if m:
                json_text = m.group(1)
        data = json.loads(json_text)
        return {
            "str": _safe_int(data.get("str")),
            "dex": _safe_int(data.get("dex")),
            "int": _safe_int(data.get("int")),
            "end": _safe_int(data.get("end")),
        }
    except Exception:
        return FALLBACK_PER_LEVEL.get(class_key, {"str": 1, "dex": 1, "int": 1, "end": 1})
