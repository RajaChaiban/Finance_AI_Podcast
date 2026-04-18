import httpx
from src.data.models import CryptoAsset
from src.utils.logger import log

BASE_URL = "https://api.coingecko.com/api/v3"


class CoinGeckoCollector:
    def __init__(self):
        pass  # No API key needed for free tier

    def collect_all(self) -> dict:
        log.info("Collecting data from CoinGecko...")
        data = {
            "crypto_extended": self._get_top_coins(),
            "crypto_global": self._get_global_stats(),
            "crypto_trending": self._get_trending(),
        }
        log.info(f"CoinGecko collection complete: {len(data['crypto_extended'])} coins")
        return data

    def _get_top_coins(self) -> list[CryptoAsset]:
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{BASE_URL}/coins/markets", params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 10,
                    "page": 1,
                    "sparkline": "false",
                })
                resp.raise_for_status()
                data = resp.json()

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

    def _get_global_stats(self) -> dict:
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{BASE_URL}/global")
                resp.raise_for_status()
                data = resp.json().get("data", {})

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

    def _get_trending(self) -> list[str]:
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{BASE_URL}/search/trending")
                resp.raise_for_status()
                data = resp.json()

            coins = data.get("coins", [])
            return [coin.get("item", {}).get("name", "") for coin in coins[:7]]
        except Exception as e:
            log.warning(f"Failed to fetch CoinGecko trending: {e}")
            return []
