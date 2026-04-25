"""End-to-end wiring tests for the Market Pulse pipeline.

These tests cover the contract between the UI layer and the pipeline:
  - Every `PodcastCategory` the UI can offer has complete metadata.
  - Every voice the UI can offer is usable as an anchor for S1 or S2.
  - Every (male, female) anchor pair the UI permits yields a valid recipe set.
  - The collector router wires up for every non-empty subset of categories.
  - The script generator cleans its output correctly for the TTS stage.
  - The TTS segment parser accepts the script format the generator emits.

No external APIs are contacted — Gemini, Kokoro, and the data collectors are
mocked or tested in isolation so the suite runs fast and offline.
"""

from __future__ import annotations

from itertools import combinations
from unittest.mock import MagicMock, patch

import pytest

from src.audio.kokoro_engine import KokoroEngine
from src.audio.voice_blender import (
    ALL_VOICE_IDS, DEFAULT_RECIPES, EMOTIONS, VOICE_CATALOG,
    BlendRecipe, build_recipes, voice_label,
)
from src.data.categories import (
    API_KEY_LABELS, CATEGORY_API_KEYS, CATEGORY_DESCRIPTIONS,
    CATEGORY_LABELS, DEFAULT_CATEGORIES, PodcastCategory,
)
from src.data.collector_router import CategoryCollectorRouter
from src.script.generator import ScriptGenerator


MALE_VOICE_IDS = [v["id"] for v in VOICE_CATALOG if v["gender"] == "male"]
FEMALE_VOICE_IDS = [v["id"] for v in VOICE_CATALOG if v["gender"] == "female"]
VALID_GRADES = {"A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F+", "F"}


# ─── Voice catalog ────────────────────────────────────────────────────────────

class TestVoiceCatalog:
    def test_ids_are_unique(self):
        ids = [v["id"] for v in VOICE_CATALOG]
        assert len(ids) == len(set(ids)), "duplicate voice ids in VOICE_CATALOG"

    def test_all_voice_ids_tuple_matches_catalog(self):
        assert ALL_VOICE_IDS == tuple(v["id"] for v in VOICE_CATALOG)

    @pytest.mark.parametrize("voice", VOICE_CATALOG, ids=[v["id"] for v in VOICE_CATALOG])
    def test_entry_has_required_fields(self, voice):
        for field in ("id", "label", "gender", "region", "grade"):
            assert field in voice and voice[field], f"{voice.get('id')} missing {field}"
        assert voice["gender"] in {"male", "female"}
        assert voice["region"] in {"us", "uk"}
        assert voice["grade"] in VALID_GRADES

    def test_has_both_genders(self):
        assert MALE_VOICE_IDS, "no male voices in catalog"
        assert FEMALE_VOICE_IDS, "no female voices in catalog"

    @pytest.mark.parametrize("voice_id", ALL_VOICE_IDS)
    def test_voice_label_is_human_readable(self, voice_id):
        label = voice_label(voice_id)
        assert voice_id not in label or " -- " in label, (
            f"voice_label({voice_id}) should include the grade, got {label!r}"
        )


# ─── Podcast categories ───────────────────────────────────────────────────────

class TestPodcastCategories:
    @pytest.mark.parametrize("cat", list(PodcastCategory), ids=[c.value for c in PodcastCategory])
    def test_every_category_has_complete_metadata(self, cat):
        assert cat in CATEGORY_LABELS and CATEGORY_LABELS[cat]
        assert cat in CATEGORY_DESCRIPTIONS and CATEGORY_DESCRIPTIONS[cat]
        assert cat in CATEGORY_API_KEYS  # may be empty list, but key must exist

    def test_default_categories_are_valid(self):
        for cat in DEFAULT_CATEGORIES:
            assert isinstance(cat, PodcastCategory)

    def test_api_key_labels_cover_referenced_keys(self):
        for required in CATEGORY_API_KEYS.values():
            for key in required:
                assert key in API_KEY_LABELS, f"missing label for {key}"


# ─── Emotion recipes for every voice pairing the UI permits ───────────────────

class TestBuildRecipesMatrix:
    """UI lets the user pick any male voice for S1 and any female voice for S2.
    Every such pairing must produce a coherent recipe set for all 7 emotions.
    """

    @pytest.mark.parametrize("s1_voice", MALE_VOICE_IDS)
    @pytest.mark.parametrize("s2_voice", FEMALE_VOICE_IDS)
    def test_every_anchor_pair_builds_valid_recipes(self, s1_voice, s2_voice):
        recipes = build_recipes(s1_voice, s2_voice)

        # Every (speaker, emotion) pair present in the defaults must remap cleanly.
        for key in DEFAULT_RECIPES:
            assert key in recipes, f"build_recipes dropped key {key}"

        for speaker in ("S1", "S2"):
            for emotion in EMOTIONS:
                recipe = recipes[(speaker, emotion)]
                assert isinstance(recipe, BlendRecipe)
                assert recipe.timbre_weights, f"empty timbre for {speaker}:{emotion}"
                # Weights must be positive and normalisable.
                total = sum(recipe.timbre_weights.values())
                assert total > 0, f"non-positive timbre total for {speaker}:{emotion}"
                if recipe.prosody_weights is not None:
                    p_total = sum(recipe.prosody_weights.values())
                    assert p_total > 0, f"non-positive prosody total for {speaker}:{emotion}"

    @pytest.mark.parametrize("s1_voice", MALE_VOICE_IDS)
    @pytest.mark.parametrize("s2_voice", FEMALE_VOICE_IDS)
    def test_anchor_dominates_neutral_recipe(self, s1_voice, s2_voice):
        # KokoroEngine forces neutral → anchor, so build_recipes must not emit
        # a neutral recipe that contradicts that (tested indirectly: the engine
        # overrides it, but we still assert the shape here).
        recipes = build_recipes(s1_voice, s2_voice)
        s1_neutral = recipes[("S1", "neutral")]
        s2_neutral = recipes[("S2", "neutral")]
        assert len(s1_neutral.timbre_weights) == 1
        assert len(s2_neutral.timbre_weights) == 1


# ─── Collector router for every category subset ───────────────────────────────

ALL_CATEGORIES = list(PodcastCategory)
NON_EMPTY_SUBSETS = [
    list(combo)
    for r in range(1, len(ALL_CATEGORIES) + 1)
    for combo in combinations(ALL_CATEGORIES, r)
]


class TestCollectorRouter:
    @pytest.fixture
    def empty_config(self):
        # No API keys → only World Monitor (primary) should be invoked.
        return {
            "gemini_api_key": "",
            "fred_api_key": "",
            "gnews_api_key": "",
            "currents_api_key": "",
            "newsdata_api_key": "",
        }

    @pytest.mark.parametrize("cats", NON_EMPTY_SUBSETS,
                             ids=[",".join(c.value for c in s) for s in NON_EMPTY_SUBSETS])
    def test_router_instantiates_for_every_subset(self, empty_config, cats):
        router = CategoryCollectorRouter(empty_config, cats)
        assert router.categories == cats

    def test_router_only_hits_world_monitor_without_keys(self, empty_config):
        """With no supplemental keys, collect_all should call only WorldMonitor."""
        with patch("src.data.collector_router.WorldMonitorCollector") as MockWM, \
             patch("src.data.collector_router.FredCollector") as MockFred, \
             patch("src.data.collector_router.GNewsCollector") as MockGNews, \
             patch("src.data.collector_router.NewsDataCollector") as MockND, \
             patch("src.data.collector_router.CurrentsCollector") as MockCurr, \
             patch("src.data.collector_router.CoinGeckoCollector") as MockCG:
            MockWM.return_value.collect.return_value = {}

            router = CategoryCollectorRouter(empty_config, [PodcastCategory.FINANCE_MACRO])
            router.collect_all()

            MockWM.assert_called_once()
            MockFred.assert_not_called()
            MockGNews.assert_not_called()
            MockND.assert_not_called()
            MockCurr.assert_not_called()
            # CoinGecko needs no key, but Finance Macro doesn't request it.
            MockCG.assert_not_called()

    def test_crypto_always_uses_coingecko(self, empty_config):
        """CoinGecko needs no API key, so Crypto always supplements with it."""
        with patch("src.data.collector_router.WorldMonitorCollector") as MockWM, \
             patch("src.data.collector_router.CoinGeckoCollector") as MockCG:
            MockWM.return_value.collect.return_value = {}
            MockCG.return_value.collect_all.return_value = {"crypto_global": {}, "crypto_trending": []}

            router = CategoryCollectorRouter(empty_config, [PodcastCategory.CRYPTO])
            router.collect_all()

            MockCG.assert_called_once()

    def test_router_skips_placeholder_keys(self, empty_config):
        """Keys still containing 'your_' must be treated as unset."""
        empty_config["gnews_api_key"] = "your_gnews_key_here"
        with patch("src.data.collector_router.WorldMonitorCollector") as MockWM, \
             patch("src.data.collector_router.GNewsCollector") as MockGNews:
            MockWM.return_value.collect.return_value = {"geopolitics": []}

            router = CategoryCollectorRouter(empty_config, [PodcastCategory.GEOPOLITICS])
            router.collect_all()

            MockGNews.assert_not_called()


# ─── Script generator cleanup (Gemini mocked) ─────────────────────────────────

class TestScriptGenerator:
    def _make_generator(self, response_text: str) -> ScriptGenerator:
        with patch("src.script.llm.gemini.genai.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value.text = response_text
            MockClient.return_value = mock_client
            gen = ScriptGenerator(api_key="test-key", model="gemini-3.1-flash-lite-preview")
            gen.provider.client = mock_client  # keep the mock around
            return gen

    def test_clean_script_drops_orphan_lines(self):
        gen = self._make_generator("")
        raw = (
            "INTRO: Market update\n"
            "[S1] Hey folks, welcome to the show.\n"
            "(dramatic pause)\n"
            "[S2] Good to be here.\n"
        )
        cleaned = gen._clean_script(raw)
        lines = cleaned.splitlines()
        assert all(line.startswith(("[S1]", "[S2]")) for line in lines)
        assert len(lines) == 2

    def test_clean_script_preserves_emotion_tags(self):
        gen = self._make_generator("")
        raw = "[S1:excited] Rally! Rally! Rally!\n[S2:concerned] Careful now.\n"
        cleaned = gen._clean_script(raw)
        assert "[S1:excited]" in cleaned
        assert "[S2:concerned]" in cleaned


# ─── TTS segment parser ───────────────────────────────────────────────────────

class TestKokoroSegmentParser:
    """The parser is a pure function; test without spinning up the model."""

    def _parser(self):
        # Build an instance whose __init__ we've bypassed so we can call
        # _parse_script without downloading Kokoro-82M.
        engine = KokoroEngine.__new__(KokoroEngine)
        return engine._parse_script

    def test_parses_plain_speaker_tags(self):
        parse = self._parser()
        segs = parse("[S1] Hello.\n[S2] Hi back.")
        assert segs == [("S1", "neutral", "Hello."), ("S2", "neutral", "Hi back.")]

    def test_parses_emotion_tags(self):
        parse = self._parser()
        segs = parse("[S1:excited] Whoa!\n[S2:serious] Yes, really.")
        assert segs == [("S1", "excited", "Whoa!"), ("S2", "serious", "Yes, really.")]

    def test_skips_blank_and_unlabelled_lines(self):
        parse = self._parser()
        segs = parse("\nstray text\n[S1] Real line.\n\n")
        assert segs == [("S1", "neutral", "Real line.")]

    def test_unknown_emotion_falls_back_to_neutral(self):
        parse = self._parser()
        segs = parse("[S1:bogus] Hello.")
        assert segs == [("S1", "neutral", "Hello.")]


# ─── Config sanity ────────────────────────────────────────────────────────────

class TestConfig:
    def test_gemini_model_is_flash_lite(self):
        import yaml
        with open("config.yaml", "r") as f:
            cfg = yaml.safe_load(f)
        assert cfg["gemini_model"] == "gemini-3.1-flash-lite-preview", (
            "config.yaml should point at Gemini 3.1 Flash Lite (cheapest tier)"
        )

    def test_configured_default_voices_exist(self):
        import yaml
        with open("config.yaml", "r") as f:
            cfg = yaml.safe_load(f)
        assert cfg["speaker_1_voice"] in ALL_VOICE_IDS
        assert cfg["speaker_2_voice"] in ALL_VOICE_IDS


# ─── Length presets ───────────────────────────────────────────────────────────

class TestLengthPresets:
    def test_every_preset_has_valid_fields(self):
        from src.script.length import LENGTH_PRESETS, DEFAULT_PRESET_KEY
        assert DEFAULT_PRESET_KEY in LENGTH_PRESETS
        for key, preset in LENGTH_PRESETS.items():
            assert preset.key == key
            assert preset.label
            assert preset.target_words > 0
            assert preset.approx_minutes

    def test_build_system_prompt_uses_target_words(self):
        from src.script.prompts import build_system_prompt
        prompt = build_system_prompt(list(DEFAULT_CATEGORIES), target_words=900)
        # The TARGET LENGTH line must reflect the provided word budget.
        assert "900" in prompt
        assert "TARGET LENGTH" in prompt

    def test_build_system_prompt_legacy_path_still_works(self):
        from src.script.prompts import build_system_prompt
        prompt = build_system_prompt(list(DEFAULT_CATEGORIES))
        assert "TARGET LENGTH" in prompt

    def test_brief_preset_replaces_structure_block(self):
        from src.script.prompts import build_system_prompt
        brief = build_system_prompt(
            list(DEFAULT_CATEGORIES), target_words=900, preset_key="brief",
        )
        standard = build_system_prompt(list(DEFAULT_CATEGORIES), target_words=2200)
        # The structure block's numbered "What to Watch Tomorrow" line is in
        # standard mode but not brief. BRIEF_STYLE still references the phrase
        # when telling Gemini to skip it, so assertions must look at the
        # numbered rubric lines, not the raw phrase.
        assert "What to Watch Tomorrow -- name specific data prints" in standard
        assert "What to Watch Tomorrow -- name specific data prints" not in brief


# ─── Snapshot audit trail ─────────────────────────────────────────────────────

class TestSnapshotAuditTrail:
    def test_from_json_fills_user_defaults_on_old_snapshot(self):
        import json
        from src.data.models import MarketSnapshot
        old = json.dumps({"date": "2026-01-01"})
        snap = MarketSnapshot.from_json(old)
        assert snap.user_voice_s1 == ""
        assert snap.user_voice_s2 == ""
        assert snap.user_length_preset == ""
        assert snap.user_target_words == 0

    def test_from_json_drops_unknown_keys(self):
        import json
        from src.data.models import MarketSnapshot
        payload = json.dumps({"date": "2026-01-01", "a_removed_field": 42})
        # Must not raise even though the key isn't on the dataclass.
        snap = MarketSnapshot.from_json(payload)
        assert snap.date == "2026-01-01"

    def test_user_fields_roundtrip(self):
        from src.data.models import MarketSnapshot
        snap = MarketSnapshot(
            date="2026-04-20",
            user_voice_s1="am_michael",
            user_voice_s2="af_heart",
            user_length_preset="brief",
            user_target_words=900,
        )
        snap2 = MarketSnapshot.from_json(snap.to_json())
        assert snap2.user_voice_s1 == "am_michael"
        assert snap2.user_voice_s2 == "af_heart"
        assert snap2.user_length_preset == "brief"
        assert snap2.user_target_words == 900
