import finnhub
import time
from datetime import datetime, timedelta
from src.data.models import StockMover, EarningsReport, EconomicEvent
from src.utils.logger import log


class FinnhubCollector:
    def __init__(self, api_key: str):
        self.client = finnhub.Client(api_key=api_key)

    def collect_all(self) -> dict:
        log.info("Collecting data from Finnhub...")
        data = {}

        data["indices"] = self._get_indices()
        data["top_gainers"] = self._get_top_movers("gainers")
        data["top_losers"] = self._get_top_movers("losers")
        data["earnings"] = self._get_earnings()
        data["economic_events"] = self._get_economic_calendar()
        data["crypto"] = self._get_crypto()
        data["forex"] = self._get_forex()
        data["commodities"] = self._get_commodities()

        log.info("Finnhub data collection complete")
        return data

    def _get_indices(self) -> dict:
        log.info("Fetching market indices...")
        indices = {}
        symbols = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "DOW": "^DJI",
        }
        for name, symbol in symbols.items():
            try:
                quote = self.client.quote(symbol)
                indices[name] = {
                    "current": quote.get("c", 0),
                    "change": quote.get("d", 0),
                    "change_percent": quote.get("dp", 0),
                    "previous_close": quote.get("pc", 0),
                }
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
                indices[name] = {"current": 0, "change": 0, "change_percent": 0, "previous_close": 0}
        return indices

    def _get_top_movers(self, category: str) -> list[StockMover]:
        log.info(f"Fetching top {category}...")
        try:
            # Finnhub may not support this on free tier; fall back gracefully
            data = self.client.stock_market_snapshot(category=category)
            movers = []
            for item in (data or [])[:5]:
                movers.append(StockMover(
                    symbol=item.get("symbol", ""),
                    name=item.get("description", item.get("symbol", "")),
                    price=item.get("c", 0),
                    change_percent=item.get("dp", 0),
                ))
            return movers
        except Exception as e:
            log.warning(f"Failed to fetch top {category}: {e}")
            return []

    def _get_earnings(self) -> list[EarningsReport]:
        log.info("Fetching earnings calendar...")
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            data = self.client.earnings_calendar(
                _from=today,
                to=today,
                symbol="",
                international=False,
            )
            reports = []
            for item in (data.get("earningsCalendar", []))[:10]:
                reports.append(EarningsReport(
                    symbol=item.get("symbol", ""),
                    name=item.get("symbol", ""),
                    eps_actual=item.get("epsActual"),
                    eps_estimate=item.get("epsEstimate"),
                    revenue_actual=item.get("revenueActual"),
                    surprise_percent=item.get("surprisePercent"),
                ))
            return reports
        except Exception as e:
            log.warning(f"Failed to fetch earnings: {e}")
            return []

    def _get_economic_calendar(self) -> list[EconomicEvent]:
        log.info("Fetching economic calendar...")
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            data = self.client.economic_calendar(
                _from=today,
                to=today,
            )
            events = []
            for item in (data.get("economicCalendar", []))[:10]:
                events.append(EconomicEvent(
                    event=item.get("event", ""),
                    country=item.get("country", ""),
                    actual=str(item.get("actual", "")),
                    previous=str(item.get("previous", "")),
                    estimate=str(item.get("estimate", "")),
                    impact=item.get("impact", "low"),
                ))
            return events
        except Exception as e:
            log.warning(f"Failed to fetch economic calendar: {e}")
            return []

    def _get_crypto(self) -> dict:
        log.info("Fetching crypto prices...")
        crypto = {}
        pairs = {
            "BTC": "BINANCE:BTCUSDT",
            "ETH": "BINANCE:ETHUSDT",
        }
        for name, symbol in pairs.items():
            try:
                quote = self.client.quote(symbol)
                crypto[name] = {
                    "price": quote.get("c", 0),
                    "change_percent": quote.get("dp", 0),
                }
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
                crypto[name] = {"price": 0, "change_percent": 0}
        return crypto

    def _get_forex(self) -> dict:
        log.info("Fetching forex rates...")
        forex = {}
        pairs = {
            "EUR/USD": "OANDA:EUR_USD",
            "GBP/USD": "OANDA:GBP_USD",
            "USD/JPY": "OANDA:USD_JPY",
        }
        for name, symbol in pairs.items():
            try:
                quote = self.client.quote(symbol)
                forex[name] = {
                    "rate": quote.get("c", 0),
                    "change_percent": quote.get("dp", 0),
                }
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
                forex[name] = {"rate": 0, "change_percent": 0}
        return forex

    def _get_commodities(self) -> dict:
        log.info("Fetching commodity prices...")
        commodities = {}
        # Finnhub uses commodity futures symbols
        symbols = {
            "Gold": "OANDA:XAU_USD",
            "Oil (WTI)": "OANDA:BCO_USD",
        }
        for name, symbol in symbols.items():
            try:
                quote = self.client.quote(symbol)
                commodities[name] = {
                    "price": quote.get("c", 0),
                    "change_percent": quote.get("dp", 0),
                }
            except Exception as e:
                log.warning(f"Failed to fetch {name}: {e}")
                commodities[name] = {"price": 0, "change_percent": 0}
        return commodities
