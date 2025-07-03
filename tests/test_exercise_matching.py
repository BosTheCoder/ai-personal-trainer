import os
import sys
from unittest.mock import AsyncMock, patch
import pytest

if os.path.join(os.path.dirname(__file__), "..", "backend") not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.utils import match_exercise_template, get_hevy_templates, OTHER_NOTES_TEMPLATE
from app.clients.hevy_client import HevyClient


class TestExerciseMatching:
    """Test suite for exercise template matching functionality."""

    @pytest.fixture
    def mock_hevy_client(self):
        """Mock HevyClient with sample exercise templates."""
        client = AsyncMock(spec=HevyClient)
        
        sample_templates = [
            {"id": "hevy_squat_001", "name": "Squat"},
            {"id": "hevy_deadlift_001", "name": "Deadlift"},
            {"id": "hevy_bench_press_001", "name": "Bench Press"},
            {"id": "hevy_overhead_press_001", "name": "Overhead Press"},
            {"id": "hevy_barbell_row_001", "name": "Barbell Row"},
            {"id": "hevy_pull_up_001", "name": "Pull-up"},
            {"id": "hevy_push_up_001", "name": "Push-up"},
            {"id": "hevy_bicep_curl_001", "name": "Bicep Curl"},
            {"id": "hevy_tricep_extension_001", "name": "Tricep Extension"},
            {"id": "hevy_lat_pulldown_001", "name": "Lat Pulldown"},
        ]
        
        client.get_exercise_templates.return_value = {
            "exercise_templates": sample_templates
        }
        
        return client

    @pytest.mark.asyncio
    async def test_exact_match(self, mock_hevy_client):
        """Test exact exercise name matching."""
        result = await match_exercise_template("Squat", mock_hevy_client)
        
        assert result["template_id"] == "hevy_squat_001"
        assert result["name"] == "Squat"

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self, mock_hevy_client):
        """Test case insensitive matching."""
        result = await match_exercise_template("DEADLIFT", mock_hevy_client)
        
        assert result["template_id"] == "hevy_deadlift_001"
        assert result["name"] == "Deadlift"

    @pytest.mark.asyncio
    async def test_partial_match(self, mock_hevy_client):
        """Test partial name matching."""
        result = await match_exercise_template("Bench", mock_hevy_client)
        
        assert result["template_id"] == "hevy_bench_press_001"
        assert result["name"] == "Bench Press"

    @pytest.mark.asyncio
    async def test_similar_match(self, mock_hevy_client):
        """Test similar name matching."""
        result = await match_exercise_template("Pull ups", mock_hevy_client)
        
        assert result["template_id"] == "hevy_pull_up_001"
        assert result["name"] == "Pull-up"

    @pytest.mark.asyncio
    async def test_no_match_fallback(self, mock_hevy_client):
        """Test fallback to Other - Notes when no good match found."""
        result = await match_exercise_template("Jumping Jacks", mock_hevy_client)
        
        assert result["template_id"] == OTHER_NOTES_TEMPLATE["template_id"]
        assert "Other – Notes - Jumping Jacks" in result["name"]

    @pytest.mark.asyncio
    async def test_empty_name_fallback(self, mock_hevy_client):
        """Test fallback for empty exercise name."""
        result = await match_exercise_template("", mock_hevy_client)
        
        assert result["template_id"] == OTHER_NOTES_TEMPLATE["template_id"]
        assert "Other – Notes" in result["name"]

    @pytest.mark.asyncio
    async def test_whitespace_only_fallback(self, mock_hevy_client):
        """Test fallback for whitespace-only exercise name."""
        result = await match_exercise_template("   ", mock_hevy_client)
        
        assert result["template_id"] == OTHER_NOTES_TEMPLATE["template_id"]
        assert "Other – Notes" in result["name"]

    @pytest.mark.asyncio
    async def test_custom_similarity_threshold(self, mock_hevy_client):
        """Test custom similarity threshold."""
        result = await match_exercise_template(
            "Squats", mock_hevy_client, similarity_threshold=0.9
        )
        
        assert result["template_id"] == "hevy_squat_001"
        assert result["name"] == "Squat"

    @pytest.mark.asyncio
    async def test_high_threshold_fallback(self, mock_hevy_client):
        """Test fallback with very high similarity threshold."""
        result = await match_exercise_template(
            "Squatting", mock_hevy_client, similarity_threshold=0.95
        )
        
        assert result["template_id"] == OTHER_NOTES_TEMPLATE["template_id"]
        assert "Other – Notes - Squatting" in result["name"]

    @pytest.mark.asyncio
    async def test_api_error_fallback(self):
        """Test fallback when API call fails."""
        failing_client = AsyncMock(spec=HevyClient)
        failing_client.get_exercise_templates.side_effect = Exception("API Error")
        
        result = await match_exercise_template("Squat", failing_client)
        
        assert result["template_id"] == OTHER_NOTES_TEMPLATE["template_id"]
        assert "Other – Notes - Squat" in result["name"]

    @pytest.mark.asyncio
    async def test_accuracy_verification(self, mock_hevy_client):
        """Test accuracy on a sample dataset."""
        test_cases = [
            ("Squat", "hevy_squat_001"),
            ("Deadlift", "hevy_deadlift_001"),
            ("Bench Press", "hevy_bench_press_001"),
            ("Overhead Press", "hevy_overhead_press_001"),
            ("Barbell Row", "hevy_barbell_row_001"),
            ("Pull-up", "hevy_pull_up_001"),
            ("Push-up", "hevy_push_up_001"),
            ("Bicep Curl", "hevy_bicep_curl_001"),
            ("Tricep Extension", "hevy_tricep_extension_001"),
            ("Lat Pulldown", "hevy_lat_pulldown_001"),
        ]
        
        correct_matches = 0
        total_tests = len(test_cases)
        
        for exercise_name, expected_id in test_cases:
            result = await match_exercise_template(exercise_name, mock_hevy_client)
            if result["template_id"] == expected_id:
                correct_matches += 1
        
        accuracy = correct_matches / total_tests
        assert accuracy >= 0.9, f"Accuracy {accuracy:.2%} is below 90% requirement"

    @pytest.mark.asyncio
    async def test_caching_functionality(self, mock_hevy_client):
        """Test that template caching works correctly."""
        from app.utils import _template_cache, _cache_timestamp
        
        with patch('app.utils._template_cache', None):
            with patch('app.utils._cache_timestamp', None):
                result1 = await match_exercise_template("Squat", mock_hevy_client)
                
                assert mock_hevy_client.get_exercise_templates.call_count == 1
                
                result2 = await match_exercise_template("Deadlift", mock_hevy_client)
                
                assert mock_hevy_client.get_exercise_templates.call_count == 1
                assert result1["template_id"] == "hevy_squat_001"
                assert result2["template_id"] == "hevy_deadlift_001"

    @pytest.mark.asyncio
    async def test_pagination_handling(self):
        """Test that pagination is handled correctly."""
        client = AsyncMock(spec=HevyClient)
        
        page1_templates = [{"id": f"template_{i}", "name": f"Exercise {i}"} for i in range(100)]
        page2_templates = [{"id": f"template_{i}", "name": f"Exercise {i}"} for i in range(100, 150)]
        
        client.get_exercise_templates.side_effect = [
            {"exercise_templates": page1_templates},
            {"exercise_templates": page2_templates},
            {"exercise_templates": []},
        ]
        
        templates = await get_hevy_templates(client)
        
        assert len(templates) == 150
        assert client.get_exercise_templates.call_count == 3
