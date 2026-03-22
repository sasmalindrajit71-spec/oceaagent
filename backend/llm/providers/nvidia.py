"""
NVIDIA NIM Provider — OpenAI-compatible API
Base URL: https://integrate.api.nvidia.com/v1
Key format: nvapi-...
Supports: Llama, Mistral, Nemotron, Mixtral, DeepSeek, Qwen, Phi, Gemma, and more
"""

import httpx
from typing import Optional

BASE_URL = "https://integrate.api.nvidia.com/v1"

# All available NVIDIA NIM models for simulation roles
NVIDIA_MODELS = {
    # Best for deep agent reasoning — large, high quality
    "deep_agent": [
        "meta/llama-3.3-70b-instruct",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "nvidia/nemotron-3-super-120b-a12b",
        "meta/llama-3.1-405b-instruct",
        "deepseek-ai/deepseek-r1",
        "qwen/qwen3-235b-a22b",
        "mistralai/mistral-large-2-instruct",
    ],
    # Best for persona generation — creative + accurate
    "persona": [
        "meta/llama-3.3-70b-instruct",
        "qwen/qwen3-235b-a22b",
        "mistralai/mixtral-8x22b-instruct-v0.1",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
    ],
    # Best for report engine — analytical + structured
    "report_engine": [
        "nvidia/nemotron-3-super-120b-a12b",
        "deepseek-ai/deepseek-r1",
        "meta/llama-3.1-405b-instruct",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "qwen/qwen3-235b-a22b",
    ],
    # Fast models for shallow/statistical processing
    "fast": [
        "meta/llama-3.1-8b-instruct",
        "microsoft/phi-3-mini-128k-instruct",
        "google/gemma-3-12b-it",
        "mistralai/mistral-7b-instruct-v0.3",
    ],
    # Graph RAG extraction
    "graph_rag": [
        "meta/llama-3.3-70b-instruct",
        "nvidia/llama-3.3-nemotron-super-49b-v1",
        "mistralai/mixtral-8x22b-instruct-v0.1",
    ],
}

# Model display names for UI
MODEL_INFO = {
    "meta/llama-3.3-70b-instruct":              { "name": "Llama 3.3 70B",          "ctx": "128K", "tier": "flagship" },
    "nvidia/llama-3.3-nemotron-super-49b-v1":   { "name": "Nemotron Super 49B",      "ctx": "128K", "tier": "flagship" },
    "nvidia/nemotron-3-super-120b-a12b":        { "name": "Nemotron 3 Super 120B",   "ctx": "128K", "tier": "flagship" },
    "meta/llama-3.1-405b-instruct":             { "name": "Llama 3.1 405B",          "ctx": "128K", "tier": "flagship" },
    "deepseek-ai/deepseek-r1":                  { "name": "DeepSeek R1",             "ctx": "128K", "tier": "reasoning" },
    "qwen/qwen3-235b-a22b":                     { "name": "Qwen3 235B",              "ctx": "32K",  "tier": "flagship" },
    "mistralai/mistral-large-2-instruct":       { "name": "Mistral Large 2",         "ctx": "128K", "tier": "flagship" },
    "mistralai/mixtral-8x22b-instruct-v0.1":    { "name": "Mixtral 8x22B",           "ctx": "65K",  "tier": "balanced" },
    "meta/llama-3.1-8b-instruct":               { "name": "Llama 3.1 8B",            "ctx": "128K", "tier": "fast" },
    "microsoft/phi-3-mini-128k-instruct":       { "name": "Phi-3 Mini 128K",         "ctx": "128K", "tier": "fast" },
    "google/gemma-3-12b-it":                    { "name": "Gemma 3 12B",             "ctx": "128K", "tier": "fast" },
    "mistralai/mistral-7b-instruct-v0.3":       { "name": "Mistral 7B v0.3",         "ctx": "32K",  "tier": "fast" },
    "microsoft/phi-3-medium-128k-instruct":     { "name": "Phi-3 Medium 128K",       "ctx": "128K", "tier": "balanced" },
    "google/gemma-3-27b-it":                    { "name": "Gemma 3 27B",             "ctx": "128K", "tier": "balanced" },
}


async def complete(
    api_key: str,
    model: str,
    messages: list,
    system: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """Call NVIDIA NIM API and return the response text."""
    if not api_key or not api_key.startswith("nvapi-"):
        raise ValueError("Invalid NVIDIA API key — must start with 'nvapi-'")

    payload_messages = []
    if system:
        payload_messages.append({"role": "system", "content": system})
    payload_messages.extend(messages)

    payload = {
        "model": model,
        "messages": payload_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def test_connection(api_key: str, model: str = "meta/llama-3.1-8b-instruct") -> dict:
    """Test if the NVIDIA API key works."""
    try:
        result = await complete(
            api_key=api_key,
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly one word: OK"}],
            max_tokens=10,
            temperature=0,
        )
        return {"valid": True, "response": result.strip()}
    except httpx.HTTPStatusError as e:
        return {"valid": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


async def list_models(api_key: str) -> list:
    """Fetch live model list from NVIDIA API."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"{BASE_URL}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            r.raise_for_status()
            data = r.json()
            return [m["id"] for m in data.get("models", data.get("data", []))]
    except Exception:
        # Return known models as fallback
        return list(MODEL_INFO.keys())