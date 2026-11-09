-- Seed initial default admin and sample problems
INSERT INTO roles (name, description) VALUES ('SUPER_ADMIN', 'Full system access') ON CONFLICT DO NOTHING;
