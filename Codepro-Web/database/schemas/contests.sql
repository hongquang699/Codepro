CREATE TABLE IF NOT EXISTS contests (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds INT NOT NULL,
    is_rated BOOLEAN DEFAULT true,
    rule_type VARCHAR(20) DEFAULT 'ICPC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contest_problems (
    contest_id BIGINT REFERENCES contests(id) ON DELETE CASCADE,
    problem_id BIGINT REFERENCES problems(id) ON DELETE CASCADE,
    alias VARCHAR(10) NOT NULL,
    points INT DEFAULT 100,
    PRIMARY KEY(contest_id, problem_id)
);
