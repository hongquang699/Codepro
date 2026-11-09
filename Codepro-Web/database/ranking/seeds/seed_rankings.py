import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from django.contrib.auth.models import User
from backend.judge.models import Profile, Problem, Contest, ContestProblem, Submission, Language, Organization
from backend.ranking.models.ranking import GlobalRanking
from backend.ranking.models.rating import UserRating
from backend.ranking.models.rating_history import RatingHistoryRecord
from backend.ranking.models.contest_ranking import ContestRanking
from backend.ranking.models.ranking_snapshot import RankingSnapshot
from backend.ranking.services.ranking_service import RankingService
from backend.ranking.services.contest_ranking_service import ContestRankingService

def run_seed():
    print("Seeding Ranking & Leaderboard Data...")

    # 1. Organizations
    legacy_org = Organization.objects.filter(slug='vnoi').first()
    if legacy_org and not Organization.objects.filter(slug='codeprooj').exists():
        legacy_org.slug = 'codeprooj'
        legacy_org.save(update_fields=['slug'])
    org_codeprooj, org_created = Organization.objects.get_or_create(
        slug='codeprooj',
        defaults={'name': 'CodeProOJ', 'short_name': 'CodeProOJ', 'about': 'Cộng đồng luyện tập lập trình thi đấu CodeProOJ'}
    )
    if not org_created and org_codeprooj.short_name.lower() in ('vnoi', 'vnoj'):
        org_codeprooj.name = 'CodeProOJ'
        org_codeprooj.short_name = 'CodeProOJ'
        org_codeprooj.about = 'Cộng đồng luyện tập lập trình thi đấu CodeProOJ'
        org_codeprooj.save(update_fields=['name', 'short_name', 'about'])
    org_hust, _ = Organization.objects.get_or_create(
        slug='hust-algo',
        defaults={'name': 'HUST Algorithm Club', 'short_name': 'HUST ACM', 'about': 'Câu lạc bộ Thuật toán ĐHBK Hà Nội'}
    )
    org_vnu, _ = Organization.objects.get_or_create(
        slug='vnu-acm',
        defaults={'name': 'VNU University of Science ICPC', 'short_name': 'VNU-HUS', 'about': 'Đội tuyển ICPC ĐHQGHN'}
    )

    # 2. Languages
    lang_cpp, _ = Language.objects.get_or_create(key='CPP17', defaults={'name': 'C++17 (GCC 11.2)', 'short_name': 'C++17', 'common_name': 'C++'})
    lang_py, _ = Language.objects.get_or_create(key='PY3', defaults={'name': 'Python 3.10', 'short_name': 'Python 3', 'common_name': 'Python'})

    # 3. Contestants
    contestant_specs = [
        ('tourist_vn', 'tourist_vn@example.invalid', 3120, 3250, 'Legendary Grandmaster', 48, 52, 'Vietnam', 'Đại học Khoa học Tự nhiên - ĐHQG HN', org_vnu),
        ('algo_master', 'algo_master@example.invalid', 2680, 2740, 'Grandmaster', 42, 49, 'Vietnam', 'Đại học Bách Khoa Hà Nội (HUST)', org_hust),
        ('petr_vn', 'petr@example.invalid', 2350, 2410, 'Master', 36, 45, 'Vietnam', 'Phổ thông Năng khiếu - ĐHQG HCM', org_codeprooj),
        ('coder_2026', 'coder2026@example.invalid', 2045, 2110, 'Candidate Master', 31, 40, 'Vietnam', 'THPT Chuyên Sư Phạm Hà Nội', org_codeprooj),
        ('cpp_ninja', 'cpp_ninja@example.invalid', 1780, 1850, 'Expert', 26, 38, 'Vietnam', 'Đại học Bách Khoa - ĐH Đà Nẵng', org_codeprooj),
        ('ken_tokyo', 'ken@tokyo.ac.jp', 1690, 1720, 'Expert', 24, 32, 'Japan', 'University of Tokyo', None),
        ('specialist_dev', 'spec@example.invalid', 1520, 1590, 'Specialist', 19, 30, 'Vietnam', 'Đại học Cần Thơ', org_codeprooj),
        ('sg_coder', 'sg_coder@nus.edu.sg', 1480, 1540, 'Specialist', 18, 28, 'Singapore', 'National University of Singapore (NUS)', None),
        ('pupil_rookie', 'pupil@example.invalid', 1310, 1370, 'Pupil', 12, 25, 'Vietnam', 'Đại học FPT Cần Thơ', org_codeprooj),
        ('test_coder_99', 'test99@example.invalid', 1140, 1200, 'Newbie', 7, 20, 'Vietnam', 'Đại học Công nghệ Thông tin - ĐHQG HCM', org_codeprooj),
        ('us_algo_kid', 'kid@mit.edu', 1950, 2010, 'Candidate Master', 28, 35, 'United States', 'Massachusetts Institute of Technology (MIT)', None),
    ]

    users = {}
    for uname, email, rating, max_r, tier, solved, subs, country, school, org in contestant_specs:
        user, created = User.objects.get_or_create(username=uname, defaults={'email': email})
        if created:
            user.set_password('codeprooj_demo_password_2026')
            user.save()
        users[uname] = user

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.rating = rating
        profile.points = float(solved * 100)
        profile.display_rank = tier
        if org:
            profile.organizations.add(org)
        profile.save()

        # UserRating
        ur, _ = UserRating.objects.update_or_create(
            user=user,
            defaults={
                'current_rating': rating,
                'max_rating': max_r,
                'rank_tier': tier,
                'contests_participated': max(1, solved // 3)
            }
        )

        # GlobalRanking
        gr, _ = GlobalRanking.objects.update_or_create(
            user=user,
            defaults={
                'rank': 1, # will recalculate
                'rating': rating,
                'score': float(solved * 100),
                'solved': solved,
                'submissions': subs,
                'country': country,
                'school': school,
                'organization': org,
                'tier': tier
            }
        )

    # 4. Create Problems & Contest Problems
    prob_c, _ = Problem.objects.get_or_create(
        code='LCS',
        defaults={'name': 'Dãy con chung dài nhất', 'description': 'Tìm độ dài dãy con chung dài nhất giữa hai xâu S và T.', 'points': 100.0}
    )
    prob_d, _ = Problem.objects.get_or_create(
        code='SHORTEST_PATH',
        defaults={'name': 'Đường đi ngắn nhất Dijkstra', 'description': 'Cho đồ thị có trọng số dương, tìm đường đi ngắn nhất từ đỉnh 1 đến đỉnh N.', 'points': 100.0}
    )

    contest = Contest.objects.filter(key='weekly-01').first()
    if not contest:
        contest = Contest.objects.create(
            key='weekly-01',
            name='CodeProOJ Weekly Contest #01',
            description='Kỳ thi lập trình định kỳ hàng tuần trên CodeProOJ.',
            start_time=timezone.now() - timedelta(hours=3),
            end_time=timezone.now() - timedelta(hours=1),
            time_limit=7200,
            format_name='icpc',
            is_rated=True
        )
    elif contest.name.startswith('VNOI '):
        contest.name = 'CodeProOJ Weekly Contest #01'
        contest.description = 'Kỳ thi lập trình định kỳ hàng tuần trên CodeProOJ.'
        contest.save(update_fields=['name', 'description'])

    prob_a = Problem.objects.filter(code='APLUS').first()
    prob_b = Problem.objects.filter(code='KNAPSACK').first()

    for idx, (p, prefix) in enumerate([(prob_a, 'A'), (prob_b, 'B'), (prob_c, 'C'), (prob_d, 'D')], 1):
        if p:
            ContestProblem.objects.get_or_create(
                contest=contest,
                problem=p,
                defaults={'points': 100.0, 'order': idx, 'output_prefix': prefix}
            )

    # 5. Seed Submissions for Contest 1
    # tourist_vn solves all 4 (A: 4m 1 try, B: 12m 1 try, C: 28m 1 try, D: 45m 1 try)
    # algo_master solves 4 (A: 5m 1 try, B: 18m 2 tries, C: 40m 1 try, D: 75m 2 tries)
    # petr_vn solves 3 (A: 7m 1 try, B: 25m 1 try, C: 55m 2 tries, D: WA 3 tries)
    # coder_2026 solves 3 (A: 10m 1 try, B: 35m 1 try, C: 70m 3 tries)
    # cpp_ninja solves 2 (A: 12m 1 try, B: 45m 2 tries, C: WA 2 tries)
    # specialist_dev solves 2 (A: 15m 1 try, B: 60m 3 tries)
    # pupil_rookie solves 1 (A: 20m 2 tries, B: WA 2 tries)
    # test_coder_99 solves 1 (A: 35m 3 tries)

    start_t = contest.start_time
    mock_contest_subs = [
        ('tourist_vn', prob_a, 'AC', 4, 1),
        ('tourist_vn', prob_b, 'AC', 12, 1),
        ('tourist_vn', prob_c, 'AC', 28, 1),
        ('tourist_vn', prob_d, 'AC', 45, 1),

        ('algo_master', prob_a, 'AC', 5, 1),
        ('algo_master', prob_b, 'WA', 15, 1),
        ('algo_master', prob_b, 'AC', 18, 2),
        ('algo_master', prob_c, 'AC', 40, 1),
        ('algo_master', prob_d, 'WA', 65, 1),
        ('algo_master', prob_d, 'AC', 75, 2),

        ('petr_vn', prob_a, 'AC', 7, 1),
        ('petr_vn', prob_b, 'AC', 25, 1),
        ('petr_vn', prob_c, 'WA', 48, 1),
        ('petr_vn', prob_c, 'AC', 55, 2),
        ('petr_vn', prob_d, 'WA', 80, 1),

        ('coder_2026', prob_a, 'AC', 10, 1),
        ('coder_2026', prob_b, 'AC', 35, 1),
        ('coder_2026', prob_c, 'WA', 60, 1),
        ('coder_2026', prob_c, 'WA', 65, 2),
        ('coder_2026', prob_c, 'AC', 70, 3),

        ('cpp_ninja', prob_a, 'AC', 12, 1),
        ('cpp_ninja', prob_b, 'WA', 40, 1),
        ('cpp_ninja', prob_b, 'AC', 45, 2),
        ('cpp_ninja', prob_c, 'WA', 85, 1),

        ('specialist_dev', prob_a, 'AC', 15, 1),
        ('specialist_dev', prob_b, 'WA', 50, 1),
        ('specialist_dev', prob_b, 'WA', 55, 2),
        ('specialist_dev', prob_b, 'AC', 60, 3),

        ('pupil_rookie', prob_a, 'WA', 15, 1),
        ('pupil_rookie', prob_a, 'AC', 20, 2),
        ('pupil_rookie', prob_b, 'WA', 50, 1),

        ('test_coder_99', prob_a, 'WA', 20, 1),
        ('test_coder_99', prob_a, 'WA', 30, 2),
        ('test_coder_99', prob_a, 'AC', 35, 3),
    ]

    for uname, prob, res, minutes, try_no in mock_contest_subs:
        if not prob:
            continue
        user = users[uname]
        sub_time = start_t + timedelta(minutes=minutes)
        Submission.objects.create(
            user=user.profile,
            problem=prob,
            contest=contest,
            language=lang_cpp,
            source=f"// Submission by {uname} for {prob.code} (try #{try_no})\n#include <iostream>\nusing namespace std;\nint main() {{ return 0; }}",
            result=res,
            points=100.0 if res == 'AC' else 0.0,
            status='D',
            time=0.015 * (try_no + 1),
            memory=2048.0,
            date=sub_time
        )

    # 6. Recalculate Contest Scoreboard
    ContestRankingService.get_scoreboard(contest.id, live=True)

    # 7. Record realistic rating histories for top contestants
    histories = [
        ('tourist_vn', [
            ('VNOI Open 2025', 3000, 3080, 80, 1, 3300),
            ('ICPC National Vietnam 2025', 3080, 3110, 30, 1, 3250),
            ('CodeProOJ Weekly Contest #01', 3110, 3120, 10, 1, 3280),
        ]),
        ('algo_master', [
            ('VNOI Open 2025', 2550, 2610, 60, 3, 2750),
            ('ICPC National Vietnam 2025', 2610, 2650, 40, 2, 2800),
            ('CodeProOJ Weekly Contest #01', 2650, 2680, 30, 2, 2820),
        ]),
        ('coder_2026', [
            ('VNOI Open 2025', 1890, 1960, 70, 8, 2150),
            ('ICPC National Vietnam 2025', 1960, 2010, 50, 6, 2180),
            ('CodeProOJ Weekly Contest #01', 2010, 2045, 35, 4, 2220),
        ]),
        ('cpp_ninja', [
            ('VNOI Open 2025', 1650, 1710, 60, 15, 1850),
            ('CodeProOJ Weekly Contest #01', 1710, 1780, 70, 5, 1920),
        ]),
    ]

    for uname, rounds in histories:
        user = users.get(uname)
        if not user:
            continue
        base_t = timezone.now() - timedelta(days=90)
        for idx, (cname, old_r, new_r, delta, rank_val, perf) in enumerate(rounds):
            t = base_t + timedelta(days=idx * 30)
            RatingHistoryRecord.objects.get_or_create(
                user=user,
                contest_name=cname,
                defaults={
                    'contest': contest if idx == len(rounds) - 1 else None,
                    'old_rating': old_r,
                    'new_rating': new_r,
                    'rating_change': delta,
                    'rank_in_contest': rank_val,
                    'performance': perf,
                    'timestamp': t
                }
            )

    # 8. Recalculate All Global Rankings
    total_ranked = RankingService.recalculate_all_global_rankings()
    print(f"Recalculated global rankings for {total_ranked} users.")

    # 9. Create snapshot
    top_global = GlobalRanking.objects.select_related('user').order_by('rank')[:10]
    snapshot_data = [
        {'rank': g.rank, 'username': g.user.username, 'rating': g.rating, 'score': g.score, 'solved': g.solved}
        for g in top_global
    ]
    RankingSnapshot.objects.create(snapshot_type='global', snapshot_key='latest', data=snapshot_data)
    print("Ranking snapshot created successfully.")
    print("Database seed completed successfully!")

if __name__ == '__main__':
    run_seed()
