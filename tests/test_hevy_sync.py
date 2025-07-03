"""Tests for Hevy synchronization service."""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

if os.path.join(os.path.dirname(__file__), "..", "backend") not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.models import Workout
from app.services.hevy_sync import push_workout_to_hevy, _map_workout_to_hevy_routine


class TestHevySync:
    """Test suite for Hevy synchronization service."""

    @pytest.mark.asyncio
    async def test_push_workout_to_hevy_success(self):
        """Test successful workout push to Hevy."""
        workout_id = "test_workout_123"
        expected_routine_id = "hevy_routine_456"
        
        mock_workout = Workout(
            id=workout_id,
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[
                {"name": "Push-ups", "sets": 3, "reps": 15},
                {"name": "Squats", "sets": 3, "reps": 20},
            ]
        )
        
        mock_hevy_response = {"id": expected_routine_id, "title": "Workout from 2024-01-15 10:30"}
        
        with patch("app.services.hevy_sync.get_workout") as mock_get_workout, \
             patch("app.services.hevy_sync.HevyClient") as mock_hevy_client_class:
            
            mock_get_workout.return_value = mock_workout
            mock_hevy_client = AsyncMock()
            mock_hevy_client.post_routine.return_value = mock_hevy_response
            mock_hevy_client_class.return_value = mock_hevy_client
            
            result = await push_workout_to_hevy(workout_id)
            
            assert result == expected_routine_id
            mock_get_workout.assert_called_once_with(workout_id)
            mock_hevy_client.post_routine.assert_called_once()
            
            call_args = mock_hevy_client.post_routine.call_args[0][0]
            assert "title" in call_args
            assert "exercises" in call_args
            assert len(call_args["exercises"]) == 2
            assert call_args["exercises"][0]["name"] == "Push-ups"

    @pytest.mark.asyncio
    async def test_push_workout_to_hevy_workout_not_found(self):
        """Test error handling when workout is not found."""
        workout_id = "nonexistent_workout"
        
        with patch("app.services.hevy_sync.get_workout") as mock_get_workout:
            mock_get_workout.return_value = None
            
            with pytest.raises(ValueError, match=f"Workout with ID {workout_id} not found"):
                await push_workout_to_hevy(workout_id)

    @pytest.mark.asyncio
    async def test_push_workout_to_hevy_api_error(self):
        """Test error handling when Hevy API call fails."""
        workout_id = "test_workout_123"
        
        mock_workout = Workout(
            id=workout_id,
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[{"name": "Push-ups", "sets": 3, "reps": 15}]
        )
        
        with patch("app.services.hevy_sync.get_workout") as mock_get_workout, \
             patch("app.services.hevy_sync.HevyClient") as mock_hevy_client_class:
            
            mock_get_workout.return_value = mock_workout
            mock_hevy_client = AsyncMock()
            mock_hevy_client.post_routine.side_effect = Exception("API Error")
            mock_hevy_client_class.return_value = mock_hevy_client
            
            with pytest.raises(Exception, match="API Error"):
                await push_workout_to_hevy(workout_id)

    @pytest.mark.asyncio
    async def test_push_workout_to_hevy_missing_routine_id(self):
        """Test error handling when Hevy API response is missing routine ID."""
        workout_id = "test_workout_123"
        
        mock_workout = Workout(
            id=workout_id,
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[{"name": "Push-ups", "sets": 3, "reps": 15}]
        )
        
        mock_hevy_response = {"title": "Workout from 2024-01-15 10:30"}
        
        with patch("app.services.hevy_sync.get_workout") as mock_get_workout, \
             patch("app.services.hevy_sync.HevyClient") as mock_hevy_client_class:
            
            mock_get_workout.return_value = mock_workout
            mock_hevy_client = AsyncMock()
            mock_hevy_client.post_routine.return_value = mock_hevy_response
            mock_hevy_client_class.return_value = mock_hevy_client
            
            with pytest.raises(Exception, match="Hevy API response missing routine ID"):
                await push_workout_to_hevy(workout_id)

    def test_map_workout_to_hevy_routine_simple_format(self):
        """Test mapping workout with simple exercise format."""
        workout = Workout(
            id="test_workout",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[
                {"name": "Push-ups", "sets": 3, "reps": 15},
                {"name": "Squats", "sets": 4, "reps": 20, "weight": 50},
            ]
        )
        
        result = _map_workout_to_hevy_routine(workout)
        
        assert result["title"] == "Workout from 2024-01-15 10:30"
        assert len(result["exercises"]) == 2
        
        pushups = result["exercises"][0]
        assert pushups["name"] == "Push-ups"
        assert len(pushups["sets"]) == 3
        assert all(s["reps"] == 15 for s in pushups["sets"])
        
        squats = result["exercises"][1]
        assert squats["name"] == "Squats"
        assert len(squats["sets"]) == 4
        assert all(s["reps"] == 20 and s["weight"] == 50 for s in squats["sets"])

    def test_map_workout_to_hevy_routine_complex_format(self):
        """Test mapping workout with complex exercise format."""
        workout = Workout(
            id="test_workout",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[
                {
                    "name": "Bench Press",
                    "sets": [
                        {"weight": 135, "reps": 10},
                        {"weight": 155, "reps": 8},
                        {"weight": 175, "reps": 6},
                    ],
                    "notes": "Felt strong today"
                }
            ]
        )
        
        result = _map_workout_to_hevy_routine(workout)
        
        assert len(result["exercises"]) == 1
        
        bench_press = result["exercises"][0]
        assert bench_press["name"] == "Bench Press"
        assert bench_press["notes"] == "Felt strong today"
        assert len(bench_press["sets"]) == 3
        assert bench_press["sets"][0] == {"weight": 135, "reps": 10}
        assert bench_press["sets"][1] == {"weight": 155, "reps": 8}
        assert bench_press["sets"][2] == {"weight": 175, "reps": 6}

    def test_map_workout_to_hevy_routine_missing_exercise_name(self):
        """Test mapping workout with missing exercise name."""
        workout = Workout(
            id="test_workout",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[
                {"sets": 3, "reps": 15}
            ]
        )
        
        result = _map_workout_to_hevy_routine(workout)
        
        assert len(result["exercises"]) == 1
        assert result["exercises"][0]["name"] == "Unknown Exercise"
        assert len(result["exercises"][0]["sets"]) == 3

    def test_map_workout_to_hevy_routine_empty_exercises(self):
        """Test mapping workout with no exercises."""
        workout = Workout(
            id="test_workout",
            date=datetime(2024, 1, 15, 10, 30),
            exercises=[]
        )
        
        result = _map_workout_to_hevy_routine(workout)
        
        assert result["title"] == "Workout from 2024-01-15 10:30"
        assert result["exercises"] == []
        assert "notes" in result
