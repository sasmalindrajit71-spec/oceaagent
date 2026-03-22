"""
OCEAN Database Models — SQLAlchemy ORM definitions.
Each simulation run gets its own SQLite file at data/simulations/{sim_id}.db
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending|extracting|validating|generating|running|paused|completed|failed
    seed_text = Column(Text)
    seed_url = Column(String)
    knowledge_graph = Column(JSON)          # validated graph nodes/edges
    current_tick = Column(Integer, default=0)
    total_ticks = Column(Integer, default=100)
    deep_agent_count = Column(Integer, default=50)
    shallow_agent_count = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error = Column(Text)
    report = Column(JSON)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    simulation_id = Column(String, nullable=False)
    tier = Column(String, nullable=False)       # deep | shallow
    name = Column(String)
    age = Column(Integer)
    occupation = Column(String)
    education = Column(String)
    location = Column(String)
    political_lean = Column(Float)              # -1.0 (left) to 1.0 (right)
    openness = Column(Float)
    conscientiousness = Column(Float)
    extraversion = Column(Float)
    agreeableness = Column(Float)
    neuroticism = Column(Float)
    emotional_baseline = Column(Float)          # -1.0 (negative) to 1.0 (positive)
    current_emotion = Column(Float)
    belief_vector = Column(JSON)                # {topic: stance_float}
    network_position = Column(Integer)          # node index in social graph
    cluster_id = Column(Integer)
    influence_score = Column(Float, default=1.0)
    provider = Column(String)                   # assigned LLM provider
    model = Column(String)                      # assigned model ID
    created_at = Column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    agent_id = Column(String, nullable=False)
    simulation_id = Column(String, nullable=False)
    tick = Column(Integer)
    content = Column(Text)
    emotional_salience = Column(Float, default=1.0)
    decay_weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True)
    simulation_id = Column(String, nullable=False)
    tick = Column(Integer)
    agent_a_id = Column(String)
    agent_b_id = Column(String)
    content = Column(Text)
    belief_delta_a = Column(Float, default=0.0)
    belief_delta_b = Column(Float, default=0.0)
    emotional_delta_a = Column(Float, default=0.0)
    emotional_delta_b = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    simulation_id = Column(String, nullable=False)
    tick = Column(Integer)
    event_type = Column(String)                 # seed | injection | system
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── DB session factory ──────────────────────────────────────────────────────

DATA_DIR = os.getenv("DATA_DIR", "./data")
MAIN_DB = f"sqlite:///{DATA_DIR}/ocean.db"

engine = create_engine(MAIN_DB, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
