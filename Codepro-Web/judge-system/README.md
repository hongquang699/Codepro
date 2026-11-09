# CodeProOJ - Standalone Judge System

Hệ thống máy chấm độc lập (Judge System) hiệu năng cao cho hệ thống chấm thi trực tuyến (Online Judge), kiến trúc microservice tách biệt hoàn toàn với Web Backend.

---

## 1. Cấu trúc thư mục (Architecture Overview)

```
judge-system/
├── judge-server/           # Master Server HTTP REST API & điều phối
│   ├── main.py             # Entrypoint server (cổng 9999)
│   ├── config.py           # Bộ đọc cấu hình YAML
│   ├── api.py              # REST API Router
│   ├── authentication.py   # Xác thực Bearer Token
│   └── heartbeat.py        # Quản lý nhịp tim và trạng thái Worker
│
├── dispatcher/             # Hàng đợi và điều phối tải (Load Balancing)
│   ├── queue.py            # Priority Queue đa luồng (hỗ trợ Memory / Redis)
│   ├── scheduler.py        # Thuật toán điều phối (Least Busy, Round Robin)
│   ├── dispatcher.py       # Vòng lặp điều phối chính
│   └── retry.py            # Tự động thử lại khi worker gặp sự cố
│
├── worker/                 # Worker node thực thi
│   ├── worker.py           # Worker daemon lắng nghe & báo cáo kết quả
│   ├── job.py              # Định nghĩa dữ liệu JudgeJob
│   ├── executor.py         # Bộ điều phối quy trình chấm toàn diện
│   ├── compiler.py         # Biên dịch mã nguồn biệt lập
│   ├── runner.py           # Chạy testcase và so khớp output
│   └── result.py           # Định dạng kết quả JudgeResult
│
├── sandbox/                # Môi trường cách ly & kiểm soát tài nguyên
│   ├── sandbox.py          # Unified Sandbox Facade
│   ├── process.py          # Kiểm soát tiến trình, streaming pipe, đo đạc
│   ├── filesystem.py       # Cách ly thư mục làm việc, chống path traversal
│   ├── network.py          # Giám sát và ngắt kết nối mạng trái phép
│   ├── memory.py           # Đo đạc RSS / Working Set đỉnh (KB)
│   ├── cpu.py              # Đo đạc chính xác thời gian CPU (User + Kernel)
│   └── security.py         # Quét mã độc, cấm system calls nguy hiểm
│
├── languages/              # Cấu hình & script chạy 11 ngôn ngữ
│   ├── cpp/                # C++17 (GNU G++)
│   ├── c/                  # C11 (GNU GCC)
│   ├── python/             # Python 3
│   ├── java/               # Java 17 (OpenJDK)
│   ├── rust/               # Rust 2021
│   ├── go/                 # Go 1.22
│   ├── javascript/         # Node.js ES2023
│   ├── typescript/         # TypeScript
│   ├── kotlin/             # Kotlin 1.9
│   ├── csharp/             # C# (.NET 8.0)
│   └── pascal/             # Free Pascal (FPC)
│
├── checker/                # Bộ chấm bài (Checker)
│   ├── checker.py          # Unified Checker Dispatcher
│   ├── standard.py         # Chấm token và chấm từng dòng
│   ├── float.py            # Chấm số thực sai số tuyệt đối/tương đối (epsilon)
│   ├── custom.py           # Trình chấm đặc biệt (Special Judge / Testlib)
│   └── testlib.h           # Thư viện testlib chuẩn CP
│
├── validator/              # Bộ thẩm định testcase đầu vào
│   ├── validator.py        # Unified Validator Dispatcher
│   ├── testlib_validator.py# Validator bằng mã C++ testlib
│   └── regex_validator.py  # Validator theo biểu thức chính quy (Regex)
│
├── testcase/               # Quản lý testcase & Subtask
│   ├── loader.py           # Đọc testcase từ thư mục problem-data (.in / .out / .ans)
│   ├── manager.py          # Điều phối testcase, subtasks
│   ├── subtask.py          # Tính điểm Subtask IOI, phụ thuộc dependencies
│   └── cache.py            # Bộ nhớ đệm LRU cho testcase của các bài toán hot
│
├── judging/                # Lõi quy trình chấm
│   ├── compile.py          # Biên dịch và kiểm tra cú pháp
│   ├── execute.py          # Chạy testcase trong sandbox
│   ├── compare.py          # So sánh kết quả qua checker
│   ├── score.py            # Tính tổng điểm, tỷ lệ % và verdict
│   ├── subtasks.py         # Xử lý chấm theo cụm subtask
│   └── verdict.py          # Bảng mã phán quyết (AC, WA, TLE, MLE, OLE, RE, CE, SE)
│
├── monitoring/             # Giám sát & cảnh báo
│   ├── health.py           # Tải CPU, RAM, dung lượng ổ đĩa
│   ├── metrics.py          # Tỷ lệ AC, thời gian trung bình, số bài đã chấm
│   ├── worker_status.py    # Thống kê tình trạng các Worker
│   └── alerts.py           # Cảnh báo ngưỡng an toàn hệ thống
│
├── config/                 # Cấu hình hệ thống (YAML)
│   ├── judge.yml           # Cấu hình Master Server, cổng, token, đường dẫn
│   ├── workers.yml         # Cấu hình danh sách worker pool & năng lực
│   ├── languages.yml       # Lệnh biên dịch/chạy & hệ số thời gian/bộ nhớ
│   └── limits.yml          # Hạn mức an toàn (CPU, RAM, Output, Source size)
│
├── storage/                # Lưu trữ nội bộ máy chấm
│   ├── submissions/        # Mã nguồn bài nộp
│   ├── testcases/          # Testcase cache
│   ├── executables/        # File nhị phân sinh ra trong quá trình chấm
│   ├── logs/               # Log chi tiết theo từng job
│   └── results/            # Kết quả JSON đã chấm
│
├── logs/                   # Nhật ký hoạt động máy chủ & worker
│   ├── judge-server.log
│   ├── worker-1.log
│   ├── worker-2.log
│   └── dispatcher.log
│
├── tests/                  # Bộ kiểm thử tự động (Unit Tests)
│   ├── test_compile.py     # Test biên dịch C++/Python
│   ├── test_runner.py      # Test sandbox, TLE, RE
│   ├── test_checker.py     # Test token, float, checker
│   └── test_subtasks.py    # Test logic điểm subtask và phụ thuộc
│
├── scripts/                # Script khởi động & bảo trì
│   ├── install.sh          # Cài đặt trình biên dịch & thư viện (Linux)
│   ├── start.sh            # Khởi động Master Server nền
│   ├── stop.sh             # Dừng Master Server
│   ├── healthcheck.sh      # Kiểm tra sức khỏe máy chấm
│   └── start.bat           # Khởi động nhanh trên Windows
│
├── Dockerfile              # Docker image đa ngôn ngữ
├── docker-compose.yml      # Cụm container Server + Worker
└── README.md
```

---

## 2. Các phán quyết (Verdicts)

| Ký hiệu | Ý nghĩa | Tiếng Việt | Ưu tiên |
|:---:|:---|:---|:---:|
| **AC** | Accepted | Kết quả chính xác hoàn toàn | 10 |
| **WA** | Wrong Answer | Kết quả đầu ra không khớp | 40 |
| **OLE**| Output Limit Exceeded | Đầu ra vượt quá giới hạn dung lượng (32MB) | 50 |
| **TLE**| Time Limit Exceeded | Quá thời gian quy định | 60 |
| **MLE**| Memory Limit Exceeded | Vượt giới hạn bộ nhớ | 70 |
| **RE** | Runtime Error | Lỗi thực thi (chia cho 0, segfault, exit code khác 0) | 80 |
| **CE** | Compilation Error | Lỗi biên dịch cú pháp | 100 |
| **SE** | System Error | Lỗi hệ thống máy chấm (thiếu testcase, v.v.) | 90 |

---

## 3. API Endpoints (Master Judge Server - Port 9999)

Tất cả các API được bảo vệ bằng Header:
`Authorization: Bearer <JUDGE_AUTH_TOKEN>`

### 3.1. Đẩy bài vào hàng đợi chấm
`POST /api/v1/submissions`
```json
{
  "submission_id": "sub_101",
  "problem_code": "MAXSUM",
  "language": "cpp",
  "source_code": "#include <iostream>\nusing namespace std;\nint main() { long long a, b; if (cin >> a >> b) cout << a + b << endl; return 0; }",
  "time_limit": 1.0,
  "memory_limit": 256,
  "checker_type": "standard",
  "priority": 1
}
```

### 3.2. Xem trạng thái bài nộp
`GET /api/v1/submissions/{id}`

### 3.3. Kiểm tra sức khỏe máy chấm
`GET /api/v1/health`
```json
{
  "status": "healthy",
  "timestamp": 1774911000.0,
  "queue_size": 0,
  "completed_results": 15
}
```

### 3.4. Quản lý Worker Nodes
`GET /api/v1/workers`

---

## 4. Hướng dẫn chạy hệ thống

### Cách 1: Chạy trực tiếp trên Windows / Linux
```bash
# Cài đặt thư viện Python phụ trợ
pip install psutil pyyaml

# Chạy Master Judge Server (Tự động khởi tạo 2 embedded worker nodes)
python judge-server/main.py
```
Hoặc trên Windows chạy file `scripts/start.bat`.

### Cách 2: Chạy kiểm thử tự động (Unit Tests)
```bash
python -m unittest discover -s tests
```

### Cách 3: Chạy bằng Docker Compose
```bash
docker-compose up -d
```
