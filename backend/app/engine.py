"""Arbitrage + MSP engine.

Given a commodity and the farmer's home mandi, find where it pays most to sell
once the cost of getting there is subtracted — and flag when prices are below
the government's Minimum Support Price (MSP), which is the distress signal that
actually matters to a small farmer.

The key idea most "mandi price" apps miss: the highest sticker price is not the
best sale. A mandi ₹300/quintal higher but 120 km away can net *less* than the
local one after transport. MandiCompass ranks by **net price = modal − transport**.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .schemas import ArbitrageResult, Commodity, Market, MarketQuote, Price

# Hiring a mini-truck runs ~₹30-40/km carrying ~30-40 quintals, i.e. roughly
# ₹1 per quintal per km. Documented and configurable.
DEFAULT_TRANSPORT_RATE = 1.0

DISCLAIMER = (
    "MandiCompass compares wholesale (modal) mandi prices and subtracts an "
    "estimated transport cost. Prices change daily and vary by grade and "
    "variety; transport is an estimate. Confirm the live rate at the mandi and "
    "factor in your own quantity, quality and time before you travel."
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def arbitrage(
    commodity: Commodity,
    origin: Market,
    markets: dict[str, Market],
    prices: list[Price],
    max_distance_km: int = 200,
    transport_rate: float = DEFAULT_TRANSPORT_RATE,
) -> ArbitrageResult:
    by_market = {p.market_id: p for p in prices if p.commodity_id == commodity.id}

    quotes: list[MarketQuote] = []
    for mid, price in by_market.items():
        market = markets.get(mid)
        if market is None:
            continue
        dist = haversine_km(origin.lat, origin.lon, market.lat, market.lon)
        if dist > max_distance_km:
            continue
        transport = round(dist * transport_rate)
        net = price.modal_price - transport
        vs_msp = (net - commodity.msp) if commodity.msp is not None else None
        quotes.append(MarketQuote(
            market_id=mid, market_name=market.name, district=market.district,
            distance_km=round(dist, 1), modal_price=price.modal_price,
            min_price=price.min_price, max_price=price.max_price,
            transport_cost_per_quintal=transport, net_price=net,
            vs_msp=vs_msp, below_msp=(vs_msp is not None and vs_msp < 0),
            is_origin=(mid == origin.id), arrival_date=price.arrival_date,
        ))

    quotes.sort(key=lambda q: -q.net_price)

    snapshot_date = quotes[0].arrival_date if quotes else ""
    best = quotes[0] if quotes else None
    origin_quote = next((q for q in quotes if q.is_origin), None)

    extra = 0
    if best and origin_quote:
        extra = best.net_price - origin_quote.net_price
    recommendation = _recommend(commodity, best, origin_quote, origin, extra)
    below = sum(1 for q in quotes if q.below_msp)
    msp_alert = _msp_alert(commodity, quotes, origin_quote)

    return ArbitrageResult(
        commodity=commodity.id, commodity_name=commodity.name, unit=commodity.unit,
        msp=commodity.msp, msp_season=commodity.msp_season,
        origin_market=origin.id, origin_market_name=origin.name,
        max_distance_km=max_distance_km,
        transport_rate_per_km_per_quintal=transport_rate,
        quotes=quotes,
        best_market_id=best.market_id if best else origin.id,
        recommendation=recommendation, extra_per_quintal=extra,
        below_msp_count=below, msp_alert=msp_alert,
        disclaimer=DISCLAIMER,
    )


def _recommend(commodity, best, origin_quote, origin, extra) -> str:
    if best is None:
        return (
            f"No {commodity.name} prices reported within range of {origin.name} "
            "in this snapshot. Try a larger distance or check back after the next update."
        )
    if best.is_origin or extra <= 0:
        return (
            f"Your local mandi, {origin.name}, is already the best net price for "
            f"{commodity.name} — selling elsewhere wouldn't beat it after transport."
        )
    return (
        f"Selling at {best.market_name} ({best.distance_km:.0f} km away) nets about "
        f"₹{extra}/quintal more than {origin.name} after transport — "
        f"roughly ₹{extra * 30:,} extra on a 30-quintal load."
    )


def _msp_alert(commodity, quotes, origin_quote) -> str | None:
    if commodity.msp is None or not quotes:
        return None
    if origin_quote and origin_quote.below_msp:
        gap = -origin_quote.vs_msp
        return (
            f"At your mandi, {commodity.name} is about ₹{gap}/quintal BELOW the "
            f"MSP of ₹{commodity.msp}. If no nearby mandi beats MSP, sell through a "
            "government procurement centre instead of taking a distress price."
        )
    best_vs = quotes[0].vs_msp
    if best_vs is not None and best_vs < 0:
        return (
            f"Every mandi in range is below the MSP of ₹{commodity.msp} for "
            f"{commodity.name}. Consider a government procurement centre."
        )
    return None
