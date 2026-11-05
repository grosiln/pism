# -*- coding: utf-8 -*-
"""PISM: sdílené složky, Samba a přístup přes FTP."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import stroj

FTP_KOREN = stroj.MISTO / "ftp"
FTP_UZIVATELE = Path("/etc/vsftpd/users")
FTP_SEZNAM = Path("/etc/vsftpd.userlist")
FTP_CONF = """# pism
listen=YES
listen_ipv6=NO
background=NO
anonymous_enable=NO
anon_upload_enable=NO
anon_mkdir_write_enable=NO
local_enable=YES
write_enable=YES
local_umask=022
use_localtime=YES
connect_from_port_20=YES
chroot_local_user=YES
allow_writeable_chroot=NO
secure_chroot_dir=/var/run/vsftpd/empty
pam_service_name=vsftpd
check_shell=NO
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO
user_config_dir=/etc/vsftpd/users
pasv_min_port=30000
pasv_max_port=30100
seccomp_sandbox=NO
"""
FTP_PAM = """# pism
auth required pam_listfile.so item=user sense=deny file=/etc/ftpusers onerr=succeed
@include common-auth
@include common-account
@include common-session
"""


def _nacti_slozky():
    if not stroj.SOUBOR_SLOZEK.exists():
        return {}
    return json.loads(stroj.SOUBOR_SLOZEK.read_text(encoding="utf-8"))


def _uloz_slozky(data):
    stroj.DATA.mkdir(exist_ok=True)
    stroj.SOUBOR_SLOZEK.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _klic_slozky(zaznam):
    if not isinstance(zaznam, dict):
        return "hlavni"
    klic = str(zaznam.get("disk") or "hlavni")
    return klic or "hlavni"


def _koren_slozek(klic):
    if klic == "hlavni":
        return stroj.SLOZKY_DIR
    for misto in stroj.mista_pro_slozky():
        if misto["klic"] == klic:
            return Path(misto["misto"]) / "slozky"
    raise stroj.StrojChyba("Disk není.")


def _cesta_slozky(nazev, klic=None):
    nazev = str(nazev or "")
    if not stroj.JMENO_SLOZKY.fullmatch(nazev):
        raise stroj.StrojChyba("Složka nejde poznat.")
    if klic is None:
        zaznam = _nacti_slozky().get(nazev)
        if not isinstance(zaznam, dict):
            raise stroj.StrojChyba("Složka není.")
        klic = _klic_slozky(zaznam)
    koren = _koren_slozek(klic)
    cesta = (koren / nazev).resolve()
    if cesta.parent != koren.resolve():
        raise stroj.StrojChyba("Složka nejde poznat.")
    return cesta


def _pravo_kanalu(prava, ucet, kanal):
    hodnota = (prava or {}).get(ucet)
    if isinstance(hodnota, str):
        return hodnota if hodnota in {"cteni", "zapis"} else ""
    if isinstance(hodnota, dict):
        pravo = str(hodnota.get(kanal) or "")
        return pravo if pravo in {"cteni", "zapis"} else ""
    return ""


def _ucty_kanalu(prava, kanal):
    cteni = []
    zapis = []
    for ucet in prava or {}:
        pravo = _pravo_kanalu(prava, ucet, kanal)
        if pravo in {"cteni", "zapis"}:
            cteni.append(ucet)
        if pravo == "zapis":
            zapis.append(ucet)
    return cteni, zapis


def _samba():
    stroj._skupina()
    slozky = _nacti_slozky()
    radky = ["# pism"]
    for nazev, zaznam in slozky.items():
        prava = zaznam.get("prava") or {}
        cteni, zapis = _ucty_kanalu(prava, "slozka")
        if not cteni:
            continue
        try:
            cesta = _cesta_slozky(nazev)
        except stroj.StrojChyba:
            continue
        jen_cteni = stroj._zapis_jen_cteni(_klic_slozky(zaznam))
        radky.extend([
            f"[{nazev}]",
            f"path = {cesta}",
            "browseable = yes",
            "read only = yes",
            "guest ok = no",
            f"valid users = {' '.join(cteni)}",
            *([] if jen_cteni or not zapis else [f"write list = {' '.join(zapis)}"]),
            "force user = root",
            f"force group = {stroj.SKUPINA}",
            "create mask = 0664",
            "directory mask = 0775",
            "",
        ])
    stroj.SMB.parent.mkdir(parents=True, exist_ok=True)
    stroj.SMB.write_text("\n".join(radky) + "\n", encoding="utf-8")
    if stroj.SMB_HLAVNI.exists():
        text = stroj.SMB_HLAVNI.read_text(encoding="utf-8")
        include = "include = /etc/samba/pism.conf"
        if include not in text:
            stroj.SMB_HLAVNI.write_text(text.rstrip() + "\n" + include + "\n", encoding="utf-8")
    subprocess.run(["systemctl", "disable", "--now", "samba-ad-dc"], capture_output=True)
    stroj._beh(["systemctl", "enable", "--now", "smbd"])
    stroj._beh(["systemctl", "restart", "smbd"])
    subprocess.run(["systemctl", "restart", "nmbd"], capture_output=True)
    _obnov_ftp()


def slozky():
    mista = stroj.mista_pro_slozky()
    return {
        "slozky": _nacti_slozky(),
        "svazek": bool(mista),
        "disky": [
            {
                "klic": misto["klic"],
                "model": misto["model"],
                "velikost": misto["velikost"],
                "cleny": misto.get("cleny") or [],
            }
            for misto in mista
        ],
    }


def zaloz_slozku(nazev, disk=""):
    nazev = str(nazev or "").strip().lower()
    if not stroj.JMENO_SLOZKY.fullmatch(nazev):
        raise stroj.StrojChyba("Jméno složky má být z malých písmen a číslic.")
    mista = stroj.mista_pro_slozky()
    if not mista:
        raise stroj.StrojChyba("Nejdřív přidej datový disk.")
    if disk:
        klic = str(disk)
    elif len(mista) == 1:
        klic = mista[0]["klic"]
    else:
        raise stroj.StrojChyba("Vyber, kam složka půjde.")
    if not any(misto["klic"] == klic for misto in mista):
        raise stroj.StrojChyba("Vyber, kam složka půjde.")
    if stroj._zapis_jen_cteni(klic):
        raise stroj.StrojChyba("Bez licence jde z tohohle disku jen číst.")
    data = _nacti_slozky()
    if nazev in data:
        raise stroj.StrojChyba("Taková složka už je.")
    cesta = _cesta_slozky(nazev, klic)
    try:
        cesta.mkdir(parents=True, exist_ok=False)
    except FileExistsError as chyba:
        raise stroj.StrojChyba("Taková složka už je.") from chyba
    stroj._vlastnik(cesta)
    data[nazev] = {"prava": {}, "disk": klic}
    _uloz_slozky(data)
    _samba()
    return slozky()


def _over_pravo(ucet, pravo):
    ucet = str(ucet or "").strip().lower()
    pravo = str(pravo or "")
    if pravo not in {"nic", "cteni", "zapis"}:
        raise stroj.StrojChyba("Vyber nemá přístup, pouze čtení, nebo plný přístup.")
    if not stroj.JMENO_UCTU.fullmatch(ucet):
        raise stroj.StrojChyba("Účet nejde poznat.")
    return ucet, pravo


def nastav_pravo(nazev, ucet, pravo):
    ucet, pravo = _over_pravo(ucet, pravo)
    nazev = str(nazev or "")
    _cesta_slozky(nazev)
    data = _nacti_slozky()
    if nazev not in data:
        raise stroj.StrojChyba("Složka není.")
    if pravo == "nic":
        data[nazev]["prava"].pop(ucet, None)
    else:
        data[nazev]["prava"][ucet] = {"slozka": pravo, "ftp": pravo}
    _uloz_slozky(data)
    _samba()
    return slozky()


def _hodnota_prava(pravo):
    pravo = str(pravo or "nic")
    if pravo not in {"nic", "cteni", "zapis"}:
        raise stroj.StrojChyba("Vyber nemá přístup, pouze čtení, nebo plný přístup.")
    return pravo


def nastav_prava(nazev, prava):
    nazev = str(nazev or "")
    _cesta_slozky(nazev)
    if not isinstance(prava, dict):
        raise stroj.StrojChyba("Vyber přístup u účtů.")
    data = _nacti_slozky()
    if nazev not in data:
        raise stroj.StrojChyba("Složka není.")
    cil = {}
    for ucet, pravo in prava.items():
        ucet = str(ucet or "").strip().lower()
        if not stroj.JMENO_UCTU.fullmatch(ucet):
            raise stroj.StrojChyba("Účet nejde poznat.")
        if isinstance(pravo, dict):
            slozka = _hodnota_prava(pravo.get("slozka", "nic"))
            ftp = _hodnota_prava(pravo.get("ftp", "nic"))
        else:
            spolecne = _hodnota_prava(pravo)
            slozka = ftp = spolecne
        zaznam = {}
        if slozka != "nic":
            zaznam["slozka"] = slozka
        if ftp != "nic":
            zaznam["ftp"] = ftp
        if zaznam:
            cil[ucet] = zaznam
    data[nazev]["prava"] = cil
    _uloz_slozky(data)
    _samba()
    return slozky()


def smaz_slozku(nazev):
    data = _nacti_slozky()
    if nazev not in data:
        raise stroj.StrojChyba("Složka není.")
    if stroj._zapis_jen_cteni(_klic_slozky(data[nazev])):
        raise stroj.StrojChyba("Bez licence jde z tohohle disku jen číst.")
    cesta = _cesta_slozky(nazev)
    _odpoj_ftp()
    if cesta.is_dir():
        shutil.rmtree(cesta)
    data.pop(nazev, None)
    _uloz_slozky(data)
    _samba()
    return slozky()


def _odpoj_ftp():
    try:
        text = Path("/proc/mounts").read_text(encoding="utf-8")
    except OSError:
        return
    koren = str(FTP_KOREN)
    cile = []
    for line in text.splitlines():
        casti = line.split()
        if len(casti) < 2:
            continue
        cil = casti[1].replace("\\040", " ")
        if cil == koren or cil.startswith(koren + "/"):
            cile.append(cil)
    for cil in sorted(cile, key=len, reverse=True):
        vysledek = subprocess.run(["umount", cil], capture_output=True)
        if vysledek.returncode != 0:
            raise stroj.StrojChyba("Složku pro FTP se nepodařilo odpojit.")


def _zapis_ftp_fstab(radky):
    puvod = stroj.FSTAB.read_text(encoding="utf-8").splitlines() if stroj.FSTAB.exists() else []
    zustane = [line for line in puvod if "# pism-ftp" not in line]
    stroj.FSTAB.write_text("\n".join(zustane + radky).rstrip() + "\n", encoding="utf-8")


def _ftp_pripraveno():
    soubor = Path("/etc/vsftpd.conf")
    try:
        return "# pism" in soubor.read_text(encoding="utf-8")
    except OSError:
        return False


def _obnov_ftp():
    if not _ftp_pripraveno() or not stroj.MISTO.is_mount():
        return
    _odpoj_ftp()
    if FTP_KOREN.exists():
        shutil.rmtree(FTP_KOREN)
    FTP_KOREN.mkdir(parents=True)
    os.chmod(FTP_KOREN, 0o755)
    FTP_UZIVATELE.mkdir(parents=True, exist_ok=True)
    for soubor in FTP_UZIVATELE.iterdir():
        if soubor.is_file():
            soubor.unlink()
    radky = []
    seznam = []
    slozky = _nacti_slozky()
    for ucet in stroj._aktivni_ucty():
        pristupy = []
        for nazev, zaznam in slozky.items():
            pravo = _pravo_kanalu(zaznam.get("prava") or {}, ucet, "ftp")
            if pravo in {"cteni", "zapis"}:
                pristupy.append((nazev, pravo))
        if not pristupy:
            continue
        domov = FTP_KOREN / ucet
        domov.mkdir()
        os.chown(domov, 0, 0)
        os.chmod(domov, 0o755)
        stroj._beh(["usermod", "-d", str(domov), ucet])
        for nazev, pravo in pristupy:
            try:
                zdroj = _cesta_slozky(nazev)
            except stroj.StrojChyba:
                continue
            if not zdroj.is_dir():
                continue
            cil = domov / nazev
            cil.mkdir()
            stroj._beh(["mount", "--bind", str(zdroj), str(cil)])
            volby = "bind"
            if pravo == "cteni" or stroj._zapis_jen_cteni(_klic_slozky(slozky.get(nazev))):
                stroj._beh(["mount", "-o", "remount,bind,ro", str(cil)])
                volby = "bind,ro"
            radky.append(f"{zdroj} {cil} none {volby} 0 0 # pism-ftp")
        (FTP_UZIVATELE / ucet).write_text(f"local_root={domov}\n", encoding="utf-8")
        seznam.append(ucet)
    _zapis_ftp_fstab(radky)
    FTP_SEZNAM.write_text(("\n".join(seznam) + "\n") if seznam else "", encoding="utf-8")
    os.chmod(FTP_SEZNAM, 0o644)
    if stroj._jednotka_bezi("vsftpd"):
        try:
            stroj._beh(["systemctl", "restart", "vsftpd"])
        except stroj.StrojChyba as chyba:
            raise stroj.StrojChyba("FTP se nepodařilo znovu spustit.") from chyba


def _priprav_ftp():
    if not stroj.MISTO.is_mount():
        raise stroj.StrojChyba("Nejdřív vytvoř svazek na datovém disku.")
    stroj._balicek("vsftpd")
    Path("/var/run/vsftpd/empty").mkdir(parents=True, exist_ok=True)
    os.chmod(Path("/var/run/vsftpd/empty"), 0o755)
    Path("/etc/vsftpd.conf").write_text(FTP_CONF, encoding="utf-8")
    Path("/etc/pam.d/vsftpd").write_text(FTP_PAM, encoding="utf-8")
    drop = Path("/etc/systemd/system/vsftpd.service.d")
    drop.mkdir(parents=True, exist_ok=True)
    (drop / "pism.conf").write_text("[Service]\nProtectSystem=no\nProtectHome=no\n", encoding="utf-8")
    stroj._beh(["systemctl", "daemon-reload"])
    _obnov_ftp()
