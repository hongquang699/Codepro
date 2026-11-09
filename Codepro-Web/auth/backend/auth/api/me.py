from django.http import JsonResponse
from django.views.decorators.http import require_GET
from backend.auth.security.auth_required import get_authenticated_user_from_request
from backend.users.models.profile import UserProfile
from backend.ranking.models.rating import UserRating


@require_GET
def me_view(request):
    """
    GET /api/v1/auth/me
    Returns current authenticated user details and profile info.
    """
    user = get_authenticated_user_from_request(request)
    if not user:
        return JsonResponse({
            'authenticated': False,
            'user': None
        }, status=401)

    profile = UserProfile.objects.filter(user=user).first()
    rating_obj = UserRating.objects.filter(user=user).first()

    is_admin = bool(user.is_staff or user.is_superuser or user.username.lower() in ['admin', 'root'])
    user_role = 'admin' if is_admin else 'user'

    return JsonResponse({
        'authenticated': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': profile.display_name if profile and profile.display_name else user.username,
            'avatar': profile.avatar if profile and profile.avatar else '/frontend/assets/images/default-avatar.svg',
            'rating': rating_obj.rating if rating_obj else 1500,
            'rank_title': rating_obj.rank if rating_obj else 'Specialist',
            'role': user_role,
            'is_admin': is_admin,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined.isoformat(),
        }
    }, status=200)
