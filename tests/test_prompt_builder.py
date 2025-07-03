import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.models import UserSettings
from backend.app.services.prompt_builder import build_single_workout_prompt


@pytest.fixture
def mock_user_settings():
    """Mock user settings for testing."""
    return UserSettings(
        user_id="test_user",
        goals=["build muscle", "lose weight"],
        api_keys={}
    )


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing."""
    return {
        "single_workout": "Create a UPDATED single workout for a user with the following preferences:\n\n- Goals: {goals}\n\n- Available equipment: {equipment}\n\n- Time available: {duration} minutes\n\n- Fitness level: {fitness_level}\n\n\nPlease provide a detailed workout plan with exercises, sets, reps, and rest periods.\n\nThis template has been updated via the API!"
    }


class TestBuildSingleWorkoutPrompt:
    """Test cases for build_single_workout_prompt function."""

    def test_basic_prompt_building(self, mock_user_settings, sample_prompts):
        """Test basic prompt building with standard inputs."""
        constraints = {
            "equipment": "dumbbells",
            "duration": "45",
            "fitness_level": "beginner"
        }
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_user_settings
            with patch.dict("main.prompts", sample_prompts):
                result = build_single_workout_prompt("test_user", constraints)
                
                assert "build muscle, lose weight" in result
                assert "dumbbells" in result
                assert "45 minutes" in result
                assert "beginner" in result

    def test_prompt_with_overrides(self, mock_user_settings, sample_prompts):
        """Test prompt building with natural language overrides."""
        constraints = {
            "equipment": "barbell",
            "duration": "60",
            "fitness_level": "advanced"
        }
        overrides = "Focus on compound movements and avoid isolation exercises"
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_user_settings
            with patch.dict("main.prompts", sample_prompts):
                result = build_single_workout_prompt("test_user", constraints, overrides)
                
                assert "Additional requirements: Focus on compound movements" in result

    def test_snapshot_fixed_inputs(self, sample_prompts):
        """Snapshot test with fixed inputs for consistency."""
        fixed_user_settings = UserSettings(
            user_id="snapshot_user",
            goals=["strength training"],
            api_keys={}
        )
        fixed_constraints = {
            "equipment": "gym equipment",
            "duration": "30",
            "fitness_level": "intermediate"
        }
        fixed_overrides = "Include warm-up and cool-down"
        
        expected_result = """Create a UPDATED single workout for a user with the following preferences:

- Goals: strength training

- Available equipment: gym equipment

- Time available: 30 minutes

- Fitness level: intermediate


Please provide a detailed workout plan with exercises, sets, reps, and rest periods.

This template has been updated via the API!

Additional requirements: Include warm-up and cool-down"""
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = fixed_user_settings
            with patch.dict("main.prompts", sample_prompts):
                result = build_single_workout_prompt("snapshot_user", fixed_constraints, fixed_overrides)
                
                assert result == expected_result

    def test_user_not_found_error(self, sample_prompts):
        """Test error when user settings not found."""
        constraints = {"equipment": "dumbbells"}
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = None
            with patch.dict("main.prompts", sample_prompts):
                with pytest.raises(ValueError, match="User settings not found for user: nonexistent_user"):
                    build_single_workout_prompt("nonexistent_user", constraints)

    def test_missing_template_error(self, mock_user_settings):
        """Test error when single_workout template not found."""
        constraints = {"equipment": "dumbbells"}
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_user_settings
            with patch.dict("main.prompts", {}):
                with pytest.raises(ValueError, match="single_workout template not found in prompts"):
                    build_single_workout_prompt("test_user", constraints)

    def test_empty_goals_default(self, sample_prompts):
        """Test default goals when user has no goals set."""
        user_settings_no_goals = UserSettings(
            user_id="test_user",
            goals=[],
            api_keys={}
        )
        constraints = {"equipment": "dumbbells"}
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = user_settings_no_goals
            with patch.dict("main.prompts", sample_prompts):
                result = build_single_workout_prompt("test_user", constraints)
                
                assert "general fitness" in result

    def test_default_constraint_values(self, mock_user_settings, sample_prompts):
        """Test default values for missing constraint parameters."""
        constraints = {}
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_user_settings
            with patch.dict("main.prompts", sample_prompts):
                result = build_single_workout_prompt("test_user", constraints)
                
                assert "bodyweight" in result
                assert "30 minutes" in result
                assert "intermediate" in result

    def test_empty_overrides_ignored(self, mock_user_settings, sample_prompts):
        """Test that empty or whitespace-only overrides are ignored."""
        constraints = {"equipment": "dumbbells"}
        
        with patch("backend.app.services.prompt_builder.get_user_settings") as mock_get_settings:
            mock_get_settings.return_value = mock_user_settings
            with patch.dict("main.prompts", sample_prompts):
                result_empty = build_single_workout_prompt("test_user", constraints, "")
                result_whitespace = build_single_workout_prompt("test_user", constraints, "   ")
                
                assert "Additional requirements:" not in result_empty
                assert "Additional requirements:" not in result_whitespace
