import httpx
from src.data.models import GeopoliticsItem, AIUpdateItem
from src.data.classifiers import classify_ai_subcategory
from src.utils.logger import log

BASE_URL = "https://api.currentsapi.services/v1"


class CurrentsCollector:
    """Collects news from Currents API.
    Free tier: 1000 requests/day, personal email signup, no credit card.
    Signup: https://currentsapi.services/en/register
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    def collect_geopolitics(self) -> list[GeopoliticsItem]:
        log.info("Collecting geopolitics from Currents API...")
        items = self._fetch_as_geopolitics(category="world", page_size=10)
        log.info(f"Currents geopolitics: {len(items)} articles")
        return items

    def collect_ai_updates(self) -> list[AIUpdateItem]:
        log.info("Collecting AI news from Currents API...")
        items = self._fetch_as_ai(
            keywords="artificial intelligence OR AI model OR machine learning OR deep learning",
            page_size=10,
        )
        log.info(f"Currents AI updates: {len(items)} articles")
        return items

    def _fetch_as_geopolitics(self, category: str, page_size: int) -> list[GeopoliticsItem]:
        try:
            articles = self._fetch_articles({"category": category, "page_size": page_size})
            return [
                GeopoliticsItem(
                    title=a.get("title", ""),
                    description=a.get("description", "") or "",
                    source=a.get("author", "") or "Currents",
                    published_at=a.get("published", ""),
                )
                for a in articles
            ]
        except Exception as e:
            log.warning(f"Failed to fetch Currents geopolitics: {e}")
            return []

    def _fetch_as_ai(self, keywords: str, page_size: int) -> list[AIUpdateItem]:
        try:
            articles = self._fetch_articles({"keywords": keywords, "page_size": page_size})
            items = []
            for a in articles:
                title = a.get("title", "") or ""
                desc = a.get("description", "") or ""
                items.append(AIUpdateItem(
                    title=title,
                    description=desc,
                    source=a.get("author", "") or "Currents",
                    published_at=a.get("published", ""),
                    subcategory=classify_ai_subcategory(title, desc),
                ))
            return items
        except Exception as e:
            log.warning(f"Failed to fetch Currents AI news: {e}")
            return []

    def _fetch_articles(self, params: dict) -> list[dict]:
        try:
            params["apiKey"] = self.api_key
            params["language"] = "en"
            with httpx.Client(timeout=30) as client:
                resp = client.get(f"{BASE_URL}/latest-news", params=params)
                resp.raise_for_status()
                return resp.json().get("news", [])
        except Exception as e:
            log.warning(f"Failed to fetch Currents API: {e}")
            return []
