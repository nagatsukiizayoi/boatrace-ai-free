-- ============================================================
-- boatrace-ai-free
-- Initial database schema for SQLite
-- STEP 61
-- ============================================================
--
-- Purpose:
--   Store boat race data, entries, odds, AI predictions,
--   tickets, race results, alert history, and model run history.
--
-- Notes:
--   - Designed for SQLite first.
--   - Naming is kept portable for future PostgreSQL migration.
--   - Use TEXT for timestamps in ISO-8601 format.
--   - Foreign keys should be enabled by application code:
--       PRAGMA foreign_keys = ON;
--
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. Venues
--    Boat race venue master.
-- ============================================================

CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  venue_code TEXT NOT NULL UNIQUE,
  venue_name TEXT NOT NULL,
  venue_name_kana TEXT,
  region TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_venues_venue_code
  ON venues (venue_code);


-- ============================================================
-- 2. Races
--    Race-level master / daily race information.
-- ============================================================

CREATE TABLE IF NOT EXISTS races (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Natural identifiers
  race_date TEXT NOT NULL,
  venue_id INTEGER NOT NULL,
  race_no INTEGER NOT NULL,

  -- Race information
  race_name TEXT,
  grade TEXT,
  distance_m INTEGER DEFAULT 1800,
  deadline_at TEXT,
  start_at TEXT,

  -- Conditions
  weather TEXT,
  wind_direction TEXT,
  wind_speed_m REAL,
  wave_height_cm REAL,
  temperature_c REAL,
  water_temperature_c REAL,
  water_line TEXT,
  is_stabilizer_used INTEGER NOT NULL DEFAULT 0,
  is_fixed_entry INTEGER NOT NULL DEFAULT 0,

  -- Status
  status TEXT NOT NULL DEFAULT 'scheduled',
  source_url TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (venue_id) REFERENCES venues(id),

  UNIQUE (race_date, venue_id, race_no),

  CHECK (race_no BETWEEN 1 AND 12),
  CHECK (is_stabilizer_used IN (0, 1)),
  CHECK (is_fixed_entry IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_races_race_date
  ON races (race_date);

CREATE INDEX IF NOT EXISTS idx_races_venue_date
  ON races (venue_id, race_date);

CREATE INDEX IF NOT EXISTS idx_races_status
  ON races (status);


-- ============================================================
-- 3. Racers
--    Racer master.
-- ============================================================

CREATE TABLE IF NOT EXISTS racers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  racer_registration_no TEXT NOT NULL UNIQUE,
  racer_name TEXT NOT NULL,
  racer_name_kana TEXT,

  branch TEXT,
  birth_prefecture TEXT,
  class_name TEXT,

  -- Current stats / latest snapshot style fields
  national_win_rate REAL,
  national_2rentai_rate REAL,
  national_3rentai_rate REAL,
  local_win_rate REAL,
  local_2rentai_rate REAL,
  local_3rentai_rate REAL,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_racers_registration_no
  ON racers (racer_registration_no);

CREATE INDEX IF NOT EXISTS idx_racers_class_name
  ON racers (class_name);


-- ============================================================
-- 4. Race entries
--    Six boat entries for each race.
-- ============================================================

CREATE TABLE IF NOT EXISTS race_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  race_id INTEGER NOT NULL,
  racer_id INTEGER NOT NULL,

  frame_no INTEGER NOT NULL,
  boat_no INTEGER NOT NULL,

  motor_no TEXT,
  boat_number TEXT,

  -- Pre-race stats
  national_win_rate REAL,
  national_2rentai_rate REAL,
  national_3rentai_rate REAL,
  local_win_rate REAL,
  local_2rentai_rate REAL,
  local_3rentai_rate REAL,

  motor_2rentai_rate REAL,
  motor_3rentai_rate REAL,
  boat_2rentai_rate REAL,
  boat_3rentai_rate REAL,

  -- Exhibition data
  exhibition_time REAL,
  exhibition_st REAL,
  tilt REAL,
  entry_course INTEGER,

  -- Start / result-related fields can be updated after race
  start_timing REAL,
  finish_order INTEGER,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
  FOREIGN KEY (racer_id) REFERENCES racers(id),

  UNIQUE (race_id, frame_no),
  UNIQUE (race_id, racer_id),

  CHECK (frame_no BETWEEN 1 AND 6),
  CHECK (boat_no BETWEEN 1 AND 6),
  CHECK (entry_course IS NULL OR entry_course BETWEEN 1 AND 6),
  CHECK (finish_order IS NULL OR finish_order BETWEEN 1 AND 6)
);

CREATE INDEX IF NOT EXISTS idx_race_entries_race_id
  ON race_entries (race_id);

CREATE INDEX IF NOT EXISTS idx_race_entries_racer_id
  ON race_entries (racer_id);

CREATE INDEX IF NOT EXISTS idx_race_entries_frame
  ON race_entries (race_id, frame_no);


-- ============================================================
-- 5. Odds snapshots
--    Odds are time-series data. Store each fetched snapshot.
-- ============================================================

CREATE TABLE IF NOT EXISTS odds_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  race_id INTEGER NOT NULL,

  bet_type TEXT NOT NULL,
  combination TEXT NOT NULL,
  odds REAL,
  popularity INTEGER,

  captured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  source TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,

  CHECK (
    bet_type IN (
      'tansho',
      'fukusho',
      '2rentan',
      '2renfuku',
      '3rentan',
      '3renfuku',
      'kakuren',
      'unknown'
    )
  )
);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_race_id
  ON odds_snapshots (race_id);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_race_bet_combo
  ON odds_snapshots (race_id, bet_type, combination);

CREATE INDEX IF NOT EXISTS idx_odds_snapshots_captured_at
  ON odds_snapshots (captured_at);


-- ============================================================
-- 6. Prediction runs
--    One row per AI/model execution.
-- ============================================================

CREATE TABLE IF NOT EXISTS prediction_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  run_key TEXT NOT NULL UNIQUE,

  target_date TEXT NOT NULL,
  executed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  model_name TEXT NOT NULL,
  model_version TEXT,
  model_params_json TEXT,

  data_version TEXT,
  source_summary_json TEXT,

  status TEXT NOT NULL DEFAULT 'completed',
  memo TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CHECK (
    status IN (
      'created',
      'running',
      'completed',
      'failed',
      'cancelled'
    )
  )
);

CREATE INDEX IF NOT EXISTS idx_prediction_runs_target_date
  ON prediction_runs (target_date);

CREATE INDEX IF NOT EXISTS idx_prediction_runs_executed_at
  ON prediction_runs (executed_at);

CREATE INDEX IF NOT EXISTS idx_prediction_runs_status
  ON prediction_runs (status);


-- ============================================================
-- 7. Predictions
--    Race-level prediction result.
-- ============================================================

CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  prediction_run_id INTEGER NOT NULL,
  race_id INTEGER NOT NULL,

  -- Main prediction summary
  favorite_boat_no INTEGER,
  rival_boat_no INTEGER,
  darkhorse_boat_no INTEGER,

  confidence REAL,
  expected_value REAL,
  recommended_total_amount INTEGER DEFAULT 0,

  -- Flexible details
  prediction_summary TEXT,
  features_json TEXT,
  scores_json TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (prediction_run_id) REFERENCES prediction_runs(id) ON DELETE CASCADE,
  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,

  UNIQUE (prediction_run_id, race_id),

  CHECK (favorite_boat_no IS NULL OR favorite_boat_no BETWEEN 1 AND 6),
  CHECK (rival_boat_no IS NULL OR rival_boat_no BETWEEN 1 AND 6),
  CHECK (darkhorse_boat_no IS NULL OR darkhorse_boat_no BETWEEN 1 AND 6)
);

CREATE INDEX IF NOT EXISTS idx_predictions_run_id
  ON predictions (prediction_run_id);

CREATE INDEX IF NOT EXISTS idx_predictions_race_id
  ON predictions (race_id);

CREATE INDEX IF NOT EXISTS idx_predictions_confidence
  ON predictions (confidence);


-- ============================================================
-- 8. Prediction tickets
--    Ticket-level recommended bets.
-- ============================================================

CREATE TABLE IF NOT EXISTS prediction_tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  prediction_id INTEGER NOT NULL,

  bet_type TEXT NOT NULL DEFAULT '3rentan',
  combination TEXT NOT NULL,

  amount INTEGER NOT NULL DEFAULT 0,

  estimated_probability REAL,
  expected_odds REAL,
  expected_value REAL,

  rank_no INTEGER,
  confidence REAL,
  reason TEXT,

  -- Result fields, updated after race result is known
  is_hit INTEGER,
  payout_amount INTEGER DEFAULT 0,
  profit_amount INTEGER,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE,

  CHECK (amount >= 0),
  CHECK (is_hit IS NULL OR is_hit IN (0, 1)),
  CHECK (
    bet_type IN (
      'tansho',
      'fukusho',
      '2rentan',
      '2renfuku',
      '3rentan',
      '3renfuku',
      'kakuren',
      'unknown'
    )
  )
);

CREATE INDEX IF NOT EXISTS idx_prediction_tickets_prediction_id
  ON prediction_tickets (prediction_id);

CREATE INDEX IF NOT EXISTS idx_prediction_tickets_bet_type
  ON prediction_tickets (bet_type);

CREATE INDEX IF NOT EXISTS idx_prediction_tickets_is_hit
  ON prediction_tickets (is_hit);


-- ============================================================
-- 9. Race results
--    Final race result and payout data.
-- ============================================================

CREATE TABLE IF NOT EXISTS race_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  race_id INTEGER NOT NULL UNIQUE,

  result_status TEXT NOT NULL DEFAULT 'official',

  first_boat_no INTEGER,
  second_boat_no INTEGER,
  third_boat_no INTEGER,

  winning_trick TEXT,

  -- Start accident / cancellation info
  has_flying INTEGER NOT NULL DEFAULT 0,
  has_late INTEGER NOT NULL DEFAULT 0,
  cancellation_json TEXT,

  -- Payouts in JSON for flexible handling
  payouts_json TEXT,

  -- Frequently used payout fields
  trifecta_combination TEXT,
  trifecta_payout INTEGER,
  trifecta_popularity INTEGER,

  exacta_combination TEXT,
  exacta_payout INTEGER,

  quinella_combination TEXT,
  quinella_payout INTEGER,

  finalized_at TEXT,
  source_url TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,

  CHECK (first_boat_no IS NULL OR first_boat_no BETWEEN 1 AND 6),
  CHECK (second_boat_no IS NULL OR second_boat_no BETWEEN 1 AND 6),
  CHECK (third_boat_no IS NULL OR third_boat_no BETWEEN 1 AND 6),
  CHECK (has_flying IN (0, 1)),
  CHECK (has_late IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_race_results_race_id
  ON race_results (race_id);

CREATE INDEX IF NOT EXISTS idx_race_results_finalized_at
  ON race_results (finalized_at);

CREATE INDEX IF NOT EXISTS idx_race_results_trifecta
  ON race_results (trifecta_combination);


-- ============================================================
-- 10. Alert events
--     Alert history. Dashboard alerts can be persisted here.
-- ============================================================

CREATE TABLE IF NOT EXISTS alert_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  prediction_run_id INTEGER,
  race_id INTEGER,

  level TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  message TEXT NOT NULL,

  details_json TEXT,

  occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (prediction_run_id) REFERENCES prediction_runs(id) ON DELETE SET NULL,
  FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE SET NULL,

  CHECK (level IN ('warning', 'danger', 'info')),
  CHECK (
    alert_type IN (
      'ticket_count',
      'total_amount',
      'update_delay',
      'update_unknown',
      'missing_exhibition_time',
      'missing_exhibition_st',
      'missing_final_odds',
      'data_fetch_error',
      'prediction_error',
      'other'
    )
  )
);

CREATE INDEX IF NOT EXISTS idx_alert_events_level
  ON alert_events (level);

CREATE INDEX IF NOT EXISTS idx_alert_events_alert_type
  ON alert_events (alert_type);

CREATE INDEX IF NOT EXISTS idx_alert_events_occurred_at
  ON alert_events (occurred_at);

CREATE INDEX IF NOT EXISTS idx_alert_events_race_id
  ON alert_events (race_id);

CREATE INDEX IF NOT EXISTS idx_alert_events_prediction_run_id
  ON alert_events (prediction_run_id);


-- ============================================================
-- 11. Export logs
--     Track generation of docs/prediction.json or other files.
-- ============================================================

CREATE TABLE IF NOT EXISTS export_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  prediction_run_id INTEGER,

  export_type TEXT NOT NULL DEFAULT 'prediction_json',
  output_path TEXT NOT NULL,
  exported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  status TEXT NOT NULL DEFAULT 'completed',
  message TEXT,

  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (prediction_run_id) REFERENCES prediction_runs(id) ON DELETE SET NULL,

  CHECK (
    export_type IN (
      'prediction_json',
      'alert_settings_json',
      'report_json',
      'csv',
      'other'
    )
  ),
  CHECK (
    status IN (
      'completed',
      'failed'
    )
  )
);

CREATE INDEX IF NOT EXISTS idx_export_logs_prediction_run_id
  ON export_logs (prediction_run_id);

CREATE INDEX IF NOT EXISTS idx_export_logs_exported_at
  ON export_logs (exported_at);


-- ============================================================
-- 12. Useful views
-- ============================================================

CREATE VIEW IF NOT EXISTS v_race_overview AS
SELECT
  r.id AS race_id,
  r.race_date,
  v.venue_code,
  v.venue_name,
  r.race_no,
  r.race_name,
  r.grade,
  r.deadline_at,
  r.start_at,
  r.status,
  r.weather,
  r.wind_speed_m,
  r.wave_height_cm,
  r.temperature_c,
  r.water_temperature_c
FROM races r
JOIN venues v
  ON r.venue_id = v.id;


CREATE VIEW IF NOT EXISTS v_prediction_ticket_results AS
SELECT
  pr.id AS prediction_run_id,
  pr.run_key,
  pr.target_date,
  pr.model_name,
  pr.model_version,
  p.id AS prediction_id,
  p.race_id,
  t.id AS ticket_id,
  t.bet_type,
  t.combination,
  t.amount,
  t.estimated_probability,
  t.expected_odds,
  t.expected_value,
  t.is_hit,
  t.payout_amount,
  t.profit_amount
FROM prediction_runs pr
JOIN predictions p
  ON p.prediction_run_id = pr.id
JOIN prediction_tickets t
  ON t.prediction_id = p.id;


CREATE VIEW IF NOT EXISTS v_prediction_run_summary AS
SELECT
  pr.id AS prediction_run_id,
  pr.run_key,
  pr.target_date,
  pr.executed_at,
  pr.model_name,
  pr.model_version,
  COUNT(DISTINCT p.race_id) AS race_count,
  COUNT(t.id) AS ticket_count,
  COALESCE(SUM(t.amount), 0) AS total_amount,
  COALESCE(SUM(t.payout_amount), 0) AS total_payout,
  COALESCE(SUM(t.payout_amount), 0) - COALESCE(SUM(t.amount), 0) AS total_profit,
  CASE
    WHEN COALESCE(SUM(t.amount), 0) = 0 THEN NULL
    ELSE ROUND(COALESCE(SUM(t.payout_amount), 0) * 100.0 / SUM(t.amount), 2)
  END AS return_rate_percent,
  CASE
    WHEN COUNT(t.id) = 0 THEN NULL
    ELSE ROUND(SUM(CASE WHEN t.is_hit = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(t.id), 2)
  END AS hit_rate_percent
FROM prediction_runs pr
LEFT JOIN predictions p
  ON p.prediction_run_id = pr.id
LEFT JOIN prediction_tickets t
  ON t.prediction_id = p.id
GROUP BY
  pr.id,
  pr.run_key,
  pr.target_date,
  pr.executed_at,
  pr.model_name,
  pr.model_version;


-- ============================================================
-- End of schema
-- ============================================================

