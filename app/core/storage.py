# -*- coding: utf-8 -*-
from typing import Dict, Optional
from .models import Player

# Простое in-memory хранилище (стабильная версия до подземелья)
_PLAYERS: Dict[int, Player] = {}

def save_player(p: Player) -> None:
    _PLAYERS[p.user_id] = p

def get_player(user_id: int) -> Optional[Player]:
    return _PLAYERS.get(user_id)

def has_player(user_id: int) -> bool:
    return user_id in _PLAYERS
