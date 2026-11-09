# HQ → CodeProOJ: kế hoạch chuyển đổi theo giai đoạn

## Hiện trạng đã kiểm tra

Repository đang chạy bằng Django/DRF/Channels (`backend/`), gateway Node (`apps/web/`), HTML/CSS/JavaScript (`frontend/`), PostgreSQL, Redis, MinIO, BullMQ cho hàng đợi kiểm tra gói đề, judge Python/C++ trong `judge-system/`, Nginx và Docker Compose. Những thành phần này đang phục vụ người dùng và có dữ liệu thật. Không đổi bảng, cắt API hay chuyển luồng chấm khi chưa có kiểm thử tương thích.

| Module đích | Phần đang có trong HQ | Chủ sở hữu hiện tại |
| --- | --- | --- |
| auth | `backend/auth`, session và CSRF | Django |
| users | `backend/users`, `backend/judge/models.py` | Django |
| problems | `backend/problems`, `backend/problem_storage` | Django |
| contests | `backend/contests`, `backend/contest_admin` | Django |
| submissions | `backend/submissions`, `backend/judge` | Django |
| ranking | `backend/ranking` | Django |
| organizations | `backend/organizations` | Django |
| admin | `backend/contest_admin`, `backend/judge/api` | Django |
| judge | `judge-system`, Redis queue | Judge Manager + Django |
| AI | `backend/anti_cheat` có thuật toán token fingerprint; dịch vụ FastAPI mới ở `apps/ai-similarity` | Worker chống gian lận |

## Chênh lệch với kiến trúc đích

- Chưa có ứng dụng React + TypeScript và NestJS + TypeScript. Giao diện hiện tại phụ thuộc nhiều tuyến HTML và script toàn cục; API hiện dùng session/CSRF và nhiều phiên bản tuyến.
- PostgreSQL, Redis, MinIO, WebSocket, Nginx và Docker đã có. BullMQ hiện dùng cho kiểm tra phiên bản đề, chưa phải hàng đợi chấm. Judge dùng giao thức/queue riêng; không thay nó bằng BullMQ cho tới khi đo được tính tương thích và khả năng phục hồi job.
- Judge worker Python/C++ đã có, nhưng cần audit sandbox trên Linux production trước khi mở rộng tải hoặc thay giao thức. Không chạy mã thí sinh trong NestJS, FastAPI hay gateway.
- Dịch vụ FastAPI ở giai đoạn đầu dùng thuật toán fingerprint hiện hữu để giữ cùng kết quả. Đây là điểm tách dịch vụ đánh giá tương đồng, **chưa phải mô hình machine learning**. Kết quả chỉ là tín hiệu để con người xem xét, không tự phạt hay sửa verdict.

## Lộ trình

1. **Đường cơ sở và dịch vụ tương đồng (đang triển khai).** Chốt API/permission test cho từng module. Thêm FastAPI nội bộ, token và timeout; worker có thể chọn qua `AI_SIMILARITY_URL` và quay về tính cục bộ khi lỗi. Không migration dữ liệu. Đo độ trễ, tỉ lệ lỗi và đối chiếu điểm trên các cặp mã đã được phép xử lý.
2. **React + TypeScript song song.** Tạo app riêng dưới tuyến thử nghiệm; chuyển từng màn hình đọc: problems, contests, ranking, organizations, users. Dùng API Django hiện tại và kiểm thử phân quyền/CSRF. Giữ trang cũ cho tới khi hành vi và accessibility tương đương.
3. **NestJS + TypeScript theo ranh giới module.** Tạo service với auth, users, problems, contests, submissions, ranking, organizations, admin, judge và AI modules. Ban đầu chỉ đọc hoặc chuyển tiếp API; xác định hợp đồng OpenAPI, ID và lỗi. Mỗi bảng PostgreSQL có một bên ghi duy nhất. Chuyển mutation một module mỗi lần với kiểm thử dữ liệu, role, audit và rollback. Auth phải giữ tương thích session trước khi chuyển đăng nhập.
4. **Hàng đợi và realtime.** Chỉ khi API submission mới đạt parity, mới thử BullMQ cho dispatch; có idempotency, retry, dead letter, thứ tự và đối chiếu kết quả với Judge Manager. Chuyển WebSocket sau khi chứng minh không mất bản tin trạng thái và vẫn kiểm soát quyền truy cập.
5. **Cắt tuyến và dọn mã cũ.** Dùng Nginx định tuyến có thể quay lại theo module. Backup PostgreSQL/MinIO, diễn tập restore, chạy canary, quan sát lỗi và xác nhận parity trước mỗi lần cắt. Chỉ xóa mã cũ sau thời gian ổn định và khi không còn tuyến hoặc dữ liệu phụ thuộc.

## Giai đoạn 1: cách chạy và quay lại

Trong Docker Compose, đặt `AI_SIMILARITY_TOKEN` là chuỗi bí mật riêng và `AI_SIMILARITY_URL=http://ai-similarity:8010` trong `.env`, rồi build/chạy `ai-similarity` và khởi động lại `anti-cheat-worker`. Dịch vụ chỉ nằm trên mạng Compose, không mở cổng public. Khi bỏ trống URL và khởi động lại worker, luồng so khớp cục bộ hoạt động như trước. Trên Windows chạy trực tiếp: đặt cùng token và URL trỏ tới FastAPI, khởi động `uvicorn main:app` từ `apps/ai-similarity` với `PYTHONPATH` trỏ về thư mục repository.

Không gửi mã nguồn tới dịch vụ bên ngoài mạng tin cậy. Hạn chế quyền đọc log và kết quả so khớp theo role quản trị kỳ thi hiện có. Cặp có điểm cao vẫn cần người duyệt và cơ chế khiếu nại hiện tại.
