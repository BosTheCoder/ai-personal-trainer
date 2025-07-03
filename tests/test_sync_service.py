"""Tests for the Hevy sync service."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

if os.path.join(os.path.dirname(__file__), "..", "backend") not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.sync_service import SyncService


class TestSyncService:
    """Test suite for SyncService."""

    @pytest.fixture
    def sync_service(self):
        """Create a SyncService instance for testing."""
        return SyncService()

    @pytest.mark.asyncio
    @patch.object(SyncService, "_run_pull_operation")
    @patch("app.services.sync_service.push_workout_to_hevy")
    @patch("app.services.sync_service.get_recent_workouts")
    async def test_run_sync_success(
        self, mock_get_workouts, mock_push, mock_pull, sync_service
    ):
        """Test successful sync operation."""
        mock_pull.return_value = None

        mock_workout = MagicMock()
        mock_workout.id = "test_workout_123"
        mock_get_workouts.return_value = [mock_workout]

        mock_push.return_value = "hevy_routine_456"

        result = await sync_service.run_sync()

        assert result["pull_success"] is True
        assert result["push_success"] is True
        assert result["pushed_workouts"] == 1
        assert result["pull_error"] is None
        assert result["push_error"] is None
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result

        mock_pull.assert_called_once()
        mock_get_workouts.assert_called_once_with(days=7)
        mock_push.assert_called_once_with("test_workout_123")

    @pytest.mark.asyncio
    @patch.object(SyncService, "_run_pull_operation")
    @patch("app.services.sync_service.push_workout_to_hevy")
    @patch("app.services.sync_service.get_recent_workouts")
    async def test_run_sync_pull_failure(
        self, mock_get_workouts, mock_push, mock_pull, sync_service
    ):
        """Test sync operation with pull failure."""
        mock_pull.side_effect = Exception("Pull failed")

        mock_workout = MagicMock()
        mock_workout.id = "test_workout_123"
        mock_get_workouts.return_value = [mock_workout]
        mock_push.return_value = "hevy_routine_456"

        result = await sync_service.run_sync()

        assert result["pull_success"] is False
        assert result["push_success"] is True
        assert result["pull_error"] == "Pull failed"
        assert result["push_error"] is None

    @pytest.mark.asyncio
    @patch.object(SyncService, "_run_pull_operation")
    @patch("app.services.sync_service.push_workout_to_hevy")
    @patch("app.services.sync_service.get_recent_workouts")
    async def test_run_sync_push_failure(
        self, mock_get_workouts, mock_push, mock_pull, sync_service
    ):
        """Test sync operation with push failure."""
        mock_pull.return_value = None

        mock_get_workouts.side_effect = Exception("Push failed")

        result = await sync_service.run_sync()

        assert result["pull_success"] is True
        assert result["push_success"] is False
        assert result["pull_error"] is None
        assert result["push_error"] == "Push failed"
