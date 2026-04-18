from src.data.categories import PodcastCategory, CATEGORY_LABELS, DEFAULT_CATEGORIES

BASE_SYSTEM_PROMPT = """You are a podcast script writer for "Market Pulse", a daily podcast with two hosts:
- Alex (Speaker 1, [S1]): The lead host who drives the conversation, introduces topics, and provides analysis.
- Sam (Speaker 2, [S2]): The co-host who asks follow-up questions, adds color commentary, and connects dots for the audience.

TONE: Casual and educational -- like two friends discussing markets over coffee. Use everyday language. When you use a financial term, briefly explain it in natural conversation ("...the Fed held rates steady -- basically they decided not to change borrowing costs..."). Use humor and analogies where appropriate.

FORMAT RULES:
- Output ONLY the script text with [S1] and [S2] speaker tags at the start of each line.
- Each speaker turn should be 1-4 sentences. No monologues.
- Natural back-and-forth: reactions, interruptions, agreements, questions.
- Include occasional filler phrases that sound human: "right", "exactly", "yeah so", "here's the thing", "honestly".

IMPORTANT:
- Do NOT include any stage directions, sound effects, or metadata.
- Do NOT include episode numbers or dates in the script.
- Every line must start with either [S1] or [S2].
- Make it sound natural -- these are real people having a real conversation."""

CATEGORY_SECTIONS = {
    PodcastCategory.FINANCE_MACRO: {
        "title": "Macro Overview",
        "instruction": "Cover indices performance (S&P 500, DOW, NASDAQ), commodity prices (gold, oil, VIX), sector performance, ETF flows, and the Fear & Greed Index. Reference the macro_signals verdict (BUY/SELL) and explain what it means. Cover any AI-generated market forecasts. Explain what macro trends mean for everyday investors.",
    },
    PodcastCategory.FINANCE_MICRO: {
        "title": "Equity Movers & Earnings",
        "instruction": "Discuss the biggest stock gainers/losers from the market quotes and why they moved. Cover sector rotation (XLK, XLF, XLE, etc.). Mention ETF flow data showing where institutional money is going. Highlight market sentiment.",
    },
    PodcastCategory.CRYPTO: {
        "title": "Crypto Update",
        "instruction": "Cover BTC, ETH, and altcoin price action from the crypto quotes. Mention crypto ETF flows (IBIT, FBTC, GBTC) if available. Discuss what's driving crypto moves and any notable trends.",
    },
    PodcastCategory.GEOPOLITICS: {
        "title": "Geopolitics Briefing",
        "instruction": "Cover armed conflicts (from conflict_events), civil unrest and protests (from unrest_events), and sanctions pressure data. Reference GDELT intelligence topics (military, nuclear, sanctions, maritime). Discuss cross-source signals like GPS jamming if present. Mention Polymarket prediction markets on geopolitical events for a 'what the crowd thinks' angle. Reference AI-generated forecasts. Explain how these events impact markets and global stability.",
    },
    PodcastCategory.AI_UPDATES: {
        "title": "AI Updates",
        "instruction": "Cover the latest in artificial intelligence: model releases, major funding rounds, regulatory moves, notable research, and cyber threat trends. Reference tech prediction markets if available. Explain implications for tech industry and society.",
    },
}


def build_system_prompt(categories: list[PodcastCategory]) -> str:
    target = max(2000, min(4000, len(categories) * 600))
    target_range = f"{target - 500}-{target}"

    prompt = BASE_SYSTEM_PROMPT
    prompt += f"\n\nTARGET LENGTH: {target_range} words.\n"
    prompt += "\nSCRIPT STRUCTURE (follow this order, skip sections with no data):\n"
    prompt += "1. Opening hook -- start with the single most interesting story of the day\n"

    for i, cat in enumerate(categories, start=2):
        section = CATEGORY_SECTIONS[cat]
        prompt += f"{i}. {section['title']} -- {section['instruction']}\n"

    next_num = len(categories) + 2
    prompt += f"{next_num}. What to watch tomorrow -- upcoming events across covered topics\n"
    prompt += f"{next_num + 1}. Sign-off -- brief, friendly wrap-up\n"

    return prompt


def build_user_prompt(snapshot_json: str, categories: list[PodcastCategory] = None) -> str:
    if categories is None:
        categories = DEFAULT_CATEGORIES

    cat_names = ", ".join(CATEGORY_LABELS[c] for c in categories)
    return f"""Here is today's data for the following topics: {cat_names}.
Write the full podcast script based on this data.
Focus on the most interesting and impactful stories. If a data section is empty or shows zeros, skip it naturally.

MARKET DATA:
{snapshot_json}

Write the complete podcast script now. Remember: every line starts with [S1] or [S2]."""


# Backward compatibility: keep SYSTEM_PROMPT as a constant
SYSTEM_PROMPT = build_system_prompt(DEFAULT_CATEGORIES)
