from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamMember
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    async def get_with_members(
        self, db: AsyncSession, *, team_id: int
    ) -> Team | None:
        """Fetch a team with its members eagerly loaded."""
        result = await db.execute(
            select(self.model)
            .options(selectinload(Team.members))
            .filter(self.model.id == team_id)
        )
        return result.scalars().first()

    async def get_teams_for_user(
        self, db: AsyncSession, *, user_id: int
    ) -> list[Team]:
        """Fetch all teams a user belongs to."""
        result = await db.execute(
            select(self.model)
            .join(TeamMember)
            .filter(TeamMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_member(
        self, db: AsyncSession, *, team_id: int, user_id: int
    ) -> TeamMember | None:
        """Fetch a specific team membership."""
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def add_member(
        self, db: AsyncSession, *, team_id: int, user_id: int, role: str
    ) -> TeamMember:
        """Add a user as a member of a team."""
        member = TeamMember(team_id=team_id, user_id=user_id, role=role)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    async def update_member_role(
        self, db: AsyncSession, *, member: TeamMember, role: str
    ) -> TeamMember:
        """Update a team member's role."""
        member.role = role
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    async def remove_member(
        self, db: AsyncSession, *, member: TeamMember
    ) -> None:
        """Remove a member from a team."""
        await db.delete(member)
        await db.commit()

    async def get_team_user_ids(
        self, db: AsyncSession, *, team_id: int
    ) -> list[int]:
        """Get all user IDs in a team."""
        result = await db.execute(
            select(TeamMember.user_id).filter(TeamMember.team_id == team_id)
        )
        return list(result.scalars().all())


team_repository = TeamRepository(Team)
