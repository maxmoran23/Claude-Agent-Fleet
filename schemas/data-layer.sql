-- ============================================================================
-- Claude Agent Fleet — Data Layer Schema
--
-- Append-only SQLite schema serving as the fleet's permanent historical record.
-- Canvases hold live state (overwritten each run). This database holds history
-- (nothing is ever updated or deleted).
--
-- Design principles:
--   - Every row captures a point-in-time observation with a timestamp
--   - No UPDATE or DELETE operations (append-only)
--   - Foreign keys kept soft (agent_name as string) for resilience
--   - All timestamps in ISO 8601 UTC
--   - Schema intentionally Postgres-compatible for future migration
--
-- Tables:
--   agent_runs              — universal run log, one row per agent run
--   fleet_metrics           — fleet-level aggregates (throttle level, budget state)
--   market_snapshots        — price, sentiment, regime captures
--   predictions             — agent-produced forecasts with outcome tracking
--   quant_signals           — quantitative signal detections (generic research)
--   portfolio_snapshots     — virtual portfolio state captures
--   regulatory_events       — surfaced regulatory developments
--   onchain_events          — surfaced on-chain monitoring events
--   defi_protocol_state     — protocol TVL, yield, governance state captures
--   opportunity_pipeline    — opportunities surfaced across agents
--   execution_outcomes      — action-package reactions and outcomes
--   upgrade_experiments     — agent-evolution experiments and their outcomes
--   attention_audit         — operator engagement metrics per agent
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Universal run log — every agent writes one row per run
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name          TEXT NOT NULL,
    run_timestamp       TEXT NOT NULL,           -- ISO 8601 UTC
    quality_score       INTEGER,                 -- 1-10, NULL if run aborted
    sources_used        TEXT,                    -- comma-separated
    fallbacks_triggered INTEGER DEFAULT 0,
    findings_count      INTEGER DEFAULT 0,
    severity_critical   INTEGER DEFAULT 0,
    severity_high       INTEGER DEFAULT 0,
    severity_medium     INTEGER DEFAULT 0,
    runtime_seconds     INTEGER,
    status              TEXT,                    -- completed | degraded | failed
    notes               TEXT                     -- optional free-form
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent     ON agent_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_runs_timestamp ON agent_runs(run_timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_runs_quality   ON agent_runs(quality_score);

-- ----------------------------------------------------------------------------
-- Fleet-level metrics — one row per watchdog run
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fleet_metrics (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_timestamp         TEXT NOT NULL,
    agents_configured          INTEGER,
    agents_healthy             INTEGER,
    agents_degraded            INTEGER,
    agents_failed              INTEGER,
    current_throttle_level     TEXT,             -- NORMAL | GREEN | YELLOW | RED
    weekly_run_count           INTEGER,
    weekly_budget_target       INTEGER,
    projected_weekly_runs      INTEGER,
    projection_ratio           REAL,
    avg_quality_last_24h       REAL,
    avg_quality_last_7d        REAL
);

CREATE INDEX IF NOT EXISTS idx_fleet_metrics_timestamp ON fleet_metrics(snapshot_timestamp);

-- ----------------------------------------------------------------------------
-- Market snapshots — captured by market monitor / market pulse agents
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_snapshots (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name            TEXT NOT NULL,
    snapshot_timestamp    TEXT NOT NULL,
    btc_usd               REAL,
    eth_usd               REAL,
    sol_usd               REAL,
    total_market_cap_usd  REAL,
    fear_greed_index      INTEGER,
    dominant_narrative    TEXT,
    market_regime         TEXT,                  -- risk-on | risk-off | neutral | event | uncertain
    volatility_regime     TEXT,                  -- quiet | active | charged | event
    data_source           TEXT,
    data_freshness_seconds INTEGER               -- how stale was the price data
);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_timestamp ON market_snapshots(snapshot_timestamp);

-- ----------------------------------------------------------------------------
-- Predictions — agent-produced forecasts, optionally linked to outcomes later
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name           TEXT NOT NULL,
    prediction_timestamp TEXT NOT NULL,
    topic                TEXT NOT NULL,
    prediction_text      TEXT NOT NULL,
    confidence           REAL,                   -- 0.0 to 1.0
    resolution_date      TEXT,                   -- when we'll know if it was right
    outcome              TEXT,                   -- correct | incorrect | ambiguous | pending
    outcome_noted_at     TEXT,                   -- when outcome was recorded
    outcome_notes        TEXT
);

CREATE INDEX IF NOT EXISTS idx_predictions_agent     ON predictions(agent_name);
CREATE INDEX IF NOT EXISTS idx_predictions_outcome   ON predictions(outcome);
CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(prediction_timestamp);

-- ----------------------------------------------------------------------------
-- Quantitative signals — generic quant/statistical signal detections
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quant_signals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name          TEXT NOT NULL,
    detection_timestamp TEXT NOT NULL,
    signal_name         TEXT NOT NULL,
    domain              TEXT,                    -- market | protocol | sector | custom
    signal_strength     REAL,
    supporting_data     TEXT,                    -- JSON-encoded supporting metrics
    outcome_window_days INTEGER,
    outcome_status      TEXT                     -- pending | confirmed | invalidated
);

CREATE INDEX IF NOT EXISTS idx_quant_signals_timestamp ON quant_signals(detection_timestamp);

-- ----------------------------------------------------------------------------
-- Portfolio snapshots — captured by virtual portfolio agents
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name          TEXT NOT NULL,
    snapshot_timestamp  TEXT NOT NULL,
    total_value_usd     REAL,
    cash_usd            REAL,
    positions_json      TEXT,                    -- JSON array of {symbol, qty, avg_price, current_price}
    pnl_24h             REAL,
    pnl_7d              REAL,
    pnl_since_inception REAL,
    trade_count_24h     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_timestamp ON portfolio_snapshots(snapshot_timestamp);

-- ----------------------------------------------------------------------------
-- Regulatory events — surfaced by regulatory oracle
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS regulatory_events (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name         TEXT NOT NULL,
    event_date         TEXT NOT NULL,
    detected_at        TEXT NOT NULL,           -- when the agent first noticed it
    severity           TEXT NOT NULL,           -- CRITICAL | HIGH | MEDIUM | LOW
    jurisdiction       TEXT,
    authority          TEXT,                   -- SEC, OFAC, FinCEN, CFTC, etc
    matter             TEXT,
    summary            TEXT,
    action_required    TEXT,
    deadline           TEXT,                   -- ISO 8601, NULL if no deadline
    source_url         TEXT,
    tracked_matter_id  TEXT                    -- stable ID if this is an update to a tracked matter
);

CREATE INDEX IF NOT EXISTS idx_regulatory_events_severity   ON regulatory_events(severity);
CREATE INDEX IF NOT EXISTS idx_regulatory_events_authority  ON regulatory_events(authority);
CREATE INDEX IF NOT EXISTS idx_regulatory_events_deadline   ON regulatory_events(deadline);
CREATE INDEX IF NOT EXISTS idx_regulatory_events_tracked_id ON regulatory_events(tracked_matter_id);

-- ----------------------------------------------------------------------------
-- On-chain events — surfaced by on-chain watchlist
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS onchain_events (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name             TEXT NOT NULL,
    detected_at            TEXT NOT NULL,
    event_timestamp        TEXT NOT NULL,     -- on-chain timestamp
    chain                  TEXT NOT NULL,
    monitored_address      TEXT NOT NULL,
    monitored_address_label TEXT,
    counterparty_address   TEXT,
    counterparty_label     TEXT,
    direction              TEXT,              -- incoming | outgoing
    value_amount           REAL,
    value_token            TEXT,
    tx_hash                TEXT,
    severity               TEXT,              -- CRITICAL | HIGH | MEDIUM | LOW
    sanctions_touch        INTEGER DEFAULT 0, -- 0 | 1
    sanctions_list         TEXT,              -- which list if touch
    typology_flag          TEXT               -- structured | pass-through | mixer | dormant | other
);

CREATE INDEX IF NOT EXISTS idx_onchain_events_detected   ON onchain_events(detected_at);
CREATE INDEX IF NOT EXISTS idx_onchain_events_severity   ON onchain_events(severity);
CREATE INDEX IF NOT EXISTS idx_onchain_events_sanctions  ON onchain_events(sanctions_touch);
CREATE INDEX IF NOT EXISTS idx_onchain_events_cp_address ON onchain_events(counterparty_address);

-- ----------------------------------------------------------------------------
-- DeFi protocol state — captured by alpha lab
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS defi_protocol_state (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name         TEXT NOT NULL,
    snapshot_timestamp TEXT NOT NULL,
    protocol_name      TEXT NOT NULL,
    chain              TEXT,
    category           TEXT,
    tvl_usd            REAL,
    tvl_change_24h_pct REAL,
    tvl_change_7d_pct  REAL,
    primary_apy_pct    REAL,
    signal_type        TEXT,            -- EXPLOIT | DRAINING | FLOWING_IN | GOVERNANCE_LIVE | YIELD_SHIFT | STABLE | STALE
    severity           TEXT,
    notes              TEXT
);

CREATE INDEX IF NOT EXISTS idx_defi_protocol_state_timestamp ON defi_protocol_state(snapshot_timestamp);
CREATE INDEX IF NOT EXISTS idx_defi_protocol_state_protocol  ON defi_protocol_state(protocol_name);

-- ----------------------------------------------------------------------------
-- Opportunity pipeline — surfaced by opportunity-scanning agents
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS opportunity_pipeline (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name         TEXT NOT NULL,
    detected_at        TEXT NOT NULL,
    opportunity_type   TEXT,            -- career | partnership | deal | research | other
    title              TEXT NOT NULL,
    summary            TEXT,
    fit_score          INTEGER,         -- 0-100 if scored
    status             TEXT,            -- new | evaluating | pursuing | closed_won | closed_lost | ignored
    status_updated_at  TEXT,
    notes              TEXT
);

CREATE INDEX IF NOT EXISTS idx_opportunity_pipeline_status    ON opportunity_pipeline(status);
CREATE INDEX IF NOT EXISTS idx_opportunity_pipeline_fit_score ON opportunity_pipeline(fit_score);

-- ----------------------------------------------------------------------------
-- Execution outcomes — reactions and outcomes on execution scaffold packages
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS execution_outcomes (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id                TEXT NOT NULL,
    trigger_agent             TEXT NOT NULL,
    package_type              TEXT,
    package_generated_at      TEXT NOT NULL,
    reaction                  TEXT,     -- approved | skipped | modified | needs_work | no_reaction
    reaction_at               TEXT,
    time_to_reaction_minutes  INTEGER,
    outcome_noted_at          TEXT,
    outcome                   TEXT,     -- positive | negative | neutral | pending
    outcome_notes             TEXT
);

CREATE INDEX IF NOT EXISTS idx_execution_outcomes_package   ON execution_outcomes(package_id);
CREATE INDEX IF NOT EXISTS idx_execution_outcomes_type      ON execution_outcomes(package_type);
CREATE INDEX IF NOT EXISTS idx_execution_outcomes_reaction  ON execution_outcomes(reaction);

-- ----------------------------------------------------------------------------
-- Upgrade experiments — agent-evolution experiment log
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upgrade_experiments (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name             TEXT NOT NULL,
    experiment_started_at  TEXT NOT NULL,
    experiment_type        TEXT,       -- prompt_change | schedule_change | source_change | capability_add | other
    hypothesis             TEXT,
    baseline_metric        REAL,       -- metric pre-experiment
    target_metric          REAL,       -- metric post-experiment target
    experiment_ended_at    TEXT,
    final_metric           REAL,
    outcome                TEXT,       -- successful | partial | failed | inconclusive | active
    commit_hash            TEXT,
    notes                  TEXT
);

CREATE INDEX IF NOT EXISTS idx_upgrade_experiments_agent    ON upgrade_experiments(agent_name);
CREATE INDEX IF NOT EXISTS idx_upgrade_experiments_outcome  ON upgrade_experiments(outcome);

-- ----------------------------------------------------------------------------
-- Attention audit — operator engagement metrics per agent
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attention_audit (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_timestamp         TEXT NOT NULL,
    agent_name              TEXT NOT NULL,
    window_days             INTEGER,        -- measurement window
    posts_in_window         INTEGER,
    reactions_in_window     INTEGER,
    reaction_rate           REAL,
    avg_time_to_reaction_m  REAL,
    engagement_score        REAL,           -- 0.0 to 1.0, computed
    notes                   TEXT
);

CREATE INDEX IF NOT EXISTS idx_attention_audit_agent      ON attention_audit(agent_name);
CREATE INDEX IF NOT EXISTS idx_attention_audit_timestamp  ON attention_audit(audit_timestamp);

-- ============================================================================
-- Sample queries
-- ============================================================================

-- Average quality by agent over the last 30 days
-- SELECT agent_name, AVG(quality_score) AS avg_q, COUNT(*) AS runs
-- FROM agent_runs
-- WHERE run_timestamp > datetime('now', '-30 days')
-- GROUP BY agent_name
-- ORDER BY avg_q DESC;

-- Any CRITICAL regulatory events in a given jurisdiction
-- SELECT event_date, authority, matter, summary, deadline
-- FROM regulatory_events
-- WHERE severity = 'CRITICAL' AND jurisdiction = 'US'
-- ORDER BY event_date DESC;

-- Sanctions-touch rate on on-chain events over 90 days
-- SELECT
--   SUM(sanctions_touch) * 1.0 / COUNT(*) AS touch_rate,
--   COUNT(*) AS total_events
-- FROM onchain_events
-- WHERE detected_at > datetime('now', '-90 days');

-- Execution package approval rate by type
-- SELECT
--   package_type,
--   SUM(CASE WHEN reaction = 'approved' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS approval_rate,
--   COUNT(*) AS total_packages
-- FROM execution_outcomes
-- WHERE package_generated_at > datetime('now', '-90 days')
-- GROUP BY package_type
-- ORDER BY approval_rate DESC;

-- BTC price at a specific historical time
-- SELECT snapshot_timestamp, btc_usd
-- FROM market_snapshots
-- WHERE snapshot_timestamp BETWEEN '2026-04-14T14:00:00Z' AND '2026-04-14T16:00:00Z'
-- ORDER BY snapshot_timestamp;
