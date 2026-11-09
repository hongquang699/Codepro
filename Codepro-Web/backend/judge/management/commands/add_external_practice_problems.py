"""Install hidden tasks adapted from VNOI, Codeforces, and AtCoder."""

import random
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.judge import problem_package as pkg
from backend.judge.models import Problem, ProblemType


PROBLEMS = {
    'VNOIAMSSEQ': {
        'name': 'Dãy số và bước nhảy (VNOI)',
        'source': 'https://oj.vnoi.info/problem/amsseq',
        'difficulty': 'medium', 'tag': 'dp', 'limit': 2,
        'statement': """# Dãy số và bước nhảy

Bạn đứng ở ô số 0 với 0 điểm. Bên phải là N ô mang giá trị a[1], ..., a[N]. Mỗi bước, bạn nhảy sang phải từ 1 đến K ô và cộng giá trị của ô vừa tới vào điểm. Bạn có thể dừng bất cứ lúc nào, kể cả khi chưa nhảy. Hãy tìm điểm lớn nhất có thể đạt.

## Dữ liệu vào
Dòng đầu gồm N và K. Dòng sau gồm N số nguyên a[i].

## Dữ liệu ra
In ra một số nguyên: điểm lớn nhất.

## Giới hạn
- 1 <= N <= 10000; 1 <= K <= 10.
- -1000 <= a[i] <= 1000.
- Thời gian 2 giây, bộ nhớ 256 MB.

## Ví dụ
Input:
~~~text
5 2
-2 3 -6 -4 5
~~~
Output:
~~~text
4
~~~

Nguồn ý tưởng: https://oj.vnoi.info/problem/amsseq
Nội dung được biên soạn lại.
""",
        'solution': """n, k = map(int, input().split())
a = list(map(int, input().split()))
dp = [0] * (n + 1)
best = 0
for i in range(1, n + 1):
    dp[i] = a[i - 1] + max(dp[max(0, i - k):i])
    best = max(best, dp[i])
print(best)
""",
    },
    'CF977A': {
        'name': 'Phép trừ đặc biệt (Codeforces 977A)',
        'source': 'https://codeforces.com/problemset/problem/977/A',
        'difficulty': 'easy', 'tag': 'implementation', 'limit': 1,
        'statement': """# Phép trừ đặc biệt

Thực hiện K lần phép biến đổi trên số nguyên dương N. Nếu chữ số cuối khác 0, giảm số đi 1. Nếu chữ số cuối là 0, xóa chữ số cuối (chia nguyên cho 10). In kết quả cuối cùng.

## Dữ liệu vào
Một dòng gồm N và K.

## Dữ liệu ra
In một số nguyên là giá trị sau K phép biến đổi.

## Giới hạn
- 2 <= N <= 10^9; 1 <= K <= 50.
- Giá trị cuối cùng luôn dương.
- Thời gian 1 giây, bộ nhớ 256 MB.

## Ví dụ
Input:
~~~text
512 4
~~~
Output:
~~~text
50
~~~

Nguồn ý tưởng: https://codeforces.com/problemset/problem/977/A
Nội dung được biên soạn lại.
""",
        'solution': """n, k = map(int, input().split())
for _ in range(k):
    n = n - 1 if n % 10 else n // 10
print(n)
""",
    },
    'ABC081B': {
        'name': 'Chia đôi đồng loạt (AtCoder ABC081B)',
        'source': 'https://atcoder.jp/contests/abs/tasks/abc081_b',
        'difficulty': 'easy', 'tag': 'implementation', 'limit': 2,
        'statement': """# Chia đôi đồng loạt

Cho N số nguyên dương. Khi tất cả các số hiện tại đều chẵn, bạn được chia đồng thời từng số cho 2. Hỏi có thể thực hiện liên tiếp tối đa bao nhiêu lần?

## Dữ liệu vào
Dòng đầu chứa N. Dòng sau chứa N số nguyên dương.

## Dữ liệu ra
In ra số lần chia tối đa.

## Giới hạn
- 1 <= N <= 200; 1 <= a[i] <= 10^9.
- Thời gian 2 giây, bộ nhớ 256 MB.

## Ví dụ
Input:
~~~text
3
8 12 40
~~~
Output:
~~~text
2
~~~

Nguồn ý tưởng: https://atcoder.jp/contests/abs/tasks/abc081_b
Nội dung được biên soạn lại.
""",
        'solution': """n = int(input())
a = list(map(int, input().split()))
count = 0
while all(x % 2 == 0 for x in a):
    a = [x // 2 for x in a]
    count += 1
print(count)
""",
    },
}


def vnoi_cases():
    fixed = [(1, 1, [-5]), (1, 1, [7]),
             (5, 2, [-2, 3, -6, -4, 5]), (5, 1, [1, -2, 3, -4, 5]),
             (5, 5, [-1] * 5), (6, 2, [5, -100, -100, 8, -3, 6]),
             (8, 3, [0] * 8)]
    rng = random.Random(1101)
    fixed.extend((n, k, [rng.randint(-1000, 1000) for _ in range(n)])
                 for n, k in [(10, 1), (20, 10), (50, 2), (100, 7),
                              (500, 10), (3000, 3), (10000, 10)])
    for n, k, values in fixed:
        dp = [0] * (n + 1)
        for i in range(1, n + 1):
            dp[i] = values[i - 1] + max(dp[max(0, i - k):i])
        yield f'{n} {k}\n' + ' '.join(map(str, values)) + '\n', f'{max(dp)}\n'


def cf_cases():
    fixed = [(512, 4), (1_000_000_000, 9), (2, 1), (10, 1),
             (20, 2), (101, 2), (987654321, 50), (999999999, 50)]
    rng = random.Random(977)
    fixed.extend((rng.randint(100_000_000, 1_000_000_000),
                  rng.randint(1, 50)) for _ in range(8))
    for n, k in fixed:
        value = n
        for _ in range(k):
            value = value - 1 if value % 10 else value // 10
        if value <= 0:
            raise CommandError(f'Invalid Codeforces case: {n} {k}')
        yield f'{n} {k}\n', f'{value}\n'


def atcoder_cases():
    fixed = [[1], [2], [2, 4], [8, 12, 40], [5, 6, 8, 10],
             [1_000_000_000], [2**29], [2**20] * 200,
             [2**29, 2**28, 2**27], [2**15, 2**15 - 1]]
    rng = random.Random(81)
    for n, shift in [(10, 1), (50, 8), (200, 0), (200, 12)]:
        fixed.append([rng.randrange(1, 1_000_000_000 // (2**shift) + 1)
                      * 2**shift for _ in range(n)])
    for values in fixed:
        count = 0
        current = values[:]
        while all(x % 2 == 0 for x in current):
            current = [x // 2 for x in current]
            count += 1
        yield f'{len(values)}\n' + ' '.join(map(str, values)) + '\n', f'{count}\n'


CASE_FACTORIES = {'VNOIAMSSEQ': vnoi_cases, 'CF977A': cf_cases,
                  'ABC081B': atcoder_cases}


class Command(BaseCommand):
    help = 'Add hidden VNOI, Codeforces, and AtCoder tasks with deterministic tests'

    def handle(self, *args, **options):
        for code, spec in PROBLEMS.items():
            root = Path(pkg.get_problem_dir(code))
            if Problem.objects.filter(code=code).exists() or root.exists():
                raise CommandError(f'{code} already exists; refusing to overwrite it')
            try:
                pkg.init_package(code, {
                    'title': spec['name'], 'time_limit': spec['limit'],
                    'memory_limit': 256, 'points': 100,
                    'difficulty': spec['difficulty'], 'status': 'ready',
                })
                pkg.save_statement(code, spec['statement'])
                solution_dir = root / 'solutions'
                solution_dir.mkdir(exist_ok=True)
                (solution_dir / 'official.py').write_text(spec['solution'], encoding='utf-8')
                testcases = list(CASE_FACTORIES[code]())
                for index, (case_input, case_output) in enumerate(testcases, 1):
                    sample_index = {'VNOIAMSSEQ': 3, 'CF977A': 1, 'ABC081B': 4}[code]
                    pkg.save_testcase(code, f'{index:02d}', case_input, case_output,
                                      points=100 / len(testcases), sample=index == sample_index)
                with transaction.atomic():
                    problem = Problem.objects.create(
                        code=code, name=spec['name'], description=spec['statement'],
                        time_limit=spec['limit'], memory_limit=262144, points=100,
                        difficulty=spec['difficulty'], status='ready', is_public=False,
                    )
                    tag, _ = ProblemType.objects.get_or_create(
                        name=spec['tag'], defaults={'full_name': spec['tag'].title()})
                    problem.types.add(tag)
            except Exception:
                shutil.rmtree(root, ignore_errors=True)
                raise
            self.stdout.write(self.style.SUCCESS(
                f'{code}: {len(testcases)} tests, hidden, source {spec["source"]}'))
