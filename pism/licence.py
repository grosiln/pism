# -*- coding: utf-8 -*-
"""PISM: licence vázaná na PI4. Jeden disk je zdarma."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import stroj


def _klic():
    import licence_klic
    return licence_klic

SOUBOR = stroj.DATA / "licence.json"
ZRCADLO = Path("/srv/pism-zrcadlo")
ZNACKA = Path("/run/pism-licence")
DNY = 30


def _nacti():
    if not SOUBOR.is_file():
        return {}
    try:
        data = json.loads(SOUBOR.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _uloz(data):
    stroj.DATA.mkdir(parents=True, exist_ok=True)
    SOUBOR.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _serial():
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    except OSError as chyba:
        raise stroj.StrojChyba("Kód tohoto PI4 nejde přečíst.") from chyba
    for radek in text.splitlines():
        if radek.lower().startswith("serial"):
            serial = radek.split(":", 1)[-1].strip().lower()
            if _klic().kod_z_serialu(serial):
                return _klic()._ciste(serial)
    raise stroj.StrojChyba("Kód tohoto PI4 nejde přečíst.")


def _usb():
    nalezene = []
    for disk in stroj._blokova():
        if disk.get("type") != "disk" or disk.get("tran") != "usb":
            continue
        if stroj._je_system(disk):
            continue
        jmeno = str(disk.get("name") or "")
        if jmeno.startswith(("mmc", "loop", "zram", "md")):
            continue
        nalezene.append(jmeno)
    return nalezene


def _ma_zrcadlo():
    try:
        text = Path("/proc/mdstat").read_text(encoding="utf-8")
    except OSError:
        return False
    return any(radek.startswith("md") and "active" in radek for radek in text.splitlines())


def _vic():
    return len(_usb()) >= 2 or _ma_zrcadlo()


def _zdroj(misto):
    try:
        text = Path("/proc/mounts").read_text(encoding="utf-8")
    except OSError:
        return ""
    for radek in text.splitlines():
        casti = radek.split()
        if len(casti) >= 2 and casti[1].replace("\\040", " ") == str(misto):
            return casti[0]
    return ""


def _je_raid(zdroj):
    jmeno = str(zdroj or "").rsplit("/", 1)[-1]
    return jmeno.startswith("md")


def _disk_z_zdroje(zdroj):
    jmeno = str(zdroj or "").rsplit("/", 1)[-1]
    while jmeno and jmeno[-1].isdigit():
        jmeno = jmeno[:-1]
    return jmeno


def _placena(data=None):
    data = _nacti() if data is None else data
    try:
        return _klic().sedi(_serial(), data.get("proti") or "")
    except stroj.StrojChyba:
        return False


def je_plna():
    return _placena()


def _start(data=None):
    data = _nacti() if data is None else data
    text = str(data.get("zkouska_od") or "")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _konec(start):
    return start + timedelta(days=DNY)


def _zkouska_bezi(data=None):
    start = _start(data)
    if not start:
        return False
    return datetime.now() < _konec(start)


def _dni(data=None):
    start = _start(data)
    if not start:
        return 0
    zbyva = (_konec(start) - datetime.now()).total_seconds()
    if zbyva <= 0:
        return 0
    return int((zbyva + 86399) // 86400)


def zapis_omezen():
    return False


def jen_cteni_svazku():
    return False


def zaznamenej():
    return


def _volny_disk():
    zdroj = _zdroj(stroj.MISTO)
    if not zdroj or _je_raid(zdroj):
        return ""
    return _disk_z_zdroje(zdroj)


def _da_se_prepnout(cil):
    cil = str(cil or "")
    if cil in {str(stroj.MISTO), str(ZRCADLO)}:
        return True
    return cil.startswith(("/mnt/", "/media/", "/run/media/", "/srv/"))


def _cile(omezeno):
    volny = _volny_disk()
    cile = []
    try:
        text = Path("/proc/mounts").read_text(encoding="utf-8")
    except OSError:
        text = ""
    for radek in text.splitlines():
        casti = radek.split()
        if len(casti) < 2 or not casti[0].startswith("/dev/"):
            continue
        cil = casti[1].replace("\\040", " ")
        if not _da_se_prepnout(cil):
            continue
        disk = _disk_z_zdroje(casti[0])
        if disk == volny:
            continue
        if disk.startswith("md") or disk in _usb() or cil == str(ZRCADLO):
            cile.append(cil)
    if not omezeno and stroj.MISTO.is_mount():
        cile.append(str(stroj.MISTO))
    return list(dict.fromkeys(cile))


def _premount(cil, jen_cteni):
    if not Path(cil).is_mount() and not (cil == str(stroj.MISTO) and stroj.MISTO.is_mount()):
        return
    volba = "remount,ro" if jen_cteni else "remount,rw"
    stroj._beh(["mount", "-o", volba, cil], cas=30)


def uplatni():
    zaznamenej()
    omezeno = zapis_omezen()
    znacka = "ro" if omezeno else "rw"
    try:
        minule = ZNACKA.read_text(encoding="ascii").strip()
    except OSError:
        minule = ""
    if omezeno or minule == "ro":
        for cil in _cile(omezeno):
            jen = jen_cteni_svazku() if cil == str(stroj.MISTO) else omezeno
            try:
                _premount(cil, jen)
            except stroj.StrojChyba:
                pass
        if not omezeno:
            try:
                _premount(str(stroj.MISTO), False)
            except stroj.StrojChyba:
                pass
    if minule == znacka or (not minule and znacka == "rw"):
        if not minule:
            try:
                ZNACKA.write_text("rw\n", encoding="ascii")
            except OSError:
                pass
        return
    try:
        stroj._samba()
    except stroj.StrojChyba:
        pass
    try:
        ZNACKA.write_text(znacka + "\n", encoding="ascii")
    except OSError:
        pass


def _vety(stav, dni):
    if stav == "placena":
        return ["Licence platí pro tohle PI4. Další disky a zrcadlo jdou používat včetně zápisu."]
    if stav == "zkouska":
        slovo = "den" if dni == 1 else "dny" if dni in {2, 3, 4} else "dní"
        return [
            f"Zkouška běží. Zbývá {dni} {slovo}. Zápis na další disk a na zrcadlo je otevřený.",
            "Až zkouška skončí, ze zrcadla a z druhého disku půjde jen číst. Soubory se dají zkopírovat. Jeden disk mimo zrcadlo zůstává.",
            "Licence na víc disků stojí 200 Kč. Pošli je na PayPal grossmann@7ruzi.cz a do zprávy u platby vlož kód tohoto PI4. Přijde proti kód.",
        ]
    if stav == "prosla":
        return [
            "Zkouška skončila. Ze zrcadla a z druhého disku jde jen číst. Soubory se dají zkopírovat, zapisovat a mazat už nejde.",
            "Jeden disk mimo zrcadlo zůstává a dá se na něj zapisovat. Data se nemažou.",
            "Licence na víc disků stojí 200 Kč. Pošli je na PayPal grossmann@7ruzi.cz a do zprávy u platby vlož kód tohoto PI4. Přijde proti kód.",
        ]
    return [
        "Jeden datový disk je zdarma. Systémová karta se nepočítá.",
        "Druhý disk a zrcadlo jdou 30 dní zkoušet. Potom z nich jde jen číst, soubory se dají zkopírovat a zápis se vypne.",
        "Licence na víc disků stojí 200 Kč. Pošli je na PayPal grossmann@7ruzi.cz a do zprávy u platby vlož kód tohoto PI4. Přijde proti kód. Platí jen pro tohle PI4.",
    ]


def stav():
    zaznamenej()
    data = _nacti()
    if _placena(data):
        druh = "placena"
    elif _vic() and _zkouska_bezi(data):
        druh = "zkouska"
    elif _vic() and _start(data):
        druh = "prosla"
    else:
        druh = "zdarma"
    return {
        "kod": _klic().kod_z_serialu(_serial()),
        "stav": druh,
        "dni": _dni(data) if druh == "zkouska" else 0,
        "placena": druh == "placena",
        "vety": _vety(druh, _dni(data) if druh == "zkouska" else 0),
    }


def zadej(proti):
    serial = _serial()
    if not _klic().sedi(serial, proti):
        raise stroj.StrojChyba("Proti kód k tomuhle PI4 nesedí.")
    data = _nacti()
    data["proti"] = _klic()._skupiny(_klic()._ciste(proti))
    _uloz(data)
    uplatni()
    return stav()
