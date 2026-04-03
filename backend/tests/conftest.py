"""测试公共夹具。"""

import os
from collections.abc import Generator
from importlib import import_module
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DB_BACKEND", "sqlite")
os.environ.setdefault("DB_AUTO_FALLBACK_SQLITE", "false")
os.environ.setdefault("SQLITE_PATH", "backend/test.db")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_FALLBACK_PROVIDER", "none")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def _create_test_app_and_db():
    _ = import_module("app.models")
    database = import_module("app.core.database")
    app = import_module("app.main").app
    Base = database.Base
    get_db = database.get_db

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.state.limiter.reset()
    return app


def _override_auth(app):
    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def mock_get_current_user():
        return CurrentUserOut(
            id=1,
            username="test_user",
            email="test@example.com",
            full_name="Test User",
            role="admin",
            is_active=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = mock_get_current_user


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = _create_test_app_and_db()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client() -> Generator[TestClient, None, None]:
    app = _create_test_app_and_db()
    _override_auth(app)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def member_client() -> Generator[TestClient, None, None]:
    """返回普通成员身份的客户端（非管理员）。"""
    app = _create_test_app_and_db()
    from app.api.v1.endpoints.auth import get_current_user
    from app.schemas.auth import CurrentUserOut

    def mock_get_current_user_as_member():
        return CurrentUserOut(
            id=999,
            username="member_user",
            email="member@example.com",
            full_name="Member User",
            role="member",
            is_active=True,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )

    app.dependency_overrides[get_current_user] = mock_get_current_user_as_member
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def safe_client() -> Generator[TestClient, None, None]:
    app = _create_test_app_and_db()
    _override_auth(app)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
