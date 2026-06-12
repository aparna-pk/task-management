from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.services.auth import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(deps.get_db)
) -> User:
    """Register a new user account."""
    return await auth_service.register(db, obj_in=user_in)


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(deps.get_db),
) -> Token:
    """Standard JSON login, returns access token for future requests."""
    user = await auth_service.authenticate(
        db, email=login_data.email, password=login_data.password
    )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)


@router.post("/login/oauth", response_model=Token)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db),
) -> Token:
    """OAuth2 compatible token login, retrieve access token for future requests."""
    user = await auth_service.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token)



@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(deps.get_current_user)) -> User:
    """Get information about the currently logged-in user."""
    return current_user
