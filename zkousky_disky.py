# -*- coding: utf-8 -*-
"""Zkoušky rozpoznání disků. Na skutečný disk nesahá."""

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "pism"))

import napoveda
import raid
import stroj


def disk(jmeno, tran="", deti=None, velikost=1000):
    return {
        "name": jmeno,
        "type": "disk",
        "tran": tran,
        "size": velikost,
        "mountpoint": "",
        "fstype": "",
        "children": deti or [],
    }


def oddil(jmeno, mount="", fstype=""):
    return {
        "name": jmeno,
        "type": "part",
        "tran": "",
        "size": 100,
        "mountpoint": mount,
        "fstype": fstype,
        "children": [],
    }


def main():
    chyby = []

    def cekej(podminka, veta):
        if not podminka:
            chyby.append(veta)

    prazdne = set()
    cekej(stroj._vhodny_kandidat(disk("sda", "usb"), prazdne), "USB datový disk má jít přidat")
    cekej(stroj._vhodny_kandidat(disk("sdb", "sata"), prazdne), "SATA datový disk má jít přidat")
    cekej(stroj._vhodny_kandidat(disk("nvme0n1", "nvme"), prazdne), "NVMe datový disk má jít přidat")
    cekej(stroj._vhodny_kandidat(disk("sdc", "sas"), prazdne), "SAS datový disk má jít přidat")
    cekej(stroj._vhodny_kandidat(disk("sdd", ""), prazdne), "Disk bez údaje o připojení má jít přidat")
    cekej(stroj._vhodny_kandidat(disk("mmcblk1", "mmc"), prazdne), "eMMC bez systému má jít přidat")

    system_sata = disk("sda", "sata", [oddil("sda1", "/")])
    system_nvme = disk("nvme0n1", "nvme", [oddil("nvme0n1p1", "/"), oddil("nvme0n1p2", "/boot/efi")])
    system_mmc = disk("mmcblk0", "mmc", [oddil("mmcblk0p1", "/"), oddil("mmcblk0p2", "/boot/firmware")])
    cekej(stroj._je_system(system_sata, prazdne), "Systémový SATA se má poznat")
    cekej(stroj._je_system(system_nvme, prazdne), "Systémový NVMe se má poznat")
    cekej(stroj._je_system(system_mmc, prazdne), "Systémová karta se má poznat")
    cekej(not stroj._vhodny_kandidat(system_sata, prazdne), "Systémový SATA se nemá nabízet")
    cekej(not stroj._vhodny_kandidat(system_nvme, prazdne), "Systémový NVMe se nemá nabízet")
    cekej(not stroj._vhodny_kandidat(system_mmc, prazdne), "Systémová karta se nemá nabízet")

    swap = disk("sdb", "sata", [oddil("sdb1", "", "swap")])
    cekej(stroj._je_system(swap, prazdne), "Swap se má brát jako systém")
    cekej(stroj._je_system(disk("sdc", "usb", [oddil("sdc1")]), {"/dev/sdc1"}), "Swap ze seznamu se má poznat")

    lvm = disk("sdd", "sata", [oddil("sdd1", "", "LVM2_member")])
    cekej(not stroj._vhodny_kandidat(lvm, prazdne), "LVM se nemá nabízet ke smazání")
    cekej(not stroj._vhodny_kandidat(disk("loop0", "usb"), prazdne), "loop se nemá nabízet")
    cekej(not stroj._vhodny_kandidat(disk("sda", "sata", velikost=0), prazdne), "Prázdná velikost se nemá nabízet")

    cekej(stroj._oddil({"name": "sda"}) == "/dev/sda1", "Oddíl SATA")
    cekej(stroj._oddil({"name": "nvme0n1"}) == "/dev/nvme0n1p1", "Oddíl NVMe")
    cekej(stroj._oddil({"name": "mmcblk0"}) == "/dev/mmcblk0p1", "Oddíl eMMC")
    cekej(stroj._popis_pripojeni("") == "neznámé", "Prázdné připojení")
    cekej(stroj._popis_pripojeni("nvme") == "NVMe", "Popis NVMe")
    cekej(stroj.slozka_programu() == "pism", "ARM bere složku pism")
    cekej(raid._rodic_disku("sda1") == "sda", "Rodič SATA")
    cekej(raid._rodic_disku("nvme0n1p1") == "nvme0n1", "Rodič NVMe")
    cekej(raid._rodic_disku("mmcblk0p2") == "mmcblk0", "Rodič eMMC")

    stejne = {"name": "sdb", "serial": "ABC", "wwn": "wwn1", "size": "10"}
    cekej(stroj._totoznost(stejne) == ("sdb", "ABC", "wwn1", "10"), "Totožnost disku")

    preklad = (Path(__file__).resolve().parent / "pism" / "web" / "preklad.js").read_text(encoding="utf-8")
    for cast in napoveda.texty()["casti"]:
        if f'"{cast["nazev"]}"' not in preklad and cast["nazev"] not in {"Síť", "Disky", "Zrcadlo", "Uživatelé", "Sdílené složky", "Služby", "Datum a čas", "Informace o systému", "Napájení", "Zavírání", "Aktualizace PISM", "GrosiStudio", "Darovat"}:
            chyby.append("Chybí překlad názvu " + cast["nazev"])
        for veta in cast["odstavce"]:
            if f'"{veta}"' not in preklad:
                chyby.append("Chybí angličtina: " + veta[:80])

    def nacti(slozka, jmeno):
        cesta = Path(__file__).resolve().parent / slozka / f"{jmeno}.py"
        spec = importlib.util.spec_from_file_location(f"{slozka}_{jmeno}", cesta)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        return modul

    pc = nacti("pism-x86-64", "stroj")
    cekej(pc.VETEV == "pc", "Počítač je větev pc")
    cekej(pc.slozka_programu() == "pism-x86-64", "Počítač bere svou složku")
    cekej(pc.znacka_stroje() == "PC", "Značka počítače")
    cekej(not pc.je_podporovany_vetrak(), "Na počítači není větrák")
    pc_napoveda = nacti("pism-x86-64", "napoveda")
    pc_preklad = (Path(__file__).resolve().parent / "pism-x86-64" / "web" / "preklad.js").read_text(encoding="utf-8")
    vetrak_je = False
    for cast in pc_napoveda.texty()["casti"]:
        for veta in cast["odstavce"]:
            if "Raspberry Pi 4" in veta and "není" not in veta:
                vetrak_je = True
            if f'"{veta}"' not in pc_preklad:
                chyby.append("V počítači chybí angličtina: " + veta[:80])
    cekej(not vetrak_je, "Nápověda počítače neslibuje větrák Pi 4")
    cekej(not (Path(__file__).resolve().parent / "pism-x86-64" / "vetrak.py").exists(), "Ve složce počítače není větrák")

    if chyby:
        print("\n".join(chyby))
        return 1
    print("zkousky disků prošly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
