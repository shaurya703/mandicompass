"""Generate the bundled sample price snapshot (data/prices.json).

This produces an ILLUSTRATIVE snapshot in the exact Agmarknet schema so the
demo works offline. Modal prices are anchored to real recent reference levels
(e.g. tomato ~₹2,600/q, onion ~₹1,300/q, Sept 2025 Agmarknet) with several
crops deliberately near or below MSP to exercise the distress-alert logic.
Per-market spreads are deterministic (hash-based), so the file is reproducible
and clearly synthetic. For real numbers, run `python -m scripts.fetch`.

    python -m scripts.make_sample_prices
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
ARRIVAL_DATE = "2025-09-15"

# base modal ₹/quintal, and cross-market spread factor (veg varies far more)
BASE = {
    "tomato": (2600, 0.22), "onion": (1300, 0.20), "potato": (1500, 0.18),
    "ragi": (3400, 0.07), "maize": (2250, 0.07), "paddy": (2320, 0.06),
    "jowar": (3300, 0.08), "bajra": (2600, 0.08), "wheat": (2500, 0.06),
    "tur": (7300, 0.07), "moong": (8200, 0.07), "urad": (7500, 0.07),
    "gram": (5400, 0.07), "groundnut": (6700, 0.08), "soybean": (4900, 0.07),
    "sunflower": (7000, 0.07), "mustard": (5900, 0.07), "cotton": (7450, 0.06),
}


def _offset(commodity: str, market: str) -> float:
    """Deterministic per-(commodity, market) factor in roughly [-1, 1]."""
    h = hashlib.sha1(f"{commodity}|{market}".encode()).digest()
    return (h[0] / 255.0) * 2 - 1


def build() -> dict:
    markets = json.loads((DATA / "markets.json").read_text())
    prices = []
    for cid, (base, spread) in BASE.items():
        # each commodity trades in a deterministic subset (~14) of markets
        chosen = [m for m in markets if _offset("present-" + cid, m["id"]) > -0.6]
        for m in chosen:
            modal = round(base * (1 + spread * _offset(cid, m["id"])) / 10) * 10
            lo = int(modal * 0.94)
            hi = int(modal * 1.07)
            prices.append({
                "market_id": m["id"], "commodity_id": cid,
                "min_price": lo, "max_price": hi, "modal_price": int(modal),
                "arrival_date": ARRIVAL_DATE,
            })
    return {
        "_meta": {
            "source": "ILLUSTRATIVE sample in Agmarknet schema; modal prices "
                      "anchored to real Sept-2025 reference levels. Run "
                      "scripts.fetch for live data.gov.in data.",
            "arrival_date": ARRIVAL_DATE, "records": len(prices),
        },
        "prices": prices,
    }


if __name__ == "__main__":
    payload = build()
    (DATA / "prices.json").write_text(json.dumps(payload, indent=2))
    print(f"wrote {payload['_meta']['records']} sample price records -> data/prices.json")
