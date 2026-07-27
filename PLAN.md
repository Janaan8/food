# Plan: Audit van Food-project (weekmenu-webapp + bonus-pipeline)

## Goal
Onafhankelijke review van het zojuist gebouwde project: mobiele weekmenu-webapp op GitHub Pages plus dagelijkse AH-bonusprijzen-pipeline. Doel: bugs, robuustheidsproblemen en onderhoudsrisico's vinden voordat dit dagelijks gebruikt wordt.

## Context
- `index.html` — statische mobiele webapp (PWA-light): afvinkbare boodschappenlijst (localStorage, key `weekmenu-2026-07-27`), recept-tab, weekplan-tab, bonuskaart die `bonus.json` fetcht en BONUS-badges op lijstitems zet.
- `manifest.json` + `icon.svg` — beginscherm-installatie op telefoon.
- `data/products.json` — watchlist: per lijstitem AH `webshopId`s van varianten.
- `scripts/update_bonus.py` — Python, stdlib-only. Haalt anoniem token op bij api.ah.nl, zoekt per watchlist-item, filtert op webshopId, schrijft `bonus.json`.
- `.github/workflows/bonus.yml` — dagelijkse cron (05:00 UTC) + workflow_dispatch; draait het script en commit `bonus.json` bij wijziging.
- Hosting: GitHub Pages vanaf `main`, public repo `Janaan8/food`.
- `Weekmenu 2026-07-27.md` / `README.md` — documentatie, geen code.
- Gebruiker: één persoon, telefoon, wekelijkse meal prep. Geen build-stap, geen dependencies — dat zo houden.

## Approach
Dit is een audit-run: de implementatie bestaat al en draait live. Codex reviewt read-only tegen dit plan; bevindingen worden geprioriteerd (MUST-FIX / SHOULD-FIX / NICE-TO-HAVE) en daarna eventueel door Codex gefixt in een vervolgfase.

## Tasks
1. [x] Webapp met afvinkbare lijst, recept en weekplan — **Done when:** vinkjes overleven page reload (localStorage), drie tabs werken, site live op https://janaan8.github.io/food/
2. [x] PWA-installeerbaar — **Done when:** manifest + icoon aanwezig, "Zet op beginscherm" geeft standalone app
3. [x] Bonus-pipeline — **Done when:** `python scripts/update_bonus.py` schrijft geldige `bonus.json` met actuele prijzen en bonusvlaggen
4. [x] Dagelijkse automatisering — **Done when:** GitHub Action draait op cron, commit alleen bij wijziging, eerste run groen
5. [x] Bonusweergave in app — **Done when:** bonuskaart toont deals + datum; lijstitems met bonusvariant krijgen badge; app blijft werken als bonus.json ontbreekt

### Fix-ronde na Codex-audit
6. [x] Script fail-closed maken — **Done when:** `update_bonus.py` retryt 429/5xx met backoff (max 3 pogingen), telt per item of alle watchlist-items gedekt zijn, en exit nonzero ZONDER bonus.json te overschrijven als dekking incompleet is of het token faalt
7. [x] Commit alleen bij echte wijziging — **Done when:** script vergelijkt nieuwe items-payload met bestaande bonus.json (timestamp genegeerd) en laat bestand ongemoeid als items identiek zijn; `updated` verandert dus alleen mee met echte prijswijzigingen
8. [x] Frontend-hardening bonusdata — **Done when:** `Array.isArray(data.items)` gecheckt, prijsvelden alleen gerenderd als eindig getal (anders regel zonder prijsinfo), elk deal-item in eigen try/catch zodat één kapot item de rest niet blokkeert
9. [x] Stale-indicator — **Done when:** als `updated` ouder is dan 3 dagen toont de bonuskaart een zichtbare waarschuwing ("laatste check kan verouderd zijn: <datum>"), en de kaart verschijnt óók (met alleen die melding) wanneer er geen deals zijn maar de data vers is, zodat "geen bonus" te onderscheiden is van "check mislukt"
10. [x] localStorage-guard — **Done when:** geparste waarde wordt alleen gebruikt als het een non-null plain object is; anders schone start zonder exception
11. [x] Workflow-safeguards — **Done when:** bonus.yml heeft `timeout-minutes`, een `concurrency`-group (geen dubbele runs), en `git pull --rebase` vóór push zodat een tussentijdse push de bot niet breekt
12. [x] Verificatie — **Done when:** `python scripts/update_bonus.py` draait lokaal foutloos en tweede run direct erna wijzigt bonus.json niet (taak 7 bewezen)

### Feature-ronde 2 (gebouwd, te auditen)
13. [x] Week-keuzesysteem — **Done when:** `data/week.json` bevat 4 opties (4 keukens) met ingrediënten, AH-prijzen, eiwit en recept; Kies-tab toont kaarten met totaal/p.p./eiwit/tijd; keuze in localStorage per weekId
14. [x] Boodschappenlijst per keuze — **Done when:** Lijst-tab rendert ingrediënten van gekozen optie per categorie met vinkjes (localStorage per week+optie), totaal, en "Al in huis"-sectie uit `uitVoorraad`
15. [x] Voorraad — **Done when:** `data/pantry.json` + Voorraad-tab; voorraaditems tellen niet mee in gerechtprijzen
16. [x] Historie — **Done when:** `data/history.json` (repo-archief) samengevoegd met lokale keuzes (localStorage), gededuplicaat per weekId (lokaal wint), nieuwste eerst
17. [x] Inslaan-advies — **Done when:** products.json heeft `houdbaar`-vlag, script geeft die door aan bonus.json, app toont "Sla in voor later" bij houdbare bonusitems
18. [x] Retro-restyle — **Done when:** crème/terracotta + Fraunces serif (Google Fonts), donkere variant via prefers-color-scheme, 5 tabs, bestaande robuustheid (fail-closed, guards) intact

### Fix-ronde na audit 2
19. [x] Week-schema validatie + render-isolatie — **Done when:** week.json wordt bij laden gevalideerd/genormaliseerd (opties-array; per optie: string key, naam, ingredienten/uitVoorraad/recept als arrays — ongeldige opties overgeslagen; ingrediënt zonder eindige prijs → prijs 0 en geen crash), en elke render-functie draait geïsoleerd zodat één kapotte tab de rest niet blokkeert
20. [x] Bonusdata-onderscheid — **Done when:** bonus-object zonder geldige items-array toont "Bonusdata niet beschikbaar" i.p.v. "Geen gevolgde producten in de bonus"
21. [x] Geldrekenen in centen — **Done when:** totalen en prijs p.p. in integer centen berekend (ook wat naar historie gaat); oosterse optie toont €4,28 p.p.

### Bewust uitgesteld (niet in deze ronde)
- Data-duplicatie index.html ↔ data/products.json samenvoegen (pak ik mee bij volgend weekmenu)
- ARIA-tabs/hash-state, SHA-pinning van actions, PWA-icoontest

## Out of scope
- Lunch/ontbijt-functionaliteit (bewust uitgesteld door gebruiker)
- Accounts, sync tussen apparaten, backend
- Frameworks, build-tooling, npm — project blijft dependency-vrij
- Offline service worker

## Verification
- Review-bevindingen met file:line, geprioriteerd
- Na eventuele fixes: `python scripts/update_bonus.py` draait foutloos; site geeft 200; bonuskaart rendert
