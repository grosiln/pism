# -*- coding: utf-8 -*-
"""PISM: síť."""

import subprocess
import time
from pathlib import Path

import stroj

_beh = stroj._beh
StrojChyba = stroj.StrojChyba
JMENO_ZARIZENI = stroj.JMENO_ZARIZENI
HOSTS = stroj.HOSTS

def _stav_site(text):
    text = text or ""
    if "disconnected" in text:
        return "odpojeno"
    if "connecting" in text:
        return "připojuje se"
    if "connected" in text:
        return "připojeno"
    if "unavailable" in text:
        return "vypnuto"
    return text or "neznámý"


def _nmcli(zarizeni):
    text = _beh([
        "nmcli", "-t", "-f",
        "IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,GENERAL.HWADDR,GENERAL.STATE,GENERAL.CONNECTION",
        "device", "show", zarizeni,
    ]).stdout
    data = {}
    for radek in text.splitlines():
        if ":" not in radek:
            continue
        klic, hodnota = radek.split(":", 1)
        klic = klic.split("[", 1)[0]
        data.setdefault(klic, [])
        if hodnota:
            data[klic].append(hodnota)
    return data


def _prvni(data, klic, prazdne=""):
    return (data.get(klic) or [prazdne])[0]


def _nmcli_bezpecne(zarizeni):
    try:
        return _nmcli(zarizeni)
    except StrojChyba:
        return {}


def _aktivni_pripojeni(zarizeni):
    try:
        text = _beh(["nmcli", "-t", "-f", "NAME,DEVICE", "connection", "show", "--active"]).stdout
    except StrojChyba:
        return ""
    for radek in text.splitlines():
        casti = _pole_nmcli(radek)
        if len(casti) >= 2 and casti[-1] == zarizeni and casti[0] not in {"lo", "loopback"}:
            return casti[0]
    return ""


def _klic_pripojeni(nazev, klic):
    return _beh(["nmcli", "-g", klic, "connection", "show", nazev]).stdout.strip()


def _maska_z_prefixu(prefix):
    try:
        n = int(prefix)
    except (TypeError, ValueError):
        return ""
    if n < 0 or n > 32:
        return ""
    bity = ("1" * n).ljust(32, "0")
    return ".".join(str(int(bity[i:i + 8], 2)) for i in range(0, 32, 8))


def _popis_adresy(zarizeni, data):
    cela = _prvni(data, "IP4.ADDRESS")
    adresa, _, prefix = cela.partition("/")
    dns = list(data.get("IP4.DNS") or [])
    brana = _prvni(data, "IP4.GATEWAY")
    nazev = _aktivni_pripojeni(zarizeni)
    rezim = "dhcp"
    if nazev:
        try:
            if _klic_pripojeni(nazev, "ipv4.method") == "manual":
                rezim = "pevna"
                if not adresa:
                    ulozena = _klic_pripojeni(nazev, "ipv4.addresses").split(",")[0].strip()
                    adresa, _, prefix = ulozena.partition("/")
                if not brana:
                    brana = _klic_pripojeni(nazev, "ipv4.gateway")
                if not dns:
                    dns = _klic_pripojeni(nazev, "ipv4.dns").replace(",", " ").split()
        except StrojChyba:
            rezim = "dhcp"
    return {
        "stav": _stav_site(_prvni(data, "GENERAL.STATE", "neznámý")),
        "adresa": adresa,
        "maska": _maska_z_prefixu(prefix) if prefix else "",
        "brana": brana,
        "dns": ", ".join(dns),
        "dns1": dns[0] if dns else "",
        "dns2": dns[1] if len(dns) > 1 else "",
        "rezim": rezim,
        "lze": bool(nazev),
        "mac": _prvni(data, "GENERAL.HWADDR"),
    }


PAMET_WIFI = Path("/var/lib/pism/wifi-pripojeni")


def _kabel_zapojen():
    try:
        return Path("/sys/class/net/eth0/carrier").read_text(encoding="ascii").strip() == "1"
    except OSError:
        return False


def _vychozi_rozhrani():
    if _kabel_zapojen():
        return "lan"
    nalezene = []
    for rozhrani, zarizeni in (("lan", "eth0"), ("wifi", "wlan0")):
        nazev = _aktivni_pripojeni(zarizeni)
        if not nazev:
            continue
        try:
            if _klic_pripojeni(nazev, "ipv4.never-default") == "yes":
                continue
            metrika = int(_klic_pripojeni(nazev, "ipv4.route-metric") or "0")
        except (StrojChyba, ValueError):
            metrika = 0
        nalezene.append((metrika, rozhrani))
    if nalezene:
        nalezene.sort()
        return nalezene[0][1]
    if _aktivni_pripojeni("eth0"):
        return "lan"
    return "wifi"


def _signal_wifi(ssid):
    if not ssid:
        return ""
    try:
        text = _beh(
            ["nmcli", "-t", "-f", "ACTIVE,SIGNAL,SSID", "dev", "wifi", "list", "--rescan", "no"],
            cas=8,
        ).stdout
    except StrojChyba:
        return ""
    for radek in text.splitlines():
        casti = _pole_nmcli(radek)
        if len(casti) >= 3 and casti[0] in {"yes", "*"} and casti[2] == ssid:
            return casti[1]
    return ""


def _wifi_profily():
    try:
        text = _beh(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]).stdout
    except StrojChyba:
        return []
    seznam = []
    for radek in text.splitlines():
        casti = _pole_nmcli(radek)
        if len(casti) >= 2 and casti[-1] == "802-11-wireless" and casti[0]:
            seznam.append(casti[0])
    return seznam


def _zapamatuj_wifi():
    nazev = _aktivni_pripojeni("wlan0")
    if not nazev:
        return
    PAMET_WIFI.parent.mkdir(parents=True, exist_ok=True)
    PAMET_WIFI.write_text(nazev + "\n", encoding="utf-8")


def _vybrana_wifi():
    profily = _wifi_profily()
    if PAMET_WIFI.is_file():
        nazev = PAMET_WIFI.read_text(encoding="utf-8").strip()
        if nazev in profily:
            return nazev
    nej = ""
    cas = -1
    for nazev in profily:
        try:
            razitko = int(_klic_pripojeni(nazev, "connection.timestamp") or "0")
        except (StrojChyba, ValueError):
            razitko = 0
        if razitko >= cas:
            cas = razitko
            nej = nazev
    return nej


def _ssid_profilu(nazev):
    if not nazev:
        return ""
    try:
        return _klic_pripojeni(nazev, "802-11-wireless.ssid") or nazev
    except StrojChyba:
        return nazev


def sit():
    lan = _popis_adresy("eth0", _nmcli_bezpecne("eth0"))
    wifi_raw = _nmcli_bezpecne("wlan0")
    wifi = _popis_adresy("wlan0", wifi_raw)
    wifi["sit"] = _prvni(wifi_raw, "GENERAL.CONNECTION") or _ssid_profilu(_vybrana_wifi())
    kabel = _kabel_zapojen()
    wifi["potlacena"] = kabel and bool(wifi["sit"])
    if wifi["potlacena"] and not wifi["lze"]:
        wifi["stav"] = "potlačená"
    wifi["signal"] = _signal_wifi(wifi["sit"]) if wifi["lze"] else ""
    vychozi = "lan" if kabel or lan["lze"] else "wifi"
    zdroj = lan if vychozi == "lan" and lan["lze"] else wifi if wifi["lze"] else lan
    return {
        "jmeno": Path("/etc/hostname").read_text(encoding="utf-8").strip(),
        "kabel": kabel,
        "obecne": {
            "vychozi": vychozi,
            "dns1": zdroj.get("dns1") or "",
            "dns2": zdroj.get("dns2") or "",
        },
        "lan": lan,
        "wifi": wifi,
    }


def nastav_jmeno(jmeno):
    jmeno = str(jmeno or "").strip().lower()
    if not JMENO_ZARIZENI.fullmatch(jmeno):
        raise StrojChyba("Jméno zařízení má být z malých písmen a číslic.")
    _beh(["hostnamectl", "set-hostname", jmeno])
    radky = []
    nalezeno = False
    if HOSTS.exists():
        for radek in HOSTS.read_text(encoding="utf-8").splitlines():
            if radek.startswith("127.0.1.1"):
                radky.append(f"127.0.1.1\t{jmeno}")
                nalezeno = True
            else:
                radky.append(radek)
    if not nalezeno:
        radky.append(f"127.0.1.1\t{jmeno}")
    HOSTS.write_text("\n".join(radky) + "\n", encoding="utf-8")
    return sit()


def _bajty_ip(text, hlaska):
    casti = str(text or "").strip().split(".")
    if len(casti) != 4:
        raise StrojChyba(hlaska)
    cisla = []
    for cast in casti:
        if not cast.isdigit():
            raise StrojChyba(hlaska)
        cislo = int(cast)
        if cislo > 255:
            raise StrojChyba(hlaska)
        cisla.append(cislo)
    return cisla


def _prefix_z_masky(maska):
    cisla = _bajty_ip(maska, "Maska má být ve tvaru 255.255.255.0.")
    bity = "".join(f"{cislo:08b}" for cislo in cisla)
    if "01" in bity:
        raise StrojChyba("Maska má být ve tvaru 255.255.255.0.")
    prefix = bity.count("1")
    if prefix < 8 or prefix > 30:
        raise StrojChyba("Maska má být ve tvaru 255.255.255.0.")
    return prefix


def _stejna_sit(adresa, maska, brana):
    sit_adresy = tuple(a & b for a, b in zip(adresa, maska))
    sit_brany = tuple(a & b for a, b in zip(brana, maska))
    if sit_adresy != sit_brany:
        raise StrojChyba("Brána musí být ve stejné síti jako adresa.")


def _dns_polozky(dns, dns2):
    seznam = []
    for polozka in (dns, dns2):
        polozka = str(polozka or "").strip()
        if not polozka or polozka in seznam:
            continue
        cisla = _bajty_ip(polozka, "DNS má být adresa.")
        if cisla[0] == 0:
            raise StrojChyba("DNS má být adresa.")
        seznam.append(polozka)
    return seznam


def _role_rozhrani(rozhrani, vychozi):
    if rozhrani == vychozi:
        return "100", "no"
    return "600", "yes"


def _zapis_pripojeni(nazev, dvojice):
    prikaz = ["nmcli", "connection", "modify", nazev]
    for klic, hodnota in dvojice:
        prikaz.extend([klic, str(hodnota)])
    _beh(prikaz)


def _aktivuj_pripojeni(nazev, zarizeni):
    try:
        _beh(["nmcli", "connection", "up", nazev, "ifname", zarizeni], cas=40)
    except StrojChyba:
        _beh(["nmcli", "connection", "up", nazev], cas=40)


def _stav_ipv4(nazev):
    klice = (
        "ipv4.method",
        "ipv4.addresses",
        "ipv4.gateway",
        "ipv4.dns",
        "ipv4.route-metric",
        "ipv4.never-default",
        "ipv4.ignore-auto-dns",
        "connection.autoconnect",
    )
    return {klic: _klic_pripojeni(nazev, klic) for klic in klice}


def _pockej_na_adresu(zarizeni):
    for _ in range(6):
        if _prvni(_nmcli_bezpecne(zarizeni), "IP4.ADDRESS"):
            return
        time.sleep(1)


def nastav_adresu(rozhrani, rezim, adresa="", maska="", brana="", dns="", dns2=""):
    rozhrani = str(rozhrani or "").strip()
    if rozhrani not in {"lan", "wifi"}:
        raise StrojChyba("Vyber kabel, nebo Wi-Fi.")
    zarizeni = "eth0" if rozhrani == "lan" else "wlan0"
    nazev = _aktivni_pripojeni(zarizeni)
    if not nazev:
        if rozhrani == "wifi":
            raise StrojChyba("Nejdřív se připoj k Wi-Fi.")
        raise StrojChyba("Kabel není připojený.")
    rezim = str(rezim or "").strip()
    vychozi = _vychozi_rozhrani()
    metrika, never = _role_rozhrani(rozhrani, vychozi)
    if rezim == "dhcp":
        dvojice = [
            ("ipv4.method", "auto"),
            ("ipv4.addresses", ""),
            ("ipv4.gateway", ""),
            ("ipv4.route-metric", metrika),
            ("ipv4.never-default", never),
            ("connection.autoconnect", "yes"),
        ]
    elif rezim == "pevna":
        cil = _bajty_ip(adresa, "Adresa nesedí.")
        if cil[0] in {0, 127} or cil == [255, 255, 255, 255]:
            raise StrojChyba("Tahle adresa se použít nedá.")
        maska_cisla = _bajty_ip(maska, "Maska má být ve tvaru 255.255.255.0.")
        prefix = _prefix_z_masky(maska)
        brana = str(brana or "").strip()
        if brana:
            brana_cisla = _bajty_ip(brana, "Brána nesedí.")
            if brana_cisla == cil:
                raise StrojChyba("Brána nemůže být stejná jako adresa.")
            _stejna_sit(cil, maska_cisla, brana_cisla)
        elif rozhrani == vychozi:
            raise StrojChyba("Připojení, kterým se chodí ven, potřebuje bránu.")
        dvojice = [
            ("ipv4.method", "manual"),
            ("ipv4.addresses", f"{'.'.join(str(c) for c in cil)}/{prefix}"),
            ("ipv4.gateway", brana),
            ("ipv4.route-metric", metrika),
            ("ipv4.never-default", never),
            ("connection.autoconnect", "yes"),
        ]
    else:
        raise StrojChyba("Vyber automaticky z routeru, nebo pevnou adresu.")
    puvodni = _stav_ipv4(nazev)
    try:
        _zapis_pripojeni(nazev, dvojice)
        _aktivuj_pripojeni(nazev, zarizeni)
    except StrojChyba:
        try:
            _zapis_pripojeni(nazev, list(puvodni.items()))
            _aktivuj_pripojeni(nazev, zarizeni)
        except StrojChyba:
            raise StrojChyba("Adresu se nepodařilo uložit.")
        raise StrojChyba("Adresu se nepodařilo použít. Nechávám původní nastavení.")
    _pockej_na_adresu(zarizeni)
    return sit()


def nastav_obecne(vychozi, dns="", dns2=""):
    vychozi = str(vychozi or "").strip()
    if _kabel_zapojen():
        vychozi = "lan"
    if vychozi not in {"lan", "wifi"}:
        raise StrojChyba("Vyber, kudy se chodí ven.")
    dns_seznam = _dns_polozky(dns, dns2)
    zarizeni = {"lan": "eth0", "wifi": "wlan0"}
    if not _aktivni_pripojeni(zarizeni[vychozi]):
        raise StrojChyba("To připojení teď není zapojené.")
    if not _prvni(_nmcli_bezpecne(zarizeni[vychozi]), "IP4.GATEWAY"):
        raise StrojChyba("Na tom připojení není brána.")
    cile = []
    for rozhrani, jmeno_zarizeni in (("lan", "eth0"), ("wifi", "wlan0")):
        if _kabel_zapojen() and rozhrani == "wifi":
            continue
        nazev = _aktivni_pripojeni(jmeno_zarizeni)
        if nazev:
            cile.append((rozhrani, jmeno_zarizeni, nazev))
    puvodni = []
    try:
        for rozhrani, jmeno_zarizeni, nazev in cile:
            metrika, never = _role_rozhrani(rozhrani, vychozi)
            puvodni.append((nazev, jmeno_zarizeni, _stav_ipv4(nazev)))
            _zapis_pripojeni(nazev, [
                ("ipv4.dns", " ".join(dns_seznam)),
                ("ipv4.ignore-auto-dns", "yes" if dns_seznam else "no"),
                ("ipv4.route-metric", metrika),
                ("ipv4.never-default", never),
                ("connection.autoconnect", "yes"),
            ])
        for nazev in _wifi_profily():
            try:
                _zapis_pripojeni(nazev, [
                    ("ipv4.dns", " ".join(dns_seznam)),
                    ("ipv4.ignore-auto-dns", "yes" if dns_seznam else "no"),
                ])
            except StrojChyba:
                pass
        poradi = sorted(cile, key=lambda polozka: polozka[0] == vychozi)
        for rozhrani, jmeno_zarizeni, nazev in poradi:
            _aktivuj_pripojeni(nazev, jmeno_zarizeni)
        srovnej_sit()
    except StrojChyba:
        try:
            for nazev, jmeno_zarizeni, stav in puvodni:
                _zapis_pripojeni(nazev, list(stav.items()))
                _aktivuj_pripojeni(nazev, jmeno_zarizeni)
        except StrojChyba:
            raise StrojChyba("Nastavení se nepodařilo uložit.")
        raise StrojChyba("Nastavení se nepodařilo použít. Nechávám původní.")
    return sit()


def _pole_nmcli(radek):
    pole = []
    aktualni = []
    escapovano = False
    for znak in radek:
        if escapovano:
            aktualni.append(znak)
            escapovano = False
        elif znak == "\\":
            escapovano = True
        elif znak == ":":
            pole.append("".join(aktualni))
            aktualni = []
        else:
            aktualni.append(znak)
    pole.append("".join(aktualni))
    return pole


def srovnej_sit():
    import fcntl
    PAMET_WIFI.parent.mkdir(parents=True, exist_ok=True)
    Path("/run").mkdir(exist_ok=True)
    with Path("/run/pism-sit.lock").open("a", encoding="utf-8") as zamek:
        fcntl.flock(zamek, fcntl.LOCK_EX)
        _zapamatuj_wifi()
        vybrana = _vybrana_wifi()
        if _kabel_zapojen():
            for nazev in _wifi_profily():
                try:
                    _zapis_pripojeni(nazev, [("connection.autoconnect", "no")])
                except StrojChyba:
                    pass
            if _aktivni_pripojeni("wlan0"):
                subprocess.run(["nmcli", "device", "disconnect", "wlan0"], capture_output=True)
            Path("/run/pism-sit").write_text("kabel\n", encoding="utf-8")
            return
        if not vybrana:
            Path("/run/pism-sit").write_text("wifi-chybi\n", encoding="utf-8")
            return
        try:
            _zapis_pripojeni(vybrana, [("connection.autoconnect", "yes")])
            _beh(["nmcli", "radio", "wifi", "on"])
            if _aktivni_pripojeni("wlan0") != vybrana:
                _aktivuj_pripojeni(vybrana, "wlan0")
        except StrojChyba:
            Path("/run/pism-sit").write_text("wifi-ceka\n", encoding="utf-8")
            return
        Path("/run/pism-sit").write_text("wifi\n", encoding="utf-8")


def wifi_site():
    _beh(["nmcli", "radio", "wifi", "on"])
    text = _beh(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"], cas=40).stdout
    site = []
    videne = set()
    for radek in text.splitlines():
        casti = _pole_nmcli(radek)
        if len(casti) < 2 or not casti[0] or casti[0] in videne:
            continue
        videne.add(casti[0])
        site.append({"ssid": casti[0], "signal": casti[1]})
    return {"site": site}


def wifi_pripoj(ssid, heslo):
    ssid = str(ssid or "").strip()
    heslo = str(heslo or "")
    if not ssid or len(ssid) > 32:
        raise StrojChyba("Chybí jméno sítě.")
    _beh(["nmcli", "radio", "wifi", "on"])
    try:
        if heslo:
            _beh(["nmcli", "dev", "wifi", "connect", ssid, "password", heslo], cas=40)
        else:
            _beh(["nmcli", "dev", "wifi", "connect", ssid], cas=40)
    except StrojChyba:
        raise StrojChyba("K Wi-Fi se nepodařilo připojit.")
    _zapamatuj_wifi()
    srovnej_sit()
    return sit()
