"""
OCEAN Simulation Runtime — advances time in ticks, orchestrates agent interactions.
"""

import uuid
import random
import json
import asyncio
from typing import Optional, Callable
from database import SessionLocal, Simulation, Agent, Interaction, Event
from memory import engine as memory_engine
from simulation.network import get_agent_neighbours, get_weak_tie_bridges
from llm import router
from config import config


DEEP_AGENT_SYSTEM = """You are roleplaying as {name}, a {age}-year-old {occupation} from {location}.

Your personality (Big Five):
- Openness: {openness:.2f}  Conscientiousness: {conscientiousness:.2f}
- Extraversion: {extraversion:.2f}  Agreeableness: {agreeableness:.2f}  Neuroticism: {neuroticism:.2f}

Your political lean: {political_lean:.2f} (-1=far left, 1=far right)
Your current emotional state: {current_emotion:.2f} (-1=very negative, 1=very positive)

Your memories:
{memories}

Respond naturally and in character. Keep responses concise (2-4 sentences).
After your response, append on a new line: EMOTION_DELTA: <float between -0.5 and 0.5>
This represents how this interaction changed your emotional state."""


INTERACTION_PROMPT = """You are having a conversation about: {topic}

The other person said: "{other_message}"

Respond as yourself. Be authentic to your personality and beliefs."""


async def run_tick(
    simulation_id: str,
    tick: int,
    social_graph: dict,
    on_event: Optional[Callable] = None,
) -> dict:
    """
    Run a single simulation tick.
    Returns a summary of interactions that occurred this tick.
    """
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=simulation_id).first()
        if not sim or sim.status == "paused":
            return {"tick": tick, "interactions": [], "paused": True}

        agents = db.query(Agent).filter_by(simulation_id=simulation_id).all()
        agent_map = {a.id: a for a in agents}

        interactions = []

        # Select interaction pairs for this tick
        pairs = _select_interaction_pairs(agents, social_graph, tick)

        for agent_a_id, agent_b_id in pairs[:10]:  # cap interactions per tick
            agent_a = agent_map.get(agent_a_id)
            agent_b = agent_map.get(agent_b_id)
            if not agent_a or not agent_b:
                continue

            interaction = await _run_interaction(
                agent_a, agent_b, simulation_id, tick, sim.knowledge_graph or {}, db
            )

            if interaction:
                interactions.append(interaction)
                if on_event:
                    await on_event({
                        "type": "interaction",
                        "tick": tick,
                        "data": interaction,
                    })

        # Decay memories for deep agents
        deep_agents = [a for a in agents if a.tier == "deep"]
        for agent in deep_agents:
            memory_engine.decay_memories(agent.id, simulation_id, tick)

        # Update simulation tick
        sim.current_tick = tick
        db.commit()

        return {"tick": tick, "interactions": interactions}

    finally:
        db.close()


async def _run_interaction(
    agent_a, agent_b, simulation_id: str, tick: int, knowledge_graph: dict, db
) -> Optional[dict]:
    """Run a single agent-to-agent interaction."""

    topics = knowledge_graph.get("core_topics", ["the current situation"])
    topic = random.choice(topics)

    # Shallow-shallow: statistical interaction only
    if agent_a.tier == "shallow" and agent_b.tier == "shallow":
        return _statistical_interaction(agent_a, agent_b, simulation_id, tick, topic, db)

    # Deep agent involved — use LLM
    try:
        # Agent A speaks first
        memories_a = memory_engine.get_active_memories(agent_a.id, simulation_id, limit=5)
        system_a = DEEP_AGENT_SYSTEM.format(
            name=agent_a.name,
            age=agent_a.age,
            occupation=agent_a.occupation,
            location=agent_a.location,
            openness=agent_a.openness,
            conscientiousness=agent_a.conscientiousness,
            extraversion=agent_a.extraversion,
            agreeableness=agent_a.agreeableness,
            neuroticism=agent_a.neuroticism,
            political_lean=agent_a.political_lean,
            current_emotion=agent_a.current_emotion,
            memories=memory_engine.format_memories_for_prompt(memories_a),
        )

        opening = await router.complete(
            role="deep_agent",
            messages=[{"role": "user", "content": f"Share your thoughts on: {topic}"}],
            system=system_a,
            max_tokens=200,
            temperature=0.85,
        )

        emotion_delta_a = _extract_emotion_delta(opening)
        opening_clean = _strip_emotion_tag(opening)

        # Agent B responds
        memories_b = memory_engine.get_active_memories(agent_b.id, simulation_id, limit=5)
        system_b = DEEP_AGENT_SYSTEM.format(
            name=agent_b.name,
            age=agent_b.age,
            occupation=agent_b.occupation,
            location=agent_b.location,
            openness=agent_b.openness,
            conscientiousness=agent_b.conscientiousness,
            extraversion=agent_b.extraversion,
            agreeableness=agent_b.agreeableness,
            neuroticism=agent_b.neuroticism,
            political_lean=agent_b.political_lean,
            current_emotion=agent_b.current_emotion,
            memories=memory_engine.format_memories_for_prompt(memories_b),
        )

        response = await router.complete(
            role="deep_agent",
            messages=[{"role": "user", "content": INTERACTION_PROMPT.format(
                topic=topic, other_message=opening_clean
            )}],
            system=system_b,
            max_tokens=200,
            temperature=0.85,
        )

        emotion_delta_b = _extract_emotion_delta(response)
        response_clean = _strip_emotion_tag(response)

        # Update emotions
        new_emotion_a = max(-1.0, min(1.0, agent_a.current_emotion + emotion_delta_a))
        new_emotion_b = max(-1.0, min(1.0, agent_b.current_emotion + emotion_delta_b))

        agent_a.current_emotion = new_emotion_a
        agent_b.current_emotion = new_emotion_b

        # Belief contagion — slight pull toward the other's beliefs
        belief_delta_a = _compute_belief_shift(agent_a, agent_b, response_clean)
        belief_delta_b = _compute_belief_shift(agent_b, agent_a, opening_clean)

        # Store memories
        salience_a = memory_engine.compute_emotional_salience(opening_clean, emotion_delta_a)
        salience_b = memory_engine.compute_emotional_salience(response_clean, emotion_delta_b)

        memory_engine.add_memory(agent_a.id, simulation_id, f"I told {agent_b.name}: {opening_clean[:200]}", tick, salience_a)
        memory_engine.add_memory(agent_b.id, simulation_id, f"{agent_a.name} told me: {opening_clean[:200]}", tick, salience_b)

        # Persist interaction
        interaction = Interaction(
            id=str(uuid.uuid4()),
            simulation_id=simulation_id,
            tick=tick,
            agent_a_id=agent_a.id,
            agent_b_id=agent_b.id,
            content=json.dumps({"a": opening_clean, "b": response_clean}),
            belief_delta_a=belief_delta_a,
            belief_delta_b=belief_delta_b,
            emotional_delta_a=emotion_delta_a,
            emotional_delta_b=emotion_delta_b,
        )
        db.add(interaction)
        db.commit()

        return {
            "id": interaction.id,
            "tick": tick,
            "agent_a": {"id": agent_a.id, "name": agent_a.name, "tier": agent_a.tier},
            "agent_b": {"id": agent_b.id, "name": agent_b.name, "tier": agent_b.tier},
            "topic": topic,
            "a_says": opening_clean,
            "b_says": response_clean,
            "emotion_delta_a": emotion_delta_a,
            "emotion_delta_b": emotion_delta_b,
        }

    except Exception as e:
        print(f"Interaction error at tick {tick}: {e}")
        return None


def _statistical_interaction(agent_a, agent_b, simulation_id, tick, topic, db) -> dict:
    """Fast statistical interaction for shallow-shallow pairs."""
    lean_diff = agent_b.political_lean - agent_a.political_lean
    contagion = lean_diff * 0.05 * agent_b.influence_score

    emotion_delta_a = random.gauss(0, 0.05)
    emotion_delta_b = random.gauss(0, 0.05)

    agent_a.current_emotion = max(-1.0, min(1.0, agent_a.current_emotion + emotion_delta_a))
    agent_b.current_emotion = max(-1.0, min(1.0, agent_b.current_emotion + emotion_delta_b))

    interaction = Interaction(
        id=str(uuid.uuid4()),
        simulation_id=simulation_id,
        tick=tick,
        agent_a_id=agent_a.id,
        agent_b_id=agent_b.id,
        content=json.dumps({"type": "statistical", "topic": topic}),
        belief_delta_a=contagion,
        belief_delta_b=-contagion * 0.5,
        emotional_delta_a=emotion_delta_a,
        emotional_delta_b=emotion_delta_b,
    )
    db.add(interaction)

    return {
        "id": interaction.id,
        "tick": tick,
        "agent_a": {"id": agent_a.id, "name": agent_a.name, "tier": "shallow"},
        "agent_b": {"id": agent_b.id, "name": agent_b.name, "tier": "shallow"},
        "topic": topic,
        "type": "statistical",
    }


def _select_interaction_pairs(agents, social_graph, tick) -> list[tuple]:
    """Select agent pairs for this tick based on social graph topology."""
    pairs = []
    deep_agents = [a for a in agents if a.tier == "deep"]

    random.shuffle(deep_agents)
    for i in range(0, len(deep_agents) - 1, 2):
        neighbours = get_agent_neighbours(social_graph, deep_agents[i].id)
        if neighbours:
            partner_id = random.choice(neighbours)
            pairs.append((deep_agents[i].id, partner_id))

    shallow_agents = [a for a in agents if a.tier == "shallow"]
    sample_size = min(len(shallow_agents) // 4, 20)
    sampled = random.sample(shallow_agents, sample_size) if shallow_agents else []
    for i in range(0, len(sampled) - 1, 2):
        pairs.append((sampled[i].id, sampled[i + 1].id))

    return pairs


def _extract_emotion_delta(text: str) -> float:
    """Extract EMOTION_DELTA from LLM response."""
    import re
    match = re.search(r"EMOTION_DELTA:\s*([-\d.]+)", text)
    if match:
        try:
            return max(-0.5, min(0.5, float(match.group(1))))
        except ValueError:
            pass
    return random.gauss(0, 0.05)


def _strip_emotion_tag(text: str) -> str:
    """Remove EMOTION_DELTA line from response."""
    import re
    return re.sub(r"\nEMOTION_DELTA:.*$", "", text, flags=re.MULTILINE).strip()


def _compute_belief_shift(agent_listener, agent_speaker, message: str) -> float:
    """
    Compute how much a listener's belief shifts after hearing a speaker.
    Agreeableness and political proximity increase susceptibility.
    """
    susceptibility = agent_listener.agreeableness * 0.3
    lean_similarity = 1.0 - abs(agent_listener.political_lean - agent_speaker.political_lean)
    shift = susceptibility * lean_similarity * 0.05 * agent_speaker.influence_score
    return round(shift, 4)