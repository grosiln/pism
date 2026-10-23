#!/bin/bash
# Jeden instalacni krok PISM. Spousti se z prikazoveho radku, soubor se na PI4 nekopiruje.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Spusť tu větu znovu se sudo na začátku."
  exit 1
fi

echo "PISM se stahuje a instaluje. Je potřeba internet."

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3 samba smartmontools mdadm curl ca-certificates tar

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://github.com/grosiln/pism/archive/refs/heads/main.tar.gz" -o "$TMP/pism.tar.gz"
tar -xzf "$TMP/pism.tar.gz" -C "$TMP"
ZDROJ="$TMP/pism-main/pism"
CIL="/home/pi/pism"

if [ ! -f "$ZDROJ/server.py" ]; then
  echo "Instalace nenašla program."
  exit 1
fi

install -d -m 755 /home/pi "$CIL" "$CIL/web" "$CIL/data"

for soubor in \
  server.py stroj.py raid.py licence.py dar.py napoveda.py cas.py sdileni.py sit.py vetrak.py \
  pism-sit pism.service pism-vetrak.service pism-sit.service grosistudio-logo.png
do
  if [ -f "$ZDROJ/$soubor" ]; then
    install -m 644 "$ZDROJ/$soubor" "$CIL/$soubor"
  fi
done
chmod 755 "$CIL/pism-sit"

for soubor in index.html app.js style.css; do
  install -m 644 "$ZDROJ/web/$soubor" "$CIL/web/$soubor"
done

groupadd -f pism

install -m 755 "$CIL/pism-sit" /usr/local/sbin/pism-sit
if [ -d /etc/NetworkManager/dispatcher.d ]; then
  install -m 755 "$CIL/pism-sit" /etc/NetworkManager/dispatcher.d/99-pism-sit
fi

install -m 644 "$CIL/pism.service" /etc/systemd/system/pism.service
install -m 644 "$CIL/pism-vetrak.service" /etc/systemd/system/pism-vetrak.service
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
systemctl enable --now pism-vetrak.service
systemctl enable --now pism-sit.service

if [ -f "$CIL/data/uzivatele.json" ]; then
  echo "Dosavadní účty a složky zůstaly."
else
  echo "PISM je prázdné. Nejsou v něm účty, sdílené složky ani připojené disky."
  echo "První otevření v prohlížeči si řekne o heslo správce."
fi

adresa="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -n "${adresa:-}" ]; then
  echo "V prohlížeči otevři http://$adresa"
else
  echo "V prohlížeči otevři adresu tohoto PI4."
fi
echo "Je to běžné http, port 80. Za adresu se číslo portu nepíše."
echo "PISM je nainstalované."
