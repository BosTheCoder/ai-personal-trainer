"""Prompt building service for generating LLM prompts."""

from typing import Any, Dict, Optional

from ..db import get_user_settings


def build_single_workout_prompt(
    user: str, constraints: Dict[str, Any], overrides: str = ""
) -> str:
    """
    Build a single workout prompt for LLM generation.
    
    Args:
        user: User ID to load settings and goals for
        constraints: Dictionary with workout constraints (equipment, duration, fitness_level)
        overrides: Natural language overrides to append to the prompt
        
    Returns:
        Final formatted prompt string ready for LLM
        
    Raises:
        ValueError: If user settings not found or required template missing
    """
    import main
    
    user_settings = get_user_settings(user)
    if not user_settings:
        raise ValueError(f"User settings not found for user: {user}")
    
    if "single_workout" not in main.prompts:
        raise ValueError("single_workout template not found in prompts")
    
    template = main.prompts["single_workout"]
    
    template_vars = {
        "goals": ", ".join(user_settings.goals) if user_settings.goals else "general fitness",
        "equipment": constraints.get("equipment", "bodyweight"),
        "duration": constraints.get("duration", "30"),
        "fitness_level": constraints.get("fitness_level", "intermediate"),
    }
    
    formatted_prompt = template.format(**template_vars)
    
    if overrides and overrides.strip():
        formatted_prompt += f"\n\nAdditional requirements: {overrides.strip()}"
    
    return formatted_prompt
