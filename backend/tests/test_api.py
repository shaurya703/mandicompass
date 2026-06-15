import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.db import Base
from app.models import CommodityRow, MarketRow, PriceRow
from scripts.seed import load


@pytest.fixture(scope="module")
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    commodities, markets, prices = load()
    with TestSession() as db:
        for c in commodities:
            db.add(CommodityRow.from_domain(c))
        for m in markets:
            db.add(MarketRow.from_domain(m))
        for p in prices:
            db.add(PriceRow.from_domain(p))
        db.commit()
    main_module.SessionLocal = TestSession
    app = main_module.create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["markets"] == 20


def test_commodities_have_real_msp(client):
    comms = {c["id"]: c for c in client.get("/api/commodities").json()["commodities"]}
    assert comms["paddy"]["msp"] == 2369
    assert comms["tomato"]["msp"] is None


def test_arbitrage_ranks_and_recommends(client):
    r = client.get("/api/arbitrage", params={"commodity": "tomato", "origin": "kolar", "max_distance": 250})
    assert r.status_code == 200
    body = r.json()
    nets = [q["net_price"] for q in body["quotes"]]
    assert nets == sorted(nets, reverse=True)
    assert body["best_market_id"]
    assert "recommendation" in body


def test_arbitrage_unknown_commodity_404(client):
    r = client.get("/api/arbitrage", params={"commodity": "diamonds", "origin": "kolar"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_arbitrage_unknown_market_404(client):
    r = client.get("/api/arbitrage", params={"commodity": "tomato", "origin": "narnia"})
    assert r.status_code == 404


def test_arbitrage_validates_distance(client):
    r = client.get("/api/arbitrage", params={"commodity": "tomato", "origin": "kolar", "max_distance": 5})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_msp_alert_for_below_msp_crop(client):
    # ragi open-market in the sample sits well below its ₹4886 MSP
    r = client.get("/api/arbitrage", params={"commodity": "ragi", "origin": "bengaluru", "max_distance": 300})
    body = r.json()
    assert body["below_msp_count"] >= 1
    assert body["msp_alert"]


def test_stats_reports_snapshot_source(client):
    body = client.get("/api/stats").json()
    assert body["markets"] == 20
    assert body["price_records"] > 100
    assert "Agmarknet" in body["snapshot_source"]


def test_meta_disclaimer(client):
    assert client.get("/api/meta").json()["disclaimer"]
