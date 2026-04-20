from dataclasses import dataclass


BRIEF_STYLE = (
    "BREVITY OVERRIDE: This is the short edition. Cover only the single biggest story "
    "per requested category -- 1-2 exchanges per segment. Skip the 'What to Watch Tomorrow' "
    "section. Skip bridges that don't add analytical value. Opening disclaimer still mandatory. "
    "A tight briefing wins."
)

DEEP_STYLE = (
    "DEEP MODE: Go one analytical layer deeper. For each category's 2-3 stories, add one "
    "cross-category consequence sentence (what else in the data this ripples into) and one "
    "counter-view sentence (the opposing read -- what would make this reading wrong). Expand "
    "'What to Watch Tomorrow' to 3-4 specific events with a why-it-matters note on each."
)


@dataclass(frozen=True)
class LengthPreset:
    key: str
    label: str
    target_words: int
    approx_minutes: str
    prompt_style: str


LENGTH_PRESETS: dict[str, LengthPreset] = {
    "brief":    LengthPreset("brief",    "Brief",      900, "5-7 min",   BRIEF_STYLE),
    "standard": LengthPreset("standard", "Standard",  2200, "14-18 min", ""),
    "deep":     LengthPreset("deep",     "Deep Dive", 3500, "22-28 min", DEEP_STYLE),
}

DEFAULT_PRESET_KEY = "standard"


def resolve_target_words(preset_key: str | None, num_categories: int) -> int | None:
    """Return the word target for a preset, clamped by category count.

    None input → None output (caller falls back to legacy per-category formula).
    """
    if preset_key is None:
        return None
    preset = LENGTH_PRESETS.get(preset_key)
    if preset is None:
        return None
    # A 3500-word deep dive with only one category asked is silly; scale by
    # categories requested but floor at half the preset target so 'brief' of
    # five categories doesn't balloon past the preset.
    per_cat_ceiling = num_categories * 600 if preset_key == "deep" else num_categories * 450
    floor = preset.target_words // 2
    return max(floor, min(preset.target_words, max(floor, per_cat_ceiling)))
