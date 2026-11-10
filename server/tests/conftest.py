from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, initialize_database


@pytest.fixture()
def db(tmp_path):
    engine = create_engine(
        "sqlite:///" + str(tmp_path / "test.sqlite3"),
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    engine.dispose()
