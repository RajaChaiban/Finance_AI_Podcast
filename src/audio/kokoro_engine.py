import re
from typing import Optional

import numpy as np
import torch
from kokoro import KPipeline

from src.audio import prosody
from src.audio.voice_blender import VoiceBlender, BlendRecipe, build_recipes
from src.utils.logger import log


# [S1], [S1:excited], [S2:serious] …
_SEGMENT_RE = re.compile(r"\[(S[12])(?::([a-z_]+))?\]\s*(.*)")


class KokoroEngine:
    def __init__(
        self,
        voice_s1: str = "am_adam",
        voice_s2: str = "af_bella",
        speed: float = 1.0,
        enable_blending: bool = True,
        enable_prosody: bool = True,
        recipes: Optional[dict] = None,
    ):
        log.info("Initializing Kokoro TTS engine...")
        self.pipeline = KPipeline(lang_code="a")  # American English
        self.anchor_map = {"S1": voice_s1, "S2": voice_s2}
        self.base_speed = speed
        self.enable_blending = enable_blending
        self.enable_prosody = enable_prosody

        effective_recipes = recipes if recipes is not None else build_recipes(voice_s1, voice_s2)
        # Neutral must always resolve to the configured anchor, regardless of recipe.
        effective_recipes = dict(effective_recipes)
        effective_recipes[("S1", "neutral")] = BlendRecipe(timbre_weights={voice_s1: 1.0})
        effective_recipes[("S2", "neutral")] = BlendRecipe(timbre_weights={voice_s2: 1.0})

        self.blender = VoiceBlender(self.pipeline, effective_recipes) if enable_blending else None
        log.info(
            f"Kokoro ready: S1={voice_s1}, S2={voice_s2}, "
            f"blending={'on' if enable_blending else 'off'}, "
            f"prosody={'on' if enable_prosody else 'off'}"
        )

    def generate_audio(self, script: str, sample_rate: int = 24000, on_progress=None) -> tuple[np.ndarray, int]:
        segments = self._parse_script(script)
        total = len(segments)
        log.info(f"Generating audio for {total} segments...")

        audio_parts = []
        for i, (speaker, emotion, text) in enumerate(segments):
            following = segments[i + 1][1] if i + 1 < total else None
            log.info(f"  Segment {i+1}/{total}: {speaker}:{emotion} ({len(text)} chars)")

            if on_progress:
                on_progress(i, total, speaker, text[:60])

            segment_audio = self._synthesize(speaker, emotion, text)
            if segment_audio is not None and len(segment_audio) > 0:
                audio_parts.append(segment_audio)
                pause_len = int(sample_rate * prosody.pause_ms(emotion, following) / 1000)
                audio_parts.append(np.zeros(pause_len, dtype=np.float32))

        if not audio_parts:
            raise RuntimeError("No audio segments generated")

        combined = np.concatenate(audio_parts)
        duration = len(combined) / sample_rate
        log.info(f"Audio generated: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        return combined, sample_rate

    def _parse_script(self, script: str) -> list[tuple[str, str, str]]:
        segments = []
        for line in script.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            match = _SEGMENT_RE.match(line)
            if not match:
                continue
            speaker = match.group(1)
            emotion = (match.group(2) or "neutral").lower()
            if emotion not in prosody.EMOTION_SPEED:
                log.warning(f"Unknown emotion '{emotion}' on {speaker}; falling back to neutral")
                emotion = "neutral"
            text = match.group(3).strip()
            if text:
                segments.append((speaker, emotion, text))
        return segments

    def _synthesize(self, speaker: str, emotion: str, text: str) -> np.ndarray | None:
        try:
            voice_arg = self._voice_for(speaker, emotion)
            stressed = prosody.stress_text(text, emotion) if self.enable_prosody else text
            speed = prosody.scale_speed(self.base_speed, emotion) if self.enable_prosody else self.base_speed

            chunks = []
            generator = self.pipeline(stressed, voice=voice_arg, speed=speed)
            for _, _, audio in generator:
                if audio is not None:
                    chunks.append(audio)
            if chunks:
                return np.concatenate(chunks)
            return None
        except Exception as e:
            log.warning(f"TTS failed for segment ({speaker}:{emotion}): {e}")
            return None

    def _voice_for(self, speaker: str, emotion: str):
        anchor = self.anchor_map.get(speaker, self.anchor_map["S1"])
        if self.blender is None or emotion == "neutral":
            return anchor
        tensor = self.blender.resolve(speaker, emotion, anchor=anchor)
        # Pipeline's load_voice() passes torch.FloatTensor through unchanged;
        # ensure we're CPU float32 so the isinstance() check matches.
        if tensor.dtype != torch.float32:
            tensor = tensor.to(torch.float32)
        if tensor.device.type != "cpu":
            tensor = tensor.cpu()
        return tensor
