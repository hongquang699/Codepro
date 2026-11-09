"""Smoke-test representative imported Codeforces tasks through the real judge."""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
import django
django.setup()

from backend.judge.bridge import grade_submission
from backend.judge.models import Language, Problem, Profile, Submission

SOLUTIONS = {
    'CF1060A': """n = int(input())
s = input().strip()
print(min(n // 11, s.count('8')))
""",
    'CF519B': """n = int(input())
a = list(map(int, input().split()))
b = list(map(int, input().split()))
c = list(map(int, input().split()))
print(sum(a) - sum(b))
print(sum(b) - sum(c))
""",
    'CF379A': """n, b = map(int, input().split())
total = n
stubs = n
while stubs >= b:
    new = stubs // b
    total += new
    stubs = new + stubs % b
print(total)
""",
    'CF615A': """n, m = map(int, input().split())
on = set()
for _ in range(n):
    row = list(map(int, input().split()))
    on.update(row[1:])
print('YES' if len(on) == m else 'NO')
""",
    'CF1101A': """q = int(input())
for _ in range(q):
    l, r, d = map(int, input().split())
    print(d if d < l else (r // d + 1) * d)
""",
}

admin = Profile.objects.get(user__username='admin')
language = Language.objects.get(key='PY3')
for code, source in SOLUTIONS.items():
    problem = Problem.objects.get(code=code)
    submission = Submission.objects.create(
        problem=problem, user=admin, language=language, source=source, status='QU')
    grade_submission(submission.id)
    submission.refresh_from_db()
    print(code, submission.id, submission.result, submission.points,
          submission.test_cases.count(), flush=True)
