import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app as app_module
from backend.database import Base
from backend.models import User
from backend.routers.auth import LoginRequest, RegisterRequest, login, register
from backend.services.auth import hash_password


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def test_bootstrap_does_not_duplicate_mixed_case_admin(db, monkeypatch):
    db.add(
        User(
            email="Admin@Example.com",
            hashed_password=hash_password("ExistingPassword123!"),
            is_active=1,
            is_approved=1,
        )
    )
    db.commit()
    monkeypatch.setattr(app_module, "SessionLocal", lambda: db)
    monkeypatch.setattr(app_module.settings, "DEFAULT_ADMIN_EMAIL", "admin@example.com")

    app_module._bootstrap_default_admin()

    assert db.query(User).count() == 1


def test_login_finds_mixed_case_stored_email(db):
    db.add(
        User(
            email="User@Example.com",
            hashed_password=hash_password("ValidPassword123!"),
            is_active=1,
            is_approved=1,
        )
    )
    db.commit()

    result = login(
        LoginRequest(email="user@example.com", password="ValidPassword123!"),
        db,
    )

    assert result.user.email == "User@Example.com"


def test_registration_rejects_mixed_case_stored_email(db):
    db.add(
        User(
            email="User@Example.com",
            hashed_password=hash_password("ValidPassword123!"),
        )
    )
    db.commit()

    with pytest.raises(HTTPException, match="Email already registered") as exc:
        register(
            RegisterRequest(
                email="user@example.com",
                password="AnotherPassword123!",
            ),
            db,
        )

    assert exc.value.status_code == 400
