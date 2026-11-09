# Terminal quản trị nội dung và chat

Chạy từ thư mục gốc dự án bằng tài khoản có quyền truy cập máy chủ và cơ sở dữ liệu. `--user` phải là username của một tài khoản Django đang hoạt động và có quyền staff.

Trong PowerShell, cài lệnh ngắn một lần:

```powershell
.\scripts\install-codepro-command.ps1
. $PROFILE.CurrentUserAllHosts
codepro
```

Gõ `codepro` từ bất kỳ thư mục nào; công cụ tự chạy trong project và trả terminal về thư mục ban đầu khi thoát. Nếu chỉ có một tài khoản staff đang hoạt động, giao diện mở ngay; nếu có nhiều tài khoản, nhập tên tài khoản hoặc dùng `codepro --user admin`. Có thể chạy một lệnh như `codepro status`. Script cài lệnh cho PowerShell, PowerShell trong VS Code và CMD của tài khoản Windows hiện tại. Sau khi cài, hãy mở terminal mới để PATH trong CMD được cập nhật. Sau khi clone project ở chỗ khác, chạy lại script cài đặt để cập nhật đường dẫn.

```powershell
python manage.py site_terminal --user admin
```

Gõ `help` để xem lệnh. Phiên tương tác hỗ trợ:

Giao diện tương tác có khung chào, dấu nhắc `›` và phần phản hồi theo kiểu hội thoại. Gõ lệnh với dấu `/` như `/status`, `/server status`, `/chats`, `/help`; cách gõ cũ không có dấu `/` vẫn hoạt động. `/clear` dọn màn hình. Có thể gõ câu mô tả để nhận gợi ý lệnh, rồi tự chọn lệnh cần chạy. Giao diện này chỉ điều khiển các chức năng quản trị đã cho phép và không kết nối AI.

```text
status
posts
show-post 12
edit-post 12 content C:\temp\new-body.txt
edit-post 12 title C:\temp\new-title.txt
chats
read 4
send username "Xin chào, chúng tôi đã nhận yêu cầu của bạn."
quit
```

## Chạy và quan sát server cục bộ

Tại dấu nhắc `site>`:

```text
server start              # Django API + web gateway
server start all          # Thêm Judge Manager + anti-cheat worker
server start judge        # Chạy riêng một dịch vụ
server status             # Health, PID, RAM, nguồn tiến trình
status                    # Dịch vụ, CPU/RAM, hàng đợi chấm và bài nộp
activity 10               # Bài nộp và job chấm gần đây
monitor 3                 # Cập nhật trạng thái mỗi 3 giây; Ctrl+C để thoát
server logs api 50        # 50 dòng log cuối của dịch vụ do terminal khởi chạy
server stop api           # Chỉ dừng tiến trình do terminal khởi chạy
server restart api        # Khởi động lại API do codepro quản lý
server restart            # Khởi động lại API và web
```

## Tệp, Git và gợi ý lệnh

Tất cả đường dẫn của `file`, `open` và `git add` phải là tệp nằm trong project. Đặt đường dẫn có khoảng trắng trong dấu nháy kép. `open` mở tệp bằng VS Code; `file` chỉ xem tối đa 200 dòng UTF-8 trong terminal.

```text
file README.md 30
open docs/development/site-terminal.md
git status
git diff
git staged
git log 5
git branch
git add README.md
git commit "Cập nhật tài liệu"
git pull
git push
suggest "khởi động lại server"
```

Có thể gõ `/github` hoặc `/gh` thay cho `/git`. `git pull` chỉ dùng fast-forward và yêu cầu cây làm việc sạch; `git push` đẩy nhánh hiện tại lên `origin`. Các lệnh Git được giới hạn trong danh sách trên, không thực thi lệnh shell tùy ý. Gõ một yêu cầu chưa nhận diện sẽ hiện gợi ý; gợi ý chỉ đề xuất lệnh, không tự chạy hoặc gửi nội dung lên dịch vụ AI.

`server start` mặc định chỉ khởi động API và gateway. `server start all` chạy thêm máy chấm và worker chống gian lận khi môi trường cục bộ đã được cấu hình. Nếu dịch vụ đã chạy, lệnh báo PID và không mở thêm tiến trình. Dịch vụ có nhãn `external` là tiến trình được khởi chạy ngoài terminal này; lệnh `server stop` không dừng chúng. Log của tiến trình do terminal khởi chạy nằm tại `storage/temp/site-terminal/` và không được commit. Công cụ này quản lý dịch vụ phát triển cục bộ; bản Docker/production dùng cơ chế quản lý dịch vụ riêng.

Có thể chạy một lệnh rồi thoát, ví dụ `python manage.py site_terminal --user admin status`. Nội dung sửa bài viết được đọc từ tệp UTF-8 tối đa 1 MB. Việc sửa bài viết được ghi vào Django admin log. Tin nhắn lưu trong hệ thống chat hiện có và tạo thông báo cho người nhận. Lệnh `read` chỉ cho xem hội thoại có tài khoản staff đã chọn tham gia. Công cụ không chạy lệnh shell và không mở terminal qua web.
