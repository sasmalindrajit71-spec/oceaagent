"""
OCEAN Report Engine — three-pass analysis producing clear, readable intelligence reports.
"""

import json
from database import SessionLocal, Simulation, Agent, Interaction, Event
from llm import router


PATTERN_SYSTEM = """You are a social dynamics analyst. Analyze simulation data and identify clear patterns.
Return ONLY valid JSON — no markdown, no preamble:
{
  "dominant_narratives": ["clear description of narrative 1", "clear description of narrative 2"],
  "opinion_clusters": [{"cluster_id": 0, "stance": "clear stance description", "size": 10, "avg_emotion": 0.2}],
  "information_cascades": ["how idea X spread through the network"],
  "tipping_points": [{"tick": 15, "description": "what changed at this moment"}],
  "echo_chambers": ["description of identified echo chamber"],
  "prediction": "Based on the simulation dynamics, the most likely outcome is: [specific prediction]"
}"""

CAUSAL_SYSTEM = """You are a causal attribution analyst.
Return ONLY valid JSON:
{
  "key_influencers": [{"name": "agent name", "reason": "why they were pivotal"}],
  "causal_chains": ["specific causal chain description"],
  "amplification_mechanisms": ["what made ideas spread"],
  "suppression_mechanisms": ["what stopped ideas from spreading"],
  "main_finding": "The single most important finding from this simulation in one sentence."
}"""

NARRATIVE_SYSTEM = """You are a senior intelligence analyst writing a briefing for a non-technical audience.

CRITICAL RULES:
1. Write in PLAIN ENGLISH — no jargon, no academic language
2. Be SPECIFIC — name actual agents, actual stances, actual outcomes
3. Make a CLEAR PREDICTION at the end — commit to one outcome
4. Structure: Summary → What happened → Why → Prediction → Key agents
5. Keep it under 500 words
6. Every paragraph must be immediately understandable by anyone

Do NOT write vague academic analysis. Write like you are explaining to a smart friend what happened in this simulation and what it means."""


async def generate_report(simulation_id: str) -> dict:
    """Run the full 3-pass report generation pipeline."""
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=simulation_id).first()
        if not sim:
            raise ValueError(f"Simulation {simulation_id} not found")

        agents = db.query(Agent).filter_by(simulation_id=simulation_id).all()
        interactions = db.query(Interaction).filter_by(simulation_id=simulation_id).order_by(
            Interaction.tick
        ).limit(200).all()

        # Build readable interaction samples
        agent_map = {a.id: a.name for a in agents}
        interaction_samples = []
        for i in interactions[:30]:
            try:
                content = json.loads(i.content) if isinstance(i.content, str) else (i.content or {})
                a_name = agent_map.get(i.agent_a_id, 'Unknown')
                b_name = agent_map.get(i.agent_b_id, 'Unknown')
                if content.get('a'):
                    interaction_samples.append(
                        f"Tick {i.tick}: {a_name} said: \"{content['a'][:120]}\""
                    )
            except Exception:
                pass

        data_summary = _build_data_summary(sim, agents, interactions, agent_map, interaction_samples)

        # Pass 1: Pattern Detection
        pattern_response = await router.complete(
            role="report_engine",
            messages=[{"role": "user", "content": f"Analyze these simulation results and identify patterns:\n\n{data_summary}"}],
            system=PATTERN_SYSTEM,
            max_tokens=1500,
            temperature=0.3,
        )
        patterns = _safe_parse_json(pattern_response)

        # Pass 2: Causal Attribution
        causal_response = await router.complete(
            role="report_engine",
            messages=[{"role": "user", "content": f"Simulation data:\n{data_summary}\n\nPatterns found:\n{json.dumps(patterns, indent=2)}\n\nNow explain WHY these patterns emerged."}],
            system=CAUSAL_SYSTEM,
            max_tokens=1500,
            temperature=0.3,
        )
        causation = _safe_parse_json(causal_response)

        # Pass 3: Narrative Synthesis — plain English briefing
        deep_agents = [a for a in agents if a.tier == 'deep']
        agent_summaries = []
        for a in sorted(deep_agents, key=lambda x: x.influence_score or 0, reverse=True)[:8]:
            emotion_word = "positive" if (a.current_emotion or 0) > 0.2 else "negative" if (a.current_emotion or 0) < -0.2 else "neutral"
            agent_summaries.append(f"- {a.name} ({a.occupation}, {a.location}): final emotion {emotion_word} ({(a.current_emotion or 0):.2f}), influence {(a.influence_score or 0):.2f}")

        synthesis_prompt = f"""Write a clear intelligence briefing about this simulation.

SIMULATION TOPIC: {sim.seed_text[:600] if sim.seed_text else sim.title}

WHAT HAPPENED IN THE SIMULATION:
- {len(agents)} agents ({sum(1 for a in agents if a.tier=='deep')} deep, {sum(1 for a in agents if a.tier=='shallow')} shallow)
- {sim.current_tick} ticks completed
- {len(interactions)} agent interactions recorded
- Average final emotion: {sum(a.current_emotion or 0 for a in agents)/max(1,len(agents)):.3f} (negative=pessimistic, positive=optimistic)

KEY AGENTS AND THEIR FINAL STATE:
{chr(10).join(agent_summaries)}

SAMPLE ACTUAL INTERACTIONS:
{chr(10).join(interaction_samples[:15])}

PATTERNS IDENTIFIED:
{json.dumps(patterns, indent=2)}

CAUSAL ANALYSIS:
{json.dumps(causation, indent=2)}

Write a clear, plain-English report. Make a specific prediction. Name real agents. Be concrete."""

        narrative = await router.complete(
            role="report_engine",
            messages=[{"role": "user", "content": synthesis_prompt}],
            system=NARRATIVE_SYSTEM,
            max_tokens=2000,
            temperature=0.4,
        )

        # Build influence ranking
        influence_ranking = sorted(
            [{"id": a.id, "name": a.name, "tier": a.tier,
              "influence": round(a.influence_score or 0, 3),
              "final_emotion": round(a.current_emotion or 0, 3),
              "occupation": a.occupation or '',
              "location": a.location or '',
              "cluster": a.cluster_id}
             for a in agents if a.tier == "deep"],
            key=lambda x: x["influence"],
            reverse=True,
        )[:15]

        # Cluster emotion summary
        cluster_emotions = {}
        for a in agents:
            cid = str(a.cluster_id or 0)
            if cid not in cluster_emotions:
                cluster_emotions[cid] = []
            cluster_emotions[cid].append(a.current_emotion or 0)
        cluster_summary = {
            cid: {
                "avg_emotion": round(sum(v)/len(v), 3),
                "size": len(v),
                "label": "Positive" if sum(v)/len(v) > 0.1 else "Negative" if sum(v)/len(v) < -0.1 else "Neutral"
            }
            for cid, v in cluster_emotions.items()
        }

        report = {
            "simulation_id": simulation_id,
            "title": sim.title,
            "ticks_completed": sim.current_tick,
            "agent_count": len(agents),
            "patterns": patterns,
            "causation": causation,
            "narrative": narrative,
            "influence_ranking": influence_ranking,
            "cluster_summary": cluster_summary,
            "stats": {
                "total_interactions": len(interactions),
                "avg_emotion_final": round(sum(a.current_emotion or 0 for a in agents) / max(1, len(agents)), 3),
                "deep_agent_count": sum(1 for a in agents if a.tier == "deep"),
                "shallow_agent_count": sum(1 for a in agents if a.tier == "shallow"),
            }
        }

        sim.report = report
        db.commit()
        return report

    finally:
        db.close()


def _build_data_summary(sim, agents, interactions, agent_map, interaction_samples) -> str:
    cluster_emotions = {}
    for a in agents:
        cid = a.cluster_id or 0
        if cid not in cluster_emotions:
            cluster_emotions[cid] = []
        cluster_emotions[cid].append(a.current_emotion or 0)

    cluster_summary = {
        str(cid): {"avg_emotion": round(sum(v)/len(v), 3), "size": len(v)}
        for cid, v in cluster_emotions.items()
    }

    top_agents = sorted(agents, key=lambda x: x.influence_score or 0, reverse=True)[:10]
    agent_list = "\n".join([
        f"  {a.name}: {a.occupation}, {a.location}, lean={round(a.political_lean or 0, 2)}, emotion={round(a.current_emotion or 0, 2)}"
        for a in top_agents if a.tier == 'deep'
    ])

    return f"""
Simulation: {sim.title}
Topic: {sim.seed_text[:400] if sim.seed_text else 'Unknown'}
Ticks: {sim.current_tick}/{sim.total_ticks}
Agents: {sum(1 for a in agents if a.tier=='deep')} deep, {sum(1 for a in agents if a.tier=='shallow')} shallow
Interactions: {len(interactions)}
Average final emotion: {round(sum(a.current_emotion or 0 for a in agents)/max(1,len(agents)), 3)}

Top influential agents:
{agent_list}

Cluster emotional states:
{json.dumps(cluster_summary, indent=2)}

Sample interactions from simulation:
{chr(10).join(interaction_samples[:20])}
"""


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