import os
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.app.ai.openrouter import send_prompt
from backend.app.models import UserSettings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_user_settings():
    """Mock user settings with OpenRouter API key."""
    return UserSettings(
        user_id="test_user", goals=["fitness"], api_keys={"openrouter": "test_api_key"}
    )


@pytest.fixture
def mock_response_success():
    """Mock successful OpenRouter API response."""
    return {
        "choices": [{"message": {"content": "This is a test response from OpenRouter"}}]
    }


@pytest.mark.asyncio
async def test_send_prompt_success(mock_user_settings, mock_response_success):
    """Test successful prompt sending."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_user_settings

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=mock_response_success)
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await send_prompt("Hello {name}!", {"name": "World"}, "test_user")

            assert result == "This is a test response from OpenRouter"
            mock_get_settings.assert_called_once_with("test_user")


@pytest.mark.asyncio
async def test_send_prompt_missing_api_key():
    """Test error when API key is missing."""
    mock_settings = UserSettings(user_id="test_user", goals=["fitness"], api_keys={})

    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError, match="OpenRouter API key not found"):
            await send_prompt("Hello!", {}, "test_user")


@pytest.mark.asyncio
async def test_send_prompt_no_user_settings():
    """Test error when user settings don't exist."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = None

        with pytest.raises(ValueError, match="OpenRouter API key not found"):
            await send_prompt("Hello!", {}, "test_user")


@pytest.mark.asyncio
async def test_send_prompt_rate_limit_retry(mock_user_settings, mock_response_success):
    """Test exponential backoff retry on rate limit (429)."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_user_settings

        with patch("httpx.AsyncClient") as mock_client:
            mock_response_429 = AsyncMock()
            mock_response_429.status_code = 429

            mock_response_success_obj = AsyncMock()
            mock_response_success_obj.status_code = 200
            mock_response_success_obj.json = AsyncMock(
                return_value=mock_response_success
            )
            mock_response_success_obj.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[mock_response_429, mock_response_success_obj]
            )

            with patch("asyncio.sleep") as mock_sleep:
                result = await send_prompt("Test", {}, "test_user")

                assert result == "This is a test response from OpenRouter"
                mock_sleep.assert_called_once_with(1.0)


@pytest.mark.asyncio
async def test_send_prompt_max_retries_exceeded(mock_user_settings):
    """Test that function raises error after max retries."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_user_settings

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.raise_for_status = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Rate limited", request=None, response=mock_response
                )
            )

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with patch("asyncio.sleep"):
                with pytest.raises(httpx.HTTPStatusError):
                    await send_prompt("Test", {}, "test_user")


@pytest.mark.asyncio
async def test_send_prompt_http_error_retry(mock_user_settings, mock_response_success):
    """Test retry on HTTP errors other than 429."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_user_settings

        with patch("httpx.AsyncClient") as mock_client:
            mock_response_success_obj = AsyncMock()
            mock_response_success_obj.status_code = 200
            mock_response_success_obj.json = AsyncMock(
                return_value=mock_response_success
            )
            mock_response_success_obj.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=[
                    httpx.RequestError("Connection failed"),
                    mock_response_success_obj,
                ]
            )

            with patch("asyncio.sleep") as mock_sleep:
                result = await send_prompt("Test", {}, "test_user")

                assert result == "This is a test response from OpenRouter"
                mock_sleep.assert_called_once_with(1.0)


@pytest.mark.asyncio
async def test_send_prompt_variable_substitution(
    mock_user_settings, mock_response_success
):
    """Test that prompt variables are properly substituted."""
    with patch("backend.app.ai.openrouter.get_user_settings") as mock_get_settings:
        mock_get_settings.return_value = mock_user_settings

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=mock_response_success)
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            await send_prompt(
                "Create a {workout_type} workout for {duration} minutes "
                "targeting {muscle_group}",
                {"workout_type": "strength", "duration": "30", "muscle_group": "chest"},
                "test_user",
            )

            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            sent_payload = call_args[1]["json"]
            expected_content = (
                "Create a strength workout for 30 minutes targeting chest"
            )

            assert sent_payload["messages"][0]["content"] == expected_content
