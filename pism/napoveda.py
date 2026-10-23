# -*- coding: utf-8 -*-
"""PISM: texty nápovědy."""


def texty():
    return {"casti": [
        {
            "nazev": "Síť",
            "odstavce": [
                "Tady se nastavuje, jak je PI4 v síti. Vidíš jméno zařízení, kabel, Wi-Fi a společné nastavení.",
                "Jméno zařízení se uloží a zůstane i po restartu.",
                "U kabelu i u Wi-Fi se volí adresa z routeru, nebo pevná adresa, maska a brána.",
                "Společně se volí, kudy se chodí ven, a dva DNS. Platí pro kabel i pro Wi-Fi a zůstanou po restartu.",
                "Když je kabel zapojený, ven se chodí kabelem a Wi-Fi je potlačená. Uložená síť a její heslo zůstanou. Připojení Wi-Fi při zapojeném kabelu síť uloží a hned ji potlačí. Když kabel po restartu není, Wi-Fi se sama přihlásí.",
            ],
        },
        {
            "nazev": "Disky",
            "odstavce": [
                "Karty jsou pod sebou. Systémová karta, každý datový disk a zrcadlo mají každá vlastní kartu. Pod nimi je Přidat disk a BETA RAID.",
                "Systémová karta je jen informace. Ukáže volné místo. Upravit u ní není, SMART nemá a sdílená složka na ni nejde. Kdo s ní chce něco dělat, udělá to sám přes SSH.",
                "Datový disk ukáže model, velikost a volné místo. Řádek obsazeno se neukazuje. Když je datových disků víc, každý má vlastní kartu.",
                "Upravit u datového disku smaže jen ten disk a složky na něm. Ostatní disky a jejich složky zůstanou. Nejdřív se napíše SMAZAT. Systémová karta zůstane.",
                "Přidat disk ukáže každý funkční disk na USB, který ještě není datový. U každého jde přidat jen sdílení, RAID se tím nezaloží. Po SMAZAT se smaže jen ten vybraný a stane se z něj datový disk. Ostatní disky zůstanou. Když žádný takový disk není, okno řekne, že disk k dispozici není.",
                "Zrcadlo má vlastní kartu. Řekne, jestli je v pořádku a oba disky jedou, nebo že je oslabené, protože jeden disk chybí. Každý disk ze zrcadla je na vlastním řádku a má vlastní SMART. Připojit k tomu není potřeba. Když zrcadlo není připojené, složka na něj nejde. Připojit ho připojí vedle datového disku, po restartu tam zůstane a pak je vidět volné místo. Nic se nemaže a datový disk zůstane.",
                "U datového disku je SMART vedle Upravit. U zrcadla ho má každý disk zvlášť. Stav je Výborný, Dobrý, nebo Špatný. Pod tím je teplota, jak dlouho disk běží a jestli má poškozená místa. Když to z disku nejde přečíst, okno to řekne a stav nevymyslí.",
            ],
        },
        {
            "nazev": "BETA RAID USB",
            "odstavce": [
                "Tlačítko nejdřív řekne, že jde o software RAID a jaké potíže nese přes USB. Konfigurace se otevře až po větě, že to bereš na vědomí. To varování se ukáže při každém otevření.",
                "V konfiguraci se ukazují jen disky, které mají pár. Disk bez páru v seznamu není. Výrobce může být jiný. Malý rozdíl ve velikosti se bere jako stejná kapacita. Systémová karta se nenabízí. Tři disky stejné kapacity se ukážou všechny a vyberou se z nich dva. Do zrcadla jdou jen dva disky z jednoho páru.",
                "Disk, který už má sdílení, vybrat jde. Před založením se zruší jeho složky a práva uživatelů k nim. Účty zůstanou. Teprve potom se oba disky smažou a založí se zrcadlo. Když se sdílení zrušit nepovede, pole se nezaloží a disky zůstanou.",
                "Když se vyberou dva jiné disky a ten se sdílením se nebere, sdílení zůstane a zrcadlo bude v Diskách vedle něj. Když zrcadlo není připojené, v Diskách ho připojí tlačítko Připojit. Nic se při tom nemaže.",
                "Zavřít bez napsání SMAZAT nic nesmaže. Když dva disky se stejnou kapacitou nejsou, okno jen řekne, co chybí, a založit nejde.",
                "Zrcadlo je jen jedno. Když už je založené, další se nezaloží.",
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
                "Složka leží na datovém disku, nebo na připojeném zrcadle. Když je takových míst víc, při zakládání nové složky se vybere, kam přijde, a seznam ukáže, kde složka leží. Když je místo jen jedno, výběr se neukáže. Dosavadní složka zůstane, kde je. Přesunout ji nejde. Bez disku ji založit nejde.",
                "U jednoho účtu se zvlášť volí přístup ke sdílené složce a zvlášť k FTP. U obojího je nemá přístup, pouze čtení, nebo plný přístup.",
                "Kdo má právo jen ke složce, do FTP se nedostane. Kdo má právo jen k FTP, složku v síti nevidí. Kdo má obojí, dostane se do obou. Pořád jde o jednu složku.",
                "Dosavadní právo, které bylo jedno pro obojí, platí pro obojí, dokud se jedno nezmění.",
                "Smazat složku nejdřív upozorní, že zmizí všechna data uvnitř. Smaže je až druhé tlačítko. Složku nejde vrátit.",
                "Zakládání, ukládání přístupu i mazání chvíli trvá. Okno řekne, že se na tom pracuje, a tlačítko nejde stisknout znovu.",
            ],
        },
        {
            "nazev": "Služby",
            "odstavce": [
                "SSH a FTP jdou zapnout a vypnout. Po potvrzení se to uloží hned a zůstane po restartu.",
                "SSH je přihlášení na PI4. Je jen zapnuté, nebo vypnuté.",
                "FTP pouští účty z PISM jen do složek, ke kterým mají právo k FTP. Kdo nemá právo k FTP u žádné složky, se nepřihlásí. Bez hesla se nikdo nedostane.",
                "Když je FTP vypnuté, nepřipojí se nikdo, i když má u složky právo k FTP.",
            ],
        },
        {
            "nazev": "Datum a čas",
            "odstavce": [
                "Ukazuje, kolik je hodin, jaké je pásmo a jestli čas bere server, nebo je nastavený ručně. Datum v přehledu je česky.",
                "Odkud čas se volí buď ze serveru, nebo ručně. Obojí najednou nejde. Když čas bere server, ruční čas se nepoužije. Když se nastaví ručně, server se vypne, aby hodiny hned zase nepřepsal.",
                "Server se vybírá ze seznamu: Česko, Evropa, Cloudflare nebo Google. Vlastní je pro server, který už máš doma.",
                "Ruční čas je datum a hodina. Po restartu zůstane. Uložením se server vypne.",
                "Časové pásmo je seznam pásem. Předvolené je to, které PI4 právě používá.",
            ],
        },
        {
            "nazev": "Informace o systému",
            "odstavce": [
                "Jen stav PI4. Jméno, verze PISM, zařízení, systém, jádro, Python, čas, jak dlouho běží, teplota a paměť. Stejné číslo verze je v liště za PI4. Systém, jádro a Python se přečtou z PI4 při otevření okna. Volné místo na discích je v Diskách a v rychlém pohledu.",
                "Na ploše vpravo pod žlutou čárou je rychlý pohled. Je tam název v síti, adresa, jestli jde ven kabel nebo Wi-Fi a přenos po síti. Čtení znamená, že si někdo ze složky bere soubory. Zápis znamená, že je do složky posílá. Když nic neběží, obě jsou 0. Dál je tam, jak dlouho PI4 běží, a řádek Procesor s teplotou. Když teplotu nejde přečíst, pohled to řekne. Pak je volné místo na systémové kartě a na datovém disku a u datového disku stav SMART. U zrcadla je jeho stav, po připojení volné místo a SMART každého disku se jménem toho disku. SMART se načte s pohledem. Teplota procesoru a přenos po síti se obnovují samy, dokud je plocha otevřená. Obsazeno se neukazuje. Nic se tím neotevírá. Vidí to i uživatel, který správu nedělá.",
                "Tady se nic nemění. Restart a vypnutí jsou u ikony napájení vpravo nahoře.",
            ],
        },
        {
            "nazev": "Napájení",
            "odstavce": [
                "Jméno přihlášeného není tlačítko. Vedle něj je ikona napájení.",
                "Kliknutí rozbalí Odhlásit, Restartovat a Vypnout. Kdo správu nedělá, vidí jen Odhlásit.",
                "Odhlášení je hned.",
                "Restart a vypnutí nejdřív otevřou okno a řeknou, co se stane. Až pak se potvrdí. Nic se nemaže.",
                "Restart PI4 na chvíli odpojí a pak zase naběhne. Vypnutí ho nechá stát, dokud ho nezapneš.",
            ],
        },
        {
            "nazev": "Zavírání",
            "odstavce": [
                "Když okno jen otevřeš, nic nezměníš a dáš Zavřít, zavře se hned. Nic se neukládá.",
                "Když nějakou hodnotu změníš a dáš Zavřít, naskočí ukládání změn. Změna se uloží a předchozí stránka se znovu načte.",
                "Když uložení trvá déle než odpočet, stránka počká, až opravdu skončí.",
                "Když se uložení nepovede, zůstaneš v okně a uvidíš proč.",
                "Smazání složky, smazání disku a přidání disku jsou změna. Zavřít u disku samo nic nesmaže. Smaže to až tlačítko po napsání SMAZAT.",
            ],
        },
        {
            "nazev": "Aktualizace PISM",
            "odstavce": [
                "PISM se samo podívá, jestli je novější verze. Podívá se, když správce otevře plochu, a znovu nejdřív za den.",
                "Když novější verze je, na ploše přibude ikona Aktualizace PISM. Když není, ikona tam není.",
                "Kliknutí otevře okno. Aktualizovat program nahradí. Účty, složky, disky, zrcadlo i síť zůstanou. Zavřít jen zavře.",
                "Když se nová verze nespustí, zůstane běžet ta současná. Běžný účet ikonu nevidí.",
            ],
        },
        {
            "nazev": "Darovat",
            "odstavce": [
                "PISM jede naplno. Víc disků i zrcadlo jdou používat včetně zápisu. Nic se za dar nezamyká a nic se neodemkne.",
                "Tlačítko Darovat je na ploše správce a je o něco větší. Otevře poděkování a PayPal grossmann@7ruzi.cz. Hodí se třeba 200 Kč, ale potěší i méně.",
                "Stejné okno se při přihlášení správce otevře jen někdy, zhruba při každém čtvrtém. Když se ukázalo nedávno, další přihlášení ho přeskočí. Obnovení stránky ho znovu neotevře. Zavřít jen zavře.",
                "Běžný účet tlačítko ani okno nevidí. V liště za PI4 je číslo verze. Není tam verze ZDARMA ani verze PLNÁ.",
            ],
        },
    ]}
