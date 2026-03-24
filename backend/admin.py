"""
OceaAgent Admin API — protected routes for the admin panel.
Uses HTTP Basic Auth with username/password from environment variables.
"""

import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from analytics import get_stats
from database import SessionLocal, Simulation, Agent, Interaction

router = APIRouter()
security = HTTPBasic()

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "ocean_admin_2026")


def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username.encode(), ADMIN_USER.encode())
    correct_pass = secrets.compare_digest(credentials.password.encode(), ADMIN_PASS.encode())
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/stats")
def admin_stats(days: int = 30, _: str = Depends(verify_admin)):
    """Full analytics dashboard data."""
    return get_stats(days=days)


@router.get("/simulations")
def admin_simulations(_: str = Depends(verify_admin)):
    """All simulations with full details."""
    db = SessionLocal()
    try:
        sims = db.query(Simulation).order_by(Simulation.created_at.desc()).all()
        return [
            {
                "id":            s.id,
                "title":         s.title,
                "status":        s.status,
                "created_at":    s.created_at.isoformat() if s.created_at else None,
                "current_tick":  s.current_tick,
                "total_ticks":   s.total_ticks,
                "deep_agents":   s.deep_agent_count,
                "shallow_agents":s.shallow_agent_count,
                "has_report":    bool(s.report),
                "error":         s.error,
            }
            for s in sims
        ]
    finally:
        db.close()


@router.get("/overview")
def admin_overview(_: str = Depends(verify_admin)):
    """Quick numbers for admin header cards."""
    db = SessionLocal()
    try:
        from analytics import SessionLocal as ADB, PageView, ActiveSession, SimEvent
        from sqlalchemy import func, distinct
        from datetime import datetime, timedelta

        adb = ADB()
        active_cutoff = datetime.utcnow() - timedelta(minutes=5)
        active_now = adb.query(ActiveSession).filter(
            ActiveSession.last_seen >= active_cutoff
        ).count()
        total_views = adb.query(PageView).count()
        today_views = adb.query(PageView).filter(
            PageView.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count()
        adb.close()

        total_sims  = db.query(Simulation).count()
        running     = db.query(Simulation).filter_by(status="running").count()
        total_agents= db.query(Agent).count()
        total_inter = db.query(Interaction).count()

        return {
            "active_now":    active_now,
            "total_views":   total_views,
            "today_views":   today_views,
            "total_sims":    total_sims,
            "running_sims":  running,
            "total_agents":  total_agents,
            "total_interactions": total_inter,
        }
    finally:
        db.close()