from django.contrib.auth.models import User
from ..models import UserAchievement
from .statistics import get_user_statistics

ALL_ACHIEVEMENTS = [
    {
        'key': 'first-ac',
        'name': 'First Accepted',
        'description': 'Được chấp nhận lời giải bài tập đầu tiên trên hệ thống.',
        'icon': '🎯'
    },
    {
        'key': '10-solved',
        'name': '10 Problems Solved',
        'description': 'Đã hoàn thành và giải chính xác 10 bài tập.',
        'icon': '🥉'
    },
    {
        'key': '50-solved',
        'name': '50 Problems Solved',
        'description': 'Đã hoàn thành và giải chính xác 50 bài tập.',
        'icon': '🥈'
    },
    {
        'key': '100-solved',
        'name': '100 Problems Solved',
        'description': 'Cột mốc giải thành công 100 bài tập lập trình.',
        'icon': '🥇'
    },
    {
        'key': '500-solved',
        'name': '500 Problems Solved',
        'description': 'Kiện tướng thuật toán với hơn 500 bài giải AC.',
        'icon': '👑'
    },
    {
        'key': 'contest-participant',
        'name': 'Contest Participant',
        'description': 'Tham gia kỳ thi lập trình thi đấu chính thức đầu tiên.',
        'icon': '🏁'
    },
    {
        'key': 'contest-winner',
        'name': 'Contest Winner',
        'description': 'Giành vị trí Quán quân (Top 1) trong một kỳ thi.',
        'icon': '🏆'
    },
    {
        'key': 'streak',
        'name': 'Consistent Coder',
        'description': 'Chăm chỉ giải bài liên tục trong nhiều ngày.',
        'icon': '🔥'
    },
    {
        'key': 'problem-setter',
        'name': 'Problem Setter',
        'description': 'Tác giả sáng tạo đề bài đóng góp cho cộng đồng.',
        'icon': '💡'
    }
]

def check_and_unlock_achievements(user):
    stats = get_user_statistics(user)
    solved = stats.get('solved_problems', 0)
    contests = stats.get('contests', 0)
    wins = stats.get('contest_wins', 0)

    unlocked_keys = set(UserAchievement.objects.filter(user=user).values_list('badge_key', flat=True))

    to_unlock = []
    if solved >= 1 and 'first-ac' not in unlocked_keys:
        to_unlock.append('first-ac')
    if solved >= 10 and '10-solved' not in unlocked_keys:
        to_unlock.append('10-solved')
    if solved >= 50 and '50-solved' not in unlocked_keys:
        to_unlock.append('50-solved')
    if solved >= 100 and '100-solved' not in unlocked_keys:
        to_unlock.append('100-solved')
    if solved >= 500 and '500-solved' not in unlocked_keys:
        to_unlock.append('500-solved')
    if contests >= 1 and 'contest-participant' not in unlocked_keys:
        to_unlock.append('contest-participant')
    if wins >= 1 and 'contest-winner' not in unlocked_keys:
        to_unlock.append('contest-winner')

    meta_map = {a['key']: a for a in ALL_ACHIEVEMENTS}
    for k in to_unlock:
        meta = meta_map.get(k)
        if meta:
            UserAchievement.objects.create(
                user=user,
                badge_key=k,
                name=meta['name'],
                description=meta['description'],
                icon=meta['icon']
            )

def get_user_achievements(user):
    check_and_unlock_achievements(user)
    unlocked = UserAchievement.objects.filter(user=user)
    unlocked_map = {a.badge_key: a for a in unlocked}

    results = []
    for ach in ALL_ACHIEVEMENTS:
        is_unlocked = ach['key'] in unlocked_map
        rec = unlocked_map.get(ach['key'])
        results.append({
            'key': ach['key'],
            'name': ach['name'],
            'description': ach['description'],
            'icon': ach['icon'],
            'is_unlocked': is_unlocked,
            'unlocked_at': rec.unlocked_at.strftime('%Y-%m-%d') if rec else None
        })

    return results
