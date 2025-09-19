# -*- coding: utf-8 -*-
# app/core/campaign.py
from __future__ import annotations

# ---   ---
_CAMPAIGNS = {
    "eclipse": {
        "title": "    ",
        "brief": (
            " ,       . "
            "  ,         . "
            "    ,      ,   ,   "
            "     .   ,      ."
        ),
        "epic": (
            " <b>    </b>\n\n"
            "  ,  ,        ,    . "
            "    ,    ,   ,   , "
            "  ,  -   .       -   "
            " ,    .    ,     , "
            " ,     ,       . "
            "    ,       ,      . "
            "      ,       , "
            "     .     : -    - , "
            "-  ,    ,  .      ,     , "
            "     .               , "
            ",  ,  ,     .     , "
            " -         ,   ."
        ),
        "arrival_city": "",
        "arrival_suffix_text": (
            "  ,         . "
            "    ,    ,    "
            "    ,     .       ; "
            "     .    :  .     . "
            "       .   ,         ."
        ),
    },
    "dragon": {
        "title": "  ",
        "brief": (
            "   ,       . "
            "Ѹ ,  ,     . "
            "          ?"
        ),
        "epic": (
            " <b>  </b>\n\n"
            "      ,    . "
            "    ,      . "
            "  ,   ,  ,     . "
            "  ,  ,        . "
            ",  -    ,          . "
            "  ,    ,      . "
            " ,    ,         ."
        ),
        "arrival_city": "",
        "arrival_suffix_text": (
            " ,  ,  ,     . "
            "      ,         . "
            "    :       ."
        ),
    },
    "plague": {
        "title": " ",
        "brief": (
            "      .   ,    . "
            " ,  .     ."
        ),
        "epic": (
            " <b> </b>\n\n"
            "    ,  - . "
            "    ,   ,  -   . "
            "   ,   :   ,     ? "
            "     ,        . "
            "  ,       . "
            " ,     , ,    ."
        ),
        "arrival_city": "",
        "arrival_suffix_text": (
            " ,     ,        . "
            "  ,        ."
        ),
    },
}

_DEFAULT = "eclipse"

# ---   ---

def welcome_text() -> str:
    return (
        "     RPG!\n\n"
        " ,      ,     , "
        "    .    ,   ,    "
        "  ."
    )

def campaigns_index() -> list[tuple[str, str]]:
    """ (id, title)    ."""
    return [(cid, data["title"]) for cid, data in _CAMPAIGNS.items()]

def get_brief(campaign_id: str | None) -> str:
    cid = campaign_id or _DEFAULT
    data = _CAMPAIGNS.get(cid, _CAMPAIGNS[_DEFAULT])
    return f" <b>{data['title']}</b>\n\n{data['brief']}"

def get_epic(campaign_id: str | None) -> str:
    cid = campaign_id or _DEFAULT
    data = _CAMPAIGNS.get(cid, _CAMPAIGNS[_DEFAULT])
    return data["epic"]

def arrival_city_name(campaign_id: str | None) -> str:
    cid = campaign_id or _DEFAULT
    data = _CAMPAIGNS.get(cid, _CAMPAIGNS[_DEFAULT])
    return data["arrival_city"]

def _is_female(gender: str, name: str) -> bool:
    if gender == "female":
        return True
    if gender == "male":
        return False
    nm = (name or "").strip().lower()
    fem_endings = ("","","","","","","","","","","","")
    return any(nm.endswith(suf) for suf in fem_endings)

def arrival_text(hero_name: str, gender: str, campaign_id: str | None) -> str:
    cid = campaign_id or _DEFAULT
    data = _CAMPAIGNS.get(cid, _CAMPAIGNS[_DEFAULT])
    fem = _is_female(gender, hero_name)
    verb = "" if fem else ""
    city = data["arrival_city"]
    return (
        f" <b>{city}</b>\n\n"
        f"{hero_name} {verb} {data['arrival_suffix_text']}"
    )

