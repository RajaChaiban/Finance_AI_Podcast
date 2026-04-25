from __future__ import annotations

from src.script.llm.base import LLMProvider


GEMINI_PLACEHOLDER = "your_gemini_key_here"


def build_provider(config: dict) -> LLMProvider:
    """Pick a provider from the merged config dict.

    Recognised keys:
      - llm_provider: "gemini" (default) or "ollama"
      - gemini_api_key, gemini_model
      - ollama_model, ollama_base_url
    """
    provider = (config.get("llm_provider") or "gemini").lower()

    if provider == "gemini":
        from src.script.llm.gemini import GeminiProvider

        api_key = config.get("gemini_api_key", "")
        if not api_key or api_key == GEMINI_PLACEHOLDER:
            raise ValueError(
                "Gemini provider selected but GEMINI_API_KEY is not set. "
                "Add it to .env or switch the provider to 'ollama' on the "
                "Settings page."
            )
        model = config.get("gemini_model") or "gemini-2.5-flash"
        return GeminiProvider(api_key=api_key, model=model)

    if provider == "ollama":
        from src.script.llm.ollama import OllamaProvider

        model = config.get("ollama_model") or "gemma4:26b"
        base_url = config.get("ollama_base_url") or "http://localhost:11434"
        return OllamaProvider(model=model, base_url=base_url)

    raise ValueError(
        f"Unknown llm_provider {provider!r}. Use 'gemini' or 'ollama'."
    )
