"""Together AI provider implementation."""

import httpx
from typing import Optional


TOGETHER_BASE = "https://api.together.xyz/v1"


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
    }

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    payload = {
        "model": model,
        "messages": payload_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{TOGETHER_BASE}/chat/completions",
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
            model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False
