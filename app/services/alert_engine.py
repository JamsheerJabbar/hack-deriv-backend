"""
Alert Engine Service
====================
Core alert processing engine that follows the architecture:
- Fetch new events from the events table
- For each event, find matching metrics and update sliding windows (Redis)
- Evaluate alerts and trigger/resolve as needed
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text
from threading import Thread, Event
import redis

from app.core.config import settings

# Database path for alerts
ALERTS_DB_PATH = "derivinsight_alerts.db"
ALERTS_DB_URL = f"sqlite:///./{ALERTS_DB_PATH}"


class AlertEngineService:
    """
    Alert Engine that processes events and evaluates alerts.
    
    Architecture:
    - events table (SQLite): stores incoming events (id, table_name, payload_json, created_at)
    - metric_specs table (SQLite): defines alert conditions (metric_id, table_name, filter_json, window_sec, threshold, is_active)
    - Redis ZSET: stores event timestamps for sliding window calculations (replaces metric_windows table)
    - alert_history table (SQLite): logs alert triggers and resolutions
    - engine_state table (SQLite): tracks last_processed_id
    
    Redis Key Pattern:
    - metric:{metric_id} -> ZSET with event timestamps as score and value
    """
    
    def __init__(self, db_url: str = None, redis_url: str = None):
        # SQLite for persistent data
        self.db_url = db_url or ALERTS_DB_URL
        self.engine = create_engine(self.db_url)
        
        # Redis for sliding window data
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis_client: Optional[redis.Redis] = None
        self._redis_available = False
        
        self._stop_event = Event()
        self._engine_thread: Optional[Thread] = None
        
        # Initialize Redis connection
        self._init_redis()
        
        print(f"[AlertEngine] Initialized with database: {self.db_url}")
        print(f"[AlertEngine] Redis: {'connected' if self._redis_available else 'not available (using fallback)'}")
    
    def _init_redis(self):
        """Initialize Redis connection."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self._redis_client.ping()
            self._redis_available = True
            print(f"[AlertEngine] Connected to Redis: {self.redis_url}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"[AlertEngine] Redis connection failed: {e}")
            print("[AlertEngine] Falling back to SQLite for metric windows")
            self._redis_available = False
            self._redis_client = None
    
    @property
    def redis(self) -> Optional[redis.Redis]:
        """Get Redis client, attempt reconnect if disconnected."""
        if self._redis_client is None:
            self._init_redis()
        return self._redis_client
    
    # ==================== DATABASE HELPERS ====================
    
    def execute(self, sql: str, params: dict = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(sql), params)
                else:
                    result = conn.execute(text(sql))
                
                if result.returns_rows:
                    return [dict(row) for row in result.mappings()]
                else:
                    conn.commit()
                    return [{"rows_affected": result.rowcount}]
        except Exception as e:
            print(f"[AlertEngine] Database error: {e}")
            return []
    
    def initialize_db(self, schema_path: str = None):
        """Initialize the alerts database with schema."""
        if schema_path is None:
            schema_path = os.path.join(os.path.dirname(__file__), "..", "files", "alerts_schema.sql")
        
        if not os.path.exists(schema_path):
            print(f"[AlertEngine] Schema file not found: {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            sql_content = f.read()
        
        statements = sql_content.split(';')
        
        with self.engine.connect() as conn:
            for statement in statements:
                if statement.strip():
                    try:
                        conn.execute(text(statement))
                    except Exception as e:
                        print(f"[AlertEngine] Schema error: {e}")
            conn.commit()
        
        print("[AlertEngine] Database initialized successfully")
        return True
    
    # ==================== EVENT OPERATIONS ====================
    
    def insert_event(self, table_name: str, payload: dict) -> int:
        """Insert a new event into the events table."""
        payload_json = json.dumps(payload)
        sql = """
            INSERT INTO events (table_name, payload_json, created_at, processed)
            VALUES (:table_name, :payload_json, :created_at, 0)
        """
        self.execute(sql, {
            "table_name": table_name,
            "payload_json": payload_json,
            "created_at": datetime.utcnow().isoformat()
        })
        
        # Get the last inserted ID
        result = self.execute("SELECT last_insert_rowid() as id")
        event_id = result[0]["id"] if result else 0
        print(f"[Event] Inserted: {table_name} (id={event_id})")
        return event_id
    
    def fetch_new_events(self, last_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch new events after the last processed ID."""
        sql = """
            SELECT id, table_name, payload_json, created_at
            FROM events
            WHERE id > :last_id
            ORDER BY id ASC
            LIMIT :limit
        """
        return self.execute(sql, {"last_id": last_id, "limit": limit})
    
    # ==================== METRIC OPERATIONS ====================
    
    def get_metrics_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all metric specs that apply to a given table/event type."""
        sql = """
            SELECT metric_id, name, table_name, filter_json, window_sec, threshold, is_active, severity
            FROM metric_specs
            WHERE table_name = :table_name
        """
        return self.execute(sql, {"table_name": table_name})
    
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get all metric specs."""
        sql = "SELECT * FROM metric_specs"
        return self.execute(sql)
    
    def create_metric(self, name: str, description: str, table_name: str, 
                      filter_json: dict, window_sec: int, threshold: int, 
                      severity: str = "medium") -> int:
        """Create a new metric spec (alert definition)."""
        sql = """
            INSERT INTO metric_specs (name, description, table_name, filter_json, window_sec, threshold, severity)
            VALUES (:name, :description, :table_name, :filter_json, :window_sec, :threshold, :severity)
        """
        self.execute(sql, {
            "name": name,
            "description": description,
            "table_name": table_name,
            "filter_json": json.dumps(filter_json),
            "window_sec": window_sec,
            "threshold": threshold,
            "severity": severity
        })
        
        result = self.execute("SELECT last_insert_rowid() as id")
        metric_id = result[0]["id"] if result else 0
        print(f"[Metric] Created: {name} (id={metric_id})")
        return metric_id
    
    def update_metric(self, metric_id: int, **kwargs) -> bool:
        """Update a metric spec."""
        allowed_fields = ["name", "description", "table_name", "filter_json", "window_sec", "threshold", "severity"]
        updates = []
        params = {"metric_id": metric_id}
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                if field == "filter_json" and isinstance(value, dict):
                    value = json.dumps(value)
                updates.append(f"{field} = :{field}")
                params[field] = value
        
        if not updates:
            return False
        
        updates.append("updated_at = :updated_at")
        params["updated_at"] = datetime.utcnow().isoformat()
        
        sql = f"UPDATE metric_specs SET {', '.join(updates)} WHERE metric_id = :metric_id"
        self.execute(sql, params)
        print(f"[Metric] Updated: metric_id={metric_id}")
        return True
    
    def delete_metric(self, metric_id: int) -> bool:
        """Delete a metric spec and its window data."""
        # Clear Redis window data
        if self._redis_available and self.redis:
            try:
                self.redis.delete(self._get_metric_key(metric_id))
            except redis.RedisError as e:
                print(f"[AlertEngine] Redis error deleting metric window: {e}")
        
        # Fallback: also delete from SQLite if table exists
        self.execute("DELETE FROM metric_windows WHERE metric_id = :metric_id", {"metric_id": metric_id})
        self.execute("DELETE FROM metric_specs WHERE metric_id = :metric_id", {"metric_id": metric_id})
        print(f"[Metric] Deleted: metric_id={metric_id}")
        return True
    
    # ==================== FILTER MATCHING ====================
    
    def matches_filter(self, payload: dict, filter_json: str) -> bool:
        """
        Check if event payload matches the metric filter.
        
        Filter examples:
        - '{}' or '' -> matches everything
        - '{"status": "failed"}' -> matches if payload["status"] == "failed"
        - '{"status": "failed", "amount_gt": 1000}' -> compound conditions
        """
        if not filter_json or filter_json == '{}':
            return True
        
        try:
            filter_dict = json.loads(filter_json) if isinstance(filter_json, str) else filter_json
        except json.JSONDecodeError:
            return True
        
        if not filter_dict:
            return True
        
        for key, expected_value in filter_dict.items():
            # Handle special operators
            if key.endswith("_gt"):
                actual_key = key[:-3]
                if actual_key not in payload or payload[actual_key] <= expected_value:
                    return False
            elif key.endswith("_lt"):
                actual_key = key[:-3]
                if actual_key not in payload or payload[actual_key] >= expected_value:
                    return False
            elif key.endswith("_gte"):
                actual_key = key[:-4]
                if actual_key not in payload or payload[actual_key] < expected_value:
                    return False
            elif key.endswith("_lte"):
                actual_key = key[:-4]
                if actual_key not in payload or payload[actual_key] > expected_value:
                    return False
            elif key.endswith("_in"):
                actual_key = key[:-3]
                if actual_key not in payload or payload[actual_key] not in expected_value:
                    return False
            else:
                # Exact match
                if key not in payload or payload[key] != expected_value:
                    return False
        
        return True
    
    # ==================== REDIS SLIDING WINDOW OPERATIONS ====================
    
    def _get_metric_key(self, metric_id: int) -> str:
        """Get Redis key for a metric's sliding window."""
        return f"metric:{metric_id}"
    
    def update_metric_window(self, metric_id: int, event_timestamp: str, window_sec: int):
        """
        Update the sliding window for a metric using Redis ZSET.
        
        Redis operations:
        - ZADD: Add event timestamp (score = unix timestamp, member = unique id)
        - ZREMRANGEBYSCORE: Remove events outside the window
        """
        if self._redis_available and self.redis:
            try:
                self._update_metric_window_redis(metric_id, event_timestamp, window_sec)
                return
            except redis.RedisError as e:
                print(f"[AlertEngine] Redis error, falling back to SQLite: {e}")
                self._redis_available = False
        
        # Fallback to SQLite
        self._update_metric_window_sqlite(metric_id, event_timestamp, window_sec)
    
    def _update_metric_window_redis(self, metric_id: int, event_timestamp: str, window_sec: int):
        """Update sliding window using Redis."""
        key = self._get_metric_key(metric_id)
        
        # Convert timestamp to unix timestamp for scoring
        try:
            if isinstance(event_timestamp, str):
                dt = datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
            else:
                dt = event_timestamp
            timestamp_score = dt.timestamp()
        except:
            timestamp_score = time.time()
        
        # Create unique member (timestamp + random suffix to allow duplicates)
        member = f"{timestamp_score}:{time.time_ns()}"
        
        # Add to sorted set (ZADD)
        self.redis.zadd(key, {member: timestamp_score})
        
        # Remove old entries outside the window (ZREMRANGEBYSCORE)
        window_start = time.time() - window_sec
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Set TTL on key to auto-expire (window_sec + buffer)
        self.redis.expire(key, window_sec + 60)
    
    def _update_metric_window_sqlite(self, metric_id: int, event_timestamp: str, window_sec: int):
        """Fallback: Update sliding window using SQLite."""
        # Add new timestamp
        sql = """
            INSERT INTO metric_windows (metric_id, event_timestamp)
            VALUES (:metric_id, :event_timestamp)
        """
        self.execute(sql, {"metric_id": metric_id, "event_timestamp": event_timestamp})
        
        # Remove old timestamps outside the window
        window_start = (datetime.utcnow() - timedelta(seconds=window_sec)).isoformat()
        sql = """
            DELETE FROM metric_windows
            WHERE metric_id = :metric_id AND event_timestamp < :window_start
        """
        self.execute(sql, {"metric_id": metric_id, "window_start": window_start})
    
    def get_window_count(self, metric_id: int, window_sec: int) -> int:
        """
        Get the count of events in the current window for a metric.
        
        Redis: ZCOUNT or ZCARD after cleanup
        """
        if self._redis_available and self.redis:
            try:
                return self._get_window_count_redis(metric_id, window_sec)
            except redis.RedisError as e:
                print(f"[AlertEngine] Redis error, falling back to SQLite: {e}")
                self._redis_available = False
        
        # Fallback to SQLite
        return self._get_window_count_sqlite(metric_id, window_sec)
    
    def _get_window_count_redis(self, metric_id: int, window_sec: int) -> int:
        """Get window count using Redis."""
        key = self._get_metric_key(metric_id)
        
        # Get current time and window start
        now = time.time()
        window_start = now - window_sec
        
        # Count entries within the window (ZCOUNT)
        count = self.redis.zcount(key, window_start, now)
        return count
    
    def _get_window_count_sqlite(self, metric_id: int, window_sec: int) -> int:
        """Fallback: Get window count using SQLite."""
        window_start = (datetime.utcnow() - timedelta(seconds=window_sec)).isoformat()
        sql = """
            SELECT COUNT(*) as count
            FROM metric_windows
            WHERE metric_id = :metric_id AND event_timestamp >= :window_start
        """
        result = self.execute(sql, {"metric_id": metric_id, "window_start": window_start})
        return result[0]["count"] if result else 0
    
    def clear_metric_window(self, metric_id: int):
        """Clear all window data for a metric."""
        if self._redis_available and self.redis:
            try:
                self.redis.delete(self._get_metric_key(metric_id))
            except redis.RedisError:
                pass
        
        # Also clear SQLite fallback
        self.execute("DELETE FROM metric_windows WHERE metric_id = :metric_id", {"metric_id": metric_id})
    
    def clear_all_windows(self):
        """Clear all metric window data from Redis."""
        if self._redis_available and self.redis:
            try:
                # Find all metric keys
                keys = self.redis.keys("metric:*")
                if keys:
                    self.redis.delete(*keys)
                print(f"[AlertEngine] Cleared {len(keys)} metric windows from Redis")
            except redis.RedisError as e:
                print(f"[AlertEngine] Redis error clearing windows: {e}")
        
        # Also clear SQLite fallback
        self.execute("DELETE FROM metric_windows")
    
    # ==================== ALERT EVALUATION ====================
    
    def evaluate_alert(self, metric: Dict[str, Any]):
        """
        Evaluate if an alert should be triggered or resolved.
        
        - If count > threshold AND not active -> trigger alert
        - If count <= threshold AND active -> resolve alert
        """
        metric_id = metric["metric_id"]
        threshold = metric["threshold"]
        is_active = metric["is_active"]
        window_sec = metric["window_sec"]
        
        count = self.get_window_count(metric_id, window_sec)
        
        if count > threshold and not is_active:
            self._trigger_alert(metric, count)
        elif count <= threshold and is_active:
            self._resolve_alert(metric, count)
    
    def _trigger_alert(self, metric: Dict[str, Any], count: int):
        """Trigger an alert."""
        metric_id = metric["metric_id"]
        message = f"🚨 ALERT TRIGGERED: {metric['name']} - Count {count} exceeds threshold {metric['threshold']}"
        
        # Log to alert history
        sql = """
            INSERT INTO alert_history (metric_id, action, event_count, threshold, message)
            VALUES (:metric_id, 'triggered', :count, :threshold, :message)
        """
        self.execute(sql, {
            "metric_id": metric_id,
            "count": count,
            "threshold": metric["threshold"],
            "message": message
        })
        
        # Mark metric as active
        self.execute("UPDATE metric_specs SET is_active = 1 WHERE metric_id = :metric_id", {"metric_id": metric_id})
        
        print(f"\n{message}")
        print(f"   Severity: {metric.get('severity', 'medium').upper()}")
        print(f"   Window: {metric['window_sec']}s | Table: {metric['table_name']}\n")
    
    def _resolve_alert(self, metric: Dict[str, Any], count: int):
        """Resolve an active alert."""
        metric_id = metric["metric_id"]
        message = f"✅ ALERT RESOLVED: {metric['name']} - Count {count} now below threshold {metric['threshold']}"
        
        # Log to alert history
        sql = """
            INSERT INTO alert_history (metric_id, action, event_count, threshold, message)
            VALUES (:metric_id, 'resolved', :count, :threshold, :message)
        """
        self.execute(sql, {
            "metric_id": metric_id,
            "count": count,
            "threshold": metric["threshold"],
            "message": message
        })
        
        # Mark metric as inactive
        self.execute("UPDATE metric_specs SET is_active = 0 WHERE metric_id = :metric_id", {"metric_id": metric_id})
        
        print(f"\n{message}\n")
    
    # ==================== ENGINE STATE ====================
    
    def get_last_processed_id(self) -> int:
        """Get the last processed event ID."""
        result = self.execute("SELECT value FROM engine_state WHERE key = 'last_processed_id'")
        return int(result[0]["value"]) if result else 0
    
    def save_last_processed_id(self, event_id: int):
        """Save the last processed event ID."""
        sql = """
            INSERT OR REPLACE INTO engine_state (key, value, updated_at)
            VALUES ('last_processed_id', :value, :updated_at)
        """
        self.execute(sql, {"value": str(event_id), "updated_at": datetime.utcnow().isoformat()})
    
    def set_engine_status(self, status: str):
        """Set the engine status (running/stopped)."""
        sql = """
            INSERT OR REPLACE INTO engine_state (key, value, updated_at)
            VALUES ('engine_status', :status, :updated_at)
        """
        self.execute(sql, {"status": status, "updated_at": datetime.utcnow().isoformat()})
    
    def get_engine_status(self) -> str:
        """Get the current engine status."""
        result = self.execute("SELECT value FROM engine_state WHERE key = 'engine_status'")
        return result[0]["value"] if result else "stopped"
    
    # ==================== CORE EVENT PROCESSING ====================
    
    def process_event(self, event: Dict[str, Any]):
        """
        Process a single event:
        1. Load metrics for this table
        2. Check filter condition for each metric
        3. Update sliding window if filter matches (Redis)
        4. Evaluate alert
        """
        table_name = event["table_name"]
        
        try:
            payload = json.loads(event["payload_json"]) if isinstance(event["payload_json"], str) else event["payload_json"]
        except json.JSONDecodeError:
            payload = {}
        
        event_timestamp = event.get("created_at", datetime.utcnow().isoformat())
        
        # Get metrics for this table
        metrics = self.get_metrics_for_table(table_name)
        
        for metric in metrics:
            # Check if event matches the filter
            if self.matches_filter(payload, metric.get("filter_json", "{}")):
                # Update sliding window (Redis)
                self.update_metric_window(metric["metric_id"], event_timestamp, metric["window_sec"])
                
                # Evaluate alert
                self.evaluate_alert(metric)
    
    # ==================== MAIN ENGINE LOOP ====================
    
    def run_engine(self, tick_interval: float = 1.0):
        """
        Main engine loop (blocking).
        Continuously fetches and processes new events.
        """
        print("[AlertEngine] Starting engine...")
        self.set_engine_status("running")
        last_processed_id = self.get_last_processed_id()
        
        print(f"[AlertEngine] Resuming from event ID: {last_processed_id}")
        
        while not self._stop_event.is_set():
            try:
                events = self.fetch_new_events(last_processed_id)
                
                for event in events:
                    self.process_event(event)
                    last_processed_id = event["id"]
                
                if events:
                    self.save_last_processed_id(last_processed_id)
                    print(f"[AlertEngine] Processed {len(events)} events. Last ID: {last_processed_id}")
                
                time.sleep(tick_interval)
                
            except Exception as e:
                print(f"[AlertEngine] Error in main loop: {e}")
                time.sleep(tick_interval)
        
        self.set_engine_status("stopped")
        print("[AlertEngine] Engine stopped.")
    
    def start_background(self, tick_interval: float = 1.0):
        """Start the engine in a background thread."""
        if self._engine_thread and self._engine_thread.is_alive():
            print("[AlertEngine] Engine already running")
            return
        
        self._stop_event.clear()
        self._engine_thread = Thread(target=self.run_engine, args=(tick_interval,), daemon=True)
        self._engine_thread.start()
        print("[AlertEngine] Engine started in background")
    
    def stop(self):
        """Stop the engine."""
        print("[AlertEngine] Stopping engine...")
        self._stop_event.set()
        if self._engine_thread:
            self._engine_thread.join(timeout=5.0)
    
    # ==================== ALERT HISTORY ====================
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alert history."""
        sql = """
            SELECT ah.*, ms.name as metric_name, ms.table_name, ms.severity
            FROM alert_history ah
            JOIN metric_specs ms ON ah.metric_id = ms.metric_id
            ORDER BY ah.created_at DESC
            LIMIT :limit
        """
        return self.execute(sql, {"limit": limit})
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all currently active alerts."""
        sql = """
            SELECT metric_id, name, table_name, filter_json, window_sec, threshold, severity
            FROM metric_specs
            WHERE is_active = 1
        """
        return self.execute(sql)
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        total_events = self.execute("SELECT COUNT(*) as count FROM events")
        total_metrics = self.execute("SELECT COUNT(*) as count FROM metric_specs")
        active_alerts = self.execute("SELECT COUNT(*) as count FROM metric_specs WHERE is_active = 1")
        total_triggered = self.execute("SELECT COUNT(*) as count FROM alert_history WHERE action = 'triggered'")
        
        return {
            "total_events": total_events[0]["count"] if total_events else 0,
            "total_metrics": total_metrics[0]["count"] if total_metrics else 0,
            "active_alerts": active_alerts[0]["count"] if active_alerts else 0,
            "total_alerts_triggered": total_triggered[0]["count"] if total_triggered else 0,
            "last_processed_id": self.get_last_processed_id(),
            "engine_status": self.get_engine_status(),
            "redis_available": self._redis_available
        }
    
    def get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis-specific statistics."""
        if not self._redis_available or not self.redis:
            return {"available": False, "message": "Redis not connected"}
        
        try:
            # Get all metric keys
            keys = self.redis.keys("metric:*")
            
            window_stats = {}
            for key in keys:
                metric_id = key.split(":")[1]
                count = self.redis.zcard(key)
                ttl = self.redis.ttl(key)
                window_stats[f"metric_{metric_id}"] = {
                    "count": count,
                    "ttl": ttl
                }
            
            return {
                "available": True,
                "total_metric_keys": len(keys),
                "windows": window_stats
            }
        except redis.RedisError as e:
            return {"available": False, "error": str(e)}


# Singleton instance
alert_engine = AlertEngineService()
