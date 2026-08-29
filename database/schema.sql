-- ModelShield — Failure Intelligence + Reproducibility schema
-- Owned by Shyalona (Section 18 of the playbook)

PRAGMA foreign_keys = ON;

-- A model/version under test (baseline or candidate)
CREATE TABLE IF NOT EXISTS models (
    model_id        TEXT PRIMARY KEY,      -- e.g. "candidate-v2"
    role            TEXT NOT NULL CHECK (role IN ('baseline', 'candidate')),
    reference       TEXT,                  -- artifact path / registry pointer
    created_at      TEXT DEFAULT (datetime('now'))
);

-- One evaluation run of a model under one challenge condition
CREATE TABLE IF NOT EXISTS evaluations (
    
    evaluation_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   TEXT NOT NULL,
    model_id        TEXT NOT NULL REFERENCES models(model_id),
    condition       TEXT NOT NULL,         -- e.g. "blur", "low_light_blur"
    parameters      TEXT NOT NULL,         -- JSON blob, e.g. {"severity": 0.6}
    baseline_score  REAL NOT NULL,
    candidate_score REAL NOT NULL,
    delta           REAL NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('pass', 'failure')),
    seed            INTEGER,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- A verified/unverified failure — the Failure Fingerprint
CREATE TABLE IF NOT EXISTS failures (
    failure_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id   INTEGER REFERENCES evaluations(evaluation_id),
    condition       TEXT NOT NULL,
    parameters      TEXT NOT NULL,         -- JSON blob
    baseline_score  REAL NOT NULL,
    candidate_score REAL NOT NULL,
    delta           REAL NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('minor', 'major', 'critical')),
    verified        INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    model_id        TEXT REFERENCES models(model_id),
    dataset_ref     TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Reproducibility Capsule — locked context needed to replay an evaluation
CREATE TABLE IF NOT EXISTS capsules (
    capsule_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id          INTEGER NOT NULL REFERENCES failures(failure_id),
    model_reference      TEXT,
    dataset_reference     TEXT,
    preprocessing        TEXT,             -- JSON blob
    seed                 INTEGER,
    evaluation_config     TEXT,             -- JSON blob
    challenge_parameters  TEXT,             -- JSON blob
    environment           TEXT,             -- JSON blob (deps/versions)
    metrics               TEXT,             -- JSON blob
    run_id                TEXT,
    created_at            TEXT DEFAULT (datetime('now'))
);

-- Regression-ready failure record — consumed by Kartikay's regression engine
CREATE TABLE IF NOT EXISTS regression_tests (
    regression_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id      INTEGER NOT NULL REFERENCES failures(failure_id),
    threshold       REAL NOT NULL,
    policy          TEXT NOT NULL CHECK (policy IN ('pass', 'review', 'block')),
    enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_evaluations_experiment ON evaluations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_failures_verified ON failures(verified);
CREATE INDEX IF NOT EXISTS idx_failures_condition ON failures(condition);
CREATE INDEX IF NOT EXISTS idx_regression_enabled ON regression_tests(enabled);
