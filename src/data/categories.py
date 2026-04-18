from enum import Enum


class PodcastCategory(str, Enum):
    FINANCE_MACRO = "finance_macro"
    FINANCE_MICRO = "finance_micro"
    CRYPTO = "crypto"
    GEOPOLITICS = "geopolitics"
    AI_UPDATES = "ai_updates"


CATEGORY_LABELS = {
    PodcastCategory.FINANCE_MACRO: "Finance \u2014 Macro",
    PodcastCategory.FINANCE_MICRO: "Finance \u2014 Micro",
    PodcastCategory.CRYPTO: "Crypto",
    PodcastCategory.GEOPOLITICS: "Geopolitics",
    PodcastCategory.AI_UPDATES: "AI Updates",
}

CATEGORY_DESCRIPTIONS = {
    PodcastCategory.FINANCE_MACRO: "GDP, CPI, interest rates, Fed decisions, employment, treasury yields, forex, commodities",
    PodcastCategory.FINANCE_MICRO: "Earnings reports, individual stock movers, sector performance, financial news",
    PodcastCategory.CRYPTO: "BTC/ETH/altcoin prices, DeFi metrics, market dominance, trending coins",
    PodcastCategory.GEOPOLITICS: "Sanctions, trade policy, conflicts, elections, international relations",
    PodcastCategory.AI_UPDATES: "Model releases, funding rounds, regulatory moves, research papers, industry news",
}

DEFAULT_CATEGORIES = [PodcastCategory.FINANCE_MACRO, PodcastCategory.FINANCE_MICRO]

# Maps each category to the env var names it requires
# World Monitor is the primary source (no key needed).
# Only supplementary sources need keys.
CATEGORY_API_KEYS = {
    PodcastCategory.FINANCE_MACRO: [],      # World Monitor (no key)
    PodcastCategory.FINANCE_MICRO: [],      # World Monitor (no key)
    PodcastCategory.CRYPTO: [],             # World Monitor (no key)
    PodcastCategory.GEOPOLITICS: [],        # World Monitor primary; GNews optional supplement
    PodcastCategory.AI_UPDATES: [],         # NewsData + GNews optional supplements
}

# Human-readable names for API keys (for UI display)
API_KEY_LABELS = {
    "finnhub_api_key": "Finnhub",
    "marketaux_api_key": "MarketAux",
    "gemini_api_key": "Gemini",
    "fred_api_key": "FRED",
    "gnews_api_key": "GNews",
    "currents_api_key": "Currents",
    "newsdata_api_key": "NewsData",
}
