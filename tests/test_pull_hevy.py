import asyncio
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from pull_hevy import (
    fetch_workouts_last_30_days,
    transform_hevy_workout_to_local,
    upsert_workout,
    main
)
from app.models import Workout
from app.db import create_workout, get_workout


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_dir = tempfile.mkdtemp()

    import app.db as db_module

    original_connect = db_module.connect_db

    db_file_path = Path(temp_dir) / "test_database.db"

    def mock_connect():
        db_file_path.parent.mkdir(parents=True, exist_ok=True)
        import sqlite3

        conn = sqlite3.connect(str(db_file_path))
        conn.row_factory = sqlite3.Row
        return conn

    db_module.connect_db = mock_connect

    db_module.init_db()

    yield temp_dir

    db_module.connect_db = original_connect
    shutil.rmtree(temp_dir)


class TestPullHevy:
    """Test suite for Hevy pull service."""

    def test_transform_hevy_workout_to_local(self):
        """Test transformation of Hevy workout format to local format."""
        hevy_workout = {
            "id": "hevy_workout_123",
            "created_at": "2024-01-15T10:30:00Z",
            "exercises": [
                {
                    "exercise_template": {"name": "Push-ups"},
                    "sets": [{"reps": 15, "weight": 0}],
                    "notes": "Felt good"
                },
                {
                    "exercise_template": {"name": "Squats"},
                    "sets": [{"reps": 20, "weight": 0}],
                    "notes": ""
                }
            ]
        }
        
        local_workout = transform_hevy_workout_to_local(hevy_workout)
        
        assert local_workout.id == "hevy_workout_123"
        assert local_workout.date == datetime(2024, 1, 15, 10, 30, tzinfo=local_workout.date.tzinfo)
        assert len(local_workout.exercises) == 2
        assert local_workout.exercises[0]["name"] == "Push-ups"
        assert local_workout.exercises[0]["notes"] == "Felt good"

    @pytest.mark.asyncio
    async def test_fetch_workouts_last_30_days(self):
        """Test fetching workouts from last 30 days with pagination."""
        mock_client = AsyncMock()
        
        now = datetime.now(timezone.utc)
        recent_workout = {
            "id": "recent_1",
            "created_at": (now - timedelta(days=5)).isoformat().replace("+00:00", "Z"),
            "exercises": []
        }
        old_workout = {
            "id": "old_1", 
            "created_at": (now - timedelta(days=35)).isoformat().replace("+00:00", "Z"),
            "exercises": []
        }
        
        mock_client.get_workouts.side_effect = [
            {"workouts": [recent_workout, old_workout]},
            {"workouts": []}
        ]
        
        workouts = await fetch_workouts_last_30_days(mock_client)
        
        assert len(workouts) == 1
        assert workouts[0]["id"] == "recent_1"
        assert mock_client.get_workouts.call_count >= 1

    def test_upsert_workout_create_new(self, temp_db):
        """Test upserting a new workout."""
        workout = Workout(
            id="new_workout_123",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[{"name": "Push-ups", "sets": 3, "reps": 15}]
        )
        
        is_new, operation = upsert_workout(workout)
        
        assert is_new is True
        assert operation == "created"
        
        retrieved = get_workout("new_workout_123")
        assert retrieved is not None
        assert retrieved.id == "new_workout_123"

    def test_upsert_workout_update_existing(self, temp_db):
        """Test upserting an existing workout."""
        initial_workout = Workout(
            id="existing_workout_123",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[{"name": "Push-ups", "sets": 3, "reps": 15}]
        )
        create_workout(initial_workout)
        
        updated_workout = Workout(
            id="existing_workout_123",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[{"name": "Push-ups", "sets": 4, "reps": 20}]
        )
        
        is_new, operation = upsert_workout(updated_workout)
        
        assert is_new is False
        assert operation == "updated"
        
        retrieved = get_workout("existing_workout_123")
        assert retrieved.exercises[0]["sets"] == 4

    @pytest.mark.asyncio
    @patch('pull_hevy.HevyClient')
    async def test_main_function_success(self, mock_hevy_client_class, temp_db):
        """Test main function with successful sync."""
        mock_client = AsyncMock()
        mock_hevy_client_class.return_value = mock_client
        
        mock_workout = {
            "id": "test_workout_1",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat().replace("+00:00", "Z"),
            "exercises": [
                {
                    "exercise_template": {"name": "Test Exercise"},
                    "sets": [{"reps": 10, "weight": 50}],
                    "notes": "Test notes"
                }
            ]
        }
        
        mock_client.get_workouts.return_value = {"workouts": [mock_workout]}
        
        await main()
        
        retrieved = get_workout("test_workout_1")
        assert retrieved is not None
        assert retrieved.id == "test_workout_1"

    @pytest.mark.asyncio
    @patch('pull_hevy.HevyClient')
    async def test_main_function_hevy_client_error(self, mock_hevy_client_class):
        """Test main function handles HevyClient initialization error."""
        mock_hevy_client_class.side_effect = ValueError("HEVY_TOKEN environment variable is required")
        
        with pytest.raises(SystemExit):
            await main()
