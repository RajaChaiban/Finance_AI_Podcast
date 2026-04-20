import httpx
from src.data.models import AIUpdateItem
from src.data.classifiers import classify_ai_subcategory
from src.utils.logger import log
from src.utils.retry import retry_http

BASE_URL = "https://newsdata.io/api/1/latest"


class NewsDataCollector:
    def __init__(self, api_key: str, client: httpx.Client | None = None):
        self.api_key = api_key
        self.client = client

    def collect_all(self) -> dict:
        log.info("Collecting AI news from NewsData.io...")
        items = self._get_ai_news()
        log.info(f"NewsData collection complete: {len(items)} articles")
        return {"ai_updates": items}

    @retry_http()
    def _raw_fetch(self) -> dict:
        params = {
            "apikey": self.api_key,
            "category": "technology",
            "q": "artificial intelligence OR AI model OR machine learning OR deep learning",
            "language": "en",
            "size": 10,
        }
        if self.client is not None:
            resp = self.client.get(BASE_URL, params=params)
        else:
            with httpx.Client(timeout=30) as client:
                resp = client.get(BASE_URL, params=params)
        resp.raise_for_status()
        return resp.json()

    def _get_ai_news(self) -> list[AIUpdateItem]:
        try:
            data = self._raw_fetch()
            results = data.get("results", [])
            items = []
            for article in results:
                title = article.get("title", "") or ""
                description = article.get("description", "") or ""
                items.append(AIUpdateItem(
                    title=title,
                    description=description,
                    source=article.get("source_name", "") or article.get("source_id", ""),
                    published_at=article.get("pubDate", ""),
                    subcategory=classify_ai_subcategory(title, description),
                ))
            return items
        except Exception as e:
            log.warning(f"Failed to fetch NewsData AI news: {e}")
            return []
