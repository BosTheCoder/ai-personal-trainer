import asyncio
from typing import Any, Dict

import httpx

from ..db import get_user_settings


async def send_prompt(prompt: str, variables: Dict[str, Any], user_id: str) -> str:
    """
    Send a prompt to OpenRouter API with variable substitution and retry logic.

    Args:
        prompt: The prompt template string
        variables: Dictionary of variables to substitute in the prompt
        user_id: User ID to retrieve API key from settings

    Returns:
        Response text from OpenRouter API

    Raises:
        ValueError: If API key is not found in user settings
        httpx.HTTPError: If API request fails after retries
    """
    user_settings = get_user_settings(user_id)
    if not user_settings or "openrouter" not in user_settings.api_keys:
        raise ValueError("OpenRouter API key not found in user settings")

    api_key = user_settings.api_keys["openrouter"]

    formatted_prompt = prompt.format(**variables)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": formatted_prompt}],
    }

    max_retries = 3
    base_delay = 1.0

    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries + 1):
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        await response.raise_for_status()

                await response.raise_for_status()

                response_data = await response.json()
                return response_data["choices"][0]["message"]["content"]

            except httpx.HTTPError:
                if attempt == max_retries:
                    raise
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)

    raise RuntimeError("Failed to get response after all retries")
