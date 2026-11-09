-- ==============================================================================
-- BẢO MẬT MYSQL - NGUYÊN TẮC QUYỀN TỐI THIỂU (LEAST PRIVILEGE) CHO DJANGO
-- ==============================================================================
-- 1. Tạo Database chuẩn mã hóa utf8mb4 (tránh các lỗi byte encoding bypass SQLi)
CREATE DATABASE IF NOT EXISTS coding_platform
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 2. Tạo User Ứng dụng Web (Web Runtime User)
-- User này CHỈ được cấp quyền thao tác DỮ LIỆU: SELECT, INSERT, UPDATE, DELETE.
-- TUYỆT ĐỐI KHÔNG CẤP: DROP, ALTER, CREATE, GRANT, SUPER, FILE.
-- Nếu kẻ tấn công khai thác được SQLi, chúng KHÔNG THỂ DROP TABLE hay ALTER SCHEMA!
CREATE USER IF NOT EXISTS 'coding_app'@'localhost' IDENTIFIED BY 'ChangeMeSecureAppPass2026!';
CREATE USER IF NOT EXISTS 'coding_app'@'127.0.0.1' IDENTIFIED BY 'ChangeMeSecureAppPass2026!';

GRANT SELECT, INSERT, UPDATE, DELETE ON coding_platform.* TO 'coding_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON coding_platform.* TO 'coding_app'@'127.0.0.1';

-- 3. Tạo User Migration / DevOps Riêng biệt (Tùy chọn)
-- Dùng user này khi chạy 'python manage.py migrate' trong quy trình CI/CD.
CREATE USER IF NOT EXISTS 'coding_migration'@'localhost' IDENTIFIED BY 'ChangeMeMigrationPass2026!';
GRANT ALL PRIVILEGES ON coding_platform.* TO 'coding_migration'@'localhost';

-- 4. Áp dụng thay đổi quyền
FLUSH PRIVILEGES;

-- 5. Thiết lập SQL Mode nghiêm ngặt mặc định ở cấp Session/Server
-- Tránh việc MySQL tự động ép kiểu hoặc cắt ngắn chuỗi gây bypass validation
SET GLOBAL sql_mode = 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION';
