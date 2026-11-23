"""测试夹具：内存 SQLite + 依赖覆盖，不碰开发数据库。"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.deps import get_db
from app.main import app as fastapi_app
import app.models  # noqa: F401  确保模型注册到 Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def clean_db():
    """每个用例前重建表，保证用例间数据隔离。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(fastapi_app)


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "secret123"},
    )
    resp = client.post(
        "/api/auth/login", data={"username": "alice", "password": "secret123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
