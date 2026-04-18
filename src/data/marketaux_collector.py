import httpx
from src.data.models import NewsItem
from src.utils.logger import log

BASE_URL = "https://api.marketaux.com/v1/news/all"


class MarketAuxCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def collect_all(self) -> dict:
        log.info("Collecting news from MarketAux...")
        news_items = self._get_top_news()
        sentiment = self._compute_market_sentiment(news_items)
        log.info(f"MarketAux collection complete: {len(news_items)} articles, sentiment={sentiment}")
        return {
            "news": news_items,
            "market_sentiment": sentiment,
        }

    def _get_top_news(self) -> list[NewsItem]:
        try:
            params = {
                "api_token": self.api_key,
                "language": "en",
                "limit": 20,
                "sort": "published_desc",
            }
            with httpx.Client(timeout=30) as client:
                resp = client.get(BASE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            articles = []
            for item in data.get("data", []):
                entities = [
                    e.get("symbol", "")
                    for e in item.get("entities", [])
                    if e.get("symbol")
                ]
                articles.append(NewsItem(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    source=item.get("source", ""),
                    published_at=item.get("published_at", ""),
                    sentiment=item.get("sentiment", 0.0) or 0.0,
                    entities=entities,
                ))
            return articles
        except Exception as e:
            log.warning(f"Failed to fetch MarketAux news: {e}")
            return []

    def _compute_market_sentiment(self, news: list[NewsItem]) -> str:
        if not news:
            return "neutral"
        avg = sum(n.sentiment for n in news) / len(news)
        if avg > 0.15:
            return "bullish"
        elif avg < -0.15:
            return "bearish"
        return "neutral"
