from django.db.models import Q


DISPLAY_TARGETS = {'both', 'web', 'client'}


def valid_display_target(value):
    return isinstance(value, str) and value in DISPLAY_TARGETS


def request_surface(request):
    return 'client' if request.headers.get('X-CodeProOJ-Surface') == 'client' else 'web'


def visible_contests(surface):
    return Q(is_visible=True) & Q(display_target__in=['both', surface])


def contest_visible(contest, surface):
    return contest.is_visible and contest.display_target in ('both', surface)
