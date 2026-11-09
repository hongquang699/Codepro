"""Restore the hidden AMS_SUM_PRIME statement and judge package."""

import random
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from backend.judge import problem_package as pkg
from backend.judge.models import Problem


CODE = 'AMS_SUM_PRIME'
STATEMENT = """# Tổng các số nguyên tố trong mảng

Cho một dãy số nguyên. Hãy tính tổng của những phần tử là số nguyên tố. Số nguyên tố là số nguyên lớn hơn 1 và chỉ có hai ước dương: 1 và chính nó. Các số âm, 0 và 1 không được tính.

## Dữ liệu vào

Dòng đầu chứa số nguyên N. N dòng tiếp theo, mỗi dòng chứa một phần tử của dãy.

## Dữ liệu ra

In ra tổng các phần tử là số nguyên tố.

## Giới hạn

- 1 <= N < 10^6.
- Giá trị tuyệt đối của mỗi phần tử không vượt quá 10^5.
- Thời gian 2 giây; bộ nhớ 256 MB.

## Ví dụ 1

Input:
~~~text
7
9
6
3
8
10
7
-2
~~~

Output:
~~~text
10
~~~

## Ví dụ 2

Input:
~~~text
5
7
3
8
0
2
~~~

Output:
~~~text
12
~~~
"""
SOLUTION = """n = int(input())
prime = [True] * 100001
prime[0] = prime[1] = False
for x in range(2, 317):
    if prime[x]:
        for y in range(x*x, 100001, x):
            prime[y] = False
answer = 0
for _ in range(n):
    x = int(input())
    if x > 1 and prime[x]:
        answer += x
print(answer)
"""


def prime_table():
    sieve = [True] * 100001
    sieve[0] = sieve[1] = False
    for x in range(2, 317):
        if sieve[x]:
            for y in range(x*x, 100001, x):
                sieve[y] = False
    return sieve


def cases():
    fixed = [[2], [0], [-2], [1], [100000], [99991], [99999],
             [9, 6, 3, 8, 10, 7, -2], [7, 3, 8, 0, 2],
             [-100000, -1, 0, 1, 4, 25, 97, 99991],
             [2, 2, 2, 2], [100000, 99999, 99991, 99989]]
    rng = random.Random(138)
    fixed.extend([rng.randint(-100000, 100000) for _ in range(n)]
                 for n in [100, 5000, 50000, 100000])
    sieve = prime_table()
    for values in fixed:
        result = sum(x for x in values if x > 1 and sieve[x])
        yield str(len(values)) + '\n' + '\n'.join(map(str, values)) + '\n', f'{result}\n'


class Command(BaseCommand):
    help = 'Restore statement and tests for hidden AMS_SUM_PRIME'

    def handle(self, *args, **options):
        problem = Problem.objects.filter(code=CODE).first()
        if not problem:
            raise CommandError(f'{CODE} does not exist')
        root = Path(pkg.get_problem_dir(CODE))
        if root.exists() and any(path.is_file() for path in root.rglob('*')):
            raise CommandError(f'{root} already contains files; refusing to overwrite it')
        pkg.init_package(CODE, {
            'title': problem.name, 'time_limit': 2,
            'memory_limit': 256, 'points': 100,
            'difficulty': problem.difficulty, 'status': 'ready',
        })
        pkg.save_statement(CODE, STATEMENT)
        solution_dir = root / 'solutions'
        solution_dir.mkdir(exist_ok=True)
        (solution_dir / 'official.py').write_text(SOLUTION, encoding='utf-8')
        generated = list(cases())
        for index, (case_input, case_output) in enumerate(generated, 1):
            pkg.save_testcase(CODE, f'{index:02d}', case_input, case_output,
                              points=100 / len(generated), sample=index in (8, 9))
        problem.description = STATEMENT
        problem.status = 'ready'
        problem.time_limit = 2
        problem.is_public = False
        problem.save(update_fields=['description', 'status', 'time_limit', 'is_public'])
        self.stdout.write(self.style.SUCCESS(
            f'Restored {CODE}: {len(generated)} tests, admin-only'))
