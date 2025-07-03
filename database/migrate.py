import os
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic_core import PydanticUndefined

backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

from app.models import (  # noqa: E402
    ExerciseTemplateRef,
    Goal,
    HevySyncToken,
    UserSettings,
    Workout,
    WorkoutPlan,
)


def get_sql_type(field_type: Any) -> str:
    """Map Pydantic field types to SQL column types."""
    if field_type is str:
        return "TEXT"
    elif field_type is int:
        return "INTEGER"
    elif field_type is float:
        return "REAL"
    elif field_type is bool:
        return "INTEGER"
    elif field_type is datetime:
        return "TEXT"
    elif get_origin(field_type) is list:
        return "TEXT"
    elif get_origin(field_type) is dict:
        return "TEXT"
    elif get_origin(field_type) is Union:
        args = get_args(field_type)
        non_none_types = [arg for arg in args if arg is not type(None)]
        if len(non_none_types) == 1:
            return get_sql_type(non_none_types[0])

    return "TEXT"


def get_primary_key_field(model_class: type[BaseModel]) -> tuple[str, bool]:
    """Determine the primary key field for a model based on existing patterns.
    Returns (field_name, needs_auto_generation)
    """
    model_name = model_class.__name__.lower()

    if model_name == "usersettings":
        return "user_id", False  # user_id exists in model
    elif model_name == "exercisetemplateref":
        return "template_id", False  # template_id exists in model
    else:
        if "id" in model_class.model_fields:
            return "id", False  # id exists in model (even if optional)
        else:
            return "id", True  # id needs to be auto-generated


def generate_create_table_sql(model_class: type[BaseModel]) -> str:
    """Generate CREATE TABLE IF NOT EXISTS SQL for a Pydantic model."""
    table_name = model_class.__name__.lower()
    primary_key_field, needs_auto_generation = get_primary_key_field(model_class)

    columns = []

    if needs_auto_generation:
        columns.append(f"{primary_key_field} TEXT PRIMARY KEY")

    for field_name, field_info in model_class.model_fields.items():
        field_type = field_info.annotation
        sql_type = get_sql_type(field_type)

        if field_name == primary_key_field and not needs_auto_generation:
            columns.append(f"{field_name} {sql_type} PRIMARY KEY")
        else:
            is_required = (
                field_info.default is PydanticUndefined
                and field_info.default_factory is None
                and not (
                    get_origin(field_type) is Union
                    and type(None) in get_args(field_type)
                )
            )

            if is_required:
                columns.append(f"{field_name} {sql_type} NOT NULL")
            else:
                columns.append(f"{field_name} {sql_type}")

    columns_sql = ",\n            ".join(columns)

    return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        )
    """


def connect_db() -> sqlite3.Connection:
    """Connect to SQLite database and return connection."""
    db_path = Path("/data/database.db")
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        db_path = Path(tempfile.gettempdir()) / "ai_trainer_test.db"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def migrate_database() -> None:
    """Run database migrations by inspecting Pydantic models and creating tables."""
    models = [
        Goal,
        ExerciseTemplateRef,
        Workout,
        WorkoutPlan,
        UserSettings,
        HevySyncToken,
    ]

    conn = connect_db()
    try:
        cursor = conn.cursor()

        for model_class in models:
            sql = generate_create_table_sql(model_class)
            cursor.execute(sql)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
