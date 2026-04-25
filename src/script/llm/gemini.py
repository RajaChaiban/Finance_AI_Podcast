from __future__ import annotations

from google import genai
from google.genai.types import GenerateContentConfig


class GeminiProvider:
    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def complete(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user,
            config=GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text
