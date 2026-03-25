"""
OCEAN Configuration — loads from oceaagent.config.yaml and environment variables.
"""

import os
import yaml
from pydantic import BaseModel
from typing import Optional, Dict
from pathlib import Path


CONFIG_PATH = Path(os.getenv("OCEAAGENT_CONFIG", "/app/oceaagent.config.yaml"))
EXAMPLE_CONFIG_PATH = Path("/app/oceaagent.config.example.yaml")


class ModelSet(BaseModel):
    deep_agent: str = ""
    shallow_agent: str = ""
    evaluator: str = ""
    graph_rag: str = ""
    report_engine: str = ""


class ProviderConfig(BaseModel):
    api_key: str = ""
    enabled: bool = False
    base_url: Optional[str] = None
    models: ModelSet = ModelSet()


class ProvidersConfig(BaseModel):
    nvidia: ProviderConfig = ProviderConfig()
    openrouter: ProviderConfig = ProviderConfig()
    groq: ProviderConfig = ProviderConfig()
    together: ProviderConfig = ProviderConfig()
    mistral: ProviderConfig = ProviderConfig()
    custom: ProviderConfig = ProviderConfig()


class SimulationConfig(BaseModel):
    default_deep_agents: int = 50
    default_shallow_agents: int = 500
    max_deep_agents: int = 500
    max_shallow_agents: int = 5000
    default_ticks: int = 100
    tick_delay_ms: int = 500


class MemoryConfig(BaseModel):
    decay_rate: float = 0.05
    emotional_salience_multiplier: float = 2.0
    max_memories_per_agent: int = 100


class OceanConfig(BaseModel):
    providers: ProvidersConfig = ProvidersConfig()
    simulation: SimulationConfig = SimulationConfig()
    memory: MemoryConfig = MemoryConfig()


def load_config() -> OceanConfig:
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        cfg = OceanConfig(**data)
    else:
        cfg = OceanConfig()

    # Override with environment variables
    if os.getenv("NVIDIA_API_KEY"):
        cfg.providers.nvidia.api_key = os.getenv("NVIDIA_API_KEY")
        cfg.providers.nvidia.enabled = True
        if not cfg.providers.nvidia.models.deep_agent:
            cfg.providers.nvidia.models = ModelSet(
                deep_agent="meta/llama-3.1-70b-instruct",
                shallow_agent="meta/llama-3.1-8b-instruct",
                evaluator="meta/llama-3.1-70b-instruct",
                graph_rag="meta/llama-3.1-70b-instruct",
                report_engine="meta/llama-3.1-70b-instruct",
            )

    if os.getenv("GROQ_API_KEY"):
        cfg.providers.groq.api_key = os.getenv("GROQ_API_KEY")
        cfg.providers.groq.enabled = True
        if not cfg.providers.groq.models.deep_agent:
            cfg.providers.groq.models = ModelSet(
                deep_agent="llama-3.3-70b-versatile",
                shallow_agent="llama-3.1-8b-instant",
                evaluator="llama-3.3-70b-versatile",
                graph_rag="llama-3.3-70b-versatile",
                report_engine="llama-3.3-70b-versatile",
            )

    if os.getenv("OPENROUTER_API_KEY"):
        cfg.providers.openrouter.api_key = os.getenv("OPENROUTER_API_KEY")
        cfg.providers.openrouter.enabled = True
        if not cfg.providers.openrouter.models.deep_agent:
            cfg.providers.openrouter.models = ModelSet(
                deep_agent="deepseek/deepseek-chat-v3-0324:free",
                shallow_agent="deepseek/deepseek-chat-v3-0324:free",
                evaluator="deepseek/deepseek-chat-v3-0324:free",
                graph_rag="deepseek/deepseek-chat-v3-0324:free",
                report_engine="deepseek/deepseek-chat-v3-0324:free",
            )

    return cfg


def save_config(config: OceanConfig):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config.model_dump(), f, default_flow_style=False)


config = load_config()