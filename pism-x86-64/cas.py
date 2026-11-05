# -*- coding: utf-8 -*-
"""PISM: datum a čas."""

import re
import shutil
import subprocess
from pathlib import Path

import stroj

NASTAVENI = Path("/etc/systemd/timesyncd.conf.d/pism.conf")
SERVERY = (
    {"id": "cesko", "nazev": "Česko", "adresa": "cz.pool.ntp.org"},
    {"id": "evropa", "nazev": "Evropa", "adresa": "europe.pool.ntp.org"},
    {"id": "cloudflare", "nazev": "Cloudflare", "adresa": "time.cloudflare.com"},
    {"id": "google", "nazev": "Google", "adresa": "time.google.com"},
)
ADRESA = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_pasma = None


def _beh(prikaz):
    return stroj._beh(prikaz)


def _ntp_zapnuto():
    text = _beh(["timedatectl", "show", "-p", "NTP", "--value"]).stdout.strip().lower()
    return text == "yes"


def _adresa_ze_souboru():
    if not NASTAVENI.is_file():
        return ""
    for radek in NASTAVENI.read_text(encoding="utf-8").splitlines():
        if radek.startswith("NTP="):
            return radek.split("=", 1)[1].strip()
    return ""


def _adresa_zive():
    try:
        return _beh(["timedatectl", "show-timesync", "-p", "ServerName", "--value"]).stdout.strip()
    except stroj.StrojChyba:
        return ""


def _adresa():
    return _adresa_ze_souboru() or _adresa_zive()


def _volba(adresa):
    for server in SERVERY:
        if server["adresa"] == adresa:
            return server["id"]
    if not adresa:
        return "cesko"
    return "vlastni"


def _popis(adresa):
    for server in SERVERY:
        if server["adresa"] == adresa:
            return server["nazev"]
    if not adresa:
        return "Česko"
    return "Vlastní"


def _pasma_seznam():
    global _pasma
    if _pasma is None:
        _pasma = [radek for radek in _beh(["timedatectl", "list-timezones"]).stdout.splitlines() if radek]
    return _pasma


def _uloz_hw():
    if shutil.which("fake-hwclock"):
        subprocess.run(["fake-hwclock", "save"], capture_output=True, check=False)


def _uloz_server(adresa):
    NASTAVENI.parent.mkdir(parents=True, exist_ok=True)
    NASTAVENI.write_text(f"[Time]\nNTP={adresa}\n", encoding="utf-8")


def _obnov_server():
    if _ntp_zapnuto():
        _beh(["systemctl", "restart", "systemd-timesyncd"])


def stav():
    cas = _beh(["date", "+%d.%m.%Y %H:%M|%Y-%m-%d|%H:%M"]).stdout.strip().split("|")
    while len(cas) < 3:
        cas.append("")
    adresa = _adresa()
    return {
        "ted": cas[0],
        "datum": cas[1],
        "hodina": cas[2],
        "pasmo": _beh(["timedatectl", "show", "-p", "Timezone", "--value"]).stdout.strip(),
        "pasma": _pasma_seznam(),
        "ntp": _ntp_zapnuto(),
        "server": adresa,
        "server_nazev": _popis(adresa),
        "volba": _volba(adresa),
        "servery": [{"id": server["id"], "nazev": server["nazev"]} for server in SERVERY],
    }


def nastav_zdroj(ntp):
    if ntp:
        if not _adresa_ze_souboru():
            _uloz_server(SERVERY[0]["adresa"])
        _beh(["timedatectl", "set-ntp", "true"])
        _beh(["systemctl", "restart", "systemd-timesyncd"])
    else:
        _beh(["timedatectl", "set-ntp", "false"])
        _uloz_hw()
    return stav()


def nastav_server(volba, adresa=""):
    volba = str(volba or "").strip()
    if volba == "vlastni":
        adresa = str(adresa or "").strip()
        if "." not in adresa or not ADRESA.fullmatch(adresa):
            raise stroj.StrojChyba("Adresa serveru nesedí.")
    else:
        nalezeny = next((server for server in SERVERY if server["id"] == volba), None)
        if not nalezeny:
            raise stroj.StrojChyba("Vyber server.")
        adresa = nalezeny["adresa"]
    _uloz_server(adresa)
    _obnov_server()
    return stav()


def nastav_rucne(datum, hodina):
    datum = str(datum or "").strip()
    hodina = str(hodina or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", datum) or not re.fullmatch(r"\d{2}:\d{2}", hodina):
        raise stroj.StrojChyba("Datum nebo hodina nesedí.")
    bylo = _ntp_zapnuto()
    _beh(["timedatectl", "set-ntp", "false"])
    try:
        _beh(["timedatectl", "set-time", f"{datum} {hodina}:00"])
    except stroj.StrojChyba as chyba:
        if bylo:
            _beh(["timedatectl", "set-ntp", "true"])
        raise stroj.StrojChyba("Takové datum nejde nastavit.") from chyba
    _uloz_hw()
    return stav()


def nastav_pasmo(pasmo):
    pasmo = str(pasmo or "").strip()
    if pasmo not in _pasma_seznam():
        raise stroj.StrojChyba("Takové pásmo není.")
    _beh(["timedatectl", "set-timezone", pasmo])
    return stav()
