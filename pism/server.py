# -*- coding: utf-8 -*-
"""PISM: přihlášení a plocha."""

import hashlib
import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import stroj
import napoveda
import raid
import cas
import licence
import dar

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DATA = ROOT / "data"
USERS = DATA / "uzivatele.json"
PORT = 80
SPRAVCE = "admin"
MIN_HESLO = 4


def _je_spravce(jmeno, zaznam):
    typ = str((zaznam or {}).get("typ") or "")
    if typ == "spravce":
        return True
    if typ == "uzivatel":
        return False
    return jmeno == SPRAVCE


def _pocet_spravcu(users):
    return sum(1 for jmeno, zaznam in users.items() if _je_spravce(jmeno, zaznam))

PLOCHA = [
    {"id": "sit", "nazev": "Síť"},
    {"id": "disky", "nazev": "Disky"},
    {"id": "uzivatele", "nazev": "Uživatelé"},
    {"id": "slozky", "nazev": "Sdílené složky"},
    {"id": "sluzby", "nazev": "Služby"},
    {"id": "cas", "nazev": "Datum a čas"},
    {"id": "system", "nazev": "Informace o systému"},
    {"id": "napoveda", "nazev": "Nápověda"},
    {"id": "dar", "nazev": "Darovat"},
]

_lock = threading.Lock()
_sessions = {}


def _hash_heslo(heslo, sul):
    return hashlib.pbkdf2_hmac(
        "sha256", heslo.encode("utf-8"), sul.encode("utf-8"), 120000
    ).hex()


def _nacti_uzivatele():
    if not USERS.exists():
        return {}
    return json.loads(USERS.read_text(encoding="utf-8"))


def _uloz_uzivatele(data):
    DATA.mkdir(exist_ok=True)
    USERS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _token_z_cookie(header):
    for part in (header or "").split(";"):
        part = part.strip()
        if part.startswith("pism="):
            return part[5:]
    return ""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _json(self, code, obj, cookie=None):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def _soubor(self, name):
        path = WEB / name
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        typ = "text/html; charset=utf-8"
        if name.endswith(".css"):
            typ = "text/css; charset=utf-8"
        elif name.endswith(".js"):
            typ = "text/javascript; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", typ)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length < 0 or length > 10000:
            return None
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

    def _ucet(self):
        token = _token_z_cookie(self.headers.get("Cookie"))
        with _lock:
            return _sessions.get(token)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._soubor("index.html")
            return
        if path == "/style.css":
            self._soubor("style.css")
            return
        if path == "/app.js":
            self._soubor("app.js")
            return
        if path == "/grosistudio-logo.png":
            logo = (ROOT / "grosistudio-logo.png").resolve()
            if logo.parent != ROOT or not logo.is_file():
                self.send_error(404)
                return
            data = logo.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == "/api/stav":
            ucet = self._ucet()
            with _lock:
                prvni = not USERS.exists()
            spravce = False
            if ucet and not prvni:
                self._normalizuj_ucty()
                with _lock:
                    spravce = _je_spravce(ucet, _nacti_uzivatele().get(ucet))
            self._json(200, {
                "ok": True, "prvni": prvni, "prihlasen": bool(ucet),
                "ucet": ucet or "", "spravce": spravce,
            })
            return
        if path == "/api/prehled":
            if not self._chtej():
                return
            self._proved(stroj.prehled)
            return
        if path == "/api/prehled/rychlost":
            if not self._chtej():
                return
            self._proved(stroj.rychlost_site)
            return
        if not self._chtej_spravu():
            return
        if path == "/api/plocha":
            self._json(200, {"ok": True, "polozky": PLOCHA})
            return
        cteni = {
            "/api/sit": stroj.sit,
            "/api/disky": stroj.disky,
            "/api/disky/raid": raid.varovani,
            "/api/disky/raid/konfigurace": raid.konfigurace,
            "/api/napoveda": napoveda.texty,
            "/api/slozky": stroj.slozky,
            "/api/system": stroj.system,
            "/api/sluzby": stroj.sluzby,
            "/api/cas": cas.stav,
            "/api/dar": dar.texty,
            "/api/uzivatele": self._seznam_uctu,
            "/api/wifi": stroj.wifi_site,
        }
        if path == "/api/disky/smart":
            from urllib.parse import parse_qs, urlsplit
            dotaz = parse_qs(urlsplit(self.path).query)
            klic = (dotaz.get("disk") or [""])[0]
            self._proved(lambda: stroj.smart(klic))
            return
        if path in cteni:
            self._proved(cteni[path])
            return
        self.send_error(404)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        data = self._body()
        if data is None:
            self._json(400, {"ok": False, "hlaseni": "Požadavek se nepovedl."})
            return
        if path == "/api/prvni":
            self._prvni(data)
            return
        if path == "/api/prihlaseni":
            self._prihlaseni(data)
            return
        if path == "/api/odhlaseni":
            token = _token_z_cookie(self.headers.get("Cookie"))
            with _lock:
                _sessions.pop(token, None)
            self._json(200, {"ok": True}, "pism=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            return
        if not self._chtej_spravu():
            return
        akce = {
            "/api/sit/jmeno": lambda: stroj.nastav_jmeno(data.get("jmeno")),
            "/api/sit/adresa": lambda: stroj.nastav_adresu(
                data.get("rozhrani"), data.get("rezim"), data.get("adresa"),
                data.get("maska"), data.get("brana"),
            ),
            "/api/sit/obecne": lambda: stroj.nastav_obecne(
                data.get("vychozi"), data.get("dns"), data.get("dns2"),
            ),
            "/api/sit/wifi": lambda: stroj.wifi_pripoj(data.get("ssid"), data.get("heslo")),
            "/api/disky/svazek": lambda: self._svazek(data),
            "/api/disky/smazat": lambda: self._smaz_disk(data),
            "/api/disky/raid/pripojit": lambda: raid.pripoj(),
            "/api/disky/raid/zalozit": lambda: self._raid(data),
            "/api/uzivatele": lambda: self._novy_ucet(data),
            "/api/uzivatele/upravit": lambda: self._upravit_ucet(data),
            "/api/uzivatele/smazat": lambda: self._odeber_ucet(data),
            "/api/slozky": lambda: stroj.zaloz_slozku(data.get("nazev"), str(data.get("disk") or "")),
            "/api/slozky/pravo": lambda: stroj.nastav_pravo(data.get("nazev"), data.get("ucet"), data.get("pravo")),
            "/api/slozky/prava": lambda: stroj.nastav_prava(data.get("nazev"), data.get("prava")),
            "/api/slozky/smazat": lambda: stroj.smaz_slozku(data.get("nazev")),
            "/api/sluzby": lambda: stroj.nastav_sluzbu(data.get("id"), data.get("zapnuto")),
            "/api/cas/zdroj": lambda: cas.nastav_zdroj(bool(data.get("ntp"))),
            "/api/cas/server": lambda: cas.nastav_server(data.get("volba"), data.get("adresa")),
            "/api/cas/rucne": lambda: cas.nastav_rucne(data.get("datum"), data.get("hodina")),
            "/api/cas/pasmo": lambda: cas.nastav_pasmo(data.get("pasmo")),
            "/api/system/restart": stroj.restartovat,
            "/api/system/vypnout": stroj.vypnout,
        }
        if path in akce:
            self._proved(akce[path])
            return
        self.send_error(404)

    def _chtej(self):
        if self._ucet():
            return True
        self._json(401, {"ok": False, "hlaseni": "Nejsi přihlášen."})
        return False

    def _chtej_spravu(self):
        if not self._chtej():
            return False
        self._normalizuj_ucty()
        ucet = self._ucet()
        with _lock:
            spravce = _je_spravce(ucet, _nacti_uzivatele().get(ucet))
        if spravce:
            return True
        self._json(403, {"ok": False, "hlaseni": "Správu dělá jen správce."})
        return False

    def _normalizuj_ucty(self):
        uvolnit = []
        with _lock:
            users = _nacti_uzivatele()
            zmena = False
            for jmeno, zaznam in users.items():
                if not isinstance(zaznam, dict):
                    continue
                if zaznam.get("typ") not in ("spravce", "uzivatel"):
                    zaznam["typ"] = "spravce" if jmeno == SPRAVCE else "uzivatel"
                    zmena = True
                if not zaznam.get("aktivni", True):
                    zaznam["aktivni"] = True
                    zmena = True
                    uvolnit.append(jmeno)
            if zmena:
                _uloz_uzivatele(users)
        for jmeno in uvolnit:
            try:
                stroj.nastav_aktivni(jmeno, True)
            except stroj.StrojChyba:
                pass

    def _proved(self, funkce):
        try:
            vysledek = funkce()
        except stroj.StrojChyba as chyba:
            self._json(400, {"ok": False, "hlaseni": str(chyba)})
            return
        if not isinstance(vysledek, dict):
            vysledek = {}
        self._json(200, {"ok": True, **vysledek})

    def _seznam_uctu(self):
        self._normalizuj_ucty()
        with _lock:
            users = _nacti_uzivatele()
        return {"ucty": [
            {"ucet": jmeno, "typ": "spravce" if _je_spravce(jmeno, zaznam) else "uzivatel"}
            for jmeno, zaznam in users.items()
        ]}

    def _svazek(self, data):
        if str(data.get("potvrzeni", "")) != "SMAZAT":
            raise stroj.StrojChyba("Pro přidání disku napiš SMAZAT.")
        return stroj.vytvor_svazek(str(data.get("disk") or ""))

    def _smaz_disk(self, data):
        if str(data.get("potvrzeni", "")) != "SMAZAT":
            raise stroj.StrojChyba("Pro smazání disku napiš SMAZAT.")
        return stroj.smaz_disk(str(data.get("disk") or "hlavni"))

    def _raid(self, data):
        if str(data.get("potvrzeni", "")) != "SMAZAT":
            raise stroj.StrojChyba("Pro založení zrcadla napiš SMAZAT.")
        return raid.zaloz(data.get("disky"))

    def _novy_ucet(self, data):
        ucet = str(data.get("ucet", "")).strip().lower()
        heslo = str(data.get("heslo", ""))
        typ = str(data.get("typ") or "uzivatel").strip()
        if typ not in ("spravce", "uzivatel"):
            raise stroj.StrojChyba("Vyber správce, nebo uživatele.")
        if ucet == SPRAVCE:
            raise stroj.StrojChyba("Správce už je založený.")
        if len(heslo) < MIN_HESLO:
            raise stroj.StrojChyba("Heslo má mít aspoň 4 znaky.")
        with _lock:
            users = _nacti_uzivatele()
            if ucet in users:
                raise stroj.StrojChyba("Takový účet už je.")
        stroj.zajisti_ucet(ucet, heslo)
        with _lock:
            users = _nacti_uzivatele()
            sul = secrets.token_hex(16)
            users[ucet] = {
                "sul": sul, "heslo": _hash_heslo(heslo, sul),
                "aktivni": True, "typ": typ,
            }
            _uloz_uzivatele(users)
        return self._seznam_uctu()

    def _heslo_uctu(self, data):
        ucet = str(data.get("ucet", "")).strip().lower()
        heslo = str(data.get("heslo", ""))
        if len(heslo) < MIN_HESLO:
            raise stroj.StrojChyba("Heslo má mít aspoň 4 znaky.")
        with _lock:
            users = _nacti_uzivatele()
            if ucet not in users:
                raise stroj.StrojChyba("Účet není.")
            sul = secrets.token_hex(16)
            users[ucet]["sul"] = sul
            users[ucet]["heslo"] = _hash_heslo(heslo, sul)
            users[ucet]["aktivni"] = True
            _uloz_uzivatele(users)
        stroj.zajisti_ucet(ucet, heslo)
        stroj.nastav_aktivni(ucet, True)
        return self._seznam_uctu()

    def _upravit_ucet(self, data):
        ucet = str(data.get("ucet", "")).strip().lower()
        typ = str(data.get("typ", "")).strip()
        heslo = str(data.get("heslo") or "")
        if typ not in ("spravce", "uzivatel"):
            raise stroj.StrojChyba("Vyber správce, nebo uživatele.")
        if heslo and len(heslo) < MIN_HESLO:
            raise stroj.StrojChyba("Heslo má mít aspoň 4 znaky.")
        with _lock:
            users = _nacti_uzivatele()
            if ucet not in users:
                raise stroj.StrojChyba("Účet není.")
            if _je_spravce(ucet, users[ucet]) and typ == "uzivatel" and _pocet_spravcu(users) <= 1:
                raise stroj.StrojChyba("Posledního správce nejde změnit na uživatele.")
            users[ucet]["typ"] = typ
            users[ucet]["aktivni"] = True
            _uloz_uzivatele(users)
        if heslo:
            self._heslo_uctu({"ucet": ucet, "heslo": heslo})
        else:
            try:
                stroj.nastav_aktivni(ucet, True)
            except stroj.StrojChyba:
                pass
        return self._seznam_uctu()

    def _odeber_ucet(self, data):
        ucet = str(data.get("ucet", "")).strip().lower()
        with _lock:
            users = _nacti_uzivatele()
            if ucet not in users:
                raise stroj.StrojChyba("Účet není.")
            if _je_spravce(ucet, users[ucet]) and _pocet_spravcu(users) <= 1:
                raise stroj.StrojChyba("Posledního správce nejde odebrat.")
        stroj.smaz_ucet(ucet)
        with _lock:
            users = _nacti_uzivatele()
            users.pop(ucet, None)
            _uloz_uzivatele(users)
        return self._seznam_uctu()

    def _prvni(self, data):
        heslo = str(data.get("heslo", ""))
        znovu = str(data.get("znovu", ""))
        if len(heslo) < MIN_HESLO:
            self._json(400, {"ok": False, "hlaseni": "Heslo má mít aspoň 4 znaky."})
            return
        if heslo != znovu:
            self._json(400, {"ok": False, "hlaseni": "Hesla se neshodují."})
            return
        with _lock:
            if USERS.exists():
                self._json(400, {"ok": False, "hlaseni": "Účet správce už je založený."})
                return
            sul = secrets.token_hex(16)
            _uloz_uzivatele({
                SPRAVCE: {
                    "sul": sul, "heslo": _hash_heslo(heslo, sul),
                    "aktivni": True, "typ": "spravce",
                }
            })
            token = secrets.token_urlsafe(32)
            _sessions[token] = SPRAVCE
        try:
            stroj.zajisti_ucet(SPRAVCE, heslo)
        except stroj.StrojChyba:
            pass
        self._json(
            200,
            {"ok": True, "ucet": SPRAVCE, "dar": _dar_pri_vstupu(SPRAVCE)},
            f"pism={token}; Path=/; HttpOnly; SameSite=Lax",
        )

    def _prihlaseni(self, data):
        ucet = str(data.get("ucet", "")).strip().lower()
        heslo = str(data.get("heslo", ""))
        self._normalizuj_ucty()
        with _lock:
            users = _nacti_uzivatele()
            zaznam = users.get(ucet)
            if not zaznam:
                platne = False
            else:
                platne = hmac.compare_digest(zaznam["heslo"], _hash_heslo(heslo, zaznam["sul"]))
            token = secrets.token_urlsafe(32) if platne else ""
            if platne:
                _sessions[token] = ucet
        if not platne:
            self._json(401, {"ok": False, "hlaseni": "Účet nebo heslo nesedí."})
            return
        try:
            stroj.zajisti_ucet(ucet, heslo)
        except stroj.StrojChyba:
            pass
        self._json(
            200,
            {"ok": True, "ucet": ucet, "dar": _dar_pri_vstupu(ucet)},
            f"pism={token}; Path=/; HttpOnly; SameSite=Lax",
        )


def _dar_pri_vstupu(ucet):
    try:
        with _lock:
            spravce = _je_spravce(ucet, _nacti_uzivatele().get(ucet))
    except Exception:
        spravce = ucet == SPRAVCE
    if not spravce:
        return False
    try:
        return dar.losuj()
    except Exception:
        return False


def main():
    try:
        licence.uplatni()
    except Exception:
        pass
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"PISM port {PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
