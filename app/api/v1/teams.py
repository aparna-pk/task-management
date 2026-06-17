from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberResponse,
    TeamResponse,
    TeamUpdate,
)
from app.services.team import team_service

router = APIRouter()


@router.post("", response_model=TeamResponse, status_code=201)
async def create_team(
    team_in: TeamCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Team:
    """Create a new team and add the current user as owner."""
    return await team_service.create_team(db, obj_in=team_in, owner_id=current_user.id)


@router.get("", response_model=list[TeamListResponse])
async def read_user_teams(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> list[Team]:
    """Retrieve all teams the current user belongs to."""
    return await team_service.get_user_teams(db, user_id=current_user.id)


@router.get("/{team_id}", response_model=TeamResponse)
async def read_team(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Team:
    """Retrieve details of a specific team. User must be a member."""
    return await team_service.get_team(db, team_id=team_id, user_id=current_user.id)


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    team_in: TeamUpdate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Team:
    """Update team details. Only OWNER or ADMIN of the team can perform this."""
    return await team_service.update_team(
        db, team_id=team_id, obj_in=team_in, user_id=current_user.id
    )


@router.delete("/{team_id}", response_model=TeamResponse)
async def delete_team(
    team_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Team:
    """Delete a team. Only OWNER can perform this."""
    return await team_service.delete_team(db, team_id=team_id, user_id=current_user.id)


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=201)
async def add_team_member(
    team_id: int,
    member_in: TeamMemberAdd,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> TeamMember:
    """Add a member to a team. Only OWNER or ADMIN can perform this."""
    return await team_service.add_member(
        db, team_id=team_id, member_data=member_in, user_id=current_user.id
    )


@router.put("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member_role(
    team_id: int,
    user_id: int,
    role: TeamRole,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> TeamMember:
    """Update a team member's role. Only OWNER can perform this."""
    return await team_service.update_member_role(
        db,
        team_id=team_id,
        member_user_id=user_id,
        role=role,
        user_id=current_user.id,
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
) -> Response:
    """Remove a member from a team. OWNER/ADMIN can remove, or user can leave."""
    await team_service.remove_member(
        db, team_id=team_id, member_user_id=user_id, user_id=current_user.id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
