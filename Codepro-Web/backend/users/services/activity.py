from datetime import datetime, timedelta
from django.utils import timezone
from ..models import UserActivity
from backend.judge.models import Submission, ContestParticipation

def get_user_activity(user, limit=30):
    activities = []

    # 1. Activities from UserActivity table
    saved_acts = UserActivity.objects.filter(user=user).order_by('-created_at')[:limit]
    for act in saved_acts:
        activities.append({
            'type': act.activity_type,
            'title': act.title,
            'description': act.description,
            'link': act.link,
            'timestamp': act.created_at.isoformat(),
            'time_display': act.created_at.strftime('%H:%M - %d/%m/%Y')
        })

    # 2. Derive recent submissions as activities
    recent_subs = Submission.objects.filter(user__user=user).select_related('problem', 'contest').order_by('-date')[:15]
    for s in recent_subs:
        prob_name = s.problem.name if s.problem else (s.problem_code or 'Unknown')
        prob_code = s.problem.code if s.problem else (s.problem_code or '')
        is_ac = (s.result == 'AC')
        title = f"{'Giải thành công' if is_ac else 'Đã nộp bài'} {prob_code} - {prob_name}"
        desc = f"Kết quả: {s.result or s.status} ({s.points or 0} điểm) • {s.language.name if s.language else 'Code'}"
        sub_link = f"/submissions/{s.id}"

        # check if not already added
        if not any(a['title'] == title and a['link'] == sub_link for a in activities):
            activities.append({
                'type': 'submission',
                'title': title,
                'description': desc,
                'link': sub_link,
                'timestamp': s.date.isoformat() if s.date else timezone.now().isoformat(),
                'time_display': s.date.strftime('%H:%M - %d/%m/%Y') if s.date else ''
            })

    # 3. Derive recent contest joins
    recent_contests = ContestParticipation.objects.filter(user__user=user).select_related('contest').order_by('-id')[:5]
    for cp in recent_contests:
        c_name = cp.contest.name if cp.contest else 'Kỳ thi'
        c_slug = cp.contest.key if cp.contest else ''
        title = f"Tham gia cuộc thi {c_name}"
        desc = f"Điểm đạt được: {cp.score} điểm"
        c_link = f"/contests/{c_slug}"
        cp_date = cp.real_start or timezone.now()
        if not any(a['title'] == title for a in activities):
            activities.append({
                'type': 'contest',
                'title': title,
                'description': desc,
                'link': c_link,
                'timestamp': cp_date.isoformat(),
                'time_display': cp_date.strftime('%H:%M - %d/%m/%Y')
            })

    # Sort all by timestamp descending
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]
