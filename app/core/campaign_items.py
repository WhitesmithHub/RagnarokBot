# -*- coding: utf-8 -*-
# app/core/campaign_items.py
from __future__ import annotations

import random
from typing import Dict, List, Optional

# ВАЖНО: ключ кампании совпадает с UI — "eclipse"
_CAMPAIGN_ITEMS: Dict[str, List[Dict]] = {
    "eclipse": [
        # -------------------- SWORDSMAN --------------------
        # Обычный (1-5)
        {
            "name": "Меч сумеречного дозора",
            "kind": "weapon", "dmg": "+1", "price": 26, "rarity": "Обычный", "level": "1-5",
            "desc": "Клинок, привыкший к ночным караулам. В сумерках держит линию удара ровно.",
        },
        {
            "name": "Кольчуга дозора",
            "kind": "armor", "material": "heavy", "def": "+1", "price": 25, "rarity": "Обычный", "level": "1-5",
            "desc": "Звенит негромко, как шаг по пустым улицам после комендантского часа.",
        },
        # Редкий (5-12)
        {
            "name": "Клинок Ночного парада",
            "kind": "weapon", "dmg": "+1", "price": 110, "rarity": "Редкий", "level": "5-12",
            "desc": "Полированная сталь, что скользит в воздухе без эха.",
            "bonus": "первая атака в бою наносит +2 урона",
        },
        {
            "name": "Ночной панцирь",
            "kind": "armor", "material": "heavy", "def": "+1", "price": 108, "rarity": "Редкий", "level": "5-12",
            "desc": "Тёмный металл держит удар, будто уводит его в глубину.",
            "bonus": "20% шанс отразить 1 урон атакующему",
        },
        # Легендарный (10-12)
        {
            "name": "Клинок Алого круга",
            "kind": "weapon", "dmg": "+2", "price": 235, "rarity": "Легендарный", "level": "10-12",
            "desc": "Гарда замкнута в круг, как диск затмения. Удар обрывается вспышкой.",
            "bonus": "каждый 4-й удар становится критическим",
        },
        {
            "name": "Латы Кровавого затмения",
            "kind": "armor", "material": "heavy", "def": "+2", "price": 235, "rarity": "Легендарный", "level": "10-12",
            "desc": "Швы, как орбиты: узор ведёт удар мимо сердца.",
            "bonus": "1 раз за бой блокирует весь урон одной атаки",
        },

        # -------------------- MAGE --------------------
        # Обычный (1-5)
        {
            "name": "Посох сумеречного ученика",
            "kind": "weapon", "dmg": "+1", "price": 21, "rarity": "Обычный", "level": "1-5",
            "desc": "Гибкое древко, руна на навершии согревает пальцы.",
        },
        {
            "name": "Мантия наблюдателя",
            "kind": "armor", "material": "robe", "def": "+1", "price": 20, "rarity": "Обычный", "level": "1-5",
            "desc": "Серая ткань, в которой ночь ближе, чем кажется.",
        },
        # Редкий (5-12)
        {
            "name": "Жезл Кровавой Луны",
            "kind": "weapon", "dmg": "+1", "price": 132, "rarity": "Редкий", "level": "5-12",
            "desc": "В навершии дрожит рубиновая капля — ровный прилив силы.",
            "bonus": "заклинания имеют +10% шанс критического урона",
        },
        {
            "name": "Роба Лунной тени",
            "kind": "armor", "material": "robe", "def": "+1", "price": 105, "rarity": "Редкий", "level": "5-12",
            "desc": "Ткань плывёт, не шурша. Подходит для тихого слова.",
            "bonus": "+5% шанс уклонения",
        },
        # Легендарный (10-12)
        {
            "name": "Скипетр Лунной тьмы",
            "kind": "weapon", "dmg": "+2", "price": 240, "rarity": "Легендарный", "level": "10-12",
            "desc": "Тёмное дерево не отражает свет — слова держатся в воздухе дольше.",
            "bonus": "каждый 3-й удар наносит дополнительно +2 урона",
        },
        {
            "name": "Одеяние Безмолвного затмения",
            "kind": "armor", "material": "robe", "def": "+2", "price": 232, "rarity": "Легендарный", "level": "10-12",
            "desc": "Тонкий шов, как лунная дужка, держит форму тишины.",
            "bonus": "после успешного заклинания лечит владельца на 1 HP (1 раз за бой)",
        },

        # -------------------- THIEF --------------------
        # Обычный (1-5)
        {
            "name": "Кинжал сумеречной улочки",
            "kind": "weapon", "dmg": "+1", "price": 24, "rarity": "Обычный", "level": "1-5",
            "desc": "Короткий клинок без блика — шаг короче, тень длиннее.",
        },
        {
            "name": "Кожаная куртка теней",
            "kind": "armor", "material": "leather", "def": "+1", "price": 22, "rarity": "Обычный", "level": "1-5",
            "desc": "Мягкая кожа, что запоминает маршруты крыш.",
        },
        # Редкий (5-12)
        {
            "name": "Катар Бесшумного вздоха",
            "kind": "weapon", "dmg": "+1", "price": 118, "rarity": "Редкий", "level": "5-12",
            "desc": "Лезвие без отражения. Первый удар — решение.",
            "bonus": "первая атака в бою наносит +2 урона",
        },
        {
            "name": "Лёгкая броня следопыта ночи",
            "kind": "armor", "material": "leather", "def": "+1", "price": 96, "rarity": "Редкий", "level": "5-12",
            "desc": "Подкладка гасит шорох. Свободный ход — половина удачи.",
            "bonus": "+5% шанс уклонения",
        },
        # Легендарный (10-12)
        {
            "name": "Катар Кровавой тиши",
            "kind": "weapon", "dmg": "+2", "price": 232, "rarity": "Легендарный", "level": "10-12",
            "desc": "Лезвие, на котором не задерживается свет.",
            "bonus": "каждый 4-й удар становится критическим",
        },
        {
            "name": "Ткань беззвучного шага",
            "kind": "armor", "material": "leather", "def": "+2", "price": 225, "rarity": "Легендарный", "level": "10-12",
            "desc": "Плотная матовая нить — тень держит шаг.",
            "bonus": "1 раз за бой блокирует весь урон одной атаки",
        },

        # -------------------- ACOLYTE --------------------
        # Обычный (1-5)
        {
            "name": "Булава монастырского караула",
            "kind": "weapon", "dmg": "+1", "price": 22, "rarity": "Обычный", "level": "1-5",
            "desc": "Гладкая рукоять, натёртая ладонями учеников.",
        },
        {
            "name": "Роба вечерней службы",
            "kind": "armor", "material": "robe", "def": "+1", "price": 21, "rarity": "Обычный", "level": "1-5",
            "desc": "Ткань сшита так, чтобы молитва ложилась ровно.",
        },
        # Редкий (5-12)
        {
            "name": "Молот погребальных псалмов",
            "kind": "weapon", "dmg": "+1", "price": 120, "rarity": "Редкий", "level": "5-12",
            "desc": "Грани поют низко и долго.",
            "bonus": "критический удар лечит владельца на 1 HP",
        },
        {
            "name": "Риза вечерней молитвы",
            "kind": "armor", "material": "robe", "def": "+1", "price": 102, "rarity": "Редкий", "level": "5-12",
            "desc": "Тихая ткань, на которой ни складки, ни сомнений.",
            "bonus": "в конце боя лечит владельца на 1 HP",
        },
        # Легендарный (10-12)
        {
            "name": "Булава алтарного круга",
            "kind": "weapon", "dmg": "+2", "price": 228, "rarity": "Легендарный", "level": "10-12",
            "desc": "Резной венец на головке держит удар в молитвенном ритме.",
            "bonus": "каждый 3-й удар наносит дополнительно +2 урона",
        },
        {
            "name": "Риза полного круга",
            "kind": "armor", "material": "robe", "def": "+2", "price": 225, "rarity": "Легендарный", "level": "10-12",
            "desc": "Края сходятся, как лунный обруч — ладно и надёжно.",
            "bonus": "получаемый урон от одной атаки 1 раз за бой снижается на 2",
        },

        # -------------------- ARCHER --------------------
        # Обычный (1-5)
        {
            "name": "Короткий лук сумерек",
            "kind": "weapon", "dmg": "+1", "price": 25, "rarity": "Обычный", "level": "1-5",
            "desc": "Сухая тетива звенит тихо, как щепотка песка.",
        },
        {
            "name": "Плащ охотника заката",
            "kind": "armor", "material": "leather", "def": "+1", "price": 23, "rarity": "Обычный", "level": "1-5",
            "desc": "Матовая ткань, на которой сумерки держатся дольше.",
        },
        # Редкий (5-12)
        {
            "name": "Лук полутени",
            "kind": "weapon", "dmg": "+1", "price": 112, "rarity": "Редкий", "level": "5-12",
            "desc": "Лёгкое древко, что любит даль и ровный выдох.",
            "bonus": "+10% шанс критического урона для дальних атак",
        },
        {
            "name": "Плащ Кровавого рассвета",
            "kind": "armor", "material": "leather", "def": "+1", "price": 112, "rarity": "Редкий", "level": "5-12",
            "desc": "Ветер прицеливается вместе с тетивой.",
            "bonus": "+10% шанс критического урона для дальних атак",
        },
        # Легендарный (10-12)
        {
            "name": "Лук Алого серпа",
            "kind": "weapon", "dmg": "+2", "price": 232, "rarity": "Легендарный", "level": "10-12",
            "desc": "Дуга, что повторяет лунный край. Стрелы уходят без колебаний.",
            "bonus": "первая атака в бою всегда критическая",
        },
        {
            "name": "Капюшон Красной луны",
            "kind": "armor", "material": "leather", "def": "+2", "price": 225, "rarity": "Легендарный", "level": "10-12",
            "desc": "Тень ложится на глаза мягко, как бархат.",
            "bonus": "15% шанс уклониться от атаки",
        },

        # -------------------- MERCHANT --------------------
        # Обычный (1-5)
        {
            "name": "Кинжал ночного торга",
            "kind": "weapon", "dmg": "+1", "price": 24, "rarity": "Обычный", "level": "1-5",
            "desc": "Резец для узловых ситуаций и тонких аргументов.",
        },
        {
            "name": "Кожаная жилетка ростовщика",
            "kind": "armor", "material": "leather", "def": "+1", "price": 22, "rarity": "Обычный", "level": "1-5",
            "desc": "Карманы помнят число монет лучше книг.",
        },
        # Редкий (5-12)
        {
            "name": "Булава писца контрактов",
            "kind": "weapon", "dmg": "+1", "price": 106, "rarity": "Редкий", "level": "5-12",
            "desc": "На рукояти зарубки — сроки, проценты и обещания.",
            "bonus": "первая атака в бою наносит +2 урона",
        },
        {
            "name": "Кираса Тёмного торга",
            "kind": "armor", "material": "leather", "def": "+1", "price": 112, "rarity": "Редкий", "level": "5-12",
            "desc": "Мягкие пластины глушат чужой напор.",
            "bonus": "20% шанс отразить 1 урон атакующему",
        },
        # Легендарный (10-12)
        {
            "name": "Кинжал Лунного счёта",
            "kind": "weapon", "dmg": "+2", "price": 230, "rarity": "Легендарный", "level": "10-12",
            "desc": "Клинок подводит итог спору быстрее бухгалтерии.",
            "bonus": "каждый 3-й удар наносит дополнительно +2 урона",
        },
        {
            "name": "Панцирь Ночного дворца обменов",
            "kind": "armor", "material": "leather", "def": "+2", "price": 228, "rarity": "Легендарный", "level": "10-12",
            "desc": "Крепкие вставки, будто штемпели в книге сделок.",
            "bonus": "20% шанс отразить 1 урон атакующему",
        },
    ]
}

def get_campaign_pool(campaign_id: Optional[str]) -> List[Dict]:
    return list(_CAMPAIGN_ITEMS.get((campaign_id or "").strip(), []))

def pick_campaign_items(campaign_id: Optional[str], k: int, class_key: Optional[str] = None) -> List[Dict]:
    pool = get_campaign_pool(campaign_id)
    if not pool or k <= 0:
        return []

    # фильтр под класс
    def fits(item: Dict) -> bool:
        if not class_key:
            return True
        name = (item.get("name") or "").lower()
        kind = item.get("kind")
        material = item.get("material")
        if kind == "weapon":
            if class_key == "swordsman":  return any(w in name for w in ("меч","клинок"))
            if class_key == "archer":     return "лук" in name
            if class_key == "thief":      return any(w in name for w in ("кинжал","катар"))
            if class_key == "mage":       return any(w in name for w in ("посох","жезл"))
            if class_key == "acolyte":    return any(w in name for w in ("булава","молот"))
            if class_key == "merchant":   return any(w in name for w in ("кинжал","булава","молот"))
        if kind == "armor":
            if class_key == "mage":       return material == "robe"
            if class_key in ("thief","archer","merchant"): return material == "leather"
            if class_key == "acolyte":    return material in ("robe","leather")
            if class_key == "swordsman":  return material in ("leather","heavy")
        return True

    pool = [x for x in pool if fits(x)] or pool
    k = min(k, len(pool))
    return random.sample(pool, k=k)

def find_campaign_item_by_name(name: str) -> Optional[Dict]:
    n = (name or "").strip().lower()
    for lst in _CAMPAIGN_ITEMS.values():
        for it in lst:
            if (it.get("name") or "").strip().lower() == n:
                return it
    return None
