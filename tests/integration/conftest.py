from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from src.modules.org.infrastructure.models import CompanyModel, DepartmentModel, PositionModel
from src.shared.infrastructure.db.base import Base
from src.shared.infrastructure.db.session import get_db_session


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    company_id = str(uuid.uuid4())
    department_id = str(uuid.uuid4())
    position_id = str(uuid.uuid4())

    with TestingSessionLocal() as session:
        session.add(
            CompanyModel(
                id=company_id,
                name="Test Company",
                industry="Internet",
                tenant_code="test-tenant",
            )
        )
        session.add(
            DepartmentModel(
                id=department_id,
                company_id=company_id,
                name="Growth",
                domain="Growth",
            )
        )
        session.add(
            PositionModel(
                id=position_id,
                company_id=company_id,
                title="Growth Manager",
                job_family="Marketing",
                level_band="P6",
            )
        )
        session.commit()

    def override_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_db
    app.state.test_ids = {
        "company_id": company_id,
        "department_id": department_id,
        "position_id": position_id,
    }

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
