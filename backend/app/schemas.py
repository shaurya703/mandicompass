"""Domain models for MandiCompass."""

from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Commodity(BaseModel):
    id: str
    name: str
    category: str
    msp: Optional[int] = None
    msp_season: Optional[str] = None
    unit: str


class Market(BaseModel):
    id: str
    name: str
    district: str
    state: str
    lat: float
    lon: float


class Price(BaseModel):
    market_id: str
    commodity_id: str
    min_price: int
    max_price: int
    modal_price: int
    arrival_date: str


class MarketQuote(BaseModel):
    market_id: str
    market_name: str
    district: str
    distance_km: float
    modal_price: int
    min_price: int
    max_price: int
    transport_cost_per_quintal: int
    net_price: int                 # modal at that market minus transport from origin
    vs_msp: Optional[int]          # net modal minus MSP (None if no MSP)
    below_msp: bool
    is_origin: bool
    arrival_date: str


class ArbitrageResult(BaseModel):
    commodity: str
    commodity_name: str
    unit: str
    msp: Optional[int]
    msp_season: Optional[str]
    origin_market: str
    origin_market_name: str
    max_distance_km: int
    transport_rate_per_km_per_quintal: float
    quotes: list[MarketQuote]      # ranked by net_price desc
    best_market_id: str
    recommendation: str
    extra_per_quintal: int         # net gain selling at best vs origin
    below_msp_count: int
    msp_alert: Optional[str]
    disclaimer: str


class Stats(BaseModel):
    commodities: int
    markets: int
    price_records: int
    snapshot_date: Optional[str]
    snapshot_source: str
    generated_on: datetime.date
