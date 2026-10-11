# Deploy CodeProOJ trên VPS bằng Docker Compose

## Cấu trúc thư mục

Clone toàn bộ repository vào `/srv/codeprooj`. Giữ `docker-compose.yml` ở thư mục gốc vì các đường dẫn bind mount được tính từ đây.

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
├── problem-data/                     # testcase, dữ liệu bền vững
├── contest-data/                     # dữ liệu kỳ thi, dữ liệu bền vững
├── storage/                          # upload, bài nộp, dữ liệu bền vững
└── judge-system/logs/                # log judge, dữ liệu bền vững
```

PostgreSQL (`pgdata`) và Redis (`redisdata`) dùng Docker volumes. Django static (`staticfiles`) cũng dùng volume để Nginx trong Compose phục vụ `/static/`; frontend tại `/frontend/` vẫn do gateway Node phục vụ. Các SQL mẫu cũ trong `database/schemas/` không được nạp vào PostgreSQL; schema ứng dụng do Django migrations tạo. Đừng đưa `.env`, whitelist thật, database, testcase riêng hoặc dữ liệu `storage/` vào Git. Việc build image không mang các thư mục dữ liệu bền vững vào image; Compose gắn chúng từ máy chủ.

## Chuẩn bị máy chủ

1. Cài Docker Engine, Compose plugin và reverse proxy HTTPS trên VPS. Trỏ DNS của tên miền về VPS.
2. Clone repository vào `/srv/codeprooj`, rồi chạy `sh scripts/prepare-deploy.sh`. Script chỉ tạo các thư mục và sao chép mẫu khi tệp cấu hình chưa tồn tại; nó không ghi đè dữ liệu cũ. Điền **secret mới, khác nhau**, `DB_PASSWORD`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` và `CODEPRO_HTTP_PORT` trong `.env`. Không dùng giá trị rỗng trong `.env.example` để chạy thật.
3. Điền IP quản trị thật vào `config/admin_ip_whitelist.json`; chép dữ liệu hiện có vào các thư mục `problem-data`, `contest-data`, `storage`, `judge-system/logs` nếu đang chuyển máy. Sao lưu PostgreSQL volume và các thư mục này trước khi cập nhật.
4. Cấp chứng chỉ TLS cho tên miền. Dùng [cấu hình Nginx máy chủ mẫu](../../infrastructure/nginx/host.example.conf), sửa `server_name`, đường dẫn chứng chỉ và cổng nếu cần. Reverse proxy HTTPS trên máy chủ chuyển tiếp tới `127.0.0.1:8080`; Compose không mở trực tiếp API, database, Redis hay Judge Manager ra Internet.

## Khởi động

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

`docker compose down` giữ các named volumes; **không dùng `down -v`** khi cần giữ database và Redis. Khi cập nhật mã, kéo commit mới rồi chạy lại `docker compose up -d --build` và `migrate`. Kiểm tra health và log trước khi mở lưu lượng công khai.

## Giới hạn hiện tại

Image Judge Manager chạy tác vụ thực thi mã thí sinh. Cần kiểm tra chính sách sandbox, quyền hệ điều hành và cách ly máy chấm trước khi nhận bài nộp từ Internet; việc sắp xếp tệp và Compose không thay thế bước này. `storage/` có thể chứa mã nguồn bài nộp nên không được cấu hình Nginx phục vụ trực tiếp toàn bộ thư mục.
