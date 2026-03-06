from unittest.mock import MagicMock

import sqlite3

from app.repositories.user_repository import UserRepository


def test_user_repository_recreates_schema_if_missing(tmp_path):
    db_path = tmp_path / "users.db"
    settings = MagicMock()
    settings.database.url = f"sqlite:///{db_path}"

    repo = UserRepository(settings)

    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE users")

    assert repo.get_by_user_id("missing") is None
