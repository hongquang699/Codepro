# Kho đề riêng trên S3/MinIO

Mã ứng dụng và dữ liệu đề được triển khai riêng. Theo cách bố trí của VNOJ, `DMOJ_PROBLEM_DATA_ROOT` trỏ đến thư mục đề/test nằm ngoài checkout. Codepro-Web lưu snapshot riêng tư trên S3/MinIO và cung cấp lệnh tải xuống, kiểm tra SHA-256 trước khi máy web hoặc judge đọc dữ liệu.

Snapshot chứa `problem-data/`, `contest-data/` và `storage/contests/`. Nó không chứa database, bài nộp, khóa mã hóa testcase hay `storage/uploads/`. Sao lưu các thành phần đó riêng. Bucket chứa test phải tắt truy cập công khai và bật versioning/backup của nhà cung cấp.

## Cấu hình

Trong `.env` đặt endpoint, tài khoản S3 có quyền đọc/ghi bucket riêng tư, và đường dẫn tuyệt đối trên máy chủ:

```dotenv
CODEPRO_DATA_ROOT=/srv/codepro-data
PROBLEM_STORAGE_ENDPOINT=https://s3.example.net
PROBLEM_STORAGE_ACCESS_KEY=...
PROBLEM_STORAGE_SECRET_KEY=...
PROBLEM_STORAGE_PRIVATE_BUCKET=problem-private
```

Với MinIO cùng máy có thể dùng `http://127.0.0.1:9000` cho lệnh chạy trực tiếp; container backend dùng endpoint trong mạng Compose. Không đưa khóa, tệp `.env` hoặc snapshot đề lên Git.

## Đưa dữ liệu cũ lên bucket

Chạy trên máy đang có dữ liệu, khi đã dừng thao tác sửa đề/test:

```sh
python manage.py sync_problem_data upload --source /path/to/old/Codepro-Web
```

Lệnh tạo ZIP gồm các tệp, thư mục rỗng và manifest SHA-256; ghi object theo checksum rồi mới cập nhật `codepro-data/v1/latest.json`. Giữ bản sao gốc cho đến khi tải xuống và kiểm tra xong. Bucket riêng tư có thể dùng chung với chức năng versioned problem storage hiện có; các object snapshot nằm dưới prefix `codepro-data/v1/`.

## Tải đề về máy web và judge

Sau khi clone mã ứng dụng và cấu hình `.env`:

```sh
python manage.py sync_problem_data download --destination /srv/codepro-data
```

Thư mục đích phải chưa tồn tại và nằm ngoài checkout. Lệnh xác minh checksum ZIP và từng tệp, từ chối đường dẫn vượt thư mục hoặc symlink, rồi mới đổi tên thư mục tạm thành đích. Nếu tải bản mới, dùng thư mục phiên bản mới, đổi `CODEPRO_DATA_ROOT` và khởi động lại backend/judge. Không ghi đè thư mục đang được máy chấm sử dụng.

Khi chạy trực tiếp thay vì Compose, đặt `DMOJ_PROBLEM_DATA_ROOT`, `DMOJ_CONTEST_DATA_ROOT`, `CODEPRO_CONTEST_PACKAGE_ROOT` và `JUDGE_PROBLEM_DATA_DIR` tới các thư mục tương ứng dưới `CODEPRO_DATA_ROOT`. Compose gắn chúng vào backend và judge; thư mục đề trong judge được gắn chỉ đọc. Cả backend và judge phải dùng cùng `TESTCASE_ENCRYPTION_KEY` để đọc test đã mã hóa.

Các commit Git cũ vẫn còn bản sao dữ liệu đề trong lịch sử. Nếu từng chứa test bí mật, đổi/thu hồi test đã lộ và xử lý lịch sử Git theo một đợt riêng có kế hoạch cho tất cả bản clone.
