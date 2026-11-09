import os
import sys
import django
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from backend.judge.models import Contest, ContestProblem, Problem, Profile, Language, Submission

admin_user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.invalid'})
admin_prof, _ = Profile.objects.get_or_create(user=admin_user)
cpp_lang, _ = Language.objects.get_or_create(key='CPP17', defaults={'name': 'C++17 (GNU G++)', 'extension': 'cpp'})

now = timezone.now()
start = now - timedelta(hours=1)
end = now + timedelta(hours=5)

contest, created = Contest.objects.get_or_create(
    key='hsg-tin-2026',
    defaults={
        'name': 'HSG TIN HỌC 2026',
        'description': 'Kỳ thi chọn Học sinh giỏi Tin học Quốc gia 2026. Bảng thi chính thức hệ thống CodeProOJ.',
        'start_time': start,
        'end_time': end,
        'time_limit': 18000,
        'is_rated': True,
        'is_visible': True,
        'format_name': 'ioi'
    }
)
if not created:
    contest.start_time = start
    contest.end_time = end
    contest.name = 'HSG TIN HỌC 2026'
    contest.save()

problems_data = [
    {
        'code': 'SUMA',
        'name': 'Tổng hai số',
        'prefix': 'A',
        'order': 1,
        'points': 100.0,
        'time_limit': 1.0,
        'memory_limit': 256,
        'description': r"""Cho hai số nguyên $A$ và $B$. Nhiệm vụ của bạn là tính tổng của hai số này và in ra kết quả.

### Đầu vào
- Dòng duy nhất chứa hai số nguyên $A$ và $B$ cách nhau bởi dấu cách.

### Đầu ra
- In ra một số nguyên duy nhất là tổng $A + B$.

### Giới hạn
- $0 \le |A|, |B| \le 10^9$ trong 60% số test.
- $0 \le |A|, |B| \le 10^{18}$ trong 40% số test còn lại.

### Ví dụ
| Đầu vào | Đầu ra |
|:---|:---|
| `2 3` | `5` |
| `-5 10` | `5` |
"""
    },
    {
        'code': 'SUBSEQ',
        'name': 'Dãy con tăng dài nhất',
        'prefix': 'B',
        'order': 2,
        'points': 100.0,
        'time_limit': 1.0,
        'memory_limit': 256,
        'description': r"""Cho dãy số nguyên gồm $N$ phần tử $A_1, A_2, \dots, A_N$. Hãy tìm độ dài của dãy con tăng nghiêm ngặt dài nhất.

Một dãy con là dãy thu được bằng cách xóa bớt một số (hoặc không xóa) phần tử mà vẫn giữ nguyên thứ tự tương đối.

### Đầu vào
- Dòng đầu tiên chứa số nguyên dương $N$.
- Dòng thứ hai chứa $N$ số nguyên $A_1, A_2, \dots, A_N$.

### Đầu ra
- In ra một số nguyên duy nhất là độ dài dãy con tăng dài nhất.

### Giới hạn
- $1 \le N \le 10^3$ trong 50% số điểm.
- $1 \le N \le 2 \times 10^5$ trong 50% số điểm còn lại.
- $|A_i| \le 10^9$.

### Ví dụ
| Đầu vào | Đầu ra |
|:---|:---|
| `6`<br>`1 2 5 3 4 9` | `5` |
"""
    },
    {
        'code': 'PATH',
        'name': 'Đường đi ngắn nhất',
        'prefix': 'C',
        'order': 3,
        'points': 100.0,
        'time_limit': 1.5,
        'memory_limit': 512,
        'description': r"""Cho đồ thị có hướng gồm $N$ đỉnh và $M$ cạnh có trọng số dương. Hãy tìm độ dài đường đi ngắn nhất từ đỉnh $1$ đến đỉnh $N$.

### Đầu vào
- Dòng đầu tiên chứa hai số nguyên $N$ và $M$.
- $M$ dòng tiếp theo, mỗi dòng gồm ba số nguyên $u, v, w$ mô tả cạnh một chiều từ $u$ đến $v$ có trọng số $w$.

### Đầu ra
- In ra một số nguyên duy nhất là khoảng cách ngắn nhất từ đỉnh $1$ tới đỉnh $N$. Nếu không có đường đi, in ra $-1$.

### Giới hạn
- $1 \le N \le 10^5$.
- $1 \le M \le 2 \times 10^5$.
- $1 \le w \le 10^9$.

### Ví dụ
| Đầu vào | Đầu ra |
|:---|:---|
| `4 4`<br>`1 2 2`<br>`2 4 3`<br>`1 3 1`<br>`3 4 5` | `5` |
"""
    },
    {
        'code': 'TREE',
        'name': 'Đường kính cây',
        'prefix': 'D',
        'order': 4,
        'points': 100.0,
        'time_limit': 1.0,
        'memory_limit': 256,
        'description': r"""Cho một cây gồm $N$ đỉnh đánh số từ $1$ đến $N$. Hãy tìm đường kính của cây, tức là khoảng cách xa nhất giữa hai đỉnh bất kỳ trên cây (số cạnh trên đường đi).

### Đầu vào
- Dòng đầu tiên chứa số nguyên dương $N$.
- $N - 1$ dòng tiếp theo, mỗi dòng chứa hai số nguyên $u$ và $v$ mô tả một cạnh nối giữa đỉnh $u$ và $v$.

### Đầu ra
- In ra một số nguyên duy nhất là đường kính của cây.

### Giới hạn
- $1 \le N \le 2 \times 10^5$.

### Ví dụ
| Đầu vào | Đầu ra |
|:---|:---|
| `5`<br>`1 2`<br>`1 3`<br>`3 4`<br>`3 5` | `3` |
"""
    }
]

for pdata in problems_data:
    prob, _ = Problem.objects.get_or_create(
        code=pdata['code'],
        defaults={
            'name': pdata['name'],
            'description': pdata['description'],
            'time_limit': pdata['time_limit'],
            'memory_limit': pdata['memory_limit'],
            'points': pdata['points'],
            'is_public': True
        }
    )
    prob.name = pdata['name']
    prob.description = pdata['description']
    prob.save()

    cp, _ = ContestProblem.objects.get_or_create(
        contest=contest,
        problem=prob,
        defaults={
            'output_prefix': pdata['prefix'],
            'order': pdata['order'],
            'points': pdata['points']
        }
    )
    cp.output_prefix = pdata['prefix']
    cp.order = pdata['order']
    cp.points = pdata['points']
    cp.save()

print("Seeded contest:", contest.key, contest.name)
print("Problems count:", ContestProblem.objects.filter(contest=contest).count())
