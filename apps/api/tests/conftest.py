"""Pytest fixtures for DeskForge API tests."""
import asyncio
import os
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import event
from sqlalchemy.pool import NullPool

# Clean up any leftover test DB
for f in ["./test.db", "./test.db-wal", "./test.db-shm"]:
    if os.path.exists(f):
        os.remove(f)

# Override settings for testing — MUST be before any src imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["APP_SECRET_KEY"] = "test-secret-key-123456789012345678901234567890"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-123456789012345678901234567890"
os.environ["ENCRYPTION_KEY"] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

from src.database import Base

# File-based SQLite engine with NullPool (no connection reuse)
test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Monkey-patch jwt module to use test session factory
import src.auth.jwt as _jwt_module
_jwt_module.async_session_factory = test_session_factory


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables for testing."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables(setup_database):
    """Delete all data before each test."""
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def app(setup_database):
    """Create a test FastAPI app with overridden dependencies."""
    from src.main import create_app
    from src.dependencies import get_db

    application = create_app()

    async def override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user in the database."""
    from src.models.user import User
    from src.auth.password import hash_password

    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=hash_password("TestPass123!"),
        name="Test User",
        email_verified=True,
        auth_provider="local",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_team(db_session: AsyncSession, test_user):
    """Create a test team with the test user as owner."""
    from src.models.team import Team
    from src.models.team_member import TeamMember
    from datetime import datetime, timezone

    team = Team(
        id=uuid4(),
        name="Test Team",
        owner_id=test_user.id,
        plan="free",
    )
    db_session.add(team)

    membership = TeamMember(
        id=uuid4(),
        team_id=team.id,
        user_id=test_user.id,
        role="owner",
        invited_at=datetime.now(timezone.utc),
        accepted_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(team)
    return team


@pytest_asyncio.fixture
async def test_editor_user(db_session: AsyncSession, test_team):
    """Create a test editor user."""
    from src.models.user import User
    from src.models.team_member import TeamMember
    from src.auth.password import hash_password
    from datetime import datetime, timezone

    user = User(
        id=uuid4(),
        email="editor@example.com",
        password_hash=hash_password("EditorPass123!"),
        name="Editor User",
        email_verified=True,
        auth_provider="local",
    )
    db_session.add(user)

    membership = TeamMember(
        id=uuid4(),
        team_id=test_team.id,
        user_id=user.id,
        role="editor",
        invited_at=datetime.now(timezone.utc),
        accepted_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def auth_headers(user) -> dict:
    """Generate valid JWT auth headers for a user."""
    from src.auth.jwt import create_access_token
    token = create_access_token(user.id, user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_header_owner(test_user) -> dict:
    """Auth headers for the owner user."""
    return auth_headers(test_user)


@pytest_asyncio.fixture
async def auth_header_editor(test_editor_user) -> dict:
    """Auth headers for the editor user."""
    return auth_headers(test_editor_user)


@pytest_asyncio.fixture
async def test_tool(db_session: AsyncSession, test_user, test_team):
    """Create a test tool."""
    from src.models.tool import Tool

    tool = Tool(
        id=uuid4(),
        team_id=test_team.id,
        created_by=test_user.id,
        name="Test Tool",
        slug="test-tool",
        description="A test tool",
        prompt="Create a dashboard showing sales data",
        spec={
            "version": 1,
            "name": "Test Tool",
            "layout": {"type": "grid", "columns": 12, "gap": "16px"},
            "components": [],
            "dataSources": [],
            "theme": {},
        },
        visibility="private",
        status="active",
    )
    db_session.add(tool)
    await db_session.commit()
    await db_session.refresh(tool)
    return tool


@pytest.fixture
def mock_llm(monkeypatch):
    """Mock OpenAI API calls for generation tests."""
    import json
    from unittest.mock import AsyncMock, MagicMock

    mock_spec = {
        "version": 1,
        "name": "Mock Tool",
        "layout": {"type": "grid", "columns": 12, "gap": "16px"},
        "components": [
            {
                "id": "comp-1",
                "type": "dataTable",
                "position": {"row": 0, "col": 0, "colSpan": 12},
                "props": {"title": "Data Table"},
            }
        ],
        "dataSources": [],
        "theme": {},
    }

    class MockChoice:
        def __init__(self, content):
            self.message = MagicMock()
            self.message.content = content
            self.finish_reason = "stop"

    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 100
            self.completion_tokens = 200
            self.total_tokens = 300

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
            self.usage = MockUsage()

    class MockAsyncCompletions:
        async def create(self, **kwargs):
            content = json.dumps({"spec": mock_spec, "explanation": "Generated mock tool"})
            return MockResponse(content)

    class MockAsyncClient:
        def __init__(self, **kwargs):
            self.chat = MagicMock()
            self.chat.completions = MockAsyncCompletions()

    # Patch the OpenAI AsyncOpenAI class
    monkeypatch.setattr("openai.AsyncOpenAI", MockAsyncClient)

    return mock_spec
