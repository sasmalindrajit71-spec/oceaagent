"""
OCEAN Persona Engine — generates agent profiles from knowledge graph.
Assigns demographics, personality (Big Five), beliefs, emotional baseline,
network position, and LLM model assignment.
"""

import uuid
import random
import json
from typing import Optional
from llm import router, get_active_providers
from config import config


PERSONA_SYSTEM = """You are a social simulation persona designer.
Given a knowledge graph about a real-world event, generate a realistic person who would have opinions about it.
Return ONLY valid JSON — no preamble, no markdown.

Return this structure:
{
  "name": "Full Name",
  "age": 34,
  "occupation": "Software Engineer",
  "education": "Bachelor's degree",
  "location": "Austin, TX",
  "political_lean": 0.2,
  "openness": 0.7,
  "conscientiousness": 0.6,
  "extraversion": 0.4,
  "agreeableness": 0.5,
  "neuroticism": 0.3,
  "emotional_baseline": 0.1,
  "belief_vector": {"topic1": 0.6, "topic2": -0.3},
  "background_narrative": "Brief 2-sentence bio explaining their perspective"
}

political_lean: -1.0 (far left) to 1.0 (far right)
Big Five traits: 0.0 to 1.0
emotional_baseline: -1.0 (pessimistic) to 1.0 (optimistic)
belief_vector values: -1.0 (strongly against) to 1.0 (strongly for)"""


def _assign_model(tier: str) -> tuple[str, str]:
    """Assign a provider/model to an agent based on tier and available providers."""
    providers = get_active_providers()
    if not providers:
        return "none", "none"

    role = "deep_agent" if tier == "deep" else "shallow_agent"
    eligible = []
    for p in providers:
        model = getattr(p["config"].models, role, "")
        if model:
            eligible.append((p["name"], model))

    if not eligible:
        # Fallback to any model
        for p in providers:
            for r in ["deep_agent", "shallow_agent", "evaluator"]:
                model = getattr(p["config"].models, r, "")
                if model:
                    return p["name"], model
        return "none", "none"

    return random.choice(eligible)


async def generate_deep_agent(simulation_id: str, knowledge_graph: dict, cluster_id: int, node_index: int) -> dict:
    """Generate a fully-featured deep agent persona."""
    topics = knowledge_graph.get("core_topics", ["general"])
    entities = [e["label"] for e in knowledge_graph.get("entities", [])[:5]]

    prompt = f"""Generate a realistic person who has opinions about this topic.

Knowledge Graph Context:
- Core topics: {', '.join(topics)}
- Key entities: {', '.join(entities)}
- Sentiment: {knowledge_graph.get('overall_sentiment', 0.0):.2f}

Create someone with a distinct perspective. Make their beliefs specific to the topics above.
Vary demographics realistically — different ages, occupations, locations, and political leanings."""

    response = await router.complete(
        role="deep_agent",
        messages=[{"role": "user", "content": prompt}],
        system=PERSONA_SYSTEM,
        max_tokens=800,
        temperature=0.9,
    )

    persona = _safe_parse_json(response)
    provider, model = _assign_model("deep")

    return {
        "id": str(uuid.uuid4()),
        "simulation_id": simulation_id,
        "tier": "deep",
        "name": persona.get("name", f"Agent_{node_index}"),
        "age": persona.get("age", random.randint(18, 75)),
        "occupation": persona.get("occupation", "Unknown"),
        "education": persona.get("education", "Unknown"),
        "location": persona.get("location", "Unknown"),
        "political_lean": _clamp(persona.get("political_lean", 0.0)),
        "openness": _clamp(persona.get("openness", 0.5)),
        "conscientiousness": _clamp(persona.get("conscientiousness", 0.5)),
        "extraversion": _clamp(persona.get("extraversion", 0.5)),
        "agreeableness": _clamp(persona.get("agreeableness", 0.5)),
        "neuroticism": _clamp(persona.get("neuroticism", 0.5)),
        "emotional_baseline": _clamp(persona.get("emotional_baseline", 0.0), -1, 1),
        "current_emotion": _clamp(persona.get("emotional_baseline", 0.0), -1, 1),
        "belief_vector": persona.get("belief_vector", {}),
        "network_position": node_index,
        "cluster_id": cluster_id,
        "influence_score": random.gauss(1.0, 0.4),
        "provider": provider,
        "model": model,
    }


def generate_shallow_agent(simulation_id: str, knowledge_graph: dict, cluster_id: int, node_index: int) -> dict:
    """Generate a lightweight shallow agent — no LLM call, statistical generation."""
    topics = knowledge_graph.get("core_topics", ["general"])
    overall_sentiment = knowledge_graph.get("overall_sentiment", 0.0)

    # Statistical generation based on cluster
    cluster_lean = (cluster_id % 5 - 2) * 0.4  # distribute clusters across political spectrum
    noise = random.gauss(0, 0.3)

    belief_vector = {}
    for topic in topics:
        belief_vector[topic] = _clamp(cluster_lean + noise + random.gauss(0, 0.2), -1, 1)

    provider, model = _assign_model("shallow")

    return {
        "id": str(uuid.uuid4()),
        "simulation_id": simulation_id,
        "tier": "shallow",
        "name": f"S{node_index:04d}",
        "age": random.randint(18, 75),
        "occupation": random.choice(["Worker", "Student", "Professional", "Retired", "Entrepreneur"]),
        "education": random.choice(["High school", "Bachelor's", "Master's", "No formal"]),
        "location": "Various",
        "political_lean": _clamp(cluster_lean + random.gauss(0, 0.25), -1, 1),
        "openness": random.uniform(0.2, 0.9),
        "conscientiousness": random.uniform(0.2, 0.9),
        "extraversion": random.uniform(0.2, 0.9),
        "agreeableness": random.uniform(0.2, 0.9),
        "neuroticism": random.uniform(0.2, 0.9),
        "emotional_baseline": _clamp(overall_sentiment + random.gauss(0, 0.3), -1, 1),
        "current_emotion": _clamp(overall_sentiment + random.gauss(0, 0.3), -1, 1),
        "belief_vector": belief_vector,
        "network_position": node_index,
        "cluster_id": cluster_id,
        "influence_score": abs(random.gauss(0.5, 0.3)),
        "provider": provider,
        "model": model,
    }


async def generate_agent_population(
    simulation_id: str,
    knowledge_graph: dict,
    deep_count: int = 50,
    shallow_count: int = 500,
) -> list[dict]:
    """Generate the full agent population for a simulation."""
    agents = []
    num_clusters = max(5, deep_count // 10)

    # Generate deep agents across clusters
    for i in range(deep_count):
        cluster_id = i % num_clusters
        agent = await generate_deep_agent(simulation_id, knowledge_graph, cluster_id, i)
        agents.append(agent)

    # Generate shallow agents across clusters
    for i in range(shallow_count):
        cluster_id = i % num_clusters
        agent = generate_shallow_agent(simulation_id, knowledge_graph, cluster_id, deep_count + i)
        agents.append(agent)

    return agents


def _clamp(val, lo=0.0, hi=1.0):
    try:
        return max(lo, min(hi, float(val)))
    except (TypeError, ValueError):
        return (lo + hi) / 2


def _safe_parse_json(text: str) -> dict:
    import re
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}
