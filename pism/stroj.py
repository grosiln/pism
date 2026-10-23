# -*- coding: utf-8 -*-
"""PISM: síť, disky, účty a informace o systému."""

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

VERZE = "1.1"
MISTO = Path("/srv/pism")
SLOZKY_DIR = MISTO / "slozky"
DALSI_KOREN = Path("/srv/pism-dalsi")
ZNACKA_DALSI = "PISMDISK"
DATA = Path(__file__).resolve().parent / "data"
SOUBOR_SLOZEK = DATA / "slozky.json"
SMB = Path("/etc/samba/pism.conf")
SMB_HLAVNI = Path("/etc/samba/smb.conf")
FSTAB = Path("/etc/fstab")
HOSTS = Path("/etc/hosts")
SKUPINA = "pism"
ZAKAZANE = {"pi", "root", "www-data", "nobody"}
JMENO_UCTU = re.compile(r"^[a-z][a-z0-9]{1,20}$")
JMENO_SLOZKY = re.compile(r"^[a-z][a-z0-9]{1,20}$")
JMENO_ZARIZENI = re.compile(r"^[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?$")


class StrojChyba(Exception):
    pass


def _beh(prikaz, vstup=None, cas=60, prostredi=None):
    try:
        prostredi_beh = os.environ.copy()
        if prostredi:
            prostredi_beh.update(prostredi)
        return subprocess.run(
            prikaz,
            input=vstup,
            text=True,
            capture_output=True,
            timeout=cas,
            check=True,
            env=prostredi_beh,
        )
    except subprocess.CalledProcessError as chyba:
        text = (chyba.stderr or chyba.stdout or "").strip()
        raise StrojChyba(text or "Příkaz na PI4 se nepovedl.") from chyba
    except subprocess.TimeoutExpired as chyba:
        raise StrojChyba("PI4 nestihla příkaz včas.") from chyba


def _skupina():
    _beh(["groupadd", "-f", SKUPINA])


def _lidske(bajty):
    hodnota = float(bajty)
    for jednotka in ("B", "KB", "MB", "GB", "TB"):
        if hodnota < 1024 or jednotka == "TB":
            if jednotka == "B":
                return f"{int(hodnota)} {jednotka}"
            return f"{hodnota:.1f} {jednotka}"
        hodnota /= 1024
    return f"{bajty} B"


def _blokova():
    text = _beh(["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,TRAN,MODEL,MOUNTPOINT,FSTYPE,LABEL,UUID"]).stdout
    return json.loads(text).get("blockdevices", [])


def _potomci(zarizeni):
    nalezene = []

    def chod(polozka):
        nalezene.append(polozka)
        for dite in polozka.get("children") or []:
            chod(dite)

    chod(zarizeni)
    return nalezene


def _je_system(zarizeni):
    return any((dite.get("mountpoint") or "") == "/" for dite in _potomci(zarizeni))


def _ma_svazek_pism(disk):
    for dite in _potomci(disk):
        if (dite.get("label") or "") == "PISM" and (dite.get("mountpoint") or "") == str(MISTO):
            return True
    return False


def _datovy():
    usb = [
        polozka for polozka in _blokova()
        if polozka.get("type") == "disk" and polozka.get("tran") == "usb" and not _je_system(polozka)
    ]
    if not usb:
        raise StrojChyba("Na USB není datový disk.")
    se_svazkem = [disk for disk in usb if _ma_svazek_pism(disk)]
    if len(se_svazkem) == 1:
        return se_svazkem[0]
    if len(usb) > 1:
        raise StrojChyba("Je připojených víc disků na USB. Nech zapojený jen ten na zkoušky.")
    return usb[0]


def _cesta_disku(jmeno):
    if not re.fullmatch(r"[a-z0-9]+", jmeno or ""):
        raise StrojChyba("Disk nejde poznat.")
    return Path("/dev") / jmeno


def _oddil(disk):
    jmeno = disk["name"]
    if jmeno[-1].isdigit():
        return f"/dev/{jmeno}p1"
    return f"/dev/{jmeno}1"


def _odpoj(misto):
    if not misto or misto == str(MISTO):
        if misto:
            _beh(["umount", misto])
        return
    chranene = {"/", "/boot", "/boot/firmware", "/home", "/usr", "/var", "/etc", "/srv"}
    if misto in chranene or misto.startswith("/boot/"):
        raise StrojChyba("Systémová karta se nemaže.")
    if str(misto).startswith(str(DALSI_KOREN) + "/") or misto == "/srv/pism-zrcadlo":
        _beh(["umount", misto])
        return
    if not (misto.startswith("/mnt/") or misto.startswith("/media/") or misto.startswith("/run/media/")):
        raise StrojChyba("Disk je připojený na nečekaném místě. Nechávám ho být.")
    _beh(["umount", misto])


def _pockej_na_oddil(cesta, oddil):
    subprocess.run(["udevadm", "settle"], timeout=20, check=False)
    if Path(oddil).exists():
        return
    try:
        subprocess.run(["partx", "-u", cesta], timeout=20, check=False)
    except FileNotFoundError:
        pass
    subprocess.run(["udevadm", "settle"], timeout=20, check=False)
    if not Path(oddil).exists():
        raise StrojChyba("Nový oddíl se neobjevil.")


def _vlastnik(cesta):
    import grp
    _skupina()
    gid = grp.getgrnam(SKUPINA).gr_gid
    os.chown(cesta, 0, gid)
    os.chmod(cesta, 0o2775)


def _obsazeni(cesta):
    if not Path(cesta).is_dir():
        return None
    stav = os.statvfs(cesta)
    celkem = stav.f_blocks * stav.f_frsize
    volno = stav.f_bavail * stav.f_frsize
    return {"celkem": _lidske(celkem), "obsazeno": _lidske(celkem - volno), "volno": _lidske(volno)}


def _volno(cesta):
    if not Path(cesta).is_dir():
        return ""
    stav = os.statvfs(cesta)
    return _lidske(stav.f_bavail * stav.f_frsize)


def _dopln_zrcadlo(seznam):
    import raid
    zrcadlo = raid.prehled_zrcadla()
    if zrcadlo:
        seznam.append(zrcadlo)


def disky():
    seznam = []
    datovy = None
    vic_disku = False
    try:
        datovy = _datovy()
    except StrojChyba as chyba:
        vic_disku = "víc disků" in str(chyba)
    for polozka in _blokova():
        if polozka.get("type") != "disk":
            continue
        systemovy = _je_system(polozka)
        je_datovy = datovy is not None and polozka.get("name") == datovy.get("name")
        if not systemovy and not je_datovy:
            continue
        oddily = [dite for dite in _potomci(polozka) if dite.get("type") == "part"]
        svazek = any((dite.get("label") or "") == "PISM" and (dite.get("mountpoint") or "") == str(MISTO) for dite in oddily)
        popis = {
            "nazev": "Systémová SD karta" if systemovy else "Datový disk",
            "model": (polozka.get("model") or "").strip() or "Neznámý disk",
            "velikost": _lidske(int(polozka.get("size") or 0)),
            "systemovy": systemovy,
            "svazek": svazek,
            "volno": _volno("/") if systemovy else (_volno(MISTO) if svazek else ""),
        }
        if not systemovy and not svazek and oddily:
            popis["poznamka"] = "Ještě to není datový disk."
        if not systemovy:
            popis["klic"] = "hlavni"
        seznam.append(popis)
    for dalsi in _seznam_datovych():
        if dalsi["hlavni"]:
            continue
        seznam.append({
            "nazev": "Datový disk",
            "model": dalsi["model"],
            "velikost": dalsi["velikost"],
            "systemovy": False,
            "svazek": True,
            "volno": dalsi["volno"],
            "klic": dalsi["klic"],
        })
    seznam.sort(key=lambda polozka: 0 if polozka.get("systemovy") else 1)
    _dopln_zrcadlo(seznam)
    ma_svazek = any(
        (polozka.get("svazek") and not polozka.get("systemovy")) or (polozka.get("zrcadlo") and polozka.get("svazek"))
        for polozka in seznam
    )
    return {
        "disky": seznam,
        "kandidati": _kandidati(),
        "lze_pridat": datovy is not None and not ma_svazek,
        "ma_svazek": ma_svazek,
        "vic_disku": vic_disku,
    }


def _je_v_poli(disk):
    for dite in _potomci(disk):
        if str(dite.get("type") or "").startswith("raid"):
            return True
        if (dite.get("fstype") or "") == "linux_raid_member":
            return True
    return False


def _kandidati():
    vysledek = []
    for disk in _blokova():
        if disk.get("type") != "disk" or disk.get("tran") != "usb" or _je_system(disk):
            continue
        jmeno = str(disk.get("name") or "")
        if not jmeno or jmeno.startswith(("mmc", "loop", "zram", "md")):
            continue
        if _ma_svazek_pism(disk) or _je_dalsi(disk) or _je_v_poli(disk):
            continue
        try:
            bajty = int(disk.get("size") or 0)
        except (TypeError, ValueError):
            bajty = 0
        if bajty <= 0:
            continue
        vysledek.append({
            "jmeno": jmeno,
            "model": (disk.get("model") or "").replace("_", " ").strip() or "Neznámý disk",
            "velikost": _lidske(bajty),
        })
    return vysledek


def _je_dalsi(disk):
    for dite in _potomci(disk):
        if (dite.get("label") or "") == ZNACKA_DALSI:
            return True
        montaz = dite.get("mountpoint") or ""
        if montaz.startswith(str(DALSI_KOREN) + "/"):
            return True
    return False


def _seznam_datovych():
    vysledek = []
    for disk in _blokova():
        if disk.get("type") != "disk":
            continue
        model = (disk.get("model") or "").replace("_", " ").strip() or "Neznámý disk"
        try:
            velikost = _lidske(int(disk.get("size") or 0))
        except (TypeError, ValueError):
            velikost = ""
        jmeno = str(disk.get("name") or "")
        for dite in _potomci(disk):
            if dite.get("type") != "part":
                continue
            label = dite.get("label") or ""
            montaz = dite.get("mountpoint") or ""
            uuid = str(dite.get("uuid") or "").lower()
            if label == "PISM" and montaz == str(MISTO):
                vysledek.append({
                    "klic": "hlavni",
                    "hlavni": True,
                    "model": model,
                    "velikost": velikost,
                    "volno": _volno(MISTO),
                    "misto": str(MISTO),
                    "jmeno": jmeno,
                    "uuid": uuid,
                })
            elif label == ZNACKA_DALSI and uuid and montaz.startswith(str(DALSI_KOREN) + "/"):
                vysledek.append({
                    "klic": uuid,
                    "hlavni": False,
                    "model": model,
                    "velikost": velikost,
                    "volno": _volno(montaz),
                    "misto": montaz,
                    "jmeno": jmeno,
                    "uuid": uuid,
                })
    return vysledek


def mista_pro_slozky():
    mista = []
    for disk in _seznam_datovych():
        if Path(disk["misto"]).is_mount():
            mista.append({
                "klic": disk["klic"],
                "model": disk["model"],
                "velikost": disk["velikost"],
                "misto": disk["misto"],
                "cleny": [],
            })
    import raid
    zrcadlo = raid.prehled_zrcadla()
    if zrcadlo and zrcadlo.get("pripojeno"):
        mista.append({
            "klic": "zrcadlo",
            "model": "Zrcadlo",
            "velikost": zrcadlo.get("velikost") or "",
            "misto": str(raid.RAID_MISTO),
            "cleny": zrcadlo.get("cleny") or [],
        })
    return mista


def _blok_podle_jmena(jmeno):
    jmeno = str(jmeno or "")
    if not re.fullmatch(r"sd[a-z]+", jmeno):
        raise StrojChyba("Disk nejde poznat.")
    for disk in _blokova():
        if disk.get("type") == "disk" and disk.get("name") == jmeno:
            return disk
    raise StrojChyba("Disk už není připojený.")


def disk_ma_sdileni(disk):
    return _ma_svazek_pism(disk) or _je_dalsi(disk)


def _klic_podle_jmena(jmeno):
    for disk in _seznam_datovych():
        if disk["jmeno"] == jmeno:
            return disk["klic"]
    return ""


def _smart_raw(data, cislo):
    for radek in (data.get("ata_smart_attributes") or {}).get("table") or []:
        if radek.get("id") != cislo:
            continue
        try:
            return int((radek.get("raw") or {}).get("value") or 0)
        except (TypeError, ValueError):
            return 0
    return 0


def _smart_json(zarizeni):
    if not shutil.which("smartctl"):
        return None
    for prikaz in (
        ["smartctl", "-j", "-a", zarizeni],
        ["smartctl", "-j", "-d", "sat", "-a", zarizeni],
    ):
        try:
            vysledek = subprocess.run(prikaz, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            continue
        try:
            data = json.loads(vysledek.stdout or "{}")
        except json.JSONDecodeError:
            continue
        stav = data.get("smart_status")
        if isinstance(stav, dict) and "passed" in stav:
            return data
    return None


def _disk_pro_smart(klic):
    klic = str(klic or "")
    if klic.startswith("raid:"):
        jmeno = klic.split(":", 1)[1]
        if not re.fullmatch(r"sd[a-z]+", jmeno):
            return {"lze": False, "veta": "Není disk k dispozici."}
        import raid
        zrcadlo = raid.prehled_zrcadla() or {}
        cleny = zrcadlo.get("cleny_disky") or []
        if not any(clen.get("jmeno") == jmeno for clen in cleny):
            return {"lze": False, "veta": "Není disk k dispozici."}
        try:
            return _blok_podle_jmena(jmeno)
        except StrojChyba:
            return {"lze": False, "veta": "Není disk k dispozici."}
    if klic:
        nalezeny = next((polozka for polozka in _seznam_datovych() if polozka["klic"] == klic), None)
        if not nalezeny:
            return {"lze": False, "veta": "Není disk k dispozici."}
        try:
            return _blok_podle_jmena(nalezeny["jmeno"])
        except StrojChyba:
            return {"lze": False, "veta": "Není disk k dispozici."}
    try:
        return _datovy()
    except StrojChyba:
        return {"lze": False, "veta": "Není disk k dispozici."}


def _kratky_smart(klic):
    stav = smart(klic)
    if stav.get("lze") and stav.get("stav_text"):
        return stav["stav_text"]
    return "nejde přečíst"


def smart(klic=""):
    disk = _disk_pro_smart(klic)
    if disk.get("lze") is False:
        return disk
    jmeno = str(disk.get("name", ""))
    if _je_system(disk) or jmeno.startswith("mmc"):
        return {"lze": False, "veta": "Systémová karta SMART nemá."}
    data = _smart_json(str(_cesta_disku(jmeno)))
    if not data:
        return {"lze": False, "veta": "Z tohoto disku SMART nejde přečíst."}
    proslo = bool((data.get("smart_status") or {}).get("passed"))
    model = (data.get("model_name") or disk.get("model") or "").replace("_", " ").strip() or "Neznámý disk"
    teplota = (data.get("temperature") or {}).get("current")
    hodiny = (data.get("power_on_time") or {}).get("hours")
    if not isinstance(hodiny, int):
        hodiny = _smart_raw(data, 9)
    presunuta = _smart_raw(data, 5)
    cekajici = _smart_raw(data, 197)
    neopravitelna = _smart_raw(data, 198)
    spatne = []
    if not proslo:
        spatne.append("kontrola neprošla")
    if cekajici > 0:
        spatne.append("čekající poškozená místa")
    if neopravitelna > 0:
        spatne.append("neopravitelná místa")
    if presunuta >= 100:
        spatne.append("hodně přesunutých míst")
    if isinstance(teplota, (int, float)) and not isinstance(teplota, bool) and teplota >= 60:
        spatne.append("disk je příliš horký")
    dobre = []
    if 0 < presunuta < 100:
        dobre.append("má přesunutá poškozená místa")
    if isinstance(teplota, (int, float)) and not isinstance(teplota, bool) and 50 <= teplota < 60:
        dobre.append("je teplý")
    if isinstance(hodiny, int) and hodiny >= 40000:
        dobre.append("je už dlouho v provozu")
    if spatne:
        stav, text, veta = "spatny", "Špatný", "Disk hlásí problém. Data na něm jsou v ohrožení."
    elif dobre:
        stav, text, veta = "dobry", "Dobrý", "Disk běží, ale " + dobre[0] + "."
    else:
        stav, text, veta = "vyborny", "Výborný", "Disk je v pořádku a nic nehlásí."
    mista = []
    if presunuta:
        mista.append(f"přesunutá místa: {presunuta}")
    if cekajici:
        mista.append(f"čekající místa: {cekajici}")
    if neopravitelna:
        mista.append(f"neopravitelná místa: {neopravitelna}")
    beh = "nejde zjistit"
    if isinstance(hodiny, int) and hodiny >= 0:
        beh = f"{hodiny:,}".replace(",", " ") + " hodin"
    teplota_text = "nejde zjistit"
    if isinstance(teplota, (int, float)) and not isinstance(teplota, bool):
        teplota_text = f"{int(teplota)} °C"
    return {
        "lze": True,
        "stav": stav,
        "stav_text": text,
        "veta": veta,
        "model": model,
        "teplota": teplota_text,
        "beh": beh,
        "mista": ", ".join(mista) if mista else "žádná",
    }


def _fstab(uuid):
    radek = f"UUID={uuid} {MISTO} ext4 defaults,noatime 0 2 # pism-svazek"
    radky = []
    if FSTAB.exists():
        radky = [
            line for line in FSTAB.read_text(encoding="utf-8").splitlines()
            if "pism-svazek" not in line and "# pism-ftp" not in line
        ]
    radky.append(radek)
    FSTAB.write_text("\n".join(radky) + "\n", encoding="utf-8")


def _priprav_prazdny(disk, label):
    jmeno = str(disk.get("name") or "")
    if _je_system(disk) or jmeno.startswith("mmc"):
        raise StrojChyba("Systémová karta se nemaže.")
    _odpoj_ftp()
    for dite in _potomci(disk):
        if dite is disk:
            continue
        _odpoj(dite.get("mountpoint"))
    cesta = str(_cesta_disku(jmeno))
    _beh(["wipefs", "-a", cesta], cas=120)
    _beh(["sfdisk", "--wipe", "always", "--wipe-partitions", "always", cesta], vstup="label: gpt\n,\n", cas=120)
    oddil = _oddil(disk)
    _pockej_na_oddil(cesta, oddil)
    _beh(["mkfs.ext4", "-F", "-L", label, oddil], cas=180)
    uuid = _beh(["blkid", "-s", "UUID", "-o", "value", oddil]).stdout.strip().lower()
    if not re.fullmatch(r"[0-9a-f-]{8,}", uuid):
        raise StrojChyba("Nový svazek nemá značku.")
    return oddil, uuid


def _token_uuid(uuid):
    token = re.sub(r"[^0-9a-f]", "", str(uuid or "").lower())[:8]
    if not re.fullmatch(r"[0-9a-f]{8}", token):
        raise StrojChyba("Nový svazek nemá značku.")
    return token


def _zaloz_hlavni(disk):
    oddil, uuid = _priprav_prazdny(disk, "PISM")
    MISTO.mkdir(parents=True, exist_ok=True)
    _beh(["mount", oddil, str(MISTO)])
    _fstab(uuid)
    _skupina()
    SLOZKY_DIR.mkdir(parents=True, exist_ok=True)
    _vlastnik(SLOZKY_DIR)


def _pridej_dalsi_fstab(uuid, misto):
    radek = f"UUID={uuid} {misto} ext4 defaults,noatime 0 2 # pism-dalsi"
    radky = []
    if FSTAB.exists():
        radky = [
            line for line in FSTAB.read_text(encoding="utf-8").splitlines()
            if f"UUID={uuid} " not in line or "# pism-dalsi" not in line
        ]
    radky.append(radek)
    FSTAB.write_text("\n".join(radky) + "\n", encoding="utf-8")


def _odeber_mista_z_fstab(mista):
    cile = {str(misto) for misto in mista}
    if not FSTAB.exists():
        return
    nove = []
    for line in FSTAB.read_text(encoding="utf-8").splitlines():
        casti = line.split()
        if len(casti) >= 2 and casti[1] in cile and ("pism-svazek" in line or "pism-dalsi" in line):
            continue
        nove.append(line)
    FSTAB.write_text(("\n".join(nove).rstrip() + "\n") if nove else "", encoding="utf-8")


def _zaloz_dalsi(disk):
    oddil, uuid = _priprav_prazdny(disk, ZNACKA_DALSI)
    misto = DALSI_KOREN / _token_uuid(uuid)
    misto.mkdir(parents=True, exist_ok=True)
    _beh(["mount", oddil, str(misto)])
    _pridej_dalsi_fstab(uuid, misto)
    koren = misto / "slozky"
    koren.mkdir(parents=True, exist_ok=True)
    _vlastnik(koren)


def vytvor_svazek(jmeno=""):
    kandidati = _kandidati()
    if jmeno:
        vybrany = next((disk for disk in kandidati if disk["jmeno"] == jmeno), None)
    else:
        vybrany = kandidati[0] if len(kandidati) == 1 else None
    if not vybrany:
        raise StrojChyba("Není disk k dispozici.")
    blok = _blok_podle_jmena(vybrany["jmeno"])
    if _seznam_datovych():
        _zaloz_dalsi(blok)
    else:
        _zaloz_hlavni(blok)
    return disky()


def _odeber_svazek_z_fstab():
    if not FSTAB.exists():
        return
    radky = [
        line for line in FSTAB.read_text(encoding="utf-8").splitlines()
        if "pism-svazek" not in line
    ]
    FSTAB.write_text(("\n".join(radky).rstrip() + "\n") if radky else "", encoding="utf-8")


def smaz_disk(klic="hlavni"):
    klic = str(klic or "hlavni")
    cil = next((disk for disk in _seznam_datovych() if disk["klic"] == klic), None)
    if not cil:
        raise StrojChyba("Disk není.")
    blok = _blok_podle_jmena(cil["jmeno"])
    if _je_system(blok) or str(blok.get("name") or "").startswith("mmc"):
        raise StrojChyba("Systémová karta se nemaže.")
    _odpoj_ftp()
    if Path(cil["misto"]).is_mount():
        try:
            _beh(["umount", cil["misto"]])
        except StrojChyba as chyba:
            raise StrojChyba("Datový disk se nepodařilo odpojit.") from chyba
    _odeber_mista_z_fstab([cil["misto"]])
    for dite in _potomci(blok):
        if dite.get("type") != "part":
            continue
        cesta_oddilu = _cesta_disku(dite.get("name"))
        if cesta_oddilu.exists():
            _beh(["wipefs", "-a", str(cesta_oddilu)], cas=120)
    _beh(["wipefs", "-a", str(_cesta_disku(cil["jmeno"]))], cas=120)
    data = _nacti_slozky()
    _uloz_slozky({nazev: zaznam for nazev, zaznam in data.items() if _klic_slozky(zaznam) != klic})
    _samba()
    return disky()


def zajisti_ucet(ucet, heslo):
    if ucet in ZAKAZANE or not JMENO_UCTU.fullmatch(ucet):
        raise StrojChyba("Takový účet nejde založit.")
    if len(heslo) < 4:
        raise StrojChyba("Heslo má mít aspoň 4 znaky.")
    _skupina()
    existuje = subprocess.run(["id", ucet], capture_output=True).returncode == 0
    if not existuje:
        _beh(["useradd", "-M", "-s", "/usr/sbin/nologin", "-G", SKUPINA, ucet])
    else:
        _beh(["usermod", "-a", "-G", SKUPINA, ucet])
    _beh(["chpasswd"], vstup=f"{ucet}:{heslo}\n")
    _beh(["smbpasswd", "-a", "-s", ucet], vstup=f"{heslo}\n{heslo}\n")
    _beh(["smbpasswd", "-e", ucet])
    _obnov_ftp()


def nastav_aktivni(ucet, aktivni):
    if subprocess.run(["id", ucet], capture_output=True).returncode != 0:
        return
    if aktivni:
        _beh(["usermod", "-U", ucet])
        _beh(["smbpasswd", "-e", ucet])
    else:
        _beh(["usermod", "-L", ucet])
        _beh(["smbpasswd", "-d", ucet])
    _obnov_ftp()


def smaz_ucet(ucet):
    ucet = str(ucet or "").strip().lower()
    if ucet in ZAKAZANE or not JMENO_UCTU.fullmatch(ucet):
        raise StrojChyba("Tento účet nejde odebrat.")
    data = _nacti_slozky()
    meneno = False
    for zaznam in data.values():
        prava = zaznam.setdefault("prava", {})
        if ucet in prava:
            prava.pop(ucet, None)
            meneno = True
    if meneno:
        _uloz_slozky(data)
    subprocess.run(["smbpasswd", "-x", ucet], capture_output=True)
    if subprocess.run(["id", ucet], capture_output=True).returncode == 0:
        try:
            _beh(["userdel", ucet])
        except StrojChyba as chyba:
            raise StrojChyba("Účet se nepodařilo odebrat.") from chyba
    if meneno:
        _samba()
    else:
        _obnov_ftp()



def _jen_cteni_svazku():
    return False


def _zapis_jen_cteni(klic):
    return False


def _jednotka_bezi(jednotka):
    return subprocess.run(["systemctl", "is-active", "--quiet", jednotka]).returncode == 0


def _jednotka_zapnuta(jednotka):
    return subprocess.run(["systemctl", "is-enabled", "--quiet", jednotka]).returncode == 0


def _stav_sluzby(zapnuto, bezi):
    if bezi:
        return "běží"
    if zapnuto:
        return "zapnutá, ale neběží"
    return "vypnutá"


def _aktivni_ucty():
    soubor = DATA / "uzivatele.json"
    if not soubor.is_file():
        return []
    try:
        data = json.loads(soubor.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    ucty = []
    for jmeno, zaznam in data.items():
        if not isinstance(zaznam, dict) or not zaznam.get("aktivni"):
            continue
        if jmeno in ZAKAZANE or not JMENO_UCTU.fullmatch(jmeno):
            continue
        if subprocess.run(["id", jmeno], capture_output=True).returncode != 0:
            continue
        ucty.append(jmeno)
    return ucty


def _balicek(jmeno):
    if subprocess.run(["dpkg", "-s", jmeno], capture_output=True).returncode == 0:
        return
    tiche = {"DEBIAN_FRONTEND": "noninteractive"}
    _beh(["apt-get", "update"], cas=180, prostredi=tiche)
    _beh(["apt-get", "install", "-y", jmeno], cas=300, prostredi=tiche)



def _prepni_jednotku(jednotka, zapnuto, hlaseni):
    try:
        if zapnuto:
            _beh(["systemctl", "enable", "--now", jednotka])
        else:
            _beh(["systemctl", "disable", "--now", jednotka])
    except StrojChyba as chyba:
        raise StrojChyba(hlaseni) from chyba
    if zapnuto and not _jednotka_bezi(jednotka):
        raise StrojChyba(hlaseni)


def sluzby():
    ssh_zap = _jednotka_zapnuta("ssh")
    ftp_zap = _jednotka_zapnuta("vsftpd")
    return {"polozky": [
        {
            "id": "ssh",
            "nazev": "SSH",
            "port": 22,
            "zapnuto": ssh_zap,
            "stav": _stav_sluzby(ssh_zap, _jednotka_bezi("ssh")),
            "poznamka": "Když SSH vypneš, z jiného počítače se do PI4 nepřihlásíš, dokud ho zase nezapneš přímo u PI4.",
        },
        {
            "id": "ftp",
            "nazev": "FTP",
            "port": 21,
            "zapnuto": ftp_zap,
            "stav": _stav_sluzby(ftp_zap, _jednotka_bezi("vsftpd")),
            "poznamka": "Přihlášení stejnými účty jako do PISM. Vidíš jen sdílené složky, ke kterým máš právo. Bez hesla se nikdo nedostane.",
        },
    ]}


def nastav_sluzbu(kod, zapnuto):
    kod = str(kod or "").strip()
    if not isinstance(zapnuto, bool):
        raise StrojChyba("Vyber zapnout, nebo vypnout.")
    if kod == "ssh":
        _prepni_jednotku("ssh", zapnuto, "SSH se nepodařilo přepnout.")
    elif kod == "ftp":
        if zapnuto:
            _priprav_ftp()
        _prepni_jednotku("vsftpd", zapnuto, "FTP se nepodařilo přepnout.")
    else:
        raise StrojChyba("Taková služba není.")
    return sluzby()


def _text_release(klic):
    try:
        radky = Path("/etc/os-release").read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for radek in radky:
        if radek.startswith(klic + "="):
            return radek.split("=", 1)[1].strip().strip('"')
    return ""


def _jadro():
    try:
        druh = Path("/proc/sys/kernel/ostype").read_text(encoding="ascii").strip()
        verze = Path("/proc/sys/kernel/osrelease").read_text(encoding="ascii").strip()
    except OSError:
        return ""
    return f"{druh} {verze}".strip()


def system():
    with open("/proc/uptime", encoding="ascii") as handle:
        sekundy = int(float(handle.read().split()[0]))
    hodiny, zbytek = divmod(sekundy, 3600)
    minuty = zbytek // 60
    with open("/proc/meminfo", encoding="ascii") as handle:
        info = {}
        for radek in handle:
            klic, hodnota = radek.split(":", 1)
            info[klic] = int(hodnota.strip().split()[0]) * 1024
    model = Path("/proc/device-tree/model").read_bytes().split(b"\0", 1)[0].decode()
    teplota = int(Path("/sys/class/thermal/thermal_zone0/temp").read_text(encoding="ascii")) / 1000
    cas = _beh(["date", "+%d.%m.%Y %H:%M"]).stdout.strip()
    return {
        "jmeno": Path("/etc/hostname").read_text(encoding="utf-8").strip(),
        "verze": VERZE,
        "model": model,
        "cas": cas,
        "beh": f"{hodiny} h {minuty} min",
        "teplota": f"{teplota:.1f} °C",
        "pamet": _obsazeni_pomer(info.get("MemTotal", 0) - info.get("MemAvailable", 0), info.get("MemTotal", 0)),
        "system": _text_release("PRETTY_NAME"),
        "jadro": _jadro(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def _napajeni(prikaz):
    if prikaz not in {"reboot", "poweroff"}:
        raise StrojChyba("Tohle nejde.")
    _beh(["systemd-run", "--on-active=2s", "--collect", "systemctl", prikaz], cas=20)


_rychlost_zamek = threading.Lock()
_rychlost_minule = {"zarizeni": "", "cas": 0.0, "prijem": 0, "odeslani": 0}


def _text_rychlosti(bajty):
    if bajty < 4 * 1024:
        return "0"
    if bajty < 1024 * 1024:
        return f"{max(1, int(bajty / 1024))} KB/s"
    return f"{bajty / (1024 * 1024):.1f} MB/s"


def _zarizeni_prenosa():
    try:
        if Path("/sys/class/net/eth0/carrier").read_text(encoding="ascii").strip() == "1":
            return "eth0"
    except OSError:
        pass
    try:
        if Path("/sys/class/net/wlan0/operstate").read_text(encoding="ascii").strip() == "up":
            return "wlan0"
    except OSError:
        pass
    return ""


def rychlost_site():
    zarizeni = _zarizeni_prenosa()
    if zarizeni not in {"eth0", "wlan0"}:
        return {"cteni": "0", "zapis": "0", "teplota": _teplota_cpu()}
    try:
        prijem = int(Path(f"/sys/class/net/{zarizeni}/statistics/rx_bytes").read_text(encoding="ascii"))
        odeslani = int(Path(f"/sys/class/net/{zarizeni}/statistics/tx_bytes").read_text(encoding="ascii"))
    except (OSError, ValueError):
        return {"cteni": "0", "zapis": "0", "teplota": _teplota_cpu()}
    ted = time.monotonic()
    with _rychlost_zamek:
        minule = _rychlost_minule
        stejny = minule["zarizeni"] == zarizeni and minule["cas"] > 0
        dt = ted - minule["cas"] if stejny else 0
        stary_prijem = minule["prijem"]
        stare_odeslani = minule["odeslani"]
        minule["zarizeni"] = zarizeni
        minule["cas"] = ted
        minule["prijem"] = prijem
        minule["odeslani"] = odeslani
        if (
            not stejny
            or dt < 0.3
            or dt > 5
            or prijem < stary_prijem
            or odeslani < stare_odeslani
        ):
            return {"cteni": "0", "zapis": "0", "teplota": _teplota_cpu()}
        cteni = (odeslani - stare_odeslani) / dt
        zapis = (prijem - stary_prijem) / dt
    return {"cteni": _text_rychlosti(cteni), "zapis": _text_rychlosti(zapis), "teplota": _teplota_cpu()}


def _teplota_cpu():
    try:
        hodnota = int(Path("/sys/class/thermal/thermal_zone0/temp").read_text(encoding="ascii")) / 1000
    except (OSError, ValueError):
        return ""
    return f"{hodnota:.1f} °C"


def prehled():
    sit_data = sit()
    lan = sit_data.get("lan") or {}
    wifi = sit_data.get("wifi") or {}
    if sit_data.get("kabel"):
        spojeni = "kabel"
        adresa = lan.get("adresa") or ""
    elif wifi.get("adresa"):
        spojeni = "Wi-Fi"
        adresa = wifi.get("adresa") or ""
    else:
        spojeni = "není připojeno"
        adresa = ""
    with open("/proc/uptime", encoding="ascii") as handle:
        sekundy = int(float(handle.read().split()[0]))
    hodiny, zbytek = divmod(sekundy, 3600)
    minuty = zbytek // 60
    radky_disku = disky().get("disky") or []
    karta = next((polozka for polozka in radky_disku if polozka.get("systemovy")), None)
    datove = [polozka for polozka in radky_disku if not polozka.get("systemovy")]
    if not datove:
        datove_vystup = [{"nazev": "Datový disk", "volno": "", "smart": "", "poznamka": "ještě není"}]
    else:
        datove_vystup = []
        for disk in datove:
            nazev = disk.get("model") if len(datove) > 1 and disk.get("model") else (disk.get("nazev") or "Disk")
            poznamka = disk.get("poznamka") or ""
            if disk.get("zrcadlo") and disk.get("stav_text"):
                poznamka = (disk["stav_text"] + (" " + poznamka if poznamka else "")).strip()
            smart_text = ""
            if disk.get("zrcadlo"):
                casti_smart = []
                for clen in disk.get("cleny_disky") or []:
                    model = clen.get("model") or "Neznámý disk"
                    kratce = _kratky_smart(clen.get("klic") or "")
                    if kratce == "nejde přečíst":
                        casti_smart.append(f"SMART {model} nejde přečíst")
                    else:
                        casti_smart.append(f"SMART {model} {kratce}")
                smart_text = " · ".join(casti_smart)
            elif not disk.get("klic") or disk.get("klic") == "hlavni":
                smart_text = _kratky_smart("")
            datove_vystup.append({
                "nazev": nazev,
                "volno": disk.get("volno") or "",
                "smart": smart_text,
                "smart_cele": bool(disk.get("zrcadlo")),
                "poznamka": poznamka,
            })
    rychlost = rychlost_site()
    return {
        "jmeno": sit_data.get("jmeno") or "",
        "adresa": adresa,
        "spojeni": spojeni,
        "cteni": rychlost["cteni"],
        "zapis": rychlost["zapis"],
        "beh": f"{hodiny} h {minuty} min",
        "teplota": _teplota_cpu(),
        "karta": (karta or {}).get("volno") or "",
        "disky": datove_vystup,
    }


def restartovat():
    _napajeni("reboot")
    return {}


def vypnout():
    _napajeni("poweroff")
    return {}


def _obsazeni_pomer(obsazeno, celkem):
    if not celkem:
        return ""
    return f"{_lidske(obsazeno)} z {_lidske(celkem)}"


import sdileni as _sdileni

_nacti_slozky = _sdileni._nacti_slozky
_uloz_slozky = _sdileni._uloz_slozky
_klic_slozky = _sdileni._klic_slozky
_koren_slozek = _sdileni._koren_slozek
_cesta_slozky = _sdileni._cesta_slozky
_pravo_kanalu = _sdileni._pravo_kanalu
_ucty_kanalu = _sdileni._ucty_kanalu
_samba = _sdileni._samba
slozky = _sdileni.slozky
zaloz_slozku = _sdileni.zaloz_slozku
nastav_pravo = _sdileni.nastav_pravo
nastav_prava = _sdileni.nastav_prava
smaz_slozku = _sdileni.smaz_slozku
_odpoj_ftp = _sdileni._odpoj_ftp
_obnov_ftp = _sdileni._obnov_ftp
_priprav_ftp = _sdileni._priprav_ftp

from sit import (
    nastav_adresu,
    nastav_jmeno,
    nastav_obecne,
    sit,
    srovnej_sit,
    wifi_pripoj,
    wifi_site,
)
