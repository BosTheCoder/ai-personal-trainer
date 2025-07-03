import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from backend.app.db import (
    create_exercise_template_ref,
    create_goal,
    create_hevy_sync_token,
    create_user_settings,
    create_workout,
    create_workout_plan,
    delete_exercise_template_ref,
    delete_goal,
    delete_hevy_sync_token,
    delete_user_settings,
    delete_workout,
    delete_workout_plan,
    get_exercise_template_ref,
    get_goal,
    get_hevy_sync_token,
    get_user_settings,
    get_workout,
    get_workout_plan,
    update_exercise_template_ref,
    update_goal,
    update_hevy_sync_token,
    update_user_settings,
    update_workout,
    update_workout_plan,
)
from backend.app.models import (
    ExerciseTemplateRef,
    Goal,
    HevySyncToken,
    UserSettings,
    Workout,
    WorkoutPlan,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    temp_dir = tempfile.mkdtemp()

    import backend.app.db as db_module

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


def test_user_settings_crud(temp_db):
    """Test UserSettings CRUD operations."""
    user_settings = UserSettings(
        user_id="test_user_123",
        goals=["lose_weight", "build_muscle"],
        api_keys={"openrouter": "test_key", "hevy": "hevy_key"},
    )

    created_id = create_user_settings(user_settings)
    assert created_id == "test_user_123"

    retrieved = get_user_settings("test_user_123")
    assert retrieved is not None
    assert retrieved.user_id == "test_user_123"
    assert retrieved.goals == ["lose_weight", "build_muscle"]
    assert retrieved.api_keys == {"openrouter": "test_key", "hevy": "hevy_key"}

    updated_settings = UserSettings(
        user_id="test_user_123",
        goals=["maintain_fitness"],
        api_keys={"openrouter": "updated_key"},
    )

    update_result = update_user_settings("test_user_123", updated_settings)
    assert update_result is True

    updated_retrieved = get_user_settings("test_user_123")
    assert updated_retrieved.goals == ["maintain_fitness"]
    assert updated_retrieved.api_keys == {"openrouter": "updated_key"}

    delete_result = delete_user_settings("test_user_123")
    assert delete_result is True

    deleted_retrieved = get_user_settings("test_user_123")
    assert deleted_retrieved is None


def test_goal_crud(temp_db):
    """Test Goal CRUD operations."""
    goal = Goal(
        name="Weight Loss",
        description="Lose 10 pounds in 3 months",
        template_id="weight_loss_template_1",
    )

    created_id = create_goal(goal)
    assert created_id is not None
    assert len(created_id) > 0

    retrieved = get_goal(created_id)
    assert retrieved is not None
    assert retrieved.name == "Weight Loss"
    assert retrieved.description == "Lose 10 pounds in 3 months"
    assert retrieved.template_id == "weight_loss_template_1"

    updated_goal = Goal(
        name="Muscle Building",
        description="Build lean muscle mass",
        template_id="muscle_building_template_1",
    )

    update_result = update_goal(created_id, updated_goal)
    assert update_result is True

    updated_retrieved = get_goal(created_id)
    assert updated_retrieved.name == "Muscle Building"
    assert updated_retrieved.description == "Build lean muscle mass"

    delete_result = delete_goal(created_id)
    assert delete_result is True

    deleted_retrieved = get_goal(created_id)
    assert deleted_retrieved is None


def test_exercise_template_ref_crud(temp_db):
    """Test ExerciseTemplateRef CRUD operations."""
    exercise_ref = ExerciseTemplateRef(template_id="push_up_template", name="Push-ups")

    created_id = create_exercise_template_ref(exercise_ref)
    assert created_id == "push_up_template"

    retrieved = get_exercise_template_ref("push_up_template")
    assert retrieved is not None
    assert retrieved.template_id == "push_up_template"
    assert retrieved.name == "Push-ups"

    updated_ref = ExerciseTemplateRef(
        template_id="push_up_template", name="Modified Push-ups"
    )

    update_result = update_exercise_template_ref("push_up_template", updated_ref)
    assert update_result is True

    updated_retrieved = get_exercise_template_ref("push_up_template")
    assert updated_retrieved.name == "Modified Push-ups"

    delete_result = delete_exercise_template_ref("push_up_template")
    assert delete_result is True

    deleted_retrieved = get_exercise_template_ref("push_up_template")
    assert deleted_retrieved is None


def test_workout_crud(temp_db):
    """Test Workout CRUD operations."""
    workout_date = datetime(2024, 1, 15, 10, 30)
    workout = Workout(
        date=workout_date,
        exercises=[
            {"name": "Push-ups", "sets": 3, "reps": 15},
            {"name": "Squats", "sets": 3, "reps": 20},
        ],
    )

    created_id = create_workout(workout)
    assert created_id is not None
    assert len(created_id) > 0

    retrieved = get_workout(created_id)
    assert retrieved is not None
    assert retrieved.date == workout_date
    assert len(retrieved.exercises) == 2
    assert retrieved.exercises[0]["name"] == "Push-ups"

    updated_workout = Workout(
        id=created_id,
        date=workout_date,
        exercises=[
            {"name": "Pull-ups", "sets": 3, "reps": 10},
            {"name": "Lunges", "sets": 3, "reps": 12},
        ],
    )

    update_result = update_workout(created_id, updated_workout)
    assert update_result is True

    updated_retrieved = get_workout(created_id)
    assert updated_retrieved.exercises[0]["name"] == "Pull-ups"

    delete_result = delete_workout(created_id)
    assert delete_result is True

    deleted_retrieved = get_workout(created_id)
    assert deleted_retrieved is None


def test_workout_plan_crud(temp_db):
    """Test WorkoutPlan CRUD operations."""
    start_date = datetime(2024, 1, 1)
    workout_plan = WorkoutPlan(
        start_date=start_date,
        weeks=12,
        workouts=[
            {"day": "Monday", "type": "Upper Body"},
            {"day": "Wednesday", "type": "Lower Body"},
            {"day": "Friday", "type": "Full Body"},
        ],
    )

    created_id = create_workout_plan(workout_plan)
    assert created_id is not None
    assert len(created_id) > 0

    retrieved = get_workout_plan(created_id)
    assert retrieved is not None
    assert retrieved.start_date == start_date
    assert retrieved.weeks == 12
    assert len(retrieved.workouts) == 3

    updated_plan = WorkoutPlan(
        id=created_id,
        start_date=start_date,
        weeks=16,
        workouts=[
            {"day": "Monday", "type": "Push"},
            {"day": "Tuesday", "type": "Pull"},
            {"day": "Thursday", "type": "Legs"},
        ],
    )

    update_result = update_workout_plan(created_id, updated_plan)
    assert update_result is True

    updated_retrieved = get_workout_plan(created_id)
    assert updated_retrieved.weeks == 16
    assert len(updated_retrieved.workouts) == 3

    delete_result = delete_workout_plan(created_id)
    assert delete_result is True

    deleted_retrieved = get_workout_plan(created_id)
    assert deleted_retrieved is None


def test_hevy_sync_token_crud(temp_db):
    """Test HevySyncToken CRUD operations."""
    expires_at = datetime(2024, 12, 31, 23, 59, 59)
    sync_token = HevySyncToken(
        access_token="hevy_access_token_123", expires_at=expires_at
    )

    created_id = create_hevy_sync_token(sync_token)
    assert created_id is not None
    assert len(created_id) > 0

    retrieved = get_hevy_sync_token(created_id)
    assert retrieved is not None
    assert retrieved.access_token == "hevy_access_token_123"
    assert retrieved.expires_at == expires_at

    updated_token = HevySyncToken(
        access_token="hevy_updated_token_456",
        expires_at=datetime(2025, 6, 30, 12, 0, 0),
    )

    update_result = update_hevy_sync_token(created_id, updated_token)
    assert update_result is True

    updated_retrieved = get_hevy_sync_token(created_id)
    assert updated_retrieved.access_token == "hevy_updated_token_456"

    delete_result = delete_hevy_sync_token(created_id)
    assert delete_result is True

    deleted_retrieved = get_hevy_sync_token(created_id)
    assert deleted_retrieved is None


def test_database_initialization(temp_db):
    """Test that database tables are created properly."""
    import backend.app.db as db_module

    conn = db_module.connect_db()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "usersettings",
            "goal",
            "exercisetemplateref",
            "workout",
            "workoutplan",
            "hevysynctoken",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} was not created"
    finally:
        conn.close()


def test_nonexistent_records(temp_db):
    """Test behavior when trying to access nonexistent records."""
    assert get_user_settings("nonexistent_user") is None
    assert get_goal("nonexistent_goal") is None
    assert get_exercise_template_ref("nonexistent_template") is None
    assert get_workout("nonexistent_workout") is None
    assert get_workout_plan("nonexistent_plan") is None
    assert get_hevy_sync_token("nonexistent_token") is None

    assert (
        update_user_settings(
            "nonexistent_user", UserSettings(user_id="test", goals=[], api_keys={})
        )
        is False
    )
    assert (
        update_goal(
            "nonexistent_goal",
            Goal(name="test", description="test", template_id="test"),
        )
        is False
    )
    assert delete_user_settings("nonexistent_user") is False
    assert delete_goal("nonexistent_goal") is False


def test_json_serialization_deserialization(temp_db):
    """Test that complex data types are properly serialized and deserialized."""
    complex_user_settings = UserSettings(
        user_id="complex_user",
        goals=["goal1", "goal2", "goal3"],
        api_keys={
            "service1": "key1",
            "service2": "key2",
            "nested": {"inner_key": "inner_value"},
        },
    )

    created_id = create_user_settings(complex_user_settings)
    retrieved = get_user_settings(created_id)

    assert retrieved is not None
    assert retrieved.goals == ["goal1", "goal2", "goal3"]
    assert retrieved.api_keys["service1"] == "key1"
    assert retrieved.api_keys["nested"]["inner_key"] == "inner_value"

    complex_workout = Workout(
        date=datetime(2024, 1, 1, 12, 0),
        exercises=[
            {
                "name": "Bench Press",
                "sets": [
                    {"weight": 135, "reps": 10},
                    {"weight": 155, "reps": 8},
                    {"weight": 175, "reps": 6},
                ],
                "notes": "Felt strong today",
            }
        ],
    )

    workout_id = create_workout(complex_workout)
    retrieved_workout = get_workout(workout_id)

    assert retrieved_workout is not None
    assert len(retrieved_workout.exercises) == 1
    assert retrieved_workout.exercises[0]["name"] == "Bench Press"
    assert len(retrieved_workout.exercises[0]["sets"]) == 3
    assert retrieved_workout.exercises[0]["sets"][0]["weight"] == 135
    assert retrieved_workout.exercises[0]["notes"] == "Felt strong today"
