from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .schemas import Commodity, Market, Price


class CommodityRow(Base):
    __tablename__ = "commodities"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    msp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    msp_season: Mapped[str | None] = mapped_column(String(30), nullable=True)
    unit: Mapped[str] = mapped_column(String(12), nullable=False)

    def to_domain(self) -> Commodity:
        return Commodity.model_validate({c.name: getattr(self, c.name) for c in self.__table__.columns})

    @classmethod
    def from_domain(cls, c: Commodity) -> "CommodityRow":
        return cls(**c.model_dump())


class MarketRow(Base):
    __tablename__ = "markets"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str] = mapped_column(String(60), nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    def to_domain(self) -> Market:
        return Market.model_validate({c.name: getattr(self, c.name) for c in self.__table__.columns})

    @classmethod
    def from_domain(cls, m: Market) -> "MarketRow":
        return cls(**m.model_dump())


class PriceRow(Base):
    __tablename__ = "prices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    commodity_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    min_price: Mapped[int] = mapped_column(Integer, nullable=False)
    max_price: Mapped[int] = mapped_column(Integer, nullable=False)
    modal_price: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_date: Mapped[str] = mapped_column(String(20), nullable=False)

    def to_domain(self) -> Price:
        return Price(
            market_id=self.market_id, commodity_id=self.commodity_id,
            min_price=self.min_price, max_price=self.max_price,
            modal_price=self.modal_price, arrival_date=self.arrival_date,
        )

    @classmethod
    def from_domain(cls, p: Price) -> "PriceRow":
        return cls(**p.model_dump())
