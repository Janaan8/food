"""Haalt actuele prijzen en bonusaanbiedingen op via de AH-api en schrijft bonus.json.

Draait dagelijks via GitHub Actions (.github/workflows/bonus.yml).
De webapp (index.html) leest bonus.json en toont badges bij producten in de bonus.
"""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.ah.nl"
HEADERS = {
    "User-Agent": "Appie/8.22.3",
    "X-Application": "AHWEBSHOP",
}

ROOT = Path(__file__).resolve().parent.parent


def get_token() -> str:
    req = urllib.request.Request(
        f"{API}/mobile-auth/v1/auth/token/anonymous",
        data=json.dumps({"clientId": "appie"}).encode(),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["access_token"]


def search(token: str, query: str) -> list[dict]:
    url = f"{API}/mobile-services/product/search/v2?query={urllib.parse.quote(query)}&size=20"
    req = urllib.request.Request(
        url, headers={**HEADERS, "Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp).get("products", [])


def main() -> int:
    watchlist = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    token = get_token()

    out_items = []
    for item in watchlist["items"]:
        try:
            products = search(token, item["query"])
        except Exception as e:  # noqa: BLE001 - één mislukte zoekopdracht mag de rest niet blokkeren
            print(f"WAARSCHUWING: zoekopdracht '{item['query']}' mislukt: {e}", file=sys.stderr)
            continue
        by_id = {p.get("webshopId"): p for p in products}
        for wid in item["ids"]:
            p = by_id.get(wid)
            if not p:
                continue
            out_items.append(
                {
                    "key": item["key"],
                    "id": wid,
                    "title": p.get("title"),
                    "size": p.get("salesUnitSize"),
                    "price": p.get("priceBeforeBonus"),
                    "bonusPrice": p.get("currentPrice"),
                    "isBonus": bool(p.get("isBonus")),
                    "mechanism": p.get("bonusMechanism"),
                }
            )

    result = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": out_items,
    }
    (ROOT / "bonus.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    bonus_count = sum(1 for i in out_items if i["isBonus"])
    print(f"bonus.json geschreven: {len(out_items)} producten, {bonus_count} in de bonus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
