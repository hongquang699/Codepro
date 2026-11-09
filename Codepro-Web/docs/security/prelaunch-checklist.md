# CodeProOJ: kiểm tra trước khi công khai

Video tham chiếu đưa ra 20 mục. Bảng này đối chiếu với mã hiện tại; trạng thái "cần triển khai" không có nghĩa đã được bật trên máy chủ công khai.

| # | Mục | Trạng thái và bằng chứng |
|---|---|---|
| 1 | Hash mật khẩu | Argon2 cho mật khẩu mới; hash cũ được xác minh và nâng cấp lúc đăng nhập (`backend/core/settings.py`). |
| 2 | Giới hạn đăng nhập | Có giới hạn theo IP và khóa khi thử sai (`security/middleware.py`, `backend/auth/security/brute_force.py`). Bộ giới hạn trong middleware lưu theo tiến trình; khi chạy nhiều worker cần kiểm tra tầng dùng chung. |
| 3 | Phiên hết hạn | `cp_session` hết hạn sau 1 ngày hoặc 30 ngày nếu chọn ghi nhớ; cookie Django 1 ngày; DRF token 30 ngày (`backend/auth/services/session.py`, `backend/auth/security/token_auth.py`). |
| 4 | Bỏ log debug nhạy cảm | OTP và URL đặt lại mật khẩu không còn bị in ra log khi SMTP lỗi. Cần rà log của các dịch vụ khác trước khi phát hành. |
| 5 | Bí mật không nằm ở frontend | Secret phía backend lấy từ biến môi trường. DRF token vẫn được trả về cho JavaScript và một số client lưu vào `localStorage`; nên chuyển dần sang phiên HttpOnly để giảm rủi ro XSS. |
| 6 | Không lộ lỗi chi tiết | Hai API tải ZIP testcase trả lỗi chung. Cần rà các API khác theo từng luồng. |
| 7 | Loại tệp tải lên | Testcase chỉ nhận ZIP hợp lệ; thành viên ZIP chỉ được có tên an toàn `.in`, `.out`, `.ans` ở thư mục gốc. Các chức năng upload khác cần rà riêng. |
| 8 | Kích thước tệp | ZIP tối đa 20 MiB, tối đa 1.000 thành viên và 100 MiB dữ liệu giải nén; từng thành viên tối đa 20 MiB. |
| 9 | Xác thực trên server | Kiểm tra ZIP, tên, trùng tên và kích thước trước khi ghi. Các endpoint khác dùng serializer/validator riêng, cần kiểm thử theo nghiệp vụ. |
| 10 | IDOR | Kiểm thử bằng hai tài khoản xác nhận không đọc được email riêng tư hay sửa hồ sơ người khác (`backend/api/v2/tests_user_access.py`). Vẫn cần mở rộng cho các tài nguyên riêng tư khác. |
| 11 | Phân quyền admin | API admin kiểm tra user active + staff/superuser phía server. Không dựa vào cookie `role` làm quyền. |
| 12 | SQL tham số hóa | Các luồng được rà dùng Django ORM. Cần kiểm toán mọi raw SQL khi thêm tính năng. |
| 13 | HTTPS | Django chuyển hướng HTTPS và bật HSTS khi `DEBUG=False`; proxy phải chuyển đúng giao thức. Cần cấu hình chứng chỉ và DNS ở nơi triển khai. |
| 14 | Security headers | Django và gateway đặt các header như nosniff, frame, referrer, CSP. CSP hiện còn `unsafe-inline`; cần thu hẹp theo từng trang. |
| 15 | Cookie | `cp_session` là HttpOnly, SameSite=Lax và Secure ở production. Cookie `admin_token` chứa API token đã bị loại bỏ; token trả về JSON vẫn là rủi ro cần xử lý. |
| 16 | CORS | Origin cho phép khai báo tường minh bằng `CORS_ALLOWED_ORIGINS`, không bật wildcard. |
| 17 | Database không public | PostgreSQL trong Compose không publish cổng ra host. Kiểm tra thêm firewall của môi trường triển khai. |
| 18 | DB user ít quyền | **Cần triển khai:** Compose đang dùng `POSTGRES_USER` làm tài khoản ứng dụng, thường là superuser của cluster mới. Tạo vai trò ứng dụng riêng và chuyển quyền sở hữu/schema trước khi công khai. |
| 19 | Cloudflare | **Cần triển khai:** chỉ có thể bật sau khi cấu hình tên miền, DNS và tài khoản Cloudflare. |
| 20 | Backup + theo dõi lỗi | Có script sao lưu DB và thư mục dữ liệu trong `scripts/backup/run.sh`; **chưa có lịch tự động, bản sao ngoài máy và cảnh báo lỗi**. |

## Triển khai backup

Trên máy Linux chạy Compose, đặt `CODEPRO_BACKUP_DIR` thành thư mục riêng có quyền truy cập giới hạn rồi chạy `bash scripts/backup/run.sh`. Script tạo `database-*.sql.gz` cùng `files-*.tar.gz`, kiểm tra định dạng và dừng nếu lệnh lỗi. Dữ liệu testcase được mã hóa bằng `TESTCASE_ENCRYPTION_KEY`; sao lưu khóa đó ở kho bí mật riêng, không để chung bản backup công khai.

Thiết lập cron/systemd timer cho script, chuyển bản sao tới kho lưu trữ ngoài máy, định kỳ khôi phục thử trên môi trường độc lập và cấu hình cảnh báo khi lệnh trả mã lỗi. Chưa đánh dấu mục 20 hoàn tất cho tới khi các bước đó được kiểm chứng.

Đăng ký và đặt lại mật khẩu cần SMTP hoạt động. Khai báo `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` (hoặc SSL) và `DEFAULT_FROM_EMAIL` trong `.env`; kiểm tra gửi thư thật trước khi công khai.
