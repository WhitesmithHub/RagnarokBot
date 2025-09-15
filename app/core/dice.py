# -*- coding: utf-8 -*-
import random
from typing import Tuple

_rng = random.SystemRandom()

def d(n: int) -> int:
    return _rng.randint(1, n)

def roll(expr: str) -> int:
    """
    Простейший парсер 'XdY+Z' / 'dY' / 'X' (целое).
    """
    expr = expr.lower().replace(" ", "")
    if "d" in expr:
        parts = expr.split("d", 1)
        x = int(parts[0]) if parts[0] else 1
        tail = parts[1]
        if "+" in tail:
            y, z = tail.split("+", 1)
            y, z = int(y), int(z)
        elif "-" in tail:
            y, z = tail.split("-", 1)
            y, z = int(y), -int(z)
        else:
            y, z = int(tail), 0
        return sum(d(y) for _ in range(max(1, x))) + z
    else:
        return int(expr)

def d20() -> int:
    return d(20)

def check_dc(mod: int, dc: int) -> Tuple[int, bool, bool]:
    """
    Возвращает (бросок, успех, крит/провал).
    20 — крит-успех, 1 — крит-провал.
    """
    r = d20()
    if r == 20:
        return r, True, True
    if r == 1:
        return r, False, True
    return r, (r + mod) >= dc, False
