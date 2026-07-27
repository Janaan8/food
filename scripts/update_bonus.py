"""Haalt actuele prijzen en bonusaanbiedingen op via de AH-api en schrijft bonus.json.

Draait dagelijks via GitHub Actions (.github/workflows/bonus.yml).
De webapp (index.html) leest bonus.json en toont badges bij producten in de bonus.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

API = "https://api.ah.nl"
MAX_ATTEMPTS = 3
HEADERS = {
    "User-Agent": "Appie/8.22.3",
    "X-Application": "AHWEBSHOP",
}

ROOT = Path(__file__).resolve().parent.parent


def retry_delay(error: urllib.error.HTTPError, attempt: int) -> float:
    retry_after = error.headers.get("Retry-After")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                pass
    return float(2 ** (attempt - 1))


def request_json(req: urllib.request.Request) -> object:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code < 600
            if not retryable or attempt == MAX_ATTEMPTS:
                raise
            delay = retry_delay(error, attempt)
            print(
                f"WAARSCHUWING: HTTP {error.code}; nieuwe poging "
                f"{attempt + 1}/{MAX_ATTEMPTS} over {delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)
    raise RuntimeError("onbereikbare retry-status")


def get_token() -> str:
    req = urllib.request.Request(
        f"{API}/mobile-auth/v1/auth/token/anonymous",
        data=json.dumps({"clientId": "appie"}).encode(),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="POST",
    )
    payload = request_json(req)
    if not isinstance(payload, dict):
        raise ValueError("tokenantwoord is geen object")
    token = payload.get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("tokenantwoord bevat geen geldig access_token")
    return token


def search(token: str, query: str) -> list[dict]:
    url = f"{API}/mobile-services/product/search/v2?query={urllib.parse.quote(query)}&size=20"
    req = urllib.request.Request(
        url, headers={**HEADERS, "Authorization": f"Bearer {token}"}
    )
    payload = request_json(req)
    if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
        raise ValueError("zoekantwoord bevat geen geldige products-lijst")
    return payload["products"]


def main() -> int:
    watchlist = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
    try:
        token = get_token()
    except Exception as error:  # noqa: BLE001 - elke tokenfout moet publicatie stoppen
        print(f"FOUT: ophalen token mislukt: {error}", file=sys.stderr)
        return 1

    out_items = []
    covered_keys = set()
    for item in watchlist["items"]:
        try:
            products = search(token, item["query"])
        except Exception as error:  # noqa: BLE001 - verzamel alle ontbrekende dekking
            print(
                f"FOUT: zoekopdracht '{item['query']}' mislukt: {error}",
                file=sys.stderr,
            )
            continue
        by_id = {
            p.get("webshopId"): p
            for p in products
            if isinstance(p, dict)
        }
        for wid in item["ids"]:
            p = by_id.get(wid)
            if not p:
                continue
            covered_keys.add(item["key"])
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
                    "houdbaar": bool(item.get("houdbaar")),
                }
            )

    expected_keys = {item["key"] for item in watchlist["items"]}
    missing_keys = sorted(expected_keys - covered_keys)
    print(
        f"Watchlist-dekking: {len(covered_keys)}/{len(expected_keys)} items"
    )
    if missing_keys:
        print(
            "FOUT: geen gevolgde productvariant gevonden voor: "
            + ", ".join(missing_keys)
            + "; bonus.json blijft ongewijzigd",
            file=sys.stderr,
        )
        return 1

    output_path = ROOT / "bonus.json"
    try:
        existing = json.loads(output_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        existing = None
    if isinstance(existing, dict) and existing.get("items") == out_items:
        print(
            f"bonus.json ongewijzigd: {len(out_items)} producten, "
            f"{sum(1 for item in out_items if item['isBonus'])} in de bonus"
        )
        return 0

    result = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": out_items,
    }
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    bonus_count = sum(1 for i in out_items if i["isBonus"])
    print(f"bonus.json geschreven: {len(out_items)} producten, {bonus_count} in de bonus")
    return 0


if __name__ == "__main__":
    sys.exit(main())
