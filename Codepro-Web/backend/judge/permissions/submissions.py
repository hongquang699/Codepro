def can_view_submission_details(user, submission):
    """Keep source, compiler output and testcase details with the author or staff."""
    return bool(
        user and user.is_authenticated and user.is_active and
        (user.is_staff or user.is_superuser or submission.user.user_id == user.pk)
    )
