-- Fast Performance Indexes for Ranking & Leaderboard Queries

-- 1. Global Leaderboard
CREATE INDEX IF NOT EXISTS idx_ranking_global_rank ON ranking_globalranking(rank);
CREATE INDEX IF NOT EXISTS idx_ranking_global_rating ON ranking_globalranking(rating DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_global_country ON ranking_globalranking(country, rank);
CREATE INDEX IF NOT EXISTS idx_ranking_global_school ON ranking_globalranking(school, rank);
CREATE INDEX IF NOT EXISTS idx_ranking_global_org ON ranking_globalranking(organization_id, rank);

-- 2. Contest Scoreboard Matrix
CREATE INDEX IF NOT EXISTS idx_ranking_contest_rank ON ranking_contestranking(contest_id, rank);
CREATE INDEX IF NOT EXISTS idx_ranking_contest_solved_penalty ON ranking_contestranking(contest_id, solved DESC, penalty ASC);

-- 3. Rating Leaderboard
CREATE INDEX IF NOT EXISTS idx_ranking_rating_current ON ranking_userrating(current_rating DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_rating_tier ON ranking_userrating(rank_tier);

-- 4. User Rating History Timeline
CREATE INDEX IF NOT EXISTS idx_ranking_history_user_time ON ranking_ratinghistoryrecord(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ranking_history_contest ON ranking_ratinghistoryrecord(contest_id);

-- 5. Leaderboard Snapshots
CREATE INDEX IF NOT EXISTS idx_ranking_snapshot_key ON ranking_rankingsnapshot(snapshot_type, snapshot_key, created_at DESC);
