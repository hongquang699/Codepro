import os
import sys
import django

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from backend.judge.models import Profile, User
from backend.community.models import (
    ForumCategory, Post, Thread, ThreadPost, Group, GroupMember, Comment
)

def seed():
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    admin_prof = admin_user.profile if admin_user else None

    # 1. Forum Categories
    cats = [
        {"name": "Competitive Programming", "slug": "competitive-programming", "description": "Chia sẻ kinh nghiệm, chiến thuật thi đấu VNOI, VOI, ICPC và Codeforces.", "icon": "trophy", "order": 1},
        {"name": "Thuật toán & Cấu trúc dữ liệu", "slug": "algorithms", "description": "Thảo luận về Graph, DP, Segment Tree, Trie, Flow và các cấu trúc nâng cao.", "icon": "cpu", "order": 2},
        {"name": "C++ & Modern C++", "slug": "cpp", "description": "Tối ưu hóa I/O, STL tricks, PBDS, Bitset và GCC builtins trong thi đấu.", "icon": "code", "order": 3},
        {"name": "Python for CP", "slug": "python", "description": "Kỹ thuật tối ưu tốc độ Python, thư viện chuẩn và giải thuật với PyPy3.", "icon": "terminal", "order": 4},
        {"name": "Thảo luận Đề bài & Editorial", "slug": "problem-discussion", "description": "Hỏi đáp hướng giải, mẹo giải quyết edge case cho các bài tập trên OJ.", "icon": "help-circle", "order": 5},
        {"name": "Kỳ thi & Cuộc thi sắp tới", "slug": "contests", "description": "Thông báo, thảo luận trước và sau các vòng thi VNOI Cup, Codeforces rounds.", "icon": "calendar", "order": 6},
        {"name": "Công nghệ & Đời sống Lập trình", "slug": "general", "description": "Giao lưu, hỏi đáp học tập, phỏng vấn và định hướng nghề nghiệp tech.", "icon": "coffee", "order": 7},
    ]

    for c in cats:
        obj, created = ForumCategory.objects.get_or_create(
            slug=c["slug"],
            defaults=c
        )
        if created:
            print(f"Created category: {obj.name}")

    if admin_prof:
        # 2. Seed Initial Posts
        posts_data = [
            {
                "title": "Bí kíp tối ưu I/O và cấu trúc dữ liệu trong C++ chuẩn thi VNOI / ICPC",
                "slug": "bi-kip-toi-uu-io-cpp-vnoi",
                "summary": "Tổng hợp các kỹ thuật cin.tie(0), Fast I/O và Policy-Based Data Structures (PBDS) giúp code chạy nhanh như gió.",
                "content": """## Bí kíp tối ưu I/O C++ cho Lập Trình Thi Đấu

Khi thi đấu lập trình, việc đọc/ghi dữ liệu lớn (lên tới $10^6$ số nguyên) thường chiếm nhiều thời gian và dễ dẫn tới lỗi **Time Limit Exceeded (TLE)**. Dưới đây là các kỹ thuật chuẩn:

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int n;
    if (cin >> n) {
        cout << "Ready for VNOI Contest: " << n << "\\n";
    }
    return 0;
}
```

### 1. Tránh sử dụng `endl`
Luôn dùng `\\n` thay vì `endl` vì `endl` tự động xả bộ đệm (flush buffer), làm chậm chương trình gấp 10 lần.

### 2. Sử dụng Ordered Set (PBDS)
Hỗ trợ tìm phần tử thứ $k$ và đếm số phần tử nhỏ hơn trong $O(\\log N)$.
""",
                "tags": ["cpp", "algorithms", "optimization", "vnoi"],
                "is_pinned": True,
                "like_count": 24,
                "view_count": 312
            },
            {
                "title": "Editorial & Hướng dẫn giải bài SUMA (Tổng hai số)",
                "slug": "editorial-suma-vnoi",
                "summary": "Phân tích độ phức tạp thời gian O(1), xử lý số nguyên 64-bit và các trường hợp tràn số.",
                "content": """## Phân tích bài toán SUMA

Bài toán yêu cầu tính tổng $A + B$.
- **Giới hạn:** $|A|, |B| \\le 10^9$.
- **Độ phức tạp tối ưu:** $O(1)$ thời gian, $O(1)$ bộ nhớ.

```python
import sys
a, b = map(int, sys.stdin.read().split())
print(a + b)
```
""",
                "tags": ["editorial", "suma", "math"],
                "is_pinned": False,
                "like_count": 15,
                "view_count": 189
            }
        ]

        for p in posts_data:
            p_obj, created = Post.objects.get_or_create(
                slug=p["slug"],
                defaults={
                    "author": admin_prof,
                    "title": p["title"],
                    "summary": p["summary"],
                    "content": p["content"],
                    "tags": p["tags"],
                    "is_pinned": p["is_pinned"],
                    "like_count": p["like_count"],
                    "view_count": p["view_count"]
                }
            )
            if created:
                print(f"Created post: {p_obj.title}")
                # Add sample comment
                Comment.objects.create(
                    post=p_obj,
                    author=admin_prof,
                    content="Bài viết rất hữu ích cho các bạn mới bắt đầu luyện thi ICPC!"
                )

        # 3. Seed Initial Thread
        cp_cat = ForumCategory.objects.filter(slug="competitive-programming").first()
        if cp_cat:
            t_obj, created = Thread.objects.get_or_create(
                category=cp_cat,
                title="Lộ trình luyện tập thuật toán từ Newbie lên Master trong 6 tháng",
                defaults={
                    "author": admin_prof,
                    "content": "Chia sẻ kinh nghiệm phân phối thời gian luyện tập theo chuyên đề: Binary Search, Two Pointers, Graph traversal, Tree & DP.",
                    "is_pinned": True,
                    "reply_count": 1,
                    "view_count": 420
                }
            )
            if created:
                ThreadPost.objects.create(
                    thread=t_obj,
                    author=admin_prof,
                    content="Nên bắt đầu với các bài tập cơ bản ở mục Problems trước, nộp thử bài SUMA và KNAPSACK để làm quen với hệ thống máy chấm."
                )
                print(f"Created thread: {t_obj.title}")

        # 4. Seed Initial Group
        legacy_group = Group.objects.filter(slug='vnoi-olympiad-club').first()
        if legacy_group and not Group.objects.filter(slug='codeprooj-olympiad-club').exists():
            legacy_group.slug = 'codeprooj-olympiad-club'
            legacy_group.name = 'CodeProOJ Olympiad Club'
            legacy_group.save(update_fields=['slug', 'name'])
        g_obj, created = Group.objects.get_or_create(
            slug="codeprooj-olympiad-club",
            defaults={
                "name": "CodeProOJ Olympiad Club",
                "description": "Nơi quy tụ các bạn học sinh sinh viên đam mê lập trình giải thuật trên cả nước.",
                "owner": admin_prof,
                "member_count": 128
            }
        )
        if created:
            GroupMember.objects.get_or_create(group=g_obj, user=admin_prof, defaults={"role": "owner"})
            print(f"Created group: {g_obj.name}")

    print("Seed community data completed successfully!")

if __name__ == "__main__":
    seed()
