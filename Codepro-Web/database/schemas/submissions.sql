CREATE TYPE submission_verdict AS ENUM (
    'QUEUED', 'COMPILING', 'RUNNING', 'CHECKING',
    'ACCEPTED', 'WRONG_ANSWER', 'TIME_LIMIT_EXCEEDED',
    'MEMORY_LIMIT_EXCEEDED', 'RUNTIME_ERROR', 'COMPILATION_ERROR'
);

CREATE TABLE IF NOT EXISTS submissions (
    id BIGSERIAL PRIMARY KEY,
    problem_id BIGINT REFERENCES problems(id),
    user_id BIGINT REFERENCES users(id),
    language VARCHAR(20) NOT NULL,
    source_code TEXT NOT NULL,
    status submission_verdict DEFAULT 'QUEUED',
    time_used_ms INT DEFAULT 0,
    memory_used_kb INT DEFAULT 0,
    points INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
