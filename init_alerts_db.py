#!/usr/bin/env python3
"""
Initialize the Alerts Engine Database
=====================================
Creates the derivinsight_alerts.db database with proper schema and sample data.

Usage:
    python init_alerts_db.py           # Initialize database
    python init_alerts_db.py --demo    # Initialize and run demo
    python init_alerts_db.py --reset   # Drop and recreate database
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.alert_engine import AlertEngineService, ALERTS_DB_PATH


def init_database(reset: bool = False):
    """Initialize the alerts database."""
    
    # Check if database already exists
    if os.path.exists(ALERTS_DB_PATH):
        if reset:
            print(f"[Init] Removing existing database: {ALERTS_DB_PATH}")
            os.remove(ALERTS_DB_PATH)
        else:
            print(f"[Init] Database already exists: {ALERTS_DB_PATH}")
            print("[Init] Use --reset to recreate")
            return True
    
    # Create alert engine and initialize
    engine = AlertEngineService()
    
    schema_path = os.path.join(os.path.dirname(__file__), "app", "files", "alerts_schema.sql")
    
    if not os.path.exists(schema_path):
        print(f"[Init] ERROR: Schema file not found: {schema_path}")
        return False
    
    print(f"[Init] Creating database: {ALERTS_DB_PATH}")
    print(f"[Init] Using schema: {schema_path}")
    
    success = engine.initialize_db(schema_path)
    
    if success:
        print("[Init] Database created successfully!")
        
        # Show stats
        stats = engine.get_stats()
        print(f"\n[Init] Database Stats:")
        print(f"  - Total metrics: {stats['total_metrics']}")
        print(f"  - Total events: {stats['total_events']}")
        print(f"  - Engine status: {stats['engine_status']}")
        
        # Show sample metrics
        metrics = engine.get_all_metrics()
        print(f"\n[Init] Sample Metric Specs (Alert Definitions):")
        for m in metrics:
            print(f"  [{m['metric_id']}] {m['name']}")
            print(f"      Table: {m['table_name']} | Filter: {m['filter_json']}")
            print(f"      Window: {m['window_sec']}s | Threshold: {m['threshold']} | Severity: {m.get('severity', 'medium')}")
        
        return True
    else:
        print("[Init] ERROR: Database initialization failed!")
        return False


def run_demo():
    """Run a quick demo of the alert engine."""
    from app.services.alert_engine import AlertEngineService
    from app.services.alert_events_generate import EventGenerator
    import time
    
    print("\n" + "="*60)
    print("ALERT ENGINE DEMO")
    print("="*60 + "\n")
    
    engine = AlertEngineService()
    generator = EventGenerator()
    
    # Start the alert engine in background
    print("[Demo] Starting alert engine...")
    engine.start_background(tick_interval=0.5)
    time.sleep(1)
    
    # Generate some normal events
    print("[Demo] Generating normal events...")
    for i in range(5):
        generator.write_event("login", {"user_id": i, "status": "success"})
        generator.write_event("transaction", {"user_id": i, "amount": 100, "status": "success"})
        time.sleep(0.2)
    
    time.sleep(2)
    
    # Generate a burst of failed logins to trigger alert
    print("\n[Demo] Generating burst of failed logins to trigger alert...")
    generator.generate_login_burst(count=15, status="failed")
    
    time.sleep(3)
    
    # Show stats
    stats = engine.get_stats()
    print(f"\n[Demo] Stats after burst:")
    print(f"  - Total events: {stats['total_events']}")
    print(f"  - Active alerts: {stats['active_alerts']}")
    print(f"  - Total triggered: {stats['total_alerts_triggered']}")
    
    # Show alert history
    history = engine.get_alert_history(limit=5)
    if history:
        print(f"\n[Demo] Recent Alert History:")
        for h in history:
            print(f"  [{h['action'].upper()}] {h.get('metric_name', h['metric_id'])}")
            print(f"      Count: {h['event_count']} | Threshold: {h['threshold']}")
            print(f"      Time: {h['created_at']}")
    
    # Stop engine
    engine.stop()
    
    print("\n[Demo] Demo completed!")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    args = sys.argv[1:]
    
    reset = "--reset" in args
    demo = "--demo" in args
    
    success = init_database(reset=reset)
    
    if success and demo:
        run_demo()


if __name__ == "__main__":
    main()
