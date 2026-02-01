-- =============================================
-- DerivInsight Alerts Engine Database Schema
-- =============================================

-- Events table: stores all incoming events from various sources
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,           -- source table/event type (e.g., 'login', 'transaction', 'kyc')
    payload_json TEXT NOT NULL,         -- JSON payload containing event data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT 0         -- flag to track if event has been processed
);

-- Index for efficient event fetching
CREATE INDEX IF NOT EXISTS idx_events_id ON events(id);
CREATE INDEX IF NOT EXISTS idx_events_table_name ON events(table_name);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);

-- Metric Specs table (alerts configuration)
-- Defines what conditions trigger alerts
CREATE TABLE IF NOT EXISTS metric_specs (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                 -- human-readable metric name
    description TEXT,                   -- description of what this metric tracks
    table_name TEXT NOT NULL,           -- which event type this metric applies to
    filter_json TEXT,                   -- JSON filter conditions (e.g., {"status": "failed"})
    window_sec INTEGER NOT NULL,        -- sliding window duration in seconds
    threshold INTEGER NOT NULL,         -- count threshold to trigger alert
    is_active BOOLEAN DEFAULT 0,        -- whether alert is currently triggered
    severity TEXT DEFAULT 'medium',     -- alert severity: low, medium, high, critical
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metric_specs_table_name ON metric_specs(table_name);
CREATE INDEX IF NOT EXISTS idx_metric_specs_is_active ON metric_specs(is_active);

-- Alert History table: logs all alert triggers and resolutions
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL,
    action TEXT NOT NULL,               -- 'triggered' or 'resolved'
    event_count INTEGER NOT NULL,       -- count at the time of action
    threshold INTEGER NOT NULL,         -- threshold at the time of action
    message TEXT,                       -- alert message
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES metric_specs(metric_id)
);

CREATE INDEX IF NOT EXISTS idx_alert_history_metric_id ON alert_history(metric_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_created_at ON alert_history(created_at);

-- Metric Windows table: stores event timestamps for sliding window calculations
-- This replaces Redis ZSET for SQLite-based implementation
CREATE TABLE IF NOT EXISTS metric_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id INTEGER NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (metric_id) REFERENCES metric_specs(metric_id)
);

CREATE INDEX IF NOT EXISTS idx_metric_windows_metric_id ON metric_windows(metric_id);
CREATE INDEX IF NOT EXISTS idx_metric_windows_event_timestamp ON metric_windows(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_metric_windows_composite ON metric_windows(metric_id, event_timestamp);

-- Engine State table: tracks processing state
CREATE TABLE IF NOT EXISTS engine_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Insert default metric specs (sample alerts)
-- =============================================

-- Alert: Too many failed logins in 5 minutes
INSERT OR IGNORE INTO metric_specs (metric_id, name, description, table_name, filter_json, window_sec, threshold, severity)
VALUES (1, 'Failed Login Spike', 'Triggers when failed login attempts exceed threshold in time window', 
        'login', '{"status": "failed"}', 300, 10, 'high');

-- Alert: Too many failed transactions in 2 minutes
INSERT OR IGNORE INTO metric_specs (metric_id, name, description, table_name, filter_json, window_sec, threshold, severity)
VALUES (2, 'Failed Transaction Spike', 'Triggers when failed transactions exceed threshold', 
        'transaction', '{"status": "failed"}', 120, 5, 'critical');

-- Alert: High volume of KYC rejections in 10 minutes
INSERT OR IGNORE INTO metric_specs (metric_id, name, description, table_name, filter_json, window_sec, threshold, severity)
VALUES (3, 'KYC Rejection Spike', 'Triggers when KYC rejections exceed threshold', 
        'kyc', '{"kyc_status": "rejected"}', 600, 3, 'medium');

-- Alert: High transaction volume (any status) in 1 minute
INSERT OR IGNORE INTO metric_specs (metric_id, name, description, table_name, filter_json, window_sec, threshold, severity)
VALUES (4, 'Transaction Volume Spike', 'Triggers when total transaction volume is high', 
        'transaction', '{}', 60, 20, 'low');

-- Alert: New user registration spike in 30 minutes
INSERT OR IGNORE INTO metric_specs (metric_id, name, description, table_name, filter_json, window_sec, threshold, severity)
VALUES (5, 'User Registration Spike', 'Triggers when new user registrations spike', 
        'user', '{}', 1800, 50, 'low');

-- Initialize engine state
INSERT OR IGNORE INTO engine_state (key, value) VALUES ('last_processed_id', '0');
INSERT OR IGNORE INTO engine_state (key, value) VALUES ('engine_status', 'stopped');
