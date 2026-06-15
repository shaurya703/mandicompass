"""Live ingestion client for Agmarknet daily mandi prices via the data.gov.in
Open Government Data API (resource 9ef84268-d588-465a-a308-a864a43d0070,
"Current daily price of various commodities from various markets").

    python -m scripts.fetch --state Karnataka --out data/prices.json

This is the real pipeline. It pages through the API, maps each record's
commodity and market name onto MandiCompass's known ids, and writes a price
snapshot. The bundled data/prices.json is a committed sample (the public API
has intermittent outages); run this when the API is up to refresh with live
data. Set DATA_GOV_API_KEY to use your own key instead of the public demo key.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.matching import match_commodity, match_market  # noqa: E402

RESOURCE = "9ef84268-d588-465a-a308-a864a43d0070"
API = f"https://api.data.gov.in/resource/{RESOURCE}"
PUBLIC_DEMO_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
DATA = Path(__file__).resolve().parents[1] / "data"


def fetch_records(state: str | None, limit: int, timeout: float) -> list[dict]:
    key = os.environ.get("DATA_GOV_API_KEY", PUBLIC_DEMO_KEY)
    params = {"api-key": key, "format": "json", "limit": limit}
    if state:
        params["filters[state]"] = state
    url = f"{API}?{urlencode(params)}"
    with urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read()).get("records", [])


def to_snapshot(records: list[dict], markets: list[dict], commodities: list[dict]) -> list[dict]:
    out = []
    for r in records:
        cid = match_commodity(r.get("commodity", ""), commodities)
        mid = match_market(r.get("market", ""), r.get("district", ""), markets)
        if not cid or not mid:
            continue
        try:
            out.append({
                "market_id": mid,
                "commodity_id": cid,
                "min_price": int(float(r["min_price"])),
                "max_price": int(float(r["max_price"])),
                "modal_price": int(float(r["modal_price"])),
                "arrival_date": r.get("arrival_date", ""),
            })
        except (KeyError, ValueError):
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="Karnataka")
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--out", default=str(DATA / "prices.json"))
    args = ap.parse_args()

    markets = json.loads((DATA / "markets.json").read_text())
    commodities = json.loads((DATA / "commodities.json").read_text())
    records = fetch_records(args.state, args.limit, args.timeout)
    snapshot = to_snapshot(records, markets, commodities)
    payload = {
        "_meta": {"source": "Agmarknet via data.gov.in (live fetch)",
                  "state": args.state, "records": len(snapshot)},
        "prices": snapshot,
    }
    Path(args.out).write_text(json.dumps(payload, indent=2))
    print(f"fetched {len(snapshot)} mapped price records -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
