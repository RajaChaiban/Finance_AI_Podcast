"""Text-level prosody / punctuation stressing for Kokoro TTS.

Kokoro's prosody responds to punctuation: commas insert short pauses,
em-dashes a longer beat, ellipses a trailing fall, exclamations lift the
contour, and letter-spaced tokens get enunciated individually. This module
rewrites segment text deterministically to steer those cues based on the
emotion tag attached to the segment. Pure functions — no model state.
"""

from __future__ import annotations

import re


EMOTION_SPEED = {
    "neutral": 1.00,
    "excited": 1.08,
    "curious": 1.00,
    "serious": 0.93,
    "warm": 0.96,
    "concerned": 0.90,
    "playful": 1.05,
}

EMOTION_PAUSE_MS = {
    "neutral": 300,
    "excited": 260,
    "curious": 340,
    "serious": 480,
    "warm": 380,
    "concerned": 500,
    "playful": 280,
}

# Tickers that should be letter-spaced for emphasis. Guarded against common
# English words (e.g., "IT", "SO", "OR") — we only match when the token
# appears in all caps AND was preceded by a recognized context.
KNOWN_TICKERS = {
    "SPY", "QQQ", "DIA", "VOO", "VTI", "IWM", "XLK", "XLF", "XLE", "XLV",
    "XLY", "XLP", "XLI", "XLU", "XLB", "XLC", "XLRE",
    "NVDA", "TSLA", "AAPL", "MSFT", "GOOG", "GOOGL", "META", "AMZN", "NFLX",
    "AMD", "INTC", "CRM", "ORCL", "AVGO", "TSM",
    "BTC", "ETH", "SOL", "XRP", "DOGE", "ADA",
    "IBIT", "FBTC", "GBTC", "ETHE",
    "JPM", "BAC", "GS", "MS", "WFC", "C",
    "VIX", "DXY",
}

CONNECTORS = [
    "however", "basically", "honestly", "here's the thing",
    "right", "exactly", "yeah so", "meanwhile", "so look",
]

_NUM_BIG = {
    "B": "billion", "b": "billion",
    "T": "trillion", "t": "trillion",
    "M": "million", "m": "million",
    "K": "thousand", "k": "thousand",
}

_DIGIT_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def _spell_number_fragment(frag: str) -> str:
    """Spell a number fragment digit-by-digit (for decimals)."""
    return " ".join(_DIGIT_WORDS.get(ch, ch) for ch in frag)


def _expand_money(match: re.Match) -> str:
    sign = match.group(1) or ""
    whole = match.group(2)
    decimal = match.group(3) or ""
    suffix = match.group(4) or ""
    unit = _NUM_BIG.get(suffix, "")
    parts = [f"{sign}{whole}"]
    if decimal:
        parts.append(f"point {_spell_number_fragment(decimal)}")
    if unit:
        parts.append(unit)
    parts.append("dollars")
    return " ".join(parts)


def _expand_percent(match: re.Match) -> str:
    sign = match.group(1) or ""
    whole = match.group(2)
    decimal = match.group(3) or ""
    out = f"{sign}{whole}"
    if decimal:
        out += f" point {_spell_number_fragment(decimal)}"
    return f"{out} percent"


def _expand_plain_big(match: re.Match) -> str:
    whole = match.group(1)
    suffix = match.group(2)
    unit = _NUM_BIG.get(suffix, "")
    return f"{whole} {unit}".strip()


def _expand_year(match: re.Match) -> str:
    """20XX → 'twenty XX' when XX is a plausible year in this conversation."""
    y = match.group(0)
    if y[:2] == "20" and 0 <= int(y[2:]) <= 99:
        tail = int(y[2:])
        if tail == 0:
            return "twenty hundred"
        tens = {0: "", 1: "ten", 2: "twenty", 3: "thirty", 4: "forty", 5: "fifty",
                6: "sixty", 7: "seventy", 8: "eighty", 9: "ninety"}
        ones = {0: "", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
                6: "six", 7: "seven", 8: "eight", 9: "nine",
                10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen",
                14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen",
                18: "eighteen", 19: "nineteen"}
        if tail < 20:
            tail_word = ones[tail]
        else:
            t, o = divmod(tail, 10)
            tail_word = tens[t] + (" " + ones[o] if o else "")
        return f"twenty {tail_word}".strip()
    return y


def _expand_numerics(text: str) -> str:
    # $1.2B / $500M / $3.50 → spoken form (must run before bare-number rules).
    text = re.sub(
        r"(-?)\$\s*(\d+)(?:\.(\d+))?\s*([BTMKbtmk])?",
        _expand_money,
        text,
    )
    # -3.5% / +10% / 2.5% → percent form
    text = re.sub(
        r"([+-]?)(\d+)(?:\.(\d+))?\s*%",
        _expand_percent,
        text,
    )
    # Plain 1.2B / 500M (without $)
    text = re.sub(
        r"\b(\d+(?:\.\d+)?)([BTMK])\b",
        _expand_plain_big,
        text,
    )
    # Years 20XX — `\b` blocks adjacent word chars (so "2025c" is safe); the
    # negative lookahead also blocks decimals like "2025.50" that slipped past
    # _expand_money (e.g. a bare number without a $ prefix).
    text = re.sub(r"\b(20\d{2})\b(?!\.\d)", _expand_year, text)
    # Q3 / Q4 → Q three / Q four
    text = re.sub(
        r"\bQ([1-4])\b",
        lambda m: f"Q {_DIGIT_WORDS[m.group(1)]}",
        text,
    )
    return text


_TICKER_ADJACENT = set(",. !?;:\n\t()-\"'")


def _emphasize_tickers(text: str) -> str:
    def repl(m: re.Match) -> str:
        ticker = m.group(1)
        if ticker not in KNOWN_TICKERS:
            return m.group(0)
        spaced = " ".join(ticker)
        # Only add emphasis commas when the ticker isn't already adjacent to
        # punctuation or sentence boundaries — otherwise we produce double
        # commas like ", N V D A,." on inputs like "NVDA." or "NVDA, AAPL".
        start, end = m.span()
        before = text[start - 1] if start > 0 else ""
        after = text[end] if end < len(text) else ""
        prefix = "" if before == "" or before in _TICKER_ADJACENT else ", "
        suffix = "" if after == "" or after in _TICKER_ADJACENT else ","
        return f"{prefix}{spaced}{suffix}"

    # Match 2-5 uppercase letter runs with optional leading $; guard so common
    # small English words like "OR/IT/SO" aren't caught (they're not in the set).
    return re.sub(r"\$?([A-Z]{2,5})\b", repl, text)


def _insert_micropauses(text: str) -> str:
    for conn in CONNECTORS:
        # Add trailing comma after connector if it doesn't already end the clause.
        pattern = rf"\b({re.escape(conn)})\b(?![,.;!?])"
        text = re.sub(pattern, r"\1,", text, flags=re.IGNORECASE)
    return text


def _apply_emotion_prosody(text: str, emotion: str) -> str:
    if emotion == "excited":
        # Lift the last sentence's terminal punctuation to exclamation if it's a period.
        # Only one replacement, at the end, to avoid every sentence shouting.
        text = re.sub(r"\.(\s*)$", r"!\1", text)
    elif emotion == "serious":
        # Swap the first mid-sentence comma for an em-dash, preserving sentence
        # terminators so "Look at this." stays intact.
        if "—" not in text and "--" not in text:
            text = re.sub(r"^([A-Z][^,.!?]{8,40}?),\s*",
                          r"\1 — ", text, count=1)
    elif emotion == "curious":
        # Questions get a trailing ellipsis for a rising, open feel.
        text = re.sub(r"\?(\s*)$", r"...\1", text)
    elif emotion == "warm":
        # Add a soft comma beat after the first few words if none present early.
        if not re.match(r"^\S+\s+\S+\s*,", text):
            text = re.sub(r"^(\S+\s+\S+\s+\S+)\s", r"\1, ", text, count=1)
    elif emotion == "concerned":
        # Pull the listener in with a leading "look," style beat.
        text = re.sub(r"\.(\s*)$", r"...\1", text)
    elif emotion == "playful":
        # Light, bouncy: no hard changes; a trailing beat only if the line is a one-liner.
        if len(text) < 80 and text.rstrip().endswith("."):
            text = text.rstrip(".") + "!"
    # neutral: no changes
    return text


def stress_text(text: str, emotion: str = "neutral") -> str:
    """Rewrite segment text to steer Kokoro's prosody for the given emotion."""
    if not text:
        return text
    text = _expand_numerics(text)
    text = _emphasize_tickers(text)
    text = _insert_micropauses(text)
    text = _apply_emotion_prosody(text, emotion)
    # Collapse any accidental double spaces the rewrites introduced.
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def scale_speed(base_speed: float, emotion: str) -> float:
    return base_speed * EMOTION_SPEED.get(emotion, 1.0)


def pause_ms(current: str, following: str | None) -> int:
    """Inter-segment pause in milliseconds.

    Use the max of the current segment's "exit pause" and the next segment's
    "entry pause" so both sides' emotional weight is respected. At section
    boundaries or between distinct emotional states, add a small extra beat.
    """
    cur = EMOTION_PAUSE_MS.get(current, 300)
    if following is None:
        return cur
    nxt = EMOTION_PAUSE_MS.get(following, 300)
    base = max(cur, nxt)
    # A shift between very different energies gets an extra 80ms of space.
    if current != following and {current, following} & {"serious", "concerned"}:
        base += 80
    return base
