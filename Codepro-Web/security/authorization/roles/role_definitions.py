"""Role definitions and inheritance tree."""
from enum import Enum
from typing import Dict, List, Set

class SystemRole(str, Enum):
    USER = "user"
    PROBLEM_SETTER = "problem-setter"
    TEACHER = "teacher"
    MODERATOR = "moderator"
    CONTEST_MANAGER = "contest-manager"
    JUDGE_MANAGER = "judge-manager"
    ADMINISTRATOR = "administrator"
    SUPER_ADMIN = "super-admin"

# Role hierarchy: child roles inherit all permissions from parents
ROLE_HIERARCHY: Dict[SystemRole, List[SystemRole]] = {
    SystemRole.SUPER_ADMIN: [SystemRole.ADMINISTRATOR],
    SystemRole.ADMINISTRATOR: [SystemRole.JUDGE_MANAGER, SystemRole.CONTEST_MANAGER, SystemRole.MODERATOR, SystemRole.PROBLEM_SETTER],
    SystemRole.JUDGE_MANAGER: [SystemRole.USER],
    SystemRole.CONTEST_MANAGER: [SystemRole.USER],
    SystemRole.MODERATOR: [SystemRole.USER],
    SystemRole.PROBLEM_SETTER: [SystemRole.USER],
    SystemRole.TEACHER: [SystemRole.USER],
    SystemRole.USER: []
}
