# -*- coding: utf-8 -*-
"""PISM: texty nápovědy pro běžný 64bitový počítač."""


def texty():
    return {"casti": [
        {
            "nazev": "Síť",
            "odstavce": [
                "Tady se nastavuje, jak je zařízení v síti. Vidíš jméno, kabel, Wi-Fi a společné nastavení.",
                "Jméno zařízení se uloží a zůstane i po restartu.",
                "U kabelu i u Wi-Fi se volí adresa z routeru, nebo pevná adresa, maska a brána.",
                "Společně se volí, kudy se chodí ven, a dva DNS. Platí pro kabel i pro Wi-Fi a zůstanou po restartu.",
                "Když je kabel zapojený, ven se chodí kabelem a Wi-Fi je potlačená. Uložená síť a její heslo zůstanou. Když kabel po restartu není, Wi-Fi se sama přihlásí.",
            ],
        },
        {
            "nazev": "Disky",
            "odstavce": [
                "Karty jsou pod sebou. Systémový disk, každý datový disk a zrcadlo mají každá vlastní kartu. Pod nimi je Přidat disk a BETA RAID.",
                "Způsob připojení je jen informace. Může být USB, SATA, NVMe, SAS, eMMC, nebo neznámé. Podle něj se disk nevyřazuje.",
                "Systémový disk je jen informace. Pozná se podle toho, že na něm běží systém, ne podle jména. Ukáže volné místo. Odebrat ani Formát u něj není a sdílená složka na něj nejde.",
                "Datový disk ukáže model, velikost, způsob připojení a volné místo. Když je datových disků víc, každý má vlastní kartu.",
                "Odebrat disk vyřadí z PISM. Složky na něm ze seznamu zmizí. V okně je zaškrtnutí Smazat data na disku. Bez zaškrtnutí data na disku zůstanou a jiný Linux je přečte přímo. Se zaškrtnutím se data smažou. Potvrzení je ODEBRAT.",
                "Formát je bokem, vedle Odebrat. Formát disk smaže a data nejdou vrátit. Disk v PISM zůstane, jen prázdný. Potvrzení je SMAZAT.",
                "Přidat disk ukáže disky, které ještě nejsou v PISM a nejsou systémové. Po SMAZAT se smaže jen ten vybraný a stane se z něj datový disk. RAID se tím nezaloží.",
                "Zrcadlo má vlastní kartu. Řekne, jestli je v pořádku a oba disky jedou, nebo že je oslabené, protože jeden disk chybí. Každý disk ze zrcadla má vlastní SMART.",
                "Odebrat zrcadlo ho vyřadí z PISM. Zaškrtnutí Smazat data na discích je stejné jako u disku. Bez zaškrtnutí data zůstanou. Jiný Linux je přečte, když zrcadlo znovu složí. Potvrzení je ODEBRAT.",
                "Formát zrcadla je bokem. Zrcadlo smaže a data nejdou vrátit. Zrcadlo v PISM zůstane, jen prázdné. Potvrzení je SMAZAT.",
                "SMART je vedle Odebrat a Formát. Stav je Výborný, Dobrý, nebo Špatný. Když to z disku nejde přečíst, okno to řekne a stav nevymyslí.",
            ],
        },
        {
            "nazev": "Zrcadlo",
            "odstavce": [
                "Tlačítko nejdřív řekne, že jde o software RAID. Když jsou mezi disky USB, ukáže i potíže USB. Konfigurace se otevře až po větě, že to bereš na vědomí.",
                "RAID není záloha. Smazaný soubor nebo chybný zápis je na discích v poli.",
                "V konfiguraci se ukazují jen disky, které mají pár stejné kapacity. Systémový disk se nenabízí. Do zrcadla jdou jen dva disky.",
                "Zavřít bez napsání SMAZAT nic nesmaže. Zrcadlo je jen jedno. Další se nezaloží, dokud se tohle neodebere.",
            ],
        },
        {
            "nazev": "Uživatelé",
            "odstavce": [
                "Správce spravuje celé PISM. Uživatel slouží ke složkám a službám a správu nedělá. Ikony správy nevidí.",
                "Přidat založí účet a zvolí, jestli je správce, nebo uživatel.",
                "Upravit mění typ účtu a heslo. Heslo se změní, jen když se vyplní. Prázdné pole heslo nechá.",
                "Posledního správce nejde změnit na uživatele ani smazat.",
                "Smazání účtu účet odebere. Složky zůstanou.",
            ],
        },
        {
            "nazev": "Sdílené složky",
            "odstavce": [
                "Složka leží na datovém disku, nebo na připojeném zrcadle. Když je takových míst víc, při zakládání nové složky se vybere, kam přijde. Když je místo jen jedno, výběr se neukáže. Dosavadní složka zůstane, kde je. Bez disku ji založit nejde.",
                "U jednoho účtu se zvlášť volí přístup ke sdílené složce a zvlášť k FTP. U obojího je nemá přístup, pouze čtení, nebo plný přístup.",
                "Kdo má právo jen ke složce, do FTP se nedostane. Kdo má právo jen k FTP, složku v síti nevidí.",
                "Smazat složku nejdřív upozorní, že zmizí všechna data uvnitř. Smaže je až druhé tlačítko. Složku nejde vrátit.",
            ],
        },
        {
            "nazev": "Služby",
            "odstavce": [
                "SSH a FTP jdou zapnout a vypnout. Po potvrzení se to uloží hned a zůstane po restartu.",
                "SSH je přihlášení na zařízení. Je jen zapnuté, nebo vypnuté.",
                "FTP pouští účty z PISM jen do složek, ke kterým mají právo k FTP. Kdo nemá právo k FTP u žádné složky, se nepřihlásí. Bez hesla se nikdo nedostane.",
                "Když je FTP vypnuté, nepřipojí se nikdo, i když má u složky právo k FTP.",
            ],
        },
        {
            "nazev": "Datum a čas",
            "odstavce": [
                "Ukazuje, kolik je hodin, jaké je pásmo a jestli čas bere server, nebo je nastavený ručně.",
                "Odkud čas se volí buď ze serveru, nebo ručně. Obojí najednou nejde. Když čas bere server, ruční čas se nepoužije. Když se nastaví ručně, server se vypne, aby hodiny hned zase nepřepsal.",
                "Časové pásmo je seznam pásem. Předvolené je to, které zařízení právě používá.",
            ],
        },
        {
            "nazev": "Informace o systému",
            "odstavce": [
                "Je tu jméno, verze PISM, zařízení, systém, jádro, Python, čas, jak dlouho běží, teplota, paměť a větrák. V liště je značka stroje, číslo verze a bíle datum, kdy verze vyšla.",
                "Větrák Raspberry Pi na tomto počítači není.",
                "Na ploše vpravo pod žlutou čárou je rychlý pohled. Je tam název v síti, adresa, jestli jde ven kabel nebo Wi-Fi, přenos, jak dlouho zařízení běží a teplota procesoru. Pak volné místo a SMART. Vidí to i uživatel, který správu nedělá.",
            ],
        },
        {
            "nazev": "Napájení",
            "odstavce": [
                "Jméno přihlášeného není tlačítko. Vedle něj je ikona napájení.",
                "Kliknutí rozbalí Odhlásit, Restartovat a Vypnout. Kdo správu nedělá, vidí jen Odhlásit.",
                "Restart zařízení na chvíli odpojí a pak zase naběhne. Vypnutí ho nechá stát, dokud ho nezapneš. Nic se nemaže.",
            ],
        },
        {
            "nazev": "Zavírání",
            "odstavce": [
                "Když okno jen otevřeš, nic nezměníš a dáš Zavřít, zavře se hned. Nic se neukládá.",
                "Když nějakou hodnotu změníš a dáš Zavřít, naskočí ukládání změn. Změna se uloží a předchozí stránka se znovu načte.",
                "Smazání složky, odebrání, formát a přidání disku jsou změna. Zavřít samo nic neprovede. Odebrání se potvrdí slovem ODEBRAT. Formát, přidání disku a založení zrcadla slovem SMAZAT.",
            ],
        },
        {
            "nazev": "Aktualizace PISM",
            "odstavce": [
                "PISM se samo podívá, jestli je novější verze. Podívá se, když správce otevře plochu, a znovu nejdřív za den.",
                "Když novější verze je, na ploše přibude ikona Aktualizace PISM. Když není, ikona tam není.",
                "Aktualizovat vymění program. Účty, složky, disky, zrcadlo i síť zůstanou. Větrák Raspberry Pi se na tomto počítači nezapne. Když se nová verze nespustí, zůstane běžet ta současná.",
            ],
        },
        {
            "nazev": "GrosiStudio",
            "odstavce": [
                "Ikona je na ploše správce, za Nápovědou a před Darovat.",
                "Kliknutí otevře v prohlížeči nové okno na https://7ruzi.cz/grosistudio. PISM zůstane otevřené.",
                "Běžný účet ikonu nevidí.",
            ],
        },
        {
            "nazev": "Darovat",
            "odstavce": [
                "PISM jede naplno. Víc disků i zrcadlo jdou používat včetně zápisu. Nic se za dar nezamyká a nic se neodemkne.",
                "Tlačítko Darovat je na ploše správce. Otevře poděkování a PayPal grossmann@7ruzi.cz. Mail je v okně tučně. Hodí se třeba 200 Kč, ale potěší i méně.",
                "Běžný účet tlačítko ani okno nevidí.",
            ],
        },
    ]}
