CREATE TABLE IF NOT EXISTS problems (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    difficulty INT DEFAULT 1000,
    time_limit_ms INT DEFAULT 2000,
    memory_limit_mb INT DEFAULT 256,
    author_id BIGINT REFERENCES users(id),
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS problem_tags (
    problem_id BIGINT REFERENCES problems(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(problem_id, tag_id)
);
