# 🌊 OCEAN
### Open-Source Multi-Agent Social Simulation Engine
**Version 1.0 — Phase 1**

> *Simulate the world before it happens.*

---

## What is OCEAN?

OCEAN is a self-hosted, open-source multi-agent social simulation platform. Feed it a real-world event — a news article, a policy announcement, a crisis — and it generates psychologically grounded AI agents that interact, evolve, and reveal how real populations would respond.

**Stack:** Python 3.11 (FastAPI + Celery) + Vue.js 3 + Docker Compose  
**LLMs:** Multi-provider routing — OpenRouter, Groq, Together AI, Mistral, or any OpenAI-compatible endpoint  
**Distribution:** `git clone → docker compose up → localhost:3000`

---

## Quickstart

### Prerequisites
- Docker and Docker Compose
- At least one free LLM provider account:
  - [OpenRouter](https://openrouter.ai) — free DeepSeek V3, Qwen QwQ-32B
  - [Groq](https://console.groq.com) — free Llama 4, Gemma 3
  - [Together AI](https://api.together.xyz) — free Llama 4
  - [Mistral](https://console.mistral.ai)
- 4GB RAM minimum, 8GB recommended

### Step 1 — Clone
```bash
git clone https://github.com/your-org/ocean
cd ocean
```

### Step 2 — Configure
```bash
cp ocean.config.example.yaml ocean.config.yaml
# Edit ocean.config.yaml — add your API keys and enable providers
```

### Step 3 — Launch
```bash
docker compose up
```

Open `http://localhost:3000` in your browser.

---

## Architecture

OCEAN has six independently replaceable layers:

| Layer | Module | Responsibility |
|---|---|---|
| 1. Ingestion | `backend/ingestion/` | Graph RAG extraction from text, URL, PDF |
| 2. Persona Engine | `backend/personas/` | Agent generation — demographics, personality, beliefs |
| 3. Memory Engine | `backend/memory/` | Decay functions, emotional salience, memory pruning |
| 4. Simulation Runtime | `backend/simulation/` | Tick engine, agent interactions, social graph topology |
| 5. LLM Gateway | `backend/llm/` | Multi-provider routing, rate-limit failover |
| 6. Report Engine | `backend/reports/` | 3-pass analysis — patterns, causation, narrative |

---

## LLM Provider Configuration

OCEAN routes agent reasoning calls across multiple providers. Configure any combination:

```yaml
# ocean.config.yaml

providers:
  openrouter:
    api_key: "sk-or-..."
    enabled: true
    models:
      deep_agent: "deepseek/deepseek-chat-v3-0324:free"
      shallow_agent: "moonshotai/moonlight-16a-instruct-preview:free"
      evaluator: "qwen/qwq-32b:free"
      graph_rag: "deepseek/deepseek-chat-v3-0324:free"
      report_engine: "qwen/qwq-32b:free"

  groq:
    api_key: "gsk_..."
    enabled: true
    models:
      deep_agent: "llama-4-scout-17b-16e-instruct"
      shallow_agent: "gemma3-27b-it"
      evaluator: "llama-4-maverick-17b-128e-instruct"
```

Each agent is assigned a provider + model at spawn time and keeps it throughout the simulation — ensuring personality consistency across ticks.

**Routing behaviour:**
- If multiple providers are active, agents are distributed across them (round-robin with random shuffle)
- If a provider hits a rate limit, OCEAN automatically fails over to the next available provider
- The simulation runtime is provider-agnostic — it calls `llm.router.complete(role, messages)` and doesn't handle provider logic directly

You can also configure API keys from the **Settings** page in the dashboard UI.

---

## Simulation Workflow

| Stage | Description |
|---|---|
| 1. Seed Upload | Paste text, upload a file, or enter a URL |
| 2. Graph RAG | Multi-pass extraction builds a knowledge graph |
| **3. Graph Validation ★** | **Operator reviews entities, topics, tensions — corrects errors before agents spawn** |
| 4. Agent Generation | Persona engine creates deep + shallow agents. Social network built. |
| 5. Simulation | Tick-based engine advances. Deep agents reason via LLM. Shallow agents interact statistically. |
| 6. Report | 3-pass analysis: pattern detection → causal attribution → narrative synthesis |
| 7. Export | Full simulation state exportable |

---

## Agent Architecture

### Deep Agents (LLM-powered)
- Full Big Five personality profile
- Memory with exponential decay and emotional salience
- Belief vector per topic (-1.0 strongly against → 1.0 strongly for)
- Fixed LLM model assignment at spawn
- Independent reasoning at each tick

### Shallow Agents (Statistical)
- Statistically generated demographics and beliefs
- Cluster-based belief distributions
- Fast batch processing — no LLM calls
- Represent crowd dynamics and silent majority

### Social Network
- Watts-Strogatz small-world topology
- Echo chambers via within-cluster preferential attachment
- Weak-tie bridges for cross-cluster idea propagation
- Visualised live in the dashboard as a D3.js force-directed graph

---

## Repository Structure

```
ocean/
├── backend/
│   ├── ingestion/         # Graph RAG extraction pipeline
│   ├── personas/          # Agent generation & personality engine
│   ├── memory/            # Memory decay & salience engine
│   ├── simulation/        # Core runtime + social network builder
│   ├── llm/               # Multi-provider router + 4 provider modules
│   │   └── providers/     # openrouter.py, groq.py, together.py, mistral.py
│   ├── reports/           # 3-pass report engine
│   ├── api/               # (reserved for future API modules)
│   ├── main.py            # FastAPI app — REST + WebSocket
│   ├── database.py        # SQLAlchemy models + session factory
│   ├── config.py          # Config loader (ocean.config.yaml)
│   ├── celery_app.py      # Celery task runner
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/         # Dashboard, NewSimulation, SimulationDetail, Settings
│       ├── components/    # WorkflowStepper, NetworkGraph, AgentInspector, etc.
│       ├── stores/        # Pinia state — simulation + settings stores
│       ├── router.js      # Vue Router
│       └── assets/        # global.css — OCEAN design system
├── docker-compose.yml
├── ocean.config.example.yaml
└── README.md
```

---

## Phase Roadmap

| Phase | Status | Features |
|---|---|---|
| **Phase 1** | ✅ **Complete** | Graph RAG ingestion, agent generation, memory engine, simulation runtime, multi-provider LLM routing, report engine, full dashboard |
| Phase 2 | Planned | Pause/resume controls, mid-simulation event injection UI, live D3 graph updates, agent inspector with memory history |
| Phase 3 | Planned | Counterfactual engine, backtesting, side-by-side simulation comparison, PDF report export |
| Phase 4 | Planned | Plugin API, community persona library, Ollama support, full REST API docs |

---

## Contributing

OCEAN is open-source and contribution-driven.

- Fork the repository on GitHub
- Read `CONTRIBUTING.md` for code standards and PR guidelines
- Open issues for bugs, feature requests, and discussion

---

## Licence

MIT — free to use, modify, and distribute, including commercially, with attribution.
