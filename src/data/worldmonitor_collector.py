import httpx
from src.data.models import (
    StockMover, CryptoAsset, GeopoliticsItem, MarketSnapshot,
)
from src.data.categories import PodcastCategory
from src.utils.logger import log

BASE_URL = "https://www.worldmonitor.app/api/bootstrap"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://www.worldmonitor.app",
    "Referer": "https://www.worldmonitor.app/",
}

# Which bootstrap keys to fetch per category
CATEGORY_KEYS = {
    PodcastCategory.FINANCE_MACRO: [
        "marketQuotes", "commodityQuotes", "macroSignals",
        "fearGreedIndex", "etfFlows", "sectors",
    ],
    PodcastCategory.FINANCE_MICRO: [
        "marketQuotes", "sectors", "etfFlows",
    ],
    PodcastCategory.CRYPTO: [
        "cryptoQuotes", "etfFlows",
    ],
    PodcastCategory.GEOPOLITICS: [
        "ucdpEvents", "unrestEvents", "sanctionsPressure",
        "gdeltIntel", "crossSourceSignals", "predictions", "forecasts",
    ],
    PodcastCategory.AI_UPDATES: [
        "gdeltIntel", "predictions",
    ],
}


class WorldMonitorCollector:
    """Fetches data from World Monitor's bootstrap API.
    One API call returns all needed data across categories.
    """

    def __init__(self):
        pass  # No API key needed

    def collect(self, categories: list[PodcastCategory], status_callback=None) -> dict:
        """Fetch data for the given categories in a single API call."""
        # Deduplicate keys across all selected categories
        all_keys = set()
        for cat in categories:
            all_keys.update(CATEGORY_KEYS.get(cat, []))

        if not all_keys:
            return {}

        if status_callback:
            status_callback("Fetching data from World Monitor...")

        log.info(f"WorldMonitor: fetching {len(all_keys)} keys for {[c.value for c in categories]}")

        raw = self._fetch_bootstrap(list(all_keys))
        if not raw:
            log.warning("WorldMonitor: bootstrap returned empty, falling back")
            return {}

        # Parse raw data into structured dict matching MarketSnapshot fields
        result = {}
        self._parse_finance_macro(raw, categories, result)
        self._parse_finance_micro(raw, categories, result)
        self._parse_crypto(raw, categories, result)
        self._parse_geopolitics(raw, categories, result)
        self._parse_ai_updates(raw, categories, result)

        log.info(f"WorldMonitor: parsed {len(result)} fields")
        return result

    def _fetch_bootstrap(self, keys: list[str]) -> dict:
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(
                    BASE_URL,
                    params={"keys": ",".join(keys)},
                    headers=HEADERS,
                )
                resp.raise_for_status()
                data = resp.json()

            result = data.get("data", {})
            missing = data.get("missing", [])
            if missing:
                log.warning(f"WorldMonitor: missing keys: {missing}")
            return result
        except Exception as e:
            log.warning(f"WorldMonitor bootstrap failed: {e}")
            return {}

    # ── Finance Macro ────────────────────────────────────────

    def _parse_finance_macro(self, raw: dict, categories: list, result: dict):
        if PodcastCategory.FINANCE_MACRO not in categories:
            return

        # Market indices from marketQuotes
        quotes = raw.get("marketQuotes", {}).get("quotes", [])
        index_symbols = {"^GSPC", "^DJI", "^IXIC", "^RUT"}
        index_names = {"^GSPC": "S&P 500", "^DJI": "DOW", "^IXIC": "NASDAQ", "^RUT": "Russell 2000"}
        indices = {}
        for q in quotes:
            sym = q.get("symbol", "")
            if sym in index_symbols:
                indices[index_names.get(sym, sym)] = {
                    "current": q.get("price", 0),
                    "change_percent": q.get("change", 0),
                }
        result["indices"] = indices

        # Commodities and Forex from commodityQuotes (WM bundles them together)
        commodity_quotes = raw.get("commodityQuotes", {}).get("quotes", [])

        commodity_map = {
            "^VIX": "VIX", "GC=F": "Gold", "SI=F": "Silver", "HG=F": "Copper",
            "PL=F": "Platinum", "CL=F": "Oil (WTI)", "BZ=F": "Oil (Brent)",
            "NG=F": "Natural Gas", "ZW=F": "Wheat", "KC=F": "Coffee", "CC=F": "Cocoa",
        }
        forex_map = {
            "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
            "USDCNY=X": "USD/CNY", "AUDUSD=X": "AUD/USD", "USDCHF=X": "USD/CHF",
            "USDCAD=X": "USD/CAD",
        }

        commodities = {}
        forex = {}
        for q in commodity_quotes:
            sym = q.get("symbol", "")
            if sym in commodity_map:
                commodities[commodity_map[sym]] = {
                    "price": q.get("price", 0),
                    "change_percent": q.get("change", 0),
                }
            elif sym in forex_map:
                forex[forex_map[sym]] = {
                    "rate": q.get("price", 0),
                    "change_percent": q.get("change", 0),
                }

        result["commodities"] = commodities
        result["forex"] = forex

        # Macro signals (BUY/SELL verdict)
        macro = raw.get("macroSignals", {})
        if macro:
            result["macro_signals"] = {
                "verdict": macro.get("verdict", ""),
                "bullish_count": macro.get("bullishCount", 0),
                "total_count": macro.get("totalCount", 0),
                "signals": macro.get("signals", {}),
            }

        # Fear & Greed Index
        fg = raw.get("fearGreedIndex", {})
        if fg:
            composite = fg.get("composite", {})
            result["fear_greed"] = {
                "score": composite.get("score", 0),
                "label": composite.get("label", ""),
                "previous": composite.get("previous", 0),
            }
            # Use fear/greed to set market sentiment
            score = composite.get("score", 50)
            if score >= 60:
                result["market_sentiment"] = "bullish"
            elif score <= 40:
                result["market_sentiment"] = "bearish"
            else:
                result["market_sentiment"] = "neutral"

        # ETF flows
        etf = raw.get("etfFlows", {})
        if etf:
            result["etf_flows"] = {
                "summary": etf.get("summary", {}),
                "etfs": etf.get("etfs", [])[:10],
            }

        # Sectors
        sectors_data = raw.get("sectors", {})
        if sectors_data:
            result["sectors"] = sectors_data.get("sectors", [])

    # ── Finance Micro ────────────────────────────────────────

    def _parse_finance_micro(self, raw: dict, categories: list, result: dict):
        if PodcastCategory.FINANCE_MICRO not in categories:
            return

        quotes = raw.get("marketQuotes", {}).get("quotes", [])
        index_symbols = {"^GSPC", "^DJI", "^IXIC", "^RUT"}

        # Separate stocks from indices
        stocks = [q for q in quotes if q.get("symbol", "") not in index_symbols]

        # Top gainers (positive change, sorted descending)
        gainers = sorted(
            [s for s in stocks if (s.get("change") or 0) > 0],
            key=lambda x: x.get("change", 0),
            reverse=True,
        )
        result["top_gainers"] = [
            StockMover(
                symbol=s.get("symbol", ""),
                name=s.get("display", s.get("name", "")),
                price=s.get("price", 0),
                change_percent=s.get("change", 0),
            )
            for s in gainers[:5]
        ]

        # Top losers (negative change, sorted ascending)
        losers = sorted(
            [s for s in stocks if (s.get("change") or 0) < 0],
            key=lambda x: x.get("change", 0),
        )
        result["top_losers"] = [
            StockMover(
                symbol=s.get("symbol", ""),
                name=s.get("display", s.get("name", "")),
                price=s.get("price", 0),
                change_percent=s.get("change", 0),
            )
            for s in losers[:5]
        ]

        # Sectors (if not already set by macro)
        if "sectors" not in result:
            sectors_data = raw.get("sectors", {})
            if sectors_data:
                result["sectors"] = sectors_data.get("sectors", [])

    # ── Crypto ───────────────────────────────────────────────

    def _parse_crypto(self, raw: dict, categories: list, result: dict):
        if PodcastCategory.CRYPTO not in categories:
            return

        crypto_quotes = raw.get("cryptoQuotes", {}).get("quotes", [])

        # Basic crypto dict (BTC/ETH)
        crypto = {}
        for q in crypto_quotes[:2]:  # BTC and ETH are first
            sym = q.get("symbol", "")
            crypto[sym] = {
                "price": q.get("price", 0),
                "change_percent": q.get("change", 0),
            }
        result["crypto"] = crypto

        # Extended list of all coins
        result["crypto_extended"] = [
            CryptoAsset(
                symbol=q.get("symbol", ""),
                name=q.get("name", ""),
                price=q.get("price", 0),
                change_percent_24h=q.get("change", 0),
                market_cap=0,  # WM doesn't provide mcap
                volume_24h=0,
            )
            for q in crypto_quotes
        ]

        # Crypto ETF flows (filter for crypto ETFs like IBIT). Merge into the
        # existing etf_flows dict (which macro populated with summary/etfs)
        # rather than overwriting it — the UI in app.py reads both shapes.
        etf = raw.get("etfFlows", {})
        if etf:
            crypto_etfs = [
                e for e in etf.get("etfs", [])
                if any(kw in (e.get("ticker", "") + e.get("issuer", "")).upper()
                       for kw in ["IBIT", "FBTC", "ARKB", "GBTC", "ETHE", "BITO"])
            ]
            if crypto_etfs:
                existing = result.setdefault("etf_flows", {})
                existing["crypto_etfs"] = crypto_etfs

    # ── Geopolitics ──────────────────────────────────────────

    def _parse_geopolitics(self, raw: dict, categories: list, result: dict):
        if PodcastCategory.GEOPOLITICS not in categories:
            return

        # UCDP armed conflicts
        ucdp = raw.get("ucdpEvents", {})
        result["conflict_events"] = [
            {
                "country": e.get("country", ""),
                "side_a": e.get("sideA", ""),
                "side_b": e.get("sideB", ""),
                "date_start": e.get("dateStart", ""),
            }
            for e in ucdp.get("events", [])[:10]
        ]

        # Unrest events (protests, civil unrest)
        unrest = raw.get("unrestEvents", {})
        result["unrest_events"] = [
            {
                "title": e.get("title", ""),
                "event_type": e.get("eventType", ""),
                "country": e.get("country", ""),
                "city": e.get("city", ""),
                "summary": e.get("summary", ""),
            }
            for e in unrest.get("events", [])[:10]
        ]

        # Sanctions pressure
        sanctions = raw.get("sanctionsPressure", {})
        if sanctions:
            result["sanctions"] = {
                "total_count": sanctions.get("totalCount", 0),
                "vessel_count": sanctions.get("vesselCount", 0),
                "aircraft_count": sanctions.get("aircraftCount", 0),
                "top_countries": [
                    {"country": c.get("countryName", ""), "count": c.get("entityCount", 0)}
                    for c in sanctions.get("countries", [])[:10]
                ],
            }

        # GDELT intelligence topics
        gdelt = raw.get("gdeltIntel", {})
        gdelt_topics = gdelt.get("topics", [])
        geo_topics = ["military", "nuclear", "sanctions", "intelligence", "maritime"]
        result["gdelt_intel"] = [
            {
                "topic": t.get("id", ""),
                "articles": [
                    {"title": a.get("title", ""), "url": a.get("url", "")}
                    for a in t.get("articles", [])[:5]
                ],
            }
            for t in gdelt_topics if t.get("id", "") in geo_topics
        ]

        # Cross-source signals (GPS jamming, multi-source alerts)
        cross = raw.get("crossSourceSignals", {})
        result["cross_signals"] = [
            {
                "type": s.get("type", ""),
                "theater": s.get("theater", ""),
                "summary": s.get("summary", ""),
                "severity": s.get("severity", ""),
            }
            for s in cross.get("signals", [])[:10]
        ]

        # Geopolitics items for the existing model (from GDELT + unrest)
        geo_items = []
        for t in gdelt_topics:
            if t.get("id", "") in geo_topics:
                for a in t.get("articles", [])[:3]:
                    geo_items.append(GeopoliticsItem(
                        title=a.get("title", ""),
                        description="",
                        source="GDELT",
                        published_at="",
                    ))
        for e in unrest.get("events", [])[:5]:
            geo_items.append(GeopoliticsItem(
                title=e.get("title", ""),
                description=e.get("summary", ""),
                source="World Monitor",
                published_at="",
            ))
        result["geopolitics"] = geo_items

        # Predictions (geopolitical)
        preds = raw.get("predictions", {})
        geo_preds = preds.get("geopolitical", [])
        result["predictions"] = [
            {
                "title": p.get("title", ""),
                "yes_price": p.get("yesPrice", 0),
                "volume": p.get("volume", 0),
                "url": p.get("url", ""),
                "category": "geopolitical",
            }
            for p in geo_preds[:10]
        ]

        # Forecasts
        fc = raw.get("forecasts", {})
        result["forecasts"] = [
            {
                "title": f.get("title", ""),
                "domain": f.get("domain", ""),
                "region": f.get("region", ""),
            }
            for f in fc.get("predictions", [])[:10]
        ]

    # ── AI Updates ───────────────────────────────────────────

    def _parse_ai_updates(self, raw: dict, categories: list, result: dict):
        if PodcastCategory.AI_UPDATES not in categories:
            return

        # GDELT cyber/tech topics
        gdelt = raw.get("gdeltIntel", {})
        gdelt_topics = gdelt.get("topics", [])
        tech_topics = ["cyber"]
        for t in gdelt_topics:
            if t.get("id", "") in tech_topics:
                existing = result.get("gdelt_intel", [])
                existing.append({
                    "topic": t.get("id", ""),
                    "articles": [
                        {"title": a.get("title", ""), "url": a.get("url", "")}
                        for a in t.get("articles", [])[:5]
                    ],
                })
                result["gdelt_intel"] = existing

        # Tech predictions from Polymarket
        preds = raw.get("predictions", {})
        tech_preds = preds.get("tech", [])
        existing_preds = result.get("predictions", [])
        existing_preds.extend([
            {
                "title": p.get("title", ""),
                "yes_price": p.get("yesPrice", 0),
                "volume": p.get("volume", 0),
                "url": p.get("url", ""),
                "category": "tech",
            }
            for p in tech_preds[:10]
        ])
        result["predictions"] = existing_preds
