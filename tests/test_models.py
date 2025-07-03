import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402

from app.models import (  # noqa: E402
    ExerciseTemplateRef,
    Goal,
    HevySyncToken,
    UserSettings,
    Workout,
    WorkoutPlan,
)


class TestGoal:
    """Test cases for Goal model"""

    def test_goal_creation_valid(self):
        """Test creating a valid Goal instance"""
        goal = Goal(
            name="Weight Loss",
            description="Lose 10 pounds in 3 months",
            template_id="template_123",
        )
        assert goal.name == "Weight Loss"
        assert goal.description == "Lose 10 pounds in 3 months"
        assert goal.template_id == "template_123"

    def test_goal_json_serialization(self):
        """Test Goal JSON serialization"""
        goal = Goal(
            name="Muscle Gain",
            description="Build muscle mass",
            template_id="template_456",
        )
        goal_dict = goal.model_dump()
        expected = {
            "name": "Muscle Gain",
            "description": "Build muscle mass",
            "template_id": "template_456",
        }
        assert goal_dict == expected

    def test_goal_json_deserialization(self):
        """Test Goal JSON deserialization"""
        data = {
            "name": "Endurance",
            "description": "Improve cardiovascular endurance",
            "template_id": "template_789",
        }
        goal = Goal.model_validate(data)
        assert goal.name == "Endurance"
        assert goal.description == "Improve cardiovascular endurance"
        assert goal.template_id == "template_789"

    def test_goal_missing_required_fields(self):
        """Test Goal validation with missing required fields"""
        with pytest.raises(ValueError):
            Goal(name="Test Goal")

    def test_goal_invalid_types(self):
        """Test Goal validation with invalid types"""
        with pytest.raises(ValueError):
            Goal(name=123, description="Test", template_id="test")


class TestExerciseTemplateRef:
    """Test cases for ExerciseTemplateRef model"""

    def test_exercise_template_ref_creation_valid(self):
        """Test creating a valid ExerciseTemplateRef instance"""
        exercise = ExerciseTemplateRef(template_id="ex_123", name="Push-ups")
        assert exercise.template_id == "ex_123"
        assert exercise.name == "Push-ups"

    def test_exercise_template_ref_json_serialization(self):
        """Test ExerciseTemplateRef JSON serialization"""
        exercise = ExerciseTemplateRef(template_id="ex_456", name="Squats")
        exercise_dict = exercise.model_dump()
        expected = {"template_id": "ex_456", "name": "Squats"}
        assert exercise_dict == expected

    def test_exercise_template_ref_json_deserialization(self):
        """Test ExerciseTemplateRef JSON deserialization"""
        data = {"template_id": "ex_789", "name": "Deadlifts"}
        exercise = ExerciseTemplateRef.model_validate(data)
        assert exercise.template_id == "ex_789"
        assert exercise.name == "Deadlifts"


class TestWorkout:
    """Test cases for Workout model"""

    def test_workout_creation_valid(self):
        """Test creating a valid Workout instance"""
        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        exercises = [
            ExerciseTemplateRef(template_id="ex_1", name="Push-ups"),
            ExerciseTemplateRef(template_id="ex_2", name="Squats"),
        ]
        workout = Workout(id="workout_123", date=workout_date, exercises=exercises)
        assert workout.id == "workout_123"
        assert workout.date == workout_date
        assert len(workout.exercises) == 2

    def test_workout_json_serialization(self):
        """Test Workout JSON serialization"""
        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        exercises = [ExerciseTemplateRef(template_id="ex_1", name="Push-ups")]
        workout = Workout(id="workout_456", date=workout_date, exercises=exercises)
        workout_dict = workout.model_dump()
        assert workout_dict["id"] == "workout_456"
        assert workout_dict["date"] == workout_date
        assert len(workout_dict["exercises"]) == 1

    def test_workout_json_deserialization(self):
        """Test Workout JSON deserialization"""
        data = {
            "id": "workout_789",
            "date": "2024-01-15T10:00:00Z",
            "exercises": [{"template_id": "ex_1", "name": "Push-ups"}],
        }
        workout = Workout.model_validate(data)
        assert workout.id == "workout_789"
        assert len(workout.exercises) == 1

    def test_workout_empty_exercises(self):
        """Test Workout with empty exercises list"""
        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        workout = Workout(id="workout_empty", date=workout_date)
        assert len(workout.exercises) == 0


class TestWorkoutPlan:
    """Test cases for WorkoutPlan model"""

    def test_workout_plan_creation_valid(self):
        """Test creating a valid WorkoutPlan instance"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        workouts = [
            Workout(
                id="workout_1",
                date=workout_date,
                exercises=[ExerciseTemplateRef(template_id="ex_1", name="Push-ups")],
            )
        ]
        plan = WorkoutPlan(
            id="plan_123", start_date=start_date, weeks=12, workouts=workouts
        )
        assert plan.id == "plan_123"
        assert plan.start_date == start_date
        assert plan.weeks == 12
        assert len(plan.workouts) == 1

    def test_workout_plan_json_serialization(self):
        """Test WorkoutPlan JSON serialization"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        plan = WorkoutPlan(id="plan_456", start_date=start_date, weeks=8, workouts=[])
        plan_dict = plan.model_dump()
        assert plan_dict["id"] == "plan_456"
        assert plan_dict["weeks"] == 8
        assert len(plan_dict["workouts"]) == 0

    def test_workout_plan_json_deserialization(self):
        """Test WorkoutPlan JSON deserialization"""
        data = {
            "id": "plan_789",
            "start_date": "2024-01-01T00:00:00Z",
            "weeks": 16,
            "workouts": [],
        }
        plan = WorkoutPlan.model_validate(data)
        assert plan.id == "plan_789"
        assert plan.weeks == 16

    def test_workout_plan_weeks_validation(self):
        """Test WorkoutPlan weeks field validation"""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        with pytest.raises(ValueError):
            WorkoutPlan(id="plan_invalid", start_date=start_date, weeks=0)


class TestUserSettings:
    """Test cases for UserSettings model"""

    def test_user_settings_creation_valid(self):
        """Test creating a valid UserSettings instance"""
        goals = [Goal(name="Weight Loss", description="Lose weight", template_id="t1")]
        api_keys = {"hevy": "secret_key_123"}
        settings = UserSettings(user_id="user_123", goals=goals, api_keys=api_keys)
        assert settings.user_id == "user_123"
        assert len(settings.goals) == 1
        assert settings.api_keys["hevy"] == "secret_key_123"

    def test_user_settings_json_serialization(self):
        """Test UserSettings JSON serialization"""
        goals = [Goal(name="Muscle Gain", description="Build muscle", template_id="t2")]
        settings = UserSettings(
            user_id="user_456", goals=goals, api_keys={"api1": "key1"}
        )
        settings_dict = settings.model_dump()
        assert settings_dict["user_id"] == "user_456"
        assert len(settings_dict["goals"]) == 1
        assert settings_dict["api_keys"]["api1"] == "key1"

    def test_user_settings_json_deserialization(self):
        """Test UserSettings JSON deserialization"""
        data = {
            "user_id": "user_789",
            "goals": [
                {
                    "name": "Endurance",
                    "description": "Build endurance",
                    "template_id": "t3",
                }
            ],
            "api_keys": {"service": "token"},
        }
        settings = UserSettings.model_validate(data)
        assert settings.user_id == "user_789"
        assert len(settings.goals) == 1
        assert settings.goals[0].name == "Endurance"

    def test_user_settings_empty_defaults(self):
        """Test UserSettings with empty defaults"""
        settings = UserSettings(user_id="user_empty")
        assert len(settings.goals) == 0
        assert len(settings.api_keys) == 0


class TestHevySyncToken:
    """Test cases for HevySyncToken model"""

    def test_hevy_sync_token_creation_valid(self):
        """Test creating a valid HevySyncToken instance"""
        expires_at = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        token = HevySyncToken(access_token="hevy_token_123", expires_at=expires_at)
        assert token.access_token == "hevy_token_123"
        assert token.expires_at == expires_at

    def test_hevy_sync_token_json_serialization(self):
        """Test HevySyncToken JSON serialization"""
        expires_at = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        token = HevySyncToken(access_token="hevy_token_456", expires_at=expires_at)
        token_dict = token.model_dump()
        assert token_dict["access_token"] == "hevy_token_456"
        assert token_dict["expires_at"] == expires_at

    def test_hevy_sync_token_json_deserialization(self):
        """Test HevySyncToken JSON deserialization"""
        data = {"access_token": "hevy_token_789", "expires_at": "2024-03-15T18:30:00Z"}
        token = HevySyncToken.model_validate(data)
        assert token.access_token == "hevy_token_789"
        assert isinstance(token.expires_at, datetime)


class TestModelIntegration:
    """Integration tests for model relationships"""

    def test_complete_user_settings_with_nested_models(self):
        """Test UserSettings with complete nested model structure"""
        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)

        exercises = [
            ExerciseTemplateRef(template_id="ex_1", name="Push-ups"),
            ExerciseTemplateRef(template_id="ex_2", name="Squats"),
        ]

        workout = Workout(id="workout_1", date=workout_date, exercises=exercises)

        WorkoutPlan(id="plan_1", start_date=start_date, weeks=12, workouts=[workout])

        goals = [
            Goal(name="Weight Loss", description="Lose 10 pounds", template_id="t1"),
            Goal(name="Strength", description="Build strength", template_id="t2"),
        ]

        settings = UserSettings(
            user_id="user_complete",
            goals=goals,
            api_keys={"hevy": "token123", "myfitnesspal": "token456"},
        )

        settings_dict = settings.model_dump()
        settings_restored = UserSettings.model_validate(settings_dict)

        assert settings_restored.user_id == "user_complete"
        assert len(settings_restored.goals) == 2
        assert settings_restored.goals[0].name == "Weight Loss"
        assert len(settings_restored.api_keys) == 2

    def test_json_round_trip_all_models(self):
        """Test JSON serialization/deserialization round-trip for all models"""
        goal = Goal(name="Test", description="Test goal", template_id="t1")
        goal_restored = Goal.model_validate(goal.model_dump())
        assert goal.name == goal_restored.name

        exercise = ExerciseTemplateRef(template_id="ex1", name="Test Exercise")
        exercise_restored = ExerciseTemplateRef.model_validate(exercise.model_dump())
        assert exercise.name == exercise_restored.name

        workout_date = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        workout = Workout(id="w1", date=workout_date, exercises=[exercise])
        workout_restored = Workout.model_validate(workout.model_dump())
        assert workout.id == workout_restored.id
        assert len(workout_restored.exercises) == 1

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        plan = WorkoutPlan(id="p1", start_date=start_date, weeks=8, workouts=[workout])
        plan_restored = WorkoutPlan.model_validate(plan.model_dump())
        assert plan.weeks == plan_restored.weeks

        settings = UserSettings(user_id="u1", goals=[goal], api_keys={"key": "value"})
        settings_restored = UserSettings.model_validate(settings.model_dump())
        assert settings.user_id == settings_restored.user_id

        expires_at = datetime(2024, 12, 31, tzinfo=timezone.utc)
        token = HevySyncToken(access_token="token", expires_at=expires_at)
        token_restored = HevySyncToken.model_validate(token.model_dump())
        assert token.access_token == token_restored.access_token
