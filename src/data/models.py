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
class MacroIndicator:
    name: str            # e.g. "10-Year Treasury Yield"
    series_id: str       # e.g. "DGS10"
    value: float
    previous_value: float
    date: str
    unit: str            # e.g. "percent", "billions_usd"


@dataclass
class CryptoAsset:
    symbol: str
    name: str
    price: float
    change_percent_24h: float
    market_cap: float
    volume_24h: float


@dataclass
class GeopoliticsItem:
    title: str
    description: str
    source: str
    published_at: str


@dataclass
class AIUpdateItem:
    title: str
    description: str
    source: str
    published_at: str
    subcategory: str     # "model_release", "funding", "regulation", "research"


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

    # Category metadata
    categories: list[str] = field(default_factory=list)

    # Finance Macro additions
    macro_indicators: list[MacroIndicator] = field(default_factory=list)

    # Crypto additions (beyond basic crypto dict)
    crypto_extended: list[CryptoAsset] = field(default_factory=list)
    crypto_global: dict = field(default_factory=dict)
    crypto_trending: list[str] = field(default_factory=list)

    # Geopolitics
    geopolitics: list[GeopoliticsItem] = field(default_factory=list)

    # AI Updates
    ai_updates: list[AIUpdateItem] = field(default_factory=list)

    # World Monitor enrichments
    fear_greed: dict = field(default_factory=dict)          # {score, label}
    macro_signals: dict = field(default_factory=dict)       # {verdict, bullishCount, signals}
    sectors: list[dict] = field(default_factory=list)       # [{symbol, name, change}]
    etf_flows: dict = field(default_factory=dict)           # {summary, etfs}
    predictions: list[dict] = field(default_factory=list)   # [{title, yesPrice, volume}]
    forecasts: list[dict] = field(default_factory=list)     # [{title, domain, region}]
    sanctions: dict = field(default_factory=dict)           # {totalCount, countries, programs}
    unrest_events: list[dict] = field(default_factory=list) # [{title, eventType, country}]
    conflict_events: list[dict] = field(default_factory=list)  # [{country, sideA, sideB}]
    cross_signals: list[dict] = field(default_factory=list) # [{type, summary, severity}]
    gdelt_intel: list[dict] = field(default_factory=list)   # [{topic, articles}]

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
        data["macro_indicators"] = [MacroIndicator(**m) for m in data.get("macro_indicators", [])]
        data["crypto_extended"] = [CryptoAsset(**c) for c in data.get("crypto_extended", [])]
        data["geopolitics"] = [GeopoliticsItem(**g) for g in data.get("geopolitics", [])]
        data["ai_updates"] = [AIUpdateItem(**a) for a in data.get("ai_updates", [])]
        return cls(**data)

    def save(self, path: str):
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "MarketSnapshot":
        with open(path, "r") as f:
            return cls.from_json(f.read())
