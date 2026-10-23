const vstup = document.querySelector("#vstup");
const plocha = document.querySelector("#plocha");
const formular = document.querySelector("#formular");
const nadpis = document.querySelector("#vstup-nadpis");
const popis = document.querySelector("#vstup-popis");
const ucetPole = document.querySelector("#ucet-pole");
const ucetVstup = document.querySelector("#ucet");
const heslo = document.querySelector("#heslo");
const znovuPole = document.querySelector("#znovu-pole");
const znovu = document.querySelector("#znovu");
const hlaseni = document.querySelector("#hlaseni");
const odeslat = document.querySelector("#odeslat");
const ikony = document.querySelector("#ikony");
const kdo = document.querySelector("#kdo");
const okno = document.querySelector("#okno");
const oknoNazev = document.querySelector("#okno-nazev");
const oknoTelo = document.querySelector("#okno-telo");
const oknoHlaseni = document.querySelector("#okno-hlaseni");
const edit = document.querySelector("#edit");
const editNazev = document.querySelector("#edit-nazev");
const editTelo = document.querySelector("#edit-telo");
const editHlaseni = document.querySelector("#edit-hlaseni");
const editZavrit = document.querySelector("#edit-zavrit");
const oknoZavrit = document.querySelector("#zavrit");
const bezSpravy = document.querySelector("#bez-spravy");
let behOdpocet = 0;
let cekaNaUlozeni = false;
let ulozitRozpracovane = null;
let jeZmena = null;
let poNavratu = null;
let obnovitSekci = null;
let opustitStranku = false;
const PROC_CEKANI = "Změny se ukládají, aby byly potom vidět. Až odpočet skončí, stránka se znovu načte.";

let prvni = false;
let sitZprava = "";
let casZprava = "";
let smartBeh = 0;
odeslat.disabled = true;

const tvary = {
  sit: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><circle cx="10" cy="24" r="4" fill="currentColor"/><circle cx="24" cy="10" r="4" fill="currentColor"/><circle cx="38" cy="24" r="4" fill="currentColor"/><circle cx="24" cy="38" r="4" fill="currentColor"/><path d="M13 21 L21 13 M27 13 L35 21 M35 27 L27 35 M21 35 L13 27" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
  disky: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><ellipse cx="24" cy="14" rx="14" ry="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 14 v16 c0 3.3 6.3 6 14 6 s14-2.7 14-6 V14" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 22 c0 3.3 6.3 6 14 6 s14-2.7 14-6" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  uzivatele: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><circle cx="24" cy="16" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 38 c2-8 8-12 14-12 s12 4 14 12" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  slozky: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><path d="M6 16 h12 l4 4 h20 v16 H6 z" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  sluzby: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><rect x="8" y="8" width="14" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><rect x="26" y="28" width="14" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M15 20 v8 h18 v-8" fill="none" stroke="currentColor" stroke-width="2"/></svg>',
  cas: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><circle cx="24" cy="24" r="14" fill="none" stroke="currentColor" stroke-width="2"/><path d="M24 14 v11 l7 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  system: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><circle cx="24" cy="24" r="14" fill="none" stroke="currentColor" stroke-width="2"/><path d="M24 20 v12" stroke="currentColor" stroke-width="2"/><circle cx="24" cy="15" r="1.6" fill="currentColor"/></svg>',
  napoveda: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><circle cx="24" cy="24" r="14" fill="none" stroke="currentColor" stroke-width="2"/><path d="M18 19 a6 6 0 1 1 8 5 c-2 1.4-2 2-2 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="24" cy="33" r="1.6" fill="currentColor"/></svg>',
  dar: '<svg viewBox="0 0 48 48" width="40" height="40" aria-hidden="true"><path d="M24 40 s-12-7.4-16.5-14.2C4.2 21.2 6.2 15 11.6 13.6 15.4 12.6 18.6 14.2 24 19.2c5.4-5 8.6-6.6 12.4-5.6 5.4 1.4 7.4 7.6 4.1 12.2C36 32.6 24 40 24 40z" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linejoin="round"/></svg>',
  aktualizace: '<svg viewBox="0 0 48 48" width="34" height="34" aria-hidden="true"><path d="M16 18 a12 12 0 1 1-2 10" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 12 v8 h8" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
};

const panely = {
  sit: nactiSit,
  disky: nactiDisky,
  uzivatele: nactiUzivatele,
  slozky: nactiSlozky,
  sluzby: nactiSluzby,
  cas: nactiCas,
  system: nactiSystem,
  napoveda: nactiNapovedu,
  dar: nactiDar,
  aktualizace: nactiAktualizace
};

function el(tag, attrs, deti) {
  const uzel = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([klic, hodnota]) => {
    if (klic === "text") uzel.textContent = hodnota;
    else if (klic === "class") uzel.className = hodnota;
    else uzel[klic] = hodnota;
  });
  (deti || []).forEach((dite) => uzel.append(dite));
  return uzel;
}

function ukazHlaseni(text) {
  hlaseni.textContent = text || "";
}

function ukazOknoHlaseni(text) {
  oknoHlaseni.textContent = text || "";
}

function ukazEditHlaseni(text) {
  editHlaseni.textContent = text || "";
}

function zavriEdit() {
  ulozitRozpracovane = null;
  jeZmena = null;
  poNavratu = null;
  edit.classList.add("skryte");
  editTelo.replaceChildren();
  ukazEditHlaseni("");
}

function zrusOdpocet() {
  behOdpocet += 1;
  cekaNaUlozeni = false;
  editZavrit.disabled = false;
  editZavrit.textContent = "Zavřít";
  oknoZavrit.disabled = false;
  oknoZavrit.textContent = "Zavřít";
}

function pripravUlozeni(funkce, zmena) {
  ulozitRozpracovane = funkce || null;
  jeZmena = typeof zmena === "function" ? zmena : null;
  poNavratu = null;
}

function textOdpocet(zbyva) {
  return zbyva > 0 ? "Ukládám změny… " + zbyva : "Ukládám změny… ještě chvíli";
}

function hlaskaOdpocet(zbyva) {
  return PROC_CEKANI + (zbyva > 0 ? " " + zbyva : "");
}

async function odejitSUlozenim(nahrazeni) {
  if (cekaNaUlozeni) return;
  const vynuceno = typeof nahrazeni === "function";
  const ulozit = vynuceno ? nahrazeni : ulozitRozpracovane;
  if (!vynuceno && !(jeZmena && jeZmena())) {
    zavriEdit();
    return;
  }
  const beh = ++behOdpocet;
  cekaNaUlozeni = true;
  opustitStranku = false;
  const zamcene = [];
  editTelo.querySelectorAll("button, input, select, textarea").forEach((uzel) => {
    zamcene.push([uzel, uzel.disabled]);
    uzel.disabled = true;
  });
  editZavrit.disabled = true;
  let zbyva = 10;
  let ulozeno = !ulozit;
  let selhani = null;
  function kresli() {
    editZavrit.textContent = textOdpocet(zbyva);
    ukazEditHlaseni(hlaskaOdpocet(zbyva));
  }
  kresli();
  const start = Date.now();
  if (ulozit) {
    Promise.resolve().then(ulozit).then(() => {
      ulozeno = true;
    }).catch((chyba) => {
      selhani = chyba;
      ulozeno = true;
    });
  }
  await new Promise((resolve) => {
    const casovac = setInterval(() => {
      if (beh !== behOdpocet) {
        clearInterval(casovac);
        resolve();
        return;
      }
      zbyva = Math.max(0, 10 - Math.floor((Date.now() - start) / 1000));
      kresli();
      if (selhani || opustitStranku || (Date.now() - start >= 10000 && ulozeno)) {
        clearInterval(casovac);
        resolve();
      }
    }, 200);
  });
  if (beh !== behOdpocet || opustitStranku) return;
  if (selhani) {
    cekaNaUlozeni = false;
    editZavrit.disabled = false;
    editZavrit.textContent = "Zavřít";
    zamcene.forEach(([uzel, byl]) => { uzel.disabled = byl; });
    ukazEditHlaseni(selhani.message || "Nepovedlo se.");
    return;
  }
  const navrat = poNavratu;
  cekaNaUlozeni = false;
  editZavrit.disabled = false;
  editZavrit.textContent = "Zavřít";
  zavriEdit();
  nactiPrehled();
  try {
    if (navrat) await navrat();
    else if (obnovitSekci) await obnovitSekci();
  } catch (chyba) {
    ukazOknoHlaseni(chyba.message);
  }
}

function odejitZPrehledu() {
  if (cekaNaUlozeni) return;
  if (!edit.classList.contains("skryte")) {
    odejitSUlozenim();
    return;
  }
  ukazOknoHlaseni("");
  if (jeZmena && jeZmena()) {
    odejitSUlozenim();
    return;
  }
  ulozitRozpracovane = null;
  jeZmena = null;
  okno.classList.add("skryte");
  nactiPrehled();
}

function otevriEdit(nazev, obsah) {
  zastavMereni();
  editNazev.textContent = nazev;
  ukazEditHlaseni("");
  editTelo.replaceChildren(obsah);
  edit.classList.remove("skryte");
}

function tlacitkoUpravit(otevrit) {
  const tlacitko = el("button", { type: "button", className: "male", textContent: "Upravit" });
  tlacitko.addEventListener("click", (udalost) => {
    udalost.stopPropagation();
    otevrit();
  });
  return tlacitko;
}

function ukazVstup(jePrvni) {
  prvni = jePrvni;
  plocha.classList.add("skryte");
  okno.classList.add("skryte");
  zrusOdpocet();
  zavriEdit();
  zastavMereni();
  vstup.classList.remove("skryte");
  nadpis.textContent = jePrvni ? "První spuštění" : "Přihlášení";
  popis.textContent = jePrvni
    ? "Zvol heslo správce. Účet bude admin."
    : "Napiš účet a heslo.";
  ucetPole.classList.toggle("skryte", jePrvni);
  ucetVstup.required = !jePrvni;
  znovuPole.classList.toggle("skryte", !jePrvni);
  znovu.required = jePrvni;
  odeslat.textContent = jePrvni ? "Založit" : "Vstoupit";
  heslo.autocomplete = jePrvni ? "new-password" : "current-password";
  ukazHlaseni("");
  heslo.value = "";
  znovu.value = "";
  if (!jePrvni && !ucetVstup.value) ucetVstup.value = "admin";
  (jePrvni ? heslo : ucetVstup).focus();
}

async function api(cesta, telo) {
  const volby = telo === undefined ? { method: "GET", cache: "no-store" } : {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(telo)
  };
  let data;
  try {
    data = await fetch(cesta, volby).then((odpoved) => odpoved.json());
  } catch (chyba) {
    throw new Error("PISM teď neodpovídá.");
  }
  if (!data.ok) throw new Error(data.hlaseni || "Nepovedlo se.");
  return data;
}

function pole(nadpisText, hodnota) {
  return el("div", { class: "blok" }, [
    el("h3", { text: nadpisText }),
    el("p", { class: "poznamka", text: hodnota || "—" })
  ]);
}

function radekFormulare(deti) {
  return el("div", { class: "rada" }, deti);
}

function udaj(popis, hodnota) {
  return el("div", { class: "udaj" }, [
    el("span", { class: "udaj-nazev", text: popis }),
    el("span", { text: hodnota || "—" })
  ]);
}

function poleRadku(popis, vstup) {
  return el("label", { class: "udaj" }, [
    el("span", { class: "udaj-nazev", text: popis }),
    vstup
  ]);
}

function blokAdresy(nadpisText, rozhrani, sitData) {
  const adresa = el("input", { type: "text", value: sitData.adresa || "" });
  const maska = el("input", { type: "text", value: sitData.maska || "" });
  const brana = el("input", { type: "text", value: sitData.brana || "" });
  const jmenoRadia = "adresa-" + rozhrani;
  const auto = el("input", { type: "radio", name: jmenoRadia, value: "dhcp" });
  const rucne = el("input", { type: "radio", name: jmenoRadia, value: "pevna" });
  if (sitData.rezim === "pevna") rucne.checked = true;
  else auto.checked = true;
  const upozorneni = el("p", { class: "poznamka", text: "" });
  function jeRucne() { return rucne.checked; }
  function prekresli() {
    const zapnuto = jeRucne();
    adresa.disabled = !zapnuto;
    maska.disabled = !zapnuto;
    brana.disabled = !zapnuto;
    const nova = adresa.value.trim();
    if (zapnuto && rozhrani === "lan" && nova && nova !== (sitData.adresa || "")) {
      upozorneni.textContent = "Po potvrzení se to uloží hned a zůstane i po restartu. PISM potom otevři na http://" + nova + ".";
      return;
    }
    upozorneni.textContent = zapnuto
      ? "Po potvrzení se pevná adresa uloží hned a zůstane i po restartu."
      : "Po potvrzení adresu zase dává router. Řádky zůstanou vidět a uložení zůstane i po restartu.";
  }
  auto.addEventListener("change", prekresli);
  rucne.addEventListener("change", prekresli);
  adresa.addEventListener("input", prekresli);
  const tlacitko = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  tlacitko.addEventListener("click", () => odejitSUlozenim());
  pripravUlozeni(async () => {
    const nova = adresa.value.trim();
    const meniLan = rozhrani === "lan" && jeRucne() && nova && nova !== (sitData.adresa || "");
    await api("/api/sit/adresa", {
      rozhrani: rozhrani,
      rezim: jeRucne() ? "pevna" : "dhcp",
      adresa: adresa.value,
      maska: maska.value,
      brana: brana.value
    });
    sitZprava = "Uloženo. Nastavení zůstane i po restartu.";
    if (meniLan && location.hostname === (sitData.adresa || "")) {
      opustitStranku = true;
      location.href = "http://" + nova + "/";
    }
  }, () => {
    const rezim = jeRucne() ? "pevna" : "dhcp";
    const puvodni = sitData.rezim === "pevna" ? "pevna" : "dhcp";
    if (rezim !== puvodni) return true;
    if (rezim !== "pevna") return false;
    return adresa.value.trim() !== (sitData.adresa || "")
      || maska.value.trim() !== (sitData.maska || "")
      || brana.value.trim() !== (sitData.brana || "");
  });
  prekresli();
  const deti = [
    el("h3", { text: nadpisText }),
    el("div", { class: "volby" }, [
      el("label", { class: "volba" }, [auto, el("span", { text: "Získat adresu automaticky" })]),
      el("label", { class: "volba" }, [rucne, el("span", { text: "Nastavit adresu ručně" })])
    ]),
    poleRadku("IP adresa:", adresa),
    poleRadku("maska:", maska),
    poleRadku("brána:", brana),
    udaj("DNS:", sitData.dns1),
    udaj("druhé DNS:", sitData.dns2)
  ];
  if (rozhrani === "wifi") {
    deti.push(udaj("jméno sítě:", sitData.sit), udaj("signál:", sitData.signal));
  }
  deti.push(udaj("stav:", sitData.stav));
  if (!sitData.lze) {
    auto.disabled = true;
    rucne.disabled = true;
    adresa.disabled = true;
    maska.disabled = true;
    brana.disabled = true;
    tlacitko.disabled = true;
    let text = "Kabel není připojený.";
    if (rozhrani === "wifi") {
      text = sitData.potlacena
        ? "Kabel má přednost. Síť je uložená a Wi-Fi je potlačená. Až kabel nebude zapojený, přihlásí se sama."
        : "Nejdřív se připoj k Wi-Fi. Adresa patří k síti, ke které jsi připojený.";
    }
    deti.push(el("p", { class: "poznamka", text: text }));
    pripravUlozeni(null);
  } else {
    deti.push(upozorneni, tlacitko);
  }
  return el("div", { class: "blok" }, deti);
}

function radekPrehledu(nazev, stav, otevrit) {
  return el("tr", {}, [
    el("td", { text: nazev }),
    el("td", { text: stav || "—" }),
    el("td", {}, [tlacitkoUpravit(otevrit)])
  ]);
}

function otevriJmenoSite(data) {
  const puvodniJmeno = data.jmeno || "";
  const jmeno = el("input", { type: "text", value: puvodniJmeno });
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Jméno zařízení", el("div", {}, [
    poleRadku("jméno:", jmeno),
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/sit/jmeno", { jmeno: jmeno.value });
    sitZprava = "Uloženo. Nastavení zůstane i po restartu.";
  }, () => jmeno.value.trim() !== puvodniJmeno.trim());
}

function otevriSpolecne(data) {
  const vychozi = el("select");
  vychozi.append(el("option", { value: "lan", text: "Kabel" }));
  const volbaWifi = el("option", { value: "wifi", text: "Wi-Fi" });
  if (data.kabel) volbaWifi.disabled = true;
  vychozi.append(volbaWifi);
  if (!data.kabel) vychozi.options[0].disabled = true;
  vychozi.value = data.kabel ? "lan" : "wifi";
  const puvodniSit = { vychozi: vychozi.value, dns1: (data.obecne && data.obecne.dns1) || "", dns2: (data.obecne && data.obecne.dns2) || "" };
  const dns1 = el("input", { type: "text", value: (data.obecne && data.obecne.dns1) || "" });
  const dns2 = el("input", { type: "text", value: (data.obecne && data.obecne.dns2) || "" });
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Společné", el("div", {}, [
    poleRadku("ven se chodí přes:", vychozi),
    poleRadku("DNS:", dns1),
    poleRadku("druhé DNS:", dns2),
    el("p", { class: "poznamka", text: "Když je kabel zapojený, Wi-Fi je potlačená. Po restartu bez kabelu se sama přihlásí do uložené sítě. DNS platí pro obojí a zůstane i po restartu." }),
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/sit/obecne", { vychozi: vychozi.value, dns: dns1.value, dns2: dns2.value });
    sitZprava = "Uloženo. Nastavení zůstane i po restartu.";
  }, () => vychozi.value !== puvodniSit.vychozi || dns1.value.trim() !== puvodniSit.dns1.trim() || dns2.value.trim() !== puvodniSit.dns2.trim());
}

function otevriWifiPripojeni() {
  const ssid = el("input", { type: "text", placeholder: "Jméno sítě" });
  const hesloSite = el("input", { type: "password", placeholder: "Heslo sítě", autocomplete: "off" });
  const pripoj = el("button", { type: "button", className: "male", textContent: "Připojit" });
  const hledat = el("button", { type: "button", className: "male", textContent: "Najít sítě" });
  const seznam = el("div", { class: "telo" });
  hledat.addEventListener("click", async () => {
    ukazEditHlaseni("");
    hledat.disabled = true;
    hledat.textContent = "Hledám sítě…";
    seznam.replaceChildren();
    try {
      const site = await api("/api/wifi");
      (site.site || []).forEach((sit) => {
        const tlacitko = el("button", {
          type: "button",
          className: "sit-tlac",
          textContent: sit.ssid + " · signál " + sit.signal
        });
        tlacitko.addEventListener("click", () => { ssid.value = sit.ssid; hesloSite.focus(); });
        seznam.append(el("div", { class: "blok" }, [tlacitko]));
      });
      if (!seznam.childElementCount) seznam.append(el("p", { class: "poznamka", text: "Žádná síť na dosah." }));
    } catch (chyba) {
      ukazEditHlaseni(chyba.message);
    }
    hledat.disabled = false;
    hledat.textContent = "Najít sítě";
  });
  pripoj.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Připojit Wi-Fi", el("div", {}, [
    el("p", { class: "poznamka", text: "Síť se uloží do PI4. Dokud je kabel zapojený, Wi-Fi zůstane potlačená." }),
    radekFormulare([ssid, hesloSite, pripoj]),
    hledat,
    seznam
  ]));
  pripravUlozeni(async () => {
    const vysledek = await api("/api/sit/wifi", { ssid: ssid.value, heslo: hesloSite.value });
    sitZprava = vysledek.wifi && vysledek.wifi.potlacena
      ? "Síť je uložená. Dokud je kabel zapojený, Wi-Fi zůstane potlačená. Až kabel nebude, přihlásí se sama."
      : "Wi-Fi je připojená. Po restartu bez kabelu se přihlásí sama.";
  }, () => ssid.value.trim() !== "" || hesloSite.value !== "");
}

async function nactiSit() {
  const data = await api("/api/sit");
  const spolecne = (data.obecne && data.obecne.vychozi) === "wifi" ? "Wi-Fi" : "Kabel";
  const dns = [data.obecne && data.obecne.dns1, data.obecne && data.obecne.dns2].filter(Boolean).join(", ");
  const wifiStav = data.wifi && data.wifi.potlacena
    ? "potlačená" + (data.wifi.sit ? " · " + data.wifi.sit : "")
    : ((data.wifi && data.wifi.sit) || (data.wifi && data.wifi.stav) || "—");
  const tabulka = el("table", { class: "prehled" });
  tabulka.append(el("thead", {}, [
    el("tr", {}, [el("th", { text: "Položka" }), el("th", { text: "Stav" }), el("th", { text: "" })])
  ]), el("tbody", {}, [
    radekPrehledu("Jméno zařízení", data.jmeno, () => otevriJmenoSite(data)),
    radekPrehledu("Společné", spolecne + (dns ? " · " + dns : ""), () => otevriSpolecne(data)),
    radekPrehledu("Kabel", (data.lan && data.lan.adresa) || (data.lan && data.lan.stav) || "—", () => otevriEdit("Kabel", blokAdresy("Kabel", "lan", data.lan))),
    radekPrehledu("Wi-Fi", wifiStav, () => otevriEdit("Wi-Fi", blokAdresy("Wi-Fi", "wifi", data.wifi))),
    radekPrehledu("Připojit Wi-Fi", "", otevriWifiPripojeni)
  ]));
  const zprava = sitZprava;
  sitZprava = "";
  oknoTelo.replaceChildren(
    ...(zprava ? [el("p", { class: "poznamka na-sirku", text: zprava })] : []),
    el("div", { class: "blok na-sirku" }, [tabulka])
  );
}

function textDisku(disk) {
  if (disk.systemovy) return disk.volno ? "volno " + disk.volno : "—";
  const casti = [disk.model, disk.velikost].filter(Boolean);
  if (disk.volno) casti.push("volno " + disk.volno);
  else if (disk.poznamka) casti.push(disk.poznamka);
  return casti.join(" · ");
}

function popisMista(disk) {
  if (!disk) return "Datový disk";
  if (disk.klic === "zrcadlo" || (disk.cleny && disk.cleny.length)) {
    return ["Zrcadlo", ...(disk.cleny || [])].filter(Boolean).join(" · ");
  }
  return [disk.model, disk.velikost].filter(Boolean).join(" · ") || "Datový disk";
}

function kartaZrcadla(disk) {
  const deti = [el("h3", { text: "Zrcadlo" })];
  if (disk.stav_text) deti.push(el("p", { class: "poznamka", text: disk.stav_text }));
  const cleny = disk.cleny_disky || [];
  if (cleny.length) {
    cleny.forEach((clen) => {
      deti.push(el("div", { class: "rada-disku" }, [
        el("p", { class: "poznamka", text: clen.model }),
        tlacitkoSmart(clen.klic)
      ]));
    });
  } else {
    (disk.cleny || []).forEach((clen) => deti.push(el("p", { class: "poznamka", text: clen })));
  }
  if (disk.velikost) deti.push(el("p", { class: "poznamka", text: disk.velikost }));
  if (disk.pripojeno && disk.volno) deti.push(el("p", { class: "poznamka", text: "volno " + disk.volno }));
  else if (disk.poznamka) deti.push(el("p", { class: "poznamka", text: disk.poznamka }));
  if (!disk.pripojeno) {
    const pripojit = el("button", { type: "button", className: "male", textContent: "Připojit" });
    pripojit.addEventListener("click", async () => {
      pripojit.disabled = true;
      try {
        await api("/api/disky/raid/pripojit", {});
        await nactiDisky();
      } catch (chyba) {
        pripojit.disabled = false;
        ukazOknoHlaseni(chyba.message);
      }
    });
    deti.push(el("div", { class: "akce" }, [pripojit]));
  }
  return el("div", { class: "blok" }, deti);
}

function otevriHlaseniDisku(nazev, text) {
  otevriEdit(nazev, el("div", {}, [el("p", { class: "poznamka", text: text })]));
  pripravUlozeni(null);
}

async function otevriPridatDisk() {
  let data;
  try {
    data = await api("/api/disky");
  } catch (chyba) {
    otevriHlaseniDisku("Přidat disk", chyba.message);
    return;
  }
  const kandidati = data.kandidati || [];
  if (!kandidati.length) {
    otevriHlaseniDisku("Přidat disk", "Není disk k dispozici.");
    return;
  }
  const deti = [el("p", { class: "poznamka", text: "Vyber disk a přidej ho jen pro sdílení. RAID se tím nezaloží. Po SMAZAT se smaže jen ten vybraný. Ostatní disky zůstanou." })];
  kandidati.forEach((disk) => {
    const potvrzeni = el("input", { type: "text", placeholder: "SMAZAT", autocomplete: "off" });
    const ulozit = el("button", { type: "button", className: "nebezpeci", textContent: "Potvrdit a přidat" });
    ulozit.addEventListener("click", () => odejitSUlozenim(async () => {
      if (potvrzeni.value !== "SMAZAT") throw new Error("Pro přidání disku napiš SMAZAT.");
      await api("/api/disky/svazek", { potvrzeni: potvrzeni.value, disk: disk.jmeno });
    }));
    deti.push(
      el("p", { class: "poznamka", text: [disk.model, disk.velikost].filter(Boolean).join(" · ") }),
      radekFormulare([potvrzeni, ulozit])
    );
  });
  otevriEdit("Přidat disk", el("div", {}, deti));
  pripravUlozeni(null);
}

function tlacitkoSmart(klic) {
  const tlacitko = el("button", { type: "button", className: "male", textContent: "SMART" });
  tlacitko.addEventListener("click", (udalost) => {
    udalost.stopPropagation();
    otevriSmart(klic);
  });
  return tlacitko;
}

async function otevriSmart(klic) {
  const beh = ++smartBeh;
  otevriEdit("SMART", el("p", { class: "poznamka", text: "Čtu informace o disku…" }));
  pripravUlozeni(null);
  try {
    const data = await api(klic ? "/api/disky/smart?disk=" + encodeURIComponent(klic) : "/api/disky/smart");
    if (beh !== smartBeh || edit.classList.contains("skryte") || editNazev.textContent !== "SMART") return;
    const deti = [];
    if (data.lze && data.stav_text) deti.push(el("h3", { text: data.stav_text }));
    deti.push(el("p", { class: "poznamka", text: data.veta || "Z tohoto disku SMART nejde přečíst." }));
    if (data.lze) {
      deti.push(pole("Disk", data.model));
      deti.push(pole("Teplota", data.teplota));
      deti.push(pole("V provozu", data.beh));
      deti.push(pole("Poškozená místa", data.mista));
    }
    editTelo.replaceChildren(...deti);
  } catch (chyba) {
    if (beh === smartBeh && !edit.classList.contains("skryte")) ukazEditHlaseni(chyba.message);
  }
}

function otevriSmazaniDisku(klic, model) {
  const potvrzeni = el("input", { type: "text", placeholder: "SMAZAT", autocomplete: "off" });
  const smazat = el("button", { type: "button", className: "nebezpeci", textContent: "Smazat disk" });
  smazat.addEventListener("click", () => odejitSUlozenim(async () => {
    await api("/api/disky/smazat", { potvrzeni: potvrzeni.value, disk: klic || "hlavni" });
  }));
  const nazev = model ? "Datový disk " + model : "Datový disk";
  otevriEdit(nazev, el("div", {}, [
    el("p", { class: "poznamka", text: "Smaže se jen tenhle disk a složky na něm. Ostatní disky a jejich složky zůstanou. Systémová karta zůstane. Nejde to vrátit. Pro potvrzení napiš SMAZAT." }),
    radekFormulare([potvrzeni, smazat])
  ]));
  pripravUlozeni(null);
}

function otevriKonfiguraciRaidu() {
  otevriEdit("Konfigurace soft RAID", el("p", { class: "poznamka", text: "Načítám…" }));
  pripravUlozeni(null);
  api("/api/disky/raid/konfigurace").then((data) => {
    if (edit.classList.contains("skryte") || editNazev.textContent !== "Konfigurace soft RAID") return;
    const deti = (data.vety || []).map((veta) => el("p", { class: "poznamka", text: veta }));
    const boxy = [];
    const vyber = el("div");
    const doplnek = el("p", { class: "poznamka", text: "" });
    (data.disky || []).forEach((disk) => {
      const text = [disk.model, disk.velikost, disk.sdileni ? "má sdílení" : ""].filter(Boolean).join(" · ");
      if (!data.lze) {
        deti.push(el("p", { class: "poznamka", text }));
        return;
      }
      const box = el("input", { type: "checkbox" });
      box.addEventListener("change", () => {
        const oznacene = boxy.filter((polozka) => polozka.box.checked).map((polozka) => polozka.disk);
        const bere = oznacene.some((polozka) => polozka.sdileni);
        if (bere) {
          const nazvy = (data.slozky || []).join(", ");
          doplnek.textContent = nazvy
            ? "Zruší se složky: " + nazvy + ". Práva uživatelů k nim zmizí. Účty zůstanou. Data na obou discích se smažou."
            : "Sdílení na vybraném disku se zruší. Účty zůstanou. Data na obou discích se smažou.";
        } else if (oznacene.length) {
          doplnek.textContent = "Stávající sdílení zůstane. Data na vybraných discích se smažou.";
        } else {
          doplnek.textContent = "";
        }
      });
      boxy.push({ box, disk });
      vyber.append(el("label", { class: "volba" }, [box, el("span", { text })]));
    });
    if (data.lze) {
      const potvrzeni = el("input", { type: "text", placeholder: "SMAZAT", autocomplete: "off" });
      const ulozit = el("button", { type: "button", className: "nebezpeci", textContent: "Potvrdit a založit" });
      ulozit.addEventListener("click", () => odejitSUlozenim(async () => {
        const oznacene = boxy.filter((polozka) => polozka.box.checked).map((polozka) => polozka.disk);
        if (oznacene.length !== 2 || !oznacene[0].klic || oznacene[0].klic !== oznacene[1].klic) {
          throw new Error("Vyber dva disky se stejnou kapacitou.");
        }
        await api("/api/disky/raid/zalozit", {
          potvrzeni: potvrzeni.value,
          disky: oznacene.map((disk) => disk.jmeno)
        });
      }));
      deti.push(vyber, doplnek, el("p", { class: "poznamka", text: "Pro potvrzení napiš SMAZAT." }), radekFormulare([potvrzeni, ulozit]));
    }
    editTelo.replaceChildren(el("div", {}, deti));
    pripravUlozeni(null);
  }).catch((chyba) => {
    if (!edit.classList.contains("skryte")) ukazEditHlaseni(chyba.message);
  });
}

async function otevriBetaRaid() {
  otevriEdit("BETA RAID USB", el("p", { class: "poznamka", text: "Načítám…" }));
  pripravUlozeni(null);
  try {
    const data = await api("/api/disky/raid");
    if (edit.classList.contains("skryte") || editNazev.textContent !== "BETA RAID USB") return;
    const beru = el("button", { type: "button", className: "male", textContent: data.beru });
    beru.addEventListener("click", () => otevriKonfiguraciRaidu());
    editTelo.replaceChildren(el("div", {}, [
      el("p", { class: "poznamka", text: data.uvod || "" }),
      el("p", { class: "poznamka", text: data.upozorneni || "" }),
      ...(data.problemy || []).map((veta) => el("p", { class: "poznamka", text: veta })),
      beru
    ]));
  } catch (chyba) {
    if (!edit.classList.contains("skryte")) ukazEditHlaseni(chyba.message);
  }
}

async function nactiDisky() {
  const data = await api("/api/disky");
  const seznam = el("div", { class: "disky-seznam" });
  (data.disky || []).forEach((disk) => {
    if (disk.zrcadlo) {
      seznam.append(kartaZrcadla(disk));
      return;
    }
    const deti = [
      el("h3", { text: disk.nazev }),
      el("p", { class: "poznamka", text: textDisku(disk) })
    ];
    if (!disk.systemovy) {
      deti.push(el("div", { class: "akce" }, [
        tlacitkoUpravit(() => otevriSmazaniDisku(disk.klic, disk.model)),
        tlacitkoSmart(disk.klic)
      ]));
    }
    seznam.append(el("div", { class: "blok" }, deti));
  });
  const pridat = el("button", { type: "button", className: "male", textContent: "Přidat disk" });
  const raid = el("button", { type: "button", className: "male", textContent: "BETA RAID USB" });
  pridat.addEventListener("click", () => otevriPridatDisk());
  raid.addEventListener("click", () => otevriBetaRaid());
  oknoTelo.replaceChildren(
    el("div", { class: "na-sirku" }, [seznam]),
    el("div", { class: "akce na-sirku" }, [pridat, raid])
  );
}

let uzivateleVyber = "";
let uzivateleSeznam = [];

function typText(typ) {
  return typ === "spravce" ? "správce" : "uživatel";
}

function posledniSpravce(ucet) {
  const spravci = uzivateleSeznam.filter((polozka) => polozka.typ === "spravce");
  return ucet.typ === "spravce" && spravci.length <= 1;
}

function vykresliUzivatele() {
  const tabulka = el("table", { class: "prehled" });
  const telo = el("tbody");
  uzivateleSeznam.forEach((ucet) => {
    const radek = el("tr", {}, [
      el("td", { text: ucet.ucet }),
      el("td", { text: typText(ucet.typ) })
    ]);
    if (ucet.ucet === uzivateleVyber) radek.classList.add("vybrano");
    radek.addEventListener("click", () => {
      uzivateleVyber = ucet.ucet;
      vykresliUzivatele();
    });
    radek.addEventListener("dblclick", () => {
      uzivateleVyber = ucet.ucet;
      otevriUcet(ucet);
    });
    telo.append(radek);
  });
  tabulka.append(el("thead", {}, [
    el("tr", {}, [el("th", { text: "Účet" }), el("th", { text: "Typ" })])
  ]), telo);
  const pridat = el("button", { type: "button", className: "male", textContent: "Přidat" });
  const upravit = el("button", { type: "button", className: "male", textContent: "Upravit", disabled: !uzivateleVyber });
  pridat.addEventListener("click", otevriNovyUcet);
  upravit.addEventListener("click", () => {
    const ucet = uzivateleSeznam.find((polozka) => polozka.ucet === uzivateleVyber);
    if (ucet) otevriUcet(ucet);
  });
  oknoTelo.replaceChildren(el("div", { class: "blok na-sirku" }, [
    tabulka,
    el("div", { class: "akce" }, [pridat, upravit])
  ]));
}

async function nactiUzivatele() {
  const data = await api("/api/uzivatele");
  uzivateleSeznam = (data.ucty || []).slice().sort((a, b) => {
    if (a.typ !== b.typ) return a.typ === "spravce" ? -1 : 1;
    return a.ucet.localeCompare(b.ucet, "cs");
  });
  if (!uzivateleSeznam.some((ucet) => ucet.ucet === uzivateleVyber)) uzivateleVyber = "";
  vykresliUzivatele();
}

function volbaTypu(aktualni, posledni) {
  const spravce = el("input", { type: "radio", name: "typ-uctu", value: "spravce" });
  const uzivatel = el("input", { type: "radio", name: "typ-uctu", value: "uzivatel" });
  spravce.checked = aktualni === "spravce";
  uzivatel.checked = aktualni !== "spravce";
  if (posledni) uzivatel.disabled = true;
  return { spravce, uzivatel, blok: el("div", { class: "volby" }, [
    el("label", { class: "volba" }, [spravce, el("span", { text: "Správce" })]),
    el("label", { class: "volba" }, [uzivatel, el("span", { text: "Uživatel" })])
  ]) };
}

function otevriNovyUcet() {
  const jmeno = el("input", { type: "text", placeholder: "Účet" });
  const hesloUctu = el("input", { type: "password", placeholder: "Heslo", autocomplete: "new-password" });
  const typ = volbaTypu("uzivatel", false);
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Nový účet", el("div", {}, [
    el("p", { class: "poznamka", text: "Správce spravuje PISM. Uživatel slouží ke složkám a službám." }),
    poleRadku("účet:", jmeno),
    poleRadku("heslo:", hesloUctu),
    poleRadku("typ účtu:", typ.blok),
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/uzivatele", {
      ucet: jmeno.value,
      heslo: hesloUctu.value,
      typ: typ.spravce.checked ? "spravce" : "uzivatel"
    });
    uzivateleVyber = jmeno.value.trim().toLowerCase();
  }, () => jmeno.value.trim() !== "" || hesloUctu.value !== "" || typ.spravce.checked);
}

function otevriUcet(ucet) {
  const posledni = posledniSpravce(ucet);
  const typ = volbaTypu(ucet.typ, posledni);
  const nove = el("input", { type: "password", placeholder: "Nové heslo", autocomplete: "new-password" });
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  const smazat = el("button", {
    type: "button",
    className: "nebezpeci",
    textContent: "Smazat uživatele",
    disabled: posledni
  });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  smazat.addEventListener("click", () => odejitSUlozenim(async () => {
    await api("/api/uzivatele/smazat", { ucet: ucet.ucet });
    if (uzivateleVyber === ucet.ucet) uzivateleVyber = "";
  }));
  otevriEdit("Účet " + ucet.ucet, el("div", {}, [
    poleRadku("typ účtu:", typ.blok),
    poleRadku("nové heslo:", nove),
    el("p", { class: "poznamka", text: posledni
      ? "Posledního správce nejde změnit na uživatele ani smazat. Heslo vyplň, jen když ho měníš."
      : "Heslo vyplň, jen když ho měníš. Smazání nechá složky být a přístup k nim zmizí." }),
    el("div", { class: "akce" }, [ulozit, smazat])
  ]));
  pripravUlozeni(async () => {
    const novyTyp = typ.spravce.checked ? "spravce" : "uzivatel";
    await api("/api/uzivatele/upravit", { ucet: ucet.ucet, typ: novyTyp, heslo: nove.value });
    if (ucet.ucet === kdo.textContent && novyTyp === "uzivatel") {
      poNavratu = async () => {
        okno.classList.add("skryte");
        await nacti();
      };
    }
  }, () => nove.value !== "" || (typ.spravce.checked ? "spravce" : "uzivatel") !== (ucet.typ === "spravce" ? "spravce" : "uzivatel"));
}

function volbaPrava(aktualni) {
  const vyber = el("select");
  [["nic", "nemá přístup"], ["cteni", "pouze čtení"], ["zapis", "plný přístup"]].forEach(([hodnota, text]) => {
    const moznost = el("option", { value: hodnota, text: text });
    if (hodnota === aktualni) moznost.selected = true;
    vyber.append(moznost);
  });
  return vyber;
}

function textPrava(pravo) {
  if (pravo === "zapis") return "plný přístup";
  if (pravo === "cteni") return "pouze čtení";
  return "nemá přístup";
}

function pravoKanalu(hodnota, kanal) {
  if (typeof hodnota === "string") return hodnota || "nic";
  if (hodnota && typeof hodnota === "object") return hodnota[kanal] || "nic";
  return "nic";
}

function souhrnPrav(prava, ucty) {
  const casti = [];
  (ucty || []).forEach((ucet) => {
    const hodnota = prava[ucet.ucet];
    const slozka = pravoKanalu(hodnota, "slozka");
    const ftp = pravoKanalu(hodnota, "ftp");
    const kusy = [];
    if (slozka !== "nic") kusy.push("složka " + textPrava(slozka));
    if (ftp !== "nic") kusy.push("FTP " + textPrava(ftp));
    if (kusy.length) casti.push(ucet.ucet + " " + kusy.join(", "));
  });
  return casti.join("; ") || "nikdo";
}

function otevriNovouSlozku(disky) {
  const nazev = el("input", { type: "text", placeholder: "Jméno složky" });
  const seznam = disky || [];
  const volba = seznam.length > 1 ? el("select") : null;
  if (volba) {
    seznam.forEach((disk) => {
      volba.append(el("option", {
        value: disk.klic,
        text: popisMista(disk)
      }));
    });
  }
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  const deti = [poleRadku("jméno:", nazev)];
  if (volba) deti.push(poleRadku("místo:", volba));
  deti.push(ulozit);
  otevriEdit("Nová složka", el("div", {}, deti));
  pripravUlozeni(
    () => api("/api/slozky", { nazev: nazev.value, disk: volba ? volba.value : ((seznam[0] && seznam[0].klic) || "") }),
    () => nazev.value.trim() !== ""
  );
}

function otevriSlozku(nazev, prava, ucty) {
  const volby = (ucty || []).map((ucet) => {
    const hodnota = prava[ucet.ucet];
    const slozka = volbaPrava(pravoKanalu(hodnota, "slozka"));
    const ftp = volbaPrava(pravoKanalu(hodnota, "ftp"));
    return {
      ucet: ucet.ucet,
      slozka,
      ftp,
      blok: el("div", {}, [
        el("h3", { text: ucet.ucet }),
        poleRadku("sdílená složka:", slozka),
        poleRadku("FTP:", ftp)
      ])
    };
  });
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  const smazat = el("button", { type: "button", className: "nebezpeci", textContent: "Smazat složku" });
  const varovani = el("p", {
    class: "poznamka skryte",
    text: "Smazáním složky " + nazev + " zmizí všechna data uvnitř. Složka se nedá vrátit."
  });
  const potvrdit = el("button", { type: "button", className: "nebezpeci skryte", textContent: "Smazat i s daty" });
  function mapaPrav() {
    const mapa = {};
    volby.forEach((polozka) => {
      mapa[polozka.ucet] = { slozka: polozka.slozka.value, ftp: polozka.ftp.value };
    });
    return mapa;
  }
  ulozit.addEventListener("click", () => odejitSUlozenim());
  smazat.addEventListener("click", () => {
    varovani.classList.remove("skryte");
    potvrdit.classList.remove("skryte");
    smazat.disabled = true;
  });
  potvrdit.addEventListener("click", () => odejitSUlozenim(() => api("/api/slozky/smazat", { nazev })));
  otevriEdit("Složka " + nazev, el("div", {}, [
    el("p", { class: "poznamka", text: "U jednoho účtu se sdílená složka a FTP nastavují zvlášť." }),
    ...volby.map((polozka) => polozka.blok),
    el("div", { class: "akce" }, [ulozit, smazat]),
    varovani,
    potvrdit
  ]));
  const puvodniPrava = volby.map((polozka) => ({ slozka: polozka.slozka.value, ftp: polozka.ftp.value }));
  pripravUlozeni(
    () => api("/api/slozky/prava", { nazev, prava: mapaPrav() }),
    () => volby.some((polozka, poradi) => polozka.slozka.value !== puvodniPrava[poradi].slozka || polozka.ftp.value !== puvodniPrava[poradi].ftp)
  );
}

async function nactiSlozky() {
  const [data, ucty] = await Promise.all([api("/api/slozky"), api("/api/uzivatele")]);
  const casti = [];
  if (!data.svazek) {
    casti.push(el("p", { class: "poznamka na-sirku", text: "Nejdřív v Diskách založ svazek." }));
  }
  const diskySlozek = data.disky || [];
  const vicDisku = diskySlozek.length > 1;
  const nazevDisku = (klic) => {
    const nalezeny = diskySlozek.find((disk) => disk.klic === (klic || "hlavni"));
    return popisMista(nalezeny);
  };
  const telo = el("tbody");
  Object.entries(data.slozky || {}).forEach(([nazev, zaznam]) => {
    const prava = (zaznam && zaznam.prava) || {};
    const bunky = [el("td", { text: nazev })];
    if (vicDisku) bunky.push(el("td", { text: nazevDisku(zaznam && zaznam.disk) }));
    bunky.push(el("td", { text: souhrnPrav(prava, ucty.ucty) }));
    bunky.push(el("td", {}, [tlacitkoUpravit(() => otevriSlozku(nazev, prava, ucty.ucty))]));
    telo.append(el("tr", {}, bunky));
  });
  const hlavicka = [el("th", { text: "Složka" })];
  if (vicDisku) hlavicka.push(el("th", { text: "Místo" }));
  hlavicka.push(el("th", { text: "Přístup" }), el("th", { text: "" }));
  const tabulka = el("table", { class: "prehled" });
  tabulka.append(el("thead", {}, [el("tr", {}, hlavicka)]), telo);
  casti.push(el("div", { class: "blok na-sirku" }, [tabulka]));
  if (data.svazek) {
    const pridat = el("button", { type: "button", className: "male", textContent: "Přidat" });
    pridat.addEventListener("click", () => otevriNovouSlozku(diskySlozek));
    casti.push(el("div", { class: "akce" }, [pridat]));
  }
  oknoTelo.replaceChildren(...casti);
}

function otevriZdrojCasu(data) {
  const zeServeru = el("input", { type: "radio", name: "zdroj-casu" });
  const rucne = el("input", { type: "radio", name: "zdroj-casu" });
  zeServeru.checked = !!data.ntp;
  rucne.checked = !data.ntp;
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Odkud čas", el("div", {}, [
    el("p", { class: "poznamka", text: "Buď čas bere server, nebo se nastaví ručně. Obojí najednou nejde." }),
    el("label", { class: "volba" }, [zeServeru, el("span", { text: "Ze serveru" })]),
    el("label", { class: "volba" }, [rucne, el("span", { text: "Ručně" })]),
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/cas/zdroj", { ntp: zeServeru.checked });
    casZprava = "Uloženo. Nastavení zůstane i po restartu.";
  }, () => zeServeru.checked !== !!data.ntp);
}

function otevriServerCasu(data) {
  const volba = el("select");
  (data.servery || []).forEach((server) => volba.append(el("option", { value: server.id, text: server.nazev })));
  volba.append(el("option", { value: "vlastni", text: "Vlastní" }));
  volba.value = data.volba || "cesko";
  const adresa = el("input", { type: "text", value: data.volba === "vlastni" ? (data.server || "") : "", placeholder: "Adresa serveru" });
  function kresli() { adresa.classList.toggle("skryte", volba.value !== "vlastni"); }
  volba.addEventListener("change", kresli);
  kresli();
  const puvodniVolba = volba.value;
  const puvodniAdresa = adresa.value.trim();
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("NTP server", el("div", {}, [
    el("p", { class: "poznamka", text: "Server se použije, když čas bere server. Ruční čas ho nepotřebuje." }),
    volba,
    adresa,
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/cas/server", { volba: volba.value, adresa: adresa.value });
    casZprava = "Uloženo. Nastavení zůstane i po restartu.";
  }, () => volba.value !== puvodniVolba || (volba.value === "vlastni" && adresa.value.trim() !== puvodniAdresa));
}

function otevriRucniCas(data) {
  const datum = el("input", { type: "date", value: data.datum || "" });
  const hodina = el("input", { type: "time", value: data.hodina || "" });
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Ruční čas", el("div", {}, [
    el("p", { class: "poznamka", text: "Uložením se server vypne a platí tento čas. Po restartu zůstane." }),
    poleRadku("datum:", datum),
    poleRadku("hodina:", hodina),
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/cas/rucne", { datum: datum.value, hodina: hodina.value });
    casZprava = "Uloženo. Čas je ruční a zůstane i po restartu.";
  }, () => datum.value !== (data.datum || "") || hodina.value !== (data.hodina || ""));
}

function otevriPasmo(data) {
  const pasmo = el("select");
  (data.pasma || []).forEach((nazev) => pasmo.append(el("option", { value: nazev, text: nazev })));
  if (data.pasmo) pasmo.value = data.pasmo;
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit("Časové pásmo", el("div", {}, [
    pasmo,
    ulozit
  ]));
  pripravUlozeni(async () => {
    await api("/api/cas/pasmo", { pasmo: pasmo.value });
    casZprava = "Uloženo. Pásmo zůstane i po restartu.";
  }, () => pasmo.value !== (data.pasmo || ""));
}

function ceskyCas(datum, hodina) {
  const text = String(datum || "").trim();
  const iso = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  const cas = /^\d{2}:\d{2}$/.test(hodina || "") ? hodina : "";
  if (iso) return Number(iso[3]) + ". " + Number(iso[2]) + ". " + iso[1] + (cas ? " " + cas : "");
  const hotovy = text.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{2}:\d{2}))?$/);
  if (hotovy) return Number(hotovy[1]) + ". " + Number(hotovy[2]) + ". " + hotovy[3] + (hotovy[4] ? " " + hotovy[4] : "");
  return [text, cas].filter(Boolean).join(" ") || "—";
}

async function nactiCas() {
  const data = await api("/api/cas");
  const tabulka = el("table", { class: "prehled" });
  tabulka.append(el("thead", {}, [
    el("tr", {}, [el("th", { text: "Položka" }), el("th", { text: "Stav" }), el("th", { text: "" })])
  ]), el("tbody", {}, [
    el("tr", {}, [
      el("td", { text: "Teď" }),
      el("td", { text: ceskyCas(data.ted) }),
      el("td", { text: "" })
    ]),
    radekPrehledu("Odkud čas", data.ntp ? "ze serveru" : "ručně", () => otevriZdrojCasu(data)),
    radekPrehledu("NTP server", data.server_nazev, () => otevriServerCasu(data)),
    radekPrehledu("Ruční čas", ceskyCas(data.datum, data.hodina), () => otevriRucniCas(data)),
    radekPrehledu("Časové pásmo", data.pasmo, () => otevriPasmo(data))
  ]));
  const zprava = casZprava;
  casZprava = "";
  oknoTelo.replaceChildren(
    ...(zprava ? [el("p", { class: "poznamka na-sirku", text: zprava })] : []),
    el("div", { class: "blok na-sirku" }, [tabulka])
  );
}

async function nactiDar() {
  const data = await api("/api/dar");
  oknoTelo.replaceChildren(el("div", { class: "na-sirku" },
    (data.vety || []).map((veta) => el("p", { class: "poznamka", text: veta }))
  ));
  pripravUlozeni(null);
}

async function pockejNaNovouVerzi(cil) {
  let videlMezeru = false;
  for (let krok = 0; krok < 40; krok += 1) {
    try {
      const stav = await fetch("/api/stav", { cache: "no-store" }).then((odpoved) => odpoved.json());
      if (stav && stav.ok && cil && stav.verze === cil && (videlMezeru || krok > 3)) return true;
      if (stav && stav.ok && !cil && videlMezeru) return true;
      if (stav && stav.ok && cil && stav.verze !== cil) videlMezeru = true;
    } catch (chyba) {
      videlMezeru = true;
    }
    await new Promise((konec) => setTimeout(konec, 1000));
  }
  return false;
}

async function nactiAktualizace() {
  const data = await api("/api/aktualizace");
  const deti = (data.vety || []).map((veta) => el("p", { class: "poznamka", text: veta }));
  if (data.lze) {
    const tlacitko = el("button", { type: "button", className: "male", textContent: "Aktualizovat" });
    tlacitko.addEventListener("click", async () => {
      tlacitko.disabled = true;
      ukazOknoHlaseni("Aktualizuji…");
      try {
        await api("/api/aktualizace", {});
        ukazOknoHlaseni("PISM se obnovuje. Stránka se načte znovu a budeš se muset přihlásit.");
        const hotovo = await pockejNaNovouVerzi(data.nova || "");
        if (!hotovo) {
          tlacitko.disabled = false;
          ukazOknoHlaseni("Aktualizace se nedokončila. Obnov stránku.");
          return;
        }
        sessionStorage.setItem("pism-po-aktualizaci", "1");
        location.reload();
      } catch (chyba) {
        tlacitko.disabled = false;
        ukazOknoHlaseni(chyba.message);
      }
    });
    deti.push(tlacitko);
  }
  oknoTelo.replaceChildren(el("div", { class: "na-sirku" }, deti));
  pripravUlozeni(null);
}

async function nactiSystem() {
  const data = await api("/api/system");
  oknoTelo.replaceChildren(
    pole("Jméno", data.jmeno),
    pole("Verze PISM", data.verze),
    pole("Zařízení", data.model),
    pole("Systém", data.system || "nejde zjistit"),
    pole("Jádro", data.jadro || "nejde zjistit"),
    pole("Python", data.python || "nejde zjistit"),
    pole("Čas", data.cas),
    pole("Běží", data.beh),
    pole("Teplota", data.teplota),
    pole("Paměť", data.pamet)
  );
}

function nactiNapovedu() {
  oknoTelo.replaceChildren(el("p", { class: "poznamka na-sirku", text: "Načítám…" }));
  api("/api/napoveda").then((data) => {
    if (okno.classList.contains("skryte") || oknoNazev.textContent !== "Nápověda") return;
    const casti = data.casti || [];
    const seznam = el("div", { class: "napoveda-seznam" });
    const vypis = el("div", { class: "napoveda-vypis" });
    function ukaz(poradi) {
      seznam.querySelectorAll("button").forEach((tlacitko, index) => {
        tlacitko.classList.toggle("vybrano", index === poradi);
      });
      const cast = casti[poradi] || {};
      const odstavce = cast.odstavce || [];
      vypis.replaceChildren(
        el("h3", { text: cast.nazev || "" }),
        ...odstavce.map((veta) => el("p", { class: "poznamka", text: veta }))
      );
    }
    casti.forEach((cast, poradi) => {
      const tlacitko = el("button", { type: "button", textContent: cast.nazev });
      tlacitko.addEventListener("click", () => ukaz(poradi));
      seznam.append(tlacitko);
    });
    oknoTelo.replaceChildren(el("div", { class: "napoveda na-sirku" }, [seznam, vypis]));
    if (casti.length) ukaz(0);
  }).catch((chyba) => {
    oknoTelo.replaceChildren();
    ukazOknoHlaseni(chyba.message);
  });
}

function otevriSluzbu(sluzba) {
  const zap = el("input", { type: "radio", name: "stav-sluzby" });
  const vyp = el("input", { type: "radio", name: "stav-sluzby" });
  zap.checked = !!sluzba.zapnuto;
  vyp.checked = !sluzba.zapnuto;
  const ulozit = el("button", { type: "button", className: "male", textContent: "Potvrdit a uložit" });
  ulozit.addEventListener("click", () => odejitSUlozenim());
  otevriEdit(sluzba.nazev, el("div", {}, [
    udaj("stav:", sluzba.stav),
    udaj("port:", String(sluzba.port)),
    el("div", { class: "volby" }, [
      el("label", { class: "volba" }, [zap, el("span", { text: "Zapnout" })]),
      el("label", { class: "volba" }, [vyp, el("span", { text: "Vypnout" })])
    ]),
    el("p", { class: "poznamka", text: sluzba.poznamka || "" }),
    ulozit
  ]));
  const puvodniSluzba = !!sluzba.zapnuto;
  pripravUlozeni(
    () => api("/api/sluzby", { id: sluzba.id, zapnuto: zap.checked }),
    () => zap.checked !== puvodniSluzba
  );
}

async function nactiSluzby() {
  const data = await api("/api/sluzby");
  const telo = el("tbody");
  (data.polozky || []).forEach((sluzba) => {
    telo.append(el("tr", {}, [
      el("td", { text: sluzba.nazev }),
      el("td", { text: sluzba.stav }),
      el("td", { text: String(sluzba.port) }),
      el("td", {}, [tlacitkoUpravit(() => otevriSluzbu(sluzba))])
    ]));
  });
  const tabulka = el("table", { class: "prehled" });
  tabulka.append(el("thead", {}, [
    el("tr", {}, [
      el("th", { text: "Služba" }),
      el("th", { text: "Stav" }),
      el("th", { text: "Port" }),
      el("th", { text: "" })
    ])
  ]), telo);
  oknoTelo.replaceChildren(el("div", { class: "blok na-sirku" }, [tabulka]));
}

async function otevri(polozka) {
  if (cekaNaUlozeni) return;
  zastavMereni();
  pripravUlozeni(null);
  zavriEdit();
  obnovitSekci = panely[polozka.id] || nactiSystem;
  oknoNazev.textContent = polozka.nazev;
  ukazOknoHlaseni("");
  oknoTelo.replaceChildren(el("p", { class: "poznamka na-sirku", text: "Načítám…" }));
  okno.classList.remove("skryte");
  try {
    await (panely[polozka.id] || nactiSystem)();
  } catch (chyba) {
    oknoTelo.replaceChildren();
    ukazOknoHlaseni(chyba.message);
  }
}

let prehledBeh = 0;

function textDiskuPrehledu(disk) {
  if (disk.poznamka && !disk.volno && !disk.smart) return disk.poznamka;
  const casti = [];
  if (disk.volno) casti.push("volno " + disk.volno);
  if (disk.smart) {
    casti.push(disk.smart_cele ? disk.smart : (disk.smart === "nejde přečíst" ? "SMART nejde přečíst" : "SMART " + disk.smart));
  }
  if (disk.poznamka && !disk.volno) casti.push(disk.poznamka);
  return casti.join(" · ") || "—";
}

function radekPrehleduPlochy(nazev, hodnota) {
  return el("p", { class: "prehled-radek" }, [
    el("span", { class: "prehled-nazev", text: nazev }),
    el("span", { text: hodnota || "—" })
  ]);
}

let prehledCasovac = 0;
let prehledMereniBezi = false;

function textPrenosu(data) {
  return "čtení " + (data.cteni || "0") + " · zápis " + (data.zapis || "0");
}

function textTeploty(data) {
  return data.teplota || "nejde zjistit";
}

function plochaJeVolna() {
  return !plocha.classList.contains("skryte")
    && okno.classList.contains("skryte")
    && edit.classList.contains("skryte");
}

function zastavMereni() {
  if (prehledCasovac) {
    clearInterval(prehledCasovac);
    prehledCasovac = 0;
  }
}

function spustMereni() {
  zastavMereni();
  if (!plochaJeVolna()) return;
  prehledCasovac = setInterval(() => {
    if (!plochaJeVolna()) {
      zastavMereni();
      return;
    }
    if (prehledMereniBezi) return;
    prehledMereniBezi = true;
    api("/api/prehled/rychlost").then((data) => {
      if (!plochaJeVolna()) return;
      const prenos = document.querySelector("#prehled-prenos");
      const teplota = document.querySelector("#prehled-teplota");
      if (prenos) prenos.textContent = textPrenosu(data);
      if (teplota) teplota.textContent = textTeploty(data);
    }).catch(() => {}).finally(() => {
      prehledMereniBezi = false;
    });
  }, 2000);
}

async function nactiPrehled() {
  const box = document.querySelector("#prehled");
  if (!box) return;
  const beh = ++prehledBeh;
  if (!box.childElementCount) box.textContent = "Načítám…";
  try {
    const data = await api("/api/prehled");
    if (beh !== prehledBeh || plocha.classList.contains("skryte")) return;
    const sitni = [data.adresa, data.spojeni].filter(Boolean).join(" · ");
    const radky = [
      el("h2", { class: "prehled-nadpis", text: "Přehled" }),
      radekPrehleduPlochy("Název", data.jmeno),
      radekPrehleduPlochy("Síť", sitni),
      el("p", { class: "prehled-radek" }, [
        el("span", { class: "prehled-nazev", text: "Přenos" }),
        el("span", { id: "prehled-prenos", text: textPrenosu(data) })
      ]),
      radekPrehleduPlochy("Běží", data.beh),
      el("p", { class: "prehled-radek" }, [
        el("span", { class: "prehled-nazev", text: "Procesor" }),
        el("span", { id: "prehled-teplota", text: textTeploty(data) })
      ]),
      radekPrehleduPlochy("Systémová karta", data.karta ? "volno " + data.karta : "—")
    ];
    (data.disky || []).forEach((disk) => radky.push(radekPrehleduPlochy(disk.nazev, textDiskuPrehledu(disk))));
    box.replaceChildren(...radky);
    spustMereni();
  } catch (chyba) {
    if (beh !== prehledBeh) return;
    box.textContent = chyba.message || "Přehled teď nejde načíst.";
  }
}

function ukazPlochu(ucet, polozky, spravce, verze) {
  vstup.classList.add("skryte");
  plocha.classList.remove("skryte");
  document.querySelector("#verze").textContent = verze ? "verze " + verze : "";
  kdo.textContent = ucet;
  bezSpravy.classList.toggle("skryte", !!spravce);
  document.querySelectorAll(".jen-spravce").forEach((uzel) => uzel.classList.toggle("skryte", !spravce));
  document.querySelector("#napajeni-menu").classList.add("skryte");
  nactiPrehled();
  ikony.replaceChildren();
  polozky.forEach((polozka) => {
    const tlacitko = document.createElement("button");
    tlacitko.type = "button";
    tlacitko.className = polozka.id === "dar"
      ? "ikona ikona-vetsi"
      : (polozka.id === "aktualizace" ? "ikona ikona-aktualizace" : "ikona");
    const tvar = document.createElement("span");
    tvar.className = "ikona-tvar";
    tvar.innerHTML = tvary[polozka.id] || "";
    const nazev = document.createElement("span");
    nazev.className = "ikona-nazev";
    nazev.textContent = polozka.nazev;
    tlacitko.append(tvar, nazev);
    tlacitko.addEventListener("click", () => otevri(polozka));
    ikony.append(tlacitko);
  });
}

async function nacti() {
  if (sessionStorage.getItem("pism-po-aktualizaci")) {
    sessionStorage.removeItem("pism-po-aktualizaci");
    try {
      await fetch("/api/odhlaseni", { method: "POST" });
    } catch (chyba) {
      /* Odhlášení doběhne po načtení. */
    }
  }
  odeslat.disabled = true;
  let stav;
  try {
    stav = await fetch("/api/stav", { cache: "no-store" }).then((odpoved) => odpoved.json());
  } catch (chyba) {
    ukazVstup(false);
    ukazHlaseni("PISM teď neodpovídá. Spusť ho znovu.");
    odeslat.disabled = false;
    return;
  }
  if (!stav.prihlasen) {
    ukazVstup(stav.prvni);
    odeslat.disabled = false;
    return false;
  }
  if (!stav.spravce) {
    ukazPlochu(stav.ucet, [], false, stav.verze);
    odeslat.disabled = false;
    return false;
  }
  const plochaOdpoved = await fetch("/api/plocha", { cache: "no-store" }).then((odpoved) => odpoved.json());
  ukazPlochu(stav.ucet, plochaOdpoved.polozky || [], true, stav.verze);
  return false;
}

formular.addEventListener("submit", async (udalost) => {
  udalost.preventDefault();
  ukazHlaseni("");
  if (!prvni && !ucetVstup.value.trim()) {
    ukazHlaseni("Napiš účet.");
    return;
  }
  const adresa = prvni ? "/api/prvni" : "/api/prihlaseni";
  const telo = prvni
    ? { heslo: heslo.value, znovu: znovu.value }
    : { ucet: ucetVstup.value.trim(), heslo: heslo.value };
  let data;
  try {
    data = await fetch(adresa, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(telo)
    }).then((odpoved) => odpoved.json());
  } catch (chyba) {
    ukazHlaseni("PISM teď neodpovídá. Spusť ho znovu.");
    return;
  }
  if (!data.ok) {
    ukazHlaseni(data.hlaseni || "Nepovedlo se.");
    return;
  }
  await nacti();
  if (data.dar) otevri({ id: "dar", nazev: "Děkuji" });
});

document.querySelector("#odhlasit").addEventListener("click", async () => {
  document.querySelector("#napajeni-menu").classList.add("skryte");
  await fetch("/api/odhlaseni", { method: "POST" });
  await nacti();
});

document.querySelector("#napajeni").addEventListener("click", (udalost) => {
  udalost.stopPropagation();
  document.querySelector("#napajeni-menu").classList.toggle("skryte");
});

document.addEventListener("click", () => {
  document.querySelector("#napajeni-menu").classList.add("skryte");
});

function otevriNapajeni(restart) {
  document.querySelector("#napajeni-menu").classList.add("skryte");
  const potvrdit = el("button", {
    type: "button",
    className: "nebezpeci",
    textContent: restart ? "Potvrdit a restartovat" : "Potvrdit a vypnout"
  });
  potvrdit.addEventListener("click", async () => {
    potvrdit.disabled = true;
    ukazEditHlaseni("");
    try {
      await api(restart ? "/api/system/restart" : "/api/system/vypnout", {});
      editTelo.replaceChildren(el("p", {
        class: "poznamka",
        text: restart
          ? "PI4 se restartuje. Za chvíli se sem vrať."
          : "PI4 se vypíná. Naběhne, až ho znovu zapneš."
      }));
    } catch (chyba) {
      potvrdit.disabled = false;
      ukazEditHlaseni(chyba.message);
    }
  });
  otevriEdit(restart ? "Restartovat" : "Vypnout", el("div", {}, [
    el("p", {
      class: "poznamka",
      text: restart
        ? "PI4 se na chvíli odpojí a pak zase naběhne. Nic se nemaže."
        : "PI4 se vypne a zůstane stát, dokud ho nezapneš. Nic se nemaže."
    }),
    potvrdit
  ]));
  pripravUlozeni(null);
}

document.querySelector("#restartovat").addEventListener("click", () => otevriNapajeni(true));
document.querySelector("#vypnout").addEventListener("click", () => otevriNapajeni(false));

oknoZavrit.addEventListener("click", () => {
  if (cekaNaUlozeni) return;
  odejitZPrehledu();
});

editZavrit.addEventListener("click", () => {
  if (cekaNaUlozeni) return;
  odejitSUlozenim();
});

document.addEventListener("keydown", (udalost) => {
  if (udalost.key !== "Escape" || cekaNaUlozeni) return;
  const menu = document.querySelector("#napajeni-menu");
  if (!menu.classList.contains("skryte") && edit.classList.contains("skryte") && okno.classList.contains("skryte")) {
    menu.classList.add("skryte");
    return;
  }
  if (!edit.classList.contains("skryte")) odejitSUlozenim();
  else if (!okno.classList.contains("skryte")) odejitZPrehledu();
});

nacti();
