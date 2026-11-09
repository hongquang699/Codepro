from backend.community.models import Post, Thread, Follow
from backend.judge.models import Contest, Problem, Profile
from django.utils import timezone

class FeedService:
    @staticmethod
    def get_community_feed(user=None, limit=20):
        # 1. Pinned and recent posts
        posts = Post.objects.filter(is_hidden=False).select_related('author__user').order_by('-is_pinned', '-created_at')[:limit]
        
        # 2. Top trending threads
        threads = Thread.objects.filter(is_hidden=False).select_related('author__user', 'category').order_by('-last_activity_at')[:5]

        # 3. Upcoming contests
        now = timezone.now()
        from backend.judge.contest_visibility import visible_contests
        upcoming_contests = Contest.objects.filter(visible_contests('web'), end_time__gt=now).order_by('start_time')[:3]

        # 4. Top community coders
        top_coders = Profile.objects.select_related('user').order_by('-rating', '-problem_count')[:5]

        return {
            'posts': posts,
            'trending_threads': threads,
            'upcoming_contests': upcoming_contests,
            'top_coders': top_coders
        }
