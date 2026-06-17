from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.team import TeamRole


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1024)


class TeamUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1024)


class TeamMemberAdd(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    role: TeamRole


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    team_id: int
    role: TeamRole
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    members: list[TeamMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)


class TeamListResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
