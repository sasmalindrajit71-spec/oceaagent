"""
OCEAN Analytics — tracks every visitor, page view, simulation event.
Stored in SQLite alongside the main database.
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi import Request

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
ANALYTICS_DB = f"sqlite:///{DATA_DIR}/analytics.db"

engine = create_engine(ANALYTICS_DB, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class PageView(Base):
    __tablename__ = "page_views"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    timestamp  = Column(DateTime, default=datetime.utcnow, index=True)
    path       = Column(String(500))
    method     = Column(String(10))
    ip_hash    = Column(String(64))   # hashed for privacy
    country    = Column(String(64), default="Unknown")
    city       = Column(String(64), default="Unknown")
    device     = Column(String(32), default="Unknown")
    browser    = Column(String(64), default="Unknown")
    os         = Column(String(64), default="Unknown")
    referrer   = Column(String(500), default="")
    session_id = Column(String(64), default="")
    duration_ms= Column(Integer, default=0)


class SimEvent(Base):
    __tablename__ = "sim_events"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    timestamp    = Column(DateTime, default=datetime.utcnow, index=True)
    event_type   = Column(String(50))   # created, started, completed, failed, report_generated
    simulation_id= Column(String(64))
    provider     = Column(String(32), default="")
    agent_count  = Column(Integer, default=0)
    tick_count   = Column(Integer, default=0)
    duration_s   = Column(Float, default=0)


class ActiveSession(Base):
    __tablename__ = "active_sessions"
    session_id  = Column(String(64), primary_key=True)
    last_seen   = Column(DateTime, default=datetime.utcnow)
    path        = Column(String(500), default="/")


def init_analytics():
    Base.metadata.create_all(engine)


def parse_user_agent(ua: str) -> dict:
    ua = ua.lower()
    device = "Desktop"
    if any(x in ua for x in ["mobile", "android", "iphone", "ipad"]):
        device = "Mobile"
    elif "tablet" in ua:
        device = "Tablet"

    browser = "Other"
    if "chrome" in ua and "edg" not in ua and "opr" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    elif "opr" in ua or "opera" in ua:
        browser = "Opera"

    os_name = "Other"
    if "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macos" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"
    elif "linux" in ua:
        os_name = "Linux"

    return {"device": device, "browser": browser, "os": os_name}


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def get_session_id(request: Request) -> str:
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "")
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def track_pageview(request: Request, path: str = None):
    """Track a page view. Call from API endpoints."""
    try:
        db = SessionLocal()
        ua_str = request.headers.get("user-agent", "")
        ua_info = parse_user_agent(ua_str)
        ip = get_client_ip(request)
        session_id = get_session_id(request)
        referrer = request.headers.get("referer", "")

        view = PageView(
            path=path or str(request.url.path),
            method=request.method,
            ip_hash=hash_ip(ip),
            device=ua_info["device"],
            browser=ua_info["browser"],
            os=ua_info["os"],
            referrer=referrer[:500] if referrer else "",
            session_id=session_id,
        )
        db.add(view)

        # Update active session
        session = db.query(ActiveSession).filter_by(session_id=session_id).first()
        if session:
            session.last_seen = datetime.utcnow()
            session.path = path or str(request.url.path)
        else:
            db.add(ActiveSession(session_id=session_id, path=path or str(request.url.path)))

        db.commit()
        db.close()
    except Exception as e:
        print(f"Analytics error: {e}")


def track_sim_event(event_type: str, simulation_id: str, **kwargs):
    """Track simulation lifecycle events."""
    try:
        db = SessionLocal()
        event = SimEvent(
            event_type=event_type,
            simulation_id=simulation_id,
            **{k: v for k, v in kwargs.items() if hasattr(SimEvent, k)}
        )
        db.add(event)
        db.commit()
        db.close()
    except Exception as e:
        print(f"Sim event tracking error: {e}")


def get_stats(days: int = 30) -> dict:
    """Get analytics summary for admin panel."""
    db = SessionLocal()
    since = datetime.utcnow() - timedelta(days=days)

    try:
        total_views   = db.query(PageView).count()
        recent_views  = db.query(PageView).filter(PageView.timestamp >= since).count()

        # Unique visitors (by session_id)
        from sqlalchemy import func, distinct
        total_unique  = db.query(func.count(distinct(PageView.session_id))).scalar() or 0
        recent_unique = db.query(func.count(distinct(PageView.session_id))).filter(PageView.timestamp >= since).scalar() or 0

        # Active right now (seen in last 5 minutes)
        active_cutoff = datetime.utcnow() - timedelta(minutes=5)
        active_now    = db.query(ActiveSession).filter(ActiveSession.last_seen >= active_cutoff).count()

        # Device breakdown
        devices = {}
        for row in db.query(PageView.device, func.count(PageView.id)).filter(
            PageView.timestamp >= since
        ).group_by(PageView.device).all():
            devices[row[0]] = row[1]

        # Browser breakdown
        browsers = {}
        for row in db.query(PageView.browser, func.count(PageView.id)).filter(
            PageView.timestamp >= since
        ).group_by(PageView.browser).all():
            browsers[row[0]] = row[1]

        # OS breakdown
        os_stats = {}
        for row in db.query(PageView.os, func.count(PageView.id)).filter(
            PageView.timestamp >= since
        ).group_by(PageView.os).all():
            os_stats[row[0]] = row[1]

        # Top pages
        top_pages = []
        for row in db.query(PageView.path, func.count(PageView.id)).filter(
            PageView.timestamp >= since
        ).group_by(PageView.path).order_by(func.count(PageView.id).desc()).limit(10).all():
            top_pages.append({"path": row[0], "views": row[1]})

        # Daily views (last 30 days)
        from sqlalchemy import cast, Date
        daily = []
        for row in db.query(
            func.date(PageView.timestamp).label("date"),
            func.count(PageView.id).label("views"),
            func.count(distinct(PageView.session_id)).label("visitors")
        ).filter(PageView.timestamp >= since).group_by(
            func.date(PageView.timestamp)
        ).order_by(func.date(PageView.timestamp)).all():
            daily.append({"date": str(row.date), "views": row.views, "visitors": row.visitors})

        # Simulation stats
        total_sims     = db.query(SimEvent).filter_by(event_type="created").count()
        completed_sims = db.query(SimEvent).filter_by(event_type="completed").count()
        failed_sims    = db.query(SimEvent).filter_by(event_type="failed").count()

        # Recent activity feed
        recent_activity = []
        for view in db.query(PageView).order_by(PageView.timestamp.desc()).limit(20).all():
            recent_activity.append({
                "time": view.timestamp.isoformat(),
                "path": view.path,
                "device": view.device,
                "browser": view.browser,
                "os": view.os,
            })

        return {
            "overview": {
                "total_views":   total_views,
                "recent_views":  recent_views,
                "total_unique":  total_unique,
                "recent_unique": recent_unique,
                "active_now":    active_now,
                "total_sims":    total_sims,
                "completed_sims":completed_sims,
                "failed_sims":   failed_sims,
            },
            "devices":   devices,
            "browsers":  browsers,
            "os_stats":  os_stats,
            "top_pages": top_pages,
            "daily":     daily,
            "recent_activity": recent_activity,
        }
    finally:
        db.close()