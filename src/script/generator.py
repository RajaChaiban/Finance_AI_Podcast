import re
from google import genai
from google.genai.types import GenerateContentConfig
from src.data.models import MarketSnapshot
from src.script.prompts import SYSTEM_PROMPT, build_user_prompt
from src.utils.logger import log


class ScriptGenerator:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, snapshot: MarketSnapshot) -> str:
        log.info("Generating podcast script with Gemini...")

        user_prompt = build_user_prompt(snapshot.to_json())

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.8,
                max_output_tokens=8192,
            ),
        )

        script = response.text
        script = self._clean_script(script)
        self._validate_script(script)

        word_count = len(script.split())
        log.info(f"Script generated: {word_count} words")
        return script

    def _clean_script(self, script: str) -> str:
        lines = script.strip().split("\n")
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Keep only lines that start with speaker tags
            if line.startswith("[S1]") or line.startswith("[S2]"):
                cleaned.append(line)
            else:
                # Try to attach orphan lines to the previous speaker
                if cleaned:
                    cleaned[-1] += " " + line
        return "\n".join(cleaned)

    def _validate_script(self, script: str):
        s1_count = script.count("[S1]")
        s2_count = script.count("[S2]")

        if s1_count == 0 or s2_count == 0:
            log.warning(f"Script validation: missing speakers (S1={s1_count}, S2={s2_count})")

        word_count = len(script.split())
        if word_count < 500:
            log.warning(f"Script is short: {word_count} words (target: 2500-3500)")
        elif word_count > 5000:
            log.warning(f"Script is long: {word_count} words (target: 2500-3500)")

    def save_script(self, script: str, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        log.info(f"Script saved to {path}")

    @staticmethod
    def load_script(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
