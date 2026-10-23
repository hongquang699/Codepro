from django.contrib.auth.models import User
from django.utils import timezone
from ..models import UserProfile, UserRating, UserStatistics

def get_or_create_profile(user):
    prof, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'display_name': user.get_full_name() or user.username,
            'country': 'Vietnam'
        }
    )
    # Check if judge.models.Profile exists to sync rating/about
    try:
        from backend.judge.models import Profile as JudgeProfile
        jp = JudgeProfile.objects.filter(user=user).first()
        if jp and not prof.bio and jp.about:
            prof.bio = jp.about
            prof.save(update_fields=['bio'])
    except Exception:
        pass
    return prof

def get_profile_data(username):
    user = User.objects.filter(username=username).first()
    if not user:
        return None

    prof = UserProfile.objects.filter(user=user).first()
    if prof is None:
        prof = UserProfile(user=user, display_name=user.get_full_name() or user.username, country='Vietnam')
    
    # Rating & Rank
    rating_val = 0
    rank_name = 'Unrated'
    is_verified = False
    judge_bio = ''
    try:
        from backend.judge.models import Profile as JudgeProfile
        jp = JudgeProfile.objects.filter(user=user).first()
        if jp:
            judge_bio = jp.about or ''
            rating_val = jp.rating if jp.rating is not None else 0
            rank_name = jp.display_rank or ('Unrated' if rating_val == 0 else 'Newbie')
            is_verified = getattr(jp, 'is_verified', False)
        else:
            ur = UserRating.objects.filter(user=user).first()
            if ur:
                rating_val = ur.current_rating if getattr(ur, 'contest_count', 0) > 0 else 0
                rank_name = ur.rank if getattr(ur, 'contest_count', 0) > 0 else 'Unrated'
    except Exception:
        pass

    # Solved count
    solved_count = 0
    try:
        from backend.judge.models import Submission
        solved_count = Submission.objects.filter(user__user=user, result='AC').values('problem').distinct().count()
    except Exception:
        pass

    return {
        'user_id': user.id,
        'username': user.username,
        'email': user.email if user.email else '',
        'display_name': prof.display_name or user.get_full_name() or user.username,
        'avatar': prof.avatar or '',
        'cover': prof.cover or '',
        'bio': prof.bio or judge_bio,
        'country': prof.country or 'Vietnam',
        'school': prof.school or '',
        'organization': prof.organization or '',
        'website': prof.website or '',
        'github': prof.github or '',
        'created_at': prof.created_at.isoformat() if prof.created_at else user.date_joined.isoformat(),
        'last_seen': prof.last_seen.isoformat() if prof.last_seen else (user.last_login.isoformat() if user.last_login else ''),
        'rating': rating_val,
        'rank': rank_name,
        'solved_count': solved_count,
        'is_verified': is_verified,
        'is_staff': user.is_staff or user.is_superuser,
    }

def update_profile(user, data):
    prof = get_or_create_profile(user)
    fields = ['display_name', 'bio', 'country', 'school', 'organization', 'website', 'github', 'avatar', 'cover']
    updated = []
    for f in fields:
        if f in data:
            setattr(prof, f, data[f])
            updated.append(f)
    if updated:
        prof.last_seen = timezone.now()
        updated.append('last_seen')
        prof.save(update_fields=updated)
    return prof
