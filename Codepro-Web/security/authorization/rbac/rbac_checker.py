"""Hierarchical RBAC evaluator."""
from typing import Set, Union
from security.authorization.roles.role_definitions import SystemRole, ROLE_HIERARCHY
from security.authorization.permissions.permission_registry import Permissions, ROLE_PERMISSIONS

class RBACChecker:
    @classmethod
    def get_all_roles(cls, role: Union[SystemRole, str]) -> Set[SystemRole]:
        """Resolves role inheritance."""
        try:
            r = SystemRole(role)
        except ValueError:
            return {SystemRole.USER}

        resolved = {r}
        stack = [r]
        while stack:
            curr = stack.pop()
            for inherited in ROLE_HIERARCHY.get(curr, []):
                if inherited not in resolved:
                    resolved.add(inherited)
                    stack.append(inherited)
        return resolved

    @classmethod
    def get_permissions_for_role(cls, role: Union[SystemRole, str]) -> Set[str]:
        all_roles = cls.get_all_roles(role)
        perms = set()
        for r in all_roles:
            perms.update(ROLE_PERMISSIONS.get(r, set()))
        return perms

    @classmethod
    def has_permission(cls, user_role: Union[SystemRole, str], permission: str) -> bool:
        if user_role == SystemRole.SUPER_ADMIN or str(user_role).lower() in ('super-admin', 'superadmin'):
            return True
        perms = cls.get_permissions_for_role(user_role)
        return permission in perms
