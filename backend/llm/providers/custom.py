"""
OCEAN LLM — Custom provider (OpenAI-compatible endpoint).
"""

import httpx
from typing import Optional


async def complete(
    api_key: str,
    base_url: str,
    model: str,
    messages: list,
    system: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """
    Call any OpenAI-compatible custom endpoint.
    Set base_url in Settings to your provider's base URL.
    """
    if not base_url:
        raise ValueError("Custom provider requires a base_url. Set it in Settings.")

    # Build message list with optional system prompt
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": full_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]