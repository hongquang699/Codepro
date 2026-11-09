from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from backend.judge.models import (
    Profile, Organization, Language, ProblemType,
    Problem, Contest, ContestProblem, ContestParticipation,
    Judge, Submission
)
from backend.judge.bridge import grade_submission

class Command(BaseCommand):
    help = 'Load CodeProOJ / DMOJ sample fixtures into the database'

    def handle(self, *args, **options):
        self.stdout.write("Loading CodeProOJ/DMOJ fixtures...")

        # 1. Organizations
        legacy_org = Organization.objects.filter(slug='vnoi').first()
        if legacy_org and not Organization.objects.filter(slug='codeprooj').exists():
            legacy_org.slug = 'codeprooj'
            legacy_org.save(update_fields=['slug'])
        codeprooj, org_created = Organization.objects.get_or_create(
            slug='codeprooj',
            defaults={'name': 'CodeProOJ', 'short_name': 'CodeProOJ', 'about': 'Cộng đồng luyện tập lập trình thi đấu CodeProOJ'}
        )
        if not org_created and codeprooj.short_name.lower() in ('vnoi', 'vnoj'):
            codeprooj.name = 'CodeProOJ'
            codeprooj.short_name = 'CodeProOJ'
            codeprooj.about = 'Cộng đồng luyện tập lập trình thi đấu CodeProOJ'
            codeprooj.save(update_fields=['name', 'short_name', 'about'])
        hsgs, _ = Organization.objects.get_or_create(
            slug='hsgs',
            defaults={'name': 'High School for Gifted Students, VNU', 'short_name': 'Chuyên KHTN', 'about': 'Trường THPT Chuyên KHTN Hà Nội'}
        )

        # 2. Languages
        langs = [
            ('CPP17', 'C++17 (GNU G++)', 'C++17', 'C++', 'c_cpp'),
            ('C11', 'C11 (GNU GCC)', 'C11', 'C', 'c_cpp'),
            ('PY3', 'Python 3.12', 'Python 3', 'Python', 'python'),
            ('PYPY3', 'PyPy 3', 'PyPy 3', 'Python', 'python'),
            ('JAVA17', 'Java 17 (OpenJDK)', 'Java 17', 'Java', 'java'),
            ('RUST', 'Rust 1.75', 'Rust', 'Rust', 'rust'),
            ('GO', 'Go 1.22', 'Go', 'Go', 'golang'),
            ('PAS', 'Free Pascal 3.2', 'Pascal', 'Pascal', 'pascal'),
        ]
        lang_objs = {}
        for key, name, sname, cname, ace in langs:
            l, _ = Language.objects.get_or_create(
                key=key,
                defaults={'name': name, 'short_name': sname, 'common_name': cname, 'ace_mode_name': ace, 'is_active': True}
            )
            lang_objs[key] = l

        # 3. Problem Types
        dp_type, _ = ProblemType.objects.get_or_create(name='dp', defaults={'full_name': 'Quy hoạch động'})
        math_type, _ = ProblemType.objects.get_or_create(name='math', defaults={'full_name': 'Toán học'})

        # 4. Users & Profiles
        users_data = [
            ('admin', 'admin@example.invalid', 'admin123', 2800, 'Grandmaster'),
            ('tourist_vn', 'tourist@example.invalid', 'tourist123', 2850, 'Grandmaster'),
            ('algo_master', 'algo@example.invalid', 'algo123', 2420, 'Master'),
            ('coder_2026', 'coder@example.invalid', 'coder123', 1542, 'Specialist'),
        ]
        profiles = {}
        for uname, email, pwd, rating, rank in users_data:
            u, created = User.objects.get_or_create(username=uname, defaults={'email': email})
            if created or not u.has_usable_password():
                u.set_password(pwd)
                if uname == 'admin':
                    u.is_staff = True
                    u.is_superuser = True
                u.save()
            prof, _ = Profile.objects.get_or_create(user=u, defaults={'rating': rating, 'display_rank': rank})
            prof.organizations.add(codeprooj)
            profiles[uname] = prof

        # 5. Problems (APLUS and KNAPSACK)
        p_aplus, _ = Problem.objects.get_or_create(
            code='APLUS',
            defaults={
                'name': 'A + B Problem',
                'description': 'Cho hai số nguyên $A$ và $B$. Tính $A + B$.\n\n### Input\n2 3\n\n### Output\n5',
                'time_limit': 1.0,
                'memory_limit': 65536,
                'points': 100.0,
                'is_public': True
            }
        )
        p_aplus.types.add(math_type)

        p_knapsack, _ = Problem.objects.get_or_create(
            code='KNAPSACK',
            defaults={
                'name': 'Bài toán cái túi (0/1 Knapsack)',
                'description': 'Tìm giá trị lớn nhất của các đồ vật có trọng lượng không vượt quá $W$.\n\n### Input\n4 7\n1 1\n3 4\n4 5\n5 7\n\n### Output\n9',
                'time_limit': 2.0,
                'memory_limit': 262144,
                'points': 100.0,
                'is_public': True
            }
        )
        p_knapsack.types.add(dp_type)

        # 6. Contest: CodeProOJ Weekly #01
        now = timezone.now()
        contest, contest_created = Contest.objects.get_or_create(
            key='weekly-01',
            defaults={
                'name': 'CodeProOJ Weekly Contest #01',
                'description': 'Kỳ thi luyện tập hàng tuần của CodeProOJ.',
                'start_time': now - timedelta(hours=1),
                'end_time': now + timedelta(hours=2),
                'time_limit': 10800,
                'is_rated': True,
                'format_name': 'icpc',
                'is_visible': True
            }
        )
        if not contest_created and contest.name.startswith('VNOI '):
            contest.name = 'CodeProOJ Weekly Contest #01'
            contest.description = 'Kỳ thi luyện tập hàng tuần của CodeProOJ.'
            contest.save(update_fields=['name', 'description'])
        ContestProblem.objects.get_or_create(contest=contest, problem=p_aplus, defaults={'order': 1, 'output_prefix': 'A', 'points': 100})
        ContestProblem.objects.get_or_create(contest=contest, problem=p_knapsack, defaults={'order': 2, 'output_prefix': 'B', 'points': 100})

        # 7. Contest Participations
        for uname, score, pen in [('tourist_vn', 200.0, 45), ('algo_master', 100.0, 20), ('coder_2026', 100.0, 35)]:
            ContestParticipation.objects.get_or_create(
                contest=contest,
                user=profiles[uname],
                defaults={'score': score, 'cumulative_time': pen * 60, 'format_data': {'A': {'ac': True, 'tries': 1}}}
            )

        # 8. Judge
        old_judge = Judge.objects.filter(name='vnoj-judge-01').first()
        if old_judge and not Judge.objects.filter(name='codeprooj-judge-01').exists():
            old_judge.name = 'codeprooj-judge-01'
            old_judge.save(update_fields=['name'])
        judge, _ = Judge.objects.get_or_create(
            name='codeprooj-judge-01',
            defaults={
                'auth_key': settings.JUDGE_AUTH_TOKEN,
                'online': True,
                'load': 0.15,
                'ping': 0.45,
                'last_seen': now,
                'runtime_versions': {'gcc': '11.2.0', 'python': '3.12.0', 'rustc': '1.75.0'}
            }
        )

        # 9. Create a sample submission and grade it
        sub, created = Submission.objects.get_or_create(
            problem=p_aplus,
            user=profiles['coder_2026'],
            language=lang_objs['CPP17'],
            defaults={
                'source': '#include <iostream>\nusing namespace std;\nint main() { long long a, b; if (cin >> a >> b) cout << a + b; return 0; }',
                'status': 'QU'
            }
        )
        grade_submission(sub.id)

        self.stdout.write(self.style.SUCCESS("CodeProOJ/DMOJ fixtures successfully loaded!"))
