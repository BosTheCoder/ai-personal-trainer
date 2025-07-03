import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # noqa: E402

from app.api.generate import (  # noqa: E402
    GenerateWorkoutRequest,
    WorkoutConstraints,
    WorkoutOverrides,
    _apply_weight_suggestions,
    _build_workout_prompt,
    _parse_ai_workout_response,
    _suggest_weight_for_exercise,
    generate_workout,
)


class TestGenerateWorkout:
    """Test suite for workout generation functionality."""

    @pytest.fixture
    def sample_constraints(self):
        """Sample workout constraints for testing."""
        return WorkoutConstraints(
            goals=["muscle building", "strength"],
            equipment=["barbell", "dumbbells"],
            duration=45,
            fitness_level="intermediate",
        )

    @pytest.fixture
    def sample_overrides(self):
        """Sample workout overrides for testing."""
        return WorkoutOverrides(
            specific_exercises=["squat", "bench press"],
            avoid_exercises=["deadlift"],
            focus_areas=["chest", "legs"],
        )

    @pytest.fixture
    def sample_ai_response(self):
        """Sample AI response for testing."""
        return """
        1. Squat
        3 sets of 8-12 reps
        Rest 90 seconds between sets

        2. Bench Press
        3 sets of 8-10 reps
        Rest 2 minutes between sets

        3. Push-ups
        2 sets of 15 reps
        Bodyweight exercise
        """

    def test_workout_constraints_validation(self):
        """Test WorkoutConstraints model validation."""
        constraints = WorkoutConstraints(
            goals=["strength"],
            equipment=["barbell"],
            duration=30,
            fitness_level="beginner",
        )

        assert constraints.goals == ["strength"]
        assert constraints.equipment == ["barbell"]
        assert constraints.duration == 30
        assert constraints.fitness_level == "beginner"

    def test_workout_constraints_defaults(self):
        """Test WorkoutConstraints default values."""
        constraints = WorkoutConstraints()

        assert constraints.goals == []
        assert constraints.equipment == []
        assert constraints.duration == 30
        assert constraints.fitness_level == "beginner"

    def test_workout_overrides_optional(self):
        """Test WorkoutOverrides optional fields."""
        overrides = WorkoutOverrides()

        assert overrides.specific_exercises is None
        assert overrides.avoid_exercises is None
        assert overrides.focus_areas is None

    def test_generate_workout_request_validation(self):
        """Test GenerateWorkoutRequest model validation."""
        constraints = WorkoutConstraints(goals=["strength"])
        request = GenerateWorkoutRequest(
            constraints=constraints, user_id="test_user_123"
        )

        assert request.constraints.goals == ["strength"]
        assert request.user_id == "test_user_123"
        assert request.overrides is None

    def test_suggest_weight_for_exercise_beginner(self):
        """Test weight suggestion for beginner level."""
        weight = _suggest_weight_for_exercise("squat", "beginner")

        assert weight is not None
        assert weight["weight"] == 20
        assert weight["unit"] == "kg"

    def test_suggest_weight_for_exercise_intermediate(self):
        """Test weight suggestion for intermediate level."""
        weight = _suggest_weight_for_exercise("bench press", "intermediate")

        assert weight is not None
        assert weight["weight"] == 40
        assert weight["unit"] == "kg"

    def test_suggest_weight_for_exercise_advanced(self):
        """Test weight suggestion for advanced level."""
        weight = _suggest_weight_for_exercise("deadlift", "advanced")

        assert weight is not None
        assert weight["weight"] == 120
        assert weight["unit"] == "kg"

    def test_suggest_weight_for_unknown_exercise(self):
        """Test weight suggestion for unknown exercise."""
        weight = _suggest_weight_for_exercise("jumping jacks", "beginner")

        assert weight is None

    def test_parse_ai_workout_response(self, sample_ai_response):
        """Test parsing AI workout response."""
        exercises = _parse_ai_workout_response(sample_ai_response)

        assert len(exercises) == 3

        assert exercises[0]["name"] == "Squat"
        assert exercises[0]["sets"] == 3
        assert exercises[0]["reps"] == "8-12"

        assert exercises[1]["name"] == "Bench Press"
        assert exercises[1]["sets"] == 3
        assert exercises[1]["reps"] == "8-10"

        assert exercises[2]["name"] == "Push-ups"
        assert exercises[2]["sets"] == 2
        assert exercises[2]["reps"] == "15"

    def test_parse_ai_workout_response_empty(self):
        """Test parsing empty AI response."""
        exercises = _parse_ai_workout_response("")

        assert len(exercises) == 1
        assert exercises[0]["name"] == "Push-ups"

    def test_build_workout_prompt_basic(self, sample_constraints):
        """Test building workout prompt with basic constraints."""
        template = (
            "Goals: {goals}, Equipment: {equipment}, "
            "Duration: {duration}, Level: {fitness_level}"
        )

        prompt = _build_workout_prompt(sample_constraints, None, template)

        assert "muscle building, strength" in prompt
        assert "barbell, dumbbells" in prompt
        assert "45" in prompt
        assert "intermediate" in prompt

    def test_build_workout_prompt_with_overrides(
        self, sample_constraints, sample_overrides
    ):
        """Test building workout prompt with overrides."""
        template = "Goals: {goals}"

        prompt = _build_workout_prompt(sample_constraints, sample_overrides, template)

        assert "squat, bench press" in prompt
        assert "deadlift" in prompt
        assert "chest, legs" in prompt

    @pytest.mark.asyncio
    async def test_apply_weight_suggestions(self):
        """Test applying weight suggestions to exercises."""
        exercises = [
            {"name": "Squat", "sets": 3, "reps": "8-12"},
            {"name": "Push-ups", "sets": 2, "reps": "15"},
        ]

        with patch("app.api.generate.match_exercise_template") as mock_match:
            mock_match.side_effect = [
                {"template_id": "hevy_squat_001", "name": "Squat"},
                {"template_id": "other_notes", "name": "Other – Notes - Push-ups"},
            ]

            enhanced = await _apply_weight_suggestions(exercises, "beginner")

            assert len(enhanced) == 2

            assert enhanced[0]["template_id"] == "hevy_squat_001"
            assert enhanced[0]["suggested_weight"]["weight"] == 20

            assert enhanced[1]["template_id"] == "other_notes"
            assert "suggested_weight" not in enhanced[1]

    @pytest.mark.asyncio
    async def test_generate_workout_success(self, sample_constraints):
        """Test successful workout generation."""
        request = GenerateWorkoutRequest(
            constraints=sample_constraints, user_id="test_user"
        )

        mock_ai_response = (
            "1. Squat\n3 sets of 8 reps\n\n2. Bench Press\n3 sets of 10 reps"
        )

        with patch("app.api.generate.send_prompt", new_callable=AsyncMock) as mock_send:
            with patch(
                "app.api.generate.match_exercise_template", new_callable=AsyncMock
            ) as mock_match:
                with patch("main.prompts", {"single_workout": "Template: {goals}"}):
                    mock_send.return_value = mock_ai_response
                    mock_match.return_value = {
                        "template_id": "test_id",
                        "name": "Test Exercise",
                    }

                    result = await generate_workout(request)

                    assert "date" in result
                    assert "exercises" in result
                    assert len(result["exercises"]) == 2
                    assert result["exercises"][0]["name"] == "Squat"
                    assert result["exercises"][1]["name"] == "Bench Press"

    @pytest.mark.asyncio
    async def test_generate_workout_missing_prompt_template(self, sample_constraints):
        """Test workout generation with missing prompt template."""
        request = GenerateWorkoutRequest(
            constraints=sample_constraints, user_id="test_user"
        )

        with patch("main.prompts", {}):
            with pytest.raises(Exception) as exc_info:
                await generate_workout(request)

            assert "Failed to generate workout" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_generate_workout_api_key_error(self, sample_constraints):
        """Test workout generation with missing API key."""
        request = GenerateWorkoutRequest(
            constraints=sample_constraints, user_id="test_user"
        )

        with patch("app.api.generate.send_prompt", new_callable=AsyncMock) as mock_send:
            with patch("main.prompts", {"single_workout": "Template"}):
                mock_send.side_effect = ValueError(
                    "OpenRouter API key not found in user settings"
                )

                with pytest.raises(Exception) as exc_info:
                    await generate_workout(request)

                assert "OpenRouter API key not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_generate_workout_with_overrides(
        self, sample_constraints, sample_overrides
    ):
        """Test workout generation with overrides."""
        request = GenerateWorkoutRequest(
            constraints=sample_constraints,
            overrides=sample_overrides,
            user_id="test_user",
        )

        mock_ai_response = "1. Squat\n3 sets of 8 reps"

        with patch("app.api.generate.send_prompt", new_callable=AsyncMock) as mock_send:
            with patch(
                "app.api.generate.match_exercise_template", new_callable=AsyncMock
            ) as mock_match:
                with patch("main.prompts", {"single_workout": "Goals: {goals}"}):
                    mock_send.return_value = mock_ai_response
                    mock_match.return_value = {
                        "template_id": "test_id",
                        "name": "Test Exercise",
                    }

                    await generate_workout(request)

                    mock_send.assert_called_once()
                    call_args = mock_send.call_args
                    prompt_used = call_args.kwargs["prompt"]

                    assert "squat, bench press" in prompt_used
                    assert "deadlift" in prompt_used
                    assert "chest, legs" in prompt_used
