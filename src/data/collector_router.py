from datetime import datetime

from src.data.categories import PodcastCategory
from src.data.models import MarketSnapshot
from src.data.worldmonitor_collector import WorldMonitorCollector
from src.data.gnews_collector import GNewsCollector
from src.data.newsdata_collector import NewsDataCollector
from src.data.guardian_collector import CurrentsCollector
from src.data.fred_collector import FredCollector
from src.data.coingecko_collector import CoinGeckoCollector
from src.utils.logger import log


def _has_key(config: dict, key_name: str) -> bool:
    val = config.get(key_name, "")
    return bool(val) and "your_" not in val


class CategoryCollectorRouter:
    """Routes selected categories to data collectors.

    Primary: World Monitor (no key needed, covers all categories)
    Supplements per category:
      - Finance Macro: FRED (treasury yields)
      - Finance Micro: (WM covers stocks)
      - Crypto: CoinGecko (DeFi, trending, global stats — no key needed)
      - Geopolitics: GNews (headlines) + Currents (world news)
      - AI Updates: GNews (AI search) + NewsData (AI/tech) + Currents (AI search)
    """

    def __init__(self, config: dict, categories: list[PodcastCategory]):
        self.config = config
        self.categories = categories

    def collect_all(self, status_callback=None) -> MarketSnapshot:
        log.info(f"Collecting data for categories: {[c.value for c in self.categories]}")
        snapshot_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "categories": [c.value for c in self.categories],
        }

        # ── World Monitor (primary source for all categories) ──
        if status_callback:
            status_callback("Fetching data from World Monitor...")

        wm = WorldMonitorCollector()
        wm_data = wm.collect(self.categories, status_callback=status_callback)
        snapshot_data.update(wm_data)

        # ── Shared collector instances (lazy, reused across categories) ──
        gnews = None
        currents = None

        def get_gnews():
            nonlocal gnews
            if gnews is None and _has_key(self.config, "gnews_api_key"):
                gnews = GNewsCollector(api_key=self.config["gnews_api_key"])
            return gnews

        def get_currents():
            nonlocal currents
            if currents is None and _has_key(self.config, "currents_api_key"):
                currents = CurrentsCollector(api_key=self.config["currents_api_key"])
            return currents

        # ── Finance Macro: supplement with FRED ────────────────
        if PodcastCategory.FINANCE_MACRO in self.categories:
            if _has_key(self.config, "fred_api_key"):
                if status_callback:
                    status_callback("Fetching treasury yields from FRED...")
                log.info("Supplementing Finance Macro with FRED")
                fred = FredCollector(api_key=self.config["fred_api_key"])
                fred_data = fred.collect_all()
                snapshot_data["macro_indicators"] = fred_data.get("macro_indicators", [])

        # ── Crypto: supplement with CoinGecko ──────────────────
        if PodcastCategory.CRYPTO in self.categories:
            if status_callback:
                status_callback("Fetching DeFi & trending from CoinGecko...")
            log.info("Supplementing Crypto with CoinGecko")
            cg = CoinGeckoCollector()
            cg_data = cg.collect_all()
            # Merge CoinGecko global stats and trending (WM doesn't have these)
            snapshot_data["crypto_global"] = cg_data.get("crypto_global", {})
            snapshot_data["crypto_trending"] = cg_data.get("crypto_trending", [])

        # ── Geopolitics: supplement with GNews + Currents ──────
        if PodcastCategory.GEOPOLITICS in self.categories:
            geo_items = snapshot_data.get("geopolitics", [])

            g = get_gnews()
            if g:
                if status_callback:
                    status_callback("Fetching geopolitics from GNews...")
                geo_items.extend(g.collect_geopolitics())

            c = get_currents()
            if c:
                if status_callback:
                    status_callback("Fetching geopolitics from Currents...")
                geo_items.extend(c.collect_geopolitics())

            snapshot_data["geopolitics"] = geo_items

        # ── AI Updates: supplement with GNews + NewsData + Currents ──
        if PodcastCategory.AI_UPDATES in self.categories:
            if status_callback:
                status_callback("Fetching AI news from dedicated sources...")
            log.info("Supplementing AI Updates with all available APIs")

            ai_items = snapshot_data.get("ai_updates", [])

            if _has_key(self.config, "newsdata_api_key"):
                newsdata = NewsDataCollector(api_key=self.config["newsdata_api_key"])
                nd_data = newsdata.collect_all()
                ai_items.extend(nd_data.get("ai_updates", []))

            g = get_gnews()
            if g:
                ai_items.extend(g.collect_ai_updates())

            c = get_currents()
            if c:
                ai_items.extend(c.collect_ai_updates())

            snapshot_data["ai_updates"] = ai_items

        snapshot = MarketSnapshot(**snapshot_data)
        log.info("Category collection complete")
        return snapshot
