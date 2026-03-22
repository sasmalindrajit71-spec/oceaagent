"""
OCEAN LLM Router — multi-provider with intelligent role-based model assignment.
Priority order: NVIDIA → OpenRouter → Groq → Together → Mistral → Custom
"""

import asyncio
import logging
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

# Role → config key mapping
ROLE_MAP = {
    "deep_agent":    "deep_agent",
    "shallow_agent": "shallow_agent",
    "evaluator":     "evaluator",
    "graph_rag":     "graph_rag",
    "report_engine": "report_engine",
}


async def complete(
    role: str,
    messages: list,
    system: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> str:
    """
    Route completion request through providers in priority order.
    Falls back to next provider if one fails.
    """
    providers = _get_ordered_providers()

    if not providers:
        raise RuntimeError("No LLM providers configured. Go to Settings and add at least one API key.")

    last_error = None
    for provider_name, provider_cfg in providers:
        model = _get_model_for_role(provider_name, provider_cfg, role)
        if not model:
            continue
        try:
            result = await _call_provider(provider_name, provider_cfg, model, messages, system, max_tokens, temperature)
            logger.info(f"[{provider_name}] {role} completed with {model}")
            return result
        except Exception as e:
            logger.warning(f"[{provider_name}] Failed for role '{role}': {e}")
            last_error = e
            continue

    raise RuntimeError(f"All providers failed for role '{role}'. Last error: {last_error}")


async def _call_provider(provider_name, provider_cfg, model, messages, system, max_tokens, temperature) -> str:
    """Call the appropriate provider module."""

    if provider_name == "nvidia":
        from llm.providers.nvidia import complete as nvidia_complete
        return await nvidia_complete(
            api_key=provider_cfg.api_key,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif provider_name == "openrouter":
        from llm.providers.openrouter import complete as or_complete
        return await or_complete(
            api_key=provider_cfg.api_key,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif provider_name == "groq":
        from llm.providers.groq import complete as groq_complete
        return await groq_complete(
            api_key=provider_cfg.api_key,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif provider_name == "together":
        from llm.providers.together import complete as together_complete
        return await together_complete(
            api_key=provider_cfg.api_key,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif provider_name == "mistral":
        from llm.providers.mistral import complete as mistral_complete
        return await mistral_complete(
            api_key=provider_cfg.api_key,
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    elif provider_name == "custom":
        from llm.providers.custom import complete as custom_complete
        return await custom_complete(
            api_key=provider_cfg.api_key,
            base_url=getattr(provider_cfg, 'base_url', ''),
            model=model,
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    raise ValueError(f"Unknown provider: {provider_name}")


def _get_ordered_providers() -> list:
    """Return enabled providers sorted by priority: nvidia first."""
    providers = config.providers
    priority = ["nvidia", "openrouter", "groq", "together", "mistral", "custom"]
    result = []
    for name in priority:
        cfg = getattr(providers, name, None)
        if cfg and getattr(cfg, "enabled", False) and getattr(cfg, "api_key", ""):
            result.append((name, cfg))
    return result


def _get_model_for_role(provider_name: str, provider_cfg, role: str) -> Optional[str]:
    """Get the model configured for a specific role on a provider."""
    models = getattr(provider_cfg, "models", None)
    if not models:
        return None
    config_key = ROLE_MAP.get(role, role)
    return getattr(models, config_key, None) or getattr(models, "deep_agent", None)


def get_active_providers() -> list:
    """Return list of currently active provider names."""
    return [name for name, _ in _get_ordered_providers()]


async def test_provider(provider_name: str, api_key: str) -> bool:
    """Test if a provider API key is valid."""
    try:
        if provider_name == "nvidia":
            from llm.providers.nvidia import test_connection
            result = await test_connection(api_key)
            return result.get("valid", False)
        elif provider_name == "groq":
            from llm.providers.groq import complete as groq_complete
            await groq_complete(api_key, "llama-3.3-70b-versatile",
                [{"role":"user","content":"say OK"}], max_tokens=5)
            return True
        elif provider_name == "openrouter":
            from llm.providers.openrouter import complete as or_complete
            await or_complete(api_key, "deepseek/deepseek-chat-v3-0324:free",
                [{"role":"user","content":"say OK"}], max_tokens=5)
            return True
        else:
            return bool(api_key and len(api_key) > 8)
    except Exception as e:
        logger.warning(f"Test failed for {provider_name}: {e}")
        return False