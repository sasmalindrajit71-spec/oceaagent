"""
OCEAN Memory Engine — manages agent memory with decay and emotional salience.
"""

import uuid
import math
from datetime import datetime
from typing import List, Optional
from database import Memory, SessionLocal
from config import config


def add_memory(
    agent_id: str,
    simulation_id: str,
    content: str,
    tick: int,
    emotional_salience: float = 1.0,
) -> dict:
    """
    Store a new memory for an agent.
    Emotional salience > 1.0 means the memory persists longer.
    """
    db = SessionLocal()
    try:
        mem = Memory(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            simulation_id=simulation_id,
            tick=tick,
            content=content,
            emotional_salience=max(0.1, emotional_salience),
            decay_weight=1.0,
        )
        db.add(mem)
        db.commit()
        return _mem_to_dict(mem)
    finally:
        db.close()


def decay_memories(agent_id: str, simulation_id: str, current_tick: int):
    """
    Apply memory decay for all memories of an agent.
    decay_weight = e^(-decay_rate * ticks_elapsed / emotional_salience)
    Memories below threshold are pruned.
    """
    db = SessionLocal()
    try:
        memories = db.query(Memory).filter_by(
            agent_id=agent_id,
            simulation_id=simulation_id
        ).all()

        decay_rate = config.memory.decay_rate
        threshold = 0.05
        to_delete = []

        for mem in memories:
            ticks_elapsed = max(0, current_tick - mem.tick)
            # Emotional salience slows decay
            effective_rate = decay_rate / max(0.1, mem.emotional_salience)
            mem.decay_weight = math.exp(-effective_rate * ticks_elapsed)

            if mem.decay_weight < threshold:
                to_delete.append(mem.id)

        for mid in to_delete:
            db.query(Memory).filter_by(id=mid).delete()

        # Enforce max memories per agent
        remaining = db.query(Memory).filter_by(
            agent_id=agent_id,
            simulation_id=simulation_id
        ).order_by(Memory.decay_weight.desc()).all()

        max_mem = config.memory.max_memories_per_agent
        if len(remaining) > max_mem:
            for mem in remaining[max_mem:]:
                db.query(Memory).filter_by(id=mem.id).delete()

        db.commit()
    finally:
        db.close()


def get_active_memories(agent_id: str, simulation_id: str, limit: int = 10) -> List[dict]:
    """
    Retrieve active memories, weighted by decay and emotional salience.
    Returns most relevant memories first.
    """
    db = SessionLocal()
    try:
        memories = db.query(Memory).filter_by(
            agent_id=agent_id,
            simulation_id=simulation_id
        ).order_by(
            (Memory.decay_weight * Memory.emotional_salience).desc()
        ).limit(limit).all()
        return [_mem_to_dict(m) for m in memories]
    finally:
        db.close()


def compute_emotional_salience(content: str, emotion_delta: float) -> float:
    """
    Compute emotional salience for a memory.
    High emotion = higher salience = slower decay.
    """
    base = 1.0
    salience_multiplier = config.memory.emotional_salience_multiplier

    # Strong emotion → high salience
    intensity = abs(emotion_delta)
    salience = base + (intensity * salience_multiplier)

    # Keyword boosters for high-salience events
    high_salience_keywords = [
        "crisis", "death", "attack", "protest", "collapse", "victory",
        "disaster", "scandal", "breakthrough", "emergency", "threat"
    ]
    content_lower = content.lower()
    for kw in high_salience_keywords:
        if kw in content_lower:
            salience += 0.5
            break

    return min(5.0, salience)


def format_memories_for_prompt(memories: List[dict]) -> str:
    """Format memories as a readable context block for LLM prompts."""
    if not memories:
        return "No significant memories."
    lines = []
    for m in memories:
        weight = m["decay_weight"] * m["emotional_salience"]
        lines.append(f"- [salience={weight:.2f}] {m['content']}")
    return "\n".join(lines)


def _mem_to_dict(m: Memory) -> dict:
    return {
        "id": m.id,
        "agent_id": m.agent_id,
        "simulation_id": m.simulation_id,
        "tick": m.tick,
        "content": m.content,
        "emotional_salience": m.emotional_salience,
        "decay_weight": m.decay_weight,
    }
