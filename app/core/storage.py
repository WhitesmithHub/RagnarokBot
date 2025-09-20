# -*- coding: utf-8 -*-
from typing import Dict, Optional
from .models import Player

# РџСЂРѕСЃС‚РѕРµ in-memory С…СЂР°РЅРёР»РёС‰Рµ (СЃС‚Р°Р±РёР»СЊРЅР°СЏ РІРµСЂСЃРёСЏ РґРѕ РїРѕРґР·РµРјРµР»СЊСЏ)
_PLAYERS: Dict[int, Player] = {}

def save_player(p: Player) -> None:
    _PLAYERS[p.user_id] = p

def get_player(user_id: int) -> Optional[Player]:
    return _PLAYERS.get(user_id)

def has_player(user_id: int) -> bool:
    return user_id in _PLAYERS



