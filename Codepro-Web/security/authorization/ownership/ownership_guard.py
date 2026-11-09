"""Resource ownership verification."""
from typing import Optional

class OwnershipGuard:
    @staticmethod
    def can_view_source(request_user: str, submission_owner: str, user_role: str = 'user', contest_freeze: bool = False) -> bool:
        if not request_user:
            return False
        # Super admin / Admin can always view
        if user_role in ('super-admin', 'administrator', 'admin'):
            return True
        # If scoreboard is frozen in contest, even owner cannot peek other sources
        if request_user.lower() == submission_owner.lower():
            return True
        return False

    @staticmethod
    def can_edit_problem(request_user: str, problem_author: str, user_role: str = 'user') -> bool:
        if user_role in ('super-admin', 'administrator', 'admin'):
            return True
        if user_role == 'problem-setter' and request_user.lower() == (problem_author or '').lower():
            return True
        return False
