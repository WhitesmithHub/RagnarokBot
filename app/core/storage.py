from typing import Dict, Optional, List, Tuple
from .models import Player
from .items import Item, MAX_SLOTS, CATALOG, CLASS_WEAPON_ALLOW, CLASS_ARMOR_ALLOW

# Игроки (in-memory)
_PLAYERS: Dict[int, Player] = {}
# Текущий ассортимент рынка
_MARKET: Dict[int, List[str]] = {}
# Флаг: нужно ли обновить рынок после похода
_MARKET_STALE: Dict[int, bool] = {}

def save_player(p: Player) -> None:
    _PLAYERS[p.user_id] = p

def get_player(user_id: int) -> Optional[Player]:
    return _PLAYERS.get(user_id)

def has_player(user_id: int) -> bool:
    return user_id in _PLAYERS

def get_market(user_id: int) -> Optional[List[str]]:
    return _MARKET.get(user_id)

def set_market(user_id: int, item_ids: List[str]) -> None:
    _MARKET[user_id] = item_ids

# пометить рынок как «протухший» (вызовем при возвращении из подземелья)
def mark_market_stale(user_id: int) -> None:
    _MARKET_STALE[user_id] = True

# забрать и сбросить флаг «протухания»
def consume_market_stale(user_id: int) -> bool:
    return _MARKET_STALE.pop(user_id, False)

# ---- Инвентарь ----
def count_used_slots(inv: Dict[str, int]) -> int:
    slots = 0
    for item_id, qty in inv.items():
        if qty <= 0:
            continue
        it = CATALOG.get(item_id)
        if it and it.stackable:
            slots += 1
        else:
            slots += qty
    return slots

def available_slots(inv: Dict[str, int]) -> int:
    return max(0, MAX_SLOTS - count_used_slots(inv))

def can_add(inv: Dict[str, int], item: Item, qty: int) -> Tuple[bool, str]:
    if qty <= 0:
        return False, "Количество должно быть положительным."
    if item.stackable:
        current = inv.get(item.id, 0)
        if current == 0 and available_slots(inv) < 1:
            return False, "Нет свободных слотов."
        remaining = item.stack_max - current
        if remaining <= 0:
            return False, f"{item.name}: достигнут лимит стака ({item.stack_max})."
        if qty > remaining:
            return False, f"{item.name}: можно купить максимум {remaining} (лимит {item.stack_max})."
        return True, ""
    if available_slots(inv) < qty:
        return False, "Недостаточно слотов в инвентаре."
    return True, ""

def add_item(inv: Dict[str, int], item: Item, qty: int) -> Tuple[bool, str]:
    if qty <= 0:
        return False, "Количество должно быть положительным."
    inv[item.id] = inv.get(item.id, 0) + qty
    if item.stackable:
        return True, f"{item.name}: добавлено {qty} (итого {inv[item.id]}/{item.stack_max})."
    return True, f"{item.name}: добавлено {qty} шт."

def take_item(inv: Dict[str, int], item_id: str, qty: int = 1) -> bool:
    if inv.get(item_id, 0) < qty:
        return False
    inv[item_id] -= qty
    if inv[item_id] <= 0:
        inv.pop(item_id, None)
    return True

def remove_gold(p: Player, amount: int) -> bool:
    if amount <= p.gold:
        p.gold -= amount
        return True
    return False

# ---- Экипировка ----
def _compatible(player: Player, it: Item) -> Tuple[bool, str]:
    if it.type == "weapon":
        cat = it.weapon_cat
        allowed = CLASS_WEAPON_ALLOW.get(player.class_key, set())
        if cat and cat not in allowed:
            return False, "Это оружие не подходит для вашего класса."
    elif it.type == "armor":
        cat = it.armor_cat or "light"
        allowed = CLASS_ARMOR_ALLOW.get(player.class_key, set())
        if cat and cat not in allowed:
            return False, "Эта броня не подходит для вашего класса."
    return True, ""

def equip(player: Player, item_id: str) -> Tuple[bool, str]:
    it = CATALOG.get(item_id)
    if not it:
        return False, "Неизвестный предмет."
    if it.type not in ("weapon", "armor"):
        return False, "Этот предмет нельзя надеть."
    if player.inventory.get(item_id, 0) <= 0:
        return False, "У тебя нет такого предмета в инвентаре."

    ok, reason = _compatible(player, it)
    if not ok:
        return False, reason

    slot = it.type
    old = player.equipment.get(slot)
    if old:
        player.inventory[old] = player.inventory.get(old, 0) + 1
    if not take_item(player.inventory, item_id, 1):
        return False, "Не хватает предметов в инвентаре."
    player.equipment[slot] = item_id
    return True, f"Надето: {it.name} ({'оружие' if slot=='weapon' else 'броня'})."

def unequip(player: Player, slot: str) -> Tuple[bool, str]:
    if slot not in ("weapon", "armor"):
        return False, "Слот должен быть weapon или armor."
    item_id = player.equipment.get(slot)
    if not item_id:
        return False, "В этом слоте ничего не надето."
    it = CATALOG.get(item_id)
    if it and (not it.stackable) and available_slots(player.inventory) < 1:
        return False, "Нет свободного места в инвентаре."
    player.inventory[item_id] = player.inventory.get(item_id, 0) + 1
    player.equipment[slot] = None
    return True, f"Снято: {it.name if it else 'предмет'}."
