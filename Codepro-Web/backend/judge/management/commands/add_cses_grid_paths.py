"""Install the hidden CSES Grid Paths I practice problem and deterministic tests."""

from pathlib import Path
import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.judge.models import Problem, ProblemType
from backend.judge import problem_package


CODE = 'CSES1638'
SOURCE = 'https://cses.fi/problemset/task/1638/'
STATEMENT = """# Đường đi trên lưới

Một tấm bảng vuông có một số ô bị chặn. Hãy đếm số cách đi từ ô góc trên bên trái đến ô góc dưới bên phải. Mỗi bước chỉ được sang phải hoặc xuống dưới, và không được đi vào ô bị chặn.

## Dữ liệu vào

Dòng đầu chứa số nguyên $n$. Tiếp theo là $n$ dòng, mỗi dòng gồm đúng $n$ ký tự: `.` là ô trống, `*` là ô bị chặn.

## Dữ liệu ra

In số đường đi, lấy phần dư khi chia cho $10^9+7$. Nếu ô đầu hoặc ô cuối bị chặn, kết quả là `0`.

## Giới hạn

- $1 \\le n \\le 1000$.
- Thời gian: 2 giây; bộ nhớ: 256 MB.

## Ví dụ

Input:
```
4
....
.*..
...*
*...
```

Output:
```
3
```

Nguồn ý tưởng: [CSES — Grid Paths I](https://cses.fi/problemset/task/1638/). Đề tiếng Việt được biên soạn lại.
"""
SOLUTION = """MOD = 1_000_000_007
n = int(input())
dp = [0] * n
for r in range(n):
    row = input().strip()
    for c, cell in enumerate(row):
        if cell == '*':
            dp[c] = 0
        elif r == 0 and c == 0:
            dp[c] = 1
        elif c:
            dp[c] = (dp[c] + dp[c - 1]) % MOD
print(dp[-1])
"""


def answer(grid):
    n = len(grid)
    dp = [0] * n
    for row_index, row in enumerate(grid):
        for col, cell in enumerate(row):
            if cell == '*':
                dp[col] = 0
            elif row_index == 0 and col == 0:
                dp[col] = 1
            elif col:
                dp[col] = (dp[col] + dp[col - 1]) % 1_000_000_007
    return dp[-1]


def cases():
    fixed = [
        ['.'], ['*'], ['..', '..'], ['*.', '..'], ['..', '.*'],
        ['...', '***', '...'], ['...', '.*.', '...'],
        ['....', '.*..', '...*', '*...'],
        ['.....', '.*.*.', '.....', '.*.*.', '.....'],
    ]
    for grid in fixed:
        yield grid
    rng = random.Random(1638)
    for n, density in [(10, 0), (20, .15), (50, .3), (100, .2),
                       (250, .28), (500, .1), (1000, 0), (1000, .3)]:
        grid = [''.join('*' if rng.random() < density else '.' for _ in range(n))
                for _ in range(n)]
        yield grid


class Command(BaseCommand):
    help = 'Add hidden CSES Grid Paths I with a complete standard-checker test set'

    def handle(self, *args, **options):
        if Problem.objects.filter(code=CODE).exists():
            raise CommandError(f'{CODE} already exists; refusing to overwrite it')
        root = Path(problem_package.get_problem_dir(CODE))
        if root.exists():
            raise CommandError(f'{root} already exists; refusing to overwrite it')
        try:
            problem_package.init_package(CODE, {
                'title': 'Đường đi trên lưới (CSES)', 'time_limit': 2,
                'memory_limit': 256, 'points': 100, 'difficulty': 'medium',
                'status': 'ready',
            })
            problem_package.save_statement(CODE, STATEMENT)
            solution_dir = root / 'solutions'
            solution_dir.mkdir(exist_ok=True)
            (solution_dir / 'official.py').write_text(SOLUTION, encoding='utf-8')
            for index, grid in enumerate(cases(), 1):
                test_input = f'{len(grid)}\n' + '\n'.join(grid) + '\n'
                problem_package.save_testcase(
                    CODE, f'{index:02d}', test_input, f'{answer(grid)}\n',
                    points=100 / 17, sample=index == 8,
                )
            with transaction.atomic():
                problem = Problem.objects.create(
                    code=CODE, name='Đường đi trên lưới (CSES)',
                    description=STATEMENT, time_limit=2, memory_limit=262144,
                    points=100, difficulty='medium', status='ready', is_public=False,
                )
                tag, _ = ProblemType.objects.get_or_create(
                    name='dp', defaults={'full_name': 'Quy hoạch động'})
                problem.types.add(tag)
        except Exception:
            import shutil
            shutil.rmtree(root, ignore_errors=True)
            raise
        self.stdout.write(self.style.SUCCESS(
            f'Added {CODE}: 17 testcases, hidden, source {SOURCE}'))
