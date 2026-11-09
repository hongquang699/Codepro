# Deploy CodeProOJ trên VPS bằng Docker Compose

## Cấu trúc thư mục

Clone mã ứng dụng vào `/srv/codeprooj`. Tải kho đề từ S3/MinIO vào `/srv/codepro-data`, nằm ngoài checkout. Giữ `docker-compose.yml` ở thư mục gốc vì các đường dẫn bind mount được tính từ đây.

```text
/srv/codeprooj/
├── docker-compose.yml
├── .env                              # cấu hình thật, không commit
├── config/admin_ip_whitelist.json    # IP admin thật, không commit
├── frontend/                         # HTML/CSS/JS, được build vào image Node
├── apps/web/                         # gateway Node
├── backend/                          # Django API, được build vào image Gunicorn
├── judge-system/                     # Judge Manager
├── infrastructure/                   # Dockerfiles, Nginx trong container
├── storage/                          # upload, bài nộp, dữ liệu bền vững
└── judge-system/logs/                # log judge, dữ liệu bền vững

/srv/codepro-data/
├── problem-data/                     # gói đề và testcase tải từ S3
├── contest-data/                     # dữ liệu kỳ thi tải từ S3
└── storage/contests/                 # gói đề theo kỳ thi tải từ S3
```

PostgreSQL (`pgdata`) và Redis (`redisdata`) dùng Docker volumes. Django static (`staticfiles`) cũng dùng volume để Nginx trong Compose phục vụ `/static/`; frontend tại `/frontend/` vẫn do gateway Node phục vụ. Các SQL mẫu cũ trong `database/schemas/` không được nạp vào PostgreSQL; schema ứng dụng do Django migrations tạo. Đừng đưa `.env`, whitelist thật, database, testcase riêng hoặc dữ liệu `storage/` vào Git. Việc build image không mang các thư mục dữ liệu bền vững vào image; Compose gắn chúng từ máy chủ.

## Chuẩn bị máy chủ

1. Cài Docker Engine, Compose plugin và reverse proxy HTTPS trên VPS. Trỏ DNS của tên miền về VPS.
2. Clone repository vào `/srv/codeprooj`, rồi chạy `sh scripts/prepare-deploy.sh`. Script chỉ tạo các thư mục vận hành và sao chép mẫu khi tệp cấu hình chưa tồn tại; nó không ghi đè dữ liệu cũ. Điền **secret mới, khác nhau**, `DB_PASSWORD`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` và `CODEPRO_HTTP_PORT` trong `.env`. Không dùng giá trị rỗng trong `.env.example` để chạy thật.
3. Điền IP quản trị thật vào `config/admin_ip_whitelist.json`; cấu hình `CODEPRO_DATA_ROOT=/srv/codepro-data` và thông tin bucket riêng tư, rồi chạy lệnh tải ở [hướng dẫn kho đề](problem-data.md). Sao lưu PostgreSQL volume, bucket S3 và các thư mục `storage`, `judge-system/logs` trước khi cập nhật.
4. Cấp chứng chỉ TLS cho tên miền. Dùng [cấu hình Nginx máy chủ mẫu](../../infrastructure/nginx/host.example.conf), sửa `server_name`, đường dẫn chứng chỉ và cổng nếu cần. Reverse proxy HTTPS trên máy chủ chuyển tiếp tới `127.0.0.1:8080`; Compose không mở trực tiếp API, database, Redis hay Judge Manager ra Internet.

## Khởi động

### Mã hóa khi truyền và khi lưu testcase

Reverse proxy ở `infrastructure/nginx/host.example.conf` chuyển HTTP sang HTTPS, chỉ cho phép TLS 1.2/1.3 và gửi HSTS trên phản hồi HTTPS. Cài chứng chỉ hợp lệ trước khi đưa dịch vụ ra Internet. Cổng HTTP nội bộ `127.0.0.1:8080` chỉ dành cho reverse proxy; không công bố cổng này ra ngoài.

Đặt `TESTCASE_ENCRYPTION_KEY` trong `.env` thành 32 byte ngẫu nhiên mã hóa base64, ví dụ tạo bằng `python -c "import base64,secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())"`. Giữ khóa ở nơi lưu bí mật và sao lưu riêng; mất khóa sẽ không đọc được testcase đã mã hóa. Backend và máy chấm phải dùng cùng khóa. File testcase mới (`.in`, `.out`, `.ans`) được mã hóa AES-256-GCM khi ghi; máy chấm giải mã trong bộ nhớ. File cũ vẫn đọc được cho đến khi chuyển đổi.

Sau khi sao lưu kho đề ngoài checkout, chạy thử `python scripts/encrypt_testcases.py /srv/codepro-data/problem-data/problems` và `python scripts/encrypt_testcases.py /srv/codepro-data/storage/contests`, rồi chạy lại cả hai lệnh với `--apply` và cùng biến môi trường khóa. Chạy lệnh chuyển đổi khi đã dừng thao tác soạn đề để tránh ghi đồng thời. Khôi phục dữ liệu phải đi kèm đúng khóa. Mã hóa tập tin không thay thế việc phân quyền thư mục, sao lưu và giới hạn quyền API. Testcase từng được commit vào Git vẫn tồn tại ở lịch sử Git sau chuyển đổi; cần xử lý riêng lịch sử và bản sao lưu nếu chúng chứa dữ liệu bí mật.

Chạy tại `/srv/codeprooj`:

```sh
docker compose config --quiet
docker compose build
docker compose up -d postgres redis
docker compose run --rm backend python manage.py migrate
docker compose up -d
docker compose ps
```

Backend tự chạy `collectstatic` khi khởi động. Chỉ chạy `createsuperuser` khi cần tạo tài khoản quản trị mới. Kiểm tra `https://codeprooj.com/`, `/problems`, `/api/v2/problems` và tệp `/static/admin/css/base.css`. Với tên miền khác, thay `codeprooj.com` trong `.env` và cấu hình Nginx máy chủ.

Gateway cung cấp WebSocket `/ws/live` để báo thay đổi cuộc thi, bài tập và bài nộp giữa web và client. Cả Nginx trong Compose và Nginx máy chủ phải chuyển tiếp `Upgrade`/`Connection`; các mẫu cấu hình trong repository đã có phần này. Kênh chỉ gửi tín hiệu làm mới, không gửi dữ liệu tài khoản hoặc mã nguồn. Trạng thái chấm bài do worker cập nhật trực tiếp vẫn dùng API polling hiện có. Bộ phát sự kiện nằm trong một tiến trình gateway; nếu chạy nhiều gateway, cần thêm Redis pub/sub trước khi cân bằng tải.

`docker compose down` giữ các named volumes; **không dùng `down -v`** khi cần giữ database và Redis. Khi cập nhật mã, kéo commit mới rồi chạy lại `docker compose up -d --build` và `migrate`. Kiểm tra health và log trước khi mở lưu lượng công khai.

## Giới hạn hiện tại

Image Judge Manager chạy tác vụ thực thi mã thí sinh. Cần kiểm tra chính sách sandbox, quyền hệ điều hành và cách ly máy chấm trước khi nhận bài nộp từ Internet; việc sắp xếp tệp và Compose không thay thế bước này. `storage/` có thể chứa mã nguồn bài nộp nên không được cấu hình Nginx phục vụ trực tiếp toàn bộ thư mục.
