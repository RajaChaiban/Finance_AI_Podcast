"""Voice style-vector blending for Kokoro TTS.

Kokoro voicepacks are torch tensors of shape (510, 1, 256). During synthesis
the pipeline slices `pack[len(phonemes) - 1]`, producing `ref_s` of shape
(1, 256). Internally, dims [0, 128) drive the decoder's timbre and
dims [128, 256) condition the duration and F0 predictors (prosody). That
split makes "timbre-from-A, prosody-from-B" blends physically meaningful.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import torch

from src.utils.logger import log


EMOTIONS = ("neutral", "excited", "curious", "serious", "warm", "concerned", "playful")

# Kokoro 82M voice catalog with the maintainer's published quality grades.
# Higher grade = better sample quality. Use this to populate UI selectors
# and to set sensible defaults (af_heart + am_michael are the top-graded
# American female/male voices).
VOICE_CATALOG: list[dict] = [
    # ── American Female ─────────────────────────────────────
    {"id": "af_heart",   "label": "Heart (American F)",    "gender": "female", "region": "us", "grade": "A"},
    {"id": "af_bella",   "label": "Bella (American F)",    "gender": "female", "region": "us", "grade": "A-"},
    {"id": "af_nicole",  "label": "Nicole (American F)",   "gender": "female", "region": "us", "grade": "B-"},
    {"id": "af_aoede",   "label": "Aoede (American F)",    "gender": "female", "region": "us", "grade": "C+"},
    {"id": "af_kore",    "label": "Kore (American F)",     "gender": "female", "region": "us", "grade": "C+"},
    {"id": "af_sarah",   "label": "Sarah (American F)",    "gender": "female", "region": "us", "grade": "C+"},
    {"id": "af_nova",    "label": "Nova (American F)",     "gender": "female", "region": "us", "grade": "C"},
    {"id": "af_alloy",   "label": "Alloy (American F)",    "gender": "female", "region": "us", "grade": "C"},
    {"id": "af_sky",     "label": "Sky (American F)",      "gender": "female", "region": "us", "grade": "C-"},
    {"id": "af_jessica", "label": "Jessica (American F)",  "gender": "female", "region": "us", "grade": "D"},
    {"id": "af_river",   "label": "River (American F)",    "gender": "female", "region": "us", "grade": "D"},
    # ── American Male ───────────────────────────────────────
    {"id": "am_michael", "label": "Michael (American M)",  "gender": "male",   "region": "us", "grade": "C+"},
    {"id": "am_fenrir",  "label": "Fenrir (American M)",   "gender": "male",   "region": "us", "grade": "C+"},
    {"id": "am_puck",    "label": "Puck (American M)",     "gender": "male",   "region": "us", "grade": "C+"},
    {"id": "am_echo",    "label": "Echo (American M)",     "gender": "male",   "region": "us", "grade": "D"},
    {"id": "am_eric",    "label": "Eric (American M)",     "gender": "male",   "region": "us", "grade": "D"},
    {"id": "am_liam",    "label": "Liam (American M)",     "gender": "male",   "region": "us", "grade": "D"},
    {"id": "am_onyx",    "label": "Onyx (American M)",     "gender": "male",   "region": "us", "grade": "D"},
    {"id": "am_adam",    "label": "Adam (American M)",     "gender": "male",   "region": "us", "grade": "F+"},
    {"id": "am_santa",   "label": "Santa (American M)",    "gender": "male",   "region": "us", "grade": "D-"},
    # ── British Female ──────────────────────────────────────
    {"id": "bf_emma",    "label": "Emma (British F)",      "gender": "female", "region": "uk", "grade": "B-"},
    {"id": "bf_isabella","label": "Isabella (British F)",  "gender": "female", "region": "uk", "grade": "C"},
    {"id": "bf_alice",   "label": "Alice (British F)",     "gender": "female", "region": "uk", "grade": "D"},
    {"id": "bf_lily",    "label": "Lily (British F)",      "gender": "female", "region": "uk", "grade": "D"},
    # ── British Male ────────────────────────────────────────
    {"id": "bm_fable",   "label": "Fable (British M)",     "gender": "male",   "region": "uk", "grade": "C"},
    {"id": "bm_george",  "label": "George (British M)",    "gender": "male",   "region": "uk", "grade": "C"},
    {"id": "bm_lewis",   "label": "Lewis (British M)",     "gender": "male",   "region": "uk", "grade": "C-"},
    {"id": "bm_daniel",  "label": "Daniel (British M)",    "gender": "male",   "region": "uk", "grade": "D"},
]

ALL_VOICE_IDS: tuple[str, ...] = tuple(v["id"] for v in VOICE_CATALOG)


def voice_label(voice_id: str) -> str:
    """Human-readable label with grade: 'Heart (American F) -- A'."""
    for v in VOICE_CATALOG:
        if v["id"] == voice_id:
            return f"{v['label']} -- {v['grade']}"
    return voice_id


# Defaults used to construct the built-in recipes. When the user picks a
# different anchor voice, we remap recipes onto that anchor so the emotion
# system keeps working without manual re-tuning.
DEFAULT_S1_ANCHOR = "am_adam"
DEFAULT_S2_ANCHOR = "af_bella"


@dataclass(frozen=True)
class BlendRecipe:
    """Linear combination of named voicepacks.

    timbre_weights applies to dims [:, :, :128].
    prosody_weights (if None) mirrors timbre_weights and applies to dims [:, :, 128:].
    Weights are normalized to sum to 1 before mixing.
    """
    timbre_weights: dict[str, float]
    prosody_weights: Optional[dict[str, float]] = None

    def voices(self) -> set[str]:
        names = set(self.timbre_weights.keys())
        if self.prosody_weights:
            names |= set(self.prosody_weights.keys())
        return names


def _normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        raise ValueError(f"Blend weights must sum to > 0, got {weights}")
    return {k: v / total for k, v in weights.items()}


class VoiceBlender:
    def __init__(self, pipeline, recipes: Optional[dict[tuple[str, str], BlendRecipe]] = None):
        self.pipeline = pipeline
        self.recipes = recipes if recipes is not None else DEFAULT_RECIPES
        self._voice_cache: dict[str, torch.Tensor] = {}
        self._blend_cache: dict[tuple[str, str], torch.Tensor] = {}

    def load(self, voice_name: str) -> torch.Tensor:
        if voice_name in self._voice_cache:
            return self._voice_cache[voice_name]
        tensor = self.pipeline.load_voice(voice_name)
        if not isinstance(tensor, torch.Tensor):
            tensor = torch.as_tensor(tensor)
        if tensor.dtype != torch.float32:
            tensor = tensor.to(torch.float32)
        self._voice_cache[voice_name] = tensor
        return tensor

    def blend(self, recipe: BlendRecipe) -> torch.Tensor:
        timbre = _normalize(recipe.timbre_weights)
        prosody = _normalize(recipe.prosody_weights) if recipe.prosody_weights else timbre

        tensors = {name: self.load(name) for name in timbre.keys() | prosody.keys()}
        reference = next(iter(tensors.values()))
        shape = reference.shape

        timbre_part = torch.zeros(shape[0], shape[1], 128, dtype=torch.float32)
        prosody_part = torch.zeros(shape[0], shape[1], 128, dtype=torch.float32)

        for name, weight in timbre.items():
            timbre_part += weight * tensors[name][:, :, :128]
        for name, weight in prosody.items():
            prosody_part += weight * tensors[name][:, :, 128:]

        blended = torch.cat([timbre_part, prosody_part], dim=2)
        return blended

    def resolve(self, speaker: str, emotion: str, anchor: Optional[str] = None) -> torch.Tensor:
        """Return a blended style tensor for (speaker, emotion).

        If a recipe is registered for the exact pair, use it. Otherwise fall back
        to the anchor voice name (the configured speaker voice) and return that
        unblended — guaranteeing the pipeline still works for any emotion tag.
        """
        key = (speaker, emotion)
        if key in self._blend_cache:
            return self._blend_cache[key]

        recipe = self.recipes.get(key)
        if recipe is None and anchor is not None:
            log.debug(f"No recipe for {key}; falling back to anchor voice '{anchor}'")
            tensor = self.load(anchor)
        elif recipe is None:
            raise KeyError(f"No blend recipe for {key} and no anchor provided")
        else:
            tensor = self.blend(recipe)

        self._blend_cache[key] = tensor
        return tensor


# ─── Default recipe registry ────────────────────────────────────────────────
# S1 anchor: am_adam (configured default). Prosody-leaning voices: am_michael
#   (animated), am_echo (warm), am_liam (youthful).
# S2 anchor: af_bella. Prosody-leaning voices: af_heart (warm/emotive),
#   af_nova (bright/energetic), af_sky (soft/curious).
# Each recipe keeps ≥50% of the anchor's timbre so the host remains recognizable;
# prosody is where we reach further for emotional color.

DEFAULT_RECIPES: dict[tuple[str, str], BlendRecipe] = {
    # ── Alex / S1 ─────────────────────────────────────────────
    ("S1", "neutral"): BlendRecipe(
        timbre_weights={"am_adam": 1.0},
    ),
    ("S1", "excited"): BlendRecipe(
        timbre_weights={"am_adam": 0.7, "am_michael": 0.3},
        prosody_weights={"am_michael": 0.7, "am_adam": 0.3},
    ),
    ("S1", "curious"): BlendRecipe(
        timbre_weights={"am_adam": 0.8, "am_liam": 0.2},
        prosody_weights={"am_liam": 0.55, "am_adam": 0.45},
    ),
    ("S1", "serious"): BlendRecipe(
        timbre_weights={"am_adam": 0.85, "am_echo": 0.15},
        prosody_weights={"am_echo": 0.6, "am_adam": 0.4},
    ),
    ("S1", "warm"): BlendRecipe(
        timbre_weights={"am_adam": 0.6, "am_echo": 0.4},
        prosody_weights={"am_echo": 0.65, "am_adam": 0.35},
    ),
    ("S1", "concerned"): BlendRecipe(
        timbre_weights={"am_adam": 0.75, "am_echo": 0.25},
        prosody_weights={"am_echo": 0.55, "am_adam": 0.3, "am_michael": 0.15},
    ),
    ("S1", "playful"): BlendRecipe(
        timbre_weights={"am_adam": 0.65, "am_michael": 0.2, "am_liam": 0.15},
        prosody_weights={"am_michael": 0.55, "am_liam": 0.3, "am_adam": 0.15},
    ),
    # ── Sam / S2 ──────────────────────────────────────────────
    ("S2", "neutral"): BlendRecipe(
        timbre_weights={"af_bella": 1.0},
    ),
    ("S2", "excited"): BlendRecipe(
        timbre_weights={"af_bella": 0.7, "af_nova": 0.3},
        prosody_weights={"af_nova": 0.7, "af_bella": 0.3},
    ),
    ("S2", "curious"): BlendRecipe(
        timbre_weights={"af_bella": 0.8, "af_sky": 0.2},
        prosody_weights={"af_sky": 0.6, "af_bella": 0.4},
    ),
    ("S2", "serious"): BlendRecipe(
        timbre_weights={"af_bella": 0.85, "af_heart": 0.15},
        prosody_weights={"af_heart": 0.6, "af_bella": 0.4},
    ),
    ("S2", "warm"): BlendRecipe(
        timbre_weights={"af_bella": 0.6, "af_heart": 0.4},
        prosody_weights={"af_heart": 0.7, "af_bella": 0.3},
    ),
    ("S2", "concerned"): BlendRecipe(
        timbre_weights={"af_bella": 0.75, "af_heart": 0.25},
        prosody_weights={"af_heart": 0.55, "af_bella": 0.3, "af_nova": 0.15},
    ),
    ("S2", "playful"): BlendRecipe(
        timbre_weights={"af_bella": 0.65, "af_nova": 0.25, "af_sky": 0.1},
        prosody_weights={"af_nova": 0.6, "af_sky": 0.25, "af_bella": 0.15},
    ),
}


def build_recipes(anchor_s1: str, anchor_s2: str,
                  base: dict[tuple[str, str], BlendRecipe] = None
                  ) -> dict[tuple[str, str], BlendRecipe]:
    """Re-anchor the built-in emotion recipes onto user-selected voices.

    Each default recipe treats `am_adam` as the S1 anchor and `af_bella` as
    the S2 anchor; every other voice in the recipe is a "color" voice mixed
    in for prosody. When the user picks a different anchor (e.g. `af_heart`
    for S2), we remap those anchor slots onto the chosen voice while keeping
    the color voices and weight structure intact. The result: the host still
    sounds recognizably like their selected voice, but the emotion system
    keeps its designed shape.
    """
    if base is None:
        base = DEFAULT_RECIPES

    anchor_for = {"S1": anchor_s1, "S2": anchor_s2}
    default_for = {"S1": DEFAULT_S1_ANCHOR, "S2": DEFAULT_S2_ANCHOR}

    def _remap(weights: Optional[dict[str, float]], speaker: str) -> Optional[dict[str, float]]:
        if weights is None:
            return None
        default_anchor = default_for[speaker]
        new_anchor = anchor_for[speaker]
        if default_anchor == new_anchor:
            return dict(weights)
        # If the user picked a voice that was already a color voice in this
        # recipe, swap names so both slots stay distinct (avoiding a collapse
        # to a single voice). Otherwise simply rename default_anchor → new.
        swap = new_anchor in weights
        out: dict[str, float] = {}
        for voice, weight in weights.items():
            if voice == default_anchor:
                key = new_anchor
            elif swap and voice == new_anchor:
                key = default_anchor
            else:
                key = voice
            out[key] = out.get(key, 0.0) + weight
        return out

    remapped: dict[tuple[str, str], BlendRecipe] = {}
    for (speaker, emotion), recipe in base.items():
        remapped[(speaker, emotion)] = BlendRecipe(
            timbre_weights=_remap(recipe.timbre_weights, speaker),
            prosody_weights=_remap(recipe.prosody_weights, speaker),
        )
    return remapped
