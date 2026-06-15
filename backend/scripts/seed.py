"""Validate datasets and load commodities, markets and the price snapshot.

    python -m scripts.seed
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.exc import OperationalError  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import CommodityRow, MarketRow, PriceRow  # noqa: E402
from app.schemas import Commodity, Market, Price  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"


def load() -> tuple[list[Commodity], list[Market], list[Price]]:
    commodities = [Commodity.model_validate(c) for c in json.loads((DATA / "commodities.json").read_text())]
    markets = [Market.model_validate(m) for m in json.loads((DATA / "markets.json").read_text())]
    snapshot = json.loads((DATA / "prices.json").read_text())
    prices = [Price.model_validate(p) for p in snapshot["prices"]]

    cids = {c.id for c in commodities}
    mids = {m.id for m in markets}
    for p in prices:
        if p.commodity_id not in cids:
            raise ValueError(f"price references unknown commodity {p.commodity_id!r}")
        if p.market_id not in mids:
            raise ValueError(f"price references unknown market {p.market_id!r}")
    return commodities, markets, prices


def wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    for attempt in range(retries):
        try:
            with engine.connect():
                return
        except OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def seed() -> int:
    commodities, markets, prices = load()
    wait_for_db()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for table in (PriceRow, MarketRow, CommodityRow):
            db.query(table).delete()
        for c in commodities:
            db.add(CommodityRow.from_domain(c))
        for m in markets:
            db.add(MarketRow.from_domain(m))
        for p in prices:
            db.add(PriceRow.from_domain(p))
        db.commit()
    print(f"seeded {len(commodities)} commodities, {len(markets)} markets, {len(prices)} prices")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed())
