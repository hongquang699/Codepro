"""Granular permission definitions."""
from typing import Dict, Set
from security.authorization.roles.role_definitions import SystemRole

class Permissions:
    # Problem permissions
    PROBLEM_VIEW = "problem:view"
    PROBLEM_CREATE = "problem:create"
    PROBLEM_UPDATE = "problem:update"
    PROBLEM_DELETE = "problem:delete"
    PROBLEM_PUBLISH = "problem:publish"
    TESTCASE_VIEW_HIDDEN = "testcase:view_hidden"
    TESTCASE_MANAGE = "testcase:manage"
    CHECKER_MANAGE = "checker:manage"
    SOLUTION_VIEW = "solution:view"

    # Submission permissions
    SUBMISSION_CREATE = "submission:create"
    SUBMISSION_VIEW = "submission:view"
    SUBMISSION_VIEW_SOURCE = "submission:view_source"
    SUBMISSION_REJUDGE = "submission:rejudge"

    # Contest permissions
    CONTEST_VIEW = "contest:view"
    CONTEST_CREATE = "contest:create"
    CONTEST_UPDATE = "contest:update"
    CONTEST_DELETE = "contest:delete"
    CONTEST_MANAGE_PARTICIPANTS = "contest:manage_participants"
    CONTEST_UNFREEZE_SCOREBOARD = "contest:unfreeze_scoreboard"

    # Judge permissions
    JUDGE_VIEW_WORKERS = "judge:view_workers"
    JUDGE_MANAGE_WORKERS = "judge:manage_workers"
    JUDGE_REJUDGE_BATCH = "judge:rejudge_batch"

    # Admin permissions
    USER_MANAGE = "user:manage"
    ROLE_ASSIGN = "role:assign"
    SYSTEM_CONFIG = "system:config"
    AUDIT_VIEW = "audit:view"

# Mapping roles to default permissions
ROLE_PERMISSIONS: Dict[SystemRole, Set[str]] = {
    SystemRole.USER: {
        Permissions.PROBLEM_VIEW,
        Permissions.SUBMISSION_CREATE,
        Permissions.SUBMISSION_VIEW,
        Permissions.CONTEST_VIEW,
    },
    SystemRole.PROBLEM_SETTER: {
        Permissions.PROBLEM_CREATE,
        Permissions.PROBLEM_UPDATE,
        Permissions.PROBLEM_PUBLISH,
        Permissions.TESTCASE_VIEW_HIDDEN,
        Permissions.TESTCASE_MANAGE,
        Permissions.CHECKER_MANAGE,
        Permissions.SOLUTION_VIEW,
    },
    SystemRole.CONTEST_MANAGER: {
        Permissions.CONTEST_CREATE,
        Permissions.CONTEST_UPDATE,
        Permissions.CONTEST_DELETE,
        Permissions.CONTEST_MANAGE_PARTICIPANTS,
        Permissions.CONTEST_UNFREEZE_SCOREBOARD,
    },
    SystemRole.JUDGE_MANAGER: {
        Permissions.JUDGE_VIEW_WORKERS,
        Permissions.JUDGE_MANAGE_WORKERS,
        Permissions.JUDGE_REJUDGE_BATCH,
        Permissions.SUBMISSION_REJUDGE,
    },
    SystemRole.MODERATOR: {
        Permissions.PROBLEM_VIEW,
        Permissions.SUBMISSION_VIEW,
        Permissions.USER_MANAGE,
    },
    SystemRole.ADMINISTRATOR: {
        Permissions.SUBMISSION_VIEW_SOURCE,
        Permissions.SUBMISSION_REJUDGE,
        Permissions.USER_MANAGE,
        Permissions.AUDIT_VIEW,
    },
    SystemRole.SUPER_ADMIN: {
        Permissions.PROBLEM_DELETE,
        Permissions.ROLE_ASSIGN,
        Permissions.SYSTEM_CONFIG,
    }
}
