# -*- coding: utf-8 -*-
# app/core/config.py
from __future__ import annotations
import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

USE_OPENAI = os.environ.get("OAI_ENABLED", "0").lower() in ("1", "true", "yes", "y")
oai_client = None
if USE_OPENAI:
    try:
        from openai import AsyncOpenAI
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
        if OPENAI_API_KEY:
            oai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    except Exception:
        oai_client = None
