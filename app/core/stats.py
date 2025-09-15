# app/core/stats.py

def max_hp_for(level: int, class_key: str) -> int:
    """
    Правила из ТЗ:
    - Мечники/Лучники: 10 ОЗ на 1 ур. и +6 за уровень
    - Послушники/Воры/Торговцы: 8 ОЗ и +5/ур.
    - Маги: 6 ОЗ и +6/ур.
    """
    cls = class_key
    if cls in ("swordsman", "archer"):
        base, per = 10, 6
    elif cls in ("acolyte", "rogue", "merchant"):
        base, per = 8, 5
    elif cls in ("mage",):
        base, per = 6, 6
    else:
        base, per = 8, 5
    # уровень 1 = base, уровень 2 = base + per, и т.д.
    return base + per * (max(1, level) - 1)
