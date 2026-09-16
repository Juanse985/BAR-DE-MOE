import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Base de datos de pruebas: SQLite en memoria, aislada de la BD "real"
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_auth.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    # el admin por defecto se crea en el evento startup (config.py)
    resp = client.post("/auth/login", json={"username": "admin", "password": "Admin123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
