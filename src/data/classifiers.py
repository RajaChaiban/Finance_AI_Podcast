"""Shared text classifiers used by multiple news collectors."""

from __future__ import annotations


_AI_SUBCATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("funding",       ("funding", "raised", "investment", "startup", "valuation")),
    ("regulation",    ("regulation", "law", "policy", "ban", "compliance")),
    ("research",      ("paper", "research", "study", "benchmark")),
    ("model_release", ("launch", "release", "model", "update", "version")),
)


def classify_ai_subcategory(title: str, description: str) -> str:
    """Bucket an AI news item into {funding, regulation, research, model_release, general}.

    Order matters: the first matching bucket wins. Buckets are checked in
    business-priority order (funding news is the most time-sensitive).
    """
    text = (title + " " + description).lower()
    for label, keywords in _AI_SUBCATEGORY_KEYWORDS:
        if any(kw in text for kw in keywords):
            return label
    return "general"
