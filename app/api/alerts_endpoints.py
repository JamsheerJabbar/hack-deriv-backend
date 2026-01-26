"""
Alert Engine API Endpoints
==========================
REST API endpoints for managing the alert engine.

Endpoints:
- POST   /api/v1/alerts/metrics           - Create a new metric spec
- GET    /api/v1/alerts/metrics           - List all metric specs
- GET    /api/v1/alerts/metrics/{id}      - Get a specific metric
- PUT    /api/v1/alerts/metrics/{id}      - Update a metric
- DELETE /api/v1/alerts/metrics/{id}      - Delete a metric
- GET    /api/v1/alerts/active            - Get active alerts
- GET    /api/v1/alerts/history           - Get alert history
- POST   /api/v1/alerts/events            - Push a new event
- GET    /api/v1/alerts/stats             - Get engine stats
- POST   /api/v1/alerts/engine/start      - Start the alert engine
- POST   /api/v1/alerts/engine/stop       - Stop the alert engine
- GET    /api/v1/alerts/engine/status     - Get engine status
- POST   /api/v1/alerts/generator/start   - Start event generator
- POST   /api/v1/alerts/generator/stop    - Stop event generator
- GET    /api/v1/alerts/generator/status  - Get generator status
- POST   /api/v1/alerts/generator/burst   - Generate burst events for testing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json

from app.services.alert_engine import AlertEngineService, ALERTS_DB_PATH
from app.services.alert_events_generate import EventGenerator
import os

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

# Initialize alert engine
alert_engine = AlertEngineService()

# Initialize event generator (singleton)
event_generator = EventGenerator()
_generator_running = False  # Track generator state

# Check if DB exists and initialize if needed
if not os.path.exists(ALERTS_DB_PATH):
    schema_path = os.path.join(os.path.dirname(__file__), "..", "files", "alerts_schema.sql")
    alert_engine.initialize_db(schema_path)


# ==================== PYDANTIC MODELS ====================

class MetricCreate(BaseModel):
    """Model for creating a new metric spec."""
    name: str = Field(..., description="Human-readable metric name")
    description: Optional[str] = Field(None, description="Description of what this metric tracks")
    table_name: str = Field(..., description="Event type this metric applies to (e.g., 'login', 'transaction')")
    filter_json: Dict[str, Any] = Field(default={}, description="Filter conditions as JSON")
    window_sec: int = Field(..., description="Sliding window duration in seconds", ge=1)
    threshold: int = Field(..., description="Count threshold to trigger alert", ge=1)
    severity: str = Field(default="medium", description="Alert severity: low, medium, high, critical")


class MetricUpdate(BaseModel):
    """Model for updating a metric spec."""
    name: Optional[str] = None
    description: Optional[str] = None
    table_name: Optional[str] = None
    filter_json: Optional[Dict[str, Any]] = None
    window_sec: Optional[int] = Field(None, ge=1)
    threshold: Optional[int] = Field(None, ge=1)
    severity: Optional[str] = None


class EventCreate(BaseModel):
    """Model for creating a new event."""
    table_name: str = Field(..., description="Event type (e.g., 'login', 'transaction', 'kyc')")
    payload: Dict[str, Any] = Field(..., description="Event payload data")


class MetricResponse(BaseModel):
    """Response model for a metric."""
    metric_id: int
    name: str
    description: Optional[str]
    table_name: str
    filter_json: str
    window_sec: int
    threshold: int
    is_active: bool
    severity: str
    created_at: Optional[str]
    updated_at: Optional[str]


class GeneratorConfig(BaseModel):
    """Configuration for the event generator."""
    user_interval: float = Field(default=60, description="Interval for user events in seconds")
    login_min_interval: float = Field(default=2, description="Min interval for login events")
    login_max_interval: float = Field(default=10, description="Max interval for login events")
    txn_min_interval: float = Field(default=1, description="Min interval for transaction events")
    txn_max_interval: float = Field(default=4, description="Max interval for transaction events")
    kyc_min_interval: float = Field(default=10, description="Min interval for KYC events")
    kyc_max_interval: float = Field(default=20, description="Max interval for KYC events")


class BurstRequest(BaseModel):
    """Request model for generating burst events."""
    event_type: str = Field(..., description="Event type: 'login', 'transaction', or 'kyc'")
    count: int = Field(default=10, description="Number of events to generate", ge=1, le=100)
    status: Optional[str] = Field(default=None, description="Status for the events (e.g., 'failed', 'success')")


# ==================== METRIC ENDPOINTS ====================

@router.post("/metrics", response_model=dict)
async def create_metric(metric: MetricCreate):
    """
    Create a new metric spec (alert definition).
    
    Example:
    ```json
    {
        "name": "Failed Login Spike",
        "description": "Triggers when failed logins exceed threshold",
        "table_name": "login",
        "filter_json": {"status": "failed"},
        "window_sec": 300,
        "threshold": 10,
        "severity": "high"
    }
    ```
    """
    metric_id = alert_engine.create_metric(
        name=metric.name,
        description=metric.description or "",
        table_name=metric.table_name,
        filter_json=metric.filter_json,
        window_sec=metric.window_sec,
        threshold=metric.threshold,
        severity=metric.severity
    )
    
    return {
        "status": "success",
        "metric_id": metric_id,
        "message": f"Metric '{metric.name}' created successfully"
    }


@router.get("/metrics")
async def list_metrics():
    """Get all metric specs."""
    metrics = alert_engine.get_all_metrics()
    return {
        "status": "success",
        "count": len(metrics),
        "metrics": metrics
    }


@router.get("/metrics/{metric_id}")
async def get_metric(metric_id: int):
    """Get a specific metric by ID."""
    result = alert_engine.execute(
        "SELECT * FROM metric_specs WHERE metric_id = :metric_id",
        {"metric_id": metric_id}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
    
    return {
        "status": "success",
        "metric": result[0]
    }


@router.put("/metrics/{metric_id}")
async def update_metric(metric_id: int, metric: MetricUpdate):
    """Update a metric spec."""
    # Check if exists
    existing = alert_engine.execute(
        "SELECT metric_id FROM metric_specs WHERE metric_id = :metric_id",
        {"metric_id": metric_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
    
    # Build update dict
    updates = {}
    if metric.name is not None:
        updates["name"] = metric.name
    if metric.description is not None:
        updates["description"] = metric.description
    if metric.table_name is not None:
        updates["table_name"] = metric.table_name
    if metric.filter_json is not None:
        updates["filter_json"] = metric.filter_json
    if metric.window_sec is not None:
        updates["window_sec"] = metric.window_sec
    if metric.threshold is not None:
        updates["threshold"] = metric.threshold
    if metric.severity is not None:
        updates["severity"] = metric.severity
    
    if updates:
        alert_engine.update_metric(metric_id, **updates)
    
    return {
        "status": "success",
        "message": f"Metric {metric_id} updated"
    }


@router.delete("/metrics/{metric_id}")
async def delete_metric(metric_id: int):
    """Delete a metric spec."""
    # Check if exists
    existing = alert_engine.execute(
        "SELECT metric_id FROM metric_specs WHERE metric_id = :metric_id",
        {"metric_id": metric_id}
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail=f"Metric {metric_id} not found")
    
    alert_engine.delete_metric(metric_id)
    
    return {
        "status": "success",
        "message": f"Metric {metric_id} deleted"
    }


# ==================== ALERT ENDPOINTS ====================

@router.get("/active")
async def get_active_alerts():
    """Get all currently active alerts."""
    active = alert_engine.get_active_alerts()
    return {
        "status": "success",
        "count": len(active),
        "active_alerts": active
    }


@router.get("/history")
async def get_alert_history(limit: int = 50):
    """Get alert history (triggers and resolutions)."""
    history = alert_engine.get_alert_history(limit=limit)
    return {
        "status": "success",
        "count": len(history),
        "history": history
    }


# ==================== EVENT ENDPOINTS ====================

@router.post("/events")
async def create_event(event: EventCreate):
    """
    Push a new event to the events table.
    
    Example:
    ```json
    {
        "table_name": "login",
        "payload": {
            "user_id": 123,
            "status": "failed",
            "ip_address": "192.168.1.1"
        }
    }
    ```
    """
    event_id = alert_engine.insert_event(
        table_name=event.table_name,
        payload=event.payload
    )
    
    return {
        "status": "success",
        "event_id": event_id,
        "message": f"Event '{event.table_name}' created"
    }


@router.get("/events")
async def list_events(limit: int = 100, offset: int = 0):
    """Get recent events."""
    events = alert_engine.execute(
        "SELECT * FROM events ORDER BY id DESC LIMIT :limit OFFSET :offset",
        {"limit": limit, "offset": offset}
    )
    
    total = alert_engine.execute("SELECT COUNT(*) as count FROM events")
    
    return {
        "status": "success",
        "total": total[0]["count"] if total else 0,
        "count": len(events),
        "events": events
    }


# ==================== ENGINE CONTROL ====================

@router.get("/stats")
async def get_stats():
    """Get engine statistics."""
    stats = alert_engine.get_stats()
    return {
        "status": "success",
        "stats": stats
    }


@router.get("/redis/stats")
async def get_redis_stats():
    """Get Redis statistics for sliding windows."""
    stats = alert_engine.get_redis_stats()
    return {
        "status": "success",
        "redis": stats
    }


@router.post("/redis/clear")
async def clear_redis_windows():
    """Clear all metric window data from Redis."""
    alert_engine.clear_all_windows()
    return {
        "status": "success",
        "message": "All metric windows cleared"
    }


@router.post("/engine/start")
async def start_engine():
    """Start the alert engine in background."""
    status = alert_engine.get_engine_status()
    
    if status == "running":
        return {
            "status": "warning",
            "message": "Engine is already running"
        }
    
    alert_engine.start_background(tick_interval=1.0)
    
    return {
        "status": "success",
        "message": "Alert engine started"
    }


@router.post("/engine/stop")
async def stop_engine():
    """Stop the alert engine."""
    status = alert_engine.get_engine_status()
    
    if status == "stopped":
        return {
            "status": "warning",
            "message": "Engine is already stopped"
        }
    
    alert_engine.stop()
    
    return {
        "status": "success",
        "message": "Alert engine stopped"
    }


@router.get("/engine/status")
async def engine_status():
    """Get the current engine status."""
    status = alert_engine.get_engine_status()
    return {
        "status": "success",
        "engine_status": status
    }


# ==================== EVENT GENERATOR CONTROL ====================

@router.post("/generator/start")
async def start_generator(config: Optional[GeneratorConfig] = None):
    """
    Start the event generator to produce simulated events.
    
    The generator creates:
    - User registration events
    - Login events (success/failed)
    - Transaction events (success/failed)
    - KYC events (pending/approved/rejected)
    
    Optional config to customize intervals.
    """
    global _generator_running
    
    if _generator_running:
        return {
            "status": "warning",
            "message": "Event generator is already running"
        }
    
    # Use default or custom config
    if config is None:
        config = GeneratorConfig()
    
    event_generator.start_all(
        user_interval=config.user_interval,
        login_interval=(config.login_min_interval, config.login_max_interval),
        txn_interval=(config.txn_min_interval, config.txn_max_interval),
        kyc_interval=(config.kyc_min_interval, config.kyc_max_interval)
    )
    
    _generator_running = True
    
    return {
        "status": "success",
        "message": "Event generator started",
        "config": {
            "user_interval": config.user_interval,
            "login_interval": [config.login_min_interval, config.login_max_interval],
            "txn_interval": [config.txn_min_interval, config.txn_max_interval],
            "kyc_interval": [config.kyc_min_interval, config.kyc_max_interval]
        }
    }


@router.post("/generator/stop")
async def stop_generator():
    """Stop the event generator."""
    global _generator_running
    
    if not _generator_running:
        return {
            "status": "warning",
            "message": "Event generator is not running"
        }
    
    event_generator.stop_all()
    _generator_running = False
    
    return {
        "status": "success",
        "message": "Event generator stopped"
    }


@router.get("/generator/status")
async def generator_status():
    """Get the current event generator status."""
    global _generator_running
    
    return {
        "status": "success",
        "generator_running": _generator_running,
        "active_threads": len(event_generator._threads) if _generator_running else 0
    }


@router.post("/generator/burst")
async def generate_burst(request: BurstRequest):
    """
    Generate a burst of events for testing alerts.
    
    This is useful for quickly testing if alerts trigger correctly.
    
    Example:
    ```json
    {
        "event_type": "login",
        "count": 15,
        "status": "failed"
    }
    ```
    
    Supported event types:
    - login: status can be "success" or "failed" (default: "failed")
    - transaction: status can be "success" or "failed" (default: "failed")
    - kyc: generates rejection events (status ignored)
    """
    event_type = request.event_type.lower()
    count = request.count
    
    if event_type == "login":
        status = request.status or "failed"
        event_generator.generate_login_burst(count=count, status=status)
        return {
            "status": "success",
            "message": f"Generated {count} {status} login events",
            "event_type": "login",
            "count": count
        }
    
    elif event_type == "transaction":
        status = request.status or "failed"
        event_generator.generate_transaction_burst(count=count, status=status)
        return {
            "status": "success",
            "message": f"Generated {count} {status} transaction events",
            "event_type": "transaction",
            "count": count
        }
    
    elif event_type == "kyc":
        event_generator.generate_kyc_rejection_burst(count=count)
        return {
            "status": "success",
            "message": f"Generated {count} KYC rejection events",
            "event_type": "kyc",
            "count": count
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event type: {event_type}. Supported: login, transaction, kyc"
        )


# ==================== COMBINED CONTROL ====================

@router.post("/start-all")
async def start_all_services(config: Optional[GeneratorConfig] = None):
    """
    Start both the alert engine and event generator.
    
    This is a convenience endpoint to start the complete system.
    """
    global _generator_running
    
    results = {}
    
    # Start alert engine
    engine_status = alert_engine.get_engine_status()
    if engine_status != "running":
        alert_engine.start_background(tick_interval=1.0)
        results["engine"] = "started"
    else:
        results["engine"] = "already running"
    
    # Start generator
    if not _generator_running:
        if config is None:
            config = GeneratorConfig()
        
        event_generator.start_all(
            user_interval=config.user_interval,
            login_interval=(config.login_min_interval, config.login_max_interval),
            txn_interval=(config.txn_min_interval, config.txn_max_interval),
            kyc_interval=(config.kyc_min_interval, config.kyc_max_interval)
        )
        _generator_running = True
        results["generator"] = "started"
    else:
        results["generator"] = "already running"
    
    return {
        "status": "success",
        "message": "Services started",
        "results": results
    }


@router.post("/stop-all")
async def stop_all_services():
    """
    Stop both the alert engine and event generator.
    """
    global _generator_running
    
    results = {}
    
    # Stop generator first
    if _generator_running:
        event_generator.stop_all()
        _generator_running = False
        results["generator"] = "stopped"
    else:
        results["generator"] = "not running"
    
    # Stop engine
    engine_status = alert_engine.get_engine_status()
    if engine_status == "running":
        alert_engine.stop()
        results["engine"] = "stopped"
    else:
        results["engine"] = "not running"
    
    return {
        "status": "success",
        "message": "Services stopped",
        "results": results
    }


@router.get("/status-all")
async def get_all_status():
    """
    Get status of both the alert engine and event generator.
    """
    global _generator_running
    
    stats = alert_engine.get_stats()
    
    return {
        "status": "success",
        "engine": {
            "status": stats["engine_status"],
            "last_processed_id": stats["last_processed_id"],
            "total_events": stats["total_events"],
            "active_alerts": stats["active_alerts"],
            "total_alerts_triggered": stats["total_alerts_triggered"]
        },
        "generator": {
            "running": _generator_running,
            "active_threads": len(event_generator._threads) if _generator_running else 0
        }
    }
