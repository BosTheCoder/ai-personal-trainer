import os
import sys
import tempfile
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app, prompts, load_prompts, save_prompts
from app.models import PromptTemplate


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_prompts():
    """Sample prompts for testing"""
    return {
        "test_prompt": "This is a test prompt with {variable}",
        "another_prompt": "Another prompt for testing"
    }


@pytest.fixture
def temp_prompts_file(sample_prompts):
    """Create a temporary prompts.yaml file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.safe_dump(sample_prompts, f)
        temp_file = f.name
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.remove(temp_file)


class TestGetPrompt:
    """Test cases for GET /prompts/{name} endpoint"""
    
    def test_get_existing_prompt(self, client, sample_prompts):
        """Test getting an existing prompt"""
        with patch.dict('main.prompts', sample_prompts):
            response = client.get("/prompts/test_prompt")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test_prompt"
            assert data["template"] == "This is a test prompt with {variable}"
    
    def test_get_nonexistent_prompt(self, client):
        """Test getting a non-existent prompt"""
        with patch.dict('main.prompts', {"existing": "template"}):
            response = client.get("/prompts/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
            assert "Available:" in response.json()["detail"]


class TestUpdatePrompt:
    """Test cases for PUT /prompts/{name} endpoint"""
    
    def test_update_existing_prompt(self, client, sample_prompts):
        """Test updating an existing prompt"""
        new_template = "Updated template with {new_variable}"
        
        with patch.dict('main.prompts', sample_prompts.copy()):
            with patch('main.save_prompts') as mock_save:
                response = client.put(
                    "/prompts/test_prompt",
                    json={"name": "test_prompt", "template": new_template}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "test_prompt"
                assert data["template"] == new_template
                assert data["message"] == "Prompt updated successfully"
                mock_save.assert_called_once()
    
    def test_create_new_prompt(self, client, sample_prompts):
        """Test creating a new prompt"""
        new_template = "Brand new template with {variable}"
        
        with patch.dict('main.prompts', sample_prompts.copy()):
            with patch('main.save_prompts') as mock_save:
                response = client.put(
                    "/prompts/new_prompt",
                    json={"name": "new_prompt", "template": new_template}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["name"] == "new_prompt"
                assert data["template"] == new_template
                mock_save.assert_called_once()
    
    def test_name_mismatch_error(self, client):
        """Test error when URL name doesn't match request body name"""
        response = client.put(
            "/prompts/url_name",
            json={"name": "body_name", "template": "test template"}
        )
        
        assert response.status_code == 400
        assert "does not match" in response.json()["detail"]
    
    def test_invalid_request_body(self, client):
        """Test error with invalid request body"""
        response = client.put(
            "/prompts/test_prompt",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422
    
    def test_save_failure_rollback(self, client, sample_prompts):
        """Test that prompts are reloaded when save fails"""
        original_prompts = sample_prompts.copy()
        
        with patch.dict('main.prompts', original_prompts):
            with patch('main.save_prompts', side_effect=Exception("Save failed")):
                with patch('main.load_prompts') as mock_load:
                    response = client.put(
                        "/prompts/test_prompt",
                        json={"name": "test_prompt", "template": "new template"}
                    )
                    
                    assert response.status_code == 500
                    assert "Failed to save prompt" in response.json()["detail"]
                    mock_load.assert_called_once()


class TestSavePrompts:
    """Test cases for save_prompts function"""
    
    def test_save_prompts_success(self, temp_prompts_file, sample_prompts):
        """Test successful saving of prompts"""
        with patch('main.prompts', sample_prompts):
            with patch('os.path.join', return_value=temp_prompts_file):
                save_prompts()
                
                with open(temp_prompts_file, 'r') as f:
                    saved_data = yaml.safe_load(f)
                assert saved_data == sample_prompts
    
    def test_save_prompts_cleanup_on_error(self, temp_prompts_file):
        """Test that temp file is cleaned up on error"""
        with patch('main.prompts', {"test": "data"}):
            with patch('os.path.join', return_value=temp_prompts_file):
                with patch('builtins.open', side_effect=Exception("Write failed")):
                    with pytest.raises(Exception):
                        save_prompts()
                    
                    temp_file = temp_prompts_file + ".tmp"
                    assert not os.path.exists(temp_file)
