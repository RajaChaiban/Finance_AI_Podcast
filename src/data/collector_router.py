import os
import time
from datetime import datetime

import httpx

from src.data.categories import PodcastCategory
from src.data.models import MarketSnapshot
from src.data.worldmonitor_collector import WorldMonitorCollector
from src.data.gnews_collector import GNewsCollector
from src.data.newsdata_collector import NewsDataCollector
from src.data.currents_collector import CurrentsCollector
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
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            # One shared connection pool for every collector this run -- saves
            # the cost of TLS handshakes against the same hosts back to back.
            self._client = httpx.Client(
                timeout=30,
                follow_redirects=True,
                headers={"User-Agent": "MarketPulse/1.0"},
            )
        return self._client

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    # ── Snapshot cache ───────────────────────────────────────
    def _cache_path(self, cache_dir: str) -> str:
        date = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(cache_dir, f"{date}-snapshot.cache.json")

    def _try_load_cached(
        self,
        cache_dir: str,
        max_age_hours: float,
        status_callback=None,
    ) -> MarketSnapshot | None:
        path = self._cache_path(cache_dir)
        if not os.path.exists(path):
            return None
        age_hours = (time.time() - os.path.getmtime(path)) / 3600.0
        if age_hours > max_age_hours:
            log.info(f"Snapshot cache stale ({age_hours:.1f}h > {max_age_hours}h), refetching")
            return None
        try:
            cached = MarketSnapshot.load(path)
        except Exception as e:
            log.warning(f"Snapshot cache unreadable ({e}), refetching")
            return None
        # Reject cache if the saved run doesn't cover every category this run
        # needs. Prevents a macro-only cache from satisfying a crypto request.
        cached_cats = set(cached.categories or [])
        requested = {c.value for c in self.categories}
        if not requested.issubset(cached_cats):
            log.info(
                f"Snapshot cache covers {cached_cats}, need {requested}; refetching"
            )
            return None
        msg = f"Loaded snapshot from cache ({age_hours:.1f}h old)"
        log.info(msg)
        if status_callback:
            status_callback(msg)
        return cached

    def _save_cache(self, cache_dir: str, snapshot: MarketSnapshot):
        os.makedirs(cache_dir, exist_ok=True)
        try:
            snapshot.save(self._cache_path(cache_dir))
        except Exception as e:
            log.warning(f"Failed to write snapshot cache: {e}")

    def collect_all(
        self,
        status_callback=None,
        cache_dir: str | None = None,
        force_refresh: bool = False,
        max_age_hours: float = 6.0,
    ) -> MarketSnapshot:
        if cache_dir and not force_refresh:
            cached = self._try_load_cached(cache_dir, max_age_hours, status_callback)
            if cached is not None:
                return cached

        log.info(f"Collecting data for categories: {[c.value for c in self.categories]}")
        snapshot_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "categories": [c.value for c in self.categories],
        }

        client = self._get_client()

        # ── World Monitor (primary source for all categories) ──
        if status_callback:
            status_callback("Fetching data from World Monitor...")

        wm = WorldMonitorCollector(client=client)
        wm_data = wm.collect(self.categories, status_callback=status_callback)
        snapshot_data.update(wm_data)

        # ── Shared collector instances (lazy, reused across categories) ──
        gnews = None
        currents = None

        def get_gnews():
            nonlocal gnews
            if gnews is None and _has_key(self.config, "gnews_api_key"):
                gnews = GNewsCollector(api_key=self.config["gnews_api_key"], client=client)
            return gnews

        def get_currents():
            nonlocal currents
            if currents is None and _has_key(self.config, "currents_api_key"):
                currents = CurrentsCollector(api_key=self.config["currents_api_key"], client=client)
            return currents

        # ── Finance Macro: supplement with FRED ────────────────
        if PodcastCategory.FINANCE_MACRO in self.categories:
            if _has_key(self.config, "fred_api_key"):
                if status_callback:
                    status_callback("Fetching treasury yields from FRED...")
                log.info("Supplementing Finance Macro with FRED")
                fred = FredCollector(api_key=self.config["fred_api_key"], client=client)
                fred_data = fred.collect_all()
                snapshot_data["macro_indicators"] = fred_data.get("macro_indicators", [])

        # ── Crypto: supplement with CoinGecko ──────────────────
        if PodcastCategory.CRYPTO in self.categories:
            if status_callback:
                status_callback("Fetching DeFi & trending from CoinGecko...")
            log.info("Supplementing Crypto with CoinGecko")
            cg = CoinGeckoCollector(client=client)
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
                newsdata = NewsDataCollector(
                    api_key=self.config["newsdata_api_key"], client=client,
                )
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
        if cache_dir:
            self._save_cache(cache_dir, snapshot)
        log.info("Category collection complete")
        return snapshot
