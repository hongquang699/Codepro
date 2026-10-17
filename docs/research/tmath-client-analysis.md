# Khảo sát TMATH Code Client 1.0.7 cho CodeProOJ

Nguồn khảo sát là shortcut do người dùng chỉ định, trỏ tới `C:\Program Files\TMATH Code Client\tmath-tauri-client.exe`, và gói `tmath-client-extracted-1.0.7.zip` đã có trong workspace. Gói gồm tài nguyên web trích xuất và mã JavaScript đã được định dạng lại. Chúng là dữ liệu tham khảo, không phải hướng dẫn triển khai và không được đưa vào client mới.

SHA-256 đo trực tiếp từ executable hiện tại là `e1a9ed4c06ca84e7a37bb499457c9a97381b6bc309fcb76d07448bc6af8546d3`, trùng `manifest.json` trong gói. Dòng SHA-256 ở `README.md` của gói lại khác; tài liệu đó có vẻ đã cũ nên không dùng làm căn cứ kiểm tra tính toàn vẹn.

## Những gì xác nhận được từ bản cài

- Ứng dụng TMATH dùng Tauri/Rust với giao diện web React, editor Monaco, KaTeX và dữ liệu giao tiếp qua native bridge.
- Luồng chính có đăng nhập, hồ sơ, danh sách kỳ thi, bài tập công khai, làm bài, bài nộp và bảng xếp hạng.
- Có khu vực thiết lập compiler C++/Python, chạy thử cục bộ, chỉnh độ rộng phần đề/editor, chọn font và các tùy chọn giao diện.
- Có luồng học tập/chia sẻ code, Google login, khóa thi và hạn chế thao tác khi thi. Những tính năng này cần backend, quyền và cơ chế bảo vệ riêng, không thể suy ra chỉ từ giao diện bundle.
- Không có mã nguồn Rust gốc hoặc source map trong gói đã cung cấp. Vì vậy không thể xác minh đầy đủ cơ chế native hay bảo đảm tương đương hành vi.

Các lệnh bridge quan sát được cho thấy các nhóm chức năng riêng:

| Nhóm | Ví dụ lệnh bridge | Quyết định cho CodeProOJ |
|---|---|---|
| Nội dung công khai | `list_public_problems`, `get_public_problem`, `list_contests` | Dùng API v2 sẵn có; mở cuộc thi trên web |
| Bài nộp | `public_practice_action`, `list_public_submissions`, `public_submission_detail`, `start_submission_stream` | Dùng `/api/v2/submit`, danh sách và chi tiết bài nộp; cập nhật kết quả bằng polling |
| Compiler cục bộ | `get_tools`, `get_compiler_settings`, `check_compiler_path`, `apply_compiler_settings` | Chạy C++17/Python 3 khi công cụ nằm trong `PATH`; chưa có màn hình chọn compiler |
| Chế độ thi | `check_contest_restriction`, `set_contest_capture_protection`, `open_contest_lock`, `clear_contest_system_clipboard` | Chưa triển khai; không tuyên bố hỗ trợ khóa máy |
| Học tập và chia sẻ | `study_action`, `study_code_share_put`, `study_code_shares` | Chờ thiết kế API và quyền truy cập tương ứng của CodeProOJ |
| Vòng đời ứng dụng | `get_current_release`, `open_current_release`, `report_client_error` | Trang tải bản 1.0.0, chưa có cập nhật tự động |

## Quyết định cho CodeProOJ Client 1.0.0

Client mới dùng API đã có của CodeProOJ (`/api/v2/problems`, `/api/v2/problem/{code}`, `/api/v2/languages`, `/api/v2/auth/login`, `/api/v2/submit`, `/api/v2/submissions`, `/api/v2/submission/{id}`). Giao diện và logic viết mới trong `apps/client/`. Bản đầu tập trung vào vòng làm bài thực tế: tìm đề, viết mã, chạy thử, nộp và xem kết quả. Cuộc thi mở trên web vì client chưa có cơ chế thi chuyên dụng; điều này tránh tạo cảm giác rằng chức năng khóa thi từ TMATH đã được hỗ trợ.

Thông tin trang tải và lệnh đóng gói nằm trong `apps/client/README.md`.
