import httpx
from src.data.models import GeopoliticsItem, AIUpdateItem
from src.utils.logger import log
from src.utils.retry import retry_http

BASE_URL = "https://gnews.io/api/v4"


class GNewsCollector:
    def __init__(self, api_key: str, client: httpx.Client | None = None):
        self.api_key = api_key
        self.client = client

    def collect_geopolitics(self) -> list[GeopoliticsItem]:
        log.info("Collecting geopolitics news from GNews...")
        items = []

        # World headlines
        headlines = self._fetch_articles("/top-headlines", params={
            "category": "world",
            "lang": "en",
            "max": 10,
        })
        for article in headlines:
            items.append(GeopoliticsItem(
                title=article.get("title", ""),
                description=article.get("description", "") or "",
                source=article.get("source", {}).get("name", ""),
                published_at=article.get("publishedAt", ""),
            ))

        log.info(f"GNews geopolitics: {len(items)} articles")
        return items

    def collect_ai_updates(self) -> list[AIUpdateItem]:
        log.info("Collecting AI news from GNews...")
        articles = self._fetch_articles("/search", params={
            "q": '"artificial intelligence" OR "AI model" OR "large language model" OR "machine learning"',
            "lang": "en",
            "max": 10,
        })

        items = []
        for article in articles:
            items.append(AIUpdateItem(
                title=article.get("title", ""),
                description=article.get("description", "") or "",
                source=article.get("source", {}).get("name", ""),
                published_at=article.get("publishedAt", ""),
                subcategory="general",
            ))

        log.info(f"GNews AI updates: {len(items)} articles")
        return items

    @retry_http()
    def _raw_fetch(self, endpoint: str, params: dict) -> dict:
        if self.client is not None:
            resp = self.client.get(f"{BASE_URL}{endpoint}", params=params)
        else:
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{BASE_URL}{endpoint}", params=params)
        resp.raise_for_status()
        return resp.json()

    def _fetch_articles(self, endpoint: str, params: dict) -> list[dict]:
        try:
            params["apikey"] = self.api_key
            data = self._raw_fetch(endpoint, params)
            return data.get("articles", [])
        except Exception as e:
            log.warning(f"Failed to fetch GNews {endpoint}: {e}")
            return []
