import re
import numpy as np
from kokoro import KPipeline
from src.utils.logger import log


class KokoroEngine:
    def __init__(self, voice_s1: str = "am_adam", voice_s2: str = "af_bella", speed: float = 1.0):
        log.info("Initializing Kokoro TTS engine...")
        self.pipeline = KPipeline(lang_code="a")  # American English
        self.voice_map = {
            "S1": voice_s1,
            "S2": voice_s2,
        }
        self.speed = speed
        log.info(f"Kokoro ready: S1={voice_s1}, S2={voice_s2}")

    def generate_audio(self, script: str, sample_rate: int = 24000, on_progress=None) -> tuple[np.ndarray, int]:
        segments = self._parse_script(script)
        total = len(segments)
        log.info(f"Generating audio for {total} segments...")

        audio_parts = []
        pause = np.zeros(int(sample_rate * 0.3), dtype=np.float32)  # 300ms pause

        for i, (speaker, text) in enumerate(segments):
            voice = self.voice_map.get(speaker, self.voice_map["S1"])
            log.info(f"  Segment {i+1}/{total}: {speaker} ({len(text)} chars)")

            if on_progress:
                on_progress(i, total, speaker, text[:60])

            segment_audio = self._synthesize(text, voice)
            if segment_audio is not None and len(segment_audio) > 0:
                audio_parts.append(segment_audio)
                audio_parts.append(pause)

        if not audio_parts:
            raise RuntimeError("No audio segments generated")

        combined = np.concatenate(audio_parts)
        duration = len(combined) / sample_rate
        log.info(f"Audio generated: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        return combined, sample_rate

    def _parse_script(self, script: str) -> list[tuple[str, str]]:
        segments = []
        for line in script.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            match = re.match(r"\[(S[12])\]\s*(.*)", line)
            if match:
                speaker = match.group(1)
                text = match.group(2).strip()
                if text:
                    segments.append((speaker, text))
        return segments

    def _synthesize(self, text: str, voice: str) -> np.ndarray | None:
        try:
            chunks = []
            generator = self.pipeline(text, voice=voice, speed=self.speed)
            for _, _, audio in generator:
                if audio is not None:
                    chunks.append(audio)
            if chunks:
                return np.concatenate(chunks)
            return None
        except Exception as e:
            log.warning(f"TTS failed for segment: {e}")
            return None
