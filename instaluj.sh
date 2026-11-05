#!/bin/bash
# Jeden instalacni krok. Na nic se nepta. Pozna stroj a vezme spravnou slozku.
set -euo pipefail

hlaska() {
  printf '%s\n%s\n' "$1" "$2"
}

if [ "$(id -u)" -ne 0 ]; then
  hlaska "Spusť tu větu znovu se sudo na začátku." "Run that sentence again with sudo at the beginning."
  exit 1
fi

hlaska "Kontroluji stroj." "Checking the computer."

if [ ! -r /etc/os-release ]; then
  hlaska "Tohle není podporovaný Debian. Instalace se zastavila. Nic se nemění." "This is not a supported Debian. The installation stopped. Nothing was changed."
  exit 1
fi
# shellcheck disable=SC1091
. /etc/os-release
case "${ID:-}" in
  debian|raspbian) ;;
  *)
    hlaska "Tohle není podporovaný Debian. Instalace se zastavila. Nic se nemění." "This is not a supported Debian. The installation stopped. Nothing was changed."
    exit 1
    ;;
esac

if ! command -v systemctl >/dev/null 2>&1 || ! command -v dpkg >/dev/null 2>&1; then
  hlaska "Chybí systemd nebo dpkg. Instalace se zastavila. Nic se nemění." "systemd or dpkg is missing. The installation stopped. Nothing was changed."
  exit 1
fi

ARCH="$(dpkg --print-architecture)"
VETEV=""
case "$ARCH" in
  arm64) VETEV="pism" ;;
  amd64) VETEV="pism-x86-64" ;;
  *)
    hlaska "Tohle není 64 bit. Instalace se zastavila. Nic se nemění." "This is not 64-bit. The installation stopped. Nothing was changed."
    exit 1
    ;;
esac

MODEL=""
if [ -r /proc/device-tree/model ]; then
  MODEL="$(tr -d '\0' < /proc/device-tree/model || true)"
fi

VETRAK=0
if [ "$VETEV" = "pism" ] && printf '%s' "$MODEL" | grep -q "Raspberry Pi 4"; then
  VETRAK=1
  hlaska "Tohle je Raspberry Pi 4, 64bitové ARM. Připravím PISM pro ARM, včetně větráku." "This is a Raspberry Pi 4, 64-bit ARM. PISM for ARM will be prepared, including the fan."
elif [ "$VETEV" = "pism" ] && printf '%s' "$MODEL" | grep -q "Raspberry Pi 5"; then
  hlaska "Tohle je Raspberry Pi 5, 64bitové ARM. Připravím PISM pro ARM. Větrák se nezapne." "This is a Raspberry Pi 5, 64-bit ARM. PISM for ARM will be prepared. The fan will not start."
elif [ "$VETEV" = "pism" ]; then
  hlaska "Tohle je 64bitové ARM. Připravím PISM pro ARM. Větrák se nezapne." "This is 64-bit ARM. PISM for ARM will be prepared. The fan will not start."
else
  hlaska "Tohle je běžný 64bitový počítač. Připravím PISM pro x86-64." "This is an ordinary 64-bit computer. PISM for x86-64 will be prepared."
fi

hlaska "Instaluji potřebné balíčky. Je potřeba internet." "Installing the needed packages. Internet is required."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 samba smartmontools mdadm curl ca-certificates tar

if [ "$VETRAK" = "1" ]; then
  if ! apt-get install -y python3-rpi.gpio; then
    VETRAK=0
    hlaska "Větrák se nezapne, balíček pro něj chybí. PISM se instaluje dál." "The fan will not start, its package is missing. PISM installation continues."
  fi
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
  hlaska "Python je moc starý. Instalace se zastavila." "Python is too old. The installation stopped."
  exit 1
fi

hlaska "Stahuji PISM." "Downloading PISM."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://github.com/grosiln/pism/archive/refs/heads/main.tar.gz" -o "$TMP/pism.tar.gz"
tar -xzf "$TMP/pism.tar.gz" -C "$TMP"
ZDROJ="$TMP/pism-main/$VETEV"
CIL="/opt/pism"
DATA="/var/lib/pism"

if [ ! -f "$ZDROJ/server.py" ]; then
  hlaska "Instalace nenašla program pro tenhle stroj. Nic dalšího se nemění." "The installation did not find the program for this computer. Nothing further was changed."
  exit 1
fi

hlaska "Připravuji služby." "Preparing the services."
install -d -m 755 "$CIL" "$CIL/web" "$DATA"

if [ -f /home/pi/pism/data/uzivatele.json ] && [ ! -f "$DATA/uzivatele.json" ]; then
  cp -a /home/pi/pism/data/. "$DATA/"
fi

for soubor in \
  server.py stroj.py raid.py licence.py dar.py napoveda.py cas.py sdileni.py sit.py vetrak.py aktualizace.py \
  pism-sit pism.service pism-vetrak.service pism-sit.service grosistudio-logo.png
do
  if [ -f "$ZDROJ/$soubor" ]; then
    install -m 644 "$ZDROJ/$soubor" "$CIL/$soubor"
  fi
done
if [ -f "$CIL/pism-sit" ]; then
  chmod 755 "$CIL/pism-sit"
fi

for soubor in index.html app.js style.css preklad.js; do
  install -m 644 "$ZDROJ/web/$soubor" "$CIL/web/$soubor"
done

groupadd -f pism

install -m 755 "$CIL/pism-sit" /usr/local/sbin/pism-sit
if [ -d /etc/NetworkManager/dispatcher.d ]; then
  install -m 755 "$CIL/pism-sit" /etc/NetworkManager/dispatcher.d/99-pism-sit
fi

install -m 644 "$CIL/pism.service" /etc/systemd/system/pism.service
install -m 644 "$CIL/pism-sit.service" /etc/systemd/system/pism-sit.service

if [ ! -f /etc/samba/pism.conf ]; then
  printf '%s\n' "# pism" > /etc/samba/pism.conf
fi
if [ -f /etc/samba/smb.conf ] && ! grep -q "include = /etc/samba/pism.conf" /etc/samba/smb.conf; then
  printf '\n%s\n' "include = /etc/samba/pism.conf" >> /etc/samba/smb.conf
fi

systemctl disable --now samba-ad-dc >/dev/null 2>&1 || true
systemctl enable --now smbd
systemctl restart smbd
systemctl try-restart nmbd || true

systemctl daemon-reload
systemctl enable --now pism.service
systemctl enable --now pism-sit.service

if [ "$VETRAK" = "1" ] && [ -f "$CIL/pism-vetrak.service" ]; then
  install -m 644 "$CIL/pism-vetrak.service" /etc/systemd/system/pism-vetrak.service
  systemctl daemon-reload
  systemctl enable --now pism-vetrak.service
else
  systemctl disable --now pism-vetrak.service >/dev/null 2>&1 || true
fi

instalace_znacka() {
  local soubor="$DATA/znacka"
  local znacka=""
  if [ -s "$soubor" ]; then
    znacka="$(tr -d ' \n\r' < "$soubor" || true)"
  fi
  if ! printf '%s' "$znacka" | grep -Eq '^[a-f0-9]{32}$'; then
    install -d -m 755 "$DATA"
    znacka="$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')"
    printf '%s\n' "$znacka" > "$soubor"
    chmod 600 "$soubor"
  fi
  curl -fs --max-time 8 -o /dev/null \
    --data-urlencode "znacka=${znacka}" \
    "https://www.7ruzi.cz/pism/oznamit.php" \
    || true
}
instalace_znacka || true

if [ -f "$DATA/uzivatele.json" ]; then
  hlaska "Dosavadní účty a složky zůstaly." "The existing accounts and folders stayed."
else
  hlaska "PISM je prázdné. Nejsou v něm účty, sdílené složky ani připojené disky." "PISM is empty. There are no accounts, shared folders or connected disks."
  hlaska "První otevření v prohlížeči si řekne o heslo správce." "The first open in the browser asks for the administrator password."
fi

adresa="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -n "${adresa:-}" ]; then
  hlaska "Hotovo. V prohlížeči otevři http://$adresa" "Done. In the browser open http://$adresa"
else
  hlaska "Hotovo. V prohlížeči otevři adresu tohoto stroje." "Done. In the browser open the address of this computer."
fi
hlaska "Je to běžné http, port 80. Za adresu se číslo portu nepíše." "It is ordinary http, port 80. The port number is not written after the address."
hlaska "PISM je nainstalované." "PISM is installed."
