"""OpenRouter provider implementation."""

import httpx
from typing import Optional


OPENROUTER_BASE = "https://openrouter.ai/api/v1"


async def complete(
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int = 1024,
    temperature: float = 0.8,
    system: Optional[str] = None,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ocean-sim/ocean",
        "X-Title": "OCEAN Simulation",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def test_key(api_key: str) -> bool:
    try:
        await complete(
            api_key=api_key,
            model="deepseek/deepseek-chat-v3-0324:free",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False
