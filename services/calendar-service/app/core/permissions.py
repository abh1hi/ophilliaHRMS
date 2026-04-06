"""Fine-grained RBAC permission matrix for calendar-service.

Permission checks happen at the service layer, not just at the role level.
Dynamic subjects ("creator", "assignee", "author") are checked against resource ownership.
"""
from fastapi import HTTPException, status
from uuid import UUID

from app.core.constants import UserRole

# Static role-based permissions
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "workspace:read":   [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE],
    "workspace:write":  [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR],
    "workspace:delete": [UserRole.SUPER_ADMIN, UserRole.ADMIN],
    "member:manage":    [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR],
    "calendar:read":    [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE],
    "calendar:write":   [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE],
    "calendar:delete":  [UserRole.SUPER_ADMIN, UserRole.ADMIN],
    "event:create":     [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE],
    "event:update":     [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "creator" (dynamic)
    "event:delete":     [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "creator" (dynamic)
    "task:create":      [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.EMPLOYEE],
    "task:assign":      [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "creator" (dynamic)
    "task:status":      [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "assignee"/"creator" (dynamic)
    "task:delete":      [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "creator" (dynamic)
    "comment:edit":     [],                                        # only "author" (dynamic)
    "comment:delete":   [UserRole.SUPER_ADMIN, UserRole.ADMIN],   # + "author" (dynamic)
    "audit:read":       [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.HR],
}


def check_permission(
    permission: str,
    current_user_role: str,
    current_user_id: UUID | str | None = None,
    resource_owner_id: UUID | str | None = None,
    assignee_ids: list[UUID | str] | None = None,
) -> None:
    """Raise HTTP 403 if the current user lacks the named permission.

    Dynamic subject checks (creator/assignee/author) compare current_user_id
    against resource_owner_id or assignee_ids.
    """
    try:
        role = UserRole(current_user_role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role")

    allowed_roles = ROLE_PERMISSIONS.get(permission, [])

    # Static role check
    if role in allowed_roles:
        return

    # Dynamic subject checks
    if current_user_id is not None:
        uid = str(current_user_id)
        # "creator" or "author" check
        if resource_owner_id is not None and uid == str(resource_owner_id):
            return
        # "assignee" check
        if assignee_ids is not None and uid in [str(a) for a in assignee_ids]:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Insufficient permissions for '{permission}'",
    )
