# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Thí sinh (ưu tiên hàng đầu):** học sinh và sinh viên luyện thi Tin học Olympic, HSG Quốc gia và ICPC. Họ làm bài, nộp mã, theo dõi kết quả và bảng xếp hạng, học thuật toán theo chủ đề.
- **Giáo viên và quản trị kỳ thi:** tạo và điều hành kỳ thi, quản lý lớp, chấm và rà soát gian lận. Đây là đối tượng thứ hai, dùng khu vực quản trị riêng.

## Product Purpose

CodeProOJ là nền tảng luyện thi và thi đấu lập trình: website chính, API và hệ thống chấm bài phân tán. Mục tiêu là để thí sinh luyện tập và thi đấu công bằng, nhanh và đáng tin cậy. Thành công nghĩa là thí sinh quay lại luyện tập đều đặn và kỳ thi diễn ra không có sự cố về chấm bài hay gian lận.

## Positioning

Chấm bài thật, không mô phỏng: mã của thí sinh không bao giờ chạy trong tiến trình web. Bài nộp đi qua Judge Manager tới các worker và sandbox. Kỳ thi có hệ thống chống gian lận dựa trên dấu vân tay token, với kháng nghị và audit log. Nền tảng cũng có chế độ thi LAN ngoại tuyến qua ứng dụng desktop.

## Operating Context

- Thí sinh dùng trình duyệt trên máy cá nhân, thường trong phòng thi hoặc khi tự luyện.
- Trong kỳ thi, thí sinh theo dõi bảng điểm trực tiếp, đề bài và thông báo qua WebSocket.
- Giáo viên và quản trị làm việc trên bảng điều khiển dày dữ liệu (bảng, bộ lọc, nhật ký).
- Ứng dụng desktop (Codepro-Client) và OJ thi qua LAN (Submit-Offline) là hai bề mặt riêng, không thuộc phạm vi website này.

## Capabilities and Constraints

- Chức năng đã có: đề bài và nộp bài, kỳ thi và bảng điểm, bảng xếp hạng với rating Elo, thư viện thuật toán, diễn đàn và nhóm học tập, blog với Markdown, cổng giáo viên, quản trị kỳ thi, chống gian lận, khu vực admin, xác thực 2FA.
- Ràng buộc kỹ thuật: frontend là HTML/JS/CSS thuần trong `frontend/`, không dùng framework. Trang phải mở qua gateway `localhost:8888` (không `file://`).
- Ràng buộc bảo mật: quyền được kiểm tra ở backend; cookie ghi cần CSRF; không đọc quyền từ `localStorage`.
- Thuật ngữ đang dùng: "kỳ thi", "bài nộp", "testcase", "bảng xếp hạng", "rating", "kháng nghị".
- Chưa xác định: không có quyết định sản phẩm nào còn mở về phạm vi chức năng.

## Brand Commitments

- Tên sản phẩm: **CodeProOJ** (Codepro trên logo và repo).
- Logo hiện có: `docs/branding/codepro-logo.png`.
- Ngôn ngữ giao diện và tài liệu: tiếng Việt.
- Chủ đề: nền tảng luyện thi Olympic Tin học, HSG Quốc gia và ICPC.
- Người dùng chọn: thí sinh là ưu tiên; hỗ trợ đầy đủ chế độ sáng và tối, với chế độ sáng là mặc định.
- Người dùng chọn: thiết kế lại toàn bộ nhận diện thị giác; giữ nội dung và chức năng.

## Evidence on Hand

- Logo: `docs/branding/codepro-logo.png`.
- Tài liệu sản phẩm: `README.md`, `AGENTS.md`, `docs/`.
- Chưa có: số liệu người dùng, lời chứng thực, khách hàng, hay case study. Không được bịa các con số này.

## Product Principles

1. Thí sinh trước: mọi màn hình làm bài, nộp bài và xem kết quả phải rõ ràng, nhanh, ít phân tâm.
2. Kết quả đáng tin: trạng thái chấm, thứ hạng và cảnh báo gian lận phải phân biệt rõ tín hiệu với kết luận.
3. Chuẩn kỹ thuật thi đấu: giữ mật độ thông tin và tính nhất quán của bảng, mã nguồn, đề bài như một công cụ làm việc.
4. Sáng và tối ngang hàng: mọi thành phần đều dùng token màu để đổi theme nhất quán.

## Accessibility & Inclusion

Mục tiêu: WCAG 2.2 AA. Chữ thường cần tỉ lệ tương phản tối thiểu 4.5:1 và liên kết dùng token màu chính; mọi chức năng phải dùng được bằng bàn phím và có menu điều hướng trên màn hình hẹp.
