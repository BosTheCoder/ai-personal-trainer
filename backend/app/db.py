import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from .models import (
    ExerciseTemplateRef,
    Goal,
    HevySyncToken,
    UserSettings,
    Workout,
    WorkoutPlan,
)

T = TypeVar("T", bound=BaseModel)


def connect_db() -> sqlite3.Connection:
    """Connect to SQLite database and return connection."""
    db_path = Path("/data/database.db")
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        import tempfile

        db_path = Path(tempfile.gettempdir()) / "ai_trainer_test.db"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create tables for all models if they don't exist."""
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usersettings (
            user_id TEXT PRIMARY KEY,
            goals TEXT NOT NULL,
            api_keys TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goal (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            template_id TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exercisetemplateref (
            template_id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workout (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            exercises TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workoutplan (
            id TEXT PRIMARY KEY,
            start_date TEXT NOT NULL,
            weeks INTEGER NOT NULL,
            workouts TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hevysynctoken (
            id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """
    )

    conn.commit()


def init_db() -> None:
    """Initialize database with all required tables."""
    conn = connect_db()
    try:
        _create_tables(conn)
    finally:
        conn.close()


def _get_table_name(model_class: Type[BaseModel]) -> str:
    """Get table name from model class."""
    return model_class.__name__.lower()


def _serialize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert complex types to JSON strings for database storage."""
    serialized = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            serialized[key] = json.dumps(value)
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


def _deserialize_data(data: Dict[str, Any], model_class: Type[T]) -> Dict[str, Any]:
    """Convert JSON strings back to complex types for model validation."""
    deserialized = dict(data)

    for field_name, field_info in model_class.model_fields.items():
        if field_name in deserialized and deserialized[field_name] is not None:
            field_type = field_info.annotation

            if hasattr(field_type, "__origin__") and field_type.__origin__ in (
                list,
                List,
            ):
                if isinstance(deserialized[field_name], str):
                    deserialized[field_name] = json.loads(deserialized[field_name])
            elif field_type is dict or (
                hasattr(field_type, "__origin__") and field_type.__origin__ is dict
            ):
                if isinstance(deserialized[field_name], str):
                    deserialized[field_name] = json.loads(deserialized[field_name])
            elif field_type is datetime:
                if isinstance(deserialized[field_name], str):
                    deserialized[field_name] = datetime.fromisoformat(
                        deserialized[field_name]
                    )

    return deserialized


def create_user_settings(data: UserSettings) -> str:
    """Create a new UserSettings record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO usersettings (user_id, goals, api_keys) VALUES (?, ?, ?)",
            (
                serialized_data["user_id"],
                serialized_data["goals"],
                serialized_data["api_keys"],
            ),
        )
        conn.commit()
        return data.user_id
    finally:
        conn.close()


def get_user_settings(user_id: str) -> Optional[UserSettings]:
    """Get UserSettings by user_id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM usersettings WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), UserSettings)
            return UserSettings.model_validate(data)
        return None
    finally:
        conn.close()


def update_user_settings(user_id: str, data: UserSettings) -> bool:
    """Update UserSettings record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE usersettings SET goals = ?, api_keys = ? WHERE user_id = ?",
            (serialized_data["goals"], serialized_data["api_keys"], user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_user_settings(user_id: str) -> bool:
    """Delete UserSettings record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("DELETE FROM usersettings WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_goal(data: Goal) -> str:
    """Create a new Goal record."""
    init_db()
    conn = connect_db()
    try:
        goal_id = str(uuid.uuid4())
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO goal (id, name, description, template_id) VALUES (?, ?, ?, ?)",
            (
                goal_id,
                serialized_data["name"],
                serialized_data["description"],
                serialized_data["template_id"],
            ),
        )
        conn.commit()
        return goal_id
    finally:
        conn.close()


def get_goal(goal_id: str) -> Optional[Goal]:
    """Get Goal by id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("SELECT * FROM goal WHERE id = ?", (goal_id,))
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), Goal)
            return Goal.model_validate(data)
        return None
    finally:
        conn.close()


def update_goal(goal_id: str, data: Goal) -> bool:
    """Update Goal record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE goal SET name = ?, description = ?, template_id = ? WHERE id = ?",
            (
                serialized_data["name"],
                serialized_data["description"],
                serialized_data["template_id"],
                goal_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_goal(goal_id: str) -> bool:
    """Delete Goal record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("DELETE FROM goal WHERE id = ?", (goal_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_exercise_template_ref(data: ExerciseTemplateRef) -> str:
    """Create a new ExerciseTemplateRef record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO exercisetemplateref (template_id, name) VALUES (?, ?)",
            (serialized_data["template_id"], serialized_data["name"]),
        )
        conn.commit()
        return data.template_id
    finally:
        conn.close()


def get_exercise_template_ref(template_id: str) -> Optional[ExerciseTemplateRef]:
    """Get ExerciseTemplateRef by template_id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM exercisetemplateref WHERE template_id = ?", (template_id,)
        )
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), ExerciseTemplateRef)
            return ExerciseTemplateRef.model_validate(data)
        return None
    finally:
        conn.close()


def update_exercise_template_ref(template_id: str, data: ExerciseTemplateRef) -> bool:
    """Update ExerciseTemplateRef record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE exercisetemplateref SET name = ? WHERE template_id = ?",
            (serialized_data["name"], template_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_exercise_template_ref(template_id: str) -> bool:
    """Delete ExerciseTemplateRef record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute(
            "DELETE FROM exercisetemplateref WHERE template_id = ?", (template_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_workout(data: Workout) -> str:
    """Create a new Workout record."""
    init_db()
    conn = connect_db()
    try:
        workout_id = data.id or str(uuid.uuid4())
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO workout (id, date, exercises) VALUES (?, ?, ?)",
            (workout_id, serialized_data["date"], serialized_data["exercises"]),
        )
        conn.commit()
        return workout_id
    finally:
        conn.close()


def get_workout(workout_id: str) -> Optional[Workout]:
    """Get Workout by id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,))
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), Workout)
            return Workout.model_validate(data)
        return None
    finally:
        conn.close()


def update_workout(workout_id: str, data: Workout) -> bool:
    """Update Workout record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE workout SET date = ?, exercises = ? WHERE id = ?",
            (serialized_data["date"], serialized_data["exercises"], workout_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_workout(workout_id: str) -> bool:
    """Delete Workout record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("DELETE FROM workout WHERE id = ?", (workout_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_workout_plan(data: WorkoutPlan) -> str:
    """Create a new WorkoutPlan record."""
    init_db()
    conn = connect_db()
    try:
        plan_id = data.id or str(uuid.uuid4())
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO workoutplan (id, start_date, weeks, workouts) VALUES (?, ?, ?, ?)",
            (
                plan_id,
                serialized_data["start_date"],
                serialized_data["weeks"],
                serialized_data["workouts"],
            ),
        )
        conn.commit()
        return plan_id
    finally:
        conn.close()


def get_workout_plan(plan_id: str) -> Optional[WorkoutPlan]:
    """Get WorkoutPlan by id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("SELECT * FROM workoutplan WHERE id = ?", (plan_id,))
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), WorkoutPlan)
            return WorkoutPlan.model_validate(data)
        return None
    finally:
        conn.close()


def update_workout_plan(plan_id: str, data: WorkoutPlan) -> bool:
    """Update WorkoutPlan record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE workoutplan SET start_date = ?, weeks = ?, workouts = ? WHERE id = ?",
            (
                serialized_data["start_date"],
                serialized_data["weeks"],
                serialized_data["workouts"],
                plan_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_workout_plan(plan_id: str) -> bool:
    """Delete WorkoutPlan record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("DELETE FROM workoutplan WHERE id = ?", (plan_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def create_hevy_sync_token(data: HevySyncToken) -> str:
    """Create a new HevySyncToken record."""
    init_db()
    conn = connect_db()
    try:
        token_id = str(uuid.uuid4())
        serialized_data = _serialize_data(data.model_dump())

        conn.execute(
            "INSERT INTO hevysynctoken (id, access_token, expires_at) VALUES (?, ?, ?)",
            (token_id, serialized_data["access_token"], serialized_data["expires_at"]),
        )
        conn.commit()
        return token_id
    finally:
        conn.close()


def get_hevy_sync_token(token_id: str) -> Optional[HevySyncToken]:
    """Get HevySyncToken by id."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("SELECT * FROM hevysynctoken WHERE id = ?", (token_id,))
        row = cursor.fetchone()
        if row:
            data = _deserialize_data(dict(row), HevySyncToken)
            return HevySyncToken.model_validate(data)
        return None
    finally:
        conn.close()


def update_hevy_sync_token(token_id: str, data: HevySyncToken) -> bool:
    """Update HevySyncToken record."""
    init_db()
    conn = connect_db()
    try:
        serialized_data = _serialize_data(data.model_dump())

        cursor = conn.execute(
            "UPDATE hevysynctoken SET access_token = ?, expires_at = ? WHERE id = ?",
            (serialized_data["access_token"], serialized_data["expires_at"], token_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_hevy_sync_token(token_id: str) -> bool:
    """Delete HevySyncToken record."""
    init_db()
    conn = connect_db()
    try:
        cursor = conn.execute("DELETE FROM hevysynctoken WHERE id = ?", (token_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
