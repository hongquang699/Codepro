-- Ranking & Leaderboard Subsystem Schema
-- Compatible with SQLite / PostgreSQL

CREATE TABLE IF NOT EXISTS ranking_globalranking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL DEFAULT 1,
    rating INTEGER NOT NULL DEFAULT 1500,
    score REAL NOT NULL DEFAULT 0.0,
    solved INTEGER NOT NULL DEFAULT 0,
    submissions INTEGER NOT NULL DEFAULT 0,
    country VARCHAR(64) DEFAULT 'Vietnam',
    school VARCHAR(128) DEFAULT '',
    organization_id INTEGER REFERENCES judge_organization(id) ON DELETE SET NULL,
    tier VARCHAR(32) DEFAULT 'Specialist',
    last_active DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ranking_contestranking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contest_id INTEGER NOT NULL REFERENCES judge_contest(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL DEFAULT 1,
    solved INTEGER NOT NULL DEFAULT 0,
    score REAL NOT NULL DEFAULT 0.0,
    penalty INTEGER NOT NULL DEFAULT 0,
    rating_before INTEGER,
    rating_after INTEGER,
    rating_change INTEGER DEFAULT 0,
    problem_details TEXT NOT NULL DEFAULT '{}',
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ranking_userrating (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth_user(id) ON DELETE CASCADE,
    current_rating INTEGER NOT NULL DEFAULT 1500,
    max_rating INTEGER NOT NULL DEFAULT 1500,
    rank_tier VARCHAR(32) DEFAULT 'Specialist',
    volatility REAL NOT NULL DEFAULT 300.0,
    contests_participated INTEGER NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ranking_ratinghistoryrecord (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    contest_id INTEGER REFERENCES judge_contest(id) ON DELETE CASCADE,
    contest_name VARCHAR(256) DEFAULT '',
    old_rating INTEGER NOT NULL,
    new_rating INTEGER NOT NULL,
    rating_change INTEGER NOT NULL,
    rank_in_contest INTEGER NOT NULL DEFAULT 1,
    performance INTEGER,
    timestamp DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ranking_rankingsnapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_type VARCHAR(32) NOT NULL DEFAULT 'global',
    snapshot_key VARCHAR(64) NOT NULL,
    data TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME NOT NULL
);
