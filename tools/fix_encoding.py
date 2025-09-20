# -*- coding: utf-8 -*-
# tools/fix_encoding.py
"""
Авто-чинилка "крякозябр" в исходниках.
Проходит по файлам проекта, пытается:
  1) Если файл не декодируется как UTF-8 — прочитать как cp1251 и пересохранить в UTF-8.
  2) Если файл декодируется как UTF-8, но внутри видны "Ð", "Ñ", "Р" и пр. — попытаться
     восстановить исходный русский текст через обратную перекодировку и сохранить в UTF-8.

Перед началом сделай резервную копию (git-коммит/branch).
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Tuple

# Что правим
EXTS = {".py", ".txt", ".md", ".ini", ".cfg", ".toml", ".env", ".yml", ".yaml"}

# Эвристика: "подозрительные" символы, характерные для mojibake UTF-8→(latin1/cp1251)
SUSPICIOUS = set("ÐÑÐ¡Ð¢ÐžÐ�ÐœÐšÐ›Ð�Ð¤Ð²Ð·Ð¸Ð№Ð°Ð±Ð²Â°Â©Â«Â»Â—Â–Â…РЃР�Р‘Р’Р“Р”Р•Р–Р—Р�Р™РљР›РњРќРћРџР РЎРўРЈР¤РҐР¦Р§РЁР©РЄР«Р¬Р­Р®РЇ")

def is_text_path(p: Path) -> bool:
    return p.suffix.lower() in EXTS and p.name != "fix_encoding.py"

def cyr_fraction(s: str) -> float:
    if not s:
        return 0.0
    total = sum(ch.isalpha() for ch in s)
    if total == 0:
        return 0.0
    cyr = sum(0x0400 <= ord(ch) <= 0x04FF for ch in s)  # кириллица
    return cyr / total

def looks_mojibake(s: str) -> bool:
    # много "Ð"/"Ñ"/"Р" и т.п. — вероятно, кракозябры
    sus = sum(ch in SUSPICIOUS for ch in s)
    return sus >= 5 and cyr_fraction(s) < 0.2

def try_fix_utf8_text(s: str) -> Tuple[bool, str]:
    """
    Файл уже декодирован как UTF-8, но текст выглядит поломанным.
    Пробуем два типичных сценария:
      - utf8 байты декодировали как latin1 → сейчас видим 'Ð�...'
      - utf8 байты декодировали как cp1251 → сейчас видим 'Р”...'
    """
    candidates = []
    for enc in ("latin1", "cp1251"):
        try:
            fixed = s.encode(enc, errors="strict").decode("utf-8", errors="strict")
            score = cyr_fraction(fixed)
            candidates.append((score, fixed))
        except Exception:
            pass
    if not candidates:
        return False, s
    best = max(candidates, key=lambda x: x[0])
    # Считаем успешной починкой, если кириллицы стало заметно
    if best[0] >= 0.3:
        return True, best[1]
    return False, s

def process_file(path: Path) -> Tuple[bool, str]:
    raw = path.read_bytes()

    # 1) Попытка — считать как UTF-8
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        # 1a) Не UTF-8 → пробуем CP1251, потом сохраняем как UTF-8
        try:
            text1251 = raw.decode("cp1251", errors="strict")
        except Exception as e:
            return False, f"{path}: не удалось декодировать ни как UTF-8, ни как CP1251 ({e})"
        path.write_text(text1251, encoding="utf-8", newline="")
        return True, f"{path}: CP1251 → UTF-8"

    # 2) Это валидный UTF-8. Проверим на «крякозябры»
    if looks_mojibake(text):
        ok, fixed = try_fix_utf8_text(text)
        if ok and fixed != text:
            path.write_text(fixed, encoding="utf-8", newline="")
            return True, f"{path}: UTF-8 mojibake → исправлено"
    return False, f"{path}: ок"

def main():
    root = Path(__file__).resolve().parents[1]  # корень проекта (на уровень выше tools)
    changed = 0
    touched = 0
    print(f"[fix-encoding] Прохожу по: {root}")
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if not is_text_path(p):
            continue
        touched += 1
        try:
            ok, msg = process_file(p)
            if ok:
                changed += 1
                print("  [+]", msg)
            else:
                # комментируй, если много вывода
                # print("  [ ]", msg)
                pass
        except Exception as e:
            print("  [!]", p, "ошибка:", e)
    print(f"[fix-encoding] Готово. Файлов проверено: {touched}, исправлено: {changed}")

if __name__ == "__main__":
    main()
