# -*- coding: utf-8 -*-
"""PISM: kontrola novější verze a její výměna."""

import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import stroj

VERZE_URL = "https://raw.githubusercontent.com/grosiln/pism/main/verze.txt"
ARCHIV_URL = "https://github.com/grosiln/pism/archive/refs/heads/main.tar.gz"
KORENOVA = Path(__file__).resolve().parent
ZALOHA = KORENOVA.parent / "pism-zaloha"
PAMET = stroj.DATA / "aktualizace.json"
KLID = 24 * 3600
MEZ = 30_000_000
SOUBORY = (
    "aktualizace.py",
    "server.py",
    "stroj.py",
    "raid.py",
    "licence.py",
    "dar.py",
    "napoveda.py",
    "cas.py",
    "sdileni.py",
    "sit.py",
    "vetrak.py",
    "pism-sit",
    "pism.service",
    "pism-vetrak.service",
    "pism-sit.service",
    "grosistudio-logo.png",
)
WEB = ("index.html", "app.js", "style.css")
_zamek = threading.Lock()


def _cislo(text):
    casti = []
    for kus in str(text or "").strip().split("."):
        if not kus.isdigit():
            return None
        casti.append(int(kus))
    return tuple(casti) if casti else None


def _novejsi(vzdalena, mistni):
    vzdalene = _cislo(vzdalena)
    mistni_cislo = _cislo(mistni)
    if not vzdalene or not mistni_cislo:
        return False
    delka = max(len(vzdalene), len(mistni_cislo))
    vzdalene = vzdalene + (0,) * (delka - len(vzdalene))
    mistni_cislo = mistni_cislo + (0,) * (delka - len(mistni_cislo))
    return vzdalene > mistni_cislo


def _nacti():
    try:
        data = json.loads(PAMET.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _uloz(data):
    stroj.DATA.mkdir(parents=True, exist_ok=True)
    PAMET.write_text(json.dumps(data), encoding="utf-8")


def _stahni(url, cas):
    pozadavek = urllib.request.Request(url, headers={"User-Agent": "PISM"})
    with urllib.request.urlopen(pozadavek, timeout=cas) as odpoved:
        data = odpoved.read(MEZ + 1)
    if len(data) > MEZ:
        raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.")
    return data


def vzdalena():
    with _zamek:
        cache = _nacti()
        ted = time.time()
        ulozena = str(cache.get("vzdalena") or "").strip()
        try:
            kontrola = float(cache.get("kontrola") or 0)
        except (TypeError, ValueError):
            kontrola = 0
        if ulozena and ted - kontrola < KLID:
            return ulozena
        try:
            text = _stahni(VERZE_URL, 8).decode("utf-8", "replace")
        except Exception:
            return ulozena
        radek = text.strip().splitlines()
        nova = radek[0].strip() if radek else ""
        if not _cislo(nova):
            return ulozena
        _uloz({"kontrola": ted, "vzdalena": nova})
        return nova


def je_novejsi():
    try:
        return _novejsi(vzdalena(), stroj.VERZE)
    except Exception:
        return False


def polozky(zaklad):
    seznam = list(zaklad)
    if je_novejsi():
        seznam.insert(0, {"id": "aktualizace", "nazev": "Aktualizace PISM"})
    return seznam


def texty():
    nova = ""
    try:
        nova = vzdalena()
    except Exception:
        nova = ""
    vety = ["Je novější PISM."]
    if nova:
        vety.append(f"Teď je {stroj.VERZE}. Nová je {nova}.")
    vety.append("Účty, složky, disky, zrcadlo i síť zůstanou.")
    return {"vety": vety, "lze": _novejsi(nova, stroj.VERZE), "nova": nova}


def _kopiruj(zdroj, cil):
    cil.mkdir(parents=True, exist_ok=True)
    (cil / "web").mkdir(exist_ok=True)
    for jmeno in SOUBORY:
        odkud = zdroj / jmeno
        if odkud.is_file():
            shutil.copy2(odkud, cil / jmeno)
    for jmeno in WEB:
        shutil.copy2(zdroj / "web" / jmeno, cil / "web" / jmeno)
    sit = cil / "pism-sit"
    if sit.is_file():
        sit.chmod(0o755)


def _verze_archivu(koren):
    soubor = koren.parent / "verze.txt"
    try:
        radek = soubor.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        radek = ""
    text = (koren / "stroj.py").read_text(encoding="utf-8")
    nalez = re.search(r'(?m)^VERZE = "([^"]+)"', text)
    ve_stroji = nalez.group(1) if nalez else ""
    if not radek or radek != ve_stroji:
        raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.")
    return radek


def _preloz(koren):
    prikazy = [sys.executable, "-m", "py_compile"]
    for jmeno in SOUBORY:
        if jmeno.endswith(".py") and (koren / jmeno).is_file():
            prikazy.append(str(koren / jmeno))
    beh = subprocess.run(prikazy, capture_output=True, text=True)
    if beh.returncode != 0:
        raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.")


def _jednotky(zdroj):
    cil = Path("/etc/systemd/system")
    if not cil.is_dir():
        return
    for jmeno in ("pism.service", "pism-vetrak.service", "pism-sit.service"):
        odkud = zdroj / jmeno
        if odkud.is_file():
            shutil.copy2(odkud, cil / jmeno)
    sit = zdroj / "pism-sit"
    if sit.is_file():
        shutil.copy2(sit, Path("/usr/local/sbin/pism-sit"))
        Path("/usr/local/sbin/pism-sit").chmod(0o755)
        dispatcher = Path("/etc/NetworkManager/dispatcher.d")
        if dispatcher.is_dir():
            shutil.copy2(sit, dispatcher / "99-pism-sit")
            (dispatcher / "99-pism-sit").chmod(0o755)
    subprocess.run(["systemctl", "daemon-reload"], capture_output=True)


def _hlidac():
    ZALOHA.mkdir(parents=True, exist_ok=True)
    radky = [
        "#!/bin/bash",
        "if curl -fsS --max-time 5 http://127.0.0.1/api/stav >/dev/null; then exit 0; fi",
    ]
    for jmeno in SOUBORY:
        radky.append(
            f'[ -f "{ZALOHA / jmeno}" ] && cp "{ZALOHA / jmeno}" "{KORENOVA / jmeno}"'
        )
    radky.append(f'mkdir -p "{KORENOVA / "web"}"')
    for jmeno in WEB:
        radky.append(
            f'[ -f "{ZALOHA / "web" / jmeno}" ] && cp "{ZALOHA / "web" / jmeno}" "{KORENOVA / "web" / jmeno}"'
        )
    radky += [
        "systemctl daemon-reload",
        "systemctl restart pism.service",
        "exit 0",
        "",
    ]
    cil = ZALOHA / "hlidac.sh"
    cil.write_text("\n".join(radky), encoding="utf-8")
    cil.chmod(0o755)
    return cil


def proved():
    if not je_novejsi():
        raise stroj.StrojChyba("Novější PISM není.")
    with tempfile.TemporaryDirectory() as tmp:
        koren_tmp = Path(tmp)
        archiv = koren_tmp / "pism.tar.gz"
        try:
            archiv.write_bytes(_stahni(ARCHIV_URL, 120))
            with tarfile.open(archiv, "r:gz") as balicek:
                if hasattr(tarfile, "data_filter"):
                    balicek.extractall(koren_tmp, filter="data")
                else:
                    balicek.extractall(koren_tmp)
        except stroj.StrojChyba:
            raise
        except Exception as chyba:
            raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.") from chyba
        nalezene = list(koren_tmp.glob("pism-*/pism/server.py"))
        if len(nalezene) != 1:
            raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.")
        zdroj = nalezene[0].parent
        nova = _verze_archivu(zdroj)
        if not _novejsi(nova, stroj.VERZE):
            raise stroj.StrojChyba("Novější PISM není.")
        _preloz(zdroj)
        _kopiruj(KORENOVA, ZALOHA)
        try:
            _kopiruj(zdroj, KORENOVA)
            _jednotky(KORENOVA)
        except Exception as chyba:
            _kopiruj(ZALOHA, KORENOVA)
            raise stroj.StrojChyba("Aktualizace se nepovedla. Tahle verze zůstala.") from chyba
    hlidac = _hlidac()
    stroj._beh(
        ["systemd-run", "--on-active=3s", "--collect", "systemctl", "restart", "pism.service"],
        cas=20,
    )
    stroj._beh(
        ["systemd-run", "--on-active=25s", "--collect", "bash", str(hlidac)],
        cas=20,
    )
    return {}
