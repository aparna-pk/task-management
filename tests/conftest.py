import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# In-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create a session-scoped event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_db():
    """Create tables in the test database and tear down after each test function."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session fixture."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient for route testing and override database sessions."""

    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def normal_user(client: AsyncClient) -> dict:
    """Fixture to register a normal test user and return their register payload."""
    user_data = {
        "email": "user@example.com",
        "password": "strongpassword123",
        "full_name": "Normal User",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest_asyncio.fixture(scope="function")
async def normal_user_token(client: AsyncClient, normal_user: dict) -> str:
    """Fixture to log in the normal user and return their JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": normal_user["email"], "password": normal_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def auth_headers(normal_user_token: str) -> dict:
    """Fixture to return auth headers for the normal user."""
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest_asyncio.fixture(scope="function")
async def other_user(client: AsyncClient) -> dict:
    """Fixture to register a second test user and return their register payload."""
    user_data = {
        "email": "other@example.com",
        "password": "otherpassword123",
        "full_name": "Other User",
    }
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return user_data


@pytest_asyncio.fixture(scope="function")
async def other_user_token(client: AsyncClient, other_user: dict) -> str:
    """Fixture to log in the second user and return their JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": other_user["email"], "password": other_user["password"]},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture(scope="function")
async def other_auth_headers(other_user_token: str) -> dict:
    """Fixture to return auth headers for the second user."""
    return {"Authorization": f"Bearer {other_user_token}"}

