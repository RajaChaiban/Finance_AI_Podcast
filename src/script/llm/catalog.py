"""Curated LLM catalog for the Generate UI.

The Generate page shows a single flat dropdown — each entry encodes a
(provider, model_tag) pair plus the human-readable label and a short
hint. Settings still accepts free-text for power users who want a tag
that isn't in the catalog.

If you add an Ollama option here, also document the rough VRAM
requirement in `note` so users on smaller cards don't pick something
that won't load.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMOption:
    id: str         # stable form value, e.g. "gemma4-26b"
    label: str      # "Gemma 4 26B"
    provider: str   # "gemini" | "ollama"
    model: str      # model tag passed to the provider, e.g. "gemma4:26b"
    note: str       # one-line UI hint
    is_local: bool  # used for the icon in the dropdown


LLM_CATALOG: list[LLMOption] = [
    # ── Cloud (Gemini 3 — preview, newest) ─────────────────────────
    # Note: gemini-3-pro-preview was deprecated 2026-03-09; use 3.1 Pro
    # going forward. Listed first so the dropdown surfaces the newest
    # options without changing the existing default — _settings_defaults
    # resolves the saved (provider, model) to its catalog id by exact
    # match, so Gemini 2.5 Flash stays selected for users who haven't
    # explicitly switched.
    LLMOption(
        id="gemini-31-pro",
        label="Gemini 3.1 Pro (preview)",
        provider="gemini",
        model="gemini-3.1-pro-preview",
        note="cloud · frontier · preview",
        is_local=False,
    ),
    LLMOption(
        id="gemini-3-flash",
        label="Gemini 3 Flash (preview)",
        provider="gemini",
        model="gemini-3-flash-preview",
        note="cloud · frontier-class · preview",
        is_local=False,
    ),
    LLMOption(
        id="gemini-31-flash-lite",
        label="Gemini 3.1 Flash Lite (preview)",
        provider="gemini",
        model="gemini-3.1-flash-lite-preview",
        note="cloud · cheapest 3.x · preview",
        is_local=False,
    ),
    # ── Cloud (Gemini 2.5 — stable) ────────────────────────────────
    LLMOption(
        id="gemini-flash",
        label="Gemini 2.5 Flash",
        provider="gemini",
        model="gemini-2.5-flash",
        note="default · cloud · fast",
        is_local=False,
    ),
    LLMOption(
        id="gemini-pro",
        label="Gemini 2.5 Pro",
        provider="gemini",
        model="gemini-2.5-pro",
        note="cloud · higher quality, slower",
        is_local=False,
    ),
    LLMOption(
        id="gemini-flash-lite",
        label="Gemini 2.5 Flash Lite",
        provider="gemini",
        model="gemini-2.5-flash-lite",
        note="cloud · cheapest · use as 503 fallback",
        is_local=False,
    ),
    # ── Local (Ollama) ─────────────────────────────────────────────
    LLMOption(
        id="gemma4-26b",
        label="Gemma 4 26B",
        provider="ollama",
        model="gemma4:26b",
        note="local · MoE 3.8B active · ~16 GB · recommended",
        is_local=True,
    ),
    LLMOption(
        id="gemma4-31b",
        label="Gemma 4 31B",
        provider="ollama",
        model="gemma4:31b",
        note="local · dense · ~20 GB · top Gemma",
        is_local=True,
    ),
    LLMOption(
        id="gemma4-e4b",
        label="Gemma 4 4B",
        provider="ollama",
        model="gemma4:e4b",
        note="local · ~3 GB · 8 GB-card tier",
        is_local=True,
    ),
    LLMOption(
        id="qwen35-27b",
        label="Qwen 3.5 27B",
        provider="ollama",
        model="qwen3.5:27b",
        note="local · ~16 GB · top instruction-following",
        is_local=True,
    ),
    LLMOption(
        id="qwen35-9b",
        label="Qwen 3.5 9B",
        provider="ollama",
        model="qwen3.5:9b",
        note="local · ~6 GB · 8 GB-card tier",
        is_local=True,
    ),
    LLMOption(
        id="qwen35-35b-a3b",
        label="Qwen 3.5 35B (MoE)",
        provider="ollama",
        model="qwen3.5:35b-a3b",
        note="local · 3B active · spills to RAM · fast iteration",
        is_local=True,
    ),
    LLMOption(
        id="mistral-small-31",
        label="Mistral Small 3.1 24B",
        provider="ollama",
        model="mistral-small3.1:24b",
        note="local · ~15 GB · concise output",
        is_local=True,
    ),
    LLMOption(
        id="gpt-oss-20b",
        label="GPT-OSS 20B",
        provider="ollama",
        model="gpt-oss:20b",
        note="local · ~16 GB · OpenAI open-weights",
        is_local=True,
    ),
    LLMOption(
        id="llama31-8b",
        label="Llama 3.1 8B",
        provider="ollama",
        model="llama3.1:8b",
        note="local · ~5 GB · widely available",
        is_local=True,
    ),
]


CATALOG_BY_ID: dict[str, LLMOption] = {opt.id: opt for opt in LLM_CATALOG}


def get_option(option_id: str) -> LLMOption | None:
    """Return the catalog entry matching ``option_id`` (or None)."""
    return CATALOG_BY_ID.get(option_id)


def default_option_id(provider: str | None, model: str | None) -> str:
    """Pick the catalog id that best matches the saved provider/model.

    Falls back to the first cloud option so the UI always has something
    selected even when Settings holds an off-catalog tag.
    """
    if provider and model:
        for opt in LLM_CATALOG:
            if opt.provider == provider and opt.model == model:
                return opt.id
    return LLM_CATALOG[0].id
