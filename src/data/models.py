from dataclasses import dataclass, field
from typing import Optional
import json
from datetime import datetime


@dataclass
class StockMover:
    symbol: str
    name: str
    price: float
    change_percent: float


@dataclass
class EarningsReport:
    symbol: str
    name: str
    eps_actual: Optional[float]
    eps_estimate: Optional[float]
    revenue_actual: Optional[float]
    surprise_percent: Optional[float]


@dataclass
class EconomicEvent:
    event: str
    country: str
    actual: Optional[str]
    previous: Optional[str]
    estimate: Optional[str]
    impact: str  # "low", "medium", "high"


@dataclass
class NewsItem:
    title: str
    description: str
    source: str
    published_at: str
    sentiment: float  # -1.0 to 1.0
    entities: list[str] = field(default_factory=list)


@dataclass
class MarketSnapshot:
    date: str
    indices: dict = field(default_factory=dict)
    top_gainers: list[StockMover] = field(default_factory=list)
    top_losers: list[StockMover] = field(default_factory=list)
    earnings: list[EarningsReport] = field(default_factory=list)
    economic_events: list[EconomicEvent] = field(default_factory=list)
    crypto: dict = field(default_factory=dict)
    forex: dict = field(default_factory=dict)
    commodities: dict = field(default_factory=dict)
    news: list[NewsItem] = field(default_factory=list)
    market_sentiment: str = "neutral"

    def to_json(self) -> str:
        return json.dumps(self._to_dict(), indent=2)

    def _to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_json(cls, json_str: str) -> "MarketSnapshot":
        data = json.loads(json_str)
        data["top_gainers"] = [StockMover(**m) for m in data.get("top_gainers", [])]
        data["top_losers"] = [StockMover(**m) for m in data.get("top_losers", [])]
        data["earnings"] = [EarningsReport(**e) for e in data.get("earnings", [])]
        data["economic_events"] = [EconomicEvent(**e) for e in data.get("economic_events", [])]
        data["news"] = [NewsItem(**n) for n in data.get("news", [])]
        return cls(**data)

    def save(self, path: str):
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "MarketSnapshot":
        with open(path, "r") as f:
            return cls.from_json(f.read())
