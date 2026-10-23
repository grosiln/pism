# -*- coding: utf-8 -*-
"""PISM: software RAID. Zrcadlo se založí až po potvrzení."""

import re
import shutil
import subprocess
import time
from pathlib import Path

import stroj

RAID_MISTO = Path("/srv/pism-zrcadlo")
MDADM = Path("/etc/mdadm/mdadm.conf")


def varovani():
    return {
        "uvod": "Toto je software RAID. Disky nespojuje samostatný řadič, spojuje je PI4.",
        "upozorneni": "Přes USB to nese tyhle problémy:",
        "problemy": [
            "Oba rychlé porty jedou po jedné společné cestě. Dva disky nepojedou každý plnou rychlostí.",
            "PI4 z portu neutáhne dva běžící disky. Když dojde proud, disk na chvíli zmizí a pole se rozpadne.",
            "Kabel, konektor nebo krabička, která odpadne, vyřadí celý disk. U zrcadla zůstane jedna kopie a pole je oslabené. Kde kopie není, spadnou všechna data.",
            "Skládání pole po výpadku trvá dlouho. Když během něj odpadne další disk, data jsou pryč.",
            "RAID není záloha. Smazaný soubor nebo chybný zápis je na discích v poli.",
            "Tohle je beta. Na pole nepatří jediná kopie dat.",
        ],
        "beru": "Přečetl jsem a beru na vědomí vše v textu zmíněné",
        "konfigurace_nadpis": "Konfigurace soft RAID",
        "konfigurace": "Vyberou se dva disky se stejnou kapacitou. Pole se založí až po potvrzení.",
    }


def _pole_bezi():
    try:
        text = Path("/proc/mdstat").read_text(encoding="utf-8")
    except OSError:
        return False
    return any(radek.startswith("md") and "active" in radek for radek in text.splitlines())


def _v_poli(disk):
    for dite in stroj._potomci(disk):
        if str(dite.get("type") or "").startswith("raid"):
            return True
        if (dite.get("fstype") or "") == "linux_raid_member":
            return True
    return False


def _stejna_kapacita(prvni, druhy):
    vetsi = max(prvni, druhy)
    if vetsi <= 0:
        return False
    return abs(prvni - druhy) / vetsi <= 0.02


def _oznac_klice(disky):
    skupiny = []
    for disk in sorted(disky, key=lambda polozka: polozka["bajty"]):
        for skupina in skupiny:
            if _stejna_kapacita(skupina[0]["bajty"], disk["bajty"]):
                skupina.append(disk)
                break
        else:
            skupiny.append([disk])
    for poradi, skupina in enumerate(skupiny, start=1):
        klic = str(poradi) if len(skupina) >= 2 else ""
        for disk in skupina:
            disk["klic"] = klic


def _rozdeleni():
    volne = []
    v_poli = 0
    for disk in stroj._blokova():
        if disk.get("type") != "disk":
            continue
        jmeno = str(disk.get("name") or "")
        if not re.fullmatch(r"sd[a-z]+", jmeno):
            continue
        if disk.get("tran") != "usb" or stroj._je_system(disk):
            continue
        if _v_poli(disk):
            v_poli += 1
            continue
        try:
            bajty = int(disk.get("size") or 0)
        except (TypeError, ValueError):
            bajty = 0
        if bajty <= 0:
            continue
        volne.append({
            "jmeno": jmeno,
            "model": (disk.get("model") or "").replace("_", " ").strip() or "Neznámý disk",
            "velikost": stroj._lidske(bajty),
            "bajty": bajty,
            "sdileni": stroj.disk_ma_sdileni(disk),
            "klic": "",
        })
    _oznac_klice(volne)
    return volne, v_poli


def _vety(disky):
    if not disky:
        return ["Není disk k dispozici. Pro zrcadlo jsou potřeba dva disky se stejnou kapacitou."]
    if not any(disk["klic"] for disk in disky):
        if len(disky) == 1 and disky[0]["sdileni"]:
            return [
                "Tenhle disk už má sdílení. Pro zrcadlo k němu připoj druhý disk se stejnou kapacitou. Sdílení a práva k jeho složkám se před založením zruší. Účty zůstanou.",
                "Nebo připoj dva jiné disky se stejnou kapacitou a tohle sdílení nech být.",
            ]
        if len(disky) == 1:
            return ["Pro zrcadlo jsou potřeba dva disky se stejnou kapacitou. Připoj ještě jeden se stejnou kapacitou."]
        return ["Připojené disky nemají stejnou kapacitu. Pro zrcadlo jsou potřeba dva se stejnou."]
    pary = [disk for disk in disky if disk["klic"]]
    vety = ["Ukazují se jen disky, které mají pár. Vyber dva se stejnou kapacitou. Výrobce může být jiný. Systémová karta se nepoužije."]
    if any(disk["sdileni"] for disk in pary):
        vety.append("Když do výběru dáš disk se sdílením, složky a práva uživatelů k nim se nejdřív zruší. Účty zůstanou. Teprve potom se oba disky smažou a založí se zrcadlo.")
        vety.append("Když disk se sdílením nevybereš, sdílení zůstane a zrcadlo bude vedle něj.")
    else:
        vety.append("Data na vybraných discích se smažou a založí se z nich zrcadlo.")
    return vety


def konfigurace():
    if _pole_bezi():
        return {
            "lze": False,
            "disky": [],
            "slozky": [],
            "vety": ["Zrcadlo už je založené. Další se teď nezaloží."],
        }
    disky, v_poli = _rozdeleni()
    if not disky and v_poli:
        return {
            "lze": False,
            "disky": [],
            "slozky": [],
            "vety": ["Tyto disky už jsou v zrcadle."],
        }
    pary = [disk for disk in disky if disk["klic"]]
    verejne = [
        {klic: disk[klic] for klic in ("jmeno", "model", "velikost", "klic", "sdileni")}
        for disk in pary
    ]
    klice = {stroj._klic_podle_jmena(disk["jmeno"]) for disk in pary if disk["sdileni"]}
    klice.discard("")
    slozky = sorted(
        nazev for nazev, zaznam in stroj._nacti_slozky().items()
        if stroj._klic_slozky(zaznam) in klice
    )
    return {
        "lze": bool(pary),
        "disky": verejne,
        "slozky": slozky,
        "vety": _vety(disky),
    }


def _obnov_sdileni(puvod):
    stroj._uloz_slozky(puvod)
    try:
        stroj._samba()
    except stroj.StrojChyba:
        pass


def _zdroj_pripojeni(misto):
    try:
        text = Path("/proc/mounts").read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        casti = line.split()
        if len(casti) >= 2 and casti[1].replace("\\040", " ") == str(misto):
            return casti[0]
    return ""


def _zrus_sdileni(jmena):
    puvod = stroj._nacti_slozky()
    fstab = stroj.FSTAB.read_text(encoding="utf-8") if stroj.FSTAB.exists() else ""
    vybrane = [disk for disk in stroj._seznam_datovych() if disk["jmeno"] in set(jmena)]
    cile = [disk["misto"] for disk in vybrane]
    klice = {disk["klic"] for disk in vybrane}
    if not klice:
        return None

    def vrat():
        stroj.FSTAB.write_text(fstab, encoding="utf-8")
        for cil in cile:
            if Path(cil).is_mount():
                continue
            try:
                Path(cil).mkdir(parents=True, exist_ok=True)
                stroj._beh(["mount", cil])
            except stroj.StrojChyba:
                return
        _obnov_sdileni(puvod)

    try:
        stroj._odpoj_ftp()
        nech = {
            nazev: zaznam for nazev, zaznam in puvod.items()
            if stroj._klic_slozky(zaznam) not in klice
        }
        stroj._uloz_slozky(nech)
        for cil in cile:
            if Path(cil).is_mount():
                stroj._beh(["umount", cil])
        stroj._odeber_mista_z_fstab(cile)
        stroj._samba()
    except Exception as chyba:
        vrat()
        raise stroj.StrojChyba("Sdílení se nepodařilo zrušit. Pole se nezaložilo.") from chyba
    return vrat


def _blok(jmeno):
    for disk in stroj._blokova():
        if disk.get("type") == "disk" and disk.get("name") == jmeno:
            return disk
    raise stroj.StrojChyba("Disk už není připojený.")


def _over_k_smazani(disk):
    jmeno = str(disk.get("name") or "")
    if not re.fullmatch(r"sd[a-z]+", jmeno):
        raise stroj.StrojChyba("Disk nejde poznat.")
    if disk.get("tran") != "usb" or stroj._je_system(disk) or jmeno.startswith("mmc"):
        raise stroj.StrojChyba("Systémová karta se nemaže.")
    cesta = stroj._cesta_disku(jmeno)
    if not re.fullmatch(r"/dev/sd[a-z]+", str(cesta)):
        raise stroj.StrojChyba("Disk nejde poznat.")
    return cesta


def _priprav_smazani(jmena):
    bloky = [_blok(jmeno) for jmeno in jmena]
    cesty = [_over_k_smazani(disk) for disk in bloky]
    for disk in bloky:
        for dite in stroj._potomci(disk):
            if dite is disk:
                continue
            stroj._odpoj(dite.get("mountpoint"))
    return bloky, cesty


def _smaz_dvojici(bloky, cesty):
    for disk, cesta in zip(bloky, cesty):
        for dite in stroj._potomci(disk):
            if dite.get("type") != "part":
                continue
            oddil = stroj._cesta_disku(str(dite.get("name") or ""))
            if oddil.exists():
                stroj._beh(["wipefs", "-a", str(oddil)], cas=120)
        stroj._beh(["wipefs", "-a", str(cesta)], cas=120)
    return [str(cesta) for cesta in cesty]


def _zarizeni_pole():
    for _ in range(10):
        if Path("/dev/md/pism").exists():
            return "/dev/md/pism"
        try:
            for radek in Path("/proc/mdstat").read_text(encoding="utf-8").splitlines():
                if radek.startswith("md") and "active" in radek:
                    cesta = Path("/dev") / radek.split()[0]
                    if cesta.exists():
                        return str(cesta)
        except OSError:
            pass
        time.sleep(1)
    raise stroj.StrojChyba("Zrcadlo se neobjevilo.")


def _znacka(zarizeni):
    for _ in range(5):
        uuid = stroj._beh(["blkid", "-s", "UUID", "-o", "value", zarizeni]).stdout.strip()
        if uuid:
            return uuid
        time.sleep(1)
    raise stroj.StrojChyba("Nové zrcadlo nemá značku.")


def _fstab_zrcadlo(uuid):
    radek = f"UUID={uuid} {RAID_MISTO} ext4 defaults,noatime 0 2 # pism-zrcadlo"
    radky = stroj.FSTAB.read_text(encoding="utf-8").splitlines() if stroj.FSTAB.exists() else []
    radky = [line for line in radky if "pism-zrcadlo" not in line]
    radky.append(radek)
    stroj.FSTAB.write_text("\n".join(radky).rstrip() + "\n", encoding="utf-8")


def prehled_zrcadla():
    try:
        radky = Path("/proc/mdstat").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    aktivni = ""
    detail = ""
    for poradi, radek in enumerate(radky):
        if radek.startswith("md") and "active" in radek:
            aktivni = radek
            detail = radky[poradi + 1] if poradi + 1 < len(radky) else ""
            break
    if not aktivni:
        return None
    jmeno_pole = aktivni.split()[0]
    jmena = re.findall(r"([a-z][a-z0-9]*)\[\d+\]", aktivni)
    chybne = set(re.findall(r"([a-z][a-z0-9]*)\[\d+\]\(F\)", aktivni))
    shoda = re.search(r"\[(\d+)/(\d+)\]", detail)
    celkem = int(shoda.group(1)) if shoda else max(len(jmena), 1)
    jedou = int(shoda.group(2)) if shoda else len(jmena) - len(chybne)
    def rodic(jmeno):
        shoda = re.fullmatch(r"(sd[a-z]+)\d*", jmeno)
        return shoda.group(1) if shoda else jmeno

    modely = {}
    velikost = ""
    rodice = {rodic(jmeno) for jmeno in jmena}
    for disk in stroj._blokova():
        if disk.get("type") != "disk":
            continue
        jmeno = str(disk.get("name") or "")
        if jmeno in rodice:
            modely[jmeno] = (disk.get("model") or "").replace("_", " ").strip() or "Neznámý disk"
        for dite in stroj._potomci(disk):
            if dite.get("name") == jmeno_pole and not velikost:
                try:
                    velikost = stroj._lidske(int(dite.get("size") or 0))
                except (TypeError, ValueError):
                    velikost = ""
    cleny_disky = []
    videne = set()
    for jmeno in jmena:
        rodic_jmeno = rodic(jmeno)
        if rodic_jmeno in videne or rodic_jmeno not in modely:
            continue
        videne.add(rodic_jmeno)
        cleny_disky.append({
            "jmeno": rodic_jmeno,
            "model": modely[rodic_jmeno],
            "klic": "raid:" + rodic_jmeno,
        })
    cleny = [polozka["model"] for polozka in cleny_disky]
    chybi = max(celkem - jedou, len(chybne), 0)
    if jedou <= 0:
        stav_text = "Zrcadlo nejede."
    elif chybi:
        stav_text = "Oslabené. Chybí jeden disk." if chybi == 1 else "Oslabené. Chybí víc disků."
    elif celkem == 2 and jedou == 2:
        stav_text = "V pořádku, oba disky jedou."
    else:
        stav_text = "V pořádku."
    pripojeno = RAID_MISTO.is_mount()
    return {
        "nazev": "Zrcadlo",
        "klic": "zrcadlo",
        "zrcadlo": True,
        "systemovy": False,
        "svazek": pripojeno,
        "cleny": cleny,
        "cleny_disky": cleny_disky,
        "velikost": velikost,
        "volno": stroj._volno(RAID_MISTO) if pripojeno else "",
        "pripojeno": pripojeno,
        "stav_text": stav_text,
        "poznamka": "" if pripojeno else "Není připojené. Složka na něj zatím nejde.",
    }


def pripoj():
    if not _pole_bezi():
        raise stroj.StrojChyba("Zrcadlo není založené.")
    if RAID_MISTO.is_mount():
        return stroj.disky()
    zarizeni = _zarizeni_pole()
    uuid = _znacka(zarizeni)
    RAID_MISTO.mkdir(parents=True, exist_ok=True)
    stroj._beh(["mount", zarizeni, str(RAID_MISTO)])
    _fstab_zrcadlo(uuid)
    koren = RAID_MISTO / "slozky"
    koren.mkdir(parents=True, exist_ok=True)
    stroj._vlastnik(koren)
    return stroj.disky()


def _uloz_pole():
    text = stroj._beh(["mdadm", "--detail", "--scan"]).stdout.splitlines()
    nove = [radek for radek in text if radek.startswith("ARRAY") and "pism" in radek]
    if not nove:
        raise stroj.StrojChyba("Zrcadlo se nepodařilo zapsat pro příští start.")
    puvod = MDADM.read_text(encoding="utf-8").splitlines() if MDADM.exists() else []
    zustane = [radek for radek in puvod if not (radek.startswith("ARRAY") and "pism" in radek)]
    MDADM.parent.mkdir(parents=True, exist_ok=True)
    MDADM.write_text("\n".join(zustane + nove).rstrip() + "\n", encoding="utf-8")
    subprocess.run(["systemctl", "enable", "mdadm"], capture_output=True)


def _zaloz_pole(cesty):
    try:
        stroj._beh(
            [
                "mdadm", "--create", "/dev/md/pism", "--level=1", "--raid-devices=2",
                "--metadata=1.2", "--name=pism", "--homehost=any", "--run", "--force",
                *cesty,
            ],
            vstup="yes\n",
            cas=180,
        )
    except stroj.StrojChyba as chyba:
        raise stroj.StrojChyba("Zrcadlo se nepodařilo založit.") from chyba
    subprocess.run(["udevadm", "settle"], timeout=20, check=False)
    zarizeni = _zarizeni_pole()
    datovy = not stroj.MISTO.is_mount()
    stitek = "PISM" if datovy else "PISMRAID"
    cil = stroj.MISTO if datovy else RAID_MISTO
    try:
        stroj._beh(["mkfs.ext4", "-F", "-L", stitek, zarizeni], cas=300)
    except stroj.StrojChyba as chyba:
        raise stroj.StrojChyba("Zrcadlo se nepodařilo připravit.") from chyba
    subprocess.run(["udevadm", "settle"], timeout=20, check=False)
    uuid = _znacka(zarizeni)
    cil.mkdir(parents=True, exist_ok=True)
    try:
        stroj._beh(["mount", zarizeni, str(cil)])
    except stroj.StrojChyba as chyba:
        raise stroj.StrojChyba("Zrcadlo se nepodařilo připojit.") from chyba
    if datovy:
        stroj._fstab(uuid)
        stroj._skupina()
        stroj.SLOZKY_DIR.mkdir(parents=True, exist_ok=True)
        stroj._vlastnik(stroj.SLOZKY_DIR)
        stroj._samba()
    else:
        _fstab_zrcadlo(uuid)
        koren = RAID_MISTO / "slozky"
        koren.mkdir(parents=True, exist_ok=True)
        stroj._vlastnik(koren)
    _uloz_pole()


def zaloz(jmena):
    if _pole_bezi():
        raise stroj.StrojChyba("Zrcadlo už je založené.")
    if not isinstance(jmena, list) or len(jmena) != 2:
        raise stroj.StrojChyba("Vyber dva disky se stejnou kapacitou.")
    jmena = [str(jmeno or "") for jmeno in jmena]
    if len(set(jmena)) != 2:
        raise stroj.StrojChyba("Vyber dva disky se stejnou kapacitou.")
    disky, _ = _rozdeleni()
    podle_jmena = {disk["jmeno"]: disk for disk in disky}
    vybrane = []
    for jmeno in jmena:
        disk = podle_jmena.get(jmeno)
        if not disk or not disk["klic"]:
            raise stroj.StrojChyba("Tyhle disky pro zrcadlo nejdou použít.")
        vybrane.append(disk)
    if vybrane[0]["klic"] != vybrane[1]["klic"]:
        raise stroj.StrojChyba("Tyhle dva nemají stejnou kapacitu.")
    try:
        stroj._balicek("mdadm")
    except stroj.StrojChyba as chyba:
        raise stroj.StrojChyba("Zrcadlo na PI4 nejde založit.") from chyba
    if not shutil.which("mdadm"):
        raise stroj.StrojChyba("Zrcadlo na PI4 nejde založit.")
    vrat = _zrus_sdileni([disk["jmeno"] for disk in vybrane]) if any(disk["sdileni"] for disk in vybrane) else None
    if _pole_bezi():
        if vrat:
            vrat()
        raise stroj.StrojChyba("Zrcadlo už je založené.")
    try:
        bloky, cesty = _priprav_smazani([disk["jmeno"] for disk in vybrane])
    except stroj.StrojChyba as chyba:
        if vrat:
            vrat()
        text = str(chyba)
        if any(veta in text for veta in ("Systémová", "nejde poznat", "není připojený", "nečekaném", "nepodařilo odpojit")):
            raise
        raise stroj.StrojChyba("Disk se nepodařilo smazat. Zrcadlo se nezaložilo.") from chyba
    try:
        hotove = _smaz_dvojici(bloky, cesty)
    except stroj.StrojChyba as chyba:
        raise stroj.StrojChyba("Disk se nepodařilo smazat. Zrcadlo se nezaložilo.") from chyba
    _zaloz_pole(hotove)
    return stroj.disky()
