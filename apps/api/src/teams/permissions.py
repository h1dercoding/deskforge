from src.models.team_member import TeamMember
from src.exceptions import InsufficientRoleError, NotTeamMemberError

ROLE_HIERARCHY = {"viewer": 0, "editor": 1, "owner": 2}


def check_role(membership: TeamMember, required_role: str) -> bool:
    """Check if a membership has at least the required role."""
    if membership is None:
        raise NotTeamMemberError()
    return ROLE_HIERARCHY.get(membership.role, -1) >= ROLE_HIERARCHY.get(required_role, 0)


def require_owner(membership: TeamMember) -> None:
    if not check_role(membership, "owner"):
        raise InsufficientRoleError("owner")


def require_editor(membership: TeamMember) -> None:
    if not check_role(membership, "editor"):
        raise InsufficientRoleError("editor")


def require_member(membership: TeamMember) -> None:
    if not check_role(membership, "viewer"):
        raise InsufficientRoleError("viewer")
