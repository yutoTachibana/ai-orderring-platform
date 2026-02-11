import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.auth.utils import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole

# ---------------------------------------------------------------------------
# Test database (SQLite in-memory)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Yield a test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """Yield a TestClient for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def test_user(db):
    """Create and return a test user persisted in the DB."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def auth_headers(test_user):
    """Return Authorization headers with a valid JWT for *test_user*."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_client(client, auth_headers):
    """Return a TestClient whose requests include a valid Bearer token."""
    client.headers.update(auth_headers)
    return client


@pytest.fixture()
def sales_user(db):
    """Create and return a sales role test user."""
    user = User(
        email="sales@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Sales User",
        role=UserRole.sales,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def sales_client(client, sales_user):
    """Return a TestClient with sales user credentials."""
    token = create_access_token(sales_user.id)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def engineer_user(db):
    """Create and return an engineer role test user."""
    user = User(
        email="engineer@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Engineer User",
        role=UserRole.engineer,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def engineer_client(client, engineer_user):
    """Return a TestClient with engineer user credentials."""
    token = create_access_token(engineer_user.id)
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
