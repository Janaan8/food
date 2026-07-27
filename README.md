# Food

Persoonlijke voedingsplanning voor spieropbouw: wekelijks 4 gerecht-opties met echte AH-prijzen, meal prep (ma t/m do), afvinkbare boodschappenlijst, voorraadbeheer en bonus-alerts.

## Onderdelen

- `index.html` — mobiele webapp met 5 tabbladen: **Kies** (4 weekopties met prijs/eiwit), **Lijst** (boodschappen met afvinken en bonusbadges), **Recept**, **Voorraad**, **Historie**. Keuze en vinkjes staan in localStorage op het toestel.
- `data/week.json` — de 4 opties van de huidige week, inclusief ingrediënten met prijzen en wat al in voorraad is.
- `data/pantry.json` — wat er in huis is (met houdbaarheid); telt niet mee in de prijs van nieuwe gerechten.
- `data/history.json` — archief van gekozen gerechten per week.
- `data/products.json` — bonus-watchlist met AH-product-id's; `houdbaar: true` items krijgen een "sla in voor later"-advies als ze in de bonus zijn.
- `scripts/update_bonus.py` — haalt dagelijks prijzen op via de AH-api en schrijft `bonus.json` (fail-closed: bij storing blijft oude data staan).
- `.github/workflows/bonus.yml` — dagelijkse cron voor de bonus-check.

Installeren als app: open de GitHub Pages-link op je telefoon en kies "Toevoegen aan beginscherm".
