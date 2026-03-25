"""
OCEAN Celery App — async simulation job runner.
"""

import asyncio
import json
import os
import sys
import logging

# Ensure /app is in Python path so all modules resolve
sys.path.insert(0, '/app')

from celery import Celery
from database import SessionLocal, Simulation, Agent, init_db

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("ocean", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    broker_connection_retry_on_startup=True,
)


@celery_app.task(bind=True, name="run_simulation")
def run_simulation_task(self, simulation_id: str):
    """Run the full simulation pipeline for a given simulation ID."""
    init_db()
    asyncio.run(_run_pipeline(simulation_id))


async def _broadcast_event(simulation_id: str, event: dict):
    """
    Broadcast event to all WebSocket clients watching this simulation.
    Handles import dynamically to avoid circular dependencies.
    """
    try:
        from main import broadcast_to_simulation
        await broadcast_to_simulation(simulation_id, event)
    except ImportError:
        logger.warning("Could not import broadcast_to_simulation, events won't be sent to WebSocket")
    except Exception as e:
        logger.error(f"Error broadcasting event: {e}")


async def _run_pipeline(simulation_id: str):
    # Import here to avoid circular imports and ensure path is set
    from simulation.runtime import run_tick
    from config import load_config  # Load fresh config, not cached version
    
    # Reload config to get latest API keys from Settings UI
    config = load_config()

    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=simulation_id).first()
        if not sim:
            logger.error(f"[OCEAN] Simulation {simulation_id} not found")
            await _broadcast_event(simulation_id, {
                "type": "error",
                "message": "Simulation not found"
            })
            return

        # Check agents exist
        from database import Agent
        agent_count = db.query(Agent).filter_by(simulation_id=simulation_id).count()
        if agent_count == 0:
            logger.error(f"[OCEAN] No agents found for simulation {simulation_id}")
            sim.status = "failed"
            sim.error = "No agents generated. Please generate agents before starting."
            db.commit()
            await _broadcast_event(simulation_id, {
                "type": "error",
                "message": "No agents generated. Please generate agents before starting."
            })
            return

        logger.info(f"[OCEAN] Starting simulation {simulation_id} with {agent_count} agents")
        await _broadcast_event(simulation_id, {
            "type": "started",
            "tick": 0,
            "total_ticks": sim.total_ticks,
            "agent_count": agent_count
        })

        sim.status = "running"
        db.commit()

        # Parse social graph
        kg = sim.knowledge_graph or {}
        social_graph_raw = kg.get("social_graph", None)

        if not social_graph_raw:
            logger.info(f"[OCEAN] No social graph for {simulation_id} — building now")
            # Build social graph from existing agents
            from database import Agent as AgentModel
            from simulation.network import build_social_graph
            agents = db.query(AgentModel).filter_by(simulation_id=simulation_id).all()
            agent_dicts = [
                {
                    "id": a.id, "tier": a.tier, "cluster_id": a.cluster_id or 0,
                    "influence_score": a.influence_score or 1.0,
                    "political_lean": a.political_lean or 0.0,
                }
                for a in agents
            ]
            social_graph = build_social_graph(agent_dicts)
            kg["social_graph"] = json.dumps(social_graph)
            sim.knowledge_graph = kg
            db.commit()
            social_graph_raw = kg["social_graph"]

        social_graph = json.loads(social_graph_raw) if isinstance(social_graph_raw, str) else social_graph_raw

        total_ticks = sim.total_ticks
        start_tick = sim.current_tick + 1

        logger.info(f"[OCEAN] Running ticks {start_tick} to {total_ticks}")

        for tick in range(start_tick, total_ticks + 1):
            # Refresh sim status
            db.expire(sim)
            db.refresh(sim)

            if sim.status == "paused":
                logger.info(f"[OCEAN] Simulation {simulation_id} paused at tick {tick}")
                await _broadcast_event(simulation_id, {
                    "type": "paused",
                    "tick": tick
                })
                break
            if sim.status == "failed":
                logger.error(f"[OCEAN] Simulation {simulation_id} marked as failed")
                break

            try:
                # Create event callback for this tick
                async def on_event(event):
                    event["simulation_id"] = simulation_id
                    await _broadcast_event(simulation_id, event)

                result = await run_tick(simulation_id, tick, social_graph, on_event=on_event)
                interaction_count = len(result.get('interactions', []))
                logger.info(f"[OCEAN] Tick {tick} complete — {interaction_count} interactions")
                
                # Broadcast tick completion
                await _broadcast_event(simulation_id, {
                    "type": "tick_complete",
                    "tick": tick,
                    "interactions": interaction_count,
                    "progress": (tick / total_ticks) * 100
                })
                
            except Exception as tick_err:
                logger.error(f"[OCEAN] Tick {tick} error: {tick_err}", exc_info=True)
                # Broadcast the error but continue simulation
                await _broadcast_event(simulation_id, {
                    "type": "tick_error",
                    "tick": tick,
                    "error": str(tick_err)
                })

            sim.current_tick = tick
            db.commit()

            # Tick delay
            delay = config.simulation.tick_delay_ms / 1000.0
            await asyncio.sleep(delay)

        if sim.status == "running":
            sim.status = "completed"
            db.commit()
            logger.info(f"[OCEAN] Simulation {simulation_id} completed")
            await _broadcast_event(simulation_id, {
                "type": "completed",
                "tick": total_ticks
            })

    except Exception as e:
        logger.error(f"[OCEAN] Pipeline error: {e}", exc_info=True)
        await _broadcast_event(simulation_id, {
            "type": "fatal_error",
            "error": str(e)
        })
        try:
            db.rollback()
            sim = db.query(Simulation).filter_by(id=simulation_id).first()
            if sim:
                sim.status = "failed"
                sim.error = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()