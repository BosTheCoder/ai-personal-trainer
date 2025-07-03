import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

database_path = os.path.join(os.path.dirname(__file__), "..", "database")
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if database_path not in sys.path:
    sys.path.insert(0, database_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from migrate import (  # noqa: E402
    generate_create_table_sql,
    get_sql_type,
    migrate_database,
)

from app.models import Goal, UserSettings  # noqa: E402


@pytest.fixture
def temp_db():
    """Create temporary database for testing migrations."""
    temp_dir = tempfile.mkdtemp()

    import migrate

    original_connect = migrate.connect_db

    db_file_path = Path(temp_dir) / "test_migration.db"

    def mock_connect():
        db_file_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_file_path))
        conn.row_factory = sqlite3.Row
        return conn

    migrate.connect_db = mock_connect

    yield temp_dir

    migrate.connect_db = original_connect
    shutil.rmtree(temp_dir)


def test_migrate_database_creates_tables(temp_db):
    """Test that migrate_database creates all expected tables."""
    migrate_database()

    import migrate

    conn = migrate.connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "goal",
            "exercisetemplateref",
            "workout",
            "workoutplan",
            "usersettings",
            "hevysynctoken",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"
    finally:
        conn.close()


def test_migrate_database_idempotent(temp_db):
    """Test that running migration multiple times produces no errors."""
    migrate_database()

    migrate_database()

    import migrate

    conn = migrate.connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert len(tables) >= 6
    finally:
        conn.close()


def test_generate_create_table_sql():
    """Test SQL generation for individual models."""
    goal_sql = generate_create_table_sql(Goal)
    assert "CREATE TABLE IF NOT EXISTS goal" in goal_sql
    assert "id TEXT PRIMARY KEY" in goal_sql
    assert "name TEXT NOT NULL" in goal_sql
    assert "description TEXT NOT NULL" in goal_sql
    assert "template_id TEXT NOT NULL" in goal_sql

    settings_sql = generate_create_table_sql(UserSettings)
    assert "CREATE TABLE IF NOT EXISTS usersettings" in settings_sql
    assert "user_id TEXT PRIMARY KEY" in settings_sql
    assert "goals TEXT" in settings_sql
    assert "api_keys TEXT" in settings_sql


def test_get_sql_type():
    """Test type mapping from Pydantic to SQL."""
    assert get_sql_type(str) == "TEXT"
    assert get_sql_type(int) == "INTEGER"
    assert get_sql_type(float) == "REAL"
    assert get_sql_type(bool) == "INTEGER"
    from datetime import datetime

    assert get_sql_type(datetime) == "TEXT"
