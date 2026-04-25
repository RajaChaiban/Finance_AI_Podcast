from __future__ import annotations

import httpx


class OllamaProvider:
    """Calls Ollama's /api/chat endpoint.

    Local generation is meaningfully slower than Gemini Flash; the timeout is
    set high so large prompts on a CPU-bound machine don't get cut off
    mid-response.
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: float = 600.0,
        client: httpx.Client | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)

    def complete(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = self._client.post(f"{self.base_url}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
