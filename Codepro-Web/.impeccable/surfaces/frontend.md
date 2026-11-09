---
version: 1
slug: "frontend"
primary_target: "frontend"
related_targets: []
---

# Direction contract: Codepro-Web (operate)

Scope: giao diện làm bài, bảng xếp hạng kỳ thi và khu vực quản trị của toàn bộ website. Chế độ: Operate.

THESIS: Bảng thủy triều của cuộc thi: mỗi bài là một điểm trên hải đồ, thứ hạng là dòng nước đang dâng. Tránh khuôn mẫu "bảng xếp hạng xám với một màu nhấn".

OWN-WORLD: Nền sáng xanh hải đồ nhạt, mực xanh đậm, đường đẳng sâu mảnh, số tabular cho điểm và thứ hạng, một màu cảnh báo duy nhất cho thay đổi. Không dùng ký hiệu la bàn hay trang trí trên màn làm việc.

STORY: Thí sinh biết ngay mình đứng ở đâu trên bảng, bài nào đang thay đổi thứ hạng, và việc tiếp theo là nộp bài nào.

FIRST VIEWPORT: Thanh điều hướng ngang phía trên (trên mobile gập vào nút menu), giữ chức năng chuẩn. Vùng chính: bảng xếp hạng kỳ thi với cột thứ hạng, thí sinh, điểm, bài đã giải. Dòng vừa đổi vị trí giữ màu cảnh báo cho tới khi được xem. Nút hành động chính (Nộp bài) nằm góc trên phải.

FORM: Hải đồ/bảng thủy triều, vị trí 3 trong danh sách; SEED REFERENCE seed:6c3ff50c7f4ade59. Raise từ "split-flap concourse": dòng đổi vị trí tại chỗ, giữ trạng thái cho tới khi người dùng nhận ra.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.
