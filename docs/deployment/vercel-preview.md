# Bản xem trước CodeProOJ trên Vercel

Vercel chỉ phục vụ HTML, CSS, JavaScript và ảnh từ `frontend/`. `vercel.json` chạy
`scripts/build-vercel-preview.js` để giữ các đường dẫn `/frontend/...` và tạo
các đường dẫn ngắn như `/`, `/problems`, `/contests` từ bảng tuyến của gateway.
Bản xem trước hiển thị thông báo rằng API và máy chấm chưa hoạt động.

Để liên kết, đăng nhập Vercel, tạo **New Project**, chọn repository
`hongquang699/Codeprooj-online-judge`, giữ **Root Directory** là thư mục gốc
và triển khai. Cấu hình build trong `vercel.json` được áp dụng từ repository.
Vercel sẽ tự triển khai lại khi có commit mới trên nhánh được chọn.

Không nhập secret của Django, PostgreSQL hoặc máy chấm vào Vercel cho bản xem
trước này. Để chạy toàn bộ nền tảng, cần triển khai Docker Compose theo
[hướng dẫn VPS](README.md) trên máy chủ HTTPS công khai, rồi thiết kế cách
định tuyến API, WebSocket và tệp client từ Vercel tới máy chủ đó. Bản `.exe`
trong `frontend/downloads/` không nằm trong Git nên không xuất hiện trên Vercel.
