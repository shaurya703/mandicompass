import datetime
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from .db import SessionLocal
from .engine import DEFAULT_TRANSPORT_RATE, DISCLAIMER, arbitrage
from .models import CommodityRow, MarketRow, PriceRow
from .schemas import ArbitrageResult, Stats

CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",") if o.strip()
]
DATA = Path(__file__).resolve().parents[1] / "data"


def _commodities():
    with SessionLocal() as db:
        return {r.id: r.to_domain() for r in db.scalars(select(CommodityRow))}


def _markets():
    with SessionLocal() as db:
        return {r.id: r.to_domain() for r in db.scalars(select(MarketRow))}


def _prices():
    with SessionLocal() as db:
        return [r.to_domain() for r in db.scalars(select(PriceRow))]


def create_app() -> FastAPI:
    app = FastAPI(title="MandiCompass API", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                       allow_methods=["*"], allow_headers=["*"])

    @app.exception_handler(HTTPException)
    async def http_err(request: Request, exc: HTTPException):
        code = {404: "not_found", 422: "validation_error"}.get(exc.status_code, "request_error")
        return JSONResponse(status_code=exc.status_code,
                            content={"error": {"code": code, "message": str(exc.detail)}})

    @app.exception_handler(RequestValidationError)
    async def val_err(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {
            "code": "validation_error", "message": "Invalid request",
            "details": [{"loc": list(e.get("loc", [])), "msg": e.get("msg")} for e in exc.errors()]}})

    @app.get("/api/health")
    def health():
        return {"status": "ok", "markets": len(_markets())}

    @app.get("/api/commodities")
    def commodities():
        return {"commodities": list(_commodities().values())}

    @app.get("/api/markets")
    def markets():
        return {"markets": list(_markets().values())}

    @app.get("/api/arbitrage", response_model=ArbitrageResult)
    def arbitrage_endpoint(
        commodity: str = Query(min_length=2),
        origin: str = Query(min_length=2, description="origin market id"),
        max_distance: int = Query(default=200, ge=10, le=1000),
        transport_rate: float = Query(default=DEFAULT_TRANSPORT_RATE, ge=0, le=20),
    ):
        comms = _commodities()
        mkts = _markets()
        c = comms.get(commodity)
        if c is None:
            raise HTTPException(404, f"Unknown commodity {commodity!r}")
        o = mkts.get(origin)
        if o is None:
            raise HTTPException(404, f"Unknown market {origin!r}")
        return arbitrage(c, o, mkts, _prices(), max_distance, transport_rate)

    @app.get("/api/stats", response_model=Stats)
    def stats():
        prices = _prices()
        meta = {}
        try:
            meta = json.loads((DATA / "prices.json").read_text()).get("_meta", {})
        except Exception:
            pass
        return Stats(
            commodities=len(_commodities()), markets=len(_markets()),
            price_records=len(prices),
            snapshot_date=meta.get("arrival_date"),
            snapshot_source=meta.get("source", "bundled snapshot"),
            generated_on=datetime.date.today(),
        )

    @app.get("/api/meta")
    def meta():
        return {"disclaimer": DISCLAIMER, "transport_rate_default": DEFAULT_TRANSPORT_RATE}

    return app


app = create_app()
