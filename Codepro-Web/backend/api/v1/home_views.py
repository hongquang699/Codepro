from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from backend.judge.models import Problem, Contest, Submission, Profile
from backend.judge.contest_visibility import visible_contests
from backend.users.models import UserRating

class HomeSummaryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        now = timezone.now()

        # Stats
        total_users = User.objects.count()
        total_problems = Problem.objects.count()
        total_subs = Submission.objects.count()
        total_contests = Contest.objects.filter(visible_contests('web')).count()
        total_ac = Submission.objects.filter(result='AC').count()

        # Featured Contest (active or upcoming or most recent)
        featured_contest = None
        c = Contest.objects.filter(visible_contests('web')).order_by('-start_time').first()
        if c:
            is_running = c.start_time <= now <= c.end_time
            is_upcoming = c.start_time > now
            featured_contest = {
                'key': c.key,
                'name': c.name,
                'format': getattr(c, 'format', 'ICPC'),
                'start_time': c.start_time.isoformat() if c.start_time else '',
                'end_time': c.end_time.isoformat() if c.end_time else '',
                'status': 'RUNNING' if is_running else ('UPCOMING' if is_upcoming else 'ENDED'),
                'status_display': 'Đang diễn ra' if is_running else ('Sắp diễn ra' if is_upcoming else 'Đã kết thúc'),
                'is_rated': getattr(c, 'is_rated', True),
                'problem_count': c.contest_problems.count() if hasattr(c, 'contest_problems') else 4
            }

        # Featured Problems
        problems = Problem.objects.order_by('-id')[:6]
        prob_list = []
        for p in problems:
            total_p_subs = Submission.objects.filter(problem=p).count()
            ac_p_subs = Submission.objects.filter(problem=p, result='AC').count()
            ac_rate = round((ac_p_subs / total_p_subs * 100), 1) if total_p_subs > 0 else 0.0
            prob_list.append({
                'code': p.code,
                'name': p.name,
                'points': p.points or 100,
                'difficulty': getattr(p, 'difficulty', 1200) or 1200,
                'ac_count': ac_p_subs,
                'ac_rate': ac_rate
            })

        # Top Coders
        top_profiles = Profile.objects.select_related('user').order_by('-rating')[:5]
        top_users = []
        for prof in top_profiles:
            user_rating = prof.rating if prof.rating is not None else 0
            user_rank = prof.display_rank or ('Unrated' if user_rating == 0 else 'Newbie')
            top_users.append({
                'username': prof.user.username,
                'display_name': prof.user.get_full_name() or prof.user.username,
                'rating': user_rating,
                'rank': user_rank,
                'solved_count': prof.problem_count or 0
            })

        # Recent Submissions
        recent_subs_qs = Submission.objects.select_related('problem', 'language', 'user__user').order_by('-date')[:6]
        recent_subs = []
        for s in recent_subs_qs:
            recent_subs.append({
                'id': s.id,
                'problem_code': s.problem.code if s.problem else (s.problem_code or ''),
                'problem_name': s.problem.name if s.problem else '',
                'user': s.user.user.username if s.user and s.user.user else 'Anonymous',
                'language': s.language.name if s.language else 'Code',
                'result': s.result or s.status,
                'score': s.points or 0,
                'time_ms': s.time,
                'date': s.date.strftime('%H:%M %d/%m/%Y') if s.date else ''
            })

        # Official Announcements / News
        announcements = [
            {
                'id': 1,
                'title': 'Kỳ thi HSG Tin học 2026 - Thử thách thuật toán toàn quốc',
                'summary': 'Kỳ thi chính thức mở cổng tham gia với 4 bài toán đặc sắc từ mức độ Cơ bản đến Olympic.',
                'date': 'Hôm nay',
                'tag': 'Contest',
                'link': '/contests/hsg-tin-2026'
            },
            {
                'id': 2,
                'title': 'Ra mắt CodePro Wiki 2.0 - Kho tàng thuật toán và cấu trúc dữ liệu',
                'summary': 'Hệ thống tài liệu chuyên đề chi tiết từ cơ bản C++ đến Quy hoạch động và Đồ thị nâng cao.',
                'date': 'Mới nhất',
                'tag': 'Wiki',
                'link': '/wiki'
            },
            {
                'id': 3,
                'title': 'Cập nhật hệ thống chấm bài tự động và Live Leaderboard thời gian thực',
                'summary': 'Cải thiện tốc độ biên dịch và thực thi sandbox sandbox, hỗ trợ chi tiết từng testcase.',
                'date': 'Tuần này',
                'tag': 'Hệ thống',
                'link': '/submissions'
            }
        ]

        return Response({
            'status': 'success',
            'stats': {
                'users': total_users,
                'problems': total_problems,
                'submissions': total_subs,
                'contests': total_contests,
                'ac_count': total_ac
            },
            'featured_contest': featured_contest,
            'featured_problems': prob_list,
            'top_users': top_users,
            'recent_submissions': recent_subs,
            'announcements': announcements
        })
