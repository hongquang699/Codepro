# Lưu dữ liệu cuộc thi

HQ dùng các model Django hiện có: Contest, ContestProblem, ContestParticipation,
Problem, Submission, SubmissionTestCase, Clarification và RatingHistory.
Mã nguồn nằm trong Submission; gói bài toán nằm ở DMOJ_PROBLEM_DATA_ROOT.

## Tạo bản lưu riêng tư

Quản trị viên có thể mở trang quản lý cuộc thi và chọn **Tải bản lưu ZIP**.
Chức năng chỉ cho tài khoản staff/superuser đang hoạt động, dùng POST có xác thực
và kiểm tra CSRF khi dùng phiên đăng nhập. API không cho tải cuộc thi đang diễn ra
hoặc bản lưu thiếu gói bài toán; dữ liệu tải về không được cache.
Endpoint: `POST /api/v2/admin/contest/{key}/archive`.

Chạy từ thư mục dự án, dùng mã cuộc thi đã kết thúc và đường dẫn ZIP mới:

```powershell
python manage.py archive_contest C:\Backups\HQ\round-01.zip --contest ROUND01
python manage.py archive_contest C:\Backups\HQ\round-01.zip --verify
```

ZIP chứa data.json (cấu hình cuộc thi, đề bài, ánh xạ bài, người tham gia,
mã nguồn, kết quả từng test, hỏi đáp, rating) và problems/ (test, checker,
validator, lời giải, tài liệu đính kèm). manifest.json ghi phiên bản định dạng,
thời điểm xuất và SHA-256/kích thước từng tệp. Gói bài bị thiếu được báo rõ.
Không ghi đè bản lưu cũ; lỗi tạo ZIP không để lại bản lưu đích dở dang.

Bản lưu có mã nguồn và test bí mật: đặt ngoài thư mục phục vụ web và giới hạn
quyền truy cập hệ điều hành. Không chứa mật khẩu, email, token hoặc khóa mã hóa.
Test giữ nguyên mã hóa hiện tại; cần sao lưu khóa riêng theo quy trình vận hành.
SHA-256 phát hiện hỏng dữ liệu, không thay thế chữ ký xác thực nguồn bản lưu.

Đây là bản xuất để lưu trữ, chưa có lệnh nhập/khôi phục tự động. ID và quan hệ
trong JSON là ID gốc; không nhập trực tiếp vào một cơ sở dữ liệu khác.
Các gói bài được đọc sau khi chụp dữ liệu DB: dừng sửa đề/test và chấm lại trong
khi xuất để có bản lưu đồng nhất. Bảng điểm được giữ qua dữ liệu người tham gia
và bài nộp; không xuất cache bảng điểm hoặc dữ liệu chống gian lận.
Cuộc thi gốc vẫn giữ nguyên để phục vụ xem lại/luyện tập theo quyền hiện có.
