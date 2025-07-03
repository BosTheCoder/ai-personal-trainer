import os
from typing import Any, Dict, Optional

import httpx


class HevyClient:
    """Hevy API client for workout and routine management."""

    def __init__(self, token: Optional[str] = None):
        """Initialize Hevy client with API token."""
        self.token = token or os.getenv("HEVY_TOKEN")
        if not self.token:
            raise ValueError("HEVY_TOKEN environment variable is required")

        self.base_url = "https://api.hevyapp.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def get_workouts(self, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get a paginated list of workouts."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/workouts",
                headers=self.headers,
                params={"page": page, "pageSize": page_size},
            )
            response.raise_for_status()
            return response.json()

    async def get_exercise_templates(
        self, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """Get a paginated list of exercise templates."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/exercise_templates",
                headers=self.headers,
                params={"page": page, "pageSize": page_size},
            )
            response.raise_for_status()
            return response.json()

    async def post_routine(self, routine_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new routine."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/routines",
                headers=self.headers,
                json=routine_data,
            )
            response.raise_for_status()
            return response.json()

    async def post_routine_folder(self, folder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new routine folder."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/routine_folders",
                headers=self.headers,
                json=folder_data,
            )
            response.raise_for_status()
            return response.json()
