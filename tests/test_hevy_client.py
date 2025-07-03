import os
import sys
from unittest.mock import patch

import pytest

if os.path.join(os.path.dirname(__file__), "..", "backend") not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.clients.hevy_client import HevyClient


class TestHevyClient:
    """Test suite for HevyClient."""

    def test_init_with_token(self):
        """Test client initialization with explicit token."""
        client = HevyClient(token="test_token")
        assert client.token == "test_token"
        assert client.headers["Authorization"] == "Bearer test_token"
        assert client.base_url == "https://api.hevyapp.com"
        assert client.headers["Content-Type"] == "application/json"

    @patch.dict(os.environ, {"HEVY_TOKEN": "env_token"})
    def test_init_with_env_token(self):
        """Test client initialization with environment token."""
        client = HevyClient()
        assert client.token == "env_token"
        assert client.headers["Authorization"] == "Bearer env_token"

    def test_init_without_token_raises_error(self):
        """Test client initialization without token raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="HEVY_TOKEN environment variable is required"
            ):
                HevyClient()

    def test_client_has_required_methods(self):
        """Test that client has all required methods."""
        client = HevyClient(token="test_token")

        assert hasattr(client, "get_workouts")
        assert hasattr(client, "get_exercise_templates")
        assert hasattr(client, "post_routine")
        assert hasattr(client, "post_routine_folder")

        assert callable(client.get_workouts)
        assert callable(client.get_exercise_templates)
        assert callable(client.post_routine)
        assert callable(client.post_routine_folder)

    def test_client_configuration(self):
        """Test client configuration and headers."""
        client = HevyClient(token="test_token_123")

        assert client.base_url == "https://api.hevyapp.com"
        assert client.headers["Authorization"] == "Bearer test_token_123"
        assert client.headers["Content-Type"] == "application/json"
