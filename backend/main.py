"""
OCEAN FastAPI Backend — REST API + WebSocket for simulation streaming.
"""

import uuid
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import init_db, get_db, SessionLocal, Event
from analytics import init_analytics, track_pageview, SessionLocal as ADB, PageView
from admin import router as admin_router, Simulation, Agent, Interaction
from config import config, save_config, OceanConfig, ProvidersConfig, ProviderConfig, ModelSet
from llm import router as llm_router, test_provider
import ingestion.extractor as extractor
import personas.engine as persona_engine
from simulation.network import build_social_graph
from simulation.runtime import run_tick
from reports.engine import generate_report
from celery_app import run_simulation_task

app = FastAPI(title="OceaAgent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ────────────────────────────────────────────────────────────
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])

# Active WebSocket connections per simulation
_ws_connections: dict[str, list[WebSocket]] = {}


@app.on_event("startup")
async def startup():
    init_db()
    init_analytics()


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# ── Provider / Settings ──────────────────────────────────────────────────────

@app.get("/api/settings/providers")
def get_providers():
    """Return current provider configuration (keys masked)."""
    providers = config.providers.model_dump()
    for name in providers:
        if providers[name].get("api_key"):
            key = providers[name]["api_key"]
            providers[name]["api_key"] = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "****"
    return providers


class UpdateProviderRequest(BaseModel):
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    base_url: Optional[str] = None
    models: Optional[dict] = None


@app.patch("/api/settings/providers/{provider_name}")
def update_provider(provider_name: str, body: UpdateProviderRequest):
    """Update a provider's configuration."""
    if not hasattr(config.providers, provider_name):
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    provider = getattr(config.providers, provider_name)

    if body.api_key is not None:
        provider.api_key = body.api_key
    if body.enabled is not None:
        provider.enabled = body.enabled
    if body.base_url is not None:
        provider.base_url = body.base_url
    if body.models is not None:
        for role, model in body.models.items():
            if hasattr(provider.models, role):
                setattr(provider.models, role, model)

    save_config(config)
    return {"status": "saved"}


@app.post("/api/settings/providers/{provider_name}/test")
async def test_provider_key(provider_name: str):
    """Test if a provider's API key is valid."""
    provider = getattr(config.providers, provider_name, None)
    if not provider:
        raise HTTPException(status_code=404)

    ok = await test_provider(provider_name, provider.api_key)
    return {"provider": provider_name, "valid": ok}


@app.get("/api/settings/nvidia/models")
async def get_nvidia_models():
    """Return all available NVIDIA NIM models grouped by role."""
    from llm.providers.nvidia import NVIDIA_MODELS, MODEL_INFO
    return {"models": NVIDIA_MODELS, "info": MODEL_INFO}


@app.get("/api/settings/active-providers")
def get_active_providers():
    return {"providers": llm_router.get_active_providers()}


@app.post("/api/analytics/pageview")
async def record_pageview(request: Request, body: dict = None):
    """Called by frontend on every page navigation."""
    path = (body or {}).get("path", str(request.url.path))
    await track_pageview(request, path)
    return {"ok": True}


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0"}


# ── Simulations ──────────────────────────────────────────────────────────────

@app.get("/api/simulations")
def list_simulations(db: Session = Depends(get_db)):
    sims = db.query(Simulation).order_by(Simulation.created_at.desc()).all()
    return [_sim_to_dict(s) for s in sims]


@app.get("/api/simulations/{sim_id}")
def get_simulation(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)
    return _sim_to_dict(sim)


class CreateSimulationRequest(BaseModel):
    title: str
    seed_text: Optional[str] = None
    seed_url: Optional[str] = None
    deep_agent_count: int = 50
    shallow_agent_count: int = 500
    total_ticks: int = 100


@app.post("/api/simulations")
async def create_simulation(body: CreateSimulationRequest, db: Session = Depends(get_db)):
    """Create a new simulation and run Graph RAG extraction."""
    sim_id = str(uuid.uuid4())

    sim = Simulation(
        id=sim_id,
        title=body.title,
        status="extracting",
        seed_text=body.seed_text,
        seed_url=body.seed_url,
        deep_agent_count=body.deep_agent_count,
        shallow_agent_count=body.shallow_agent_count,
        total_ticks=body.total_ticks,
    )
    db.add(sim)
    db.commit()

    # Run extraction async
    asyncio.create_task(_extract_and_prepare(sim_id, body))

    return {"id": sim_id, "status": "extracting"}


async def _extract_and_prepare(sim_id: str, body: CreateSimulationRequest):
    """Background: extract knowledge graph and set status to validating."""
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=sim_id).first()

        if body.seed_url:
            text, graph = await extractor.extract_from_url(body.seed_url)
            sim.seed_text = text
        elif body.seed_text:
            graph = await extractor.extract_from_text(body.seed_text)
        else:
            sim.status = "failed"
            sim.error = "No seed content provided"
            db.commit()
            return

        sim.knowledge_graph = graph
        sim.status = "validating"
        db.commit()

    except Exception as e:
        sim.status = "failed"
        sim.error = str(e)
        db.commit()
    finally:
        db.close()


@app.post("/api/simulations/upload")
async def create_simulation_from_file(
    title: str = Form(...),
    deep_agent_count: int = Form(50),
    shallow_agent_count: int = Form(500),
    total_ticks: int = Form(100),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Create simulation from uploaded PDF or text file."""
    sim_id = str(uuid.uuid4())
    content = await file.read()

    sim = Simulation(
        id=sim_id,
        title=title,
        status="extracting",
        deep_agent_count=deep_agent_count,
        shallow_agent_count=shallow_agent_count,
        total_ticks=total_ticks,
    )
    db.add(sim)
    db.commit()

    asyncio.create_task(_extract_from_file(sim_id, content, file.filename or ""))
    return {"id": sim_id, "status": "extracting"}


async def _extract_from_file(sim_id: str, content: bytes, filename: str):
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=sim_id).first()

        if filename.lower().endswith(".pdf"):
            text, graph = await extractor.extract_from_pdf(content)
        else:
            text = content.decode("utf-8", errors="ignore")
            graph = await extractor.extract_from_text(text)

        sim.seed_text = text
        sim.knowledge_graph = graph
        sim.status = "validating"
        db.commit()
    except Exception as e:
        sim.status = "failed"
        sim.error = str(e)
        db.commit()
    finally:
        db.close()


# Graph validation — operator approves/edits extracted graph
@app.patch("/api/simulations/{sim_id}/graph")
def update_graph(sim_id: str, graph: dict, db: Session = Depends(get_db)):
    """Operator edits to the knowledge graph before agent generation."""
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)
    sim.knowledge_graph = graph
    db.commit()
    return {"status": "updated"}


@app.post("/api/simulations/{sim_id}/generate-agents")
async def generate_agents(sim_id: str, db: Session = Depends(get_db)):
    """Generate agent population and social graph after graph validation."""
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)

    sim.status = "generating"
    db.commit()

    asyncio.create_task(_generate_agents_task(sim_id))
    return {"status": "generating"}


async def _generate_agents_task(sim_id: str):
    db = SessionLocal()
    try:
        sim = db.query(Simulation).filter_by(id=sim_id).first()
        graph = sim.knowledge_graph or {}

        agents = await persona_engine.generate_agent_population(
            sim_id, graph,
            deep_count=sim.deep_agent_count,
            shallow_count=sim.shallow_agent_count,
        )

        # Persist agents
        for a in agents:
            db.add(Agent(**{k: v for k, v in a.items() if k != "belief_vector"},
                         belief_vector=a.get("belief_vector", {})))
        db.flush()

        # Build social graph
        social_graph = build_social_graph(agents)

        # Store social graph inside knowledge_graph blob
        kg = sim.knowledge_graph or {}
        kg["social_graph"] = json.dumps(social_graph)
        sim.knowledge_graph = kg
        sim.status = "ready"
        db.commit()

    except Exception as e:
        db.rollback()
        sim = db.query(Simulation).filter_by(id=sim_id).first()
        if sim:
            sim.status = "failed"
            sim.error = str(e)
            db.commit()
    finally:
        db.close()


@app.post("/api/simulations/{sim_id}/start")
def start_simulation(sim_id: str, db: Session = Depends(get_db)):
    """Start or resume simulation."""
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)
    if sim.status not in ["ready", "paused"]:
        raise HTTPException(status_code=400, detail=f"Cannot start simulation in status: {sim.status}")

    sim.status = "running"
    db.commit()

    run_simulation_task.delay(sim_id)
    return {"status": "running"}


@app.post("/api/simulations/{sim_id}/pause")
def pause_simulation(sim_id: str, db: Session = Depends(get_db)):
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)
    sim.status = "paused"
    db.commit()
    return {"status": "paused"}


@app.post("/api/simulations/{sim_id}/inject-event")
async def inject_event(sim_id: str, body: dict, db: Session = Depends(get_db)):
    """Inject a new event into a running simulation."""
    sim = db.query(Simulation).filter_by(id=sim_id).first()
    if not sim:
        raise HTTPException(status_code=404)

    event = Event(
        id=str(uuid.uuid4()),
        simulation_id=sim_id,
        tick=sim.current_tick,
        event_type="injection",
        content=body.get("content", ""),
    )
    db.add(event)
    db.commit()
    return {"status": "injected", "event_id": event.id}


@app.post("/api/simulations/{sim_id}/report")
async def generate_simulation_report(sim_id: str):
    """Trigger report generation for a completed/paused simulation."""
    report = await generate_report(sim_id)
    return report


# ── Agents ──────────────────────────────────────────────────────────────────

@app.get("/api/simulations/{sim_id}/agents")
def get_agents(sim_id: str, tier: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Agent).filter_by(simulation_id=sim_id)
    if tier:
        q = q.filter_by(tier=tier)
    agents = q.all()
    return [_agent_to_dict(a) for a in agents]


@app.get("/api/simulations/{sim_id}/agents/{agent_id}")
def get_agent(sim_id: str, agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter_by(id=agent_id, simulation_id=sim_id).first()
    if not agent:
        raise HTTPException(status_code=404)
    return _agent_to_dict(agent)


@app.get("/api/simulations/{sim_id}/interactions")
def get_interactions(sim_id: str, tick: Optional[int] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Interaction).filter_by(simulation_id=sim_id)
    if tick is not None:
        q = q.filter_by(tick=tick)
    interactions = q.order_by(Interaction.tick.desc()).limit(limit).all()
    return [_interaction_to_dict(i) for i in interactions]


# ── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws/{sim_id}")
async def websocket_endpoint(websocket: WebSocket, sim_id: str):
    """Real-time simulation state streaming."""
    await websocket.accept()
    if sim_id not in _ws_connections:
        _ws_connections[sim_id] = []
    _ws_connections[sim_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        _ws_connections[sim_id].remove(websocket)


async def broadcast_to_simulation(sim_id: str, message: dict):
    """Broadcast a message to all WebSocket clients watching this simulation."""
    connections = _ws_connections.get(sim_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


# ── Serializers ──────────────────────────────────────────────────────────────

def _sim_to_dict(s: Simulation) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "status": s.status,
        "current_tick": s.current_tick,
        "total_ticks": s.total_ticks,
        "deep_agent_count": s.deep_agent_count,
        "shallow_agent_count": s.shallow_agent_count,
        "knowledge_graph": {
            k: v for k, v in (s.knowledge_graph or {}).items()
            if k != "social_graph"
        },
        "has_report": bool(s.report),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "error": s.error,
    }


def _agent_to_dict(a: Agent) -> dict:
    return {
        "id": a.id,
        "simulation_id": a.simulation_id,
        "tier": a.tier,
        "name": a.name,
        "age": a.age,
        "occupation": a.occupation,
        "education": a.education,
        "location": a.location,
        "political_lean": a.political_lean,
        "openness": a.openness,
        "conscientiousness": a.conscientiousness,
        "extraversion": a.extraversion,
        "agreeableness": a.agreeableness,
        "neuroticism": a.neuroticism,
        "emotional_baseline": a.emotional_baseline,
        "current_emotion": a.current_emotion,
        "belief_vector": a.belief_vector,
        "cluster_id": a.cluster_id,
        "influence_score": a.influence_score,
        "provider": a.provider,
        "model": a.model,
    }


def _interaction_to_dict(i: Interaction) -> dict:
    return {
        "id": i.id,
        "simulation_id": i.simulation_id,
        "tick": i.tick,
        "agent_a_id": i.agent_a_id,
        "agent_b_id": i.agent_b_id,
        "content": i.content,
        "belief_delta_a": i.belief_delta_a,
        "belief_delta_b": i.belief_delta_b,
        "emotional_delta_a": i.emotional_delta_a,
        "emotional_delta_b": i.emotional_delta_b,
    }