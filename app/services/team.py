from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.team import Team, TeamMember, TeamRole
from app.repositories.team import team_repository
from app.repositories.user import user_repository
from app.schemas.team import TeamCreate, TeamMemberAdd, TeamUpdate


class TeamService:
    async def create_team(
        self, db: AsyncSession, *, obj_in: TeamCreate, owner_id: int
    ) -> Team:
        """Create a new team and add the creator as OWNER."""
        team = await team_repository.create(db, obj_in=obj_in)
        await team_repository.add_member(
            db, team_id=team.id, user_id=owner_id, role=TeamRole.OWNER
        )
        # Re-fetch with members loaded
        fetched_team = await team_repository.get_with_members(db, team_id=team.id)
        if not fetched_team:
            raise NotFoundException(message="Team not found after creation.")
        return fetched_team

    async def get_team(self, db: AsyncSession, *, team_id: int, user_id: int) -> Team:
        """Get a team by ID. User must be a member."""
        team = await team_repository.get_with_members(db, team_id=team_id)
        if not team:
            raise NotFoundException(message="Team not found.")
        member = await team_repository.get_member(db, team_id=team_id, user_id=user_id)
        if not member:
            raise ForbiddenException(message="You are not a member of this team.")
        return team

    async def get_user_teams(self, db: AsyncSession, *, user_id: int) -> list[Team]:
        """Get all teams a user belongs to."""
        return await team_repository.get_teams_for_user(db, user_id=user_id)

    async def update_team(
        self, db: AsyncSession, *, team_id: int, obj_in: TeamUpdate, user_id: int
    ) -> Team:
        """Update a team. Only OWNER or ADMIN can update."""
        team = await team_repository.get(db, id=team_id)
        if not team:
            raise NotFoundException(message="Team not found.")
        await self._require_admin(db, team_id=team_id, user_id=user_id)
        updated = await team_repository.update(db, db_obj=team, obj_in=obj_in)
        fetched_team = await team_repository.get_with_members(db, team_id=updated.id)
        if not fetched_team:
            raise NotFoundException(message="Team not found after update.")
        return fetched_team

    async def delete_team(
        self, db: AsyncSession, *, team_id: int, user_id: int
    ) -> Team:
        """Delete a team. Only OWNER can delete."""
        team = await team_repository.get(db, id=team_id)
        if not team:
            raise NotFoundException(message="Team not found.")
        member = await team_repository.get_member(db, team_id=team_id, user_id=user_id)
        if not member or member.role != TeamRole.OWNER:
            raise ForbiddenException(message="Only the team owner can delete the team.")
        await team_repository.remove(db, id=team_id)
        return team

    async def add_member(
        self,
        db: AsyncSession,
        *,
        team_id: int,
        member_data: TeamMemberAdd,
        user_id: int,
    ) -> TeamMember:
        """Add a member to a team. Only OWNER or ADMIN can add members."""
        team = await team_repository.get(db, id=team_id)
        if not team:
            raise NotFoundException(message="Team not found.")
        await self._require_admin(db, team_id=team_id, user_id=user_id)

        # Check target user exists
        target_user = await user_repository.get(db, id=member_data.user_id)
        if not target_user:
            raise NotFoundException(message="User not found.")

        # Check if already a member
        existing = await team_repository.get_member(
            db, team_id=team_id, user_id=member_data.user_id
        )
        if existing:
            raise BadRequestException(message="User is already a member of this team.")

        return await team_repository.add_member(
            db,
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )

    async def update_member_role(
        self,
        db: AsyncSession,
        *,
        team_id: int,
        member_user_id: int,
        role: TeamRole,
        user_id: int,
    ) -> TeamMember:
        """Update a member's role. Only OWNER can change roles."""
        member = await team_repository.get_member(db, team_id=team_id, user_id=user_id)
        if not member or member.role != TeamRole.OWNER:
            raise ForbiddenException(
                message="Only the team owner can change member roles."
            )

        target_member = await team_repository.get_member(
            db, team_id=team_id, user_id=member_user_id
        )
        if not target_member:
            raise NotFoundException(message="Member not found in this team.")

        return await team_repository.update_member_role(
            db, member=target_member, role=role
        )

    async def remove_member(
        self,
        db: AsyncSession,
        *,
        team_id: int,
        member_user_id: int,
        user_id: int,
    ) -> None:
        """Remove a member from a team. OWNER/ADMIN can remove, or user can leave."""
        target_member = await team_repository.get_member(
            db, team_id=team_id, user_id=member_user_id
        )
        if not target_member:
            raise NotFoundException(message="Member not found in this team.")

        # Allow self-removal (leaving) unless OWNER
        if member_user_id == user_id:
            if target_member.role == TeamRole.OWNER:
                raise BadRequestException(
                    message="Team owner cannot leave. "
                    "Transfer ownership or delete the team."
                )
            await team_repository.remove_member(db, member=target_member)
            return

        # Otherwise, require admin privileges
        await self._require_admin(db, team_id=team_id, user_id=user_id)
        if target_member.role == TeamRole.OWNER:
            raise ForbiddenException(message="Cannot remove the team owner.")
        await team_repository.remove_member(db, member=target_member)

    async def is_team_member(
        self, db: AsyncSession, *, team_id: int, user_id: int
    ) -> bool:
        """Check if a user is a member of a team."""
        member = await team_repository.get_member(db, team_id=team_id, user_id=user_id)
        return member is not None

    async def _require_admin(
        self, db: AsyncSession, *, team_id: int, user_id: int
    ) -> TeamMember:
        """Verify the user is an OWNER or ADMIN of the team."""
        member = await team_repository.get_member(db, team_id=team_id, user_id=user_id)
        if not member or member.role not in (TeamRole.OWNER, TeamRole.ADMIN):
            raise ForbiddenException(
                message="You do not have admin privileges for this team."
            )
        return member


team_service = TeamService()
