# -*- coding: utf-8 -*-
"""PISM: dobrovolný dar."""

import json
import random
import time

import stroj

SOUBOR = stroj.DATA / "dar.json"
KLID = 3 * 24 * 3600
VETY = [
    "Děkuji, že používáš PISM.",
    "Vzniká po večerech a každá další úprava stojí čas. Když ti dobře slouží a chceš podpořit vývoj, pošli dar na PayPal grossmann@7ruzi.cz. Hodí se třeba 200 Kč, ale potěší i méně.",
    "Nic se tím nezmění. Disky, složky i zrcadlo jedou dál stejně.",
    "Děkuji.",
]


def texty():
    return {"vety": VETY}


def _naposledy():
    try:
        data = json.loads(SOUBOR.read_text(encoding="utf-8"))
        return float(data.get("naposledy") or 0)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0.0


def losuj():
    ted = time.time()
    naposledy = _naposledy()
    if naposledy and ted - naposledy < KLID:
        return False
    if random.randrange(4) != 0:
        return False
    try:
        stroj.DATA.mkdir(exist_ok=True)
        SOUBOR.write_text(json.dumps({"naposledy": ted}), encoding="utf-8")
    except OSError:
        return False
    return True
