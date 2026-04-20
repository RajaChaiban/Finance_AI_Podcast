import httpx
from src.data.models import CryptoAsset
from src.utils.logger import log
from src.utils.retry import retry_http

BASE_URL = "https://api.coingecko.com/api/v3"


class CoinGeckoCollector:
    def __init__(self, client: httpx.Client | None = None):
        # Free tier needs no API key; injected client lets the router pool
        # connections with the rest of the pipeline.
        self.client = client

    def collect_all(self) -> dict:
        log.info("Collecting data from CoinGecko...")
        data = {
            "crypto_extended": self._get_top_coins(),
            "crypto_global": self._get_global_stats(),
            "crypto_trending": self._get_trending(),
        }
        log.info(f"CoinGecko collection complete: {len(data['crypto_extended'])} coins")
        return data

    def _get(self, path: str, params: dict | None = None):
        url = f"{BASE_URL}{path}"
        if self.client is not None:
            return self.client.get(url, params=params)
        with httpx.Client(timeout=30) as client:
            return client.get(url, params=params)

    @retry_http()
    def _raw_top_coins(self) -> list:
        resp = self._get("/coins/markets", params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": "false",
        })
        resp.raise_for_status()
        return resp.json()

    def _get_top_coins(self) -> list[CryptoAsset]:
        try:
            data = self._raw_top_coins()
            coins = []
            for item in data:
                coins.append(CryptoAsset(
                    symbol=item.get("symbol", "").upper(),
                    name=item.get("name", ""),
                    price=item.get("current_price", 0) or 0,
                    change_percent_24h=item.get("price_change_percentage_24h", 0) or 0,
                    market_cap=item.get("market_cap", 0) or 0,
                    volume_24h=item.get("total_volume", 0) or 0,
                ))
            return coins
        except Exception as e:
            log.warning(f"Failed to fetch CoinGecko top coins: {e}")
            return []

    @retry_http()
    def _raw_global_stats(self) -> dict:
        resp = self._get("/global")
        resp.raise_for_status()
        return resp.json()

    def _get_global_stats(self) -> dict:
        try:
            data = self._raw_global_stats().get("data", {})
            return {
                "total_market_cap_usd": data.get("total_market_cap", {}).get("usd", 0),
                "total_volume_24h_usd": data.get("total_volume", {}).get("usd", 0),
                "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
                "eth_dominance": data.get("market_cap_percentage", {}).get("eth", 0),
                "active_cryptocurrencies": data.get("active_cryptocurrencies", 0),
            }
        except Exception as e:
            log.warning(f"Failed to fetch CoinGecko global stats: {e}")
            return {}

    @retry_http()
    def _raw_trending(self) -> dict:
        resp = self._get("/search/trending")
        resp.raise_for_status()
        return resp.json()

    def _get_trending(self) -> list[str]:
        try:
            data = self._raw_trending()
            coins = data.get("coins", [])
            return [coin.get("item", {}).get("name", "") for coin in coins[:7]]
        except Exception as e:
            log.warning(f"Failed to fetch CoinGecko trending: {e}")
            return []
