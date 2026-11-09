"""Install ten more hidden problems adapted from external competitive judges."""

import random
import shutil
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from backend.judge import problem_package as pkg
from backend.judge.models import Problem, ProblemType


def statement(title, body, input_format, output_format, limits, example_in, example_out, source):
    return (f'# {title}\n\n{body}\n\n## Dữ liệu vào\n{input_format}\n\n'
            f'## Dữ liệu ra\n{output_format}\n\n## Giới hạn\n{limits}\n\n'
            f'## Ví dụ\nInput:\n~~~text\n{example_in}\n~~~\n\n'
            f'Output:\n~~~text\n{example_out}\n~~~\n\n'
            f'Nguồn ý tưởng: {source}. Nội dung được biên soạn lại.\n')


QBMAX_SOLUTION = """m, n = map(int, input().split())
grid = [list(map(int, input().split())) for _ in range(m)]
dp = [grid[r][0] for r in range(m)]
for c in range(1, n):
    old = dp[:]
    for r in range(m):
        dp[r] = grid[r][c] + max(old[max(0, r-1):min(m, r+2)])
print(max(dp))
"""

C11CUT_SOLUTION = """m, n = map(int, input().split())
grid = [list(map(int, input().split())) for _ in range(m)]
best = 0
for mask in range(1 << (m*n)):
    total = 0
    for r in range(m):
        value = 0
        for c in range(n):
            if mask & (1 << (r*n+c)):
                value = value*10 + grid[r][c]
            else:
                total += value
                value = 0
        total += value
    for c in range(n):
        value = 0
        for r in range(m):
            if not mask & (1 << (r*n+c)):
                value = value*10 + grid[r][c]
            else:
                total += value
                value = 0
        total += value
    best = max(best, total)
print(best)
"""

PROBLEMS = {
    'VNOIQBMAX': {
        'name': 'Đường đi tổng lớn nhất (VNOI)',
        'source': 'https://oj.vnoi.info/problem/qbmax', 'tag': 'dp',
        'difficulty': 'medium', 'limit': 2, 'solution': QBMAX_SOLUTION,
        'statement': statement(
            'Đường đi tổng lớn nhất', 'Cho bảng m hàng, n cột. Chọn một ô ở cột đầu rồi đi tới cột cuối. Mỗi bước sang cột kế tiếp, ở cùng hàng hoặc lệch một hàng. Tổng các giá trị trên đường đi cần lớn nhất.',
            'Dòng đầu là m, n. Tiếp theo là m dòng, mỗi dòng n số nguyên.',
            'In tổng lớn nhất.', '1 <= m,n <= 100; |a[i][j]| <= 100.',
            '1 3\n1 -2 4', '3', 'https://oj.vnoi.info/problem/qbmax'),
    },
    'VNOIC11CUT': {
        'name': 'Cắt bảng chữ số (VNOI)',
        'source': 'https://oj.vnoi.info/problem/c11cut', 'tag': 'brute-force',
        'difficulty': 'medium', 'limit': 4, 'solution': C11CUT_SOLUTION,
        'statement': statement(
            'Cắt bảng chữ số', 'Mỗi ô của bảng chứa một chữ số. Chia toàn bộ bảng thành các mảnh liên tiếp, mỗi mảnh chỉ nằm trên một hàng hoặc một cột. Đọc các chữ số của một mảnh từ trái sang phải hoặc từ trên xuống dưới để tạo thành một số. Hãy tìm tổng lớn nhất của các số trên các mảnh.',
            'Dòng đầu chứa m, n. Mỗi trong m dòng tiếp theo có n chữ số, cách nhau bằng dấu cách.',
            'In tổng lớn nhất.', '1 <= m,n <= 4; mỗi ô là chữ số từ 0 đến 9.',
            '2 3\n1 2 3\n3 1 2', '435', 'https://oj.vnoi.info/problem/c11cut'),
    },
    'CF4A': {
        'name': 'Chia quả dưa (Codeforces 4A)',
        'source': 'https://codeforces.com/problemset/problem/4/A', 'tag': 'math',
        'difficulty': 'easy', 'limit': 1,
        'solution': """w = int(input())
print('YES' if w > 2 and w % 2 == 0 else 'NO')
""",
        'statement': statement(
            'Chia quả dưa', 'Một quả dưa nặng w kilôgam. Có thể chia thành hai phần có khối lượng nguyên dương, đều là số chẵn hay không?',
            'Một số nguyên w.', 'In YES nếu có thể, ngược lại in NO.',
            '1 <= w <= 100.', '8', 'YES',
            'https://codeforces.com/problemset/problem/4/A'),
    },
    'CF71A': {
        'name': 'Viết tắt từ dài (Codeforces 71A)',
        'source': 'https://codeforces.com/problemset/problem/71/A', 'tag': 'strings',
        'difficulty': 'easy', 'limit': 1,
        'solution': """n = int(input())
for _ in range(n):
    word = input().strip()
    print(word if len(word) <= 10 else word[0] + str(len(word)-2) + word[-1])
""",
        'statement': statement(
            'Viết tắt từ dài', 'Với mỗi từ dài hơn 10 ký tự, thay nó bằng chữ cái đầu, số ký tự ở giữa và chữ cái cuối. Các từ khác giữ nguyên.',
            'Dòng đầu là n; tiếp theo n dòng, mỗi dòng một từ chỉ gồm chữ thường.',
            'In n dòng là các từ sau khi xử lý.',
            '1 <= n <= 100; độ dài mỗi từ từ 1 đến 100.',
            '2\nword\nlocalization', 'word\nl10n',
            'https://codeforces.com/problemset/problem/71/A'),
    },
    'CF231A': {
        'name': 'Nhóm ba người (Codeforces 231A)',
        'source': 'https://codeforces.com/problemset/problem/231/A', 'tag': 'implementation',
        'difficulty': 'easy', 'limit': 1,
        'solution': """n = int(input())
answer = 0
for _ in range(n):
    answer += sum(map(int, input().split())) >= 2
print(answer)
""",
        'statement': statement(
            'Nhóm ba người', 'Với mỗi bài, ba thành viên cho biết họ có chắc cách giải hay không. Nhóm chỉ giải bài khi ít nhất hai người chắc chắn. Hãy đếm số bài nhóm sẽ giải.',
            'Dòng đầu là n. Tiếp theo n dòng, mỗi dòng có ba số 0 hoặc 1.',
            'In số bài nhóm sẽ giải.', '1 <= n <= 1000.',
            '3\n1 1 0\n1 0 0\n0 1 1', '2',
            'https://codeforces.com/problemset/problem/231/A'),
    },
    'CF158A': {
        'name': 'Vòng tiếp theo (Codeforces 158A)',
        'source': 'https://codeforces.com/problemset/problem/158/A', 'tag': 'implementation',
        'difficulty': 'easy', 'limit': 1,
        'solution': """n, k = map(int, input().split())
scores = list(map(int, input().split()))
print(sum(x > 0 and x >= scores[k-1] for x in scores))
""",
        'statement': statement(
            'Vòng tiếp theo', 'Danh sách điểm của n thí sinh đã xếp không tăng. Thí sinh được vào vòng sau nếu điểm dương và không thấp hơn điểm của người đứng thứ k. Hãy đếm số người vào vòng sau.',
            'Dòng đầu gồm n, k. Dòng sau gồm n điểm theo thứ tự không tăng.',
            'In số người được vào vòng sau.',
            '1 <= k <= n <= 50; 0 <= điểm <= 100.',
            '4 2\n0 0 0 0', '0',
            'https://codeforces.com/problemset/problem/158/A'),
    },
    'ABC086A': {
        'name': 'Chẵn lẻ tích (AtCoder ABC086A)',
        'source': 'https://atcoder.jp/contests/abs/tasks/abc086_a',
        'tag': 'math', 'difficulty': 'easy', 'limit': 2,
        'solution': """a, b = map(int, input().split())
print('Even' if a*b % 2 == 0 else 'Odd')
""",
        'statement': statement(
            'Chẵn lẻ tích', 'Cho hai số nguyên dương. Xác định tích của chúng là chẵn hay lẻ.',
            'Một dòng gồm a, b.', 'In Even nếu tích chẵn, Odd nếu tích lẻ.',
            '1 <= a,b <= 10000.', '3 4', 'Even',
            'https://atcoder.jp/contests/abs/tasks/abc086_a'),
    },
    'ABC081A': {
        'name': 'Đếm ô đánh dấu (AtCoder ABC081A)',
        'source': 'https://atcoder.jp/contests/abs/tasks/abc081_a',
        'tag': 'implementation', 'difficulty': 'easy', 'limit': 2,
        'solution': """s = input().strip()
print(s.count('1'))
""",
        'statement': statement(
            'Đếm ô đánh dấu', 'Ba ô được biểu diễn bằng một xâu gồm ba ký tự 0 hoặc 1. Đếm số ô được đánh dấu 1.',
            'Một xâu nhị phân dài đúng 3.', 'In số ký tự 1.',
            'Mỗi ký tự là 0 hoặc 1.', '101', '2',
            'https://atcoder.jp/contests/abs/tasks/abc081_a'),
    },
    'ABC083B': {
        'name': 'Tổng theo chữ số (AtCoder ABC083B)',
        'source': 'https://atcoder.jp/contests/abs/tasks/abc083_b',
        'tag': 'brute-force', 'difficulty': 'easy', 'limit': 2,
        'solution': """n, a, b = map(int, input().split())
answer = 0
for x in range(1, n+1):
    digits = sum(map(int, str(x)))
    if a <= digits <= b:
        answer += x
print(answer)
""",
        'statement': statement(
            'Tổng theo chữ số', 'Xét các số nguyên từ 1 đến N. Cộng các số có tổng chữ số thập phân nằm trong đoạn từ A đến B.',
            'Một dòng gồm N, A, B.', 'In tổng cần tìm.',
            '1 <= N <= 10000; 1 <= A <= B <= 36.',
            '20 2 5', '84',
            'https://atcoder.jp/contests/abs/tasks/abc083_b'),
    },
    'ABC087B': {
        'name': 'Chọn đồng xu (AtCoder ABC087B)',
        'source': 'https://atcoder.jp/contests/abs/tasks/abc087_b',
        'tag': 'brute-force', 'difficulty': 'easy', 'limit': 2,
        'solution': """a = int(input())
b = int(input())
c = int(input())
x = int(input())
answer = 0
for i in range(a+1):
    for j in range(b+1):
        rest = x - 500*i - 100*j
        if rest >= 0 and rest % 50 == 0 and rest // 50 <= c:
            answer += 1
print(answer)
""",
        'statement': statement(
            'Chọn đồng xu', 'Bạn có A đồng mệnh giá 500, B đồng mệnh giá 100 và C đồng mệnh giá 50. Có bao nhiêu cách chọn số lượng đồng mỗi loại để được đúng X? Các đồng cùng mệnh giá không phân biệt.',
            'Bốn dòng lần lượt chứa A, B, C, X.', 'In số cách chọn.',
            '0 <= A,B,C <= 50; A+B+C >= 1; 50 <= X <= 20000; X chia hết cho 50.',
            '2\n2\n2\n100', '2',
            'https://atcoder.jp/contests/abs/tasks/abc087_b'),
    },
}


def qbmax_cases():
    sample = [[9, -2, 6, 2, 1, 3, 4], [0, -1, 6, 7, 1, 3, 3],
              [8, -2, 8, 2, 5, 3, 2], [1, -1, 6, 2, 1, 6, 1],
              [7, -2, 6, 2, 1, 3, 7]]
    grids = [[[5]], [[1, -2, 4]], [[-5], [-3], [-8]],
             [[-5, -3], [-2, -7]], sample]
    rng = random.Random(1001)
    grids += [[[rng.randint(-100, 100) for _ in range(n)] for _ in range(m)]
              for m, n in [(3, 8), (8, 3), (20, 20), (100, 100)]]
    for grid in grids:
        m, n = len(grid), len(grid[0])
        dp = [row[0] for row in grid]
        for col in range(1, n):
            dp = [grid[row][col] + max(dp[max(0, row-1):min(m, row+2)])
                  for row in range(m)]
        yield f'{m} {n}\n' + '\n'.join(' '.join(map(str, row)) for row in grid) + '\n', f'{max(dp)}\n'


def cut_value(grid):
    m, n = len(grid), len(grid[0])
    best = 0
    for mask in range(1 << (m*n)):
        total = 0
        for row in range(m):
            value = 0
            for col in range(n):
                if mask & (1 << (row*n+col)):
                    value = value*10 + grid[row][col]
                else:
                    total += value
                    value = 0
            total += value
        for col in range(n):
            value = 0
            for row in range(m):
                if not mask & (1 << (row*n+col)):
                    value = value*10 + grid[row][col]
                else:
                    total += value
                    value = 0
            total += value
        best = max(best, total)
    return best


def cut_cases():
    grids = [[[0]], [[9]], [[1, 2, 3]], [[1], [2], [3]],
             [[1, 2, 3], [3, 1, 2]], [[0, 0], [0, 0]],
             [[9, 0, 9], [1, 2, 3], [4, 5, 6]]]
    rng = random.Random(1102)
    grids += [[[rng.randrange(10) for _ in range(n)] for _ in range(m)]
              for m, n in [(3, 4), (4, 4)]]
    for grid in grids:
        m, n = len(grid), len(grid[0])
        yield f'{m} {n}\n' + '\n'.join(' '.join(map(str, row)) for row in grid) + '\n', f'{cut_value(grid)}\n'


def cf4_cases():
    for w in [1, 2, 3, 4, 5, 6, 8, 99, 100]:
        yield f'{w}\n', ('YES' if w > 2 and w % 2 == 0 else 'NO') + '\n'


def cf71_cases():
    sets = [['a'], ['abcdefghij'], ['abcdefghijk'], ['localization'],
            ['word', 'localization', 'internationalization'],
            ['z'*100], ['a'*10, 'b'*11, 'c'*100]]
    rng = random.Random(71)
    sets += [[''.join(rng.choice('abcxyz') for _ in range(rng.randint(1, 100)))
              for _ in range(n)] for n in [30, 100]]
    for words in sets:
        result = [w if len(w) <= 10 else w[0] + str(len(w)-2) + w[-1] for w in words]
        yield f'{len(words)}\n' + '\n'.join(words) + '\n', '\n'.join(result) + '\n'


def cf231_cases():
    sets = [[[1, 1, 0]], [[0, 0, 0]], [[1, 1, 1]],
            [[1, 1, 0], [1, 0, 0], [0, 1, 1]]]
    rng = random.Random(231)
    sets += [[[rng.randrange(2) for _ in range(3)] for _ in range(n)]
             for n in [5, 20, 100, 1000]]
    for triples in sets:
        yield f'{len(triples)}\n' + '\n'.join(' '.join(map(str, t)) for t in triples) + '\n', f'{sum(sum(t)>=2 for t in triples)}\n'


def cf158_cases():
    sets = [(5, [10, 9, 8, 7, 7, 7, 5, 5]),
            (2, [0, 0, 0, 0]), (1, [1]), (1, [0]),
            (3, [100, 100, 100, 0]), (4, [9, 8, 7, 6, 5])]
    rng = random.Random(158)
    sets += [(rng.randint(1, n), sorted((rng.randrange(101) for _ in range(n)), reverse=True))
             for n in [10, 20, 50]]
    for k, scores in sets:
        n = len(scores)
        yield f'{n} {k}\n' + ' '.join(map(str, scores)) + '\n', f'{sum(x > 0 and x >= scores[k-1] for x in scores)}\n'


def abc86_cases():
    for a, b in [(3, 4), (1, 21), (1, 1), (2, 2), (9999, 9999),
                 (10000, 9999), (10000, 10000), (9877, 1357)]:
        yield f'{a} {b}\n', ('Even' if a*b % 2 == 0 else 'Odd') + '\n'


def abc81_cases():
    for bits in range(8):
        s = f'{bits:03b}'
        yield s + '\n', f'{s.count("1")}\n'


def abc83_cases():
    for n, a, b in [(20, 2, 5), (10, 1, 2), (100, 4, 16),
                    (1, 1, 1), (10000, 1, 36), (10000, 36, 36),
                    (9999, 9, 18), (500, 1, 1), (10000, 20, 30)]:
        total = sum(x for x in range(1, n+1) if a <= sum(map(int, str(x))) <= b)
        yield f'{n} {a} {b}\n', f'{total}\n'


def abc87_cases():
    sets = [(2, 2, 2, 100), (5, 1, 0, 150), (30, 40, 50, 6000),
            (0, 0, 1, 50), (1, 0, 0, 500), (50, 50, 50, 20000),
            (50, 50, 50, 5000), (0, 50, 50, 2550), (13, 7, 29, 1850)]
    for a, b, c, x in sets:
        total = sum(500*i + 100*j + 50*k == x
                    for i in range(a+1) for j in range(b+1) for k in range(c+1))
        yield f'{a}\n{b}\n{c}\n{x}\n', f'{total}\n'


FACTORIES = {
    'VNOIQBMAX': qbmax_cases, 'VNOIC11CUT': cut_cases,
    'CF4A': cf4_cases, 'CF71A': cf71_cases, 'CF231A': cf231_cases,
    'CF158A': cf158_cases, 'ABC086A': abc86_cases, 'ABC081A': abc81_cases,
    'ABC083B': abc83_cases, 'ABC087B': abc87_cases,
}
SAMPLES = {'VNOIQBMAX': 5, 'VNOIC11CUT': 5, 'CF4A': 7, 'CF71A': 5,
           'CF231A': 4, 'CF158A': 2, 'ABC086A': 1, 'ABC081A': 6,
           'ABC083B': 1, 'ABC087B': 1}


class Command(BaseCommand):
    help = 'Install ten hidden VNOI, Codeforces, and AtCoder tasks with tests'

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
                testcases = list(FACTORIES[code]())
                for index, (case_input, case_output) in enumerate(testcases, 1):
                    pkg.save_testcase(code, f'{index:02d}', case_input, case_output,
                                      points=100 / len(testcases), sample=index == SAMPLES[code])
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
