from google import genai
from google.genai.types import GenerateContentConfig
from src.data.models import MarketSnapshot
from src.data.categories import PodcastCategory, DEFAULT_CATEGORIES
from src.script.prompts import (
    build_system_prompt,
    build_user_prompt,
    FORBIDDEN_ADVICE_PHRASES,
)
from src.utils.logger import log


class ScriptGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(
        self,
        snapshot: MarketSnapshot,
        categories: list[PodcastCategory] = None,
        target_words: int | None = None,
        preset_key: str | None = None,
    ) -> str:
        if categories is None:
            categories = DEFAULT_CATEGORIES

        log.info("Generating podcast script with Gemini...")

        system_prompt = build_system_prompt(categories, target_words=target_words, preset_key=preset_key)
        user_prompt = build_user_prompt(snapshot.to_json(), categories)

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )

        script = response.text
        script = self._clean_script(script)
        self._validate_script(script, len(categories), target_words=target_words, preset_key=preset_key)
        self._validate_content(script)

        word_count = len(script.split())
        log.info(f"Script generated: {word_count} words")
        return script

    _SPEAKER_PREFIX_RE = (
        "[S1]", "[S2]", "[S1:", "[S2:",
    )

    def _clean_script(self, script: str) -> str:
        lines = script.strip().split("\n")
        cleaned = []
        dropped = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(self._SPEAKER_PREFIX_RE):
                cleaned.append(line)
            else:
                # Drop orphan lines (preambles like "INTRO:", stage directions,
                # unlabelled continuations). Attaching them to the previous
                # speaker turn was causing non-dialogue text to be read aloud.
                dropped += 1
                log.warning(f"Dropping orphan line: {line[:80]!r}")
        if dropped:
            log.warning(f"Cleaned script: dropped {dropped} orphan line(s)")
        return "\n".join(cleaned)

    def _validate_script(
        self,
        script: str,
        num_categories: int = 2,
        target_words: int | None = None,
        preset_key: str | None = None,
    ):
        s1_count = script.count("[S1]")
        s2_count = script.count("[S2]")

        if s1_count == 0 or s2_count == 0:
            log.warning(f"Script validation: missing speakers (S1={s1_count}, S2={s2_count})")

        word_count = len(script.split())
        if target_words is None:
            # Legacy path preserved for callers that haven't threaded a preset.
            target = max(1800, min(2500, num_categories * 450))
        else:
            target = int(target_words)
        low = target - 500
        high = target + 500

        if word_count < low:
            log.warning(f"Script is short: {word_count} words (target: ~{target})")
        elif word_count > high and preset_key != "deep":
            # Deep mode explicitly asks Gemini to go long, so the commuter cap
            # warning would be noise.
            log.warning(
                f"Script is long: {word_count} words (target: ~{target}); "
                "commuter attention caps at ~20 min -- consider trimming"
            )

    def _validate_content(self, script: str):
        """Scan for advice-language phrases that must not appear in the script.

        The prompt forbids these, but Gemini occasionally drifts -- particularly
        when the data contains explicit buy/sell signals. Logging-only rather
        than regenerating: a reject-and-retry loop would double latency and
        cost, and the prompt-level constraint catches the vast majority. The
        warning is surfaced so a human can gate publishing.
        """
        lower = script.lower()
        hits = [phrase for phrase in FORBIDDEN_ADVICE_PHRASES if phrase in lower]
        if hits:
            log.warning(
                f"Script contains advice-like language: {hits}. "
                "Review before publishing -- this is a regulatory risk."
            )

    def save_script(self, script: str, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        log.info(f"Script saved to {path}")

    @staticmethod
    def load_script(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
