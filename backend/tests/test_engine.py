import pytest

from app.engine import arbitrage, haversine_km
from app.matching import match_commodity, match_market
from app.schemas import Commodity, Market, Price
from scripts.seed import load


@pytest.fixture(scope="module")
def data():
    commodities, markets, prices = load()
    return ({c.id: c for c in commodities}, {m.id: m for m in markets}, prices)


class TestDistance:
    def test_haversine_known_distance(self):
        # Bengaluru -> Mysuru is ~125-145 km as the crow flies
        d = haversine_km(12.975, 77.572, 12.296, 76.653)
        assert 120 < d < 150

    def test_zero_distance(self):
        assert haversine_km(13.0, 77.0, 13.0, 77.0) == 0


class TestMatching:
    def test_commodity_aliases(self, data):
        commodities = list(data[0].values())
        assert match_commodity("Bengal Gram (Gram)(Whole)", commodities) == "gram"
        assert match_commodity("Tomato", commodities) == "tomato"
        assert match_commodity("Paddy(Dhan)(Common)", commodities) == "paddy"

    def test_market_match_by_district(self, data):
        markets = list(data[1].values())
        assert match_market("Bandipalya", "Mysuru", markets) == "mysuru"


class TestArbitrage:
    def test_ranks_by_net_price_not_sticker(self, data):
        commodities, markets, prices = data
        # craft two markets: far one has higher sticker but loses after transport
        m_local = Market(id="L", name="Local", district="D", state="KA", lat=13.0, lon=77.0)
        m_far = Market(id="F", name="Far", district="D2", state="KA", lat=14.0, lon=77.0)  # ~111 km
        mkts = {"L": m_local, "F": m_far}
        c = Commodity(id="tomato", name="Tomato", category="vegetable", msp=None, msp_season=None, unit="₹/quintal")
        pr = [
            Price(market_id="L", commodity_id="tomato", min_price=2000, max_price=2200, modal_price=2100, arrival_date="2025-09-15"),
            Price(market_id="F", commodity_id="tomato", min_price=2150, max_price=2300, modal_price=2200, arrival_date="2025-09-15"),
        ]
        res = arbitrage(c, m_local, mkts, pr, max_distance_km=200, transport_rate=1.0)
        # Far modal is 100 higher but ~111 km * 1 = 111 transport -> net lower
        assert res.best_market_id == "L"
        assert res.quotes[0].market_id == "L"

    def test_recommends_far_market_when_worth_it(self, data):
        m_local = Market(id="L", name="Local", district="D", state="KA", lat=13.0, lon=77.0)
        m_far = Market(id="F", name="Far", district="D2", state="KA", lat=13.2, lon=77.0)  # ~22 km
        mkts = {"L": m_local, "F": m_far}
        c = Commodity(id="onion", name="Onion", category="vegetable", msp=None, msp_season=None, unit="₹/quintal")
        pr = [
            Price(market_id="L", commodity_id="onion", min_price=1200, max_price=1300, modal_price=1250, arrival_date="2025-09-15"),
            Price(market_id="F", commodity_id="onion", min_price=1500, max_price=1600, modal_price=1550, arrival_date="2025-09-15"),
        ]
        res = arbitrage(c, m_local, mkts, pr, max_distance_km=200, transport_rate=1.0)
        assert res.best_market_id == "F"
        assert res.extra_per_quintal > 250  # 300 sticker gap minus ~22 transport
        assert "more than" in res.recommendation

    def test_msp_below_alert(self, data):
        m = Market(id="L", name="Local", district="D", state="KA", lat=13.0, lon=77.0)
        c = Commodity(id="tur", name="Tur", category="pulse", msp=8000, msp_season="Kharif 2025-26", unit="₹/quintal")
        pr = [Price(market_id="L", commodity_id="tur", min_price=7000, max_price=7200, modal_price=7100, arrival_date="2025-09-15")]
        res = arbitrage(c, m, {"L": m}, pr, 200, 1.0)
        assert res.below_msp_count == 1
        assert res.msp_alert and "BELOW the MSP" in res.msp_alert
        assert res.quotes[0].below_msp is True

    def test_distance_filter_excludes_far_markets(self, data):
        m_local = Market(id="L", name="Local", district="D", state="KA", lat=13.0, lon=77.0)
        m_far = Market(id="F", name="Far", district="D2", state="KA", lat=18.0, lon=77.0)  # ~555 km
        mkts = {"L": m_local, "F": m_far}
        c = Commodity(id="onion", name="Onion", category="vegetable", msp=None, msp_season=None, unit="₹/quintal")
        pr = [
            Price(market_id="L", commodity_id="onion", min_price=1200, max_price=1300, modal_price=1250, arrival_date="2025-09-15"),
            Price(market_id="F", commodity_id="onion", min_price=2000, max_price=2100, modal_price=2050, arrival_date="2025-09-15"),
        ]
        res = arbitrage(c, m_local, mkts, pr, max_distance_km=100, transport_rate=1.0)
        assert {q.market_id for q in res.quotes} == {"L"}

    def test_real_dataset_runs(self, data):
        commodities, markets, prices = data
        res = arbitrage(commodities["tomato"], markets["kolar"], markets, prices, 200, 1.0)
        assert res.quotes
        assert res.quotes[0].net_price == max(q.net_price for q in res.quotes)
        assert any(q.is_origin for q in res.quotes)

    def test_msp_data_is_real(self, data):
        commodities = data[0]
        assert commodities["paddy"].msp == 2369   # real 2025-26 MSP
        assert commodities["wheat"].msp == 2425
        assert commodities["ragi"].msp == 4886
